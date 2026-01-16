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
    to the tenant's specific directory. It prevents cross-tenant data leakage
    and path traversal attacks.
    
    Security measures:
    - Validates tenant value against allowed tenants
    - Resolves path and ensures it stays under DOCUMENTS_BASE_DIR
    - Prevents path traversal attacks (../, etc.)
    
    Args:
        tenant: The tenant identifier (e.g., "tenantA", "tenantB")
        
    Returns:
        Dictionary mapping filename to document content
        
    Raises:
        ValueError: If tenant value is invalid or contains path traversal attempts
    """
    # Defensive check: reject unexpected tenant values
    # Only allow known tenant identifiers
    allowed_tenants = {"tenantA", "tenantB"}
    if tenant not in allowed_tenants:
        raise ValueError(f"Invalid tenant identifier: {tenant}")
    
    # Build tenant directory path
    tenant_dir = DOCUMENTS_BASE_DIR / tenant
    
    # Resolve path to absolute and ensure it stays under DOCUMENTS_BASE_DIR
    # This prevents path traversal attacks (e.g., tenant="../../other_folder")
    base_dir_abs = DOCUMENTS_BASE_DIR.resolve()
    tenant_dir_abs = tenant_dir.resolve()
    
    # Ensure the resolved tenant directory is actually under the base directory
    try:
        tenant_dir_abs.relative_to(base_dir_abs)
    except ValueError:
        # Path traversal detected - tenant_dir is not under base_dir
        raise ValueError(f"Path traversal detected: {tenant}")
    
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


# Time expression detection for delay/deadline queries
TIME_WORDS = {"jour", "jours", "heure", "heures", "h", "48h", "5"}
TIME_REGEX = re.compile(r"\b\d+\s*(jour|jours|heure|heures|h)\b", re.IGNORECASE)


def canonicalize_token(tok: str) -> str:
    """
    Very small stemming/canonicalization to reduce French variations.
    declarer/declare/declaration -> declar
    resiliation/resilier -> resili
    """
    if tok.startswith("declar"):
        return "declar"
    if tok.startswith("resili"):
        return "resili"
    return tok


def canonicalize_tokens(tokens: Set[str]) -> Set[str]:
    """Canonicalize a set of tokens."""
    return {canonicalize_token(t) for t in tokens}


def has_time_expression(text: str) -> bool:
    """Check if text contains a time expression (e.g., '5 jours', '48h')."""
    t = normalize_text(text)
    return bool(TIME_REGEX.search(t))


def search_documents(documents: dict[str, str], query: str) -> tuple[str, List[str]]:
    """
    Improved keyword-based search with precision scoring and best-match selection.
    
    This search approach:
    1. Normalizes both query and documents (lowercase, no accents, no punctuation)
    2. Splits into word tokens
    3. Scores documents by number of matching tokens
    4. Selects only the best-matching document(s)
    5. Scores sentences and selects the best sentence(s)
    6. Prioritizes email-containing sentences for email queries
    
    Args:
        documents: Dictionary mapping filename to content
        query: Search query string
        
    Returns:
        Tuple of (answer, list of source filenames)
    """
    # Normalize and tokenize the query
    query_normalized = normalize_text(query)
    query_tokens = tokenize_text(query_normalized)
    query_tokens = canonicalize_tokens(query_tokens)
    
    # Check if query is about email
    query_lower = query.lower()
    is_email_query = 'email' in query_lower or 'mail' in query_lower or 'adresse' in query_lower
    
    # Detect "delay/deadline intent"
    wants_delay = ("delai" in query_tokens) or ("délai" in query_lower) or ("jours" in query_lower) or ("jour" in query_lower)
    
    # Detect "suivi" (follow-up) intent
    wants_suivi = "suivi" in query_tokens or "suivi" in query_lower
    
    # Topic keywords for gating - must be present in both query and document
    topic_keywords = {'sinistre', 'resiliation', 'rc', 'exclusion'}
    
    # Detect if query is specifically about exclusion
    wants_exclusion = "exclusion" in query_tokens or "exclusion" in query_lower
    
    # Extract topic keywords present in the query
    query_topics = topic_keywords.intersection(query_tokens)
    
    # Special handling for exclusion queries: only require "exclusion" token
    # Do not require other topic keywords like "rc" or "produit"
    # But we'll check for specific exclusion details in sentence matching
    exclusion_details = set()  # Initialize empty set
    # Keywords that indicate specific exclusion types (not product names)
    exclusion_type_keywords = {'travaux', 'hauteur', 'sous-traitance', 'metres', 'metre', 'declaree', 'declare'}
    
    if wants_exclusion:
        query_topics = {"exclusion"}  # Only require exclusion, ignore other topics
        # Extract meaningful query tokens beyond "exclusion" for detailed matching
        # Only keep tokens that are actually about exclusion types, not product names
        all_details = query_tokens - {"exclusion"} - topic_keywords
        exclusion_details = {d for d in all_details if d in exclusion_type_keywords}
    
    # Score each document by number of matching tokens
    # Apply topic gating: if query has topic keywords, only consider documents with those topics
    doc_scores = {}
    for filename, content in documents.items():
        # Normalize and tokenize document content
        content_normalized = normalize_text(content)
        content_tokens = tokenize_text(content_normalized)
        content_tokens = canonicalize_tokens(content_tokens)
        
        # Topic gating: if query contains topic keywords, document must also contain them
        if query_topics:
            doc_topics = topic_keywords.intersection(content_tokens)
            # Document must contain all topic keywords from the query
            if not query_topics.issubset(doc_topics):
                continue  # Skip this document - doesn't match required topics
        
        # For exclusion queries: ensure document actually contains "exclusion" word
        # This is a safety check to prevent false matches
        if wants_exclusion:
            content_lower = content.lower()
            if "exclusion" not in content_lower:
                continue  # Skip this document - doesn't have exclusion information
        
        # For exclusion queries with specific details: document must contain those details
        # Example: "exclusion des travaux en hauteur" -> document must contain "travaux" or "hauteur"
        if wants_exclusion and exclusion_details:
            content_details = exclusion_details.intersection(content_tokens)
            # If query mentions specific exclusion details, document must contain at least one
            if not content_details:
                continue  # Skip this document - doesn't match the specific exclusion mentioned
        
        # Intent keyword gating: if query asks about "suivi", document must contain "suivi" or "hebdomadaire"
        if wants_suivi:
            content_lower = content.lower()
            has_suivi = "suivi" in content_lower or "hebdomadaire" in content_lower
            if not has_suivi:
                continue  # Skip this document - doesn't have follow-up information
        
        # Email gating: for email questions, document must contain '@'
        if is_email_query and '@' not in content:
            continue  # Skip this document - doesn't have email address
        
        # Find intersection of query tokens and document tokens
        matching_tokens = query_tokens.intersection(content_tokens)
        
        # Score = number of matching tokens
        if len(matching_tokens) >= 1:
            doc_scores[filename] = len(matching_tokens)
    
    if not doc_scores:
        return "Aucune information disponible pour ce client", []
    
    # Select only documents with the highest score (best match)
    max_score = max(doc_scores.values())
    best_docs = [filename for filename, score in doc_scores.items() if score == max_score]
    
    # Find the best sentence overall from all best documents
    all_sentence_scores = []
    
    for filename in best_docs:
        content = documents[filename]
        
        # Split content into sentences using BOTH newline and dot
        # First split by newlines, then split each line by dots
        sentences = []
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Split line by dots
            if '.' in line:
                line_sentences = [s.strip() for s in line.split('.') if s.strip()]
                sentences.extend(line_sentences)
            else:
                sentences.append(line)
        
        # Clean empty sentences
        sentences = [s for s in sentences if s.strip()]
        
        # Filter out title-like lines
        # Titles are typically short and lack verbs or punctuation
        filtered_sentences = []
        verb_patterns = ['doit', 'est', 'sont', 'envoyé', 'enregistrée', 'validé', 'valide', 
                        'couvre', 'transmet', 'effectué', 'déclaré', 'déclaration']
        
        for sentence in sentences:
            # Special case: if sentence contains "exclusion", always keep it
            # (even if short or lacks verbs, as exclusion lines are often brief)
            sentence_lower = sentence.lower()
            has_exclusion = "exclusion" in sentence_lower
            
            if not has_exclusion:
                # Skip lines shorter than 25 characters
                if len(sentence) < 25:
                    continue
                
                # Skip lines that don't contain punctuation or verbs
                has_punctuation = '.' in sentence or ':' in sentence
                has_verb = any(verb in sentence_lower for verb in verb_patterns)
                
                # Keep sentence if it has punctuation OR a verb
                if not (has_punctuation or has_verb):
                    continue
            
            # Keep the sentence (either has exclusion, or passed normal filtering)
            filtered_sentences.append(sentence)
        
        sentences = filtered_sentences
        
        # Score each sentence
        for sentence in sentences:
            sentence_normalized = normalize_text(sentence)
            sentence_tokens = tokenize_text(sentence_normalized)
            sentence_tokens = canonicalize_tokens(sentence_tokens)
            
            # Topic gating for sentences: if query has topic keywords, sentence must also contain them
            if query_topics:
                sentence_topics = topic_keywords.intersection(sentence_tokens)
                # Sentence must contain all topic keywords from the query
                if not query_topics.issubset(sentence_topics):
                    continue  # Skip this sentence - doesn't match required topics
            
            # For exclusion queries with specific details: sentence must contain those details
            # Example: "exclusion des travaux en hauteur" -> sentence must contain "travaux" or "hauteur"
            if wants_exclusion and exclusion_details:
                sentence_details = exclusion_details.intersection(sentence_tokens)
                # If query mentions specific exclusion details, sentence must contain at least one
                if not sentence_details:
                    continue  # Skip this sentence - doesn't match the specific exclusion mentioned
            
            # Delay gating: for delay questions, ONLY accept sentences with time info
            if wants_delay and not has_time_expression(sentence):
                continue
            
            # Intent keyword gating: if query asks about "suivi", sentence must contain "suivi" or "hebdomadaire"
            if wants_suivi:
                sentence_lower = sentence.lower()
                has_suivi = "suivi" in sentence_lower or "hebdomadaire" in sentence_lower
                if not has_suivi:
                    continue  # Skip this sentence - doesn't have follow-up information
            
            # Email gating: for email questions, ONLY accept sentences with '@'
            if is_email_query and '@' not in sentence:
                continue  # Skip this sentence - doesn't have email address
            
            # Count matching tokens in this sentence
            matching_count = len(query_tokens.intersection(sentence_tokens))
            
            # Email prioritization: if query is about email and sentence contains '@', prioritize it
            email_bonus = 10 if (is_email_query and '@' in sentence) else 0
            
            score = matching_count + email_bonus
            if score > 0:  # Only include sentences with at least one match
                all_sentence_scores.append((score, sentence, filename))
    
    # Select the single best sentence overall (highest score)
    if all_sentence_scores:
        best_score, best_sentence, best_doc = max(all_sentence_scores, key=lambda x: x[0])
        return best_sentence, [best_doc]
    
    # If nothing matched at sentence-level, return no answer
    return "Aucune information disponible pour ce client", []


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
    
    # CRITICAL SECURITY CHECK: Verify all sources belong to this tenant
    # This is a defensive check to ensure tenant isolation
    for source in sources:
        # Extract tenant from filename pattern (docA* = tenantA, docB* = tenantB)
        if tenant == "tenantA" and not source.startswith("docA"):
            raise ValueError(f"SECURITY VIOLATION: Source {source} does not belong to tenant {tenant}")
        if tenant == "tenantB" and not source.startswith("docB"):
            raise ValueError(f"SECURITY VIOLATION: Source {source} does not belong to tenant {tenant}")
    
    return {
        "answer": answer,
        "sources": sources
    }

