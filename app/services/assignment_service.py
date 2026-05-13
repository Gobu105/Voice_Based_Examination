from datetime import datetime, timezone
from app.database.models import get_next_id


def assign_exam_to_candidate(db, candidate_id, exam_id, assigned_by=None):
    if db.exam_assignments.find_one({'candidate_id': candidate_id, 'exam_id': exam_id}):
        return False
    assignment_id = get_next_id('exam_assignments')
    db.exam_assignments.insert_one({
        '_id': assignment_id,
        'candidate_id': candidate_id,
        'exam_id': exam_id,
        'assigned_by': assigned_by,
        'created_at': datetime.now(timezone.utc),
    })
    return True


def assign_examiner_to_candidate(db, examiner_id, candidate_id, exam_id):
    if db.examiner_assignments.find_one({'examiner_id': examiner_id, 'candidate_id': candidate_id, 'exam_id': exam_id}):
        return False
    assignment_id = get_next_id('examiner_assignments')
    db.examiner_assignments.insert_one({
        '_id': assignment_id,
        'examiner_id': examiner_id,
        'candidate_id': candidate_id,
        'exam_id': exam_id,
        'created_at': datetime.now(timezone.utc),
    })
    return True
