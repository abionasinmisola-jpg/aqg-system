from backend import db
from datetime import datetime


class Course(db.Model):
    __tablename__ = "courses"

    id          = db.Column(db.Integer, primary_key=True)
    code        = db.Column(db.String(20), unique=True, nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    domain      = db.Column(db.String(20), nullable=False)  # mathematics | programming
    lecturer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_available = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    lecturer    = db.relationship("User", backref="courses")
    enrollments = db.relationship("Enrollment", backref="course", lazy=True, cascade="all, delete-orphan")
    tests       = db.relationship("Test", backref="course", lazy=True, cascade="all, delete-orphan")

    def enrolled_count(self):
        return len([e for e in self.enrollments if e.status == "enrolled"])

    def __repr__(self):
        return f"<Course {self.code} - {self.title}>"