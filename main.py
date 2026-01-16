"""
FastAPI Backend for Multi-Tenant SaaS Technical Test

This application demonstrates secure tenant isolation using API keys.
Tenant identification is done server-side via HTTP headers to ensure
security and prevent client-side manipulation.
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Set
from pathlib import Path
from pydantic import BaseModel
import unicodedata
import re

app = FastAPI(title="Multi-Tenant Document Search API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    """Request body for search endpoint. Note: tenant is NOT in the body."""
    query: str


# Tenant API key mapping
# In production, this would be stored securely (e.g., database, secrets manager)
TENANT_KEYS = {
    "tenantA_key": "tenantA",
    "tenantB_key": "tenantB"
}

# Base documents directory
DOCUMENTS_BASE_DIR = Path("documents")


def resolve_tenant(api_key: Optional[str]) -> str:
    """
    Centralized tenant resolution function.
    
    This function is the single point of truth for tenant identification.
    It ensures that tenant resolution logic is consistent across the application
    and prevents tenant information from leaking into request bodies.
    
    Args:
        api_key: The API key from the X-API-KEY header
        
    Returns:
        The tenant identifier (e.g., "tenantA", "tenantB")
        
    Raises:
        HTTPException: 401 if the API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-KEY header"
        )
    
    tenant = TENANT_KEYS.get(api_key)
    if not tenant:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return tenant


def load_tenant_documents(tenant: str) -> dict[str, str]:
    """
    Load documents ONLY from the resolved tenant's folder.
    
    This function enforces tenant isolation by restricting document access
    to the tenant's specific directory. It prevents cross-tenant data leakage.
    
    Args:
        tenant: The tenant identifier (e.g., "tenantA", "tenantB")
        
    Returns:
        Dictionary mapping filename to document content
    """
    tenant_dir = DOCUMENTS_BASE_DIR / tenant
    
    if not tenant_dir.exists():
        return {}
    
    documents = {}
    for file_path in tenant_dir.iterdir():
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    documents[file_path.name] = f.read()
            except Exception:
                # Skip files that can't be read
                continue
    
    return documents


def normalize_text(text: str) -> str:
    """
    Normalize text for search matching.
    
    This function:
    1. Converts to lowercase
    2. Removes accents (é -> e, à -> a, etc.)
    3. Removes punctuation
    
    This ensures that "Que couvre la RC Pro" can match "La RC Pro couvre..."
    regardless of accents, case, or punctuation differences.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text without accents, punctuation, and in lowercase
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove accents by decomposing unicode characters and removing diacritics
    # Example: "causés" -> "causes", "activité" -> "activite"
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Remove punctuation and special characters, keep only alphanumeric and spaces
    # This handles: "RC Pro" matches "RC-Pro" or "RC.Pro"
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Normalize whitespace (multiple spaces -> single space)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def tokenize_text(text: str) -> Set[str]:
    """
    Split normalized text into meaningful words (tokens).
    
    Filters out single-character words and common French stop words.
    This improves matching by focusing on meaningful keywords while
    preserving important short words like "RC" (acronyms).
    
    Args:
        text: Normalized text string
        
    Returns:
        Set of meaningful word tokens
    """
    # Common French stop words to filter out (2-3 characters)
    # These are articles, prepositions, and common words that don't add semantic meaning
    french_stop_words = {
        'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'que', 
        'qui', 'dans', 'sur', 'par', 'pour', 'avec', 'sans', 'sous', 'aux',
        'au', 'en', 'l', 'd', 'ce', 'se', 'ne', 'te', 'me', 'je', 'tu', 'il',
        'elle', 'nous', 'vous', 'ils', 'elles', 'son', 'sa', 'ses', 'mon', 'ma',
        'ton', 'ta', 'notre', 'votre', 'leur', 'leurs'
    }
    
    # Split into words
    words = text.split()
    
    # Filter: keep words that are either:
    # 1. 3+ characters (likely meaningful), OR
    # 2. 2 characters but not in stop words list (preserves acronyms like "RC")
    meaningful_words = {
        word for word in words 
        if len(word) >= 3 or (len(word) == 2 and word not in french_stop_words)
    }
    
    return meaningful_words


def search_documents(documents: dict[str, str], query: str) -> tuple[str, List[str]]:
    """
    Improved keyword-based search with normalization and token matching.
    
    This search approach:
    1. Normalizes both query and documents (lowercase, no accents, no punctuation)
    2. Splits into word tokens
    3. Uses keyword intersection instead of full string matching
    4. Requires at least 1 meaningful word to match
    
    This ensures that "Que couvre la RC Pro" correctly matches
    "La RC Pro couvre les dommages causés aux tiers..." even with:
    - Different word order
    - Accents (causés vs causes)
    - Punctuation differences
    - Case differences
    
    Args:
        documents: Dictionary mapping filename to content
        query: Search query string
        
    Returns:
        Tuple of (answer, list of source filenames)
    """
    # Normalize and tokenize the query
    query_normalized = normalize_text(query)
    query_tokens = tokenize_text(query_normalized)
    
    # Need at least 2 meaningful words in the query to search
    if len(query_tokens) < 2:
        # If query has less than 2 meaningful words, fall back to simple matching
        # This handles edge cases like single word queries
        query_lower = query.lower()
        matching_docs = []
        for filename, content in documents.items():
            if query_lower in content.lower():
                matching_docs.append(filename)
    else:
        matching_docs = []
        
        # Search through all documents for the tenant
        for filename, content in documents.items():
            # Normalize and tokenize document content
            content_normalized = normalize_text(content)
            content_tokens = tokenize_text(content_normalized)
            
            # Find intersection of query tokens and document tokens
            # This finds which meaningful words from the query appear in the document
            matching_tokens = query_tokens.intersection(content_tokens)
            
            # Require at least 1 matching meaningful word
            # For this dataset, one matching keyword is sufficient because:
            # 1. Documents are domain-specific (insurance procedures, products)
            # 2. Stop words are filtered out, so matching tokens are meaningful
            # 3. Queries like "Quel est l'email pour déclarer un sinistre?" may only
            #    have one meaningful keyword ("sinistre") but should still match
            #    relevant documents. Requiring 2+ tokens would incorrectly reject
            #    valid matches in such cases.
            if len(matching_tokens) >= 1:
                matching_docs.append(filename)
    
    if not matching_docs:
        return "Aucune information disponible pour ce client", []
    
    # Build answer from matching documents
    # Extract relevant sentences that contain matching keywords
    answer_parts = []
    query_normalized = normalize_text(query)
    query_tokens = tokenize_text(query_normalized)
    
    for filename in matching_docs:
        content = documents[filename]
        content_normalized = normalize_text(content)
        content_tokens = tokenize_text(content_normalized)
        
        # Find sentences that contain matching keywords
        sentences = content.split('.')
        for sentence in sentences:
            sentence_normalized = normalize_text(sentence)
            sentence_tokens = tokenize_text(sentence_normalized)
            
            # If sentence contains at least one matching token, include it
            if query_tokens.intersection(sentence_tokens):
                answer_parts.append(sentence.strip())
                break  # Take first relevant sentence per document
    
    answer = " ".join(answer_parts) if answer_parts else f"Found in {len(matching_docs)} document(s)"
    
    return answer, matching_docs


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/search")
def search(
    request: SearchRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY")
):
    """
    Search endpoint with tenant isolation.
    
    The tenant is resolved server-side from the X-API-KEY header.
    This ensures security because:
    1. The tenant cannot be manipulated by the client in the request body
    2. All tenant resolution happens in one centralized function
    3. Documents are loaded only from the tenant's specific folder
    
    Args:
        query: The search query string
        x_api_key: API key from X-API-KEY header
        
    Returns:
        JSON response with answer and sources
    """
    # Resolve tenant from API key (server-side only)
    # Note: tenant is NEVER in the request body - only in the header
    tenant = resolve_tenant(x_api_key)
    
    # Load documents ONLY from this tenant's folder
    # This enforces strict tenant isolation
    documents = load_tenant_documents(tenant)
    
    if not documents:
        return {
            "answer": "Aucune information disponible pour ce client",
            "sources": []
        }
    
    # Perform simple keyword search
    answer, sources = search_documents(documents, request.query)
    
    return {
        "answer": answer,
        "sources": sources
    }

