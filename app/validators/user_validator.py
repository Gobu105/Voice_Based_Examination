import re

EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')


def validate_registration(full_name, username, email, password, registration_no=None):
    if not full_name or not username or not email or not password:
        return False, 'All required fields must be filled.'
    if not EMAIL_REGEX.match(email):
        return False, 'Please enter a valid email address.'
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long.'
    if registration_no is not None and not str(registration_no).strip():
        return False, 'Registration number is required for candidate accounts.'
    return True, None


def validate_login(username, password):
    if not username or not password:
        return False, 'Username and password are required.'
    return True, None
