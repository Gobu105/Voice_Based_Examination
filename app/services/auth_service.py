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
    return user.get('role') == role and _is_active_flag(user)


def logout_current_role():
    from flask import session, redirect, url_for, g
    accounts = session.get('accounts') or {}
    if getattr(g, 'current_role', None):
        accounts.pop(g.current_role, None)
        session['accounts'] = accounts
    return redirect(url_for('auth_routes.show_login'))
