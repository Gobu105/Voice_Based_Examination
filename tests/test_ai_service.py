from app.services.ai_service import score_answer


def test_score_answer_empty_answer_returns_zero():
    assert score_answer("What is the capital of India?", "   ", "Model answer") == 0


def test_score_answer_with_model_answer_returns_reasonable_score():
    score = score_answer(
        "Explain the solution.",
        "The correct solution explains the core concept clearly.",
        "The correct solution explains the core concept clearly.",
    )

    assert isinstance(score, int)
    assert 0 <= score <= 10
    assert score >= 5


def test_score_answer_question_keyword_scoring():
    score = score_answer(
        "What is the capital of France?",
        "Paris is the capital of France.",
        "",
    )
    assert score > 0
    assert score <= 10
