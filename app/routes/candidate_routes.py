from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, g, current_app
from app.database.models import get_db, get_next_id
from app.utils.decorators import roles_required
from app.utils.helpers import _is_active_flag, _candidate_and_user, get_active_exam, ensure_examiner_assignment, normalize_answer, format_datetime_for_display

candidate_routes = Blueprint('candidate_routes', __name__)


@candidate_routes.route('/candidate/dashboard')
@roles_required(('CANDIDATE',))
def candidate_dashboard():
    db = get_db()
    candidate = db.candidates.find_one({'reg_id': g.current_user_id})
    exam = get_active_exam(db)
    invigilator_started = False
    if candidate and exam:
        invigilator_started = db.exam_sessions.find_one({'candidate_id': candidate['_id'], 'exam_id': exam['_id'], 'status': {'$ne': 'SUBMITTED'}}) is not None
    return render_template('candidate/student_dashboard.html', invigilator_started=invigilator_started)


@candidate_routes.route('/candidate/results')
@roles_required(('CANDIDATE',))
def candidate_results():
    db = get_db()
    candidate = db.candidates.find_one({'reg_id': g.current_user_id})
    user = db.users.find_one({'_id': g.current_user_id})
    if not candidate:
        return render_template('candidate/candidate_results.html', student_name=user['full_name'] if user else 'Student', results=[])

    sessions = list(db.exam_sessions.find({'candidate_id': candidate['_id']}).sort('start_time', -1))
    results = []
    for sess in sessions:
        exam = db.exams.find_one({'_id': sess['exam_id']})
        answers = list(db.answers.find({'session_id': sess['_id']}))
        graded_answers = [a for a in answers if a.get('marks') is not None]
        graded_at_values = [a.get('graded_at') for a in graded_answers if a.get('graded_at')]
        results.append({
            'session_id': sess['_id'],
            'exam_name': exam['exam_name'] if exam else f"Exam #{sess.get('exam_id')}",
            'exam_active': _is_active_flag(exam) if exam else False,
            'status': sess.get('status', 'UNKNOWN'),
            'answers_count': len(answers),
            'graded_count': len(graded_answers),
            'total_marks': sum(a.get('marks', 0) or 0 for a in graded_answers) if graded_answers else None,
            'started_at': format_datetime_for_display(sess.get('start_time')),
            'submitted_at': format_datetime_for_display(sess.get('submitted_at') or sess.get('end_time')),
            'graded_at': format_datetime_for_display(max(graded_at_values) if graded_at_values else None),
        })
    return render_template('candidate/candidate_results.html', student_name=user['full_name'] if user else 'Student', results=results)


@candidate_routes.route('/api/session_check')
@roles_required(('ADMIN', 'INVIGILATOR', 'EXAMINER', 'CANDIDATE'))
def session_check():
    return jsonify({'ok': True})


@candidate_routes.route('/api/questions')
@roles_required(('CANDIDATE',))
def get_questions():
    db = get_db()
    exam = get_active_exam(db)
    if not exam:
        return jsonify({'error': 'No exam available'}), 400
    questions = list(db.questions.find({'exam_id': exam['_id']}))
    return jsonify([{'id': q['_id'], 'text': q['question_text']} for q in questions])


@candidate_routes.route('/api/save_answer', methods=['POST'])
@roles_required(('CANDIDATE',))
def save_answer():
    db = get_db()
    if g.exam_session_id is None:
        return jsonify({'error': 'session not started'}), 400
    data = request.get_json() or {}
    question_id = int(data.get('question_id', 0))
    answer_text = data.get('answer', '')
    question = db.questions.find_one({'_id': question_id})
    normalized_answer = normalize_answer(question['question_text'] if question else '', answer_text)

    exam_sess = db.exam_sessions.find_one({'_id': g.exam_session_id})
    if not exam_sess:
        return jsonify({'error': 'session not found'}), 400

    exam = db.exams.find_one({'_id': exam_sess['exam_id']})
    if not exam:
        return jsonify({'error': 'exam not found'}), 400

    ensure_examiner_assignment(db, exam_sess['candidate_id'], exam_sess['exam_id'])
    exam_key = __import__('app.services.crypto_service', fromlist=['decrypt_exam_key']).decrypt_exam_key(
        bytes(exam['enc_key_ciphertext']),
        bytes(exam['enc_key_iv']),
        bytes(exam['enc_key_tag']),
        current_app._master_key,
    )
    ciphertext, iv, tag = __import__('app.services.crypto_service', fromlist=['encrypt_answer']).encrypt_answer(normalized_answer, exam_key)
    now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    integrity = __import__('app.services.crypto_service', fromlist=['compute_integrity_hash']).compute_integrity_hash(current_app._master_key, normalized_answer, question_id, g.exam_session_id, now)

    answer_id = get_next_id('answers')
    db.answers.insert_one({
        '_id': answer_id,
        'session_id': g.exam_session_id,
        'question_id': question_id,
        'answer_ciphertext': ciphertext,
        'answer_iv': iv,
        'answer_tag': tag,
        'integrity_hash': integrity,
        'encrypted_at': now,
        'marks': None,
    })
    return jsonify({'status': 'saved', 'normalized_answer': normalized_answer})


@candidate_routes.route('/api/exam_status')
@roles_required(('CANDIDATE',))
def exam_status():
    db = get_db()
    candidate = db.candidates.find_one({'reg_id': g.current_user_id})
    if not candidate:
        return jsonify({'invigilator_started': False})
    exam = get_active_exam(db)
    if not exam:
        return jsonify({'invigilator_started': False})
    has_session = db.exam_sessions.find_one({'candidate_id': candidate['_id'], 'exam_id': exam['_id'], 'status': {'$ne': 'SUBMITTED'}}) is not None
    return jsonify({'invigilator_started': has_session})


@candidate_routes.route('/api/start_exam')
@roles_required(('CANDIDATE',))
def start_exam():
    db = get_db()
    candidate = db.candidates.find_one({'reg_id': g.current_user_id})
    if not candidate:
        return jsonify({'error': 'Candidate profile not found for this user'}), 400
    exam = get_active_exam(db)
    if not exam:
        return jsonify({'error': 'No exam available'}), 400

    existing = db.exam_sessions.find_one({'candidate_id': candidate['_id'], 'exam_id': exam['_id'], 'status': {'$ne': 'SUBMITTED'}})
    if not existing:
        return jsonify({'error': 'You cannot start the exam yet. The invigilator must assign you to an exam and then start it. Wait for the invigilator to start the exam.'}), 403
    ensure_examiner_assignment(db, candidate['_id'], exam['_id'])

    accounts = session.get('accounts') or {}
    candidate_account = accounts.get('CANDIDATE') or {}
    candidate_account['user_id'] = g.current_user_id
    candidate_account['exam_session_id'] = existing['_id']
    accounts['CANDIDATE'] = candidate_account
    session['accounts'] = accounts
    return jsonify({'session_id': existing['_id'], 'duration_minutes': exam['duration'], 'invigilator_started': True})


@candidate_routes.route('/api/submit_exam', methods=['POST'])
@roles_required(('CANDIDATE',))
def submit_exam():
    db = get_db()
    if g.exam_session_id is None:
        return jsonify({'error': 'session not started'}), 400
    exam_sess = db.exam_sessions.find_one({'_id': g.exam_session_id})
    if not exam_sess:
        return jsonify({'error': 'session not found'}), 404
    candidate = db.candidates.find_one({'reg_id': g.current_user_id})
    if not candidate or exam_sess.get('candidate_id') != candidate['_id']:
        return jsonify({'error': 'forbidden'}), 403

    now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    if exam_sess.get('status') != 'SUBMITTED':
        db.exam_sessions.update_one({'_id': g.exam_session_id}, {'$set': {'status': 'SUBMITTED', 'end_time': now, 'submitted_at': now}})
    accounts = session.get('accounts') or {}
    candidate_account = accounts.get('CANDIDATE') or {}
    candidate_account['exam_session_id'] = None
    accounts['CANDIDATE'] = candidate_account
    session['accounts'] = accounts
    return jsonify({'status': 'submitted', 'submitted_at': format_datetime_for_display(now)})


@candidate_routes.route('/exam/submitted')
def exam_submitted():
    return render_template('candidate/exam_submitted.html')
