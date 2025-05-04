from app import schemas
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import User, LandlordProfile, TenantProfile, UserPreference
from app.schemas import (
    LandlordProfileCreate, LandlordProfile as LandlordProfileSchema,
    TenantProfileCreate, TenantProfile as TenantProfileSchema,
    LandlordProfileUpdate, TenantProfileUpdate
)
from app.auth import get_current_user

router = APIRouter()

# Landlord profile endpoints
@router.post("/landlord", response_model=LandlordProfileSchema, status_code=status.HTTP_201_CREATED)
def create_landlord_profile(
    profile_data: LandlordProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a landlord profile for the current user
    """
    # Check if user is already a tenant
    if current_user.user_type == "tenant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant users cannot create landlord profiles"
        )
    
    # Check if user already has a landlord profile
    existing_profile = db.query(LandlordProfile).filter(
        LandlordProfile.user_id == current_user.id
    ).first()
    
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Landlord profile already exists"
        )
    
    # Create landlord profile with specific fields that match the model
    db_profile = LandlordProfile(
        user_id=current_user.id,
        company_name=profile_data.company_name,
        contact_phone=profile_data.contact_phone,
        description=profile_data.description
    )
    
    # Update user's user type flag
    current_user.user_type = "landlord"
    
    # Save to database
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return db_profile

@router.get("/landlord", response_model=LandlordProfileSchema)
def get_my_landlord_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's landlord profile with their properties
    """
    profile = db.query(LandlordProfile).filter(
        LandlordProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landlord profile not found"
        )
    
    db.refresh(profile)
    
    return profile

@router.put("/landlord", response_model=LandlordProfileSchema)
def update_landlord_profile(
    profile_data: LandlordProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the current user's landlord profile
    """
    profile = db.query(LandlordProfile).filter(
        LandlordProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landlord profile not found"
        )
    
    # Update profile attributes that exist in the model
    data_dict = profile_data.dict(exclude_unset=True)
    
    if "company_name" in data_dict:
        profile.company_name = data_dict["company_name"]
    if "contact_phone" in data_dict:
        profile.contact_phone = data_dict["contact_phone"]
    if "description" in data_dict:
        profile.description = data_dict["description"]
    
    db.commit()
    db.refresh(profile)
    
    return profile

# Tenant profile endpoints
@router.post("/tenant", response_model=TenantProfileSchema, status_code=status.HTTP_201_CREATED)
def create_tenant_profile(
    profile_data: TenantProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a tenant profile for the current user
    """
    # Check if user is already a landlord
    if current_user.user_type == "landlord":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Landlord users cannot create tenant profiles"
        )
    
    # Check if user already has a tenant profile
    existing_profile = db.query(TenantProfile).filter(
        TenantProfile.user_id == current_user.id
    ).first()
    
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant profile already exists"
        )
    
    # Create tenant profile with specific fields that match the model
    db_profile = TenantProfile(
        user_id=current_user.id,
        budget=profile_data.budget,
        preferred_location=profile_data.preferred_location,
        preferred_core_lat=profile_data.preferred_core_lat,
        preferred_core_lng=profile_data.preferred_core_lng
    )
    
    # Update user's user_type flag
    current_user.user_type = "tenant"
    
    # Save to database
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return db_profile

@router.get("/tenant", response_model=TenantProfileSchema)
def get_my_tenant_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's tenant profile
    """
    profile = db.query(TenantProfile).filter(
        TenantProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant profile not found"
        )
    
    return profile

@router.put("/tenant", response_model=TenantProfileSchema)
def update_tenant_profile(
    profile_data: TenantProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update tenant"""
    # Check
    if current_user.user_type != "tenant":
        raise HTTPException(status_code=403, detail="Only tenants can update tenant profiles")
    
    profile = db.query(TenantProfile).filter(TenantProfile.user_id == current_user.id).first()
    if not profile:
        profile = TenantProfile(user_id=current_user.id)
        db.add(profile)
    
    # Update only fields that exist in the model
    data_dict = profile_data.dict(exclude_unset=True)
    
    if "budget" in data_dict:
        profile.budget = data_dict["budget"]
    if "preferred_location" in data_dict:
        profile.preferred_location = data_dict["preferred_location"]
    if "preferred_core_lat" in data_dict:
        profile.preferred_core_lat = data_dict["preferred_core_lat"]
    if "preferred_core_lng" in data_dict:
        profile.preferred_core_lng = data_dict["preferred_core_lng"]
    
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/preferences", response_model=List[schemas.UserPreference])
def get_user_preferences(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all preferences for the current user
    
    Args:
        category: Optional filter by preference category 
                (e.g., 'lifestyle', 'property', 'roommate', 'location', 'tenant_ideal_home')
    
    Returns:
        List of user preferences
    """
    # Build query
    query = db.query(UserPreference).filter(UserPreference.user_id == current_user.id)
    
    if category:
        query = query.filter(UserPreference.preference_category == category)
    
    preferences = query.all()
    return preferences

@router.post("/preferences", response_model=schemas.UserPreference, status_code=status.HTTP_201_CREATED)
def add_user_preference(
    preference_data: schemas.UserPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new preference for the current user
    
    Args:
        preference_data: User preference to add
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Created user preference
    """
    # Create new preference
    new_preference = UserPreference(
        user_id=current_user.id,
        preference_key=preference_data.preference_key,
        preference_value=preference_data.preference_value,
        preference_category=preference_data.preference_category,
        source="manual_input"
    )
    
    # Save to database
    db.add(new_preference)
    db.commit()
    db.refresh(new_preference)
    
    return new_preference

@router.delete("/preferences/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_preference(
    preference_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user preference
    
    Args:
        preference_id: ID of the preference to delete
        current_user: Authenticated user
        db: Database session
    """
    # Find preference
    preference = db.query(UserPreference).filter(
        UserPreference.id == preference_id,
        UserPreference.user_id == current_user.id
    ).first()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found or does not belong to current user"
        )
    
    # Delete preference
    db.delete(preference)
    db.commit()
    
    return None