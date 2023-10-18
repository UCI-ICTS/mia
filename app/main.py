import json
import os
import shortuuid
from app import app, db
from datetime import datetime
from flask import Flask, request, render_template, jsonify, abort, redirect
from functools import wraps

from app.models.chat import Chat, ChatScriptVersion
from app.models.user import User, UserChatUrl


global chat
global chat_graph
global workflow

# TODO
# 1. check graph keys coming from the user to make sure they are valid
# 2. change id to chat_id
# 3. need some cache or database to store stuff like user responses and workflows
# 4. track all user responses and timestamp it


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
def start_chat(invite_id):
    print('Starting chatbot...')
    global chat
    chat = load_chat()
    #start_id = _get_chat_start_id(chat)
    start_id = 'CPf9CCz'

    global workflow
    workflow = []
    next_chat_sequence = process_workflow(start_id)

    return render_template(template_name_or_list='chat.html', next_chat_sequence=next_chat_sequence)


@app.route('/invite/<uuid:invite_id>/user_response')
@authenticate_user_invite_url
def user_response(invite_id):
    try:
        user_response_id = request.args.get('id')
        echo_user_response = _get_response(user_response_id)

        if chat[user_response_id]['child_ids']:
            next_id = chat[user_response_id]['child_ids'][0]
        else:
            next_id = 'terminal_node'
        next_chat_sequence = process_workflow(next_id)
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

    next_chat_sequence = process_workflow(node_id)
    return jsonify(echo_user_response=echo_user_response, next_sequence=next_chat_sequence)


@app.route('/invite/<uuid:invite_id>/family_enrollment_form', methods=['POST'])
@authenticate_user_invite_url
def family_enrollment_form(invite_id):
    checked_checkboxes = []
    checkbox_workflow_ids = []

    if request.form.get('id_node'):
        parent_id = request.form.get('id_node')
        if parent_id in chat:
            parent_node = chat[parent_id]
        else:
            raise Exception('ERROR: parent id not found in chat script')
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
    generate_workflow(chat, start_node_id, checkbox_workflow_ids)
    next_chat_sequence = process_workflow(start_node_id)

    return jsonify(echo_user_response=checked_checkboxes, next_sequence=next_chat_sequence)


@app.route('/invite/<uuid:invite_id>/child_age_enrollment_form', methods=['POST'])
@authenticate_user_invite_url
def child_age_enrollment_form(invite_id):
    checked_checkboxes = []
    checkbox_workflow_ids = []

    if request.form.get('id_node'):
        parent_id = request.form.get('id_node')
        if parent_id in chat:
            parent_node = chat[parent_id]
        else:
            raise Exception('ERROR: parent id not found in chat script')
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
    generate_workflow(chat, start_node_id, checkbox_workflow_ids)
    next_chat_sequence = process_workflow(start_node_id)

    return jsonify(echo_user_response=checked_checkboxes, next_sequence=next_chat_sequence)


@app.route('/script_builder')
def script_builder():
    global chat_graph
    chat_graph = load_chat()
    return render_template("script_builder.html")


@app.route('/add_message', methods=['POST'])
def add_message():
    new_id = shortuuid.uuid()[:7]
    while new_id in chat_graph:
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

    chat_graph[new_id] = new_message

    # If a parent_ids exists, append the new_id to its child_id list
    if parent_ids and len(chat_graph) > 1:
        for parent_id in parent_ids:
            chat_graph[parent_id]['child_ids'].append(new_id)

    response_data = {
        "id": new_id,
        "type": new_message["type"],
        "messages": new_message["messages"],
        "parent_ids": new_message["parent_ids"]
    }
    return jsonify(response_data)


@app.route('/save_graph', methods=['POST'])
def save_graph():
    # save to a file for easy editing
    with open("chat_graph.json", "w") as file:
        json.dump(chat_graph, file, indent=4)

    # save to the database for safe keeping
    chat_id = '2a15e88e-5458-4078-9956-619cdfcf6030'  # PMGRC Consent ID (it's the only one)
    version = ChatScriptVersion.get_max_version_number(chat_id) + 1
    script = ChatScriptVersion(
        chat_id=chat_id,
        version_number=version,
        script=chat_graph
    )
    db.session.add(script)
    db.session.commit()

    return jsonify({"message": "Chat graph saved successfully!"})


@app.route('/get_saved_chat', methods=['GET'])
def get_saved_chat():
    if os.path.exists('chat_graph.json'):
        with open('chat_graph.json', 'r') as file:
            chat_graph = json.load(file)
        return jsonify(chat_graph)
    else:
        # Return an empty JSON object if the file doesn't exist
        return jsonify({})


@app.route('/admin', methods=['GET'])
def admin():
    return render_template('admin.html')


@app.route('/admin/users', methods=['GET'])
def admin_manage_users():
    users = db.session.query(User, Chat.name).outerjoin(
        ChatScriptVersion, User.chat_script_version_id == ChatScriptVersion.chat_script_version_id).outerjoin(
        Chat, ChatScriptVersion.chat_id == Chat.chat_id).all()
    chat_names = Chat.get_chat_names()
    return render_template('users.html', users=users, chat_names=chat_names)


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
        user.chat_name = request.form.get('chat_name', None)
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
    return jsonify(user.chat_url)


@app.route('/admin/users/delete_user/<string:user_id>', methods=['GET'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect('/admin/users')


def process_workflow(chat_id):
    # check if workflow is already defined because we don't want to overwrite it
    global workflow

    try:
        workflow
    except NameError:
        workflow = []

    # we use workflows to process specific flows within the overall chat (e.g., conditional responses)
    if len(workflow) > 0:
        if chat_id not in workflow[0]:
            chat_id = workflow[0][0]
        if chat_id in workflow[0]:
            print(f"Processing workflow with {chat_id}")
            print(f"Current workflow: {workflow}")
            next_chat_sequence, node_ids = _get_next_chat_sequence(chat_id)
            print(f"node ids to remove: {node_ids} | end_sequence: {next_chat_sequence['end_sequence']}")
            [workflow[0].remove(node_id) for node_id in node_ids
             if chat[chat_id]['metadata'] == chat[node_id]['metadata']]

            # if the "current" workflow array is empty remove it
            if not workflow[0] or next_chat_sequence['end_sequence']:
                workflow.pop(0)
        else:
            raise Exception("ERROR: chat id not found in workflow")
    else:
        next_chat_sequence, node_ids = _get_next_chat_sequence(chat_id)
    return next_chat_sequence


def generate_workflow(chat, start_node_id, user_option_node_ids):
    # generate a sub workflow to dynamically process user responses
    global workflow

    # check if workflow is already defined because we don't want to overwrite it
    try:
        workflow
    except NameError:
        workflow = []

    metadata_field = chat[start_node_id]['metadata']['workflow']
    for user_option_node_id in user_option_node_ids:
        sub_graph = traverse(chat, user_option_node_id, metadata_field)
        workflow.append(sub_graph)
    return workflow


def traverse(chat, start_id, metadata_field):
    sub_graph_nodes = []

    def dfs(node_id):
        # depth-first search
        node = chat.get(node_id, {})
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


def load_chat():
    chat_graph = {}
    if os.path.exists('chat_graph.json'):
        with open('chat_graph.json', 'r') as file:
            chat_graph = json.load(file)
    return chat_graph


def _get_response(node_id):
    if chat[node_id]['html_type'] == 'form':
        response = chat[node_id]['html_content']
    elif chat[node_id]['type'] == 'user':
        response = chat[node_id]['messages'][0]  # there should only be a single message
    else:
        response = chat[node_id]['messages']
    return response


def _get_next_chat_sequence(node_id):
    bot_messages = []
    user_responses = []
    node_ids = []
    queue = [node_id]
    end_sequence = []

    while queue:
        current_node_id = queue.pop(0)
        node = chat.get(current_node_id)

        if 'end_sequence' in node['metadata']:
            end_sequence.append(node['metadata']['end_sequence'])

        if node['type'] == 'bot':
            bot_messages.extend(_get_response(current_node_id))
            queue.extend(node['child_ids'])
        else:
            user_responses.append((current_node_id, _get_response(current_node_id)))
        node_ids.append(current_node_id)

    user_html_type = 'button'
    if len(chat[node_id]['child_ids']) == 1:
        child_id = chat[node_id]['child_ids'][0]
        if chat[child_id]['html_type'] == 'form' and chat[child_id]['type'] == 'user':
            user_html_type = 'form'

    bot_html_type = ''
    bot_html_content = ''
    if chat[node_id]['html_type'] == 'image' and chat[node_id]['type'] == 'bot':
        bot_html_type = 'image'
        bot_html_content = chat[node_id]['html_content']

    data = {
        'bot_messages': bot_messages,
        'user_responses': user_responses,
        'user_html_type': user_html_type,
        'bot_html_type': bot_html_type,
        'bot_html_content': bot_html_content,
        'end_sequence': any(end_sequence)
    }
    print(f"next chat sequence: {data}")
    return data, node_ids


def _get_chat_start_id(chat_graph):
    # find the node in the graph with a parent_id = start
    start_key = ""
    for key in chat_graph:
        if chat_graph[key]['parent_ids'] and chat_graph[key]['parent_ids'][0] == 'start':
            start_key = key
            break

    if start_key:
        return start_key
    else:
        raise Exception("ERROR: chat_graph start key not found")
