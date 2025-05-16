# app/recommendations.py
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.models import User, Property, UserPreference, TenantProfile, Interaction
from app import schemas

class RecommendationEngine:
    """Housing recommendation engine that implements collaborative filtering and content-based algorithms"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_property_recommendations_for_user(self, user_id: int, limit: int = 10) -> List[Tuple[Property, float]]:
        """
        Generate property recommendations for a specific user
        
        Args:
            user_id: ID of the user to generate recommendations for
            limit: Maximum number of recommendations to return
            
        Returns:
            List of (Property, score) tuples sorted by score in descending order
        """
        # Get user profile and preferences
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.user_type != "tenant":
            return []
            
        # Get tenant profile
        tenant_profile = self.db.query(TenantProfile).filter(
            TenantProfile.user_id == user_id
        ).first()
        
        if not tenant_profile:
            return []
            
        # Get user preferences
        user_prefs = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).all()
        
        # Create preference map
        pref_map = {}
        for pref in user_prefs:
            pref_map[pref.preference_key] = pref.preference_value
            
        # Get all active properties
        all_properties = self.db.query(Property).filter(Property.is_active == True).all()
        
        # Calculate scores for each property
        property_scores = []
        for prop in all_properties:
            score = self._calculate_property_score(prop, tenant_profile, pref_map)
            property_scores.append((prop, score))
            
        # Sort by score
        property_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top recommendations
        return property_scores[:limit]
    
    def get_roommate_recommendations_for_user(self, user_id: int, limit: int = 10) -> List[Tuple[User, float]]:
        """
        Generate roommate recommendations for a specific user
        
        Args:
            user_id: ID of the user to generate recommendations for
            limit: Maximum number of recommendations to return
            
        Returns:
            List of (User, score) tuples sorted by score in descending order
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.user_type != "tenant":
            return []
        
        # Get tenant profile
        tenant_profile = self.db.query(TenantProfile).filter(
            TenantProfile.user_id == user_id
        ).first()
        
        if not tenant_profile:
            return []
        
        # Get all potential roommates (tenant users that are not the current user)
        potential_roommates = self.db.query(User).filter(
            User.user_type == "tenant",
            User.id != user_id
        ).all()
        
        # Calculate match scores
        roommate_scores = []
        for roommate in potential_roommates:
            score = self._calculate_roommate_compatibility(user_id, roommate.id)
            roommate_scores.append((roommate, score))
        
        # Sort by score
        roommate_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top recommendations
        return roommate_scores[:limit]
    
    def _calculate_property_score(self, property: Property, tenant_profile: TenantProfile, 
                                 preferences: Dict[str, Any]) -> float:
        """Calculate match score between a property and user preferences"""
        score = 0.0
        
        # Budget match (higher score if property price is within budget)
        if tenant_profile.budget and property.price <= tenant_profile.budget:
            score += 0.3
        elif tenant_profile.budget:
            # Score decreases as price exceeds budget
            price_ratio = tenant_profile.budget / property.price if property.price > 0 else 0
            score += 0.3 * max(0, min(1, price_ratio))
        
        # Location match
        if tenant_profile.preferred_location and property.city:
            if tenant_profile.preferred_location.lower() == property.city.lower():
                score += 0.3
            elif property.address and tenant_profile.preferred_location.lower() in property.address.lower():
                score += 0.2
        
        # Property type match
        if preferences.get('property_type') and property.property_type:
            if preferences['property_type'].lower() == property.property_type.lower():
                score += 0.2
        
        # Bedroom match
        if preferences.get('bedrooms') and property.bedrooms:
            if int(preferences['bedrooms']) == property.bedrooms:
                score += 0.1
        
        # Bathroom match
        if preferences.get('bathrooms') and property.bathrooms:
            if float(preferences['bathrooms']) == property.bathrooms:
                score += 0.1
        
        return score
    
    def _calculate_roommate_compatibility(self, user_id1: int, user_id2: int) -> float:
        """Calculate compatibility score between two potential roommates"""
        # Get tenant profiles
        profile1 = self.db.query(TenantProfile).filter(
            TenantProfile.user_id == user_id1
        ).first()
        
        profile2 = self.db.query(TenantProfile).filter(
            TenantProfile.user_id == user_id2
        ).first()
        
        if not profile1 or not profile2:
            return 0.0
        
        score = 0.0
        
        # Budget compatibility (closer budgets = higher score)
        if profile1.budget and profile2.budget:
            budget_diff = abs(profile1.budget - profile2.budget)
            max_budget = max(profile1.budget, profile2.budget)
            budget_score = 1.0 - (budget_diff / max_budget if max_budget > 0 else 0)
            score += 0.3 * budget_score
        
        # Location preference match
        if profile1.preferred_location and profile2.preferred_location:
            if profile1.preferred_location.lower() == profile2.preferred_location.lower():
                score += 0.3
        
        # Get user preferences
        prefs1 = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id1,
            UserPreference.preference_category == "lifestyle"
        ).all()
        
        prefs2 = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id2,
            UserPreference.preference_category == "lifestyle"
        ).all()
        
        # Create preference maps
        pref_map1 = {p.preference_key: p.preference_value for p in prefs1}
        pref_map2 = {p.preference_key: p.preference_value for p in prefs2}
        
        # Lifestyle preference match
        matching_prefs = 0
        total_prefs = len(set(pref_map1.keys()).union(set(pref_map2.keys())))
        
        for key in pref_map1:
            if key in pref_map2 and pref_map1[key] == pref_map2[key]:
                matching_prefs += 1
        
        if total_prefs > 0:
            score += 0.4 * (matching_prefs / total_prefs)
        
        return score

def get_property_recommendations_for_user(db: Session, user_id: int, limit: int = 10) -> List[Tuple[Property, float]]:
    """Wrapper function to get property recommendations using the RecommendationEngine"""
    engine = RecommendationEngine(db)
    return engine.get_property_recommendations_for_user(user_id, limit)

def get_roommate_recommendations_for_user(db: Session, user_id: int, limit: int = 10) -> List[Tuple[User, float]]:
    """Wrapper function to get roommate recommendations using the RecommendationEngine"""
    engine = RecommendationEngine(db)
    return engine.get_roommate_recommendations_for_user(user_id, limit)