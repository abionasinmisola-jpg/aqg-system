from backend import db
from datetime import datetime


class Result(db.Model):
    __tablename__ = "results"

    id           = db.Column(db.Integer, primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    test_id      = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=False)
    course_id    = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    score        = db.Column(db.Float, nullable=False)
    total        = db.Column(db.Integer, nullable=False)
    percentage   = db.Column(db.Float, nullable=False)
    grade        = db.Column(db.String(5), nullable=False)
    answers      = db.Column(db.Text, nullable=True)  # JSON string of answers
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student      = db.relationship("User", backref="results")
    course       = db.relationship("Course", backref="results")

    def __repr__(self):
        return f"<Result student={self.student_id} test={self.test_id} score={self.percentage}%>"