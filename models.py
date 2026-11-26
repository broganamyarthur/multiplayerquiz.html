"""Database models for the quiz app."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Question(db.Model):
    """One multiple-choice quiz question."""

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(300), nullable=False)
    options = db.Column(db.JSON, nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(500))
    category = db.Column(db.String(50))

    def to_dict(self):
        """Return the question as a dictionary, ready to send as JSON."""
        return {
            "id": self.id,
            "text": self.text,
            "options": self.options,
            "answer": self.answer,
            "image": self.image,
            "category": self.category,
        }