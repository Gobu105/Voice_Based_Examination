from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from app.database.models import get_db, get_next_id
from app.services.auth_service import build_email_verification_fields, send_verification_email
from app.services.academic_service import get_academic_context, create_academic_item, enrich_candidate_academic, enrich_exam_academic
from app.utils.decorators import role_required
from app.utils.helpers import _is_active_flag, _candidate_and_user, generate_registration_number, is_valid_email
from app.validators import validate_registration

admin_routes = Blueprint('admin_routes', __name__)


@admin_routes.route('/admin/dashboard')
@role_required('ADMIN')
def admin_dashboard():
    db = get_db()
    users = list(db.users.find())
    exams = list(db.exams.find())
    candidates = list(db.candidates.find())
    academic = get_academic_context(db)

    for user in users:
        user['is_active'] = _is_active_flag(user)
    for exam in exams:
        exam['is_active'] = _is_active_flag(exam)
        enrich_exam_academic(exam, academic)
    for candidate in candidates:
        student_user = db.users.find_one({'_id': candidate.get('reg_id')})
        candidate['student_name'] = student_user['full_name'] if student_user else 'Unknown'
        candidate['is_active'] = _is_active_flag(student_user) if student_user else False
        enrich_candidate_academic(candidate, academic)

    examiner_assignments = []
    for a in db.examiner_assignments.find():
        examiner = db.users.find_one({'_id': a['examiner_id']})
        candidate = db.candidates.find_one({'_id': a['candidate_id']})
        student_user = db.users.find_one({'_id': candidate['reg_id']}) if candidate else None
        exam = db.exams.find_one({'_id': a['exam_id']})
        examiner_assignments.append({
            '_id': a['_id'],
            'examiner_name': examiner['full_name'] if examiner else 'Unknown',
            'student_name': student_user['full_name'] if student_user else 'Unknown',
            'registration_no': candidate.get('registration_no', 'N/A') if candidate else 'N/A',
            'exam_name': exam['exam_name'] if exam else 'Unknown',
        })

    invigilator_assignments = []
    for exam in exams:
        inv = db.users.find_one({'_id': exam.get('created_by')})
        if inv:
            invigilator_assignments.append({
                'exam_id': exam['_id'],
                'invigilator_name': inv['full_name'],
                'exam_name': exam['exam_name'],
            })

    return render_template('admin/admin_dashboard.html', users=users, exams=exams, candidates=candidates, examiner_assignments=examiner_assignments, invigilator_assignments=invigilator_assignments, academic=academic)


@admin_routes.route('/admin/create_academic_item/<collection_name>', methods=['POST'])
@role_required('ADMIN')
def admin_create_academic_item(collection_name):
    db = get_db()
    try:
        data = {
            'name': request.form.get('name', '').strip(),
            'code': request.form.get('code', '').strip(),
            'number': int(request.form.get('number', 0) or 0) or None,
            'credits': int(request.form.get('credits', 0) or 0) or None,
            'weightage': int(request.form.get('weightage', 0) or 0) or None,
            'department_id': int(request.form.get('department_id', 0) or 0) or None,
            'semester_id': int(request.form.get('semester_id', 0) or 0) or None,
        }
        create_academic_item(db, collection_name, data)
        flash('Academic item created successfully.')
    except ValueError as exc:
        flash(str(exc))
    return redirect(url_for('admin_routes.admin_dashboard'))


@admin_routes.route('/admin/create_user', methods=['POST'])
@role_required('ADMIN')
def admin_create_user():
    db = get_db()
    full_name = request.form.get('full_name', '').strip()
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    phone = request.form.get('phone_no', '').strip()
    role = request.form.get('role', '').strip()
    registration_no = request.form.get('registration_no', '').strip()
    department_id = int(request.form.get('department_id', 0) or 0) or None
    semester_id = int(request.form.get('semester_id', 0) or 0) or None
    academic_year_id = int(request.form.get('academic_year_id', 0) or 0) or None

    if role not in ('INVIGILATOR', 'EXAMINER', 'CANDIDATE', 'ADMIN'):
        flash('Invalid role selected.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    if not all([full_name, username, email, password]):
        flash('All required fields must be filled.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    if not is_valid_email(email):
        flash('Please enter a valid email address.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    if len(password) < 8:
        flash('Password must be at least 8 characters long.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    registration_value = registration_no if role == 'CANDIDATE' else None
    valid, validation_error = validate_registration(full_name, username, email, password, registration_value)
    if not valid:
        flash(validation_error)
        return redirect(url_for('admin_routes.admin_dashboard'))

    if db.users.find_one({'username': username}):
        flash(f"Username '{username}' already exists.")
        return redirect(url_for('admin_routes.admin_dashboard'))

    if db.users.find_one({'email': email}):
        flash(f"Email '{email}' already exists.")
        return redirect(url_for('admin_routes.admin_dashboard'))

    if role == 'CANDIDATE':
        if not registration_no:
            registration_no = generate_registration_number(db)
        if db.candidates.find_one({'registration_no': registration_no}):
            flash(f"Registration number '{registration_no}' already exists.")
            return redirect(url_for('admin_routes.admin_dashboard'))

    verification_fields = build_email_verification_fields()
    user_id = get_next_id('users')
    db.users.insert_one({
        '_id': user_id,
        'full_name': full_name,
        'username': username,
        'email': email,
        'password_hash': __import__('werkzeug.security', fromlist=['generate_password_hash']).generate_password_hash(password),
        'role': role,
        'is_active': True,
        'email_verified': False,
        'verification_token': verification_fields['verification_token'],
        'verification_sent_at': verification_fields['verification_sent_at'],
        'phone_no': phone or None,
        'created_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
        'session_token': None,
    })

    if role == 'CANDIDATE':
        cand_id = get_next_id('candidates')
        db.candidates.insert_one({
            '_id': cand_id,
            'reg_id': user_id,
            'registration_no': registration_no,
            'department_id': department_id,
            'semester_id': semester_id,
            'academic_year_id': academic_year_id,
        })

    verification_url = send_verification_email({'email': email, 'full_name': full_name, 'verification_token': verification_fields['verification_token']})
    if verification_url:
        flash(f"{role.title()} '{full_name}' created. Verification link: {verification_url}")
    else:
        flash(f"{role.title()} '{full_name}' created successfully. A verification email has been sent.")

    return redirect(url_for('admin_routes.admin_dashboard'))


@admin_routes.route('/admin/toggle_student_status/<int:user_id>', methods=['POST'])
@role_required('ADMIN')
def admin_toggle_student_status(user_id):
    db = get_db()
    user = db.users.find_one({'_id': user_id})
    if not user or user.get('role') != 'CANDIDATE':
        flash('Student not found.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    new_status = not _is_active_flag(user)
    db.users.update_one({'_id': user_id}, {'$set': {'is_active': new_status, 'updated_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc)}})
    flash(f"Student '{user['full_name']}' set to {'Active' if new_status else 'Inactive'}.")
    return redirect(url_for('admin_routes.admin_dashboard'))


@admin_routes.route('/admin/assign_examiner', methods=['POST'])
@role_required('ADMIN')
def admin_assign_examiner():
    db = get_db()
    examiner_id = int(request.form.get('examiner_id', 0))
    candidate_id = int(request.form.get('candidate_id', 0))
    exam_id = int(request.form.get('exam_id', 0))

    examiner = db.users.find_one({'_id': examiner_id, 'role': 'EXAMINER'})
    if not examiner:
        flash('Examiner not found.')
        return redirect(url_for('admin_routes.admin_dashboard'))
    if not _is_active_flag(examiner):
        flash('Cannot assign an inactive examiner.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    candidate, student_user = _candidate_and_user(db, candidate_id)
    if not candidate or not student_user:
        flash('Student not found.')
        return redirect(url_for('admin_routes.admin_dashboard'))
    if not _is_active_flag(student_user):
        flash('Cannot assign an inactive student.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    existing = db.examiner_assignments.find_one({'examiner_id': examiner_id, 'candidate_id': candidate_id, 'exam_id': exam_id})
    if existing:
        flash('This assignment already exists.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    assign_id = get_next_id('examiner_assignments')
    db.examiner_assignments.insert_one({'_id': assign_id, 'examiner_id': examiner_id, 'candidate_id': candidate_id, 'exam_id': exam_id})
    flash('Examiner assigned to student successfully.')
    return redirect(url_for('admin_routes.admin_dashboard'))


@admin_routes.route('/admin/remove_examiner_assignment/<int:assign_id>', methods=['POST'])
@role_required('ADMIN')
def admin_remove_examiner_assignment(assign_id):
    db = get_db()
    db.examiner_assignments.delete_one({'_id': assign_id})
    flash('Examiner assignment removed.')
    return redirect(url_for('admin_routes.admin_dashboard'))


@admin_routes.route('/admin/assign_invigilator', methods=['POST'])
@role_required('ADMIN')
def admin_assign_invigilator():
    db = get_db()
    invigilator_id = int(request.form.get('invigilator_id', 0))
    exam_id = int(request.form.get('exam_id', 0))

    inv = db.users.find_one({'_id': invigilator_id, 'role': 'INVIGILATOR'})
    if not inv:
        flash('Invigilator not found.')
        return redirect(url_for('admin_routes.admin_dashboard'))
    if not _is_active_flag(inv):
        flash('Cannot assign an inactive invigilator.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    exam = db.exams.find_one({'_id': exam_id})
    if not exam:
        flash('Exam not found.')
        return redirect(url_for('admin_routes.admin_dashboard'))

    db.exams.update_one({'_id': exam_id}, {'$set': {'created_by': invigilator_id}})
    flash(f"Invigilator '{inv['full_name']}' assigned to '{exam['exam_name']}'.")
    return redirect(url_for('admin_routes.admin_dashboard'))
