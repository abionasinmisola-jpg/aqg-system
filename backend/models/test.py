from backend import db
from datetime import datetime


class Test(db.Model):
    __tablename__ = "tests"

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    course_id    = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    lecturer_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bloom_level  = db.Column(db.String(20), nullable=False)
    category     = db.Column(db.String(20), default="test")  
    domain       = db.Column(db.String(20), nullable=False)
    time_limit   = db.Column(db.Integer, default=30)  # in minutes
    is_published = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    lecturer     = db.relationship("User", backref="tests")
    questions    = db.relationship("Question", backref="test", lazy=True, cascade="all, delete-orphan")
    results      = db.relationship("Result", backref="test", lazy=True, cascade="all, delete-orphan")

    def question_count(self):
        return len(self.questions)

    def __repr__(self):
        return f"<Test {self.title}>"