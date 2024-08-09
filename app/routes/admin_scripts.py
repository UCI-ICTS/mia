import shortuuid
import json
import os
from datetime import datetime
from flask import request, render_template, jsonify, redirect, Blueprint, send_file, current_app
from flask_login import login_required, current_user
from app import db
from sqlalchemy.orm.attributes import flag_modified
from app.models.chat import Chat, ChatScriptVersion

VERSION_SCRIPTS = False  # useful for debugging and testing scripts with the same user


admin_scripts_bp = Blueprint('admin_scripts', __name__)


# Use the before_request hook to apply login_required to all routes in the blueprint
@admin_scripts_bp.before_request
@login_required
def before_request():
    # This will ensure that every request to this blueprint is checked against login_required
    if not current_user.is_authenticated:
        return redirect('auth.login')


@admin_scripts_bp.route('/', methods=['GET'])
def get_scripts():
    scripts = db.session.query(Chat).all()
    return render_template('scripts.html', scripts=scripts)


@admin_scripts_bp.route('/edit_script/<string:chat_id>', methods=['GET'])
def edit_script(chat_id):
    script = db.session.get(Chat, chat_id)
    data = {
        'script_id': script.chat_id,
        'script_name': script.name,
        'script_description': script.description
    }
    return jsonify(data)


@admin_scripts_bp.route('/add_update_script', methods=['POST'])
def add_update_script():
    chat_id = request.form.get('script_id', None)
    script = db.session.get(Chat, chat_id)

    if script:
        # update script attributes
        script.name = request.form['script_name']
        script.description = request.form['script_description']
    else:
        # create new script and then a version
        script = Chat(
            name=request.form['script_name'],
            description=request.form['script_description']
        )
        db.session.add(script)
        db.session.commit()

        script_version = ChatScriptVersion(
            chat_id=script.chat_id,
            version_number=0,
            script={}
        )
        db.session.add(script_version)
        db.session.commit()

    return redirect('/admin/scripts')


@admin_scripts_bp.route('/delete_script/<string:chat_id>', methods=['GET'])
def delete_script(chat_id):
    chat = db.session.get(Chat, chat_id)
    if chat:
        db.session.delete(chat)
        db.session.commit()
    return redirect('/admin/scripts')


@admin_scripts_bp.route('/edit_script_content/<string:chat_id>', methods=['GET'])
def edit_script_content(chat_id):
    chat = db.session.get(Chat, chat_id)
    latest_version = ChatScriptVersion.get_max_version_number(chat_id)
    script_version = ChatScriptVersion.query.filter_by(chat_id=chat.chat_id, version_number=latest_version).first()

    if script_version:
        script = script_version.script
    else:
        script = {}

    return render_template('script_editor.html', script=script, chat_id=chat_id, script_name=chat.name)


def preprocess_data(data):
    # Create a mapping of parent IDs to their child nodes
    parent_to_children = {}
    for key, value in data.items():
        for parent_id in value['parent_ids']:
            if parent_id not in parent_to_children:
                parent_to_children[parent_id] = []
            parent_to_children[parent_id].append(key)
    return parent_to_children


@admin_scripts_bp.route('/view_script_content/<string:chat_id>', methods=['GET'])
def view_script_content(chat_id):
    chat = db.session.get(Chat, chat_id)
    latest_version = ChatScriptVersion.get_max_version_number(chat_id)
    script_version = ChatScriptVersion.query.filter_by(chat_id=chat.chat_id, version_number=latest_version).first()

    if script_version:
        script = script_version.script
    else:
        script = {}

    parent_to_children = preprocess_data(script)
    return render_template('view_script.html', script=script, script_name=chat.name,
                           parent_to_children=parent_to_children)


@admin_scripts_bp.route('/edit_script_content/download_script/<string:chat_id>', methods=['POST'])
def download_script(chat_id):
    chat = db.session.get(Chat, chat_id)
    version = ChatScriptVersion.get_max_version_number(chat_id)
    chat_script_version = ChatScriptVersion.query.filter_by(chat_id=str(chat_id), version_number=version).first()
    script = chat_script_version.script
    if chat:
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{chat.name}_{timestamp}.json"

        # Create the full path for the temp_scripts directory
        temp_scripts_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'temp_scripts'))
        os.makedirs(temp_scripts_dir, exist_ok=True)

        # Save to the correct temporary file location
        temp_file_path = os.path.join(temp_scripts_dir, filename)
        with open(temp_file_path, 'w') as file:
            json.dump(script, file, indent=4)

        # Save to the database for safe keeping
        if VERSION_SCRIPTS:
            new_version = version + 1
            new_chat_script_version = ChatScriptVersion(
                chat_id=chat.chat_id,
                version_number=new_version,
                script=script
            )
            db.session.add(new_chat_script_version)
            db.session.commit()

        # Send file to user using the absolute path
        return send_file(temp_file_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({'message': 'Error: script id not found'})


@admin_scripts_bp.route('/edit_script_content/add_message/<string:chat_id>', methods=['POST'])
def add_message(chat_id):
    # get the most recent script
    version = ChatScriptVersion.get_max_version_number(chat_id)
    chat_script_version = db.session.query(ChatScriptVersion).filter(ChatScriptVersion.chat_id == str(chat_id),
                                                                     ChatScriptVersion.version_number == version).first()
    script = chat_script_version.script

    new_id = shortuuid.uuid()[:7]
    while new_id in script:
        new_id = shortuuid.uuid()[:7]

    split_msgs = request.form.get('messages').split('\n')
    messages = [m.strip() for m in split_msgs]
    split_parents = request.form.get('parent_ids').split(',')
    parent_ids = [p.strip() for p in split_parents]
    new_message = {
        "type": request.form.get('type'),
        "messages": messages,
        "parent_ids": parent_ids,
        "child_ids": [],
        "attachment": None,
        "html_type": 'button',
        "html_content": None,
        "metadata": {
            'workflow': '',
            'end_sequence': False
        }
    }

    script[new_id] = new_message

    # If a parent_ids exists, append the new_id to its child_id list
    if parent_ids and len(script) > 1:
        for parent_id in parent_ids:
            script[parent_id]['child_ids'].append(new_id)

    chat_script_version.script = script
    flag_modified(chat_script_version, 'script')
    db.session.commit()

    response_data = {
        "id": new_id,
        "type": new_message["type"],
        "messages": new_message["messages"],
        "parent_ids": new_message["parent_ids"]
    }
    return jsonify(response_data)
