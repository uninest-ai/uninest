# app/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict

from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserPreference
from openai import OpenAI
from app.config import settings

router = APIRouter()

@router.post("/message", response_model=Dict)
async def chat_with_bot(
    message: Dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ChatAI: Collect user preference"""
    user_message = message.get("message", "")
    
    # Retrieve previous chat history (not implemented in this example)
    
    # Get OpenAI API
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a real estate consultant helping users find their ideal home. Try to identify the user's preferences and return them in JSON format {'preferences': [{'key': 'feature_name', 'value': 'preference_level'}]}."},
            {"role": "user", "content": user_message}
        ]
    )

    bot_response = response.choices[0].message.content
    
    # Extract and construct User preference
    try:
        import json
        import re
        
        # Locate text using re
        json_match = re.search(r'\{.*\}', bot_response, re.DOTALL)
        if json_match:
            preferences_data = json.loads(json_match.group())
            
            if "preferences" in preferences_data:
                # Save preference
                for pref in preferences_data["preferences"]:
                    preference = UserPreference(
                        user_id=current_user.id,
                        preference_key=pref["key"],
                        preference_value=pref["value"],
                        source="chat"
                    )
                    db.add(preference)
                
                db.commit()
        
        # strip and clean response
        clean_response = re.sub(r'\{.*\}', '', bot_response, flags=re.DOTALL).strip()
        return {"response": clean_response}
    
    except Exception as e:
        # send back original if parse fail
        return {"response": bot_response}