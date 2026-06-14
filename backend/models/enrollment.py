from backend import db
from datetime import datetime


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id          = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id   = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    status      = db.Column(db.String(20), default="enrolled")  # enrolled | removed
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student     = db.relationship("User", backref="enrollments")

    def __repr__(self):
        return f"<Enrollment student={self.student_id} course={self.course_id}>"