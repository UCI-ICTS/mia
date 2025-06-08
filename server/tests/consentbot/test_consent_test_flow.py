
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from io import StringIO
from rest_framework.test import APIClient
from consentbot.models import Consent, ConsentSession, ConsentTestAttempt
from authentication.models import Feedback


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

FORMS = ["enroll_form"]

FORM_RESPONSES={
    "checkbox_form":[
        {
            "name": "checkbox_form", 
            "value": ["myself", "myChildChildren", "childOtherParent", "adultFamilyMember"]
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


class ConsentTestFlowTest(TestCase):
    fixtures = ['tests/fixtures/test_data.json']

    def setUp(self):
        self.client = APIClient()
        self.WALK = False
        self.user = User.objects.get(username="wheel")
        self.user.set_password("wheel")
        self.user.save()
        auth_response = self.client.post("/mia/auth/login/", {
            "email": self.user.email,
            "password": "wheel"
        }, format="json")
        self.token = auth_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.test_scenario = "needs_retry"
        # self.test_scenario = "perfect_score"
        self.correct_nodes = TEST_SCENARIOS[self.test_scenario]["correct_nodes"][:]

    def dump_test_data(self, file_name:str="test_results.json")-> None:
        out = StringIO()
        call_command('dumpdata', '--exclude', 'contenttypes', '--indent', '2', stdout=out)
        with open(file_name, 'w') as f:
            f.write(out.getvalue())

    def handle_form_submission(self, node, session_slug):
        response = node["responses"][0]
        label = response["label"]
        form_type = label["form_type"]  # assume checked in advance
        payload = {
            "session_slug": session_slug,
            "node_id": response["id"],
            "form_type": form_type,
            "form_responses": FORM_RESPONSES.get(form_type, [])
        }
        form_response = self.client.post("/mia/consentbot/consent-response/", payload, format="json")
        if len(form_response.data['chat'][-1]['responses']) == 0 and form_type != "feedback":
            import pdb; pdb.set_trace()

        try: 
            self.assertEqual(form_response.status_code, 200)
        except:
            import pdb; pdb.set_trace()

        return form_response

    def handle_test_question(self, node, session_slug):
        """
        Submit the correct answer if available; otherwise fall back to a known incorrect option.
        """
        print(node['metadata']['end_sequence'])
        if len(node["responses"]) == 1:
            node_id = node["responses"][0]['id']
            return self.client.get(f"/mia/consentbot/consent-response/{session_slug}/?node_id={node_id}")
        
        for response_option in node.get("responses", []):
            node_id = response_option["id"]
            if node_id in self.correct_nodes:
                return self.client.get(f"/mia/consentbot/consent-response/{session_slug}/?node_id={node_id}")

        # Fallback: submit the first known incorrect answer
        for response_option in node.get("responses", []):
            node_id = response_option["id"]
            if node_id in INCORRECT_NODES:
                return self.client.get(f"/mia/consentbot/consent-response/{session_slug}/?node_id={node_id}")

        # If no match found at all, raise for clarity
        import pdb; pdb.set_trace()
        raise ValueError(f"No matching correct or incorrect response found for node {node['node_id']}")


    def advance_chat(self, node, session_slug):
        response = node.get("responses", [])[0]

        if not isinstance(response, dict):
            raise ValueError(f"Malformed response: {response}")

        metadata = response.get("metadata", {})
        workflow = metadata.get("workflow", "")
        end_sequence = metadata.get("end_sequence", False)

        # print(f"{node['node_id']}\n{metadata}")

        # Check if this response is a form response (label is a dict with form_type)
        label = response.get("label")
        if isinstance(label, dict) and "form_type" in label:
            return self.handle_form_submission(node, session_slug)

        if workflow == "test_user_understanding":
            
            if end_sequence and self.test_scenario == "needs_retry":
                # import pdb; pdb.set_trace()
                self.test_scenario = "perfect_score"
                self.correct_nodes = TEST_SCENARIOS[self.test_scenario]["correct_nodes"][:]
                retry_choice = self.handle_test_question(node, session_slug).data['chat'][-1]['responses']
                for response_option in retry_choice:
                    if response_option['metadata']['workflow'] == "test_user_understanding":
                        return self.client.get(f"/mia/consentbot/consent-response/{session_slug}/?node_id={response_option['id']}")
            return self.handle_test_question(node, session_slug)

        # Default to GET
        return self.client.get(f"/mia/consentbot/consent-response/{session_slug}/?node_id={response['id']}")


    def test_consent_test_flow(self):
        create_response = self.client.post("/mia/consentbot/consent-url/", {
            "username": "jane"
        }, format="json")
        self.assertEqual(create_response.status_code, 201)

        get_invite = self.client.get("/mia/consentbot/consent-url/jane/invite-link/")
        session_slug = get_invite.data['session_slug']

        res = self.client.get(f"/mia/consentbot/consent/{session_slug}/")

        count = 0
        for _ in range(150):
            count += 1
            try: 
                last_turn = res.data["chat"][-1]
            except:
                import pdb; pdb.set_trace()
            if not last_turn.get("responses"):
                break
            else:
                res = self.advance_chat(last_turn, session_slug)
            
            if count > 90:
                print(
                    count, "\n\tParticipant: ",
                    [message for message in res.data['chat'][-2]['messages']],
                    "\n\tMIA: ",
                    [message for message in res.data['chat'][-1]['messages']]
                )
                # if count == 107:
                #     import pdb;pdb.set_trace()
            try: 
                self.assertEqual(res.status_code, 200)
            except:
                print(res.data)
                import pdb; pdb.set_trace()
        session = ConsentSession.objects.get(session_slug=session_slug)
        session_user = session.user

        attempts = session_user.test_attempts.all()
        self.assertTrue(attempts.exists())
        
        consent = session.consent
        
        # ✅ Consent completion
        self.assertIsNotNone(consent.consented_at)
        self.assertEqual(consent.user_full_name_consent, "Jane Doe")

        # ✅ Result return preferences
        self.assertTrue(consent.return_primary_results)
        self.assertTrue(consent.return_actionable_secondary_results)
        self.assertTrue(consent.return_secondary_results)

        # ✅ Sample storage preferences
        self.assertTrue(consent.store_sample_this_study)
        self.assertTrue(consent.store_sample_other_studies)

        # ✅ PHI use preferences
        self.assertTrue(consent.store_phi_this_study)
        self.assertTrue(consent.store_phi_other_studies)

        # ✅ User flag
        session_user.refresh_from_db()
        self.assertTrue(session_user.consent_complete)

