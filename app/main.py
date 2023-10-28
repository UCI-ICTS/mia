import json
import os
import shortuuid
from app import app, db
from datetime import datetime
from flask import Flask, request, render_template, jsonify, abort, redirect
from functools import wraps
from sqlalchemy.orm.attributes import flag_modified

from app.models.chat import Chat, ChatScriptVersion
from app.models.user import User, UserChatUrl, UserConversationCache

# flags
VERSION_SCRIPTS = False  # useful for debugging and testing scripts with the same user


def authenticate_user_invite_url(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        invite_id = kwargs.get('invite_id')

        if invite_id is None:
            print("invite_id is not provided")
            abort(400)  # Bad request

        # Use invite_id to query the database and check expiration.
        chat_url_instance = UserChatUrl.query.filter_by(chat_url=str(invite_id)).filter(
            UserChatUrl.expires_at > datetime.utcnow()).first()

        if chat_url_instance is None:
            print("User invite id not found in the database")
            abort(404)  # Not found or expired

        print(f"User authenticated {invite_id}")
        return func(*args, **kwargs)

    return decorated_function


# define routes
@app.route('/invite/<uuid:invite_id>/')
@authenticate_user_invite_url
def user_invite(invite_id):
    print(f'Starting conversation for invite id {invite_id}')
    conversation_graph = get_script_from_invite_id(invite_id)
    workflow, current_node_id = get_user_conversation_cache(invite_id)
    if current_node_id == 'start':
        start_node_id = get_chat_start_id(conversation_graph)
    else:
        start_node_id = current_node_id
    #start_node_id = 'CPf9CCz' # '8Z6qtgu'
    set_user_conversation_cache(invite_id, workflow, start_node_id)
    next_chat_sequence = process_workflow(conversation_graph, start_node_id, invite_id)
    return render_template(template_name_or_list='chat.html', next_chat_sequence=next_chat_sequence)


@app.route('/invite/<uuid:invite_id>/user_response')
@authenticate_user_invite_url
def user_response(invite_id):
    try:
        conversation_graph = get_script_from_invite_id(invite_id)
        user_response_id = request.args.get('id')
        echo_user_response = get_response(conversation_graph, user_response_id)

        if conversation_graph[user_response_id]['child_ids']:
            next_id = conversation_graph[user_response_id]['child_ids'][0]
        else:
            next_id = 'terminal_node'
        next_chat_sequence = process_workflow(conversation_graph, next_id, invite_id)
        return jsonify(echo_user_response=echo_user_response, next_sequence=next_chat_sequence)
    except Exception as e:
        print(f"Error: {e}")


@app.route('/invite/<uuid:invite_id>/contact_another_adult_form', methods=['POST'])
@authenticate_user_invite_url
def contact_another_adult_form(invite_id):
    first_name, last_name, phone, email = '', '', '', ''
    submitted = request.form.get('submit') == 'true'

    if submitted:
        if request.form.get('firstname'):
            first_name = request.form.get('firstname')
        if request.form.get('lastname'):
            last_name = request.form.get('lastname')
        if request.form.get('phone'):
            phone = request.form.get('phone')
        if request.form.get('email'):
            email = request.form.get('email')
        if request.form.get('id_submit_node'):
            node_id = request.form.get('id_submit_node')

        user_chat_url = UserChatUrl.query.filter_by(chat_url=str(invite_id)).first()
        user = db.session.get(User, user_chat_url.user_id)
        user_chat = db.session.get(Chat, user.chat_script_version.chat_id)
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            chat_name=user_chat.name,
            referred_by=user.user_id
        )
        db.session.add(new_user)
        db.session.commit()
        echo_user_response = "Submitted!"
    else:
        if request.form.get('id_skip_node'):
            node_id = request.form.get('id_skip_node')
        echo_user_response = "Let's skip this"

    conversation_graph = get_script_from_invite_id(invite_id)
    next_chat_sequence = process_workflow(conversation_graph, node_id, invite_id)
    return jsonify(echo_user_response=echo_user_response, next_sequence=next_chat_sequence)


@app.route('/invite/<uuid:invite_id>/family_enrollment_form', methods=['POST'])
@authenticate_user_invite_url
def family_enrollment_form(invite_id):
    conversation_graph = get_script_from_invite_id(invite_id)
    checked_checkboxes = []
    checkbox_workflow_ids = []

    if request.form.get('id_node'):
        parent_id = request.form.get('id_node')
        if parent_id in conversation_graph:
            parent_node = conversation_graph[parent_id]
        else:
            raise Exception('ERROR: parent id not found in conversation_graph script')
    else:
        raise Exception('ERROR: parent id not found in user submitted form')

    # For each checkbox in the form, check if it was checked and get the node id
    if request.form.get('myself'):
        checked_checkboxes.append('Myself')
        checkbox_workflow_ids.append(request.form.get('id_myself'))

    if request.form.get('childOtherParent'):
        checked_checkboxes.append("My child's other parent")
        checkbox_workflow_ids.append(request.form.get('id_childOtherParent'))

    if request.form.get('adultFamilyMember'):
        checked_checkboxes.append('Another adult family member')
        checkbox_workflow_ids.append(request.form.get('id_adultFamilyMember'))

    if request.form.get('myChildChildren'):
        checked_checkboxes.append('My child/children')
        checkbox_workflow_ids.append(request.form.get('id_myChildChildren'))

    # as of python 3.7, dict preserve order, so we can filter duplicate nodes while preserving order
    checkbox_workflow_ids = list(dict.fromkeys(checkbox_workflow_ids))

    # check that ids are children ids of the parent node
    if not all([i in parent_node['child_ids'] for i in checkbox_workflow_ids]):
        raise Exception('ERROR: child id not found in parent id for user submitted form')

    start_node_id = checkbox_workflow_ids[0]
    generate_workflow(conversation_graph, start_node_id, checkbox_workflow_ids, invite_id)
    next_chat_sequence = process_workflow(conversation_graph, start_node_id, invite_id)

    return jsonify(echo_user_response=checked_checkboxes, next_sequence=next_chat_sequence)


@app.route('/invite/<uuid:invite_id>/child_age_enrollment_form', methods=['POST'])
@authenticate_user_invite_url
def child_age_enrollment_form(invite_id):
    conversation_graph = get_script_from_invite_id(invite_id)
    checked_checkboxes = []
    checkbox_workflow_ids = []

    if request.form.get('id_node'):
        parent_id = request.form.get('id_node')
        if parent_id in conversation_graph:
            parent_node = conversation_graph[parent_id]
        else:
            raise Exception('ERROR: parent id not found in conversation_graph script')
    else:
        raise Exception('ERROR: parent id not found in user submitted form')

    # For each checkbox in the form, check if it was checked and get the node id
    if request.form.get('ageSixOrLess'):
        checked_checkboxes.append('6 years or younger')
        checkbox_workflow_ids.append(request.form.get('id_ageSixOrLess'))

    if request.form.get('ageSevenToSeventeen'):
        checked_checkboxes.append('7-17 years')
        checkbox_workflow_ids.append(request.form.get('id_ageSevenToSeventeen'))

    if request.form.get('eighteenOrOlder'):
        checked_checkboxes.append('18 years or older')
        checkbox_workflow_ids.append(request.form.get('id_eighteenOrOlder'))

    # check that ids are children ids of the parent node
    if not all([i in parent_node['child_ids'] for i in checkbox_workflow_ids]):
        raise Exception('ERROR: child id not found in parent id for user submitted form')

    start_node_id = checkbox_workflow_ids[0]
    generate_workflow(conversation_graph, start_node_id, checkbox_workflow_ids, invite_id)
    next_chat_sequence = process_workflow(conversation_graph, start_node_id, invite_id)

    return jsonify(echo_user_response=checked_checkboxes, next_sequence=next_chat_sequence)


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


@app.route('/admin', methods=['GET'])
def admin():
    return render_template('admin.html')


@app.route('/admin/users', methods=['GET'])
def admin_manage_users():
    users_and_chats = db.session.query(User, Chat.name).outerjoin(
        ChatScriptVersion, User.chat_script_version_id == ChatScriptVersion.chat_script_version_id).outerjoin(
        Chat, ChatScriptVersion.chat_id == Chat.chat_id).all()
    chat_names = Chat.get_chat_names()

    user_data = []
    for user, chat_name in users_and_chats:
        user_data.append({
            'user_id': user.user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone,
            'chat_name': chat_name,
            'consent_complete': user.consent_complete,
            'invite_expired': False if user.chat_url else True,
            'created_at': user.created_at
        })
    return render_template('users.html', users=user_data, chat_names=chat_names)


@app.route('/admin/users/add_update_user', methods=['POST'])
def add_update_user():
    user_id = request.form.get('user_id', None)
    user = db.session.get(User, user_id)
    # Check if user_id exists. If it does, update the user; otherwise, create a new user.
    if user:
        # Update user attributes
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.phone = request.form.get('phone', None)
    else:
        # Create a new user
        user = User(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            phone=request.form.get('phone', None),
            chat_name=request.form.get('chat_name', None)
        )
        db.session.add(user)

    # Commit the session to save changes to the database
    db.session.commit()

    return redirect('/admin/users')


@app.route('/admin/users/get_user/<string:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.session.get(User, user_id)
    chat = db.session.get(Chat, user.chat_script_version.chat_id)
    data = {
        'user_id': user.user_id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone,
        'chat_name': chat.name
    }
    return jsonify(data)


@app.route('/admin/users/get_user_chat_url/<string:user_id>', methods=['GET'])
def get_user_chat_url(user_id):
    user = db.session.get(User, user_id)
    if user.chat_url:
        data = {
            'expired': False,
            'text': user.chat_url
        }
    else:
        data = {
            'expired': True,
            'text': 'Invite link expired. Please regenerate a new link'
        }
    return jsonify(data)


@app.route('/admin/users/generate_new_chat_url/<string:user_id>', methods=['GET'])
def generate_new_chat_url(user_id):
    user = db.session.get(User, user_id)
    user.regenerate_chat_url()
    return redirect('/admin/users')


@app.route('/admin/users/delete_user/<string:user_id>', methods=['GET'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect('/admin/users')


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


def process_workflow(conversation_graph, chat_id, invite_id):
    # check if workflow is already defined because we don't want to overwrite it
    workflow, _ = get_user_conversation_cache(invite_id)

    # we use workflows to process specific flows within the overall chat (e.g., conditional responses)
    if len(workflow) > 0:
        if chat_id not in workflow[0]:
            chat_id = workflow[0][0]
        if chat_id in workflow[0]:
            print(f"Processing workflow with {chat_id}")
            print(f"Current workflow: {workflow}")
            next_chat_sequence, node_ids = get_next_chat_sequence(conversation_graph, chat_id)
            print(f"node ids to remove: {node_ids} | end_sequence: {next_chat_sequence['end_sequence']}")
            [workflow[0].remove(node_id) for node_id in node_ids
             if conversation_graph[chat_id]['metadata'] == conversation_graph[node_id]['metadata']]

            # if the "current" workflow array is empty, or we're at the end of a workflow sequence remove it
            if not workflow[0] or next_chat_sequence['end_sequence']:
                workflow.pop(0)
                set_user_conversation_cache(invite_id, workflow, None)
            print(f"workflow: {workflow}")
        else:
            raise Exception("ERROR: chat id not found in workflow")
    else:
        next_chat_sequence, node_ids = get_next_chat_sequence(conversation_graph, chat_id)

        if next_chat_sequence['user_html_type'] == 'button':
            # this hack prevents the conversation from restarting at a form, video, or image input. this is necessary
            # because the rendering template assumes you start with buttons. we use javascript to render other html
            # elements dynamically with the browser.
            set_user_conversation_cache(invite_id, None, node_ids[0])
    return next_chat_sequence


def generate_workflow(conversation_graph, start_node_id, user_option_node_ids, invite_id):
    # generate a sub workflow to dynamically process user responses
    workflow, _ = get_user_conversation_cache(invite_id)

    metadata_field = conversation_graph[start_node_id]['metadata']['workflow']
    for user_option_node_id in user_option_node_ids:
        sub_graph = traverse(conversation_graph, user_option_node_id, metadata_field)
        workflow.append(sub_graph)

    set_user_conversation_cache(invite_id, workflow, None)
    return workflow


def traverse(conversation_graph, start_id, metadata_field):
    sub_graph_nodes = []

    def dfs(node_id):
        # depth-first search
        node = conversation_graph.get(node_id, {})
        metadata = node.get('metadata', {})

        if metadata_field and 'workflow' in metadata:
            if metadata_field != metadata['workflow']:
                return sub_graph_nodes

        print(node_id, node)  # Process the node (e.g., print it)
        sub_graph_nodes.append(node_id)

        child_ids = node.get('child_ids', [])
        for child_id in child_ids:
            dfs(child_id)

    dfs(start_id)
    return sub_graph_nodes


def get_script_from_invite_id(invite_id):
    script = db.session.query(ChatScriptVersion.script) \
        .join(User, User.chat_script_version_id == ChatScriptVersion.chat_script_version_id) \
        .join(UserChatUrl, User.user_id == UserChatUrl.user_id) \
        .filter(UserChatUrl.chat_url == str(invite_id)).scalar()

    if script:
        return script
    else:
        raise Exception(f'ERROR: script not found for {invite_id}')


def get_response(conversation_graph, node_id):
    if conversation_graph[node_id]['html_type'] == 'form':
        response = conversation_graph[node_id]['html_content']
    elif conversation_graph[node_id]['type'] == 'user':
        response = conversation_graph[node_id]['messages'][0]  # there should only be a single message
    else:
        response = conversation_graph[node_id]['messages']
    return response


def get_next_chat_sequence(conversation_graph, node_id):
    bot_messages = []
    user_responses = []
    node_ids = []
    queue = [node_id]
    end_sequence = []

    while queue:
        current_node_id = queue.pop(0)
        node = conversation_graph.get(current_node_id)

        if 'end_sequence' in node['metadata']:
            end_sequence.append(node['metadata']['end_sequence'])

        if node['type'] == 'bot':
            bot_messages.extend(get_response(conversation_graph, current_node_id))
            queue.extend(node['child_ids'])
        else:
            user_responses.append((current_node_id, get_response(conversation_graph, current_node_id)))
        node_ids.append(current_node_id)

    user_html_type = 'button'
    if len(conversation_graph[node_id]['child_ids']) == 1:
        child_id = conversation_graph[node_id]['child_ids'][0]
        if conversation_graph[child_id]['html_type'] == 'form' and conversation_graph[child_id]['type'] == 'user':
            user_html_type = 'form'

    bot_html_type = ''
    bot_html_content = ''
    if conversation_graph[node_id]['html_type'] in ['image', 'video'] and conversation_graph[node_id]['type'] == 'bot':
        bot_html_type = conversation_graph[node_id]['html_type']
        bot_html_content = conversation_graph[node_id]['html_content']

    data = {
        'bot_messages': bot_messages,
        'user_responses': user_responses,
        'user_html_type': user_html_type,
        'bot_html_type': bot_html_type,
        'bot_html_content': bot_html_content,
        'end_sequence': any(end_sequence)
    }
    print(f"next chat sequence: {data}")
    print(f"chat sequence node ids: {node_ids}")
    return data, node_ids


def get_chat_start_id(conversation_graph):
    # find the node in the graph with a parent_id = start
    start_node = ""
    for node_id in conversation_graph:
        if conversation_graph[node_id]['parent_ids'] and conversation_graph[node_id]['parent_ids'][0] == 'start':
            start_node = node_id
            break

    if start_node:
        return start_node
    else:
        raise Exception("ERROR: conversation_graph start key not found")


def get_user_conversation_cache(invite_id):
    user_conversation_cache = db.session.query(UserConversationCache).join(UserChatUrl).\
        filter(UserChatUrl.chat_url == str(invite_id)).first()
    workflow = json.loads(user_conversation_cache.workflow)
    current_node_id = user_conversation_cache.current_node_id
    return workflow, current_node_id


def set_user_conversation_cache(invite_id, workflow=None, current_node_id=None):
    user_conversation_cache = db.session.query(UserConversationCache).join(UserChatUrl).\
        filter(UserChatUrl.chat_url == str(invite_id)).first()

    if workflow is not None:
        user_conversation_cache.workflow = json.dumps(workflow)
    if current_node_id is not None:
        user_conversation_cache.current_node_id = current_node_id

    db.session.commit()
