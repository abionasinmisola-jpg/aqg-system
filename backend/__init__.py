from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address, default_limits=["10000 per day", "1000 per hour"])


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///aqg.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["PERMANENT_SESSION_LIFETIME"] = 1800

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    
    from backend.services.email_service import init_mail
    init_mail(app)

    login_manager.login_view = "auth.student_login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    from backend.routes.auth import auth_bp
    from backend.routes.lecturer import lecturer_bp
    from backend.routes.student import student_bp
    from backend.routes.admin import admin_bp
    from backend.routes.upload import upload_bp
    from backend.routes.course import course_bp
    from backend.routes.student_views import student_views_bp
    from backend.routes.test_route import test_bp
    app.register_blueprint(test_bp)
    from backend.models.upload import Upload
    from backend.models.course import Course
    from backend.models.enrollment import Enrollment
    from backend.models.test import Test
    from backend.models.result import Result
    from backend.models.question import Question

    app.register_blueprint(course_bp)
    app.register_blueprint(student_views_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(lecturer_bp)
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(admin_bp)
    app.register_blueprint(upload_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.student_login"))

    with app.app_context():
        db.create_all()

    return app