from app import app, db
from datetime import datetime
from flask import request, render_template, jsonify, abort
from functools import wraps
from app.models.user import User, UserChatUrl, UserConsent, UserChatCache
from app.models.chat import Chat
from app.utils.utils import (get_script_from_invite_id, get_chat_start_id, process_workflow, get_response,
                             generate_workflow, process_test_question, process_user_consent)
from app.utils.cache import (get_user_workflow, get_user_current_node_id, set_user_workflow, set_user_current_node_id,
                             get_consenting_myself, get_consent_node, set_consenting_myself, set_consenting_children)
from app.utils.enumerations import *


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

    workflow = get_user_workflow(invite_id)
    if workflow is None:
        workflow = []
        set_user_workflow(invite_id, workflow)
    current_node_id = get_user_current_node_id(invite_id)
    if current_node_id is None:
        current_node_id = 'start'

    if current_node_id == 'start':
        start_node_id = get_chat_start_id(conversation_graph)
    else:
        start_node_id = current_node_id

    #############################################################################################
    # FOR TESTING PURPOSES ONLY - DELETE WHEN TESTING IS COMPLETE
    start_node_id = '4bYChBx'
    set_consenting_myself(invite_id, True)  # DELETE IMPORT
    key = f'invite_id:{invite_id}:children_consenting'
    user_chat_cache = db.session.get(UserChatCache, key)
    if user_chat_cache:
        db.session.delete(user_chat_cache)
        db.session.commit()
    set_user_workflow(invite_id, [])
    #############################################################################################

    set_user_current_node_id(invite_id, start_node_id)
    next_chat_sequence = process_workflow(conversation_graph, start_node_id, invite_id)
    return render_template(template_name_or_list='chat.html', next_chat_sequence=next_chat_sequence)


@app.route('/invite/<uuid:invite_id>/user_response')
@authenticate_user_invite_url
def user_response(invite_id):
    try:
        conversation_graph = get_script_from_invite_id(invite_id)
        user_response_node_id = request.args.get('id')
        echo_user_response = get_response(conversation_graph, user_response_node_id)
        node = conversation_graph[user_response_node_id]['metadata']

        # we might override the next node based on various chat specific logic
        if node['workflow'] == 'test_user_understanding':
            next_node_id = process_test_question(conversation_graph, user_response_node_id, invite_id)
        elif node['workflow'] == 'start_consent':
            next_node_id = process_user_consent(conversation_graph, user_response_node_id, invite_id)
        else:
            next_node_id = ''

        if next_node_id == '':
            if conversation_graph[user_response_node_id]['child_ids']:
                next_node_id = conversation_graph[user_response_node_id]['child_ids'][0]
            else:
                next_node_id = 'terminal_node'

        next_chat_sequence = process_workflow(conversation_graph, next_node_id, invite_id)
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


@app.route('/invite/<uuid:invite_id>/save_consent_preferences', methods=['POST'])
@authenticate_user_invite_url
def save_consent_preferences(invite_id):
    conversation_graph = get_script_from_invite_id(invite_id)

    if request.form.get('id_node'):
        parent_id = request.form.get('id_node')
        if parent_id not in conversation_graph:
            raise Exception('ERROR: parent id not found in conversation_graph script')
    else:
        raise Exception('ERROR: parent id not found in user submitted form')

    #TODO can't get the first value because you could be consenting for yourself and
    # your children so how do we know the difference???
    # need consentor_id and consentee_id - something like that

    user_consent = None

    if get_consenting_myself(invite_id):
        user_id = UserChatUrl.query.filter_by(chat_url=str(invite_id)).first().user_id
        user_consent = UserConsent.query.filter_by(user_id=user_id).first()

    if user_consent:
        echo_user_response = ['Submitted preferences']

        if request.form.get('storeSamplesThisStudy'):
            store_sample_this_study = request.form.get('storeSamplesThisStudy') == 'yes'
            user_consent.store_sample_this_study = store_sample_this_study

        if request.form.get('storeSamplesOtherStudies'):
            store_sample_other_studies = request.form.get('storeSamplesOtherStudies') == 'yes'
            user_consent.store_sample_other_studies = store_sample_other_studies

        if request.form.get('storePhiThisStudy'):
            store_phi_this_study = request.form.get('storePhiThisStudy') == 'yes'
            user_consent.store_phi_this_study = store_phi_this_study

        if request.form.get('storePhiOtherStudies'):
            store_phi_other_studies = request.form.get('storePhiOtherStudies') == 'yes'
            user_consent.store_phi_other_studies = store_phi_other_studies

        if request.form.get('rorPrimary'):
            return_primary_results = request.form.get('rorPrimary') == 'yes'
            user_consent.return_primary_results = return_primary_results

        if request.form.get('rorSecondary'):
            return_actionable_secondary_results = request.form.get('rorSecondary') == 'yes'
            user_consent.return_actionable_secondary_results = return_actionable_secondary_results

        if request.form.get('rorSecondaryNot'):
            return_secondary_results = request.form.get('rorSecondaryNot') == 'yes'
            user_consent.return_secondary_results = return_secondary_results

        if request.form.get('fullname'):
            full_name = request.form.get('fullname')
            user_consent.user_full_name_consent = full_name

        if request.form.get('consent'):
            # checkbox checked
            user_consent.consented_at = datetime.utcnow()
            user_consent.consent_statements = CONSENT_STATEMENTS
            user = db.session.get(User, user_id)
            user.consent_complete = True
            echo_user_response = ['I consent to this study']

        db.session.commit()

        next_node_id = process_user_consent(conversation_graph, parent_id, invite_id)
        if next_node_id == '':
            next_node_id = conversation_graph[parent_id]['child_ids'][0]
        next_chat_sequence = process_workflow(conversation_graph, next_node_id, invite_id)
        return jsonify(echo_user_response=echo_user_response, next_sequence=next_chat_sequence)


@app.route('/invite/<uuid:invite_id>/children_enrollment_form', methods=['POST'])
@authenticate_user_invite_url
def children_enrollment_form(invite_id):
    conversation_graph = get_script_from_invite_id(invite_id)

    if request.form.get('id_node'):
        parent_id = request.form.get('id_node')
        if parent_id not in conversation_graph:
            raise Exception('ERROR: parent id not found in conversation_graph script')
    else:
        raise Exception('ERROR: parent id not found in user submitted form')

    if request.form.get('numChildrenEnroll'):
        num_children_to_enroll = int(request.form.get('numChildrenEnroll'))
        user_id = UserChatUrl.query.filter_by(chat_url=str(invite_id)).first().user_id
        user = db.session.get(User, user_id)
        user.num_children_enrolling = num_children_to_enroll
        db.session.commit()

        if num_children_to_enroll <= 3:
            child_text = 'child' if num_children_to_enroll == 1 else 'children'
            echo_user_response = f'Enrolling {num_children_to_enroll} {child_text}'
            child_consent_start_node_id = request.form.get('one-three')

            for i in range(num_children_to_enroll):
                generate_workflow(conversation_graph, child_consent_start_node_id, [child_consent_start_node_id],
                                  invite_id)
        else:
            echo_user_response = 'Enrolling 4 or more children'
            child_consent_start_node_id = request.form.get('four-more')

        next_chat_sequence = process_workflow(conversation_graph, child_consent_start_node_id, invite_id)
        return jsonify(echo_user_response=[echo_user_response], next_sequence=next_chat_sequence)


@app.route('/invite/<uuid:invite_id>/child_sample_health_info_use', methods=['POST'])
@authenticate_user_invite_url
def child_sample_health_info_use_form(invite_id):
    # TODO need to add the corresponding js code
    pass
