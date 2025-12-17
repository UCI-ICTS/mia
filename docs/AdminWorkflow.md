# KAURO Admin Workflow
## 1. Admin receives an invite to join Kauro
- Admin receives an onboarding email.
- Clicks “Activate Account”.
- Sets password.
- Logs in to the Kauro Dashboard for the first time.

*Outcome: Admin account active and authenticated.*

## 2. Admin adds a participant + generates invite

- Go to Participants → Add Participant.
- Enter name + email + (optional) metadata.
- Click “Generate New Invite Link”.
- System creates a Consent Session.
- System generates unique URL: `https://mia.genomics.icts.uci.edu/mia/invite/<id>/`
- System sends participant an invite email containing the chat link.

*Outcome: Participant receives study invite with automated link.*

## 3. Participant starts consent chat
- Participant opens the link on mobile.
- Chat begins (KAURO deterministic chatbot).
- If confused or needing help, participant clicks “Contact the team”.
- This triggers an automatic Follow-Up Task for staff.
- Stored under: Follow-Up → Pending Items.
*Outcome: Real-time communication requests funnel into admin dashboard.*

## 4. Admin resolves follow-up

- Admin opens Follow-Up module.
- Each item shows:
	- Participant name
	- Session node where question occurred
	- Participant message
- Admin clicks Resolve.
- (Optional) Add a note.
- Item disappears from Pending and moves to Resolved.

*Outcome: Follow-up workflow completed with one click.*

## 5. Participant completes consent chat
- Participant passes test.
- Participant fills in information about sample storage and handling.
- Participants "signs" consent form.
- Consent form and chat transcript PDFs are generated and stored on server.
- This triggers an automatic email to the participant with a copy of their documents. 
- Stored under: Participant Documents.

*Outcome: Documentation of consent and sample handling.*