import requests
from typing import Dict
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Property

class RapidAPIFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "realty-mole-property-api.p.rapidapi.com"
        }
    
    def get_real_properties(self, db: Session, landlord_id: int, limit: int = 20) -> Dict:
        try:
            url = "https://realty-mole-property-api.p.rapidapi.com/rentalListings"
            params = {
                "city": "Pittsburgh",
                "state": "PA", 
                "limit": min(limit, 50)
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'API call failed with status {response.status_code}',
                    'saved_count': 0
                }
            
            data = response.json()
            listings = data.get('listings', [])
            
            saved_count = 0
            properties = []
            
            for listing in listings:
                try:
                    title = listing.get('formattedAddress', 'Property Listing')
                    price = float(listing.get('price', 0))
                    address = listing.get('formattedAddress', '')
                    
                    if price <= 0 or not address:
                        continue
                    
                    # 检查重复
                    existing = db.query(Property).filter(
                        Property.address == address,
                        Property.price == price,
                        Property.landlord_id == landlord_id
                    ).first()
                    
                    if existing:
                        continue
                    
                    # 创建新房源
                    new_property = Property(
                        title=title,
                        price=price,
                        description=f"Real property from RapidAPI: {address}",
                        property_type='apartment',
                        bedrooms=listing.get('bedrooms'),
                        bathrooms=listing.get('bathrooms'),
                        address=address,
                        city='Pittsburgh',
                        latitude=listing.get('latitude'),
                        longitude=listing.get('longitude'),
                        landlord_id=landlord_id,
                        is_active=True
                    )
                    
                    db.add(new_property)
                    db.commit()
                    db.refresh(new_property)
                    
                    saved_count += 1
                    properties.append({
                        'title': title,
                        'price': price,
                        'address': address
                    })
                    
                except Exception as e:
                    db.rollback()
                    continue
            
            return {
                'success': True,
                'total_fetched': len(listings),
                'saved_count': saved_count,
                'properties': properties,
                'api_calls_used': 1
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'saved_count': 0
            }
