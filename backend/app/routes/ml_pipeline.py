# app/routes/ml_pipeline.py
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.services.ml_data_pipeline import MLDataPipelineService

router = APIRouter()

@router.post("/extract-property-features", response_model=Dict[str, Any])
def extract_property_features(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract property features for ML model training
    """
    # Check if user has admin access
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access ML pipeline functions"
        )
    
    # Create pipeline service
    pipeline_service = MLDataPipelineService(db)
    
    # Extract property features
    try:
        df = pipeline_service.extract_property_features_dataset()
        
        return {
            "status": "success",
            "message": f"Successfully extracted {len(df)} property records",
            "columns": df.columns.tolist(),
            "sample": df.head(5).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting property features: {str(e)}"
        )

@router.post("/prepare-floor-plan-data", response_model=Dict[str, Any])
def prepare_floor_plan_data(
    labeled_data: List[Dict[str, Any]] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prepare floor plan annotations for ML model training
    """
    # Check if user has admin access
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access ML pipeline functions"
        )
    
    # Create pipeline service
    pipeline_service = MLDataPipelineService(db)
    
    # Prepare floor plan data
    try:
        df, file_path = pipeline_service.prepare_floor_plan_training_data(labeled_data)
        
        return {
            "status": "success",
            "message": f"Successfully prepared {len(df)} floor plan annotations",
            "file_path": file_path,
            "columns": df.columns.tolist(),
            "sample": df.head(5).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error preparing floor plan data: {str(e)}"
        )

@router.post("/generate-feature-vectors", response_model=Dict[str, Any])
def generate_feature_vectors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate architectural feature vectors for ML model training
    """
    # Check if user has admin access
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access ML pipeline functions"
        )
    
    # Create pipeline service
    pipeline_service = MLDataPipelineService(db)
    
    # Generate feature vectors
    try:
        feature_array = pipeline_service.generate_architectural_feature_vectors()
        
        return {
            "status": "success",
            "message": f"Successfully generated {feature_array.shape[0]} feature vectors with {feature_array.shape[1]} dimensions",
            "shape": feature_array.shape,
            "sample": feature_array[:5].tolist()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating feature vectors: {str(e)}"
        )

@router.post("/upload-floor-plan-annotation", response_model=Dict[str, Any])
async def upload_floor_plan_annotation(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a floor plan annotation file (JSON format)
    """
    # Check if user has admin or annotator access
    if current_user.user_type not in ["admin", "annotator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or annotator users can upload annotations"
        )
    
    # Check file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON annotation files are accepted"
        )
    
    # Read file content
    content = await file.read()
    
    try:
        # Parse JSON content
        import json
        annotations = json.loads(content)
        
        # Create pipeline service
        pipeline_service = MLDataPipelineService(db)
        
        # Process annotations
        df, file_path = pipeline_service.prepare_floor_plan_training_data([annotations])
        
        return {
            "status": "success",
            "message": "Successfully uploaded floor plan annotation",
            "file_path": file_path
        }
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing annotation: {str(e)}"
        )

@router.get("/audit-training-data", response_model=Dict[str, Any])
def audit_training_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Audit ML training data for quality and completeness
    """
    # Check if user has admin access
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access ML pipeline functions"
        )
    
    # Create pipeline service
    pipeline_service = MLDataPipelineService(db)
    
    # Audit training data
    try:
        audit_report = pipeline_service.audit_training_data()
        
        return {
            "status": "success",
            "audit_report": audit_report
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error auditing training data: {str(e)}"
        )

@router.get("/extract-user-preferences", response_model=Dict[str, Any])
def extract_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract user preferences for recommendation model training
    """
    # Check if user has admin access
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access ML pipeline functions"
        )
    
    # Create pipeline service
    pipeline_service = MLDataPipelineService(db)
    
    # Extract user preferences
    try:
        df = pipeline_service.extract_user_preferences_dataset()
        
        return {
            "status": "success",
            "message": f"Successfully extracted {len(df)} user preference records",
            "columns": df.columns.tolist(),
            "sample": df.head(5).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting user preferences: {str(e)}"
        )