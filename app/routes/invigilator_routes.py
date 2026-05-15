from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, g, current_app
from app.database.models import get_db, get_next_id
from app.services.auth_service import build_email_verification_fields, send_verification_email
from app.services.exam_service import create_exam as create_exam_record, activate_exam, get_questions_for_exam
from app.services.session_service import create_exam_session
from app.utils.decorators import roles_required
from app.utils.helpers import _is_active_flag, _candidate_and_user, get_active_exam, ensure_examiner_assignment, generate_registration_number, is_valid_email
from app.validators import validate_registration

invigilator_routes = Blueprint('invigilator_routes', __name__)


@invigilator_routes.route('/invigilator/dashboard')
@roles_required(('INVIGILATOR',))
def invigilator_dashboard():
    db = get_db()
    exams = list(db.exams.find())
    for exam in exams:
        exam['is_active'] = _is_active_flag(exam)

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
    completed_assignments = []
    for a in db.exam_assignments.find():
        c = db.candidates.find_one({'_id': a['candidate_id']})
        u = db.users.find_one({'_id': c['reg_id']}) if c else None
        ex = db.exams.find_one({'_id': a['exam_id']})
        submitted_session = db.exam_sessions.find_one({
            'candidate_id': a['candidate_id'],
            'exam_id': a['exam_id'],
            'status': 'SUBMITTED',
        })
        assignment_item = {
            '_id': a['_id'],
            'candidate_name': u['full_name'] if u else 'Unknown',
            'exam_name': ex['exam_name'] if ex else 'Unknown',
            'candidate_id': a['candidate_id'],
            'exam_id': a['exam_id'],
            'candidate_active': _is_active_flag(u) if u else False,
            'exam_active': _is_active_flag(ex) if ex else False,
        }
        if submitted_session:
            completed_assignments.append(assignment_item)
        else:
            exam_assignments.append(assignment_item)

    return render_template('invigilator/invigilator_dashboard.html', exams=exams, active_exams=active_exams, candidates=candidates, active_candidates=active_candidates, exam_assignments=exam_assignments, completed_assignments=completed_assignments)


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

    if not all([full_name, username, email, password]):
        flash('All required fields must be filled.')
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    if not is_valid_email(email):
        flash('Please enter a valid email address.')
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    if len(password) < 8:
        flash('Password must be at least 8 characters long.')
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    valid, validation_error = validate_registration(full_name, username, email, password)
    if not valid:
        flash(validation_error)
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    if db.users.find_one({'username': username}):
        flash(f"Username '{username}' already exists.")
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    if db.users.find_one({'email': email}):
        flash(f"Email '{email}' already exists.")
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    if not registration_no:
        registration_no = generate_registration_number(db)

    if db.candidates.find_one({'registration_no': registration_no}):
        flash(f"Registration number '{registration_no}' already exists.")
        return redirect(request.referrer or url_for('invigilator_routes.invigilator_dashboard'))

    verification_fields = build_email_verification_fields()
    reg_id = get_next_id('users')
    db.users.insert_one({
        '_id': reg_id,
        'full_name': full_name,
        'username': username,
        'email': email,
        'password_hash': __import__('werkzeug.security', fromlist=['generate_password_hash']).generate_password_hash(password),
        'role': 'CANDIDATE',
        'is_active': True,
        'email_verified': False,
        'verification_token': verification_fields['verification_token'],
        'verification_sent_at': verification_fields['verification_sent_at'],
        'phone_no': phone or None,
        'created_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
        'session_token': None,
    })
    candidate_id = get_next_id('candidates')
    db.candidates.insert_one({'_id': candidate_id, 'reg_id': reg_id, 'registration_no': registration_no})

    verification_url = send_verification_email({'email': email, 'full_name': full_name, 'verification_token': verification_fields['verification_token']})
    if verification_url:
        flash(f"Student '{full_name}' created. Verification link: {verification_url}")
    else:
        flash(f"Student '{full_name}' created successfully. A verification email has been sent.")
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
        if duration <= 0:
            duration = 60
    except ValueError:
        duration = 60

    create_exam_record(db, exam_name, duration, g.current_user_id, current_app._master_key)
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


@invigilator_routes.route('/invigilator/edit_exam/<int:exam_id>', methods=['GET', 'POST'])
@roles_required(('INVIGILATOR',))
def edit_exam(exam_id):
    db = get_db()
    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    if request.method == 'POST':
        exam_name = request.form.get('name', '').strip()
        duration = request.form.get('duration', '60').strip()

        if not exam_name:
            flash('Exam name is required.')
            return redirect(request.url)

        try:
            duration = int(duration)
            if duration <= 0:
                duration = 60
        except ValueError:
            duration = 60

        db.exams.update_one({'_id': exam_id}, {'$set': {'exam_name': exam_name, 'duration': duration, 'updated_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)}})
        flash(f"Exam '{exam_name}' updated successfully.")
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    return render_template('invigilator/edit_exam.html', exam=exam)


@invigilator_routes.route('/invigilator/edit_questions/<int:exam_id>')
@roles_required(('INVIGILATOR',))
def edit_questions(exam_id):
    db = get_db()
    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    return render_template('invigilator/edit_questions.html', exam=exam)


@invigilator_routes.route('/invigilator/delete_exam/<int:exam_id>', methods=['POST'])
@roles_required(('INVIGILATOR',))
def delete_exam(exam_id):
    db = get_db()
    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    # Check if exam has sessions
    sessions = list(db.exam_sessions.find({'exam_id': exam_id}))
    if sessions:
        flash('Cannot delete exam with existing sessions.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    db.exams.delete_one({'_id': exam_id})
    flash(f"Exam '{exam.get('exam_name', exam_id)}' deleted successfully.")
    return redirect(url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/start_exam/<int:exam_id>')
@roles_required(('INVIGILATOR',))
def start_exam_invigilator(exam_id):
    db = get_db()
    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    activate_exam(db, exam_id)

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
        existing = db.exam_sessions.find_one({'candidate_id': cid, 'exam_id': exam_id, 'status': 'STARTED'})
        if not existing:
            create_exam_session(db, cid, exam_id)
            created += 1

    flash(f"Exam '{exam['exam_name']}' started. Session created for {created} student(s) (eligible: {len(eligible_candidate_ids)}, skipped inactive: {skipped_inactive}).")
    return redirect(url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/stop_exam/<int:exam_id>', methods=['POST'])
@roles_required(('INVIGILATOR',))
def stop_exam_invigilator(exam_id):
    db = get_db()
    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))

    now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    db.exams.update_one({'_id': exam_id}, {'$set': {'is_active': False, 'stopped_at': now, 'updated_at': now}})
    db.exam_sessions.update_many(
        {'exam_id': exam_id, 'status': 'STARTED'},
        {'$set': {'status': 'STOPPED', 'end_time': now}},
    )
    flash(f"Exam '{exam['exam_name']}' stopped.")
    return redirect(url_for('invigilator_routes.invigilator_dashboard'))


@invigilator_routes.route('/invigilator/get_questions/<int:exam_id>')
@roles_required(('INVIGILATOR',))
def get_exam_questions(exam_id):
    db = get_db()
    questions = get_questions_for_exam(db, exam_id)
    return jsonify([{'id': q['_id'], 'text': q['question_text'], 'model_answer': q.get('model_answer', '')} for q in questions])


@invigilator_routes.route('/invigilator/add_question', methods=['POST'])
@roles_required(('INVIGILATOR',))
def add_question():
    db = get_db()
    data = request.get_json()
    exam_id = data.get('exam_id', 0)
    text = data.get('text', '').strip()
    model_answer = data.get('model_answer', '').strip()
    if not text or not model_answer:
        return jsonify({'error': 'Both question and answer key are required.'}), 400
    q_id = get_next_id('questions')
    db.questions.insert_one({'_id': q_id, 'exam_id': exam_id, 'question_text': text, 'model_answer': model_answer, 'created_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)})
    return jsonify({'message': 'Question added successfully'})


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
    return jsonify({'message': 'Question deleted successfully'})
