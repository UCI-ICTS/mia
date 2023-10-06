# SQLAlchemy user model
from app import db
from datetime import datetime, timedelta
from sqlalchemy.ext.hybrid import hybrid_property
import uuid


class User(db.Model):
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    referred_by = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=True)
    consent_complete = db.Column(db.Boolean, default=False, nullable=False)
    enrolling_children = db.Column(db.Boolean, default=False, nullable=False)

    # Establish relationships
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side=[user_id]), lazy=True)
    chat_urls = db.relationship('UserChatUrl', backref='user', lazy=True)

    @hybrid_property
    def chat_url(self):
        for url in self.chat_urls:
            if datetime.utcnow() < url.expires_at:
                return url.chat_url
        return None

    def regenerate_chat_url(self):
        new_chat_url = UserChatUrl()
        self.chat_urls.append(new_chat_url)
        db.session.commit()
        return new_chat_url.chat_url

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        # Append a new UserChatUrl instance to chat_urls when a User is created
        self.chat_urls.append(UserChatUrl())


class UserChatUrl(db.Model):
    chat_url_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_url = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(weeks=1))
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)


# Example queries
# user = User.query.get(some_user_id)
#
# # Iterating over associated UserChatUrl instances
# for chat_url_instance in user.chat_urls:
#     print(chat_url_instance.chat_url)
#
# # Adding a new associated UserChatUrl instance
# new_chat_url_instance = UserChatUrl(user=user)
# user.chat_urls.append(new_chat_url_instance)
#
# # Checking the number of associated UserChatUrl instances
# count = len(user.chat_urls)
