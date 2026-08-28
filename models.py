from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Complaint(db.Model):
    """Represents a single complaint submitted by a student."""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # One of: Hostel, Mess/Canteen, Academics, Infrastructure, Wi-Fi/IT, Other
    category = db.Column(db.String(50), nullable=False, default="Other")

    location = db.Column(db.String(150), nullable=True)
    submitted_by = db.Column(db.String(100), nullable=True)  # optional / anonymous allowed

    # One of: Open, In Progress, Resolved
    status = db.Column(db.String(20), nullable=False, default="Open")

    # One of: Low, Medium, High
    priority = db.Column(db.String(10), nullable=False, default="Medium")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Complaint {self.id}: {self.title}>"
