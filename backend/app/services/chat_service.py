# app/services/chat_service.py
from typing import Dict, List, Optional
from openai import OpenAI
import re
import json

from app.config import settings
from app.models import UserPreference

class ChatService:
    """Service for AI chat interactions and preference extraction"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
    
    def chat_with_ai(self, user_message: str, history: Optional[List[Dict]] = None) -> Dict:
        """
        Process user message with AI and extract housing preferences
        
        Args:
            user_message: The user's input message
            history: Optional list of previous message dictionaries
            
        Returns:
            Dictionary containing AI response and extracted preferences
        """
        # Prepare system message with detailed prompt
        system_message = """
        You are a professional real estate consultant helping users find their ideal home near CMU (Carnegie Mellon University).
        Identify the user's housing preferences in the following categories:
        
        1. Property preferences:
           - property_type (apartment, house, condo, studio)
           - bedrooms (1, 2, 3+)
           - bathrooms (1, 1.5, 2+)
           - price_range (budget in $)
           - amenities (parking, laundry, gym, etc.)
        
        2. Location preferences:
           - neighborhood (Shadyside, Squirrel Hill, Oakland, etc.)
           - distance_to_campus (walking distance, 5 min drive, etc.)
           - transportation (bus access, bikeable, need parking, etc.)
        
        3. Lifestyle preferences:
           - noise_level (quiet, moderate, lively)
           - roommates (yes, no, how many)
           - pet_friendly (yes, no, type of pet)
           - study_space (needs desk, separate room, etc.)
        
        Return your response in two parts:
        1. A helpful, conversational response to the user
        2. A JSON object with extracted preferences in this format:
           {
             "preferences": [
               {
                 "key": "property_type",
                 "value": "apartment",
                 "category": "property",
                 "description": "User is looking for an apartment"
               },
               ...
             ]
           }
        
        Only include preferences that you can confidently extract from the conversation.
        """
        
        # Prepare messages for the API call
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history if provided
        if history:
            messages.extend(history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,  # More creative but still focused
            max_tokens=1000   # Allow longer responses
        )

        bot_response = response.choices[0].message.content
        
        # Try to extract preference information
        preferences = []
        try:
            # Find JSON part in the response using regex
            json_match = re.search(r'\{.*\}', bot_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                preferences_data = json.loads(json_str)
                
                if "preferences" in preferences_data:
                    preferences = preferences_data["preferences"]
                    # Add default values if missing
                    for pref in preferences:
                        if "category" not in pref:
                            pref["category"] = "property"
                        if "description" not in pref:
                            pref["description"] = f"Preference for {pref['key']}: {pref['value']}"
            
            # Return clean response without JSON
            clean_response = re.sub(r'\{.*\}', '', bot_response, flags=re.DOTALL).strip()
            
        except Exception as e:
            # If JSON parsing fails, return original response
            clean_response = bot_response
            print(f"Error parsing preferences: {e}")
        
        return {
            "response": clean_response,
            "preferences": preferences
        }
    
    def create_preference_objects(self, user_id: int, preferences: List[Dict]) -> List[UserPreference]:
        """
        Convert extracted preferences to UserPreference objects
        
        Args:
            user_id: ID of the current user
            preferences: List of preference dictionaries
        
        Returns:
            List of UserPreference objects ready to be added to the database
        """
        preference_objects = []
        
        for pref in preferences:
            # Check for required fields
            if "key" not in pref or "value" not in pref:
                continue
                
            preference = UserPreference(
                user_id=user_id,
                preference_key=pref["key"],
                preference_value=pref["value"],
                preference_category=pref.get("category", "property"),
                source="chat"
            )
            preference_objects.append(preference)
        
        return preference_objects