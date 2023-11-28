# holds factory data for tests

INVITE_ID = '56a475ee-45cc-4872-8749-619ae0eb7592'

SIMPLE_SCRIPT = """{
    "CaLvKv4": {
        "type": "bot",
        "messages": [
            "this is part 1 of the first message",
            "this is part 2 of the first message"
        ],
        "parent_ids": [
            "start"
        ],
        "child_ids": [
            "m84n5MM"
        ],
        "attachment": null,
        "html_type": "button",
        "html_content": null,
        "metadata": {
            "workflow": "",
            "end_sequence": "false"
        }
    },
    "m84n5MM": {
        "type": "user",
        "messages": [
            "this is a user message"
        ],
        "parent_ids": [
            "CaLvKv4"
        ],
        "child_ids": [
            "de5ZDgm"
        ],
        "attachment": null,
        "html_type": "button",
        "html_content": null,
        "metadata": {
            "workflow": "test_workflow",
            "end_sequence": "false"
        }
    },
    "de5ZDgm": {
        "type": "bot",
        "messages": [
            "this is the last message",
            "goodbye"
        ],
        "parent_ids": [
            "m84n5MM"
        ],
        "child_ids": [],
        "attachment": null,
        "html_type": "button",
        "html_content": null,
        "metadata": {
            "workflow": "test_workflow",
            "end_sequence": "true"
        }
    }
}"""
