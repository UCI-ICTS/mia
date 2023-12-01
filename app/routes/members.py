from flask import request, render_template, jsonify, redirect, Blueprint
from flask_login import login_required, current_user
from app import db
from app.models.members import MemberRoleGroup, Members

member_users_bp = Blueprint('members', __name__)


@member_users_bp.before_request
@login_required
def before_request():
    # This will ensure that every request to this blueprint is checked against login_required
    if not current_user.is_authenticated:
        return redirect('auth.login')


@member_users_bp.route('/', methods=['GET'])
def manage_members():
    members = db.session.query(Members).all()
    return render_template('members.html', members=members, member_role_group=MemberRoleGroup)


@member_users_bp.route('/add_update_member', methods=['POST'])
def add_update_member():
    member_id = request.form.get('member_id', None)
    member = db.session.get(Members, member_id)

    role_group_enum = None
    member_value = request.form['member_role']
    for role in MemberRoleGroup:
        if role.value == member_value:
            role_group_enum = role
            break

    # check if member exists. If it does, update else create new member
    if member:
        # update
        member.full_name = request.form['full_name']
        member.email = request.form['email']
        member.role = role_group_enum
        password = request.form.get('password', None)
        if password:
            member.set_password(password)
    else:
        # create new member
        member = Members(
            full_name=request.form['full_name'],
            email=request.form['email'],
            role=role_group_enum,
            password=request.form['password']
        )
        db.session.add(member)
    db.session.commit()
    return redirect('/admin/members')


@member_users_bp.route('/get_member/<string:member_id>', methods=['GET'])
def get_member(member_id):
    member = db.session.get(Members, member_id)
    data = {
        'member_id': member.member_id,
        'full_name': member.full_name,
        'email': member.email,
        'role': member.role.value
    }
    return jsonify(data)


@member_users_bp.route('delete_member/<string:member_id>', methods=['GET'])
def delete_member(member_id):
    member = db.session.get(Members, member_id)
    if member:
        db.session.delete(member)
        db.session.commit()
    return redirect('/admin/members')
