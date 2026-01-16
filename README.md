Project Overview

This project is a technical demonstration of a multi-tenant SaaS application.

It allows different clients (tenants) to search their own private documents while guaranteeing strict data isolation between clients.

Each client:

Has its own documents

Cannot see or access documents from other clients

Is identified only by a secure API key sent automatically by the interface

The goal is to demonstrate:
✔ Secure tenant separation
✔ Simple and reliable backend logic
✔ Easy-to-use interface for non-technical users

Technologies Used

Backend: Python, FastAPI

Frontend: React (Vite)

Storage: Local files (per tenant folders)

Security: API Key via HTTP header (X-API-KEY)

Project Structure
TESTACTUDATA/
├── main.py                 # Backend API
├── requirements.txt        # Python dependencies
├── documents/
│   ├── tenantA/            # Client A documents
│   └── tenantB/            # Client B documents
└── frontend/               # Web interface (React)

Prerequisites

Make sure you have installed:

✅ Python 3.8 or higher

✅ Node.js 16 or higher (with npm)

Check versions:

python --version
node --version

How to Run the Application
▶ Step 1 — Start Backend

Open a terminal in the project folder:

pip install -r requirements.txt
uvicorn main:app --reload


Backend runs on:

http://localhost:8000


⚠️ Keep this terminal open.

▶ Step 2 — Start Frontend

Open a second terminal:

cd frontend
npm install
npm run dev


Open browser:

http://localhost:3000

How to Use the Application

Select a client from the dropdown:

Client A

Client B

Type a question.

Click Search.

The system will return:

The answer (if found)

The source document(s)

Example Tests
✅ Client A Test

Select Client A, ask:

Quelle est l’exclusion du produit RC Pro ?


Expected:

Travaux en hauteur au-delà de 3 mètres

✅ Client B Test

Select Client B, ask:

Quelle est l’exclusion du produit RC Pro B ?


Expected:

Sous-traitance non déclarée

🔒 Security Test

Select Client A, ask:

Sous-traitance non déclarée


Expected:

Aucune information disponible pour ce client


This proves tenant isolation works.

Tenant Isolation Explained

Tenant isolation means that each client has their own private data space.

How this project guarantees isolation:

The client identity is resolved only from the HTTP header X-API-KEY.

The tenant is never sent in the request body.

Documents are physically separated in folders:

documents/tenantA/
documents/tenantB/


The backend loads only the folder belonging to the authenticated tenant.

Cross-tenant access is impossible by design.

API Endpoints

GET /
Health check

POST /search
Body:

{
  "query": "your question"
}


Header:

X-API-KEY

Stopping the Application

Press:

CTRL + C


in both terminal windows.

