from flask import request, render_template, jsonify, redirect, Blueprint
from flask_login import login_required, current_user
from app import db
from app.models.chat import Chat, ChatScriptVersion
from app.models.user import User, UserFollowUp


admin_follow_up_bp = Blueprint('admin_follow_up', __name__)


@admin_follow_up_bp.before_request
@login_required
def before_request():
    # This will ensure that every request to this blueprint is checked against login_required
    if not current_user.is_authenticated:
        return redirect('auth.login')


@admin_follow_up_bp.route('/', methods=['GET'])
def admin_follow_up():
    user_follow_up_query = db.session.query(User, Chat.name, UserFollowUp).join(
        UserFollowUp, User.user_id == UserFollowUp.user_id).outerjoin(
        ChatScriptVersion, User.chat_script_version_id == ChatScriptVersion.chat_script_version_id).outerjoin(
        Chat, ChatScriptVersion.chat_id == Chat.chat_id).all()

    user_data = []
    for user, chat_name, user_follow_up in user_follow_up_query:
        user_data.append({
            'user_follow_up_id': user_follow_up.user_follow_up_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone,
            'chat_name': chat_name,
            'reason': user_follow_up.follow_up_reason,
            'more_info': user_follow_up.follow_up_info,
            'resolved': user_follow_up.resolved,
            'created_at': user.created_at
        })
    return render_template('follow_up.html', users=user_data)


@admin_follow_up_bp.route('/resolve/<string:user_follow_up_id>', methods=['GET'])
def resolve_user_follow_up(user_follow_up_id):
    user_follow_up = db.session.get(UserFollowUp, user_follow_up_id)
    if user_follow_up:
        user_follow_up.resolved = True
        db.session.commit()
    return redirect('/admin/follow_up')
