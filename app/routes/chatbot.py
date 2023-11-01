from app import app, db
from datetime import datetime
from flask import request, render_template, jsonify, abort
from functools import wraps
from app.models.user import User, UserChatUrl
from app.models.chat import Chat
from app.utils.utils import (get_script_from_invite_id, get_user_conversation_cache, get_chat_start_id,
                             set_user_conversation_cache, process_workflow, get_response, generate_workflow,
                             save_test_question)


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

        # check if current node is part of a test question
        save_test_question(conversation_graph, user_response_id, invite_id)

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