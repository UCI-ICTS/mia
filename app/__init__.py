from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import models
from app.routes.chatbot import (user_invite, user_response, contact_another_adult_form, family_enrollment_form,
                                child_age_enrollment_form)
from app.routes.admin import admin
from app.routes.admin_users import (admin_manage_users, add_update_user, get_user, get_user_chat_url,
                                    generate_new_chat_url, delete_user)
from app.routes.admin_scripts import (get_scripts, edit_script, add_update_script, add_message, delete_script,
                                      edit_script_content, save_script)
