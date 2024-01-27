import datetime
import json
import os.path

from datetime import datetime, timedelta
from app import db
from app.models.chat import Chat, ChatScriptVersion
from app.models.user import User, UserChatUrl, UserTest, UserConsent, ConsentAgeGroup, UserFollowUp
from app.utils.cache import (get_user_workflow, set_user_workflow, set_consenting_myself,
                             set_consent_node, get_consent_node, set_consenting_children, get_consenting_children)
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified

# flags
NUM_TEST_QUESTIONS_CORRECT = 10
NUM_TEST_TRIES = 2


def get_script_from_invite_id(invite_id):
    script = db.session.query(ChatScriptVersion.script) \
        .join(User, User.chat_script_version_id == ChatScriptVersion.chat_script_version_id) \
        .join(UserChatUrl, User.user_id == UserChatUrl.user_id) \
        .filter(UserChatUrl.chat_url == str(invite_id)).scalar()

    if script:
        return script
    else:
        raise Exception(f'ERROR: script not found for {invite_id}')


def process_workflow(chat_id, invite_id):
    conversation_graph = get_script_from_invite_id(invite_id)

    # check if workflow is already defined because we don't want to overwrite it
    workflow = get_user_workflow(invite_id)

    # we use workflows to process specific flows within the overall chat (e.g., conditional responses)
    if isinstance(workflow, list) and len(workflow) > 0:
        if chat_id not in workflow[0]:
            chat_id = workflow[0][0]
        if chat_id in workflow[0]:
            next_chat_sequence, node_ids = get_next_chat_sequence(conversation_graph, chat_id)
            [workflow[0].remove(node_id) for node_id in node_ids
             if conversation_graph[chat_id]['metadata'] == conversation_graph[node_id]['metadata']]

            print(f'Workflow: {workflow}')
            # if the "current" workflow array is empty, or we're at the end of a workflow sequence remove it
            if not workflow[0] or next_chat_sequence['end_sequence']:
                workflow.pop(0)
                set_user_workflow(invite_id, workflow)
        else:
            raise Exception("ERROR: chat id not found in sequence")
    else:
        next_chat_sequence, node_ids = get_next_chat_sequence(conversation_graph, chat_id)

        if next_chat_sequence['user_html_type'] == 'button':
            # this hack prevents the conversation from restarting at a form, video, or image input. this is necessary
            # because the rendering template assumes you start with buttons. we use javascript to render other html
            # elements dynamically with the browser.
            set_user_current_node_id(invite_id, node_ids[0])
    return next_chat_sequence


def generate_workflow(start_node_id, user_option_node_ids, invite_id):
    conversation_graph = get_script_from_invite_id(invite_id)

    # generate a sub workflow to dynamically process user responses
    workflow = get_user_workflow(invite_id)

    metadata_field = conversation_graph[start_node_id]['metadata']['workflow']
    for user_option_node_id in user_option_node_ids:
        sub_graph = traverse(conversation_graph, user_option_node_id, metadata_field)
        workflow.append(sub_graph)
    set_user_workflow(invite_id, workflow)
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


def process_user_consent(conversation_graph, current_node_id, invite_id):
    node = conversation_graph[current_node_id]['metadata']
    if node['workflow'] in ['start_consent', 'end_consent']:
        user_id = UserChatUrl.query.filter_by(chat_url=str(invite_id)).first().user_id
        user = db.session.get(User, user_id)

        # first we check if you're enrolling yourself and do that first
        if user.enrolling_myself and user.consent_complete is False:
            # create user consent db entry
            adult = ConsentAgeGroup.EIGHTEEN_AND_OVER
            user_consent = UserConsent(
                user_id=user.user_id,
                consent_age_group=adult
            )
            db.session.add(user_consent)
            db.session.commit()
            set_consenting_myself(invite_id, True)
            set_consent_node(invite_id, current_node_id)
            return node['enrolling_myself_node_id']

        # then we'll check if you're enrolling children
        elif user.enrolling_children:
            set_consenting_myself(invite_id, False)
            if get_consenting_children(invite_id) is None:
                set_consenting_children(invite_id, True)
                consent_node_id = get_consent_node(invite_id)
                node = conversation_graph[consent_node_id]['metadata']
                return node['enrolling_children_node_id']

    elif node['workflow'] == 'decline_consent':
        user_id = UserChatUrl.query.filter_by(chat_url=str(invite_id)).first().user_id
        user = db.session.get(User, user_id)

        user.declined_consent = True
        db.session.commit()

    return ''


def process_test_question(conversation_graph, current_node_id, invite_id):
    node = conversation_graph[current_node_id]['metadata']
    if node['workflow'] == 'test_user_understanding':
        user_id = UserChatUrl.query.filter_by(chat_url=str(invite_id)).first().user_id
        user = db.session.get(User, user_id)
        chat_script_version_id = db.session.get(User, user.user_id).chat_script_version.chat_script_version_id
        save_test_question(conversation_graph, current_node_id, user, chat_script_version_id)
        if node['end_sequence'] is True:
            result = get_test_results(user, chat_script_version_id)
            if result != NUM_TEST_QUESTIONS_CORRECT:
                if user.num_test_tries < NUM_TEST_TRIES:
                    # retry
                    user.num_test_tries += 1
                    db.session.commit()
                    return node['retry_node_id']
                else:
                    # fail, contact someone
                    return node['fail_node_id']
            else:
                # passed the test
                return node['pass_node_id']
    return ''


def save_test_question(conversation_graph, current_node_id, user, chat_script_version_id):
    node = conversation_graph[current_node_id]
    if 'test_question_answer_correct' in node['metadata'] and node['type'] == 'user':
        parent_id = node['parent_ids'][0]
        parent_node = conversation_graph[parent_id]
        if 'test_question' in parent_node['metadata'] and parent_node['metadata']['test_question'] is True:
            test_question = parent_node['messages'][0]
            user_answer = node['messages'][0]
            answer_correct = node['metadata']['test_question_answer_correct']
            print(f'test question: {test_question}')
            print(f'user answer: {user_answer}')

            user_test_result = UserTest(
                user_id=user.user_id,
                chat_script_version_id=chat_script_version_id,
                test_try_num=user.num_test_tries,
                test_question=test_question,
                user_answer=user_answer,
                answer_correct=answer_correct
            )
            db.session.add(user_test_result)
            db.session.commit()
    else:
        return


def get_test_results(user, chat_script_version_id):
    test_try = user.num_test_tries
    user_results = (
        db.session.query(func.count(UserTest.answer_correct))
        .filter(UserTest.user_id == user.user_id, UserTest.chat_script_version_id == chat_script_version_id,
                UserTest.test_try_num == test_try, UserTest.answer_correct == True)
        .group_by(UserTest.user_id, UserTest.chat_script_version_id)
        .scalar()
    )
    return user_results


def create_follow_up_with_user(invite_id, reason, more_info):
    user_id = UserChatUrl.query.filter_by(chat_url=str(invite_id)).first().user_id
    user_follow_up = UserFollowUp(
        user_id=user_id,
        follow_up_reason=reason,
        follow_up_info=more_info
    )
    db.session.add(user_follow_up)
    db.session.commit()


def clean_up_after_chat(invite_id):
    # set the chat url to expire in 24 hrs
    user_chat_url = UserChatUrl.query.filter_by(chat_url=str(invite_id)).first()
    user_chat_url.expires_at = datetime.utcnow() + timedelta(hours=24)
    db.session.commit()


def _replace_db_script_with_json(chat_name, json_file):
    # helper method for editing the json script directly and then uploading to the database
    chat = Chat.query.filter_by(name=chat_name).first()
    version = ChatScriptVersion.get_max_version_number(chat.chat_id)
    chat_script_version = ChatScriptVersion.query.filter_by(chat_id=chat.chat_id, version_number=version).first()

    if os.path.exists(json_file):
        with open(json_file, 'r') as file:
            new_script = json.load(file)

    chat_script_version.script = new_script
    flag_modified(chat_script_version, 'script')

    db.session.commit()
    print('Saved!')
