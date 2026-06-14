from backend import db
from datetime import datetime


class Question(db.Model):
    __tablename__ = "questions"

    id                    = db.Column(db.Integer, primary_key=True)
    test_id               = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=True)
    lecturer_id           = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id             = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    question_text         = db.Column(db.Text, nullable=False)
    option_a              = db.Column(db.String(500), nullable=True)
    option_b              = db.Column(db.String(500), nullable=True)
    option_c              = db.Column(db.String(500), nullable=True)
    option_d              = db.Column(db.String(500), nullable=True)             
    correct_answer        = db.Column(db.String(200), nullable=False)  # 'A'/'B'/'C'/'D' for MCQ, the lowercase word for fill  # A B C D
    bloom_level           = db.Column(db.String(20), nullable=False)
    domain                = db.Column(db.String(20), nullable=False)
    question_type         = db.Column(db.String(20), default="mcq")  # mcq | fill
    llm_used              = db.Column(db.String(50), nullable=True)  # gpt4o | gemini | deepseek
    verification_status   = db.Column(db.String(20), default="pending")  # verified | warning | failed
    verification_message  = db.Column(db.Text, nullable=True)
    bloom_aligned         = db.Column(db.Boolean, default=False)
    is_approved           = db.Column(db.Boolean, default=False)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    lecturer              = db.relationship("User", backref="questions")
    course                = db.relationship("Course", backref="questions")

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question_text,
            "options": {
                "A": self.option_a,
                "B": self.option_b,
                "C": self.option_c,
                "D": self.option_d
            },
            "answer": self.correct_answer,
            "bloom_level": self.bloom_level,
            "domain": self.domain,
            "verification_status": self.verification_status,
            "verification_message": self.verification_message,
            "bloom_aligned": self.bloom_aligned,
            "is_approved": self.is_approved
        }

    def __repr__(self):
        return f"<Question {self.id} [{self.bloom_level}] [{self.domain}]>"