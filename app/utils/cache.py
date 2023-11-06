import json

from app import db
from app.models.user import UserChatCache


def get_user_workflow(invite_id):
    key = f'invite_id:{invite_id}:workflow'
    user_chat_cache = db.session.query(UserChatCache).get(key)
    if user_chat_cache:
        value = user_chat_cache.value
        return json.loads(value)
    else:
        return None


def set_user_workflow(invite_id, workflow):
    key = f'invite_id:{invite_id}:workflow'
    user_chat_cache = db.session.query(UserChatCache).get(key)
    if user_chat_cache:
        user_chat_cache.value = json.dumps(workflow)
    else:
        user_chat_cache = UserChatCache(key=key, value=json.dumps(workflow))
        db.session.add(user_chat_cache)
    db.session.commit()


def get_user_current_node_id(invite_id):
    key = f'invite_id:{invite_id}:current_node_id'
    user_chat_cache = db.session.query(UserChatCache).get(key)
    if user_chat_cache:
        value = user_chat_cache.value
        return value
    else:
        return None


def set_user_current_node_id(invite_id, current_node_id):
    key = f'invite_id:{invite_id}:current_node_id'
    user_chat_cache = db.session.query(UserChatCache).get(key)
    if user_chat_cache:
        user_chat_cache.value = current_node_id
    else:
        user_chat_cache = UserChatCache(key=key, value=current_node_id)
        db.session.add(user_chat_cache)
    db.session.commit()
