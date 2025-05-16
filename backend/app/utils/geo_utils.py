import math
from sqlalchemy.orm import Session
from app.models import Property

# Carnegie Mellon University coordinates
CMU_LATITUDE = 40.4433
CMU_LONGITUDE = -79.9436

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula
    Returns distance in miles
    """
    # Radius of the Earth in miles
    R = 3958.8
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def update_cmu_distances(db: Session):
    """
    Update distance_to_core for all properties in the database
    Call this function when new properties are added or after migrations
    """
    properties = db.query(Property).all()
    
    for prop in properties:
        if prop.latitude and prop.longitude:
            distance = calculate_distance(
                CMU_LATITUDE, CMU_LONGITUDE,
                prop.latitude, prop.longitude
            )
            prop.distance_to_core = distance
    
    db.commit()
    return f"Updated distances for {len(properties)} properties"

def get_nearby_properties(db: Session, latitude: float, longitude: float, radius: float = 5.0):
    """
    Get all properties within a given radius from the specified coordinates
    Returns a list of properties sorted by distance
    """
    properties = db.query(Property).all()
    nearby_properties = []
    
    for prop in properties:
        if prop.latitude and prop.longitude:
            distance = calculate_distance(
                latitude, longitude,
                prop.latitude, prop.longitude
            )
            
            if distance <= radius:
                # Add distance as a dynamic attribute
                setattr(prop, "distance", distance)
                nearby_properties.append(prop)
    
    # Sort by distance
    nearby_properties.sort(key=lambda x: getattr(x, "distance"))
    return nearby_properties