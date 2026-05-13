from functools import wraps
from flask import g, redirect, url_for


def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if g.current_role != role:
                return redirect(url_for('auth_routes.show_login'))
            return func(*args, **kwargs)
        return wrapper
    return decorator


def roles_required(roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if g.current_role not in roles:
                return redirect(url_for('auth_routes.show_login'))
            return func(*args, **kwargs)
        return wrapper
    return decorator
