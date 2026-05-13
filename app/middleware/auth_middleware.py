from functools import wraps
from flask import session, redirect, url_for, g


def login_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            accounts = session.get('accounts', {})
            account = accounts.get(role)
            if not account or 'user_id' not in account:
                return redirect(url_for('auth_routes.show_login'))
            g.current_user_id = account.get('user_id')
            g.exam_session_id = account.get('exam_session_id')
            return func(*args, **kwargs)
        return wrapper
    return decorator


def load_session():
    accounts = session.get('accounts', {})
    current = accounts.get(getattr(g, 'current_role', None))
    if isinstance(current, dict):
        g.current_user_id = current.get('user_id')
        g.exam_session_id = current.get('exam_session_id')
