# Code Structure and Reasoning

## Overview
MIA is a web app built with Django on the backend and React on the frontend. It's designed to manage personalized consent workflows, user authentication, and follow-up tracking. The system includes tools for both participants and administrators, making it easier to handle consent, feedback, and user management in one place.

## Reasoning for Structure
1. Separation of Concerns:
    - Client handles only the UI and state, relying on the server for data.
    - Server is modular, splitting logic into services, selectors, and APIs for maintainability.
2. Extensibility:
    - Redux Toolkit allows flexible state management for future features.
    - Django ViewSets + DRF allow rapid API expansion with built-in validation and authentication.
3. Scalability:
    - PostgreSQL provides robust relational data support.
    - The project can scale horizontally, as APIs and frontend components are decoupled.

### Repository Layout
``` 
mia/
├── admin/                   # Configuration and administration files
├── client/                  # React frontend application
├── server/                  # Django backend application
├── docs/                    # Documentation files (e.g., setup instructions, API references, )
├── README.md                # Project overview
└── ...
```

## Client (Frontend)
- Framework: React
- State Management: Redux Toolkit
- Component Library: Ant Design (AntD)
- Routing: React Router
- Testing: Jest (future integration with MSW possible)
- Key Features:
    - Consent Chat UI using dynamic forms rendered from JSON structures.
    - Authentication Flow with JWT.
    - Admin Dashboard for managing users, follow-ups, and consent scripts.
    - Error Boundaries for graceful error handling.
    - React app with Redux Toolkit for state management. 

### Folder Structure:
```
client/src/
├── components/           # Reusable UI components (e.g., ConsentForm, ErrorBoundary)
├── pages/                # Page-level components (e.g., LoginPage, Dashboard)
├── slices/               # Redux slices (e.g., authSlice, dataSlice)
├── services/             # API service handlers using Axios
├── __tests__/            # Frontend test files (currently Jest-based)
├── App.js                # Main React app entry
└── setupTests.js         # Jest and testing library setup
```

## Server (Backend)
- Framework: Django
- Database: PostgreSQL
- API: Django REST Framework (DRF) + Simple JWT
- Swagger Integration: drf-yasg for API documentation
- Testing: Django TestCase, using fixtures where relevant.

### Applications:
- authentication/: Handles user auth, JWT, password changes, follow-ups.
- consentbot/: Manages consent scripts and chat workflows.

### Key Backend Concepts:
- Custom User Model: Extended from AbstractUser, includes fields like phone, referred_by, consent_complete.
- JWT Tokens: Login, refresh, verify, and logout endpoints using Simple JWT.
- FollowUps: Users can submit follow-up requests; admins can resolve them.
- Consent Scripts: JSON-based dynamic consent flows linked to users.

### Folder Structure:
```
server/
├── authentication/
│   ├── apis.py               # API endpoints for auth, follow-ups
│   ├── services.py           # Business logic and serializers for user creation, password changes
│   ├── selectors.py          # Data fetching helpers
│   ├── models.py             # User, FollowUp, Feedback models
│   └── urls.py               # URL routing for auth APIs
|
├── config/                   # Server level organization for settings, URLs, etc.
│   ├── settings.py           # Django settings (PostgreSQL, CORS, JWT config)
│   ├── urls.py               # Project-level URL routing
│   ├── manage.py             # Django CLI entry point
|
└── consentbot/               # Consent flow management
    ├── apis.py               # API endpoints for consentbot
    ├── services.py           # Business logic and serializers for Consent creation, ConsentTest
    ├── selectors.py          # Data fetching helpers
    ├── models.py             # Consent, ConsentScript, ConsentTest, ConsentUrl models
    └── urls.py               # URL routing for consentbot APIs

```


