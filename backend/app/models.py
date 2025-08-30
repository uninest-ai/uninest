from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, Table, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

# Define association tables for many-to-many relationships
# roommate preferences should be related to each user. what this means is the potential roomates of the user(tenant)
roommate_preferences = Table(
    "roommate_preferences",
    Base.metadata,
    Column("tenant_profile_id", Integer, ForeignKey("tenant_profiles.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True)
)

# potential properties to tenant
property_preferences = Table(
    "property_preferences",
    Base.metadata,
    # foreign key to tenant profile instead of user cause user included landlord.
    Column("tenant_profile_id", Integer, ForeignKey("tenant_profiles.id"), primary_key=True),
    Column("property_id", Integer, ForeignKey("properties.id"), primary_key=True)
)

# Not using inheritance so user can be tenant and owner at the same time (IGNORE this, do this when free ltr)
# In the User class, add the preferred_roommates relationship
class User(Base):
    """
    User model representing registered users
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    user_type = Column(String, nullable=False)  # 'tenant' or 'landlord'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    interactions = relationship("Interaction", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    
    # this preference use to store user preferences, include labels extractec from chat, image upload, bio etc. Should I put this in tenant profile or user profile?
    preferences = relationship("UserPreference", back_populates="user")
    
    tenant_profile = relationship("TenantProfile", back_populates="user", uselist=False)
    landlord_profile = relationship("LandlordProfile", back_populates="user", uselist=False)
    
    preferred_roommates = relationship("TenantProfile", secondary=roommate_preferences, back_populates="recommended_roommates")

    @property
    def is_landlord(self):
        return self.user_type == "landlord"
        
    @property
    def is_tenant(self):
        return self.user_type == "tenant"

class TenantProfile(Base):
    """
    Profile for users who are looking for properties (tenants)
    """
    __tablename__ = "tenant_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    budget = Column(Float, nullable=True)
    preferred_location = Column(String, nullable=True)
    preferred_core_lat = Column(Float, nullable=True)  # Latitude of preferred core location
    preferred_core_lng = Column(Float, nullable=True)  # Longitude of preferred core location
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Recommendation lists
    recommended_properties = relationship("Property", secondary=property_preferences, back_populates="preferred_by_users")
    recommended_roommates = relationship("User", secondary=roommate_preferences, back_populates="preferred_roommates")
    
    # Relationship back to user
    user = relationship("User", back_populates="tenant_profile")

class LandlordProfile(Base):
    """
    Profile for users who own and list properties (landlords)
    """
    __tablename__ = "landlord_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    verification_status = Column(Boolean, default=False)  # Whether landlord is verified
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional fields for 3rd party API data
    profile_image_url = Column(String, nullable=True)  # Landlord/company profile image
    website_url = Column(String, nullable=True)  # Company website
    email = Column(String, nullable=True)  # Contact email
    office_address = Column(String, nullable=True)  # Office address
    api_source = Column(String, nullable=True)  # Source of landlord data (realtor16, etc.)
    api_metadata = Column(JSON, nullable=True)  # Additional API metadata
    
    # Relationship back to user
    user = relationship("User", back_populates="landlord_profile")
    # list of properties
    listed_properties = relationship("Property", back_populates="landlord")

class UserPreference(Base):
    """UserPreference Model for storing user-specific preferences"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preference_key = Column(String, nullable=False)
    preference_value = Column(String, nullable=False)
    preference_category = Column(String, nullable=False)  # e.g., 'lifestyle', 'property', 'roommate', 'location', 'tenant_ideal_home'
    source = Column(String, nullable=False)  # 'chat', 'image_upload', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    distance_to_core = Column(Float, nullable=True)  # Search radius or confidence score
    
    # Relationships
    user = relationship("User", back_populates="preferences")

# Find the Property class and modify the landlord_id column
class Property(Base):
    """
    Property model representing property listings
    """
    __tablename__ = "properties"

    # Basic info:
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text)
    image_url = Column(String)
    
    landlord_id = Column(Integer, ForeignKey("landlord_profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Property details
    property_type = Column(String, nullable=True)  # apartment, house, condo, etc.
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Float, nullable=True)  # 1.5, 2, etc.
    area = Column(Float, nullable=True)  # square footage
    
    # Labels stored as JSON
    labels = Column(JSON, nullable=True)  # Store labels as JSON
    
    # Location information
    latitude = Column(Float, nullable=True) 
    longitude = Column(Float, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    
    # 3rd Party API Data Fields
    original_listing_url = Column(String, nullable=True)  # Original housing website link
    api_source = Column(String, nullable=True)  # realtor16, realty_mole, etc.
    api_property_id = Column(String, nullable=True)  # Property ID from API
    api_images = Column(JSON, nullable=True)  # Images from API stored as JSON array
    extended_description = Column(Text, nullable=True)  # Additional description from API
    api_amenities = Column(JSON, nullable=True)  # Amenities from API stored as JSON
    api_metadata = Column(JSON, nullable=True)  # Additional metadata from API
    
    # Relationships
    landlord = relationship("LandlordProfile", back_populates="listed_properties")
    interactions = relationship("Interaction", back_populates="property")
    comments = relationship("Comment", back_populates="property")
    images = relationship("PropertyImage", back_populates="property")
    
    # Many-to-many relationship with tenant profiles
    preferred_by_users = relationship(
        "TenantProfile", 
        secondary="property_preferences", 
        back_populates="recommended_properties"
    )
    
class PropertyImage(Base):
    """房产图片模型"""
    __tablename__ = "property_images"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    image_url = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)  # 是否为主图
    labels = Column(JSON, nullable=True)  # 图片分析标签
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    property = relationship("Property", back_populates="images")

class Interaction(Base):
    """
    Interaction model for tracking user interactions with properties
    """
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    action = Column(String, nullable=False)  # 'click', 'like', 'comment'
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    property = relationship("Property", back_populates="interactions")

class Message(Base):
    """
    Message model for communication between users
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

class Comment(Base):
    """
    Comment model for property reviews
    """
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="comments")
    property = relationship("Property", back_populates="comments")