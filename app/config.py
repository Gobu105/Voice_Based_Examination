import os


class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'secretkey123')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'exam_db')
    EXAM_MASTER_KEY = os.environ.get('EXAM_MASTER_KEY')
    DEFAULT_EXAM_DURATION_MINUTES = int(os.environ.get('DEFAULT_EXAM_DURATION_MINUTES', '60'))
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME', 'voice_exam_session')
