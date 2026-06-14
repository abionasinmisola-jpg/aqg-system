from backend import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    full_name    = db.Column(db.String(120), nullable=False)
    email        = db.Column(db.String(150), unique=True, nullable=False)
    password     = db.Column(db.String(256), nullable=False)
    role         = db.Column(db.String(20), nullable=False)  # 'student' | 'lecturer' | 'admin'
    matric_no    = db.Column(db.String(50), nullable=True)  # students only
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # Lecturer specific
    must_change_password = db.Column(db.Boolean, default=False)
    failed_logins        = db.Column(db.Integer, default=0)
    locked_until         = db.Column(db.DateTime, nullable=True)
    last_login           = db.Column(db.DateTime, nullable=True)

    def set_password(self, plain_password):
        self.password = bcrypt.generate_password_hash(plain_password).decode("utf-8")

    def check_password(self, plain_password):
        return bcrypt.check_password_hash(self.password, plain_password)

    def is_lecturer(self):
        return self.role == "lecturer"

    def is_student(self):
        return self.role == "student"

    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"