import shortuuid, json

from flask import request, render_template, jsonify, redirect
from app import app, db
from sqlalchemy.orm.attributes import flag_modified
from app.models.chat import Chat, ChatScriptVersion

VERSION_SCRIPTS = False  # useful for debugging and testing scripts with the same user


@app.route('/admin/scripts', methods=['GET'])
def get_scripts():
    scripts = db.session.query(Chat).all()
    return render_template('scripts.html', scripts=scripts)


@app.route('/admin/scripts/edit_script/<string:chat_id>', methods=['GET'])
def edit_script(chat_id):
    script = db.session.get(Chat, chat_id)
    data = {
        'script_id': script.chat_id,
        'script_name': script.name,
        'script_description': script.description
    }
    return jsonify(data)


@app.route('/admin/scripts/add_update_script', methods=['POST'])
def add_update_script():
    chat_id = request.form.get('script_id', None)
    script = db.session.get(Chat, chat_id)

    if script:
        # update script attributes
        script.name = request.form['script_name']
        script.description = request.form['script_description']
    else:
        # create new script
        script = Chat(
            name=request.form['script_name'],
            description=request.form['script_description']
        )
        db.session.add(script)

    # commit the session to save the changes to the database
    db.session.commit()
    return redirect('/admin/scripts')


@app.route('/admin/scripts/delete_script/<string:chat_id>', methods=['GET'])
def delete_script(chat_id):
    chat = db.session.get(Chat, chat_id)
    if chat:
        db.session.delete(chat)
        db.session.commit()
    return redirect('/admin/scripts')


@app.route('/admin/scripts/edit_script_content/<string:chat_id>', methods=['GET'])
def edit_script_content(chat_id):
    chat = db.session.get(Chat, chat_id)
    latest_version = ChatScriptVersion.get_max_version_number(chat_id)
    script_version = ChatScriptVersion.query.filter_by(chat_id=chat.chat_id, version_number=latest_version).first()

    if script_version:
        script = script_version.script
    else:
        script = {}

    return render_template('script_editor.html', script=script, chat_id=chat_id, script_name=chat.name)


@app.route('/admin/scripts/edit_script_content/save_script/<string:chat_id>', methods=['POST'])
def save_script(chat_id):
    chat = db.session.get(Chat, chat_id)
    version = ChatScriptVersion.get_max_version_number(chat_id)
    chat_script_version = ChatScriptVersion.query.filter_by(chat_id=str(chat_id), version_number=version).first()
    script = chat_script_version.script

    if chat:
        # save to a file for easy editing
        with open(chat.name + '.json', 'w') as file:
            json.dump(script, file, indent=4)

        # save to the database for safe keeping
        if VERSION_SCRIPTS:
            new_version = version + 1
            new_chat_script_version = ChatScriptVersion(
                chat_id=chat.chat_id,
                version_number=new_version,
                script=script
            )
            db.session.add(new_chat_script_version)
            db.session.commit()

        return jsonify({'message': 'Chat graph saved successfully!'})
    else:
        return jsonify({'message': 'Error: script id not found'})


@app.route('/admin/scripts/edit_script_content/add_message/<string:chat_id>', methods=['POST'])
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

    print(f'script: {script}')
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
