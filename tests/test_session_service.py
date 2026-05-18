from datetime import datetime, timezone

from app.services import session_service


class FakeCollection:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        self.documents.append(document)

    def update_one(self, filter_query, update):
        for document in self.documents:
            if document.get("_id") == filter_query.get("_id"):
                document.update(update.get("$set", {}))

    def find_one(self, query):
        for document in self.documents:
            match = True
            for key, value in query.items():
                if document.get(key) != value:
                    match = False
                    break
            if match:
                return document
        return None


class FakeDB:
    def __init__(self):
        self.exam_sessions = FakeCollection()


def test_create_complete_and_get_active_session(monkeypatch):
    monkeypatch.setattr(session_service, "get_next_id", lambda _: 101)
    db = FakeDB()

    session_id = session_service.create_exam_session(db, candidate_id=55, exam_id=77)
    assert session_id == 101

    active = session_service.get_active_session(db, 55, 77)
    assert active is not None
    assert active["status"] == "STARTED"
    assert active["candidate_id"] == 55
    assert active["exam_id"] == 77

    completed = session_service.complete_exam_session(db, session_id)
    assert completed["status"] == "SUBMITTED"
    assert completed["end_time"] is not None
    assert completed["submitted_at"] is not None


def test_get_active_session_returns_none_when_no_session_exists():
    db = FakeDB()
    assert session_service.get_active_session(db, 1, 2) is None
