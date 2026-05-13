import logging
from flask import request

logger = logging.getLogger('voice_exam')


def init_app(app):
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    app.before_request(log_request)


def log_request():
    logger.info('%s %s %s', request.remote_addr, request.method, request.path)
