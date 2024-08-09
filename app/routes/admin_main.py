from flask import render_template, Blueprint
from flask_login import login_required
from app.models.user import User, UserFollowUp
from app.models.chat import Chat

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/', methods=['GET'])
@login_required
def admin():
    # get various counts
    data = {
        'user_followup_count': UserFollowUp.query.filter_by(resolved=False).count(),
        'user_count': User.query.count(),
        'user_consent_complete_count': User.query.filter_by(consent_complete=True).count(),
        'chat_count': Chat.query.count()
    }
    return render_template('admin.html', data=data)
