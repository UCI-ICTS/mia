# MIA (Medical Information Assistant)
A virtual HIPAA-compliant clinical consentbot that facilitates virtual conversations with patients.

MIA is designed to be deployed in a variaty of environments. If configurd properly it should work with any external application that presents properly formatted API requests with appropirate authentication credentials.

This repository is composed of two serivce applications. The server application is a Django API DB and the client application is a Redux/React UI.

# MIA Consent Chat Engine – Architecture Overview

The **MIA Consent Chat Engine** is a **graph-driven, stateful conversation system** designed to guide users through personalized consent flows for research studies. It combines structured metadata, dynamic branching, and real-time user interactions to deliver a responsive and compliant experience.

---

## Core Concepts

### Node Graph (DAG)
- The chat script is structured as a **Directed Acyclic Graph (DAG)**.
- Each node represents either a bot message or a user input.
- Nodes contain:
  - `type`: `"bot"` or `"user"`
  - `messages`: List of strings (bot dialog or button labels)
  - `child_ids`: IDs of next nodes
  - `render_type`: `"button"`, `"form"`, `"image"`, `"video"`, etc.
  - `render_content`: optional image/video/form JSON
  - `metadata`: includes flags like `workflow`, `end_sequence`, etc.

```jsonc
{
  "type": "bot",
  "messages": ["Welcome to the study!"],
  "child_ids": ["abc123"],
  "render_type": "button",
  "metadata": {
    "workflow": "start_consent",
    "end_sequence": false
  }
}
```

---

## Engine Workflow

### 1. **Initialization**
- Chat starts at a designated node (`start_consent`) defined in the script.
- The conversation graph is loaded from a `ConsentScript` JSON blob.
- An invite link (`invite_id`) associates each session with a user.

### 2. **Sequence Traversal**
- The engine uses `process_consent_sequence()` to collect all bot messages until a user response is needed.
- Bot messages are delivered with a typing delay for realism.
- Responses are rendered as Ant Design buttons or forms.

### 3. **User Response**
- Clicking a button or submitting a form dispatches a Redux thunk (`submitConsentResponse`).
- Backend handles form logic via custom processors like:
  - `handle_family_enrollment_form`
  - `handle_phi_use`
  - `handle_result_return`
- After form processing, the next node is determined and the process repeats.

### 4. **Workflow Control**
- Nodes can belong to named workflows (e.g., `"family_enrollment"`) via `metadata.workflow`.
- Dynamic workflows can be **generated at runtime** using `generate_workflow()`.

---

## Key Components

| Component | Purpose |
|----------|---------|
| `ConsentScript` model | Stores the graph JSON, versioned |
| `ConsentPage.js` | React chat UI with typing delays and Ant Design components |
| `selectors.py` | Graph traversal logic (`get_next_consent_sequence`) |
| `services.py` | Form processors and chat state mutation |
| `dataSlice.js` | Redux logic for fetching/submitting chat data |
| `UserConsentUrl` | Invite link manager tying users to sessions |

---

## Special Features

-  **Form rendering** from JSON (`render_type: form`)
-  **Typing indicator** (“Mia is typing...”)
-  **Session timeout** modal after inactivity
-  **Feedback, PHI, and result return forms** handled as modular processors
-  **Dynamic sub-workflows** depending on user inputs (e.g., enrolling child vs self)

---

## Example Chat Flow

```text
Bot: Welcome to the PMGRC study
User: [👋 Hi Mia!]
Bot: Let me walk you through it...
Bot: Here’s what we’ll cover...
User: [Sounds good]
Bot: [Video or Image Rendered]
User: [Submit feedback form]
```


## Deployment

- [Local deployment](docs/deployment/localDeployment.md) 
    - For develpment or internal use only
- [Production deployment](docs/deployment/productionDeployment.md)
    - For deployment that is exposed to the internet
- [Docker deployment](docs/deployment/dockerDeployment.md)
    - WIP: comming soon

## Development and troubleshooting
- [Contribution Guide lines](docs/CONTRIBUTING.md)
- [FAQ and trouble shooting](docs/faq.md)
- [`.secretes` configuration](docs/config.md)
- [Testing](docs/testing.md)