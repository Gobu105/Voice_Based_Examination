from datetime import datetime, timezone

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, g, current_app
from pymongo.errors import PyMongoError
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
        invigilator_started = db.exam_sessions.find_one({'candidate_id': candidate['_id'], 'exam_id': exam['_id'], 'status': 'STARTED'}) is not None
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
    if question_id <= 0 or not isinstance(answer_text, str):
        return jsonify({'error': 'Invalid request data'}), 400

    question = db.questions.find_one({'_id': question_id})
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    normalized_answer = normalize_answer(question['question_text'], answer_text)
    if not normalized_answer:
        return jsonify({'error': 'Answer text is empty after normalization'}), 400

    exam_sess = db.exam_sessions.find_one({'_id': g.exam_session_id})
    if not exam_sess:
        return jsonify({'error': 'session not found'}), 400
    if exam_sess.get('status') == 'SUBMITTED':
        return jsonify({'error': 'Exam session already submitted'}), 403

    exam = db.exams.find_one({'_id': exam_sess['exam_id']})
    if not exam:
        return jsonify({'error': 'exam not found'}), 400

    if not ensure_examiner_assignment(db, exam_sess['candidate_id'], exam_sess['exam_id']):
        return jsonify({'error': 'Examiner assignment unavailable'}), 500

    try:
        exam_key = __import__('app.services.crypto_service', fromlist=['decrypt_exam_key']).decrypt_exam_key(
            bytes(exam['enc_key_ciphertext']),
            bytes(exam['enc_key_iv']),
            bytes(exam['enc_key_tag']),
            current_app._master_key,
        )
        ciphertext, iv, tag = __import__('app.services.crypto_service', fromlist=['encrypt_answer']).encrypt_answer(normalized_answer, exam_key)
        now = datetime.now(timezone.utc)
        integrity = __import__('app.services.crypto_service', fromlist=['compute_integrity_hash']).compute_integrity_hash(
            current_app._master_key,
            normalized_answer,
            question_id,
            g.exam_session_id,
            now,
        )

        answer_doc = db.answers.find_one({'session_id': g.exam_session_id, 'question_id': question_id})
        version_item = {
            'version_number': 1,
            'answer_ciphertext': ciphertext,
            'answer_iv': iv,
            'answer_tag': tag,
            'integrity_hash': integrity,
            'encrypted_at': now,
        }

        if answer_doc:
            last_versions = answer_doc.get('versions', [])
            last_text = None
            if last_versions:
                try:
                    last_text = __import__('app.services.crypto_service', fromlist=['decrypt_answer']).decrypt_answer(
                        bytes(last_versions[-1]['answer_ciphertext']),
                        bytes(last_versions[-1]['answer_iv']),
                        bytes(last_versions[-1]['answer_tag']),
                        exam_key,
                    )
                except Exception:
                    last_text = None

            if last_text == normalized_answer:
                return jsonify({
                    'status': 'unchanged',
                    'message': 'Answer has not changed since last save.',
                    'last_saved_at': format_datetime_for_display(answer_doc.get('updated_at') or answer_doc.get('encrypted_at')),
                })

            version_item['version_number'] = len(last_versions) + 1
            last_versions.append(version_item)
            db.answers.update_one(
                {'_id': answer_doc['_id']},
                {
                    '$set': {
                        'answer_ciphertext': ciphertext,
                        'answer_iv': iv,
                        'answer_tag': tag,
                        'integrity_hash': integrity,
                        'encrypted_at': now,
                        'versions': last_versions,
                        'updated_at': now,
                    }
                },
            )
            version_count = len(last_versions)
        else:
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
                'versions': [version_item],
                'created_at': now,
                'updated_at': now,
            })
            version_count = 1

        return jsonify({
            'status': 'saved',
            'normalized_answer': normalized_answer,
            'version_count': version_count,
            'last_saved_at': format_datetime_for_display(now),
        })
    except PyMongoError as exc:
        return jsonify({'error': 'Database error saving answer. Please retry.'}), 500
    except Exception as exc:
        return jsonify({'error': f'Unable to save answer: {str(exc)}'}), 500


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
    has_session = db.exam_sessions.find_one({'candidate_id': candidate['_id'], 'exam_id': exam['_id'], 'status': 'STARTED'}) is not None
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

    existing = db.exam_sessions.find_one({'candidate_id': candidate['_id'], 'exam_id': exam['_id'], 'status': 'STARTED'})
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


@candidate_routes.route('/api/transcribe', methods=['POST'])
@roles_required(('CANDIDATE',))
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if not audio_file or not audio_file.filename:
        return jsonify({'error': 'Invalid audio file'}), 400
    
    # Validate format
    if not __import__('app.services.speech_service', fromlist=['validate_audio_format']).validate_audio_format(audio_file.filename):
        return jsonify({'error': 'Unsupported audio format. Use WAV, MP3, OGG, or M4A.'}), 400
    
    try:
        audio_bytes = audio_file.read()
        transcription = __import__('app.services.speech_service', fromlist=['transcribe_audio']).transcribe_audio(audio_bytes)
        return jsonify({'transcription': transcription})
    except Exception as e:
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500


@candidate_routes.route('/exam/submitted')
def exam_submitted():
    return render_template('candidate/exam_submitted.html')
