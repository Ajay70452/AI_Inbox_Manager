"""
Company Context Tests

Tests for company context management
"""

import pytest
from models import CompanyContext


def test_create_company_context(client, test_user, auth_headers):
    """Test creating company context"""
    response = client.post(
        "/api/v1/company-context",
        json={
            "context_type": "policy",
            "title": "Email Response Policy",
            "content": "Always respond within 24 hours"
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Email Response Policy"
    assert data["context_type"] == "policy"


def test_list_company_contexts(client, test_user, auth_headers, db_session):
    """Test listing company contexts"""
    # Create test contexts
    context1 = CompanyContext(
        user_id=test_user.id,
        context_type="policy",
        title="Test Policy",
        content="Test content"
    )
    context2 = CompanyContext(
        user_id=test_user.id,
        context_type="faq",
        title="Test FAQ",
        content="Test FAQ content"
    )
    db_session.add_all([context1, context2])
    db_session.commit()

    response = client.get("/api/v1/company-context", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_company_context_by_id(client, test_user, auth_headers, db_session):
    """Test getting a specific company context"""
    context = CompanyContext(
        user_id=test_user.id,
        context_type="policy",
        title="Test Policy",
        content="Test content"
    )
    db_session.add(context)
    db_session.commit()
    db_session.refresh(context)

    response = client.get(
        f"/api/v1/company-context/{context.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Policy"


def test_update_company_context(client, test_user, auth_headers, db_session):
    """Test updating company context"""
    context = CompanyContext(
        user_id=test_user.id,
        context_type="policy",
        title="Test Policy",
        content="Test content"
    )
    db_session.add(context)
    db_session.commit()
    db_session.refresh(context)

    response = client.put(
        f"/api/v1/company-context/{context.id}",
        json={
            "context_type": "policy",
            "title": "Updated Policy",
            "content": "Updated content"
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Policy"
    assert data["content"] == "Updated content"


def test_delete_company_context(client, test_user, auth_headers, db_session):
    """Test deleting company context"""
    context = CompanyContext(
        user_id=test_user.id,
        context_type="policy",
        title="Test Policy",
        content="Test content"
    )
    db_session.add(context)
    db_session.commit()
    db_session.refresh(context)

    response = client.delete(
        f"/api/v1/company-context/{context.id}",
        headers=auth_headers
    )

    assert response.status_code == 200

    # Verify it's deleted
    response = client.get(
        f"/api/v1/company-context/{context.id}",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_get_context_by_type(client, test_user, auth_headers, db_session):
    """Test filtering contexts by type"""
    context1 = CompanyContext(
        user_id=test_user.id,
        context_type="policy",
        title="Test Policy",
        content="Test content"
    )
    context2 = CompanyContext(
        user_id=test_user.id,
        context_type="faq",
        title="Test FAQ",
        content="Test FAQ content"
    )
    db_session.add_all([context1, context2])
    db_session.commit()

    response = client.get(
        "/api/v1/company-context?context_type=policy",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["context_type"] == "policy"
