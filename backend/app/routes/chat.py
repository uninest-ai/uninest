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
client = OpenAI(api_key=settings.OPENAI_API_KEY)  # Create client instance

@router.post("/message", response_model=Dict)
async def chat_with_bot(
    message: Dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat AI: collect user preference"""
    user_message = message.get("message", "")
    
    # get prev convo for faster (not implement yet)
    
    # Use faster OpenAI model for better response times
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Faster and cheaper than GPT-4
        messages=[
            {"role": "system", "content": "You are a real estate consultant helping users find their ideal home. Try to identify user preferences and return them in JSON format {'preferences': [{'key': 'feature_name', 'value': 'preference_level'}]}."},
            {"role": "user", "content": user_message}
        ],
        max_tokens=300,  # Limit response length for faster responses
        temperature=0.7  # Slightly more focused responses
    )
    
    bot_response = response.choices[0].message.content
    
    # Extract
    try:
        import json
        import re
        
        preferences_data = None
        
        # Search json
        json_match = re.search(r'\{.*\}', bot_response, re.DOTALL)
        if json_match:
            preferences_data = json.loads(json_match.group())
            
            if preferences_data and "preferences" in preferences_data:
                # save pref
                for pref in preferences_data["preferences"]:
                    preference = UserPreference(
                        user_id=current_user.id,
                        preference_key=pref["key"],
                        preference_value=pref["value"],
                        source="chat"
                    )
                    db.add(preference)
                
                db.commit()
        
        # Include the JSON preferences in the response
        clean_response = re.sub(r'\{.*\}', '', bot_response, flags=re.DOTALL).strip()
        
        # Add the extracted preferences to the response
        if preferences_data and "preferences" in preferences_data:
            preferences_json = json.dumps(preferences_data, indent=2)
            final_response = f"{clean_response}\n\nHere are the preferences I've collected from our conversation:\n```json\n{preferences_json}\n```"
        else:
            final_response = clean_response
            
        return {"response": final_response}
    
    except Exception as e:
        # return ori if parse fails
        return {"response": bot_response}