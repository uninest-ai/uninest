import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_password_hash
from app.models import User, TenantProfile

@pytest.fixture
def client(override_get_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(test_db):
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("Test1234"),
        user_type="tenant"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Create tenant profile
    tenant_profile = TenantProfile(user_id=user.id)
    test_db.add(tenant_profile)
    test_db.commit()
    
    return user


def get_auth_token(client, email="test@example.com", password="Test1234"):
    """Helper function to get auth token"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return token


def test_get_current_user(client, test_user):
    """Test getting current user profile"""
    token = get_auth_token(client)
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username


def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_get_user_by_id(client, test_user):
    """Test getting a user by ID"""
    token = get_auth_token(client)
    response = client.get(
        f"/api/v1/users/{test_user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username


def test_get_nonexistent_user(client, test_user):
    """Test getting a non-existent user"""
    token = get_auth_token(client)
    response = client.get(
        "/api/v1/users/999",  # Non-existent ID
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_update_user(client, test_user):
    """Test updating user information"""
    token = get_auth_token(client)
    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "updateduser"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updateduser"
    assert data["email"] == test_user.email  # Email should remain unchanged


def test_update_user_email(client, test_user, test_db):
    """Test updating user email"""
    token = get_auth_token(client)
    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "newemail@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"
    
    # Verify DB was updated
    updated_user = test_db.query(User).filter(User.id == test_user.id).first()
    assert updated_user.email == "newemail@example.com"


def test_update_user_duplicate_email(client, test_user, test_db):
    """Test updating user with an email that already exists"""
    # Create another user
    other_user = User(
        email="other@example.com",
        username="otheruser",
        password_hash=get_password_hash("Test1234"),
        user_type="tenant"
    )
    test_db.add(other_user)
    test_db.commit()
    
    # Try to update the first user with the email of the second user
    token = get_auth_token(client)
    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "other@example.com"}
    )
    assert response.status_code == 400
    assert "Email already registered" in response.text