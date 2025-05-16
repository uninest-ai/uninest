import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_password_hash
from app.models import User, Property, LandlordProfile

@pytest.fixture
def client(override_get_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_landlord(test_db):
    landlord = User(
        email="landlord@example.com",
        username="landlorduser",
        password_hash=get_password_hash("Test1234"),
        user_type="landlord"
    )
    test_db.add(landlord)
    test_db.commit()
    test_db.refresh(landlord)
    
    landlord_profile = LandlordProfile(user_id=landlord.id)
    test_db.add(landlord_profile)
    test_db.commit()
    test_db.refresh(landlord_profile)
    
    return landlord


@pytest.fixture
def test_property(test_db, test_landlord):
    # First get the landlord's profile
    landlord_profile = test_db.query(LandlordProfile).filter(
        LandlordProfile.user_id == test_landlord.id
    ).first()
    
    property = Property(
        title="Test Property",
        price=1500.0,
        description="A nice test property",
        property_type="apartment",
        bedrooms=2,
        bathrooms=1.5,
        area=1000.0,
        landlord_id=landlord_profile.id
    )
    test_db.add(property)
    test_db.commit()
    test_db.refresh(property)
    return property


def get_auth_token(client, email="landlord@example.com", password="Test1234"):
    """Helper function to get auth token"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return token


def test_create_property(client, test_landlord):
    """Test creating a new property"""
    token = get_auth_token(client)
    response = client.post(
        "/api/v1/properties/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "New Property",
            "price": 1200.0,
            "description": "A brand new property",
            "property_type": "apartment",
            "bedrooms": 2,
            "bathrooms": 1.0,
            "area": 900.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Property"
    assert data["price"] == 1200.0
    assert data["bedrooms"] == 2


def test_get_properties(client, test_property):
    """Test getting all properties"""
    response = client.get("/api/v1/properties/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(prop["title"] == test_property.title for prop in data)


def test_get_property_by_id(client, test_property):
    """Test getting a specific property by ID"""
    response = client.get(f"/api/v1/properties/{test_property.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == test_property.title
    assert data["price"] == test_property.price
    assert data["description"] == test_property.description


def test_get_nonexistent_property(client):
    """Test getting a non-existent property"""
    response = client.get("/api/v1/properties/999")  # Non-existent ID
    assert response.status_code == 404


def test_update_property(client, test_property, test_landlord):
    """Test updating a property"""
    token = get_auth_token(client)
    response = client.put(
        f"/api/v1/properties/{test_property.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Property",
            "price": 1600.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Property"
    assert data["price"] == 1600.0
    # Other fields should remain unchanged
    assert data["description"] == test_property.description


def test_update_property_unauthorized(client, test_property, test_db):
    """Test updating a property by someone who doesn't own it"""
    # Create a tenant user
    tenant = User(
        email="tenant@example.com",
        username="tenantuser",
        password_hash=get_password_hash("Test1234"),
        user_type="tenant"
    )
    test_db.add(tenant)
    test_db.commit()
    
    # Get token for tenant
    token = get_auth_token(client, email="tenant@example.com")
    
    # Try to update the property
    response = client.put(
        f"/api/v1/properties/{test_property.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Unauthorized Update"}
    )
    # This should fail with a 403 Forbidden
    assert response.status_code == 403


def test_delete_property(client, test_property, test_landlord):
    """Test deleting a property"""
    token = get_auth_token(client)
    response = client.delete(
        f"/api/v1/properties/{test_property.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
    
    # Verify property is deleted
    response = client.get(f"/api/v1/properties/{test_property.id}")
    assert response.status_code == 404


def test_delete_property_unauthorized(client, test_property, test_db):
    """Test deleting a property by someone who doesn't own it"""
    # Create a tenant user
    tenant = User(
        email="tenant@example.com",
        username="tenantuser",
        password_hash=get_password_hash("Test1234"),
        user_type="tenant"
    )
    test_db.add(tenant)
    test_db.commit()
    
    # Get token for tenant
    token = get_auth_token(client, email="tenant@example.com")
    
    # Try to delete the property
    response = client.delete(
        f"/api/v1/properties/{test_property.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    # This should fail with a 403 Forbidden
    assert response.status_code == 403