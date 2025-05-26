from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from consentbot.models import ConsentUrl, ConsentTestAttempt
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

TEST_SCENARIOS = {
    "perfect_score": {
        "correct_nodes": [
            "c3jUXWd", "KyvB8Qe", "KmYUkXf", "EgapBwq", "enKSA2K",
            "mcjM5XL", "Yj34Tnd", "b3HAamY", "TBaxMHp", "DiTdvf2"
        ],
    },
    "needs_retry": {
        "correct_nodes": [
            "c3jUXWd", "KyvB8Qe", "KmYUkXf",  # Questions 1–3 only correct
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

def form_handler(node:dict, invite_id:str):
    form_type = node['responses'][0]['label']['form_type']
    url = f"/mia/consentbot/consent-response/"
    payload = {
        "invite_id": str(invite_id),
        "node_id": node['responses'][0]['id'],
        "form_type": form_type,
        "form_responses": FORM_RESPONSES[form_type]
    }
    # print(payload)
    if form_type in ["consent","text_fields","child_contact"]:
        import json; print(json.dumps(node['responses'][0]['label']))
        import pdb; pdb.set_trace()
    response = APIClient().post(url, payload, format="json")
    
    return response.data['chat'][-1]['node_id']

def test_handler(node: dict, invite_id: str, count: int):
    correct_node_id = node['responses'][0]['id']

    while CORRECT_NODES:
        # Submit the current answer
        res = APIClient().get(f"/mia/consentbot/consent-response/{invite_id}/?node_id={correct_node_id}")
        count += 1
        last_turn = res.data["chat"][-1]

        print("\n", last_turn, "\n", "count: ", count, "\n")

        # Remove after processing the node
        if correct_node_id in CORRECT_NODES:
            CORRECT_NODES.remove(correct_node_id)

        # Determine the next correct response to send
        found = False
        for answer in last_turn['responses']:
            if answer['id'] in CORRECT_NODES:
                correct_node_id = answer['id']
                found = True
                break
        # End loop if no more correct responses
        if not found:
            break  

    # Confirm the test results
    user = ConsentUrl.objects.get(consent_url=invite_id).user
    attempts = ConsentTestAttempt.objects.filter(
        user=user, consent_script_version=user.consent_script
    ).order_by("started_at")

    # import pdb; pdb.set_trace()
    return res.data["chat"][-1]['responses'][0]['id']

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
        self.invite_id = get_invite.data['consent_url']
        self.user = ConsentUrl.objects.get(consent_url=self.invite_id).user
        url = f"/mia/consentbot/consent/{self.invite_id}/"
        res = self.client.get(url)
        count = 0
        # Step 2: Walk through nodes
        for _ in range(150):  # simulate up to 10 responses
            response_id = None
            last_turn = res.data["chat"][-1]
            count += 1
            if count > 90:
                print("\n",last_turn, "\n", "count: ",count, "\n" )

            responses = last_turn.get("responses", [])
            if not responses:
                break
            if responses[0]['id'] in FORM_NODES:
                response_id = form_handler(last_turn, self.invite_id)
            
            if responses[0]['id'] == "bmorWZo":
                response_id = test_handler(last_turn, self.invite_id, count)
                
            if response_id == None:
                response_id = responses[0]["id"]
            res = self.client.get(
                f"/mia/consentbot/consent-response/{self.invite_id}/?node_id={response_id}"
            )
            try:
                self.assertEqual(res.status_code, 200)
            except:
                import pdb; pdb.set_trace()

        # Step 3: Check test attempt was recorded
        attempts = self.user.test_attempts.all()
        self.assertTrue(attempts.exists())
        # import pdb; pdb.set_trace()
