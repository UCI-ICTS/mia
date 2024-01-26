from .Factory.factory_data import INVITE_ID
from app.utils.cache import (get_user_workflow, get_consenting_myself, get_consent_node,
                             get_child_user_id, get_child_user_consent_id, get_consenting_children, set_user_workflow,
                             set_consenting_myself, set_consent_node, set_child_user_id,
                             set_child_user_consent_id, set_consenting_children)


def test_get_user_workflow_none(app):
    value = get_user_workflow(INVITE_ID)
    assert value is None


def test_get_consenting_myself_none(app):
    value = get_consenting_myself(INVITE_ID)
    assert value is None


def test_get_consenting_children_none(app):
    value = get_consenting_children(INVITE_ID)
    assert value is None


def test_get_consent_node_none(app):
    value = get_consent_node(INVITE_ID)
    assert value is None


def test_get_child_user_id_none(app):
    value = get_child_user_id(INVITE_ID)
    assert value is None


def test_get_child_user_consent_id_none(app):
    value = get_child_user_consent_id(INVITE_ID)
    assert value is None


def test_set_get_user_workflow_value(app, session_transaction):
    test_value = ['test']
    set_user_workflow(INVITE_ID, test_value)
    value = get_user_workflow(INVITE_ID)
    assert value == test_value


def test_set_get_consenting_myself_value(app):
    test_value = True
    set_consenting_myself(INVITE_ID, test_value)
    value = get_consenting_myself(INVITE_ID)
    assert value == test_value


def test_set_get_consenting_children_value(app):
    test_value = True
    set_consenting_children(INVITE_ID, test_value)
    value = get_consenting_children(INVITE_ID)
    assert value == test_value


def test_set_get_consent_node_value(app):
    test_value = 'EF452Dx'
    set_consent_node(INVITE_ID, test_value)
    value = get_consent_node(INVITE_ID)
    assert value == test_value


def test_set_get_child_user_id_value(app):
    test_value = '23SEsxg'
    set_child_user_id(INVITE_ID, test_value)
    value = get_child_user_id(INVITE_ID)
    assert value == test_value


def test_set_child_user_consent_id_value(app):
    test_value = 'QWxw324'
    set_child_user_consent_id(INVITE_ID, test_value)
    value = get_child_user_consent_id(INVITE_ID)
    assert value == test_value
