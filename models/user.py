from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()


class User(db.Model):
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    referred_by = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=True)
    chat_url = db.Column(db.String(255), nullable=True)
    consent_complete = db.Column(db.Boolean, default=False, nullable=False)
    enrolling_children = db.Column(db.Boolean, default=False, nullable=False)

    # Establish relationships
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side=[user_id]), lazy=True)


class UserResponse(db.Model):
    response_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_history = db.Column(db.JSON, nullable=False)
    current_chat_id = db.Column(db.String(36), db.ForeignKey('chat.chat_id'), nullable=False)

    # Foreign key relationships, if needed
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)

    # Establish relationships
    user = db.relationship('User', backref='responses', lazy=True)
