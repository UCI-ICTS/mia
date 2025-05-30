from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from consentbot.models import ConsentSession, ConsentTestAttempt
from django.contrib.auth import get_user_model


User = get_user_model()
QUESTION_NODES = [
    "VWzWNAK", "hfQYPNY", "aBLobjJ", "nWC8AGV", "LFgk3AZ",
    "hHuaG87", "2Bh3yqe", "Wi8Xzvj", "JLwjXJk", "NPkVfwh"
]
CORRECT_NODES = [
    "c3jUXWd", "KyvB8Qe", "KmYUkXf", "EgapBwq", "enKSA2K",
    "mcjM5XL", "Yj34Tnd", "b3HAamY", "TBaxMHp","DiTdvf2"
]
INCORRECT_NODES = [
    "6PJ8q9D","9LwDBiM","BZCE5J4","oXEsSu9","cCwcBvK",
    "DViRS7T","HSHVE6v","BnpCPkN","mh5Ta4t","Mc6Kfcw","W3wVKub"
]

TEST_SCENARIOS = {
    "perfect_score": {
        "correct_nodes": [
            "c3jUXWd", "KyvB8Qe", "KmYUkXf", "EgapBwq", "enKSA2K",
            "mcjM5XL", "Yj34Tnd", "b3HAamY", "TBaxMHp", "DiTdvf2"
        ],
    },
    "needs_retry": {
        "correct_nodes": [
            "c3jUXWd", "KyvB8Qe",  "enKSA2K",
            "mcjM5XL", "Yj34Tnd", "b3HAamY"
        ],
    },
    "fail_test": {
        "correct_nodes": [],
    },
}


FORM_NODES = [
    "b5nYNf6","gWJxSfh","GkgFmXm","8A8kAJS","gdiDJUS",
    "VZsTdFg","nriTamw","AimWGCA","YkoAEVe","XGa7LFM",
    "SFiuhW9","VaSzySv","nU9xybq","nAaeApX","aXDDbh2"
]

FORM_RESPONSES={
    "checkbox_form":[
        {
            "name": "checkbox_form", 
            "value": ["myself", "childOtherParent"]
        }
    ],
    "sample_storage": [
        {
            "name": "storeSamplesOtherStudies",
            "value":"yes"
        }
    ],
    "phi_use": [
        {
            "name": "storePhiOtherStudies",
            "value":"yes"
        }
    ],
    "result_return": [
        {
            "name": "rorPrimary",
            "value":"yes"
        },
        {
            "name": "rorSecondary",
            "value":"yes"
        },
        {
            "name": "rorSecondaryNot",
            "value":"yes"
        }
    ],
    "feedback": [
        {
            "name": "satisfaction",
            "value": "Dissatisfied"
        },
        {
            "name": "suggestions",
            "value": "Some test text here"
        }
    ],
    "consent": [
        {
            "name": "fullname",
            "value": "Jane Doe"
        },
        {
            "name": "consent",
            "value": "checked"
        }
    ],
    "text_fields": {},
    "child_contact": {},
}

count = 0

def form_handler(node:dict, session_slug:str):
    form_type = node['responses'][0]['label']['form_type']
    url = f"/mia/consentbot/consent-response/"
    payload = {
        "session_slug": str(session_slug),
        "node_id": node['responses'][0]['id'],
        "form_type": form_type,
        "form_responses": FORM_RESPONSES[form_type]
    }
    # print(payload)
    if form_type in ["text_fields","child_contact"]:
        import json; print(json.dumps(node['responses'][0]['label']))
        import pdb; pdb.set_trace()
    response = APIClient().post(url, payload, format="json")
    print(response.data['chat'][-1]['node_id'])
    return response.data['chat'][-1]['node_id']

def retry_test_handler(node: dict, session_slug: str, count: int, scenario_key: str, retry:bool=False):
    correct_nodes = TEST_SCENARIOS[scenario_key]["correct_nodes"][:]
    answer_node_id = node['responses'][0]['id']  # fallback

    if retry:
        # Confirm the test results
        user = ConsentSession.objects.get(session_slug=session_slug).user
        attempts = ConsentTestAttempt.objects.filter(
            user=user, consent_script_version=user.consent_script
        ).order_by("started_at")
        retry_question_ids = attempts[0].incorrect_question_ids()
        for question in retry_question_ids:
            for answer in node['responses']:
                if answer['id'] in correct_nodes:
                    answer_node_id = answer['id']
                    break
            retry_res = APIClient().get(f"/mia/consentbot/consent-response/{session_slug}/?node_id={answer_node_id}")
            node = retry_res.data["chat"][-1]
            # print("\n", node, "\n", "135 count: ", count, "\n")
            # print("\nRetry answer submitted:", answer_node_id, "\n")
    answer_node_id = node['responses'][0]['id']
    final_res = APIClient().get(f"/mia/consentbot/consent-response/{session_slug}/?node_id={answer_node_id}")
    answer_node_id = final_res.data['chat'][-1]['responses'][0]['id']
    return answer_node_id

    
NUM_TEST_QUESTIONS = 10  # or import from your settings/constants

def test_handler(node: dict, session_slug: str, count: int, scenario_key: str, retry: bool = False):
    correct_nodes = TEST_SCENARIOS[scenario_key].get("correct_nodes", [])[:]
    answer_node_id =  node['responses'][0]['id']

    while answer_node_id != "nFpTPVg":
        count += 1
        res = APIClient().get(f"/mia/consentbot/consent-response/{session_slug}/?node_id={answer_node_id}")
        count += 1
        last_turn = res.data["chat"][-1]

        matched = False
        for answer in last_turn['responses']:
            if answer['id'] in correct_nodes:
                answer_node_id = answer['id']
                correct_nodes.remove(answer_node_id)
                matched = True
                break

        if not matched:
            # Pick a known incorrect one if available
            for answer in last_turn['responses']:
                if answer['id'] in INCORRECT_NODES:
                    answer_node_id = answer['id']
                    break
            else:
                answer_node_id = last_turn['responses'][0]['id']

    user = ConsentSession.objects.get(session_slug=session_slug).user
    attempt = ConsentTestAttempt.objects.get(user=user, consent_script_version=user.consent_script)
    conf_res = APIClient().get(f"/mia/consentbot/consent-response/{session_slug}/?node_id={answer_node_id}")

    if attempt.percent_correct() == 100:
        return conf_res.data["chat"][-1]['responses'][0]['id']
    elif scenario_key == "needs_retry":
        
        return "kZ6qj4C"  # retry
    else:
        return "DdxFUae"  # speak to manager

class ConsentTestFlowTest(TestCase):
    fixtures = ['tests/fixtures/test_data.json']
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(username="wheel")
        self.password = "example-password"
        self.user.set_password(self.password)
        self.user.save()
        auth_response = self.client.post("/mia/auth/login/", {
            "email": self.user.email,
            "password": self.password
        }, format="json")
        self.token = auth_response.data["access"]


    def test_consent_test_flow(self):
        # Step 1: Create initial consent invite
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        create_response = self.client.post("/mia/consentbot/consent-url/",{
            "username": "jane"
        }, format="json")
        self.assertEqual(create_response.status_code, 201)

        get_invite = self.client.get("/mia/consentbot/consent-url/jane/invite-link/")
        self.session_slug = get_invite.data['session_slug']
        import pdb; pdb.set_trace()
        self.user = ConsentSession.objects.get(session_slug=self.session_slug).user
        url = f"/mia/consentbot/consent/{self.session_slug}/"
        res = self.client.get(url)
        count = 0

        # Step 2: Walk through nodes
        for _ in range(150):  # simulate up to 10 responses
            response_id = None
            last_turn = res.data["chat"][-1]
            count += 1
            if count == 90:
                payload = {
                    "email": "jdoe@testing.com",
                    "follow_up_reason": "privacy",
                    "follow_up_info": "I am not happy.\n\nLast Node ID: nFpTPVg",
                    "follow_up_reason": "privacy"
                }
                follow_up_res = self.client.post(f"/mia/auth/follow-ups/", payload, format="json")
            responses = last_turn.get("responses", [])
            if not responses:
                break
            if responses[0]['id'] in FORM_NODES:
                response_id = form_handler(last_turn, self.session_slug)
            
            if responses[0]['id'] == "bmorWZo":
                response_id = test_handler(last_turn, self.session_slug, count, "needs_retry")
                
            if response_id == "kZ6qj4C":
                retry_res = self.client.get(f"/mia/consentbot/consent-response/{self.session_slug}/?node_id={response_id}")
                response_id = retry_test_handler(retry_res.data['chat'][-1], self.session_slug, count, "perfect_score", True)
            if response_id == None:
                response_id = responses[0]["id"]
            res = self.client.get(
                f"/mia/consentbot/consent-response/{self.session_slug}/?node_id={response_id}"
            )
            try:
                self.assertEqual(res.status_code, 200)
            except:
                import pdb; pdb.set_trace()

        # Step 3: Check test attempt was recorded
        attempts = self.user.test_attempts.all()
        self.assertTrue(attempts.exists())
        # check for forms and final consent conditions
