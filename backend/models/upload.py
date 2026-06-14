from backend import db
from datetime import datetime


class Upload(db.Model):
    __tablename__ = "uploads"

    id            = db.Column(db.Integer, primary_key=True)
    filename      = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_type     = db.Column(db.String(20), nullable=False)
    file_size     = db.Column(db.Integer, nullable=False)
    lecturer_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id     = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    test_id       = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=True)
    uploaded_at   = db.Column(db.DateTime, default=datetime.utcnow)
    status        = db.Column(db.String(20), default="pending")

    lecturer = db.relationship("User", backref="uploads")

    def file_size_readable(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size // 1024} KB"
        else:
            return f"{self.file_size // (1024 * 1024)} MB"

    def __repr__(self):
        return f"<Upload {self.original_name}>"