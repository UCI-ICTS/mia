import json
import os
import shortuuid
from app import app, db
from datetime import datetime
from flask import Flask, request, render_template, jsonify, abort
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
    start_id = _get_chat_start_id(chat)
    #start_id = 'CPf9CCz'

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
        print(f"user_response: {next_chat_sequence}")
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
            chat_id = request.form.get('id_submit_node')

        echo_user_response = "Submitted!"
        print(f"""
        --- SAVE THIS TO A DATABASE IN THE FUTURE ---
        first name: {first_name}
        last name: {last_name}
        phone: {phone}
        email: {email}
        """)
    else:
        if request.form.get('id_skip_node'):
            chat_id = request.form.get('id_skip_node')
        echo_user_response = "Let's skip this"

    next_chat_sequence = process_workflow(chat_id)
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

    print(checked_checkboxes)
    print(checkbox_workflow_ids)
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
        "metadata": []
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
    chat_id = '6dbee346-3236-4067-b6a7-7da5da0199bf'  # PMGRC Consent ID (it's the only one)
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


def process_workflow(chat_id):
    # we use workflows to process specific flows within the overall chat (e.g., conditional responses)
    if len(workflow) > 0:
        if chat_id not in workflow[0]:
            chat_id = workflow[0][0]
        if chat_id in workflow[0]:
            print(f"Processing workflow with {chat_id}")
            print(f"Current workflow: {workflow}")
            next_chat_sequence, node_ids = _get_next_chat_sequence(chat_id)
            print(f"node ids to remove: {node_ids}")
            [workflow[0].remove(node_id) for node_id in node_ids
             if chat[chat_id]['metadata'] == chat[node_id]['metadata']]
            if not workflow[0]:
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

    metadata_field = chat[start_node_id]['metadata'][0]
    for user_option_node_id in user_option_node_ids:
        sub_graph = traverse(chat, user_option_node_id, metadata_field)
        workflow.append(sub_graph)
    return workflow


def traverse(chat, start_id, metadata_field):
    sub_graph_nodes = []

    def dfs(node_id):
        # depth-first search
        node = chat.get(node_id, {})
        metadata = node.get("metadata", [])

        if metadata_field:
            if metadata_field not in metadata:
                return sub_graph_nodes

        print(node_id, node)  # Process the node (e.g., print it)
        sub_graph_nodes.append(node_id)

        child_ids = node.get("child_ids", [])
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


def _get_response(id):
    if chat[id]['html_type'] == 'form':
        response = chat[id]['html_content']
    elif chat[id]['type'] == 'user':
        response = chat[id]['messages'][0]  # there should only be a single message
    else:
        response = chat[id]['messages']
    return response


def _get_next_chat_sequence(chat_id):
    bot_messages = []
    user_responses = []
    node_ids = []
    queue = [chat_id]

    while queue:
        current_node_id = queue.pop(0)
        node = chat.get(current_node_id)

        if node['type'] == 'bot':
            bot_messages.extend(_get_response(current_node_id))
            queue.extend(node['child_ids'])
        else:
            user_responses.append((current_node_id, _get_response(current_node_id)))
        node_ids.append(current_node_id)

    user_html_type = 'button'
    if len(chat[chat_id]['child_ids']) == 1:
        child_id = chat[chat_id]['child_ids'][0]
        if chat[child_id]['html_type'] == 'form' and chat[child_id]['type'] == 'user':
            user_html_type = 'form'

    bot_html_type = ''
    bot_html_content = ''
    if chat[chat_id]['html_type'] == 'image' and chat[chat_id]['type'] == 'bot':
        bot_html_type = 'image'
        bot_html_content = chat[chat_id]['html_content']

    data = {
        'bot_messages': bot_messages,
        'user_responses': user_responses,
        'user_html_type': user_html_type,
        'bot_html_type': bot_html_type,
        'bot_html_content': bot_html_content
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
