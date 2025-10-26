# app/routes/recommendations.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database import get_db
from app.models import User, Property, UserPreference, TenantProfile
from app.auth import get_current_user
from app import recommendations
from app import schemas  # Add this import to fix the previous error
from app.services.hybrid_search import hybrid_search_simple  # Import hybrid search function

router = APIRouter()  # This line was missing

@router.get("/properties", response_model=List[schemas.PropertyRecommendation])
def get_property_recommendations(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Based on user preferences, recommend properties using hybrid search"""
    if current_user.user_type != "tenant":
        raise HTTPException(status_code=403, detail="Only tenants can receive property recommendations")

    # Get user tenant profile
    tenant_profile = db.query(TenantProfile).filter(
        TenantProfile.user_id == current_user.id
    ).first()

    if not tenant_profile:
        raise HTTPException(status_code=404, detail="Tenant profile not found")

    # Get user preferences
    user_preferences = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).all()

    # Build search query from user preferences
    search_terms = []

    # Add tenant profile information
    if tenant_profile.preferred_location:
        search_terms.append(tenant_profile.preferred_location)

    # Add preference values as search terms
    for pref in user_preferences:
        # Use preference value as search term
        if pref.preference_value and pref.preference_value.strip():
            search_terms.append(pref.preference_value)

    # If no preferences, use default search
    if not search_terms:
        search_terms = ["apartment", "house"]

    # Combine search terms into a query
    search_query = " ".join(search_terms)

    # Use hybrid search to find properties
    search_results = hybrid_search_simple(db=db, query=search_query, limit=limit)

    # Update recommendation relationships
    if search_results:
        # Get property IDs from search results
        property_ids = [result["id"] for result in search_results]

        # Fetch property objects for updating relationships
        top_properties = db.query(Property).filter(Property.id.in_(property_ids)).all()

        # Clear existing recommendations
        tenant_profile.recommended_properties = []
        db.flush()

        # Add new recommendations
        tenant_profile.recommended_properties = top_properties
        db.commit()

    # Build response from hybrid search results
    return [
        {
            "id": result["id"],
            "title": result["title"],
            "price": result["price"],
            "description": result["description"],
            "image_url": result.get("image_url"),
            "api_images": result.get("api_images", []),
            "property_type": result["property_type"],
            "bedrooms": result["bedrooms"],
            "bathrooms": result["bathrooms"],
            "area": result.get("area", 0),
            "address": result["address"],
            "city": result["city"],
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "match_score": round(result["scores"]["hybrid_rrf"] * 100)  # Convert to percentage
        }
        for result in search_results
    ]

@router.get("/roommates", response_model=List[schemas.RoommateRecommendation])
def get_roommate_recommendations(
    limit: int = Query(10, ge=1, le=100),
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
        # Get top recommended roommates up to the limit
        top_roommates = [rec[0] for rec in roommate_recommendations[:limit]]
        
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