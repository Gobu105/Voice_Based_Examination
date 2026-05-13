from app.database.models import get_next_id
from app.utils.helpers import normalize_answer


def get_candidate_for_user(db, user_id):
    return db.candidates.find_one({'reg_id': user_id})


def get_candidate_by_registration(db, registration_no):
    return db.candidates.find_one({'registration_no': registration_no})


def build_candidate_answer(question_text, answer_text):
    normalized = normalize_answer(question_text, answer_text)
    return {'original_answer': answer_text, 'normalized_answer': normalized}


def create_candidate_user_payload(full_name, username, email, password_hash, phone_no=None):
    return {
        'full_name': full_name,
        'username': username,
        'email': email,
        'password_hash': password_hash,
        'role': 'CANDIDATE',
        'is_active': True,
        'phone_no': phone_no,
    }
