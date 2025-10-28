"""
Synthetic Data Generator for Testing and Development

This module generates synthetic property data for testing purposes.
DO NOT use this in production for actual property listings.
Use multi_source_fetcher.py for real property data from external APIs.
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import Property, User, LandlordProfile
import random
import logging

logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """
    Generates synthetic property data for testing and development.

    WARNING: This is for testing purposes only. Real property data
    should come from external APIs via MultiSourceFetcher.
    """

    def __init__(self):
        self.pittsburgh_neighborhoods = [
            {"name": "Oakland", "lat": 40.4418, "lng": -79.9561, "avg_rent": 1400},
            {"name": "Shadyside", "lat": 40.4520, "lng": -79.9343, "avg_rent": 1600},
            {"name": "Squirrel Hill", "lat": 40.4384, "lng": -79.9221, "avg_rent": 1350},
            {"name": "Greenfield", "lat": 40.4268, "lng": -79.9390, "avg_rent": 1200},
            {"name": "Point Breeze", "lat": 40.4446, "lng": -79.9081, "avg_rent": 1300},
            {"name": "Regent Square", "lat": 40.4290, "lng": -79.8956, "avg_rent": 1450},
            {"name": "Bloomfield", "lat": 40.4633, "lng": -79.9496, "avg_rent": 1250},
            {"name": "Friendship", "lat": 40.4583, "lng": -79.9398, "avg_rent": 1550}
        ]

    def generate_synthetic_properties(self, db: Session, limit: int = 10) -> Dict:
        """
        Generate synthetic Pittsburgh housing data for testing

        WARNING: This generates FAKE data for testing purposes only.
        Do not use for production property listings.
        """
        properties_list = []
        saved_count = 0

        for neighborhood in self.pittsburgh_neighborhoods[:limit]:
            try:
                # Create diverse property types
                for i in range(2):  # 2 properties per neighborhood
                    property_data = self._generate_neighborhood_property(neighborhood, i)

                    # Get or create landlord for this area
                    landlord = self._get_or_create_area_landlord(db, neighborhood['name'])
                    if not landlord:
                        continue

                    # Check for duplicates
                    existing = db.query(Property).filter(
                        Property.address == property_data['address'],
                        Property.landlord_id == landlord.id
                    ).first()

                    if existing:
                        continue

                    # Create property
                    new_property = Property(
                        title=property_data['title'],
                        price=property_data['price'],
                        description=property_data['description'],
                        property_type=property_data['property_type'],
                        bedrooms=property_data['bedrooms'],
                        bathrooms=property_data['bathrooms'],
                        area=property_data['area'],
                        address=property_data['address'],
                        city="Pittsburgh",
                        latitude=property_data['latitude'],
                        longitude=property_data['longitude'],
                        landlord_id=landlord.id,
                        is_active=True,
                        # Mark as synthetic data
                        api_source='synthetic_test_data',
                        extended_description='WARNING: This is synthetic test data, not a real property listing.'
                    )

                    db.add(new_property)
                    db.commit()
                    db.refresh(new_property)

                    saved_count += 1
                    properties_list.append({
                        'title': property_data['title'],
                        'price': property_data['price'],
                        'address': property_data['address'],
                        'neighborhood': neighborhood['name']
                    })

            except Exception as e:
                db.rollback()
                logger.error(f"Error generating synthetic property: {e}")
                continue

        return {
            'success': True,
            'total_fetched': len(self.pittsburgh_neighborhoods) * 2,
            'saved_count': saved_count,
            'properties': properties_list
        }

    def _generate_neighborhood_property(self, neighborhood: Dict, index: int) -> Dict:
        """Generate realistic property data for Pittsburgh neighborhoods"""
        property_types = ['apartment', 'house', 'condo', 'townhouse']
        property_type = random.choice(property_types)

        bedrooms = random.choice([1, 2, 3, 4])
        bathrooms = random.choice([1, 1.5, 2, 2.5, 3])

        # Price variation based on neighborhood and property type
        base_rent = neighborhood['avg_rent']
        type_multipliers = {'apartment': 0.9, 'house': 1.3, 'condo': 1.1, 'townhouse': 1.2}
        room_multiplier = 0.6 + (bedrooms * 0.2)

        price = int(base_rent * type_multipliers[property_type] * room_multiplier)

        # Generate realistic address
        street_numbers = [100 + index * 50 + random.randint(1, 49) for _ in range(1)]
        streets = ['Oak St', 'Pine Ave', 'Maple Dr', 'Cedar Way', 'Elm St', 'Walnut Ave', 'Cherry St']
        street = random.choice(streets)
        address = f"{street_numbers[0]} {street}, {neighborhood['name']}, PA 15213"

        # Add some realistic variation to coordinates
        lat_variation = random.uniform(-0.01, 0.01)
        lng_variation = random.uniform(-0.01, 0.01)

        return {
            'title': f"{bedrooms}BR/{bathrooms}BA {property_type.title()} in {neighborhood['name']}",
            'price': price,
            'description': f"[SYNTHETIC TEST DATA] Beautiful {property_type} in {neighborhood['name']} neighborhood\n\nClose to CMU and University of Pittsburgh\nWalking distance to public transportation\nNear restaurants and shopping\n\nThis {property_type} offers modern amenities and great location for students and professionals.",
            'property_type': property_type,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'area': random.randint(600, 1500),
            'address': address,
            'latitude': neighborhood['lat'] + lat_variation,
            'longitude': neighborhood['lng'] + lng_variation
        }

    def _get_or_create_area_landlord(self, db: Session, area_name: str) -> Optional[LandlordProfile]:
        """Get or create landlord for specific Pittsburgh area (synthetic data)"""
        company_name = f"{area_name} Property Management [TEST DATA]"

        # Try to find existing landlord
        existing = db.query(LandlordProfile).filter(
            LandlordProfile.company_name == company_name
        ).first()

        if existing:
            return existing

        # Create new landlord
        try:
            user_email = f"{area_name.lower().replace(' ', '_')}_synthetic@test.local"

            # Create user if doesn't exist
            existing_user = db.query(User).filter(User.email == user_email).first()
            if not existing_user:
                new_user = User(
                    email=user_email,
                    username=company_name,
                    password_hash="synthetic_test_landlord",
                    user_type="landlord"
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                existing_user = new_user

            # Create landlord profile
            new_landlord = LandlordProfile(
                user_id=existing_user.id,
                company_name=company_name,
                contact_phone=f"412-555-{random.randint(1000, 9999)}",
                description=f"[SYNTHETIC TEST DATA] Property management in {area_name}, Pittsburgh.",
                verification_status=False,  # Mark as unverified since it's fake
                api_source='synthetic_test_data'
            )

            db.add(new_landlord)
            db.commit()
            db.refresh(new_landlord)

            return new_landlord

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating synthetic landlord: {e}")
            return None


def get_synthetic_generator() -> SyntheticDataGenerator:
    """Get singleton instance of synthetic data generator"""
    return SyntheticDataGenerator()