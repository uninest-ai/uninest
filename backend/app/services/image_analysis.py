import base64
import json
import re
from typing import Dict, Any, List
import google.generativeai as genai
from app.config import settings

class SimpleImageAnalysisService:
    def __init__(self):
        # Try Gemini first (cheaper), fallback to OpenAI if needed
        self.gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.openai_key = getattr(settings, 'OPENAI_API_KEY', None)

        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.client = genai.GenerativeModel('gemini-1.5-flash')
                self.client_type = "gemini"
                print("Gemini client initialized successfully (cost-effective!)")
            except Exception as e:
                print(f"Warning: Gemini client initialization failed: {e}")
                self.client = None
                self.client_type = None
        else:
            print("No GEMINI_API_KEY found, image analysis unavailable")
            self.client = None
            self.client_type = None
    
    def _extract_features(self, image_bytes: bytes, analysis_type: str) -> Dict[str, Any]:
        """
        Extract features from an image using Gemini Vision API

        Args:
            image_bytes: Image data in bytes
            analysis_type: 'tenant_preference' or 'property_listing'

        Returns:
            Dictionary of extracted features
        """
        if self.client is None:
            return {"error": "AI client not available"}

        # Customize prompt based on analysis type
        if analysis_type == 'tenant_preference':
            prompt = (
                "Analyze this image of an ideal home. Identify key characteristics "
                "that represent the tenant's preferences. Return ONLY a valid JSON (no markdown, no ```json```) with this structure: "
                "{'architectural_style': {'value': '...', 'confidence': 0.8}, "
                "'space_feeling': {'value': '...', 'confidence': 0.8}, "
                "'key_features': [{'name': '...', 'confidence': 0.8}], "
                "'mood': {'value': '...', 'confidence': 0.8}}"
            )
        else:  # property_listing
            prompt = (
                "Analyze this property image. Identify detailed characteristics. "
                "Return ONLY a valid JSON (no markdown, no ```json```) with this structure: "
                "{'property_type': {'value': '...', 'confidence': 0.8}, "
                "'architectural_style': {'value': '...', 'confidence': 0.8}, "
                "'key_features': [{'name': '...', 'confidence': 0.8}], "
                "'condition': {'value': '...', 'confidence': 0.8}, "
                "'potential_appeal': {'value': '...', 'confidence': 0.8}}"
            )

        try:
            # Use Gemini API
            import PIL.Image
            import io

            # Convert bytes to PIL Image for Gemini
            image = PIL.Image.open(io.BytesIO(image_bytes))

            # Generate content with Gemini
            response = self.client.generate_content([prompt, image])

            # Extract content
            content = response.text

            # Remove markdown code blocks if present
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            content = content.strip()

            # Extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL | re.MULTILINE)
            if json_match:
                try:
                    features = json.loads(json_match.group(0))
                    return {
                        "status": "success",
                        "features": self._normalize_features(features)
                    }
                except json.JSONDecodeError as e:
                    return {
                        "status": "error",
                        "message": f"Could not parse JSON from response: {str(e)}"
                    }

            return {
                "status": "error",
                "message": "No JSON found in response",
                "raw_response": content[:200]  # First 200 chars for debugging
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Gemini API error: {str(e)}"
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