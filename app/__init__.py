from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config, DevConfig


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_type='Config'):
    app = Flask(__name__)

    if config_type == 'DevConfig':
        app.config.from_object(DevConfig)
    else:
        app.config.from_object(Config)

    from app.auth import load_user

    from app.routes.chatbot import invite_bp
    from app.routes.admin_main import admin_bp
    from app.routes.admin_scripts import admin_scripts_bp
    from app.routes.admin_users import admin_users_bp
    from app.routes.authentication import auth_bp
    from app.routes.members import member_users_bp
    from app.routes.admin_follow_up import admin_follow_up_bp

    app.register_blueprint(invite_bp, url_prefix='/invite')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(admin_scripts_bp, url_prefix='/admin/scripts')
    app.register_blueprint(admin_users_bp, url_prefix='/admin/users')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(member_users_bp, url_prefix='/admin/members')
    app.register_blueprint(admin_follow_up_bp, url_prefix='/admin/follow_up')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    return app


# these are at the bottom to avoid circular imports
from app import models
from app.routes.chatbot import (user_invite, user_response, contact_another_adult_form, family_enrollment_form,
                                child_age_enrollment_form)
from app.routes.admin_main import admin
from app.routes.admin_users import (admin_manage_users, add_update_user, get_user, get_user_chat_url,
                                    generate_new_chat_url, delete_user)
from app.routes.admin_scripts import (get_scripts, edit_script, add_update_script, add_message, delete_script,
                                      edit_script_content, save_script)


