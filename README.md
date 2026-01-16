# Multi-Tenant Document Search API

A technical test project demonstrating a secure multi-tenant SaaS application with a FastAPI backend and React frontend. This system allows different clients (tenants) to search through their own private document collections while ensuring complete data isolation between clients.

## What This Project Does

This application provides a document search service where:

- **Different clients have separate document collections** - Client A can only see Client A's documents, and Client B can only see Client B's documents
- **Security is enforced server-side** - The system automatically determines which client is making a request and restricts access to only their documents
- **Simple keyword search** - Users can ask questions and receive answers based on relevant documents

Think of it like a secure filing cabinet where each client has their own locked drawer - they can only access their own files, never someone else's.

## Project Structure

```
TESTACTUDATA/
├── main.py                 # FastAPI backend server
├── requirements.txt        # Python dependencies
├── documents/             # Document storage (separated by tenant)
│   ├── tenantA/          # Client A's documents
│   └── tenantB/          # Client B's documents
└── frontend/             # React frontend application
    ├── src/
    └── package.json
```

## Prerequisites

- **Python 3.8+** installed on your system
- **Node.js 16+** and npm installed on your system

## Running the Application

### Step 1: Start the Backend (FastAPI)

1. Open a terminal/command prompt in the project root directory (`TESTACTUDATA`)

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

   The backend will be running at `http://localhost:8000`

   You should see output indicating the server is running. Keep this terminal window open.

### Step 2: Start the Frontend (React)

1. Open a **new** terminal/command prompt window

2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

3. Install Node.js dependencies (first time only):
   ```bash
   npm install
   ```

4. Start the React development server:
   ```bash
   npm run dev
   ```

   The frontend will be running at `http://localhost:3000`

   Your web browser should automatically open, or you can manually navigate to `http://localhost:3000`



### Test Scenario 1: Client A

1. **Select Client A** from the dropdown menu at the top of the page

2. **Ask a question about Client A's documents:**
   - Try: "résiliation" (about cancellation procedures)
   - Or: "RC Pro" (about the RC Pro product)
   - Or: "sinistre" (about claims)
   
   **Expected Result:** You should see an answer with source document names (e.g., docA1_procedure_resiliation.txt or docA2_produit_rc_pro_a.txt)

3. **Ask a question about Client B's documents:**
   - Try: "sous-traitance" (this term only appears in Client B's documents)
   
   **Expected Result:** You should see "Aucune information disponible pour ce client" (No information available for this client)
   
   This proves that Client A cannot access Client B's documents.

### Test Scenario 2: Client B

1. **Select Client B** from the dropdown menu

2. **Ask a question about Client B's documents:**
   - Try: "sous-traitance" (about subcontracting exclusions)
   - Or: "sinistre" (about claims procedures)
   - Or: "claims@assureur-b.com" (Client B's claims email)
   
   **Expected Result:** You should see an answer with source document names (e.g., docB1_procedure_sinistre.txt or docB2_produit_rc_pro_b.txt)

3. **Ask a question about Client A's documents:**
   - Try: "assureur-a.fr" (this email only appears in Client A's documents)
   
   **Expected Result:** You should see "Aucune information disponible pour ce client"
   
   This proves that Client B cannot access Client A's documents.

### What This Proves

✅ **Tenant Isolation Works:** Each client can only access their own documents  
✅ **Security is Enforced:** The system prevents cross-client data access  
✅ **User-Friendly:** Non-technical users can easily test and verify the system

## Understanding Tenant Isolation

### What is Tenant Isolation?

Tenant isolation means that each client (tenant) has their own completely separate data space. It's like having separate bank accounts - even though they're in the same bank, one account holder can never see or access another account holder's money.

### How It Works in This Application

1. **Client Selection:** When you select "Client A" or "Client B" in the dropdown, the system uses a special key (API key) to identify which client you are.

2. **Server-Side Security:** The server (not your browser) determines which client you are based on this key. This is important because it means you cannot trick the system into showing you another client's documents.

3. **Automatic Filtering:** Once the server knows which client you are, it automatically only searches through that client's documents. It physically cannot access the other client's documents.

4. **No Cross-Access:** Even if you try to ask about something that exists in another client's documents, the system will correctly respond that no information is available for your client.

### Why This Matters

In a real business scenario:
- **Legal Compliance:** Different clients may have different privacy requirements
- **Data Protection:** Prevents accidental or malicious access to wrong data
- **Trust:** Clients need to know their data is completely separate from others
- **Regulations:** Many industries require strict data separation (healthcare, finance, etc.)

## Why Simple Search Instead of Advanced AI?

This application uses a simple keyword-based search approach rather than advanced machine learning or AI. Here's why:

### 1. **Clarity and Transparency**
   - Simple search is easy to understand and debug
   - You can see exactly why a document matched (it contains your search term)
   - No "black box" behavior that's hard to explain

### 2. **Reliability**
   - Simple search is predictable - same query always gives same results
   - No unexpected behavior from AI models
   - Easier to test and verify correctness

### 3. **Performance**
   - Fast response times without heavy computation
   - No need for expensive AI infrastructure
   - Works well even with limited resources

### 4. **Interview Context**
   - For a technical test, simplicity demonstrates good engineering judgment
   - Shows focus on core requirements (tenant isolation) rather than over-engineering
   - Easier for reviewers to understand and evaluate

### 5. **Real-World Suitability**
   - Many business use cases don't need AI - keyword search is sufficient
   - Easier to maintain and update
   - Lower operational costs

**Note:** In a production system, you might add more sophisticated search later if needed, but starting simple is often the right engineering decision.

## Technical Details (For Developers)

### Backend Architecture

- **Framework:** FastAPI (Python)
- **Tenant Resolution:** Centralized in `resolve_tenant()` function
- **Security:** API keys in `X-API-KEY` header only (never in request body)
- **Document Loading:** Tenant-specific folder access enforced
- **Search:** Case-insensitive keyword matching

### Frontend Architecture

- **Framework:** React with Vite
- **State Management:** React hooks (useState)
- **API Communication:** Fetch API with proper header handling
- **Error Handling:** User-friendly error messages

### API Endpoints

- `GET /` - Health check
- `POST /search` - Search endpoint (requires `X-API-KEY` header)

## Troubleshooting

### Backend won't start
- Make sure Python 3.8+ is installed: `python --version`
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Ensure port 8000 is not already in use

### Frontend won't start
- Make sure Node.js is installed: `node --version`
- Run `npm install` in the frontend directory
- Ensure port 3000 is not already in use

### "CORS error" in browser
- Make sure the backend is running before starting the frontend
- Check that backend is on `http://localhost:8000`

### No results found
- Verify you're asking about content that exists in the selected client's documents
- Check the document files in `documents/tenantA/` or `documents/tenantB/`
- Try simpler, shorter search terms

## Security Notes

- **API Keys:** In production, these would be stored securely (database, secrets manager)
- **CORS:** Currently allows localhost:3000 for development
- **Document Access:** File system access is restricted to tenant-specific folders
- **Input Validation:** FastAPI automatically validates request structure

## License

This is a technical test project for recruitment purposes.

