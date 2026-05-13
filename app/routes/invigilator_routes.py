from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, g, current_app
from app.database.models import get_db, get_next_id
from app.utils.decorators import roles_required
from app.utils.helpers import _is_active_flag, _candidate_and_user, get_active_exam, ensure_examiner_assignment

invigilator_routes = Blueprint('invigilator_routes', __name__)


@invigilator_routes.route('/invigilator/dashboard')
@roles_required(('INVIGILATOR',))
def invigilator_dashboard():
    db = get_db()
    exams = list(db.exams.find())
    for exam in exams:
        exam['is_active'] = _is_active_flag(exam)
    sessions = list(db.exam_sessions.find())

    candidates = []
    for candidate in db.candidates.find():
        user = db.users.find_one({'_id': candidate['reg_id']})
        if not user:
            continue
        candidates.append({
            '_id': candidate['_id'],
            'user_id': user['_id'],
            'full_name': user['full_name'],
            'registration_no': candidate.get('registration_no', 'N/A'),
            'is_active': _is_active_flag(user),
        })

    active_candidates = [c for c in candidates if c['is_active']]
    active_exams = [e for e in exams if e['is_active']]
    exam_assignments = []
    for a in db.exam_assignments.find():
        c = db.candidates.find_one({'_id': a['candidate_id']})
        u = db.users.find_one({'_id': c['reg_id']}) if c else None
        ex = db.exams.find_one({'_id': a['exam_id']})
        exam_assignments.append({
            '_id': a['_id'],
            'candidate_name': u['full_name'] if u else 'Unknown',
            'exam_name': ex['exam_name'] if ex else 'Unknown',
            'candidate_id': a['candidate_id'],
            'exam_id': a['exam_id'],
            'candidate_active': _is_active_flag(u) if u else False,
            'exam_active': _is_active_flag(ex) if ex else False,
        })

    return render_template('invigilator/invigilator_dashboard.html', exams=exams, active_exams=active_exams, sessions=sessions, candidates=candidates, active_candidates=active_candidates, exam_assignments=exam_assignments)


@invigilator_routes.route('/invigilator/create_student', methods=['POST'])
@roles_required(('INVIGILATOR', 'ADMIN'))
def create_student():
    db = get_db()
    full_name = request.form.get('full_name', '').strip()
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    phone = request.form.get('phone_no', '').strip()
    registration_no = request.form.get('registration_no', '').strip()

    if not all([full_name, username, email, password, registration_no]):
        flash('All required fields must be filled.')
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    if db.users.find_one({'username': username}):
        flash(f"Username '{username}' already exists.")
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    if db.users.find_one({'email': email}):
        flash(f"Email '{email}' already exists.")
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    if db.candidates.find_one({'registration_no': registration_no}):
        flash(f"Registration number '{registration_no}' already exists.")
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    reg_id = get_next_id('users')
    db.users.insert_one({'_id': reg_id, 'full_name': full_name, 'username': username, 'email': email, 'password_hash': __import__('werkzeug.security', fromlist=['generate_password_hash']).generate_password_hash(password), 'role': 'CANDIDATE', 'is_active': True, 'phone_no': phone or None, 'created_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc), 'session_token': None})
    candidate_id = get_next_id('candidates')
    db.candidates.insert_one({'_id': candidate_id, 'reg_id': reg_id, 'registration_no': registration_no})

    flash(f"Student '{full_name}' created successfully (username: {username}).")
    return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/toggle_student_status/<int:candidate_id>', methods=['POST'])
@roles_required(('INVIGILATOR',))
def invigilator_toggle_student_status(candidate_id):
    db = get_db()
    candidate, user = _candidate_and_user(db, candidate_id)
    if not candidate or not user:
        flash('Student not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    new_status = not _is_active_flag(user)
    db.users.update_one({'_id': user['_id']}, {'$set': {'is_active': new_status, 'updated_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)}})
    flash(f"Student '{user['full_name']}' set to {'Active' if new_status else 'Inactive'}.")
    return redirect(url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/assign_student_exam', methods=['POST'])
@roles_required(('INVIGILATOR',))
def assign_student_exam():
    db = get_db()
    candidate_id = int(request.form.get('candidate_id', 0))
    exam_id = int(request.form.get('exam_id', 0))

    candidate, user = _candidate_and_user(db, candidate_id)
    if not candidate or not user:
        flash('Student not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))
    if not _is_active_flag(user):
        flash('Inactive students cannot be assigned to exams.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    existing = db.exam_assignments.find_one({'candidate_id': candidate_id, 'exam_id': exam_id})
    if existing:
        flash('This student is already assigned to that exam.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    assign_id = get_next_id('exam_assignments')
    db.exam_assignments.insert_one({'_id': assign_id, 'candidate_id': candidate_id, 'exam_id': exam_id, 'assigned_by': g.current_user_id})
    flash('Student assigned to exam.')
    return redirect(url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/unassign_student_exam/<int:assign_id>', methods=['POST'])
@roles_required(('INVIGILATOR',))
def unassign_student_exam(assign_id):
    db = get_db()
    db.exam_assignments.delete_one({'_id': assign_id})
    flash('Student unassigned from exam.')
    return redirect(url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/create_exam', methods=['POST'])
@roles_required(('INVIGILATOR', 'ADMIN'))
def create_exam():
    db = get_db()
    exam_name = request.form.get('name', '').strip()
    duration = request.form.get('duration', '60').strip()

    if not exam_name:
        flash('Exam name is required.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    try:
        duration = int(duration)
    except ValueError:
        duration = 60

    exam_key = __import__('app.services.crypto_service', fromlist=['generate_exam_key']).generate_exam_key()
    enc_ct, enc_iv, enc_tag = __import__('app.services.crypto_service', fromlist=['encrypt_exam_key']).encrypt_exam_key(exam_key, current_app._master_key)

    exam_id = get_next_id('exams')
    db.exams.insert_one({'_id': exam_id, 'exam_name': exam_name, 'duration': duration, 'total_marks': 100, 'is_active': False, 'created_by': g.current_user_id, 'created_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc), 'enc_key_ciphertext': enc_ct, 'enc_key_iv': enc_iv, 'enc_key_tag': enc_tag})
    flash(f"Exam '{exam_name}' created successfully.")
    return redirect(url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/toggle_exam_status/<int:exam_id>', methods=['POST'])
@roles_required(('INVIGILATOR',))
def invigilator_toggle_exam_status(exam_id):
    db = get_db()
    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    new_status = not _is_active_flag(exam)
    if new_status:
        db.exams.update_many({}, {'$set': {'is_active': False}})
    db.exams.update_one({'_id': exam_id}, {'$set': {'is_active': new_status, 'updated_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)}})
    flash(f"Exam '{exam.get('exam_name', exam_id)}' set to {'Active' if new_status else 'Inactive'}.")
    return redirect(url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/start_exam/<int:exam_id>')
@roles_required(('INVIGILATOR',))
def start_exam_invigilator(exam_id):
    db = get_db()
    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    db.exams.update_many({}, {'$set': {'is_active': False}})
    db.exams.update_one({'_id': exam_id}, {'$set': {'is_active': True}})

    candidate_ids = {a['candidate_id'] for a in db.examiner_assignments.find({'exam_id': exam_id})}
    candidate_ids.update({a['candidate_id'] for a in db.exam_assignments.find({'exam_id': exam_id})})

    eligible_candidate_ids = []
    skipped_inactive = 0
    for cid in candidate_ids:
        _, cand_user = _candidate_and_user(db, cid)
        if not cand_user or not _is_active_flag(cand_user):
            skipped_inactive += 1
            continue
        eligible_candidate_ids.append(cid)

    created = 0
    for cid in eligible_candidate_ids:
        ensure_examiner_assignment(db, cid, exam_id)
        existing = db.exam_sessions.find_one({'candidate_id': cid, 'exam_id': exam_id, 'status': {'$ne': 'SUBMITTED'}})
        if not existing:
            session_id = get_next_id('exam_sessions')
            db.exam_sessions.insert_one({'_id': session_id, 'exam_id': exam_id, 'candidate_id': cid, 'start_time': __import__('datetime').datetime.now(__import__('datetime').timezone.utc), 'end_time': None, 'status': 'STARTED'})
            created += 1

    flash(f"Exam '{exam['exam_name']}' started. Session created for {created} student(s) (eligible: {len(eligible_candidate_ids)}, skipped inactive: {skipped_inactive}).")
    return redirect(url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/get_questions/<int:exam_id>')
@roles_required(('INVIGILATOR',))
def get_exam_questions(exam_id):
    db = get_db()
    questions = list(db.questions.find({'exam_id': exam_id}))
    return jsonify([{'id': q['_id'], 'text': q['question_text'], 'model_answer': q.get('model_answer', '')} for q in questions])


@invigilator_routes.route('/invigilator/add_question', methods=['POST'])
@roles_required(('INVIGILATOR',))
def add_question():
    db = get_db()
    exam_id = int(request.form.get('exam_id', 0))
    text = request.form.get('text', '').strip()
    model_answer = request.form.get('model_answer', '').strip()
    if not text or not model_answer:
        return jsonify({'error': 'Both question and answer key are required.'}), 400
    q_id = get_next_id('questions')
    db.questions.insert_one({'_id': q_id, 'exam_id': exam_id, 'question_text': text, 'model_answer': model_answer, 'created_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)})
    return jsonify({'status': 'added'})


@invigilator_routes.route('/invigilator/update_question', methods=['POST'])
@roles_required(('INVIGILATOR',))
def update_question():
    db = get_db()
    qid = int(request.form.get('qid', 0))
    text = request.form.get('text', '').strip()
    model_answer = request.form.get('model_answer', '').strip()
    if not text or not model_answer:
        return jsonify({'error': 'Both question and answer key are required.'}), 400
    db.questions.update_one({'_id': qid}, {'$set': {'question_text': text, 'model_answer': model_answer, 'updated_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)}})
    return jsonify({'status': 'updated'})


@invigilator_routes.route('/invigilator/delete_question/<int:qid>', methods=['POST'])
@roles_required(('INVIGILATOR',))
def delete_question(qid):
    db = get_db()
    db.questions.delete_one({'_id': qid})
    return jsonify({'status': 'deleted'})


@invigilator_routes.route('/invigilator/save_marks', methods=['POST'])
@roles_required(('INVIGILATOR',))
def save_marks():
    db = get_db()
    answer_id = int(request.form.get('answer_id', 0))
    marks = int(request.form.get('marks', 0))
    db.answers.update_one({'_id': answer_id}, {'$set': {'marks': marks, 'grading_method': 'MANUAL', 'graded_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)}})
    return jsonify({'status': 'marks saved'})


@invigilator_routes.route('/invigilator/get_answers/<int:session_id>')
@roles_required(('INVIGILATOR',))
def get_answers(session_id):
    db = get_db()
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
        data.append({'answer_id': a['_id'], 'question': q['question_text'] if q else 'Unknown', 'model_answer': q.get('model_answer', '') if q else '', 'answer': plaintext, 'marks': a.get('marks'), 'tampered': tampered})
    return jsonify(data)


@invigilator_routes.route('/invigilator/get_result/<int:session_id>')
@roles_required(('INVIGILATOR',))
def get_result(session_id):
    db = get_db()
    answers = list(db.answers.find({'session_id': session_id}))
    total = sum(a.get('marks', 0) or 0 for a in answers)
    return jsonify({'total_marks': total})
