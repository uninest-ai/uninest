# app/schemas.py
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    user_type: str = "tenant"  # Default to tenant, can be "landlord" or "tenant"

# Add User schema for backward compatibility with tests
class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str
    confirm_password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v
    
    @validator('user_type')
    def validate_user_type(cls, v):
        if v not in ["tenant", "landlord"]:
            raise ValueError('user_type must be either "tenant" or "landlord"')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    user_type: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True  # This was previously orm_mode = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class PropertyBase(BaseModel):
    title: str
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    area: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    labels: Optional[List[Dict[str, Any]]] = None  # Flexible JSON-like structure
    # New 3rd party API fields
    original_listing_url: Optional[str] = None
    api_source: Optional[str] = None
    api_property_id: Optional[str] = None
    api_images: Optional[List[str]] = None
    extended_description: Optional[str] = None
    api_amenities: Optional[List[str]] = None
    api_metadata: Optional[Dict[str, Any]] = None

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(PropertyBase):
    title: Optional[str] = None
    price: Optional[float] = None

class PropertyImageResponse(BaseModel):
    id: int
    image_url: str
    is_primary: bool
    labels: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True

# Landlord info for property responses
class LandlordInfo(BaseModel):
    id: int
    company_name: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    verification_status: bool = False
    profile_image_url: Optional[str] = None
    website_url: Optional[str] = None
    email: Optional[str] = None
    office_address: Optional[str] = None
    
    class Config:
        from_attributes = True

class PropertyResponse(PropertyBase):
    id: int
    landlord_id: int 
    created_at: datetime
    is_active: bool
    images: List[PropertyImageResponse] = []
    landlord: Optional[LandlordInfo] = None  # Include landlord information
    
    class Config:
        from_attributes = True


# Tenant Profile schemas - Updated to match models.py
class TenantProfileBase(BaseModel):
    budget: Optional[float] = None
    preferred_location: Optional[str] = None
    preferred_core_lat: Optional[float] = None
    preferred_core_lng: Optional[float] = None

class TenantProfileCreate(TenantProfileBase):
    pass

class TenantProfileUpdate(TenantProfileBase):
    pass

class TenantProfile(TenantProfileBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Landlord Profile schemas - Updated to match models.py
class LandlordProfileBase(BaseModel):
    company_name: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    verification_status: Optional[bool] = False
    # New 3rd party API fields
    profile_image_url: Optional[str] = None
    website_url: Optional[str] = None
    email: Optional[str] = None
    office_address: Optional[str] = None
    api_source: Optional[str] = None
    api_metadata: Optional[Dict[str, Any]] = None

class LandlordProfileCreate(LandlordProfileBase):
    pass

class LandlordProfileUpdate(LandlordProfileBase):
    pass

class LandlordProfile(LandlordProfileBase):
    id: int
    user_id: int
    created_at: datetime
    listed_properties: List[PropertyResponse] = []
    
    class Config:
        from_attributes = True
        
# User Preference schemas
class UserPreferenceBase(BaseModel):
    preference_key: str
    preference_value: str
    preference_category: str  # e.g., "property", "lifestyle", "roommate"

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreferenceUpdate(UserPreferenceBase):
    preference_key: Optional[str] = None
    preference_value: Optional[str] = None
    preference_category: Optional[str] = None

# Add this so that response includes all fields
class UserPreference(UserPreferenceBase):
    id: int
    user_id: int
    source: Optional[str] = None  # 'chat', 'image_upload', etc.
    created_at: Optional[datetime] = None
    distance_to_core: Optional[float] = None  # Search radius or confidence score
    
    class Config:
        from_attributes = True  # This was previously orm_mode = True

# Recommendation schemas
class PropertyRecommendation(BaseModel):
    id: int
    title: str
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    api_images: Optional[List[str]] = None  # Include api_images for fallback
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    area: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    match_score: int  # Score from 0-100
    
    class Config:
        from_attributes = True

class TenantProfileInfo(BaseModel):
    budget: Optional[float] = None
    preferred_location: Optional[str] = None
    
    class Config:
        from_attributes = True

class RoommateRecommendation(BaseModel):
    id: int
    username: str
    email: EmailStr
    match_score: int  # Score from 0-100
    tenant_profile: Optional[TenantProfileInfo] = None
    
    class Config:
        from_attributes = True
        
# chatai realted schemas
class ChatAIMessage(BaseModel):
    message: str
    
    class Config:
        from_attributes = True
        
class PreferenceOutput(BaseModel):
    key: str
    value: str
    category: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
class ChatAIResponse(BaseModel):
    response: str
    
    class Config:
        from_attributes = True
        
class ChatFullResponse(ChatAIResponse):
    preferences: Optional[List[PreferenceOutput]] = []
    
    class Config:
        from_attributes = True


# Message schemas
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    receiver_id: int

class MessageUpdate(BaseModel):
    is_read: bool = True

class MessageResponse(MessageBase):
    id: int
    sender_id: int
    receiver_id: int
    timestamp: datetime
    is_read: bool
    
    class Config:
        from_attributes = True

# Comment schemas
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    property_id: int

class CommentResponse(CommentBase):
    id: int
    user_id: int
    property_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True