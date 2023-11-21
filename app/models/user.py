# SQLAlchemy user model
import uuid, enum

from app import db
from app.models.chat import Chat, ChatScriptVersion
from datetime import datetime, timedelta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Enum


class User(db.Model):
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    referred_by = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=True)
    consent_complete = db.Column(db.Boolean, default=False, nullable=False)
    declined_consent = db.Column(db.Boolean, default=False, nullable=False)
    enrolling_myself = db.Column(db.Boolean, default=False, nullable=False)
    enrolling_children = db.Column(db.Boolean, default=False, nullable=False)
    num_children_enrolling = db.Column(db.Integer, default=0, nullable=False)
    num_test_tries = db.Column(db.Integer, default=1, nullable=True)
    chat_script_version_id = db.Column(db.String(36), db.ForeignKey('chat_script_version.chat_script_version_id'),
                                       nullable=True)
    # Establish relationships
    chat_script_version = db.relationship('ChatScriptVersion', backref='users', lazy=True)
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side=[user_id]), lazy=True)
    chat_urls = db.relationship('UserChatUrl', backref='user', lazy=True, cascade='all, delete')
    user_tests = db.relationship('UserTest', backref='user', lazy=True, cascade='all, delete')
    user_follow_up = db.relationship('UserFollowUp', backref='user', lazy=True, cascade='all, delete')

    # needs more thought...
    # user_consent = db.relationship('UserConsent', backref='user_id', lazy=True, cascade='all, delete')

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

    def __init__(self, chat_name=None, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

        # Assign the latest ChatScriptVersion by chat_name
        if chat_name:
            chat = Chat.query.filter_by(name=chat_name).first()
            if chat:
                version_number = ChatScriptVersion.get_max_version_number(chat.chat_id)
                chat_script_version = ChatScriptVersion.query.filter_by(chat_id=chat.chat_id,
                                                                        version_number=version_number).first()
                if chat_script_version:
                    self.chat_script_version_id = chat_script_version.chat_script_version_id

        # Append a new UserChatUrl instance to chat_urls when a User is created
        new_chat_url = UserChatUrl()
        self.chat_urls.append(new_chat_url)

        db.session.commit()


class UserChatUrl(db.Model):
    chat_url_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_url = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(weeks=1))
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)


class UserChatCache(db.Model):
    key = db.Column(db.String(200), primary_key=True)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<UserChatCache(key='{self.key}', value='{self.value}')>"


class UserTest(db.Model):
    user_test_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    chat_script_version_id = db.Column(db.String(36), db.ForeignKey('chat_script_version.chat_script_version_id'),
                                       nullable=False)
    test_try_num = db.Column(db.Integer, default=1, nullable=True)
    test_question = db.Column(db.String(200), nullable=False)
    user_answer = db.Column(db.String(200), nullable=False)
    answer_correct = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ConsentAgeGroup(enum.Enum):
    LESS_THAN_SIX = "<=6"
    SEVEN_TO_SEVENTEEN = "7-17"
    EIGHTEEN_AND_OVER = ">=18"
    EIGHTEEN_AND_OVER_GUARDIANSHIP = ">=18 guardianship"


class UserConsent(db.Model):
    user_consent_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    dependent_user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=True)
    consent_age_group = db.Column(Enum(ConsentAgeGroup))
    store_sample_this_study = db.Column(db.Boolean, default=True, nullable=False)
    store_sample_other_studies = db.Column(db.Boolean, default=False, nullable=False)
    store_phi_this_study = db.Column(db.Boolean, default=True, nullable=False)
    store_phi_other_studies = db.Column(db.Boolean, default=False, nullable=False)
    return_primary_results = db.Column(db.Boolean, default=False, nullable=False)
    return_actionable_secondary_results = db.Column(db.Boolean, default=False, nullable=False)
    return_secondary_results = db.Column(db.Boolean, default=False, nullable=False)
    consent_statements = db.Column(db.String(2000), default='', nullable=False)
    user_full_name_consent = db.Column(db.String(200), default='', nullable=False)
    child_full_name_consent = db.Column(db.String(200), nullable=True)
    consented_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserFollowUp(db.Model):
    user_follow_up_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    follow_up_reason = db.Column(db.String(200), default='', nullable=False)
    follow_up_info = db.Column(db.String(200), default='', nullable=False)
    resolved = db.Column(db.Boolean, default=False, nullable=False)


class UserFeedback(db.Model):
    user_feedback_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.user_id'), nullable=False)
    satisfaction = db.Column(db.String(25), nullable=True)
    suggestions = db.Column(db.String(2000), nullable=True)


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
