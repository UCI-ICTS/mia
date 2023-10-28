from flask import render_template
from app import app


@app.route('/admin', methods=['GET'])
def admin():
    return render_template('admin.html')
