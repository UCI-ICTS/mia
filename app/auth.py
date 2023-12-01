from app import login_manager
from app.models.members import Members


@login_manager.user_loader
def load_user(admin_user_id):
    return Members.query.get(admin_user_id)
