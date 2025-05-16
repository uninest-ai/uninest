# app/routes/floor_plans.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.services.floor_plan_analyzer import FloorPlanAnalysisService

router = APIRouter()
floor_plan_service = FloorPlanAnalysisService()

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_floor_plan(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a floor plan image to extract architectural features
    
    Args:
        file: Uploaded floor plan image
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
    
    # Analyze floor plan
    analysis_result = floor_plan_service.analyze_floor_plan(image_data)
    
    if analysis_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=analysis_result["message"]
        )
    
    # Generate optimization suggestions
    suggestions = floor_plan_service.generate_optimization_suggestions(analysis_result["analysis"])
    
    return {
        "status": "success",
        "analysis": analysis_result["analysis"],
        "optimization_suggestions": suggestions
    }

@router.post("/materials", response_model=Dict[str, Any])
async def analyze_construction_materials(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze construction materials in a property image
    
    Args:
        file: Uploaded property image
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
    
    # Analyze materials
    analysis_result = floor_plan_service.analyze_construction_materials(image_data)
    
    if analysis_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=analysis_result["message"]
        )
    
    return analysis_result

@router.post("/efficiency", response_model=Dict[str, Any])
async def analyze_space_efficiency(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze space efficiency and propose optimizations for a floor plan
    
    Args:
        file: Uploaded floor plan image
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
    
    # Analyze floor plan for efficiency
    analysis_result = floor_plan_service.analyze_floor_plan(image_data)
    
    if analysis_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=analysis_result["message"]
        )
    
    # Extract efficiency-specific metrics
    efficiency_metrics = {
        "layout_efficiency": analysis_result["analysis"].get("layout_efficiency_score", 0),
        "spatial_relationships": analysis_result["analysis"].get("spatial_relationships", {}),
        "traffic_flow": analysis_result["analysis"].get("traffic_flow_patterns", {}),
        "natural_light": analysis_result["analysis"].get("natural_light_optimization", 0)
    }
    
    # Generate efficiency-focused optimization suggestions
    suggestions = floor_plan_service.generate_optimization_suggestions(analysis_result["analysis"])
    efficiency_suggestions = [s for s in suggestions if s.get("category") in ["space_efficiency", "traffic_flow"]]
    
    return {
        "status": "success",
        "efficiency_metrics": efficiency_metrics,
        "optimization_suggestions": efficiency_suggestions
    }