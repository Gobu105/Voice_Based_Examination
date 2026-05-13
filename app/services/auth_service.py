import os
import smtplib
import secrets
from datetime import datetime, timezone
from email.message import EmailMessage

from app.database.models import get_db
from app.utils.helpers import _is_active_flag


def verify_session_for_role(role, account):
    if not account:
        return False
    uid = account.get('user_id')
    if uid is None:
        return False
    db = get_db()
    user = db.users.find_one({'_id': uid})
    if not user:
        return False
    is_verified = user.get('email_verified', True)
    return user.get('role') == role and _is_active_flag(user) and is_verified


def generate_verification_token() -> str:
    return secrets.token_urlsafe(24)


def build_email_verification_fields():
    return {
        'email_verified': False,
        'verification_token': generate_verification_token(),
        'verification_sent_at': datetime.now(timezone.utc),
    }


def verify_email_token(token):
    if not token:
        return None
    db = get_db()
    user = db.users.find_one({'verification_token': token})
    if not user:
        return None
    db.users.update_one(
        {'_id': user['_id']},
        {
            '$set': {
                'email_verified': True,
                'verification_token': None,
                'verified_at': datetime.now(timezone.utc),
            }
        },
    )
    user['email_verified'] = True
    user['verification_token'] = None
    user['verified_at'] = datetime.now(timezone.utc)
    return user


def get_email_verification_url(token):
    base = os.environ.get('APP_BASE_URL', 'http://localhost:5005')
    return f"{base.rstrip('/')}/verify_email/{token}"


def send_verification_email(user):
    if not user or 'verification_token' not in user:
        return None
    verification_url = get_email_verification_url(user['verification_token'])
    mail_server = os.environ.get('MAIL_SERVER')
    if not mail_server:
        print('EMAIL VERIFICATION URL:', verification_url)
        return verification_url

    message = EmailMessage()
    message['Subject'] = 'Verify your exam account email'
    message['From'] = os.environ.get('MAIL_FROM', 'no-reply@example.com')
    message['To'] = user.get('email')
    message.set_content(
        f"Hi {user.get('full_name', '')},\n\n"
        f"Please verify your email for the voice exam system by visiting:\n{verification_url}\n\n"
        "If you did not request this, ignore this message.\n"
    )

    port = int(os.environ.get('MAIL_PORT', '587'))
    use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
    username = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')

    try:
        with smtplib.SMTP(mail_server, port, timeout=15) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(message)
        return verification_url
    except Exception as exc:
        print('Failed to send verification email:', exc)
        return verification_url


def logout_current_role():
    from flask import session, redirect, url_for, g

    accounts = session.get('accounts') or {}
    if getattr(g, 'current_role', None):
        accounts.pop(g.current_role, None)
        session['accounts'] = accounts
    return redirect(url_for('auth_routes.show_login'))
