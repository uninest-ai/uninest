# app/routes/recommendations.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database import get_db
from app.models import User, Property, UserPreference, TenantProfile
from app.auth import get_current_user
from app import recommendations
from app import schemas

router = APIRouter() 

@router.get("/properties", response_model=List[schemas.PropertyRecommendation])
def get_property_recommendations(
    limit: int = Query(10, ge=1, le=50), # show limit can be change from front
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Based on user preferences, recommend properties"""
    if current_user.user_type != "tenant":
        raise HTTPException(status_code=403, detail="Only tenants can receive property recommendations")
    
    # Get user tenant profile
    tenant_profile = db.query(TenantProfile).filter(
        TenantProfile.user_id == current_user.id
    ).first()
    
    if not tenant_profile:
        raise HTTPException(status_code=404, detail="Tenant profile not found")
    
    # Use recommendation engine to get recommendations
    property_recommendations = recommendations.get_property_recommendations_for_user(
        db, current_user.id, limit
    )
    
    # Update recommendation relationships
    if property_recommendations:
        # Get top 10 recommended properties
        top_properties = [rec[0] for rec in property_recommendations[:10]]
        
        # Clear existing recommendations
        tenant_profile.recommended_properties = []
        db.flush()
        
        # Add new recommendations
        tenant_profile.recommended_properties = top_properties
        db.commit()
    
    # Build response
    return [
        {
            "id": p[0].id,
            "title": p[0].title,
            "price": p[0].price,
            "description": p[0].description,
            "image_url": p[0].image_url,
            "property_type": p[0].property_type,
            "bedrooms": p[0].bedrooms,
            "bathrooms": p[0].bathrooms,
            "area": p[0].area,
            "address": p[0].address,
            "city": p[0].city,
            "latitude": p[0].latitude,
            "longitude": p[0].longitude,
            "match_score": round(p[1] * 100)  # Convert to percentage
        }
        for p in property_recommendations
    ]

@router.get("/roommates", response_model=List[schemas.RoommateRecommendation])
def get_roommate_recommendations(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Based on user preferences, recommend potential roommates"""
    if current_user.user_type != "tenant":
        raise HTTPException(status_code=403, detail="Only tenants can receive roommate recommendations")
    
    # Get user tenant profile
    tenant_profile = db.query(TenantProfile).filter(
        TenantProfile.user_id == current_user.id
    ).first()
    
    if not tenant_profile:
        raise HTTPException(status_code=404, detail="Tenant profile not found")
    
    # Use recommendation engine to get recommendations
    roommate_recommendations = recommendations.get_roommate_recommendations_for_user(
        db, current_user.id, limit
    )
    
    # Update recommendation relationships
    if roommate_recommendations:
        # Get top 10 recommended roommates
        top_roommates = [rec[0] for rec in roommate_recommendations[:10]]
        
        # Clear existing recommendations
        tenant_profile.recommended_roommates = []
        db.flush()
        
        # Add new recommendations
        tenant_profile.recommended_roommates = top_roommates
        db.commit()
    
    # Build response
    return [
        {
            "id": r[0].id,
            "username": r[0].username,
            "email": r[0].email,
            "match_score": round(r[1] * 100),  # Convert to percentage
            "tenant_profile": {
                "budget": r[0].tenant_profile.budget if r[0].tenant_profile else None,
                "preferred_location": r[0].tenant_profile.preferred_location if r[0].tenant_profile else None
            } if r[0].tenant_profile else None
        }
        for r in roommate_recommendations
    ]