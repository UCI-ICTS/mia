# SQLAlchemy chat model
from app import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid


class Chat(db.Model):
    chat_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    script_versions = db.relationship('ChatScriptVersion', backref='chat', lazy=True)


class ChatScriptVersion(db.Model):
    chat_script_version_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = db.Column(db.String(36), db.ForeignKey('chat.chat_id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    script = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('chat_id', 'version_number', name='_chat_version_uc'),
    )

    @classmethod
    def get_max_version_number(cls, chat_id):
        """
        Get the highest version number for a given chat_id.

        :param chat_id: str, the ID of the chat.
        :return: int, the maximum version number.
        """
        # Use db.func.max to get the highest version_number
        max_version = db.session.query(db.func.max(cls.version_number)).filter_by(chat_id=chat_id).scalar()
        return max_version if max_version is not None else 0
