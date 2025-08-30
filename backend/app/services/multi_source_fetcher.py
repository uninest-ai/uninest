import requests
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import time
from app.models import Property, User, LandlordProfile

class MultiSourceFetcher:
    """
    Multi-source real estate API fetcher that combines data from multiple APIs
    for comprehensive housing data in Pittsburgh area
    """
    
    def __init__(self, rapidapi_key: str):
        self.rapidapi_key = rapidapi_key
        self.api_sources = {
            'realtor16': {
                'host': 'realtor16.p.rapidapi.com',
                'priority': 1,
                'rate_limit': 100  # requests per minute
            },
            'realty_mole': {
                'host': 'realty-mole-property-api.p.rapidapi.com',
                'priority': 2,
                'rate_limit': 60
            },
            'rentals_com': {
                'host': 'rentals-com1.p.rapidapi.com',
                'priority': 3,
                'rate_limit': 50
            }
        }
        self.last_api_call = {}
        
    def get_comprehensive_property_data(self, db: Session, limit: int = 50) -> Dict:
        """
        Fetch comprehensive property data from multiple sources
        """
        results = {
            'success': True,
            'total_fetched': 0,
            'saved_count': 0,
            'created_landlords': 0,
            'api_sources_used': [],
            'properties': [],
            'errors': []
        }
        
        # Fetch from primary source (Realtor16)
        try:
            realtor_result = self._fetch_from_realtor16(db, limit // 2)
            if realtor_result['success']:
                results['total_fetched'] += realtor_result.get('total_fetched', 0)
                results['saved_count'] += realtor_result.get('saved_count', 0)
                results['created_landlords'] += realtor_result.get('created_landlords', 0)
                results['properties'].extend(realtor_result.get('properties', []))
                results['api_sources_used'].append('realtor16')
        except Exception as e:
            results['errors'].append(f"Realtor16 API error: {str(e)}")
            
        # Fetch from secondary source (Realty Mole)
        try:
            time.sleep(1)  # Rate limiting
            mole_result = self._fetch_from_realty_mole(db, limit // 4)
            if mole_result['success']:
                results['total_fetched'] += mole_result.get('total_fetched', 0)
                results['saved_count'] += mole_result.get('saved_count', 0)
                results['properties'].extend(mole_result.get('properties', []))
                results['api_sources_used'].append('realty_mole')
        except Exception as e:
            results['errors'].append(f"Realty Mole API error: {str(e)}")
            
        # Fetch from tertiary source (Custom Pittsburgh data)
        try:
            time.sleep(1)  # Rate limiting
            custom_result = self._fetch_custom_pittsburgh_data(db, limit // 4)
            if custom_result['success']:
                results['total_fetched'] += custom_result.get('total_fetched', 0)
                results['saved_count'] += custom_result.get('saved_count', 0)
                results['properties'].extend(custom_result.get('properties', []))
                results['api_sources_used'].append('custom_pittsburgh')
        except Exception as e:
            results['errors'].append(f"Custom Pittsburgh data error: {str(e)}")
            
        return results
    
    def _fetch_from_realtor16(self, db: Session, limit: int) -> Dict:
        """Fetch data from Realtor16 API"""
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "realtor16.p.rapidapi.com"
        }
        
        url = "https://realtor16.p.rapidapi.com/search/forrent/coordinates"
        params = {
            "latitude": "40.4406",    # Pittsburgh coordinates
            "longitude": "-79.9959",
            "radius": "25",           # 25 mile radius
            "limit": str(limit)
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'API call failed: {response.status_code}'}
            
        data = response.json()
        properties_data = data.get('properties', [])
        
        return self._process_realtor16_properties(db, properties_data)
    
    def _fetch_from_realty_mole(self, db: Session, limit: int) -> Dict:
        """Fetch data from Realty Mole API"""
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "realty-mole-property-api.p.rapidapi.com"
        }
        
        url = "https://realty-mole-property-api.p.rapidapi.com/rentalListings"
        params = {
            "city": "Pittsburgh",
            "state": "PA",
            "limit": str(min(limit, 50))
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'API call failed: {response.status_code}'}
            
        data = response.json()
        listings = data.get('listings', [])
        
        return self._process_realty_mole_properties(db, listings)
    
    def _fetch_custom_pittsburgh_data(self, db: Session, limit: int) -> Dict:
        """Generate custom Pittsburgh housing data for areas near CMU"""
        pittsburgh_neighborhoods = [
            {"name": "Oakland", "lat": 40.4418, "lng": -79.9561, "avg_rent": 1400},
            {"name": "Shadyside", "lat": 40.4520, "lng": -79.9343, "avg_rent": 1600},
            {"name": "Squirrel Hill", "lat": 40.4384, "lng": -79.9221, "avg_rent": 1350},
            {"name": "Greenfield", "lat": 40.4268, "lng": -79.9390, "avg_rent": 1200},
            {"name": "Point Breeze", "lat": 40.4446, "lng": -79.9081, "avg_rent": 1300},
            {"name": "Regent Square", "lat": 40.4290, "lng": -79.8956, "avg_rent": 1450},
            {"name": "Bloomfield", "lat": 40.4633, "lng": -79.9496, "avg_rent": 1250},
            {"name": "Friendship", "lat": 40.4583, "lng": -79.9398, "avg_rent": 1550}
        ]
        
        properties_list = []
        saved_count = 0
        
        for neighborhood in pittsburgh_neighborhoods[:limit]:
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
                        is_active=True
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
                continue
        
        return {
            'success': True,
            'total_fetched': len(pittsburgh_neighborhoods) * 2,
            'saved_count': saved_count,
            'properties': properties_list
        }
    
    def _process_realtor16_properties(self, db: Session, properties_data: List[Dict]) -> Dict:
        """Process Realtor16 property data"""
        saved_count = 0
        created_landlords = 0
        properties_list = []
        
        for prop in properties_data:
            try:
                # Extract property information
                description_data = prop.get('description', {})
                location = prop.get('location', {})
                address_data = location.get('address', {})
                
                # Build address
                address_parts = []
                if address_data.get('line'):
                    address_parts.append(address_data['line'])
                if address_data.get('city'):
                    address_parts.append(address_data['city'])
                if address_data.get('state_code'):
                    address_parts.append(address_data['state_code'])
                
                full_address = ', '.join(address_parts) if address_parts else 'Pittsburgh, PA'
                
                # Extract other details
                beds = description_data.get('beds', 1)
                baths = description_data.get('baths_consolidated', '1')
                prop_type = description_data.get('type', 'apartment')
                
                title = f"{beds}BR/{baths}BA {prop_type.replace('_', ' ').title()}"
                
                # Get price
                list_price = prop.get('list_price', 1200)
                if isinstance(list_price, dict):
                    price = list_price.get('min', 1200) or 1200
                else:
                    price = list_price or 1200
                
                # Get or create landlord
                landlord_info = self._extract_landlord_from_realtor16(prop)
                landlord = self._get_or_create_api_landlord(db, landlord_info)
                if landlord and landlord_info.get('newly_created'):
                    created_landlords += 1
                
                if not landlord:
                    continue
                
                # Check for duplicates
                existing = db.query(Property).filter(
                    Property.address == full_address,
                    Property.landlord_id == landlord.id
                ).first()
                
                if existing:
                    continue
                
                # Extract images from API data
                api_images = []
                photos = prop.get('photos', [])
                if photos:
                    api_images = [photo.get('href') for photo in photos if photo.get('href')]
                
                # Extract original listing URL
                listing_url = prop.get('permalink') or prop.get('href')
                if not listing_url and prop.get('property_id'):
                    listing_url = f"https://www.realtor.com/realestateandhomes-detail/{prop.get('property_id')}"
                
                # Create extended description with API data
                extended_desc = f"Real estate listing from Realtor16 API\n{full_address}\nProperty ID: {prop.get('property_id', 'N/A')}"
                
                # Format property description from dict
                desc_dict = prop.get('description', {})
                if isinstance(desc_dict, dict):
                    formatted_desc = []
                    for key, value in desc_dict.items():
                        if value is not None and value != '':
                            formatted_desc.append(f"{key.replace('_', ' ').title()}: {value}")
                    if formatted_desc:
                        extended_desc += f"\n\nProperty Details:\n" + "\n".join(formatted_desc)
                
                # Extract amenities and features
                amenities = []
                if description_data.get('garage'):
                    amenities.append(f"Garage: {description_data['garage']}")
                if description_data.get('lot_sqft'):
                    amenities.append(f"Lot Size: {description_data['lot_sqft']} sq ft")
                if prop.get('virtual_tours'):
                    amenities.append("Virtual Tour Available")
                
                # Create property
                new_property = Property(
                    title=title,
                    price=float(price),
                    description=f"Beautiful {prop_type.replace('_', ' ').title()} in Pittsburgh\n\nLocation: {full_address}\nProperty ID: {prop.get('property_id', 'N/A')}\n\nThis property is sourced from Realtor16 API and offers great value in the Pittsburgh area.",
                    property_type=self._normalize_property_type(prop_type),
                    bedrooms=beds,
                    bathrooms=self._parse_bathrooms(baths),
                    area=description_data.get('sqft'),
                    address=full_address,
                    city="Pittsburgh",
                    latitude=location.get('coordinate', {}).get('lat'),
                    longitude=location.get('coordinate', {}).get('lon'),
                    landlord_id=landlord.id,
                    is_active=True,
                    # New 3rd party API fields
                    original_listing_url=listing_url,
                    api_source='realtor16',
                    api_property_id=str(prop.get('property_id', '')),
                    api_images=api_images,
                    extended_description=extended_desc,
                    api_amenities=amenities,
                    api_metadata={
                        'mls_id': prop.get('mls', {}).get('id'),
                        'status': prop.get('status'),
                        'listing_date': prop.get('list_date'),
                        'price_per_sqft': prop.get('price_per_sqft'),
                        'lot_size': description_data.get('lot_sqft'),
                        'year_built': description_data.get('year_built'),
                        'garage': description_data.get('garage'),
                        'stories': description_data.get('stories')
                    }
                )
                
                db.add(new_property)
                db.commit()
                db.refresh(new_property)
                
                saved_count += 1
                properties_list.append({
                    'title': title,
                    'price': price,
                    'address': full_address,
                    'source': 'realtor16'
                })
                
            except Exception as e:
                db.rollback()
                continue
        
        return {
            'success': True,
            'total_fetched': len(properties_data),
            'saved_count': saved_count,
            'created_landlords': created_landlords,
            'properties': properties_list
        }
    
    def _process_realty_mole_properties(self, db: Session, listings: List[Dict]) -> Dict:
        """Process Realty Mole property data"""
        saved_count = 0
        properties_list = []
        
        # Get a default landlord for Realty Mole properties
        default_landlord = self._get_or_create_api_landlord(db, {
            'company_name': 'Realty Mole Properties',
            'unique_key': 'realty_mole_default',
            'description': 'Properties sourced from Realty Mole API'
        })
        
        if not default_landlord:
            return {'success': False, 'error': 'Could not create default landlord'}
        
        for listing in listings:
            try:
                title = listing.get('formattedAddress', 'Property Listing')
                price = float(listing.get('price', 0))
                address = listing.get('formattedAddress', '')
                
                if price <= 0 or not address:
                    continue
                
                # Check for duplicates
                existing = db.query(Property).filter(
                    Property.address == address,
                    Property.landlord_id == default_landlord.id
                ).first()
                
                if existing:
                    continue
                
                # Extract images if available
                api_images = []
                if listing.get('propertyPhotos'):
                    api_images = [photo for photo in listing['propertyPhotos'] if photo]
                
                # Create extended description
                extended_desc = f"Property from Realty Mole API\nAddress: {address}\nData source: Realty Mole Property API"
                if listing.get('description'):
                    extended_desc += f"\n\nDescription: {listing['description']}"
                
                # Extract amenities
                amenities = []
                if listing.get('propertyType'):
                    amenities.append(f"Type: {listing['propertyType']}")
                if listing.get('rentEstimate'):
                    amenities.append(f"Estimated Rent: ${listing['rentEstimate']}")
                if listing.get('squareFootage'):
                    amenities.append(f"Square Footage: {listing['squareFootage']} sq ft")
                
                # Create property
                new_property = Property(
                    title=title,
                    price=price,
                    description=f"Quality rental property in Pittsburgh\n\nAddress: {address}\nData sourced from Realty Mole Property API\n\nThis property offers great amenities and is well-located in the Pittsburgh area.",
                    property_type='apartment',
                    bedrooms=listing.get('bedrooms', 1),
                    bathrooms=listing.get('bathrooms', 1),
                    address=address,
                    city='Pittsburgh',
                    latitude=listing.get('latitude'),
                    longitude=listing.get('longitude'),
                    landlord_id=default_landlord.id,
                    is_active=True,
                    # New 3rd party API fields
                    original_listing_url=listing.get('url'),
                    api_source='realty_mole',
                    api_property_id=str(listing.get('id', '')),
                    api_images=api_images,
                    extended_description=extended_desc,
                    api_amenities=amenities,
                    api_metadata={
                        'property_type': listing.get('propertyType'),
                        'rent_estimate': listing.get('rentEstimate'),
                        'square_footage': listing.get('squareFootage'),
                        'year_built': listing.get('yearBuilt'),
                        'lot_size': listing.get('lotSize')
                    }
                )
                
                db.add(new_property)
                db.commit()
                db.refresh(new_property)
                
                saved_count += 1
                properties_list.append({
                    'title': title,
                    'price': price,
                    'address': address,
                    'source': 'realty_mole'
                })
                
            except Exception as e:
                db.rollback()
                continue
        
        return {
            'success': True,
            'total_fetched': len(listings),
            'saved_count': saved_count,
            'properties': properties_list
        }
    
    def _generate_neighborhood_property(self, neighborhood: Dict, index: int) -> Dict:
        """Generate realistic property data for Pittsburgh neighborhoods"""
        import random
        
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
            'description': f"Beautiful {property_type} in {neighborhood['name']} neighborhood\n\nClose to CMU and University of Pittsburgh\nWalking distance to public transportation\nNear restaurants and shopping\n\nThis {property_type} offers modern amenities and great location for students and professionals.",
            'property_type': property_type,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'area': random.randint(600, 1500),
            'address': address,
            'latitude': neighborhood['lat'] + lat_variation,
            'longitude': neighborhood['lng'] + lng_variation
        }
    
    def _get_or_create_area_landlord(self, db: Session, area_name: str) -> Optional[LandlordProfile]:
        """Get or create landlord for specific Pittsburgh area"""
        company_name = f"{area_name} Property Management"
        
        # Try to find existing landlord
        existing = db.query(LandlordProfile).filter(
            LandlordProfile.company_name == company_name
        ).first()
        
        if existing:
            return existing
        
        # Create new landlord
        try:
            user_email = f"{area_name.lower().replace(' ', '_')}_properties@pittsburgh.local"
            
            # Create user if doesn't exist
            existing_user = db.query(User).filter(User.email == user_email).first()
            if not existing_user:
                new_user = User(
                    email=user_email,
                    username=company_name,
                    password_hash="auto_generated_landlord",
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
                description=f"Professional property management in {area_name}, Pittsburgh. Specializing in student and professional housing near universities.",
                verification_status=True
            )
            
            db.add(new_landlord)
            db.commit()
            db.refresh(new_landlord)
            
            return new_landlord
            
        except Exception as e:
            db.rollback()
            return None
    
    def _extract_landlord_from_realtor16(self, prop: Dict) -> Dict:
        """Extract landlord information from Realtor16 data"""
        landlord_info = {
            'company_name': 'Pittsburgh Property Management',
            'unique_key': 'pittsburgh_default',
            'description': 'Property management company'
        }
        
        # Extract from advertisers
        advertisers = prop.get('advertisers', [])
        if advertisers:
            advertiser = advertisers[0]
            office = advertiser.get('office', {})
            agent = advertiser.get('agent', {})
            
            if office and office.get('name'):
                landlord_info['company_name'] = office['name']
                landlord_info['unique_key'] = office['name'].lower().replace(' ', '_').replace('.', '')
                
                # Enhanced landlord information from API
                landlord_info.update({
                    'contact_phone': office.get('phone'),
                    'website_url': office.get('website'),
                    'office_address': self._format_office_address(office.get('address', {})),
                    'profile_image_url': office.get('photo', {}).get('href'),
                    'api_source': 'realtor16',
                    'api_metadata': {
                        'office_id': office.get('id'),
                        'agent_name': f"{agent.get('first_name', '')} {agent.get('last_name', '')}".strip(),
                        'agent_phone': agent.get('phone'),
                        'agent_email': agent.get('email'),
                        'mls_id': office.get('mls_id')
                    }
                })
            elif agent:
                # If no office, use agent information
                agent_name = f"{agent.get('first_name', '')} {agent.get('last_name', '')}".strip()
                if agent_name:
                    landlord_info['company_name'] = f"{agent_name} - Real Estate Agent"
                    landlord_info['unique_key'] = agent_name.lower().replace(' ', '_')
                    landlord_info['contact_phone'] = agent.get('phone')
                    landlord_info['email'] = agent.get('email')
        
        return landlord_info
    
    def _format_office_address(self, address_data: Dict) -> str:
        """Format office address from API data"""
        if not address_data:
            return None
        
        parts = []
        if address_data.get('line'):
            parts.append(address_data['line'])
        if address_data.get('city'):
            parts.append(address_data['city'])
        if address_data.get('state_code'):
            parts.append(address_data['state_code'])
        if address_data.get('postal_code'):
            parts.append(address_data['postal_code'])
        
        return ', '.join(parts) if parts else None
    
    def _get_or_create_api_landlord(self, db: Session, landlord_info: Dict) -> Optional[LandlordProfile]:
        """Get or create landlord from API data"""
        try:
            # Check if landlord exists
            existing = db.query(LandlordProfile).filter(
                LandlordProfile.company_name == landlord_info['company_name']
            ).first()
            
            if existing:
                landlord_info['newly_created'] = False
                return existing
            
            # Create new user and landlord
            user_email = f"{landlord_info['unique_key']}@api.generated"
            
            existing_user = db.query(User).filter(User.email == user_email).first()
            if not existing_user:
                new_user = User(
                    email=user_email,
                    username=landlord_info['company_name'],
                    password_hash="auto_generated_api_landlord",
                    user_type="landlord"
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                existing_user = new_user
            
            new_landlord = LandlordProfile(
                user_id=existing_user.id,
                company_name=landlord_info['company_name'],
                description=landlord_info.get('description', 'API-generated property management'),
                verification_status=True,
                # Enhanced fields from API
                contact_phone=landlord_info.get('contact_phone'),
                website_url=landlord_info.get('website_url'),
                email=landlord_info.get('email'),
                office_address=landlord_info.get('office_address'),
                profile_image_url=landlord_info.get('profile_image_url'),
                api_source=landlord_info.get('api_source'),
                api_metadata=landlord_info.get('api_metadata')
            )
            
            db.add(new_landlord)
            db.commit()
            db.refresh(new_landlord)
            
            landlord_info['newly_created'] = True
            return new_landlord
            
        except Exception as e:
            db.rollback()
            return None
    
    def _normalize_property_type(self, api_type: str) -> str:
        """Normalize property types"""
        type_mapping = {
            'single_family': 'house',
            'condo': 'condo', 
            'townhouse': 'townhouse',
            'apartment': 'apartment',
            'multi_family': 'apartment'
        }
        return type_mapping.get(api_type.lower(), 'apartment')
    
    def _parse_bathrooms(self, baths_str) -> float:
        """Parse bathroom count"""
        if not baths_str:
            return 1.0
        try:
            return float(str(baths_str).replace('+', ''))
        except:
            return 1.0

import random  # Add this import at the top of the file