import re
import math
import random
from datetime import datetime, timezone

try:
    import language_tool_python
except ImportError:
    language_tool_python = None

_grammar_tool = None
if language_tool_python is not None:
    try:
        _grammar_tool = language_tool_python.LanguageTool('en-US')
    except Exception:
        _grammar_tool = None


def _is_active_flag(doc):
    if not doc:
        return False
    return doc.get('is_active', False) is True


def _candidate_and_user(db, candidate_id):
    candidate = db.candidates.find_one({'_id': candidate_id})
    if not candidate:
        return None, None
    user = db.users.find_one({'_id': candidate['reg_id']})
    return candidate, user


def get_active_exam(db):
    return db.exams.find_one({'is_active': True})


def ensure_examiner_assignment(db, candidate_id, exam_id):
    existing = db.examiner_assignments.find_one({'candidate_id': candidate_id, 'exam_id': exam_id})
    if existing:
        return existing

    prior = db.examiner_assignments.find_one({'candidate_id': candidate_id}, sort=[('_id', 1)])
    examiner_id = prior.get('examiner_id') if prior else None

    if examiner_id is None:
        examiner_user = db.users.find_one({'role': 'EXAMINER', 'is_active': True}, sort=[('_id', 1)])
        if not examiner_user:
            return None
        examiner_id = examiner_user['_id']

    result = db.counters.find_one_and_update(
        {'_id': 'examiner_assignments'},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=__import__('pymongo').ReturnDocument.AFTER,
    )
    assign_id = result['seq']
    assignment = {
        '_id': assign_id,
        'examiner_id': examiner_id,
        'candidate_id': candidate_id,
        'exam_id': exam_id,
        'auto_assigned': True,
        'created_at': datetime.now(timezone.utc),
    }
    db.examiner_assignments.insert_one(assignment)
    return assignment


def normalize_answer(question_text, answer_text):
    text = ' '.join(str(answer_text or '').strip().split())
    if not text:
        return text

    text = re.sub(r'im', "I'm", text, flags=re.IGNORECASE)
    text = re.sub(r'i', 'I', text)

    fillers_pattern = r'(um+|uh+|erm|like|you know|sort of|kind of)'
    text = re.sub(fillers_pattern, '', text, flags=re.IGNORECASE)
    text = ' '.join(text.split())

    words = text.split()
    for idx in range(len(words) - 1):
        if words[idx].lower() in ('a', 'an'):
            next_word = re.sub(r'[^A-Za-z]', '', words[idx + 1])
            if next_word:
                starts_vowel = next_word[0].lower() in 'aeiou'
                if words[idx].lower() == 'a' and starts_vowel:
                    words[idx] = 'an'
                elif words[idx].lower() == 'an' and not starts_vowel:
                    words[idx] = 'a'
    text = ' '.join(words)

    if text:
        text = text[0].upper() + text[1:]
    text = re.sub(r'(?<=[\.\!\?]\s)([a-z])', lambda m: m.group(1).upper(), text)

    if text and text[-1] not in '.!?':
        text += '.'

    if question_text and 'capital of' in question_text.lower():
        text = text.title()

    if _grammar_tool is not None:
        try:
            matches = _grammar_tool.check(text)
            text = language_tool_python.utils.correct(text, matches)
        except Exception:
            pass

    return text


def format_datetime_for_display(dt):
    if not dt:
        return '-'
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime('%d %b %Y, %I:%M %p UTC')


EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')


def is_valid_email(email):
    if not email:
        return False
    return EMAIL_REGEX.match(email) is not None


def generate_registration_number(db, prefix='STU'):
    for _ in range(25):
        candidate_code = datetime.now(timezone.utc).strftime('%y%m%d')
        suffix = f"{random.randint(1000, 9999)}"
        reg_no = f"{prefix}-{candidate_code}-{suffix}"
        if not db.candidates.find_one({'registration_no': reg_no}):
            return reg_no
    raise RuntimeError('Unable to generate a unique registration number. Try again.')
