"""
Tests for tenant isolation security.

These tests verify that:
1. Tenant A cannot access Tenant B's documents
2. Tenant B cannot access Tenant A's documents
3. Invalid API keys return 401
4. Path traversal attacks are prevented
"""

import pytest
from fastapi.testclient import TestClient
from main import app, resolve_tenant, load_tenant_documents

client = TestClient(app)


def test_tenant_a_cannot_access_tenant_b_documents():
    """Client A should not be able to access Client B's documents."""
    # Query for something that only exists in Tenant B's documents
    # "sous-traitance" only appears in docB2_produit_rc_pro_b.txt
    response = client.post(
        "/search",
        json={"query": "sous-traitance"},
        headers={"X-API-KEY": "tenantA_key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should return "no information available" not Tenant B's content
    assert data["answer"] == "Aucune information disponible pour ce client"
    assert data["sources"] == []


def test_tenant_b_cannot_access_tenant_a_documents():
    """Client B should not be able to access Client A's documents."""
    # Query for something that only exists in Tenant A's documents
    # "assureur-a.fr" only appears in docA2_produit_rc_pro_a.txt
    response = client.post(
        "/search",
        json={"query": "assureur-a.fr"},
        headers={"X-API-KEY": "tenantB_key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should return "no information available" not Tenant A's content
    assert data["answer"] == "Aucune information disponible pour ce client"
    assert data["sources"] == []


def test_tenant_a_can_access_own_documents():
    """Client A should be able to access their own documents."""
    # Query for something in Tenant A's documents
    response = client.post(
        "/search",
        json={"query": "résiliation"},
        headers={"X-API-KEY": "tenantA_key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should return information from Tenant A's documents
    assert data["answer"] != "Aucune information disponible pour ce client"
    assert len(data["sources"]) > 0
    # Sources should only be from tenantA
    assert all("docA" in source for source in data["sources"])


def test_tenant_b_can_access_own_documents():
    """Client B should be able to access their own documents."""
    # Query for something in Tenant B's documents
    response = client.post(
        "/search",
        json={"query": "sinistre"},
        headers={"X-API-KEY": "tenantB_key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should return information from Tenant B's documents
    assert data["answer"] != "Aucune information disponible pour ce client"
    assert len(data["sources"]) > 0
    # Sources should only be from tenantB
    assert all("docB" in source for source in data["sources"])


def test_invalid_api_key_returns_401():
    """Invalid API key should return 401 Unauthorized."""
    response = client.post(
        "/search",
        json={"query": "test"},
        headers={"X-API-KEY": "invalid_key"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "Invalid API key" in data["detail"] or "invalid" in data["detail"].lower()


def test_missing_api_key_returns_401():
    """Missing API key should return 401 Unauthorized."""
    response = client.post(
        "/search",
        json={"query": "test"}
        # No X-API-KEY header
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "Missing" in data["detail"] or "missing" in data["detail"].lower()


def test_resolve_tenant_valid_keys():
    """resolve_tenant should correctly map valid API keys to tenants."""
    assert resolve_tenant("tenantA_key") == "tenantA"
    assert resolve_tenant("tenantB_key") == "tenantB"


def test_resolve_tenant_invalid_key():
    """resolve_tenant should raise HTTPException for invalid keys."""
    with pytest.raises(Exception):  # HTTPException from FastAPI
        resolve_tenant("invalid_key")


def test_resolve_tenant_none():
    """resolve_tenant should raise HTTPException for None/missing keys."""
    with pytest.raises(Exception):  # HTTPException from FastAPI
        resolve_tenant(None)


def test_load_tenant_documents_path_traversal_prevention():
    """load_tenant_documents should prevent path traversal attacks."""
    # Attempt path traversal
    with pytest.raises(ValueError, match="Path traversal|Invalid tenant"):
        load_tenant_documents("../../etc/passwd")
    
    with pytest.raises(ValueError, match="Path traversal|Invalid tenant"):
        load_tenant_documents("../tenantB")
    
    with pytest.raises(ValueError, match="Invalid tenant"):
        load_tenant_documents("tenantC")  # Unknown tenant


def test_load_tenant_documents_valid_tenants():
    """load_tenant_documents should work for valid tenants."""
    # Should not raise exceptions for valid tenants
    docs_a = load_tenant_documents("tenantA")
    docs_b = load_tenant_documents("tenantB")
    
    # Both should return dictionaries (may be empty if no files)
    assert isinstance(docs_a, dict)
    assert isinstance(docs_b, dict)
    
    # If documents exist, they should be loaded
    # (This depends on the actual files in the documents folder)

