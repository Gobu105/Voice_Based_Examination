def validate_exam_name(exam_name):
    if not exam_name or not exam_name.strip():
        return False, 'Exam name cannot be blank.'
    return True, None


def validate_duration(duration):
    try:
        duration = int(duration)
    except (TypeError, ValueError):
        return False, 'Duration must be a whole number of minutes.'
    if duration <= 0:
        return False, 'Duration must be greater than zero.'
    return True, None
