# Multi-Tenant Document Search Frontend

Simple React frontend to test the multi-tenant FastAPI backend.

## Setup

```bash
cd frontend
npm install
```

## Run

```bash
npm run dev
```

The app will be available at http://localhost:3000

Make sure the FastAPI backend is running on http://localhost:8000

## Usage

1. Select a client (A or B) from the dropdown
2. Enter your question in the textarea
3. Click "Search"
4. View the answer and sources

**Important**: The client selection affects ONLY the `X-API-KEY` header. The tenant is NEVER sent in the request body.

