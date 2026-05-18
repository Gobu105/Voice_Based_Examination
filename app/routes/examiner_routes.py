from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, g, current_app
from app.database.models import get_db
from app.utils.decorators import role_required
from app.services.ai_service import score_answer

examiner_routes = Blueprint('examiner_routes', __name__)


def _now():
    return __import__('datetime').datetime.now(__import__('datetime').timezone.utc)


def _examiner_can_access_session(db, examiner_id, session_id):
    exam_sess = db.exam_sessions.find_one({'_id': session_id})
    if not exam_sess:
        return False
    assignment = db.examiner_assignments.find_one({'examiner_id': examiner_id, 'candidate_id': exam_sess['candidate_id'], 'exam_id': exam_sess['exam_id']})
    return assignment is not None


def _get_evaluation_state(exam_sess):
    evaluation = exam_sess.get('evaluation') or {}
    return {
        'locked': bool(evaluation.get('locked')),
        'locked_at': evaluation.get('locked_at'),
        'locked_by': evaluation.get('locked_by'),
        'reopened_at': evaluation.get('reopened_at'),
        'reopened_by': evaluation.get('reopened_by'),
        'reopen_count': int(evaluation.get('reopen_count', 0) or 0),
    }


def _is_evaluation_locked(exam_sess):
    return _get_evaluation_state(exam_sess)['locked']


@examiner_routes.route('/examiner/dashboard')
@role_required('EXAMINER')
def examiner_dashboard():
    db = get_db()
    examiner_id = g.current_user_id
    assignments = list(db.examiner_assignments.find({'examiner_id': examiner_id}))
    students = []
    for a in assignments:
        candidate = db.candidates.find_one({'_id': a['candidate_id']})
        if not candidate:
            continue
        user = db.users.find_one({'_id': candidate['reg_id']})
        exam = db.exams.find_one({'_id': a['exam_id']})
        sessions_list = list(db.exam_sessions.find({'candidate_id': candidate['_id'], 'exam_id': a['exam_id']}))
        students.append({'candidate_id': candidate['_id'], 'registration_no': candidate.get('registration_no', 'N/A'), 'full_name': user['full_name'] if user else 'Unknown', 'exam_name': exam['exam_name'] if exam else 'Unknown', 'exam_id': a['exam_id'], 'sessions': sessions_list})
    return render_template('examiner/examiner_dashboard.html', students=students)


@examiner_routes.route('/examiner/evaluate/<int:session_id>')
@role_required('EXAMINER')
def examiner_evaluate(session_id):
    db = get_db()
    if not _examiner_can_access_session(db, g.current_user_id, session_id):
        flash('You are not assigned to evaluate this exam session.')
        return redirect(url_for('examiner_routes.examiner_dashboard'))

    exam_sess = db.exam_sessions.find_one({'_id': session_id})
    if not exam_sess:
        flash('Exam session not found.')
        return redirect(url_for('examiner_routes.examiner_dashboard'))

    candidate = db.candidates.find_one({'_id': exam_sess['candidate_id']})
    user = db.users.find_one({'_id': candidate['reg_id']}) if candidate else None
    exam = db.exams.find_one({'_id': exam_sess['exam_id']})

    return render_template(
        'examiner/evaluate.html',
        session_id=session_id,
        student_name=user['full_name'] if user else 'Unknown Student',
        registration_no=candidate.get('registration_no', 'N/A') if candidate else 'N/A',
        exam_name=exam['exam_name'] if exam else 'Unknown Exam',
    )


@examiner_routes.route('/examiner/delete_session/<int:session_id>', methods=['POST'])
@role_required('EXAMINER')
def examiner_delete_session(session_id):
    db = get_db()
    if not _examiner_can_access_session(db, g.current_user_id, session_id):
        flash('You are not assigned to delete this exam session.')
        return redirect(url_for('examiner_routes.examiner_dashboard'))
    flash('Deleting sessions is disabled. Exam records are preserved.')
    return redirect(url_for('examiner_routes.examiner_dashboard'))


@examiner_routes.route('/examiner/get_student_answers/<int:session_id>')
@role_required('EXAMINER')
def get_student_answers(session_id):
    db = get_db()
    if not _examiner_can_access_session(db, g.current_user_id, session_id):
        return jsonify({"error": "you are not assigned to grade this student's exam"}), 403
    exam_sess = db.exam_sessions.find_one({'_id': session_id})
    if not exam_sess:
        return jsonify({'error': 'session not found'}), 404
    exam = db.exams.find_one({'_id': exam_sess['exam_id']})
    exam_key = __import__('app.services.crypto_service', fromlist=['decrypt_exam_key']).decrypt_exam_key(bytes(exam['enc_key_ciphertext']), bytes(exam['enc_key_iv']), bytes(exam['enc_key_tag']), current_app._master_key)
    answers = list(db.answers.find({'session_id': session_id}))
    data = []
    for a in answers:
        q = db.questions.find_one({'_id': a['question_id']})
        try:
            plaintext = __import__('app.services.crypto_service', fromlist=['decrypt_answer']).decrypt_answer(bytes(a['answer_ciphertext']), bytes(a['answer_iv']), bytes(a['answer_tag']), exam_key)
            tampered = not __import__('app.services.crypto_service', fromlist=['verify_integrity_hash']).verify_integrity_hash(current_app._master_key, plaintext, a['question_id'], session_id, a['encrypted_at'], a['integrity_hash'])
        except Exception:
            plaintext = '[DECRYPTION FAILED — answer may have been tampered with]'
            tampered = True
        data.append({'answer_id': a['_id'], 'question': q['question_text'] if q else 'Unknown', 'model_answer': q.get('model_answer', '') if q else '', 'answer': plaintext, 'marks': a.get('marks'), 'ai_marks': a.get('ai_marks'), 'grading_method': a.get('grading_method'), 'tampered': tampered})
    return jsonify({'answers': data, 'evaluation': _get_evaluation_state(exam_sess)})


@examiner_routes.route('/examiner/save_grade', methods=['POST'])
@role_required('EXAMINER')
def examiner_save_grade():
    db = get_db()
    data = request.get_json(silent=True) or request.form
    answer_id = int(data.get('answer_id', 0))
    marks = int(data.get('marks', 0))
    answer_doc = db.answers.find_one({'_id': answer_id})
    if not answer_doc:
        return jsonify({'error': 'answer not found'}), 404
    if not _examiner_can_access_session(db, g.current_user_id, answer_doc['session_id']):
        return jsonify({"error": "you are not assigned to grade this student's exam"}), 403
    exam_sess = db.exam_sessions.find_one({'_id': answer_doc['session_id']})
    if _is_evaluation_locked(exam_sess):
        return jsonify({'error': 'Evaluation is locked. Re-open evaluation before changing marks.'}), 423
    if marks < 0 or marks > 10:
        return jsonify({'error': 'Marks must be between 0 and 10.'}), 400
    db.answers.update_one({'_id': answer_id}, {'$set': {'marks': marks, 'grading_method': 'MANUAL', 'graded_at': _now(), 'graded_by': g.current_user_id}})
    return jsonify({'status': 'marks saved', 'marks': marks})


@examiner_routes.route('/examiner/ai_grade', methods=['POST'])
@role_required('EXAMINER')
def examiner_ai_grade():
    db = get_db()
    data = request.get_json(silent=True) or request.form
    answer_id = int(data.get('answer_id', 0))
    answer_doc = db.answers.find_one({'_id': answer_id})
    if not answer_doc:
        return jsonify({'error': 'answer not found'}), 404
    if not _examiner_can_access_session(db, g.current_user_id, answer_doc['session_id']):
        return jsonify({"error": "you are not assigned to grade this student's exam"}), 403
    exam_sess = db.exam_sessions.find_one({'_id': answer_doc['session_id']})
    if _is_evaluation_locked(exam_sess):
        return jsonify({'error': 'Evaluation is locked. Re-open evaluation before AI grading.'}), 423
    exam = db.exams.find_one({'_id': exam_sess['exam_id']})
    exam_key = __import__('app.services.crypto_service', fromlist=['decrypt_exam_key']).decrypt_exam_key(bytes(exam['enc_key_ciphertext']), bytes(exam['enc_key_iv']), bytes(exam['enc_key_tag']), current_app._master_key)
    try:
        plaintext = __import__('app.services.crypto_service', fromlist=['decrypt_answer']).decrypt_answer(bytes(answer_doc['answer_ciphertext']), bytes(answer_doc['answer_iv']), bytes(answer_doc['answer_tag']), exam_key)
    except Exception:
        return jsonify({'error': 'decryption failed'}), 500
    question = db.questions.find_one({'_id': answer_doc['question_id']})
    question_text = question['question_text'] if question else ''
    model_answer = question.get('model_answer', '') if question else ''
    ai_marks = score_answer(question_text, plaintext, model_answer)
    db.answers.update_one({'_id': answer_id}, {'$set': {'marks': ai_marks, 'ai_marks': ai_marks, 'grading_method': 'AI', 'graded_at': _now(), 'graded_by': g.current_user_id}})
    return jsonify({'status': 'ai graded', 'marks': ai_marks})


@examiner_routes.route('/examiner/ai_grade_all', methods=['POST'])
@role_required('EXAMINER')
def examiner_ai_grade_all():
    db = get_db()
    data = request.get_json(silent=True) or request.form
    session_id = int(data.get('session_id', 0))

    if not _examiner_can_access_session(db, g.current_user_id, session_id):
        return jsonify({"error": "you are not assigned to grade this student's exam"}), 403

    exam_sess = db.exam_sessions.find_one({'_id': session_id})
    if not exam_sess:
        return jsonify({'error': 'session not found'}), 404
    if _is_evaluation_locked(exam_sess):
        return jsonify({'error': 'Evaluation is locked. Re-open evaluation before AI grading.'}), 423

    exam = db.exams.find_one({'_id': exam_sess['exam_id']})
    if not exam:
        return jsonify({'error': 'exam not found'}), 404

    exam_key = __import__('app.services.crypto_service', fromlist=['decrypt_exam_key']).decrypt_exam_key(bytes(exam['enc_key_ciphertext']), bytes(exam['enc_key_iv']), bytes(exam['enc_key_tag']), current_app._master_key)
    graded_count = 0

    for answer_doc in db.answers.find({'session_id': session_id}):
        try:
            plaintext = __import__('app.services.crypto_service', fromlist=['decrypt_answer']).decrypt_answer(bytes(answer_doc['answer_ciphertext']), bytes(answer_doc['answer_iv']), bytes(answer_doc['answer_tag']), exam_key)
        except Exception:
            continue

        question = db.questions.find_one({'_id': answer_doc['question_id']})
        question_text = question['question_text'] if question else ''
        model_answer = question.get('model_answer', '') if question else ''
        ai_marks = score_answer(question_text, plaintext, model_answer)
        db.answers.update_one({'_id': answer_doc['_id']}, {'$set': {'marks': ai_marks, 'ai_marks': ai_marks, 'grading_method': 'AI', 'graded_at': _now(), 'graded_by': g.current_user_id}})
        graded_count += 1

    return jsonify({'status': 'ai graded', 'message': f'AI graded {graded_count} answer(s).'})


@examiner_routes.route('/examiner/lock_evaluation', methods=['POST'])
@role_required('EXAMINER')
def lock_evaluation():
    db = get_db()
    data = request.get_json(silent=True) or request.form
    session_id = int(data.get('session_id', 0))

    if not _examiner_can_access_session(db, g.current_user_id, session_id):
        return jsonify({"error": "you are not assigned to lock this evaluation"}), 403

    exam_sess = db.exam_sessions.find_one({'_id': session_id})
    if not exam_sess:
        return jsonify({'error': 'session not found'}), 404

    answers = list(db.answers.find({'session_id': session_id}))
    if not answers:
        return jsonify({'error': 'No answers are available to lock.'}), 400

    ungraded_count = sum(1 for a in answers if a.get('marks') is None)
    if ungraded_count:
        return jsonify({'error': f'{ungraded_count} answer(s) still need marks before locking.'}), 400

    now = _now()
    db.exam_sessions.update_one(
        {'_id': session_id},
        {'$set': {
            'evaluation.locked': True,
            'evaluation.locked_at': now,
            'evaluation.locked_by': g.current_user_id,
            'evaluation.updated_at': now,
        }},
    )
    return jsonify({'status': 'locked', 'message': 'Evaluation locked.'})


@examiner_routes.route('/examiner/reopen_evaluation', methods=['POST'])
@role_required('EXAMINER')
def reopen_evaluation():
    db = get_db()
    data = request.get_json(silent=True) or request.form
    session_id = int(data.get('session_id', 0))

    if not _examiner_can_access_session(db, g.current_user_id, session_id):
        return jsonify({"error": "you are not assigned to re-open this evaluation"}), 403

    exam_sess = db.exam_sessions.find_one({'_id': session_id})
    if not exam_sess:
        return jsonify({'error': 'session not found'}), 404

    evaluation = _get_evaluation_state(exam_sess)
    now = _now()
    db.exam_sessions.update_one(
        {'_id': session_id},
        {'$set': {
            'evaluation.locked': False,
            'evaluation.reopened_at': now,
            'evaluation.reopened_by': g.current_user_id,
            'evaluation.updated_at': now,
        },
         '$inc': {'evaluation.reopen_count': 1 if evaluation['locked'] else 0}},
    )
    return jsonify({'status': 'reopened', 'message': 'Evaluation re-opened for changes.'})


@examiner_routes.route('/examiner/get_result/<int:session_id>')
@role_required('EXAMINER')
def examiner_get_result(session_id):
    db = get_db()
    if not _examiner_can_access_session(db, g.current_user_id, session_id):
        return jsonify({"error": "you are not assigned to grade this student's exam"}), 403
    answers = list(db.answers.find({'session_id': session_id}))
    total = sum(a.get('marks', 0) or 0 for a in answers)
    return jsonify({'total_marks': total})
