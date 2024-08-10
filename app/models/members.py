import enum
import uuid
from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum


class MemberRoleGroup(enum.Enum):
    ADMIN = 'admin'
    MEMBER = 'member'


class Members(UserMixin, db.Model):
    member_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)  # this is hashed
    role = db.Column(Enum(MemberRoleGroup), default=MemberRoleGroup.MEMBER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, **kwargs):
        super(Members, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])

    def get_id(self):
        return self.member_id

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
