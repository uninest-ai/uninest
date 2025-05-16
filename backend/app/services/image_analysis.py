import base64
import json
import re
from typing import Dict, Any, List
from openai import OpenAI
from app.config import settings

class SimpleImageAnalysisService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
    
    def _extract_features(self, image_bytes: bytes, analysis_type: str) -> Dict[str, Any]:
        """
        Extract features from an image using OpenAI Vision API
        
        Args:
            image_bytes: Image data in bytes
            analysis_type: 'tenant_preference' or 'property_listing'
        
        Returns:
            Dictionary of extracted features
        """
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Customize prompt based on analysis type
        if analysis_type == 'tenant_preference':
            prompt = (
                "Analyze this image of an ideal home. Identify key characteristics "
                "that represent the tenant's preferences. Return a JSON with the following "
                "structure: {"
                "'architectural_style': {'value': '...', 'confidence': 0-1}, "
                "'space_feeling': {'value': '...', 'confidence': 0-1}, "
                "'key_features': [{'name': '...', 'confidence': 0-1}, ...], "
                "'mood': {'value': '...', 'confidence': 0-1}"
                "}"
            )
        else:  # property_listing
            prompt = (
                "Analyze this property image. Identify detailed characteristics "
                "of the property. Return a JSON with the following structure: {"
                "'property_type': {'value': '...', 'confidence': 0-1}, "
                "'architectural_style': {'value': '...', 'confidence': 0-1}, "
                "'key_features': [{'name': '...', 'confidence': 0-1}, ...], "
                "'condition': {'value': '...', 'confidence': 0-1}, "
                "'potential_appeal': {'value': '...', 'confidence': 0-1}"
                "}"
            )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            # Extract content
            content = response.choices[0].message.content
            
            # Extract JSON 
            json_match = re.search(r'\{.*\}', content, re.DOTALL | re.MULTILINE)
            if json_match:
                try:
                    features = json.loads(json_match.group(0))
                    return {
                        "status": "success",
                        "features": self._normalize_features(features)
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "message": "Could not parse JSON from response"
                    }
            
            return {
                "status": "error",
                "message": "No JSON found in response"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _normalize_features(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize features into a consistent list format
        
        Args:
            features: Raw features dictionary from OpenAI
        
        Returns:
            Normalized list of features
        """
        normalized_features = []
        
        # Process top-level single-value features
        for key, value in features.items():
            if isinstance(value, dict) and 'value' in value and 'confidence' in value:
                normalized_features.append({
                    "name": key,
                    "value": value['value'],
                    "confidence": value['confidence'],
                    "type": "primary_attribute"
                })
        
        # Process key features list
        if 'key_features' in features and isinstance(features['key_features'], list):
            normalized_features.extend([
                {
                    "name": feature['name'] if isinstance(feature, dict) else feature,
                    "confidence": feature.get('confidence', 0.7) if isinstance(feature, dict) else 0.7,
                    "type": "additional_feature"
                } for feature in features['key_features']
            ])
        
        return normalized_features
    
    def analyze_tenant_preference_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze an image uploaded by a tenant representing their ideal home
        
        Args:
            image_bytes: Image data in bytes
        
        Returns:
            Analyzed features of the ideal home
        """
        return self._extract_features(image_bytes, 'tenant_preference')
    
    def analyze_property_listing_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze an image uploaded by a landlord of their property
        
        Args:
            image_bytes: Image data in bytes
        
        Returns:
            Analyzed features of the property
        """
        return self._extract_features(image_bytes, 'property_listing')