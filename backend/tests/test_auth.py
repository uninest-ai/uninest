import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_password_hash
from app.models import User

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
    return user


def test_register_user(client):
    """Test user registration endpoint"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "Password123",
            "confirm_password": "Password123",
            "user_type": "tenant"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "password" not in data


def test_register_duplicate_email(client, test_user):
    """Test registration with an existing email address"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",  # Same as test_user
            "username": "anotheruser",
            "password": "Password123",
            "confirm_password": "Password123",
            "user_type": "tenant"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.text


def test_register_password_mismatch(client):
    """Test registration with mismatched passwords"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "Password123",
            "confirm_password": "DifferentPassword123",
            "user_type": "tenant"
        }
    )
    assert response.status_code == 422  # Validation error


def test_login_user(client, test_user):
    """Test user login endpoint"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Test1234"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Test login with a non-existent user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "Test1234"}
    )
    assert response.status_code == 401