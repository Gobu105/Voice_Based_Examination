from typing import Iterable


def compute_total_marks(answers: Iterable[dict]) -> int:
    return sum(a.get('marks', 0) or 0 for a in answers)
