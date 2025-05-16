import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_password_hash
from app.models import User, Property, UserPreference, TenantProfile, LandlordProfile

@pytest.fixture
def client(override_get_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_tenant(test_db):
    """Create a test tenant with preferences"""
    tenant = User(
        email="tenant@example.com",
        username="tenantuser",
        password_hash=get_password_hash("Test1234"),
        user_type="tenant"
    )
    test_db.add(tenant)
    test_db.commit()
    test_db.refresh(tenant)
    
    # Create tenant profile
    profile = TenantProfile(
        user_id=tenant.id,
        budget=1500.0,
        preferred_location="Pittsburgh"
    )
    test_db.add(profile)
    
    # Add preferences
    preferences = [
        UserPreference(
            user_id=tenant.id,
            preference_key="property_type",
            preference_value="apartment",
            preference_category="property",
            source="test"
        ),
        UserPreference(
            user_id=tenant.id,
            preference_key="bedrooms",
            preference_value="2",
            preference_category="property",
            source="test"
        ),
        UserPreference(
            user_id=tenant.id,
            preference_key="bathrooms",
            preference_value="1.5",
            preference_category="property",
            source="test"
        )
    ]
    for pref in preferences:
        test_db.add(pref)
    
    test_db.commit()
    return tenant


@pytest.fixture
def test_landlord(test_db):
    """Create a test landlord with properties"""
    landlord = User(
        email="landlord@example.com",
        username="landlorduser",
        password_hash=get_password_hash("Test1234"),
        user_type="landlord"
    )
    test_db.add(landlord)
    test_db.commit()
    test_db.refresh(landlord)
    
    # Create landlord profile
    landlord_profile = LandlordProfile(user_id=landlord.id)
    test_db.add(landlord_profile)
    test_db.commit()
    test_db.refresh(landlord_profile)
    
    return landlord


@pytest.fixture
def test_properties(test_db, test_landlord):
    """Create test properties for recommendations"""
    landlord_profile = test_db.query(LandlordProfile).filter(
        LandlordProfile.user_id == test_landlord.id
    ).first()
    
    # Create several properties with different attributes
    properties = [
        Property(
            title="Matching Apartment 1",
            price=1200.0,
            description="Perfect match for preferences",
            property_type="apartment",
            bedrooms=2,
            bathrooms=1.5,
            area=1000.0,
            city="Pittsburgh",
            landlord_id=landlord_profile.id,
            is_active=True
        ),
        Property(
            title="Matching Apartment 2",
            price=1400.0,
            description="Another good match",
            property_type="apartment",
            bedrooms=2,
            bathrooms=1.0,
            area=950.0,
            city="Pittsburgh",
            landlord_id=landlord_profile.id,
            is_active=True
        ),
        Property(
            title="Non-matching House",
            price=2500.0,
            description="Much more expensive house",
            property_type="house",
            bedrooms=4,
            bathrooms=3.0,
            area=2000.0,
            city="Philadelphia",
            landlord_id=landlord_profile.id,
            is_active=True
        ),
        Property(
            title="Inactive Property",
            price=1300.0,
            description="Good match but inactive",
            property_type="apartment",
            bedrooms=2,
            bathrooms=1.5,
            area=1000.0,
            city="Pittsburgh",
            landlord_id=landlord_profile.id,
            is_active=False
        )
    ]
    
    for prop in properties:
        test_db.add(prop)
    
    test_db.commit()
    return properties


@pytest.fixture
def test_roommates(test_db):
    """Create potential roommates for tests"""
    roommates = [
        User(
            email="roommate1@example.com",
            username="roommate1",
            password_hash=get_password_hash("Test1234"),
            user_type="tenant"
        ),
        User(
            email="roommate2@example.com",
            username="roommate2",
            password_hash=get_password_hash("Test1234"),
            user_type="tenant"
        )
    ]
    
    for roommate in roommates:
        test_db.add(roommate)
    
    test_db.commit()
    
    # Create profiles for the roommates
    roommate1 = test_db.query(User).filter(User.email == "roommate1@example.com").first()
    roommate2 = test_db.query(User).filter(User.email == "roommate2@example.com").first()
    
    profiles = [
        TenantProfile(
            user_id=roommate1.id,
            budget=1600.0,
            preferred_location="Pittsburgh"
        ),
        TenantProfile(
            user_id=roommate2.id,
            budget=1200.0,
            preferred_location="Oakland"
        )
    ]
    
    for profile in profiles:
        test_db.add(profile)
    
    test_db.commit()
    return roommates


def get_auth_token(client, email="tenant@example.com", password="Test1234"):
    """Helper function to get auth token"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return token


def test_get_property_recommendations(client, test_tenant, test_properties):
    """Test getting property recommendations"""
    token = get_auth_token(client)
    response = client.get(
        "/api/v1/recommendations/properties",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # There should be some recommendations
    assert len(data) > 0
    
    # The matching properties should have higher scores
    matching_props = [p for p in data if "Matching" in p["title"]]
    non_matching_props = [p for p in data if "Non-matching" in p["title"]]
    
    print("Matching properties:", matching_props)
    print("Non-matching properties:", non_matching_props)
    # If we have both matching and non-matching, check scores
    if matching_props and non_matching_props:
        assert max(p["match_score"] for p in matching_props) > max(p["match_score"] for p in non_matching_props)
    
    # Inactive properties should not be in recommendations
    inactive_props = [p for p in data if "Inactive" in p["title"]]
    assert len(inactive_props) == 0


def test_get_property_recommendations_unauthorized(client):
    """Test getting recommendations without auth"""
    response = client.get("/api/v1/recommendations/properties")
    assert response.status_code == 401


def test_get_roommate_recommendations(client, test_tenant, test_roommates):
    """Test getting roommate recommendations"""
    token = get_auth_token(client)
    response = client.get(
        "/api/v1/recommendations/roommates",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # There should be some recommendations
    assert len(data) > 0
    
    # Check that we're getting expected data structure
    for roommate in data:
        print("recommendation:", roommate)
        assert "id" in roommate
        assert "username" in roommate
        assert "email" in roommate
        assert "match_score" in roommate
        if "tenant_profile" in roommate and roommate["tenant_profile"]:
            assert "budget" in roommate["tenant_profile"]
            assert "preferred_location" in roommate["tenant_profile"]


def test_get_roommate_recommendations_as_landlord(client, test_db):
    """Test that landlords can't get roommate recommendations"""
    # Create a landlord user
    landlord = User(
        email="onlylanlord@example.com",
        username="onlylanlord",
        password_hash=get_password_hash("Test1234"),
        user_type="landlord"
    )
    test_db.add(landlord)
    test_db.commit()
    
    # Get token for landlord
    token = get_auth_token(client, email="onlylanlord@example.com")
    
    # Try to get roommate recommendations
    response = client.get(
        "/api/v1/recommendations/roommates",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # This should fail with a 403 Forbidden
    assert response.status_code == 403