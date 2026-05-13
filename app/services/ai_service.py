import math
import re
from difflib import SequenceMatcher


def score_answer(question_text: str, answer_text: str, model_answer: str) -> int:
    if not answer_text or not answer_text.strip():
        return 0

    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'of', 'in', 'to',
        'and', 'or', 'for', 'with', 'on', 'at', 'by', 'from', 'it', 'its',
        'this', 'that', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
        'what', 'which', 'who', 'how', 'when', 'where', 'why', 'each',
        'every', 'all', 'any', 'give', 'state', 'explain', 'describe',
        'define', 'illustrate', 'example', 'suitable', 'real', 'world',
        'one', 'two', 'three', 'using', 'between', 'them', 'type',
    }

    answer_tokens = [
        t for t in re.findall(r"[A-Za-z0-9']+", answer_text.lower())
        if len(t) > 2 and t not in stop_words
    ]

    if model_answer and model_answer.strip():
        model_tokens = [
            t for t in re.findall(r"[A-Za-z0-9']+", model_answer.lower())
            if len(t) > 2 and t not in stop_words
        ]
        model_set = set(model_tokens)
        answer_set = set(answer_tokens)

        coverage_score = min(6, round((len(model_set & answer_set) / len(model_set)) * 6)) if model_set else 0
        similarity_ratio = SequenceMatcher(None, ' '.join(model_tokens), ' '.join(answer_tokens)).ratio() if model_tokens and answer_tokens else 0
        similarity_score = min(2, round(similarity_ratio * 2))
        model_len = max(1, len(model_answer.split()))
        answer_len = len(answer_text.split())
        length_ratio = answer_len / model_len
        length_score = 2 if length_ratio >= 0.75 else 1 if length_ratio >= 0.4 else 0
        return max(0, min(10, coverage_score + similarity_score + length_score))

    question_tokens = [
        t for t in re.findall(r"[A-Za-z0-9']+", question_text.lower())
        if len(t) > 2 and t not in stop_words
    ]
    keyword_score = min(6, round((len(set(question_tokens) & set(answer_tokens)) / len(question_tokens)) * 6)) if question_tokens else 0
    word_count = len(answer_text.split())
    length_score = min(2, math.ceil((word_count / 50) * 2))
    sentences = [s.strip() for s in re.split(r'[.!?]+', answer_text) if s.strip()]
    structure_score = 2 if len(sentences) >= 2 else 0
    return min(10, keyword_score + length_score + structure_score)
