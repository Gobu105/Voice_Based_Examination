import uuid
from flask import g


def assign_request_id():
    request_id = str(uuid.uuid4())
    g.request_id = request_id


def init_app(app):
    app.before_request(assign_request_id)
