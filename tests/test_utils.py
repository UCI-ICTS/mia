import json
from .Factory.factory_data import SIMPLE_SCRIPT, INVITE_ID
from app.utils.cache import set_user_workflow, get_user_workflow
from app.utils.utils import process_workflow, generate_workflow


def test_process_workflow_simple(app):
    chat_id = 'CaLvKv4'
    script = json.loads(SIMPLE_SCRIPT)
    expected_chat_sequence = {'bot_messages': ['this is part 1 of the first message', 'this is part 2 of the first message'], 'user_responses': [('m84n5MM', 'this is a user message')], 'user_html_type': 'button', 'bot_html_type': '', 'bot_html_content': '', 'end_sequence': True}
    next_chat_sequence = process_workflow(script, chat_id, INVITE_ID)

    assert next_chat_sequence == expected_chat_sequence


def test_generate_workflow(app):
    chat_id = 'm84n5MM'
    script = json.loads(SIMPLE_SCRIPT)
    set_user_workflow(INVITE_ID, [])

    expected_workflow = [['m84n5MM', 'de5ZDgm']]
    workflow = generate_workflow(script, chat_id, [chat_id], INVITE_ID)

    assert len(workflow[0]) == 2
    assert workflow == expected_workflow


def test_process_workflow_with_workflow(app):
    chat_id = 'm84n5MM'
    script = json.loads(SIMPLE_SCRIPT)
    set_user_workflow(INVITE_ID, [])

    expected_chat_sequence = {'bot_messages': [], 'user_responses': [('m84n5MM', 'this is a user message')], 'user_html_type': 'button', 'bot_html_type': '', 'bot_html_content': '', 'end_sequence': True}
    generate_workflow(script, chat_id, [chat_id], INVITE_ID)
    next_chat_sequence = process_workflow(script, chat_id, INVITE_ID)

    assert next_chat_sequence == expected_chat_sequence

    expected_workflow = []
    workflow = get_user_workflow(INVITE_ID)

    assert workflow == expected_workflow





