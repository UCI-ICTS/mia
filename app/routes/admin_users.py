from flask import request, render_template, jsonify, redirect, Blueprint, current_app
from flask_login import login_required, current_user
from app import db
from app.models.chat import Chat, ChatScriptVersion
from app.models.user import User


admin_users_bp = Blueprint('admin_users', __name__)


@admin_users_bp.before_request
@login_required
def before_request():
    # This will ensure that every request to this blueprint is checked against login_required
    if not current_user.is_authenticated:
        return redirect('auth.login')


@admin_users_bp.route('/', methods=['GET'])
def admin_manage_users():
    users_and_chats = db.session.query(User, Chat.name).outerjoin(
        ChatScriptVersion, User.chat_script_version_id == ChatScriptVersion.chat_script_version_id).outerjoin(
        Chat, ChatScriptVersion.chat_id == Chat.chat_id).all()
    chat_names = Chat.get_chat_names()

    user_data = []
    for user, chat_name in users_and_chats:
        user_data.append({
            'user_id': user.user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone,
            'chat_name': chat_name,
            'consent_complete': user.consent_complete,
            'invite_expired': False if user.chat_url else True,
            'created_at': user.created_at
        })
    return render_template('users.html', users=user_data, chat_names=chat_names)


@admin_users_bp.route('/add_update_user', methods=['POST'])
def add_update_user():
    user_id = request.form.get('user_id', None)
    user = db.session.get(User, user_id)
    # Check if user_id exists. If it does, update the user; otherwise, create a new user.
    if user:
        # Update user attributes
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.phone = request.form.get('phone', None)
    else:
        # Create a new user
        user = User(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            phone=request.form.get('phone', None),
            chat_name=request.form.get('chat_name', None)
        )
        db.session.add(user)
    db.session.commit()
    return redirect('/admin/users')


@admin_users_bp.route('/get_user/<string:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.session.get(User, user_id)
    chat = db.session.get(Chat, user.chat_script_version.chat_id)
    data = {
        'user_id': user.user_id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone,
        'chat_name': chat.name
    }
    return jsonify(data)


@admin_users_bp.route('/get_user_chat_url/<string:user_id>', methods=['GET'])
def get_user_chat_url(user_id):
    user = db.session.get(User, user_id)
    base_url = 'http://' + current_app.config['HOST']

    if user.chat_url:
        data = {
            'text': base_url + '/invite/' + user.chat_url
        }
    else:
        data = {
            'text': 'Invite link expired. Please regenerate a new link'
        }
    return jsonify(data)


@admin_users_bp.route('/generate_new_chat_url/<string:user_id>', methods=['GET'])
def generate_new_chat_url(user_id):
    user = db.session.get(User, user_id)
    user.regenerate_chat_url()
    return redirect('/admin/users')


@admin_users_bp.route('/delete_user/<string:user_id>', methods=['GET'])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect('/admin/users')
