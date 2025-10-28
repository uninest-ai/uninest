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
        self.nyc_neighborhoods = [
            {"name": "Manhattan", "lat": 40.7831, "lng": -73.9712, "avg_rent": 3500},
            {"name": "Brooklyn", "lat": 40.6782, "lng": -73.9442, "avg_rent": 2800},
            {"name": "Queens", "lat": 40.7282, "lng": -73.7949, "avg_rent": 2400},
            {"name": "Bronx", "lat": 40.8448, "lng": -73.8648, "avg_rent": 2000},
            {"name": "Upper East Side", "lat": 40.7736, "lng": -73.9566, "avg_rent": 4200},
            {"name": "Upper West Side", "lat": 40.7870, "lng": -73.9754, "avg_rent": 3900},
            {"name": "East Village", "lat": 40.7265, "lng": -73.9815, "avg_rent": 3200},
            {"name": "Williamsburg", "lat": 40.7081, "lng": -73.9571, "avg_rent": 3000}
        ]

    def generate_synthetic_landlords(self, db: Session, count: int = 5) -> Dict:
        """
        Generate synthetic landlord profiles and users for testing

        WARNING: This generates FAKE landlords/users for testing purposes only.

        Args:
            db: Database session
            count: Number of synthetic landlords to create (max 8 neighborhoods)

        Returns:
            Dictionary with created landlords info
        """
        created_landlords = []
        created_users = []
        errors = []

        neighborhoods_to_use = self.nyc_neighborhoods[:min(count, len(self.nyc_neighborhoods))]

        for neighborhood in neighborhoods_to_use:
            try:
                landlord = self._get_or_create_area_landlord(db, neighborhood['name'])
                if landlord:
                    created_landlords.append({
                        'id': landlord.id,
                        'company_name': landlord.company_name,
                        'area': neighborhood['name']
                    })
            except Exception as e:
                errors.append(f"Error creating landlord for {neighborhood['name']}: {str(e)}")
                logger.error(f"Error creating synthetic landlord: {e}")
                continue

        return {
            'success': True,
            'landlords_created': len(created_landlords),
            'landlords': created_landlords,
            'errors': errors
        }

    def generate_synthetic_properties_only(
        self,
        db: Session,
        properties_per_landlord: int = 2,
        landlord_limit: int = None
    ) -> Dict:
        """
        Generate synthetic properties for existing landlords

        WARNING: This generates FAKE properties for testing purposes only.
        Use existing landlords (synthetic or real) to attach properties to.

        Args:
            db: Database session
            properties_per_landlord: Number of properties per landlord
            landlord_limit: Max number of landlords to use (None = all)

        Returns:
            Dictionary with created properties info
        """
        properties_list = []
        saved_count = 0
        errors = []

        # Get existing landlords (prefer synthetic ones)
        landlords = db.query(LandlordProfile).filter(
            LandlordProfile.api_source == 'synthetic_test_data'
        ).limit(landlord_limit).all() if landlord_limit else db.query(LandlordProfile).filter(
            LandlordProfile.api_source == 'synthetic_test_data'
        ).all()

        if not landlords:
            return {
                'success': False,
                'error': 'No synthetic landlords found. Run generate_synthetic_landlords first.',
                'saved_count': 0,
                'properties': []
            }

        for landlord in landlords:
            # Find neighborhood from company name
            neighborhood_name = landlord.company_name.replace(' Property Management [TEST DATA]', '')
            neighborhood = next(
                (n for n in self.nyc_neighborhoods if n['name'] == neighborhood_name),
                self.nyc_neighborhoods[0]  # fallback
            )

            for i in range(properties_per_landlord):
                try:
                    property_data = self._generate_neighborhood_property(neighborhood, i)

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
                        city="New York",
                        latitude=property_data['latitude'],
                        longitude=property_data['longitude'],
                        landlord_id=landlord.id,
                        is_active=True,
                        api_source='synthetic_test_data',
                        extended_description='WARNING: This is synthetic test data, not a real property listing.'
                    )

                    db.add(new_property)
                    db.commit()
                    db.refresh(new_property)

                    saved_count += 1
                    properties_list.append({
                        'id': new_property.id,
                        'title': property_data['title'],
                        'price': property_data['price'],
                        'address': property_data['address'],
                        'landlord': landlord.company_name
                    })

                except Exception as e:
                    db.rollback()
                    errors.append(f"Error creating property: {str(e)}")
                    logger.error(f"Error generating synthetic property: {e}")
                    continue

        return {
            'success': True,
            'saved_count': saved_count,
            'properties': properties_list,
            'errors': errors
        }

    def generate_synthetic_properties(self, db: Session, limit: int = 10) -> Dict:
        """
        Generate synthetic NYC housing data for testing

        WARNING: This generates FAKE data for testing purposes only.
        Do not use for production property listings.
        """
        properties_list = []
        saved_count = 0

        for neighborhood in self.nyc_neighborhoods[:limit]:
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
                        city="New York",
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
            'total_fetched': len(self.nyc_neighborhoods) * 2,
            'saved_count': saved_count,
            'properties': properties_list
        }

    def _generate_neighborhood_property(self, neighborhood: Dict, index: int) -> Dict:
        """Generate realistic property data for NYC neighborhoods"""
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
            'description': f"[SYNTHETIC TEST DATA] Beautiful {property_type} in {neighborhood['name']} neighborhood\n\nClose to NYC universities and attractions\nWalking distance to subway stations\nNear restaurants and shopping\n\nThis {property_type} offers modern amenities and great location for students and professionals.",
            'property_type': property_type,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'area': random.randint(600, 1500),
            'address': address,
            'latitude': neighborhood['lat'] + lat_variation,
            'longitude': neighborhood['lng'] + lng_variation
        }

    def _get_or_create_area_landlord(self, db: Session, area_name: str) -> Optional[LandlordProfile]:
        """Get or create landlord for specific NYC area (synthetic data)"""
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
                description=f"[SYNTHETIC TEST DATA] Property management in {area_name}, New York.",
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