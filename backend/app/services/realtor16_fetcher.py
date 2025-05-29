import requests
from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Property, User, LandlordProfile

class Realtor16Fetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "realtor16.p.rapidapi.com"
        }
    
    def get_real_properties_with_landlords(self, db: Session, limit: int = 20) -> Dict:
        """
        获取真实房源并自动创建对应的房东
        
        Args:
            db: 数据库会话
            limit: 获取房源数量
            
        Returns:
            获取结果统计
        """
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
            created_landlords = 0
            properties_list = []
            
            # 处理前limit个房源
            for prop in properties_data[:limit]:
                try:
                    # 提取房源信息
                    processed_property = self._process_property_data(prop)
                    if not processed_property:
                        continue
                    
                    # 提取房东信息
                    landlord_info = self._extract_landlord_info(prop)
                    
                    # 获取或创建房东
                    landlord_profile = self._get_or_create_landlord(db, landlord_info)
                    if landlord_profile:
                        if landlord_info.get('newly_created'):
                            created_landlords += 1
                    else:
                        continue
                    
                    # 检查房源是否已存在
                    existing = db.query(Property).filter(
                        Property.address == processed_property['address'],
                        Property.landlord_id == landlord_profile.id
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
                        landlord_id=landlord_profile.id,
                        is_active=True,
                        labels=[]
                    )
                    
                    db.add(new_property)
                    db.commit()
                    db.refresh(new_property)
                    
                    saved_count += 1
                    properties_list.append({
                        'title': processed_property['title'],
                        'price': processed_property['price'],
                        'address': processed_property['address'],
                        'landlord_name': landlord_info.get('company_name', 'Property Manager')
                    })
                    
                except Exception as e:
                    print(f"Error processing property: {str(e)}")
                    db.rollback()
                    continue
            
            return {
                'success': True,
                'total_fetched': len(properties_data),
                'saved_count': saved_count,
                'created_landlords': created_landlords,
                'properties': properties_list,
                'api_calls_used': 1,
                'message': f'Successfully created {created_landlords} landlords and {saved_count} properties'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'saved_count': 0
            }
    
    def _extract_landlord_info(self, prop: Dict) -> Dict:
        """从房源数据中提取房东信息"""
        landlord_info = {
            'company_name': 'Unknown Property Management',
            'contact_phone': None,
            'description': 'Property management company',
            'unique_key': 'default_landlord'
        }
        
        try:
            # 从API数据中提取房东信息
            advertisers = prop.get('advertisers', [])
            if advertisers:
                advertiser = advertisers[0]  # 取第一个广告商
                
                # 提取公司名称
                office = advertiser.get('office', {})
                if office and office.get('name'):
                    landlord_info['company_name'] = office['name']
                    landlord_info['unique_key'] = office['name'].lower().replace(' ', '_')
                
                # 提取电话
                phones = advertiser.get('phones', [])
                if phones:
                    phone = phones[0]
                    if phone.get('number'):
                        landlord_info['contact_phone'] = phone['number']
                
                # 更新描述
                landlord_info['description'] = f"Real estate agency: {landlord_info['company_name']}"
            
            # 如果没有广告商信息，从地址生成房东
            else:
                location = prop.get('location', {})
                address = location.get('address', {})
                city = address.get('city', 'Pittsburgh')
                
                landlord_info['company_name'] = f"{city} Property Management"
                landlord_info['unique_key'] = f"{city.lower()}_property_management"
                landlord_info['description'] = f"Property management company in {city}"
            
        except Exception as e:
            print(f"Error extracting landlord info: {str(e)}")
        
        return landlord_info
    
    def _get_or_create_landlord(self, db: Session, landlord_info: Dict) -> LandlordProfile:
        """获取或创建房东"""
        try:
            # 尝试找到现有房东（基于公司名称）
            existing_landlord = db.query(LandlordProfile).filter(
                LandlordProfile.company_name == landlord_info['company_name']
            ).first()
            
            if existing_landlord:
                landlord_info['newly_created'] = False
                return existing_landlord
            
            # 创建新用户账户
            user_email = f"{landlord_info['unique_key']}@realtor16.auto"
            
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.email == user_email).first()
            if existing_user:
                # 如果用户存在但没有房东资料，创建房东资料
                existing_landlord_profile = db.query(LandlordProfile).filter(
                    LandlordProfile.user_id == existing_user.id
                ).first()
                
                if existing_landlord_profile:
                    landlord_info['newly_created'] = False
                    return existing_landlord_profile
            else:
                # 创建新用户
                new_user = User(
                    email=user_email,
                    username=landlord_info['company_name'],
                    password_hash="auto_generated_landlord",  # 自动生成的房东不需要真实密码
                    user_type="landlord"
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                existing_user = new_user
            
            # 创建房东资料
            new_landlord = LandlordProfile(
                user_id=existing_user.id,
                company_name=landlord_info['company_name'],
                contact_phone=landlord_info['contact_phone'],
                description=landlord_info['description'],
                verification_status=True  # 来自真实API的房东标记为已验证
            )
            
            db.add(new_landlord)
            db.commit()
            db.refresh(new_landlord)
            
            landlord_info['newly_created'] = True
            return new_landlord
            
        except Exception as e:
            print(f"Error creating landlord: {str(e)}")
            db.rollback()
            return None
    
    def _process_property_data(self, prop: Dict) -> Dict:
        """处理API返回的房源数据"""
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
            
            full_address = ', '.join(address_parts) if address_parts else 'Pittsburgh, PA'
            
            # 构建标题
            beds = description_data.get('beds', 1)
            baths = description_data.get('baths_consolidated', '1')
            prop_type = description_data.get('type', 'property').replace('_', ' ').title()
            
            title = f"{beds}BR/{baths}BA {prop_type}"
            if address_data.get('city'):
                title += f" - {address_data['city']}"
            
            # 获取价格
            list_price = prop.get('list_price', 1200)
            if isinstance(list_price, dict):
                price = list_price.get('min', 1200) or list_price.get('max', 1200)
            else:
                price = list_price or 1200
            
            # 构建详细描述
            description_parts = ["Real property listing with authentic landlord information."]
            if description_data.get('sqft'):
                description_parts.append(f"Size: {description_data['sqft']} sqft.")
            if description_data.get('year_built'):
                description_parts.append(f"Built in {description_data['year_built']}.")
            
            return {
                'title': title,
                'price': price,
                'description': ' '.join(description_parts),
                'property_type': self._normalize_property_type(description_data.get('type', '')),
                'bedrooms': description_data.get('beds', 1),
                'bathrooms': self._parse_bathrooms(description_data.get('baths_consolidated', '1')),
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
        """解析浴室数量"""
        if not baths_str:
            return 1.0
        try:
            return float(str(baths_str).replace('+', ''))
        except:
            return 1.0
