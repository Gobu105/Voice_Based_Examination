from datetime import datetime, timezone
from app.database.models import get_next_id


def create_exam_session(db, candidate_id, exam_id):
    session_id = get_next_id('exam_sessions')
    now = datetime.now(timezone.utc)
    db.exam_sessions.insert_one({
        '_id': session_id,
        'exam_id': exam_id,
        'candidate_id': candidate_id,
        'start_time': now,
        'end_time': None,
        'status': 'STARTED',
    })
    return session_id


def complete_exam_session(db, session_id):
    now = datetime.now(timezone.utc)
    db.exam_sessions.update_one({'_id': session_id}, {'$set': {'status': 'SUBMITTED', 'end_time': now, 'submitted_at': now}})
    return db.exam_sessions.find_one({'_id': session_id})


def get_active_session(db, candidate_id, exam_id):
    return db.exam_sessions.find_one({'candidate_id': candidate_id, 'exam_id': exam_id, 'status': 'STARTED'})
