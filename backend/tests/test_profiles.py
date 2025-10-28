import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_password_hash
from app.models import User, TenantProfile, LandlordProfile

@pytest.fixture
def client(override_get_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_tenant(test_db):
    user = User(
        email="tenant@example.com",
        username="tenantuser",
        password_hash=get_password_hash("Test1234"),
        user_type="tenant"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_landlord(test_db):
    user = User(
        email="landlord@example.com",
        username="landlorduser",
        password_hash=get_password_hash("Test1234"),
        user_type="landlord"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def get_auth_token(client, email, password="Test1234"):
    """Helper function to get auth token"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return token


# Tenant Profile Tests
def test_create_tenant_profile(client, test_tenant):
    """Test creating a tenant profile"""
    token = get_auth_token(client, test_tenant.email)
    response = client.post(
        "/api/v1/profile/tenant",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 1200.0,
            "preferred_location": "New York",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["budget"] == 1200.0
    assert data["preferred_location"] == "New York"


def test_get_tenant_profile(client, test_tenant, test_db):
    """Test retrieving a tenant profile"""
    # First create a profile
    profile = TenantProfile(
        user_id=test_tenant.id,
        budget=1500.0,
        preferred_location="Oakland"
    )
    test_db.add(profile)
    test_db.commit()
    
    # Get the profile
    token = get_auth_token(client, test_tenant.email)
    response = client.get(
        "/api/v1/profile/tenant",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["budget"] == 1500.0
    assert data["preferred_location"] == "Oakland"


def test_update_tenant_profile(client, test_tenant, test_db):
    """Test updating a tenant profile"""
    # First create a profile
    profile = TenantProfile(
        user_id=test_tenant.id,
        budget=1000.0,
        preferred_location="Shadyside"
    )
    test_db.add(profile)
    test_db.commit()
    
    # Update the profile
    token = get_auth_token(client, test_tenant.email)
    response = client.put(
        "/api/v1/profile/tenant",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 1200.0,
            "preferred_location": "Oakland"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["budget"] == 1200.0
    assert data["preferred_location"] == "Oakland"


def test_get_nonexistent_tenant_profile(client, test_tenant):
    """Test getting a tenant profile that doesn't exist yet"""
    token = get_auth_token(client, test_tenant.email)
    response = client.get(
        "/api/v1/profile/tenant",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


# Landlord Profile Tests
def test_create_landlord_profile(client, test_landlord):
    """Test creating a landlord profile"""
    token = get_auth_token(client, test_landlord.email)
    response = client.post(
        "/api/v1/profile/landlord",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_name": "Best Properties LLC",
            "contact_phone": "412-555-1234",
            "description": "We offer the best rental properties in Pittsburgh"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == "Best Properties LLC"
    assert data["contact_phone"] == "412-555-1234"


def test_get_landlord_profile(client, test_landlord, test_db):
    """Test retrieving a landlord profile"""
    # First create a profile
    profile = LandlordProfile(
        user_id=test_landlord.id,
        company_name="Real Estate Inc",
        contact_phone="412-555-6789"
    )
    test_db.add(profile)
    test_db.commit()
    
    # Get the profile
    token = get_auth_token(client, test_landlord.email)
    response = client.get(
        "/api/v1/profile/landlord",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Real Estate Inc"
    assert data["contact_phone"] == "412-555-6789"


def test_update_landlord_profile(client, test_landlord, test_db):
    """Test updating a landlord profile"""
    # First create a profile
    profile = LandlordProfile(
        user_id=test_landlord.id,
        company_name="Old Name Realty",
        contact_phone="412-555-9999"
    )
    test_db.add(profile)
    test_db.commit()
    
    # Update the profile
    token = get_auth_token(client, test_landlord.email)
    response = client.put(
        "/api/v1/profile/landlord",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_name": "New Name Properties",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "New Name Properties"
    assert data["contact_phone"] == "412-555-9999"  # Should remain unchanged


def test_get_nonexistent_landlord_profile(client, test_landlord):
    """Test getting a landlord profile that doesn't exist yet"""
    token = get_auth_token(client, test_landlord.email)
    response = client.get(
        "/api/v1/profile/landlord",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_wrong_user_type_for_profile(client, test_db):
    """Test tenant trying to create landlord profile and vice versa"""
    # Create a test tenant
    tenant = User(
        email="tenant_only@example.com",
        username="tenantonly",
        password_hash=get_password_hash("Test1234"),
        user_type="tenant"
    )
    test_db.add(tenant)
    test_db.commit()
    
    # Tenant tries to create landlord profile
    token = get_auth_token(client, "tenant_only@example.com")
    response = client.post(
        "/api/v1/profile/landlord",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_name": "Invalid Company",
            "contact_phone": "412-555-0000"
        }
    )
    # Should fail with a 403 Forbidden
    assert response.status_code == 403