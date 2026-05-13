from flask import Flask
import os

from .database.models import init_app as init_db
from .services.crypto_service import load_master_key
from .routes.auth_routes import auth_routes
from .routes.admin_routes import admin_routes
from .routes.invigilator_routes import invigilator_routes
from .routes.examiner_routes import examiner_routes
from .routes.candidate_routes import candidate_routes


def create_app() -> Flask:
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'secretkey123')

    app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    app.config['MONGO_DB_NAME'] = os.environ.get('MONGO_DB_NAME', 'exam_db')

    init_db(app)
    app._master_key = load_master_key()

    app.register_blueprint(auth_routes)
    app.register_blueprint(admin_routes)
    app.register_blueprint(invigilator_routes)
    app.register_blueprint(examiner_routes)
    app.register_blueprint(candidate_routes)

    return app


app = create_app()
