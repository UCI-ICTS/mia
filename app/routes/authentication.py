from flask import render_template, redirect, url_for, request, Blueprint
from flask_login import login_user, login_required, logout_user
from app.models.members import Members

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # In a real app, use hashed passwords
        member = Members.query.filter_by(email=email).first()
        if member and member.check_password(password):
            login_user(member)
            return redirect('/admin')
        else:
            return 'Invalid username or password'
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')
