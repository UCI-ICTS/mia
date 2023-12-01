from flask import render_template, Blueprint
from flask_login import login_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/', methods=['GET'])
@login_required
def admin():
    return render_template('admin.html')
