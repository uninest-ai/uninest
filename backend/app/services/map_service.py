from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Property, User, Interaction
from app.utils.geo_utils import get_nearby_properties

class MapService:
    """
    Service for map-related operations and recommendations
    """
    def __init__(self, db: Session):
        self.db = db
        
    def has_user_interacted(self, user_id: int, property_id: int) -> bool:
        """
        Check if a user has interacted with a specific property
        """
        interaction = self.db.query(Interaction).filter(
            Interaction.user_id == user_id,
            Interaction.property_id == property_id
        ).first()
        
        return bool(interaction)
    
    def get_properties_for_map(
        self,
        user: User,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: float = 5.0,
        max_price: Optional[float] = None,
        limit: int = 20
    ) -> List[dict]:
        """
        Get properties for map display with user-specific enhancements
        """
        # Base query for properties
        query = self.db.query(Property)
        
        # Apply price filter if provided
        if max_price:
            query = query.filter(Property.price <= max_price)
        
        # Get properties based on location
        if latitude and longitude:
            # Get properties within radius
            properties = get_nearby_properties(self.db, latitude, longitude, radius)
            # Limit results
            properties = properties[:limit]
        else:
            # If no location provided, sort by proximity to CMU
            properties = query.order_by(Property.distance_to_core).limit(limit).all()
        
        # Enhanced response with user-specific data
        result = []
        for prop in properties:
            # Check if user has interacted with this property
            interaction = self.db.query(Interaction).filter(
                Interaction.user_id == user.id,
                Interaction.property_id == prop.id
            ).first()
            
            # Create response dictionary
            prop_dict = {
                "id": prop.id,
                "title": prop.title,
                "price": prop.price,
                "latitude": prop.latitude,
                "longitude": prop.longitude,
                "image_url": prop.image_url,
                "address": prop.address,
                "city": prop.city,
                "has_interacted": bool(interaction),
                "distance_to_core": prop.distance_to_core,
                "distance": getattr(prop, "distance", None)
            }
            
            result.append(prop_dict)
        
        return result
    
    def get_personalized_map_recommendations(
        self,
        user: User,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        limit: int = 20
    ) -> List[dict]:
        """
        Get personalized property recommendations for the map based on user preferences
        and interaction history
        """
        # Get user's interactions to determine preferences
        user_interactions = self.db.query(Interaction).filter(
            Interaction.user_id == user.id,
            Interaction.action.in_(["view", "like", "save"])
        ).all()
        
        # If user has interactions, use them to determine preferences
        if user_interactions:
            # Get properties the user has interacted with
            interacted_property_ids = [i.property_id for i in user_interactions]
            interacted_properties = self.db.query(Property).filter(
                Property.id.in_(interacted_property_ids)
            ).all()
            
            # Calculate average price of properties the user is interested in
            if interacted_properties:
                avg_price = sum(p.price for p in interacted_properties) / len(interacted_properties)
                price_range = (avg_price * 0.7, avg_price * 1.3)  # +/- 30%
                
                # Find similar properties based on price range
                query = self.db.query(Property).filter(
                    Property.id.notin_(interacted_property_ids),
                    Property.price.between(price_range[0], price_range[1])
                )
                
                # If location provided, use it to sort
                if latitude and longitude:
                    properties = get_nearby_properties(self.db, latitude, longitude)
                    # Filter by price range
                    properties = [p for p in properties if price_range[0] <= p.price <= price_range[1]]
                    # Filter out already interacted properties
                    properties = [p for p in properties if p.id not in interacted_property_ids]
                    # Limit results
                    properties = properties[:limit]
                else:
                    # Sort by proximity to CMU
                    properties = query.order_by(Property.distance_to_core).limit(limit).all()
            else:
                # Fallback to default recommendations
                properties = self.get_properties_for_map(
                    user, latitude, longitude, limit=limit
                )
                return properties
        else:
            # New user - provide default recommendations
            properties = self.get_properties_for_map(
                user, latitude, longitude, limit=limit
            )
            return properties
        
        # Format response
        result = []
        for prop in properties:
            prop_dict = {
                "id": prop.id,
                "title": prop.title,
                "price": prop.price,
                "latitude": prop.latitude,
                "longitude": prop.longitude,
                "image_url": prop.image_url,
                "address": prop.address,
                "city": prop.city,
                "distance_to_core": prop.distance_to_core,
                "distance": getattr(prop, "distance", None),
                "recommendation_reason": "Based on your browsing history"
            }
            
            result.append(prop_dict)
        
        return result