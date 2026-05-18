from datetime import datetime, timezone
from app.database.models import get_next_id
from app.utils.helpers import _is_active_flag
from .crypto_service import encrypt_exam_key, generate_exam_key


def get_exam_by_id(db, exam_id):
    return db.exams.find_one({'_id': exam_id})


def create_exam(db, name, duration, creator_id, master_key, academic_data=None):
    exam_key = generate_exam_key()
    ciphertext, iv, tag = encrypt_exam_key(exam_key, master_key)
    exam_id = get_next_id('exams')
    payload = {
        '_id': exam_id,
        'exam_name': name,
        'duration': duration,
        'total_marks': 100,
        'is_active': False,
        'created_by': creator_id,
        'created_at': datetime.now(timezone.utc),
        'enc_key_ciphertext': ciphertext,
        'enc_key_iv': iv,
        'enc_key_tag': tag,
    }
    if academic_data:
        payload.update({k: v for k, v in academic_data.items() if v})
    db.exams.insert_one(payload)
    return exam_id


def activate_exam(db, exam_id):
    db.exams.update_many({}, {'$set': {'is_active': False}})
    db.exams.update_one({'_id': exam_id}, {'$set': {'is_active': True, 'updated_at': datetime.now(timezone.utc)}})


def get_questions_for_exam(db, exam_id):
    return list(db.questions.find({'exam_id': exam_id}))


def is_active_exam(exam):
    return _is_active_flag(exam)
