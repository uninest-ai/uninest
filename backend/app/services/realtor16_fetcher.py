import requests
from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Property

class Realtor16Fetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "realtor16.p.rapidapi.com"
        }
    
    def get_real_properties(self, db: Session, landlord_id: int, limit: int = 20) -> Dict:
        """使用Realtor16 API获取匹兹堡房源"""
        try:
            # 匹兹堡的坐标
            url = "https://realtor16.p.rapidapi.com/search/forrent/coordinates"
            params = {
                "latitude": "40.4406",    # 匹兹堡坐标
                "longitude": "-79.9959",  # 匹兹堡坐标
                "radius": "30"            # 30英里半径
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'API call failed with status {response.status_code}',
                    'saved_count': 0
                }
            
            data = response.json()
            properties_data = data.get('properties', [])
            
            if not properties_data:
                return {
                    'success': False,
                    'error': 'No properties found in response',
                    'saved_count': 0
                }
            
            saved_count = 0
            properties_list = []
            
            # 处理前limit个房源
            for prop in properties_data[:limit]:
                try:
                    # 提取房源信息
                    processed_property = self._process_property_data(prop)
                    
                    if not processed_property:
                        continue
                    
                    # 检查重复
                    existing = db.query(Property).filter(
                        Property.address == processed_property['address'],
                        Property.landlord_id == landlord_id
                    ).first()
                    
                    if existing:
                        continue
                    
                    # 创建新房源
                    new_property = Property(
                        title=processed_property['title'],
                        price=float(processed_property['price']),
                        description=processed_property['description'],
                        property_type=processed_property['property_type'],
                        bedrooms=processed_property['bedrooms'],
                        bathrooms=processed_property['bathrooms'],
                        area=processed_property['area'],
                        address=processed_property['address'],
                        city="Pittsburgh",
                        latitude=processed_property.get('latitude'),
                        longitude=processed_property.get('longitude'),
                        landlord_id=landlord_id,
                        is_active=True,
                        labels=[{
                            'source': 'realtor16_api',
                            'import_date': str(datetime.utcnow().date()),
                            'is_real_listing': True
                        }]
                    )
                    
                    db.add(new_property)
                    db.commit()
                    db.refresh(new_property)
                    
                    saved_count += 1
                    properties_list.append({
                        'title': processed_property['title'],
                        'price': processed_property['price'],
                        'address': processed_property['address']
                    })
                    
                except Exception as e:
                    print(f"Error processing property: {str(e)}")
                    db.rollback()
                    continue
            
            return {
                'success': True,
                'total_fetched': len(properties_data),
                'saved_count': saved_count,
                'properties': properties_list,
                'api_calls_used': 1,
                'message': f'Successfully fetched {saved_count} real properties from Realtor16'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'saved_count': 0
            }
    
    def _process_property_data(self, prop: Dict) -> Dict:
        """处理API返回的房源数据，转换为系统格式"""
        try:
            # 提取基本信息
            description_data = prop.get('description', {})
            location = prop.get('location', {})
            address_data = location.get('address', {})
            
            # 构建地址
            address_parts = []
            if address_data.get('line'):
                address_parts.append(address_data['line'])
            if address_data.get('city'):
                address_parts.append(address_data['city'])
            if address_data.get('state_code'):
                address_parts.append(address_data['state_code'])
            if address_data.get('postal_code'):
                address_parts.append(address_data['postal_code'])
            
            full_address = ', '.join(address_parts) if address_parts else 'Address not available'
            
            # 构建标题
            beds = description_data.get('beds', 0)
            baths = description_data.get('baths_consolidated', '0')
            prop_type = description_data.get('type', 'property').replace('_', ' ').title()
            
            title = f"{beds}BR/{baths}BA {prop_type}"
            if address_data.get('city'):
                title += f" - {address_data['city']}"
            
            # 获取租金价格
            list_price = prop.get('list_price', 0)
            if isinstance(list_price, dict):
                price = list_price.get('min', 0) or list_price.get('max', 0)
            else:
                price = list_price or 0
            
            # 构建描述
            description_parts = [f"Real estate listing from Realtor16 API."]
            
            if description_data.get('sqft'):
                description_parts.append(f"Size: {description_data['sqft']} sqft.")
            if description_data.get('year_built'):
                description_parts.append(f"Built in {description_data['year_built']}.")
            if description_data.get('garage'):
                description_parts.append(f"Garage spaces: {description_data['garage']}.")
            
            description = ' '.join(description_parts)
            
            return {
                'title': title,
                'price': price,
                'description': description,
                'property_type': self._normalize_property_type(description_data.get('type', '')),
                'bedrooms': description_data.get('beds'),
                'bathrooms': self._parse_bathrooms(description_data.get('baths_consolidated')),
                'area': description_data.get('sqft'),
                'address': full_address,
                'latitude': location.get('coordinate', {}).get('lat'),
                'longitude': location.get('coordinate', {}).get('lon')
            }
            
        except Exception as e:
            print(f"Error processing property data: {str(e)}")
            return None
    
    def _normalize_property_type(self, api_type: str) -> str:
        """标准化房产类型"""
        type_mapping = {
            'single_family': 'house',
            'condo': 'condo',
            'townhouse': 'townhouse',
            'apartment': 'apartment',
            'multi_family': 'apartment'
        }
        return type_mapping.get(api_type.lower(), 'apartment')
    
    def _parse_bathrooms(self, baths_str) -> float:
        """解析浴室数量字符串"""
        if not baths_str:
            return 1.0
        try:
            return float(baths_str)
        except:
            return 1.0