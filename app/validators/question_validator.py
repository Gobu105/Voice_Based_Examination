def validate_question_text(text):
    if not text or not text.strip():
        return False, 'Question text cannot be blank.'
    if len(text.strip()) < 10:
        return False, 'Question text should be more descriptive.'
    return True, None


def validate_model_answer(answer):
    if not answer or not answer.strip():
        return False, 'Model answer cannot be blank.'
    return True, None
