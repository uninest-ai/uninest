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
        """获取真实房源并自动创建对应的房东（包含原始链接）"""
        try:
            # 纽约的坐标
            url = "https://realtor16.p.rapidapi.com/search/forrent/coordinates"
            params = {
                "latitude": "40.7128",    # 纽约坐标
                "longitude": "-74.0060",  # 纽约坐标
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
                    # 提取房源信息（包含原始链接）
                    processed_property = self._process_property_data_with_links(prop)
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
                        description=processed_property['description'],  # 包含原始链接
                        property_type=processed_property['property_type'],
                        bedrooms=processed_property['bedrooms'],
                        bathrooms=processed_property['bathrooms'],
                        area=processed_property['area'],
                        address=processed_property['address'],
                        city="New York",
                        latitude=processed_property.get('latitude'),
                        longitude=processed_property.get('longitude'),
                        landlord_id=landlord_profile.id,
                        is_active=True
                    )
                    
                    db.add(new_property)
                    db.commit()
                    db.refresh(new_property)
                    
                    saved_count += 1
                    properties_list.append({
                        'title': processed_property['title'],
                        'price': processed_property['price'],
                        'address': processed_property['address'],
                        'landlord_name': landlord_info.get('company_name', 'Property Manager'),
                        'original_link': processed_property.get('original_link', 'N/A')
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
                'message': f'Successfully created {created_landlords} landlords and {saved_count} properties with original links'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'saved_count': 0
            }
    
    def _process_property_data_with_links(self, prop: Dict) -> Dict:
        """处理API返回的房源数据，包含原始链接和详细信息"""
        try:
            # 提取基本信息
            description_data = prop.get('description', {})
            location = prop.get('location', {})
            address_data = location.get('address', {})
            
            # 提取原始链接和ID信息
            property_url = prop.get('permalink', '')  # Realtor.com链接
            property_id = prop.get('property_id', '')
            mls_id = prop.get('mls', {}).get('id', '') if prop.get('mls') else ''
            
            # 构建各种可能的链接
            links_info = self._build_property_links(property_url, property_id, mls_id, address_data)
            
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
            
            # 构建增强的描述（包含所有链接和信息）
            description = self._build_enhanced_description(
                description_data, links_info, address_data, prop
            )
            
            return {
                'title': title,
                'price': price,
                'description': description,
                'property_type': self._normalize_property_type(description_data.get('type', '')),
                'bedrooms': description_data.get('beds', 1),
                'bathrooms': self._parse_bathrooms(description_data.get('baths_consolidated', '1')),
                'area': description_data.get('sqft'),
                'address': full_address,
                'latitude': location.get('coordinate', {}).get('lat'),
                'longitude': location.get('coordinate', {}).get('lon'),
                'original_link': links_info.get('primary_link', 'N/A')
            }
            
        except Exception as e:
            print(f"Error processing property data: {str(e)}")
            return None
    
    def _build_property_links(self, property_url: str, property_id: str, mls_id: str, address_data: Dict) -> Dict:
        """构建房源的各种链接"""
        links = {
            'primary_link': property_url or 'N/A',
            'realtor_search_link': '',
            'zillow_search_link': '',
            'apartments_search_link': ''
        }
        
        # 构建搜索友好的地址
        if address_data.get('line') and address_data.get('city'):
            search_address = f"{address_data['line']}, {address_data['city']}, {address_data.get('state_code', 'PA')}"
            encoded_address = search_address.replace(' ', '+').replace(',', '%2C')
            
            # 构建各种房源网站的搜索链接
            links['realtor_search_link'] = f"https://www.realtor.com/realestateandhomes-search/{encoded_address}"
            links['zillow_search_link'] = f"https://www.zillow.com/homes/{encoded_address}_rb/"
            links['apartments_search_link'] = f"https://www.apartments.com/{address_data.get('city', 'pittsburgh')}-pa/"
        
        # 如果有MLS ID，构建更精确的链接
        if mls_id:
            links['mls_link'] = f"https://www.realtor.com/realestateandhomes-detail/{mls_id}"
        
        return links
    
    def _build_enhanced_description(self, description_data: Dict, links_info: Dict, 
                                  address_data: Dict, full_prop_data: Dict) -> str:
        """构建包含所有有用信息的增强描述"""
        
        description_parts = []
        
        # 基本描述
        description_parts.append("🏠 **Real Estate Listing from Realtor16 API**")
        
        # 位置信息
        if address_data.get('neighborhood'):
            description_parts.append(f"Neighborhood: {address_data['neighborhood']}")
        
        # 原始链接部分
        description_parts.append("\n🔗 **View Original Listing:**")
        
        if links_info.get('primary_link') and links_info['primary_link'] != 'N/A':
            description_parts.append(f"• Original: {links_info['primary_link']}")
        
        # 替代搜索链接
        description_parts.append("\n🔍 **Find Similar Properties:**")
        
        if links_info.get('realtor_search_link'):
            description_parts.append(f"• Realtor.com: {links_info['realtor_search_link']}")
        
        if links_info.get('zillow_search_link'):
            description_parts.append(f"• Zillow: {links_info['zillow_search_link']}")
        
        if links_info.get('apartments_search_link'):
            description_parts.append(f"• Apartments.com: {links_info['apartments_search_link']}")
        
        # MLS信息
        mls_data = full_prop_data.get('mls', {})
        if mls_data.get('id'):
            description_parts.append(f"\n📋 MLS ID: {mls_data['id']}")
        
        # 数据来源信息
        description_parts.append(f"\n📊 **Data Source:** Realtor16 API | Updated: {datetime.now().strftime('%Y-%m-%d')}")
        
        return "\n".join(description_parts)
    
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
                    landlord_info['unique_key'] = office['name'].lower().replace(' ', '_').replace('.', '')
                
                # 提取电话
                phones = advertiser.get('phones', [])
                if phones:
                    phone = phones[0]
                    if phone.get('number'):
                        landlord_info['contact_phone'] = phone['number']
                
                # 构建包含链接的房东描述
                office_website = office.get('website', '')
                landlord_description_parts = [
                    f"Real estate agency: {landlord_info['company_name']}"
                ]
                
                if office_website:
                    landlord_description_parts.append(f"Website: {office_website}")
                
                if landlord_info['contact_phone']:
                    landlord_description_parts.append(f"Phone: {landlord_info['contact_phone']}")
                
                landlord_info['description'] = " | ".join(landlord_description_parts)
            
            # 如果没有广告商信息，从地址生成房东
            else:
                location = prop.get('location', {})
                address = location.get('address', {})
                city = address.get('city', 'Pittsburgh')
                
                landlord_info['company_name'] = f"{city} Property Management"
                landlord_info['unique_key'] = f"{city.lower()}_property_management"
                landlord_info['description'] = f"Property management company in {city}, PA"
            
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
                    password_hash="auto_generated_landlord",
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
                description=landlord_info['description'],  # 包含网站和联系信息
                verification_status=True
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

