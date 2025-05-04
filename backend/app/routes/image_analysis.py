# app/routes/image_analysis.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.image_analysis import SimpleImageAnalysisService
from app.services.storage_service import S3ImageService
from app.auth import get_current_user
from app.models import User, UserPreference, Property, TenantProfile

router = APIRouter()
image_service = SimpleImageAnalysisService()

@router.post("/analyze", response_model=dict)
async def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze uploaded image and store preferences/property characteristics
    
    The analysis type is automatically determined based on user type:
    - For tenants: tenant_preference analysis
    - For landlords: property_listing analysis
    
    Args:
        file: Uploaded image file
        current_user: Authenticated user
        db: Database session
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are accepted"
        )
    
    # Automatically determine analysis type based on user type
    if current_user.user_type == "tenant":
        analysis_type = "tenant_preference"
    elif current_user.user_type == "landlord":
        analysis_type = "property_listing"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User type not recognized for image analysis"
        )
    
    # Read image data
    image_data = await file.read()
    
    # Perform analysis based on determined type
    if analysis_type == "tenant_preference":
        analysis_result = image_service.analyze_tenant_preference_image(image_data)
    else:  # property_listing
        analysis_result = image_service.analyze_property_listing_image(image_data)
    
    # Rest of your code remains the same
    if analysis_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=analysis_result["message"]
        )
    
    # Store preferences/labels based on user type
    try:
        if analysis_type == "tenant_preference":
            # Store as user preferences for tenant
            tenant_profile = db.query(TenantProfile).filter(
                TenantProfile.user_id == current_user.id
            ).first()
            
            # Store preferences
            for feature in analysis_result["features"]:
                pref = UserPreference(
                    user_id=current_user.id,
                    preference_key=feature["name"],
                    preference_value=str(feature.get("value", feature["name"])),
                    preference_category="tenant_ideal_home",
                    source="image_upload",
                    distance_to_core=feature.get("confidence", 0.7)
                )
                db.add(pref)
        
        else:  # property_listing
            # Verify landlord has a profile
            landlord_profile = current_user.landlord_profile
            if not landlord_profile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Landlord profile not found"
                )
            
            # Create or update a property with these labels
            property = Property(
                landlord_id=landlord_profile.id,
                labels=analysis_result["features"]
            )
            db.add(property)
        
        # Commit changes
        db.commit()
        
        return {
            "status": "success", 
            "message": f"Image analyzed as {analysis_type} and data stored",
            "features": analysis_result["features"]
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing analysis results: {str(e)}"
        )