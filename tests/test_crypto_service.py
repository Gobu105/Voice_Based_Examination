import base64
import os
from datetime import datetime, timezone

from app.services import crypto_service


def test_generate_master_key_returns_base64_string():
    key = crypto_service.generate_master_key()
    assert isinstance(key, str)

    decoded = base64.urlsafe_b64decode(key)
    assert len(decoded) == 32


def test_encrypt_and_decrypt_exam_key_roundtrip():
    master_key = os.urandom(32)
    exam_key = crypto_service.generate_exam_key()

    ciphertext, iv, tag = crypto_service.encrypt_exam_key(exam_key, master_key)
    assert ciphertext != exam_key
    assert len(iv) == 12
    assert len(tag) == 16

    decrypted = crypto_service.decrypt_exam_key(ciphertext, iv, tag, master_key)
    assert decrypted == exam_key


def test_encrypt_and_decrypt_answer_roundtrip():
    exam_key = crypto_service.generate_exam_key()
    plaintext = "This is a secure answer."

    ciphertext, iv, tag = crypto_service.encrypt_answer(plaintext, exam_key)
    assert ciphertext != plaintext.encode("utf-8")
    assert len(iv) == 12
    assert len(tag) == 16

    decrypted = crypto_service.decrypt_answer(ciphertext, iv, tag, exam_key)
    assert decrypted == plaintext


def test_compute_and_verify_integrity_hash():
    master_key = os.urandom(32)
    timestamp = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    digest = crypto_service.compute_integrity_hash(
        master_key,
        "answer text",
        question_id=10,
        session_id=20,
        timestamp=timestamp,
    )

    assert crypto_service.verify_integrity_hash(
        master_key,
        "answer text",
        question_id=10,
        session_id=20,
        timestamp=timestamp,
        expected_hash=digest,
    )

    assert not crypto_service.verify_integrity_hash(
        master_key,
        "wrong answer",
        question_id=10,
        session_id=20,
        timestamp=timestamp,
        expected_hash=digest,
    )


def test_compute_integrity_hash_normalizes_timestamp_microseconds_and_tzinfo():
    master_key = os.urandom(32)
    timestamp_tz = datetime(2025, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
    timestamp_naive = timestamp_tz.replace(tzinfo=None)

    digest_tz = crypto_service.compute_integrity_hash(
        master_key,
        "answer text",
        question_id=10,
        session_id=20,
        timestamp=timestamp_tz,
    )
    digest_naive = crypto_service.compute_integrity_hash(
        master_key,
        "answer text",
        question_id=10,
        session_id=20,
        timestamp=timestamp_naive,
    )

    assert digest_tz == digest_naive
