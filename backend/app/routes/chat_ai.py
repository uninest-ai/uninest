# app/routes/chat.py
from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserPreference
from app.services.chat_service import ChatService
from app.schemas import ChatAIMessage, ChatAIResponse, ChatFullResponse, PreferenceOutput

router = APIRouter()
chat_service = ChatService()

@router.post("/message", response_model=ChatAIResponse)
async def chat_with_bot(
    message_data: ChatAIMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with AI and collect user preferences for housing recommendations
    
    - **message**: user input message
    """
    user_message = message_data.message
    
    # Use chat service to process message and extract preferences
    result = chat_service.chat_with_ai(user_message)
    
    # Create preference objects and save to database
    if result["preferences"]:
        preference_objects = chat_service.create_preference_objects(
            user_id=current_user.id,
            preferences=result["preferences"]
        )
        
        # Add preferences to database with upsert logic
        for pref_obj in preference_objects:
            # Check if preference already exists
            existing_pref = db.query(UserPreference).filter(
                UserPreference.user_id == pref_obj.user_id,
                UserPreference.preference_key == pref_obj.preference_key,
                UserPreference.preference_category == pref_obj.preference_category,
                UserPreference.source == pref_obj.source
            ).first()
            
            if existing_pref:
                # Update existing preference
                existing_pref.preference_value = pref_obj.preference_value
                existing_pref.created_at = pref_obj.created_at
            else:
                # Add new preference
                db.add(pref_obj)
        db.commit()
    
    return {"response": result["response"]}

@router.post("/message/full", response_model=ChatFullResponse)
async def chat_with_bot_full_response(
    message_data: ChatAIMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with AI and return both the response and extracted preferences
    
    - **message**: user input message
    """
    user_message = message_data.message
    
    # Use chat service to process message and extract preferences
    result = chat_service.chat_with_ai(user_message)
    
    # Create preference objects and save to database
    preference_objects = []
    if result["preferences"]:
        preference_objects = chat_service.create_preference_objects(
            user_id=current_user.id,
            preferences=result["preferences"]
        )
        
        # Add preferences to database with upsert logic
        for pref_obj in preference_objects:
            # Check if preference already exists
            existing_pref = db.query(UserPreference).filter(
                UserPreference.user_id == pref_obj.user_id,
                UserPreference.preference_key == pref_obj.preference_key,
                UserPreference.preference_category == pref_obj.preference_category,
                UserPreference.source == pref_obj.source
            ).first()
            
            if existing_pref:
                # Update existing preference
                existing_pref.preference_value = pref_obj.preference_value
                existing_pref.created_at = pref_obj.created_at
            else:
                # Add new preference
                db.add(pref_obj)
        db.commit()
        
        # Refresh each preference object individually
        for pref_obj in preference_objects:
            if pref_obj in db:
                db.refresh(pref_obj)
    
    # Format preferences for response
    preferences_output = [
        {
            "key": pref.preference_key,
            "value": pref.preference_value,
            "category": pref.preference_category,
            "created_at": pref.created_at
        }
        for pref in preference_objects
    ]
    
    return {
        "response": result["response"],
        "preferences": preferences_output
    }

@router.get("/preferences", response_model=List[PreferenceOutput])
async def get_user_preferences(
    category: Optional[str] = Query(None, description="Filter preferences by specific category"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's housing preferences collected from chat interactions
    
    - **category**: Optional preference category filter (e.g., "property", "lifestyle", "location")
    """
    query = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id,
        UserPreference.source == "chat"
    )
    
    if category:
        query = query.filter(UserPreference.preference_category == category)
    
    preferences = query.all()
    
    return [
        {
            "key": pref.preference_key,
            "value": pref.preference_value,
            "category": pref.preference_category,
            "created_at": pref.created_at
        }
        for pref in preferences
    ]

@router.delete("/preferences", status_code=204)
async def clear_user_preferences(
    category: Optional[str] = Query(None, description="Filter preferences by specific category"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear user housing preferences collected from chat interactions
    
    - **category**: Optional preference category filter, if provided, only preferences in that category will be deleted
    """
    query = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id,
        UserPreference.source == "chat"
    )
    
    if category:
        query = query.filter(UserPreference.preference_category == category)
    
    query.delete()
    db.commit()
    return None