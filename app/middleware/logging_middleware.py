import logging
import os
from flask import request

logger = logging.getLogger('voice_exam')


def init_app(app):
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        file_handler = logging.FileHandler(os.path.join(logs_dir, 'app.log'))
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    app.before_request(log_request)


def log_request():
    logger.info('%s %s %s', request.remote_addr, request.method, request.path)
