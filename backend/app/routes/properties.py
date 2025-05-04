from app import schemas
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.models import Property, PropertyImage, LandlordProfile, User
from app.schemas import PropertyCreate, PropertyResponse, PropertyUpdate
from app.auth import get_current_user
from app.services.storage_service import S3ImageService
from app.services.image_analysis import SimpleImageAnalysisService

router = APIRouter()
image_service = SimpleImageAnalysisService()
storage_service = S3ImageService()

@router.post("/", response_model=schemas.PropertyResponse)
def create_property(
    property_data: schemas.PropertyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new property listing"""
    # Check
    if current_user.user_type != "landlord":
        raise HTTPException(status_code=403, detail="Only landlords can create properties")
    
    # Get data
    landlord_profile = db.query(LandlordProfile).filter(
        LandlordProfile.user_id == current_user.id
    ).first()
    
    if not landlord_profile:
        raise HTTPException(status_code=404, detail="Landlord profile not found")
    
    # Create new
    new_property = Property(
        **property_data.dict(),
        landlord_id=landlord_profile.id
    )
    
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    
    return new_property

@router.get("/", response_model=List[PropertyResponse], summary="Get All Properties")
def get_properties(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all property listings with pagination"""
    # Join load the landlord relationship for all properties
    properties = db.query(Property).options(
        joinedload(Property.landlord).joinedload(LandlordProfile.user)
    ).offset(skip).limit(limit).all()
    
    # Add landlord information to each property
    response = []
    for property in properties:
        prop_response = PropertyResponse.from_orm(property)
        if property.landlord:
            prop_response.landlord_company = property.landlord.company_name
            prop_response.landlord_contact = property.landlord.contact_phone
            prop_response.landlord_description = property.landlord.description
            prop_response.landlord_verification = property.landlord.verification_status
            prop_response.landlord_name = property.landlord.user.username if property.landlord.user else None
        response.append(prop_response)
    
    return response

@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific property by ID"""
    # Join load the landlord relationship to get landlord information
    property = db.query(Property).options(
        joinedload(Property.landlord).joinedload(LandlordProfile.user)
    ).filter(Property.id == property_id).first()
    
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Add landlord information to the response
    response = PropertyResponse.from_orm(property)
    if property.landlord:
        response.landlord_company = property.landlord.company_name
        response.landlord_contact = property.landlord.contact_phone
        response.landlord_description = property.landlord.description
        response.landlord_verification = property.landlord.verification_status
        response.landlord_name = property.landlord.user.username if property.landlord.user else None
    
    return response

@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a property listing"""
    property = db.query(Property).filter(Property.id == property_id).first()
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Get landlord profile
    landlord_profile = db.query(LandlordProfile).filter(
        LandlordProfile.user_id == current_user.id
    ).first()
    
    # Check case: Instead of checking property.owner_id which doesn't exist
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this property")
    
    # Update property fields
    for key, value in property_data.dict(exclude_unset=True).items():
        setattr(property, key, value)
    
    db.commit()
    db.refresh(property)
    return property

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a property listing"""
    property = db.query(Property).filter(Property.id == property_id).first()
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Get landlord profile
    landlord_profile = db.query(LandlordProfile).filter(
        LandlordProfile.user_id == current_user.id
    ).first()
    
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this property")
    
    # First delete all associated property images
    db.query(PropertyImage).filter(PropertyImage.property_id == property_id).delete()
    
    # Then delete the property itself
    db.delete(property)
    db.commit()
    return None

@router.post("/{property_id}/images", response_model=dict)
async def upload_property_images(
    property_id: int,
    files: List[UploadFile] = File(...),
    is_primary: bool = Form(False),  # if the first as primary
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload multiple property images"""
    # check
    if current_user.user_type != "landlord":
        raise HTTPException(status_code=403, detail="Only landlord can upload images")
    
    # check if exists and is the landlord's
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail= f"Property {property_id} not exists")
    
    landlord_profile = current_user.landlord_profile
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="You are not the landlord of this properties")
    
    uploaded_images = []
    
    # for multiple images
    for i, file in enumerate(files):
        try:
            # get to analyse
            image_data = await file.read()
            await file.seek(0)  # reset pointer
            
            analysis_result = image_service.analyze_property_listing_image(image_data)
            
            # upload to s3
            image_url = await storage_service.upload_image(file, property_id, landlord_profile.id)
            
            # Set as primary if first image and is_primary is True, or no existing images
            set_as_primary = False
            if i == 0 and is_primary:
                # Set the previous primary image (if any) to non-primary
                existing_primary = db.query(PropertyImage).filter(
                    PropertyImage.property_id == property_id,
                    PropertyImage.is_primary == True
                ).first()
                
                if existing_primary:
                    existing_primary.is_primary = False
                    
                set_as_primary = True
            elif db.query(PropertyImage).filter(PropertyImage.property_id == property_id).count() == 0:
                # If this is the property's first image, set it as the primary image
                set_as_primary = True
            
            # New img
            property_image = PropertyImage(
                property_id=property_id,
                image_url=image_url,
                is_primary=set_as_primary,
                labels=analysis_result.get("features", [])
            )
            
            db.add(property_image)
            db.flush()  # Get ID without committing
            
            # If it's the primary image, update the property's main image URL
            if set_as_primary:
                property.image_url = image_url
            
            uploaded_images.append({
                "id": property_image.id,
                "image_url": image_url,
                "is_primary": set_as_primary,
                "analysis": analysis_result.get("features", [])
            })
        
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload fail: {str(e)}"
            )
    
    # Commit changes
    db.commit()
    
    return {
        "status": "success",
        "message": f"{len(uploaded_images)} of images uploaded",
        "images": uploaded_images
    }

# Get all the images
@router.get("/{property_id}/images", response_model=List[dict])
async def get_property_images(
    property_id: int,
    db: Session = Depends(get_db)
):
    """All images"""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail= f"Property {property_id} not exists")
    
    images = db.query(PropertyImage).filter(
        PropertyImage.property_id == property_id
    ).all()
    
    return [
        {
            "id": image.id,
            "image_url": image.image_url,
            "is_primary": image.is_primary,
            "labels": image.labels
        }
        for image in images
    ]

# Delete images
@router.delete("/{property_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property_image(
    property_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete property images"""
    # Check if landlord
    if current_user.user_type != "landlord":
        raise HTTPException(status_code=403, detail="Only landlord can delete properties images")
    
    # Check if property exists and is landlords'
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not exists")
    
    landlord_profile = current_user.landlord_profile
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete images (you are not the landlord of this properties)")
    
    # Filter image to delete
    image = db.query(PropertyImage).filter(
        PropertyImage.id == image_id,
        PropertyImage.property_id == property_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail=f"Property {image_id} not exists")
    
    if image.is_primary:
        other_image = db.query(PropertyImage).filter(
            PropertyImage.property_id == property_id,
            PropertyImage.id != image_id
        ).first()
        
        if other_image:
            other_image.is_primary = True
            property.image_url = other_image.image_url
        else:
            property.image_url = None
    
    db.delete(image)
    db.commit()
    
    return None

# Set primary picture
@router.put("/{property_id}/images/{image_id}/primary", response_model=dict)
async def set_primary_image(
    property_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set certain image to be primary images"""
    # Check if landlord
    if current_user.user_type != "landlord":
        raise HTTPException(status_code=403, detail="Only landlord can set primary image")
    
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not exists")
    
    landlord_profile = current_user.landlord_profile
    if not landlord_profile or property.landlord_id != landlord_profile.id:
        raise HTTPException(status_code=403, detail="Not authorize to set property primary images")
    
    # Find the prim img
    new_primary = db.query(PropertyImage).filter(
        PropertyImage.id == image_id,
        PropertyImage.property_id == property_id
    ).first()
    
    if not new_primary:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not exists")
    
    # set curr to prim
    current_primary = db.query(PropertyImage).filter(
        PropertyImage.property_id == property_id,
        PropertyImage.is_primary == True
    ).first()
    
    if current_primary:
        current_primary.is_primary = False
    
    # Set new primary
    new_primary.is_primary = True
    property.image_url = new_primary.image_url
    
    db.commit()
    
    return {
        "status": "success",
        "message": "primary image set successfully",
        "image": {
            "id": new_primary.id,
            "image_url": new_primary.image_url,
            "is_primary": True
        }
    }