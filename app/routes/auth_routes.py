from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, flash, jsonify, g
from app.database.models import get_db
from app.services.auth_service import (
    verify_session_for_role,
    logout_current_role,
    verify_email_token,
    send_verification_email,
)


auth_routes = Blueprint('auth_routes', __name__)


def get_request_role(path, args):
    if path in ('/', '/login', '/logout', '/exam/submitted', '/go') or path.startswith('/static/'):
        return None
    if path.startswith('/candidate'):
        return 'CANDIDATE'
    if path.startswith('/admin'):
        return 'ADMIN'
    if path.startswith('/invigilator'):
        return 'INVIGILATOR'
    if path.startswith('/examiner'):
        return 'EXAMINER'
    if path.startswith('/api/'):
        if path == '/api/session_check':
            role = (args.get('role') or '').strip().upper()
            if role in {'ADMIN', 'INVIGILATOR', 'EXAMINER', 'CANDIDATE'}:
                return role
        return 'CANDIDATE'
    return None


@auth_routes.before_app_request
def enforce_single_session():
    role = get_request_role(request.path, request.args)
    if role is None:
        return None

    accounts = session.get('accounts') or {}
    account = accounts.get(role)
    if account is None:
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({'error': 'session_expired'}), 401
        return redirect(url_for('auth_routes.show_login'))

    if not verify_session_for_role(role, account):
        accounts.pop(role, None)
        session['accounts'] = accounts
        flash('Your session is no longer valid. Please log in again.')
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({'error': 'session_expired'}), 401
        return redirect(url_for('auth_routes.show_login'))

    g.current_user_id = account['user_id']
    g.current_role = role
    g.exam_session_id = account.get('exam_session_id') if role == 'CANDIDATE' else None


@auth_routes.route('/')
def index():
    return redirect(url_for('auth_routes.show_login'))


@auth_routes.route('/login', methods=['GET'])
def show_login():
    return render_template('shared/login.html')


@auth_routes.route('/login', methods=['POST'])
def login():
    db = get_db()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    user = db.users.find_one({'username': username})
    if not user:
        flash('Invalid username or password')
        return redirect(url_for('auth_routes.show_login'))

    if not user.get('password_hash'):
        flash('Invalid username or password')
        return redirect(url_for('auth_routes.show_login'))

    from werkzeug.security import check_password_hash
    if not check_password_hash(user['password_hash'], password):
        flash('Invalid username or password')
        return redirect(url_for('auth_routes.show_login'))

    if user.get('is_active', True) is False:
        flash('Your account is inactive. Please contact an administrator.')
        return redirect(url_for('auth_routes.show_login'))

    if user.get('email_verified') is False:
        verification_url = send_verification_email(user)
        if verification_url:
            flash(f'Email verification required. Verification link: {verification_url}')
        else:
            flash('Email verification required. Please ask your administrator to resend the verification link.')
        return redirect(url_for('auth_routes.show_login'))

    accounts = session.get('accounts') or {}
    accounts[user['role']] = {'user_id': user['_id']}
    if user['role'] == 'CANDIDATE':
        accounts[user['role']]['exam_session_id'] = None
    session['accounts'] = accounts

    if user['role'] == 'INVIGILATOR':
        return redirect(url_for('invigilator_routes.invigilator_dashboard'))
    if user['role'] == 'CANDIDATE':
        return redirect(url_for('candidate_routes.candidate_dashboard'))
    if user['role'] == 'ADMIN':
        return redirect(url_for('admin_routes.admin_dashboard'))
    if user['role'] == 'EXAMINER':
        return redirect(url_for('examiner_routes.examiner_dashboard'))

    return redirect(url_for('auth_routes.show_login'))


@auth_routes.route('/go')
def go_to_dashboard():
    accounts = session.get('accounts') or {}
    for role in ('ADMIN', 'INVIGILATOR', 'EXAMINER', 'CANDIDATE'):
        acc = accounts.get(role)
        if acc and verify_session_for_role(role, acc):
            if role == 'INVIGILATOR':
                return redirect(url_for('invigilator_routes.invigilator_dashboard'))
            if role == 'CANDIDATE':
                return redirect(url_for('candidate_routes.candidate_dashboard'))
            if role == 'ADMIN':
                return redirect(url_for('admin_routes.admin_dashboard'))
            if role == 'EXAMINER':
                return redirect(url_for('examiner_routes.examiner_dashboard'))
    return redirect(url_for('auth_routes.show_login'))


@auth_routes.route('/verify_email/<token>')
def verify_email(token):
    user = verify_email_token(token)
    if not user:
        flash('Verification link is invalid or expired.')
        return redirect(url_for('auth_routes.show_login'))

    flash(f"Email verified for {user.get('full_name', 'your account')}. You may now log in.")
    return redirect(url_for('auth_routes.show_login'))


@auth_routes.route('/candidate/logout')
def candidate_logout():
    return logout_current_role()


@auth_routes.route('/invigilator/logout')
def invigilator_logout():
    return logout_current_role()


@auth_routes.route('/admin/logout')
def admin_logout():
    return logout_current_role()


@auth_routes.route('/examiner/logout')
def examiner_logout():
    return logout_current_role()


@auth_routes.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_routes.show_login'))
