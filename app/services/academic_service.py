from datetime import datetime, timezone

from app.database.models import get_next_id


ACADEMIC_COLLECTIONS = {
    'departments': 'department',
    'subjects': 'subject',
    'academic_years': 'academic_year',
    'semesters': 'semester',
    'exam_types': 'exam_type',
}


def get_academic_context(db):
    return {
        'departments': list(db.departments.find().sort('name', 1)),
        'subjects': list(db.subjects.find().sort('name', 1)),
        'academic_years': list(db.academic_years.find().sort('name', 1)),
        'semesters': list(db.semesters.find().sort('number', 1)),
        'exam_types': list(db.exam_types.find().sort('name', 1)),
    }


def create_academic_item(db, collection_name, data):
    if collection_name not in ACADEMIC_COLLECTIONS:
        raise ValueError('Invalid academic collection.')

    cleaned = {k: v for k, v in data.items() if v not in (None, '')}
    if not cleaned.get('name'):
        raise ValueError('Name is required.')

    existing = db[collection_name].find_one({'name': cleaned['name']})
    if existing:
        raise ValueError(f"{cleaned['name']} already exists.")

    cleaned['_id'] = get_next_id(collection_name)
    cleaned['created_at'] = datetime.now(timezone.utc)
    cleaned['is_active'] = True
    db[collection_name].insert_one(cleaned)
    return cleaned['_id']


def label_for(items, item_id, default='Not set'):
    if not item_id:
        return default
    for item in items:
        if item.get('_id') == item_id:
            return item.get('name', default)
    return default


def enrich_candidate_academic(candidate, context):
    candidate['department_name'] = label_for(context['departments'], candidate.get('department_id'))
    candidate['semester_name'] = label_for(context['semesters'], candidate.get('semester_id'))
    candidate['academic_year_name'] = label_for(context['academic_years'], candidate.get('academic_year_id'))
    return candidate


def enrich_exam_academic(exam, context):
    exam['department_name'] = label_for(context['departments'], exam.get('department_id'))
    exam['subject_name'] = label_for(context['subjects'], exam.get('subject_id'))
    exam['semester_name'] = label_for(context['semesters'], exam.get('semester_id'))
    exam['academic_year_name'] = label_for(context['academic_years'], exam.get('academic_year_id'))
    exam['exam_type_name'] = label_for(context['exam_types'], exam.get('exam_type_id'))
    return exam


def calculate_grade_point(percentage):
    if percentage >= 90:
        return 10
    if percentage >= 80:
        return 9
    if percentage >= 70:
        return 8
    if percentage >= 60:
        return 7
    if percentage >= 50:
        return 6
    if percentage >= 40:
        return 5
    return 0


def build_candidate_semester_results(db, candidate_id, context):
    sessions = list(db.exam_sessions.find({'candidate_id': candidate_id, 'status': 'SUBMITTED'}).sort('submitted_at', -1))
    grouped = {}

    for sess in sessions:
        exam = db.exams.find_one({'_id': sess['exam_id']})
        if not exam:
            continue

        answers = list(db.answers.find({'session_id': sess['_id']}))
        total_marks = sum(a.get('marks', 0) or 0 for a in answers)
        max_marks = max(1, len(answers) * 10)
        percentage = round((total_marks / max_marks) * 100, 2)
        grade_point = calculate_grade_point(percentage)
        semester_id = exam.get('semester_id') or 0

        bucket = grouped.setdefault(semester_id, {
            'semester_id': semester_id,
            'semester_name': label_for(context['semesters'], semester_id, 'Unassigned Semester'),
            'subjects': [],
        })
        bucket['subjects'].append({
            'exam_name': exam.get('exam_name', f"Exam #{exam.get('_id')}"),
            'subject_name': label_for(context['subjects'], exam.get('subject_id'), 'Unassigned Subject'),
            'exam_type_name': label_for(context['exam_types'], exam.get('exam_type_id'), 'Exam'),
            'total_marks': total_marks,
            'max_marks': max_marks,
            'percentage': percentage,
            'grade_point': grade_point,
            'submitted_at': sess.get('submitted_at') or sess.get('end_time'),
        })

    results = []
    for bucket in grouped.values():
        subjects = bucket['subjects']
        bucket['sgpa'] = round(sum(s['grade_point'] for s in subjects) / len(subjects), 2) if subjects else None
        results.append(bucket)

    cgpa_values = [r['sgpa'] for r in results if r['sgpa'] is not None]
    cgpa = round(sum(cgpa_values) / len(cgpa_values), 2) if cgpa_values else None
    return results, cgpa
