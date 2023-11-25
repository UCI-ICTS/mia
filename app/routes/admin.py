from flask import render_template, Blueprint


admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/', methods=['GET'])
def admin():
    return render_template('admin.html')
