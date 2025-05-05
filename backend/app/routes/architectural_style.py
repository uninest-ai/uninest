# app/routes/architectural_style.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Body, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List

from app.database import get_db
from app.models import User, Property
from app.auth import get_current_user
from app.services.architectural_classifier import ArchitecturalStyleClassifier

router = APIRouter()
style_classifier = ArchitecturalStyleClassifier()

@router.post("/classify", response_model=Dict[str, Any])
async def classify_architectural_style(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Classify the architectural style of a building in an image
    
    Args:
        file: Uploaded image of a building
        current_user: Authenticated user
        db: Database session
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are accepted"
        )
    
    # Read image data
    image_data = await file.read()
    
    # Classify architectural style
    result = style_classifier.classify_architectural_style(image_data)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return result

@router.post("/compare", response_model=Dict[str, Any])
async def compare_architectural_styles(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare architectural styles between two buildings
    
    Args:
        file1: First building image
        file2: Second building image
        current_user: Authenticated user
        db: Database session
    """
    # Check file types
    if not file1.content_type.startswith("image/") or not file2.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are accepted"
        )
    
    # Read image data
    image_data1 = await file1.read()
    image_data2 = await file2.read()
    
    # Compare styles
    result = style_classifier.compare_architectural_styles(image_data1, image_data2)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return result

@router.get("/guidelines/{style_name}", response_model=Dict[str, Any])
async def get_style_guidelines(
    style_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed architectural style guidelines
    
    Args:
        style_name: Name of architectural style
        current_user: Authenticated user
        db: Database session
    """
    # Generate style guidelines
    result = style_classifier.generate_style_guidelines(style_name)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return result

@router.post("/property/{property_id}/classify", response_model=Dict[str, Any])
async def classify_property_style(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Classify the architectural style of an existing property
    
    Args:
        property_id: ID of the property to classify
        current_user: Authenticated user
        db: Database session
    """
    # Check if property exists
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Check if property has an image
    if not property.image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property has no image to classify"
        )
    
    # Download image (simplified - in a real system, you would use proper download logic)
    import requests
    try:
        response = requests.get(property.image_url)
        image_data = response.content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading property image: {str(e)}"
        )
    
    # Classify architectural style
    result = style_classifier.classify_architectural_style(image_data)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    # Update property with style information
    try:
        # Extract primary style
        primary_style = result["classification"]["primary_architectural_style"]
        
        # Create or update property labels
        if property.labels is None:
            property.labels = []
        
        # Check if style label already exists
        style_label_exists = False
        for i, label in enumerate(property.labels):
            if isinstance(label, dict) and label.get("name") == "architectural_style":
                # Update existing label
                property.labels[i]["value"] = primary_style
                property.labels[i]["confidence"] = result["classification"]["confidence_score"]
                style_label_exists = True
                break
        
        # Add new label if needed
        if not style_label_exists:
            property.labels.append({
                "name": "architectural_style",
                "value": primary_style,
                "confidence": result["classification"]["confidence_score"],
                "type": "primary_attribute"
            })
        
        # Save to database
        db.commit()
        
        # Return result with updated property info
        result["property_updated"] = True
        return result
        
    except Exception as e:
        db.rollback()
        # Still return classification result even if update failed
        result["property_updated"] = False
        result["update_error"] = str(e)
        return result