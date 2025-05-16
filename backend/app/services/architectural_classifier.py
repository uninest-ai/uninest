# app/services/architectural_classifier.py
import base64
import json
import re
import numpy as np
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.config import settings

class ArchitecturalStyleClassifier:
    """Service for analyzing and classifying architectural styles in property images"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        
        # Define common architectural styles with features
        self.styles = {
            "modern": {
                "features": ["clean lines", "open floor plans", "minimal ornamentation", 
                             "flat roofs", "large windows", "integration with nature"],
                "materials": ["concrete", "steel", "glass", "exposed elements"]
            },
            "contemporary": {
                "features": ["asymmetrical shapes", "open spaces", "sustainable elements",
                             "emphasis on indoor-outdoor living", "irregular forms"],
                "materials": ["recycled materials", "sustainable wood", "energy-efficient glass"]
            },
            "craftsman": {
                "features": ["low-pitched roofs", "wide eaves", "exposed beams", 
                             "tapered columns", "porches", "built-in furniture"],
                "materials": ["natural wood", "stone", "handcrafted details", "earthy colors"]
            },
            "colonial": {
                "features": ["symmetrical facades", "centered entry door", "multi-pane windows",
                             "medium-pitched roofs", "classic proportions"],
                "materials": ["brick", "wood siding", "shutters", "columns"]
            },
            "mediterranean": {
                "features": ["stucco walls", "low-pitched tile roofs", "arched doorways",
                             "wrought iron details", "courtyards", "warm colors"],
                "materials": ["terracotta", "stucco", "clay tiles", "wrought iron"]
            },
            "mid-century_modern": {
                "features": ["flat planes", "large glass windows", "open space",
                             "integration with nature", "changes in elevation"],
                "materials": ["wood", "glass", "steel", "non-traditional materials"]
            },
            "victorian": {
                "features": ["asymmetrical shapes", "steep pitched roofs", "textured wall surfaces",
                             "ornate trim", "towers", "bay windows", "vibrant colors"],
                "materials": ["wood siding", "intricate woodwork", "decorative glass", "brick"]
            },
            "ranch": {
                "features": ["single-story", "long and low profile", "open floor plan",
                             "sliding glass doors", "attached garage", "minimal exterior decoration"],
                "materials": ["brick", "wood", "stucco", "simple materials"]
            },
            "tudor": {
                "features": ["steeply pitched roof", "cross gables", "decorative half-timbering",
                             "tall narrow windows", "massive chimneys", "asymmetrical design"],
                "materials": ["brick", "stone", "stucco", "dark wood accents"]
            }
        }
    
    def classify_architectural_style(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Classify the architectural style of a building in an image
        
        Args:
            image_bytes: Image data in bytes
            
        Returns:
            Dictionary with classification results
        """
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Prompt for architectural style analysis
        prompt = """
        As an architectural expert, analyze this building image. Identify the architectural style, 
        key design features, materials used, and approximate construction period.
        
        Respond with a structured JSON object containing:
        1. Primary architectural style
        2. Confidence score (0-1)
        3. Secondary influences (if any)
        4. Key architectural features visible
        5. Primary building materials
        6. Distinctive elements
        7. Approximate construction period
        8. Design efficiency observations
        
        Structure the response as valid JSON only.
        """
        
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
                max_tokens=600
            )
            
            # Extract content
            content = response.choices[0].message.content
            
            # Extract JSON 
            json_match = re.search(r'\{.*\}', content, re.DOTALL | re.MULTILINE)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    
                    # Enhance result with additional style information
                    primary_style = result.get("primary_architectural_style", "").lower().replace(" ", "_")
                    if primary_style in self.styles:
                        result["style_reference"] = self.styles[primary_style]
                    
                    return {
                        "status": "success",
                        "classification": result
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "message": "Could not parse JSON from response"
                    }
            
            return {
                "status": "error",
                "message": "No valid classification found in response"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def compare_architectural_styles(self, image_bytes1: bytes, image_bytes2: bytes) -> Dict[str, Any]:
        """
        Compare architectural styles between two buildings
        
        Args:
            image_bytes1: First image data in bytes
            image_bytes2: Second image data in bytes
            
        Returns:
            Dictionary with comparison results
        """
        # Get classifications for both images
        result1 = self.classify_architectural_style(image_bytes1)
        result2 = self.classify_architectural_style(image_bytes2)
        
        if result1["status"] == "error" or result2["status"] == "error":
            return {
                "status": "error",
                "message": "Error classifying one or both images"
            }
        
        # Compare styles
        style1 = result1["classification"]["primary_architectural_style"]
        style2 = result2["classification"]["primary_architectural_style"]
        
        # Calculate similarity score
        similarity_score = self._calculate_style_similarity(
            result1["classification"],
            result2["classification"]
        )
        
        # Prepare comparison result
        comparison = {
            "building1_style": style1,
            "building2_style": style2,
            "similarity_score": similarity_score,
            "shared_features": self._find_shared_features(
                result1["classification"]["key_architectural_features"],
                result2["classification"]["key_architectural_features"]
            ),
            "shared_materials": self._find_shared_features(
                result1["classification"]["primary_building_materials"],
                result2["classification"]["primary_building_materials"]
            ),
            "style_compatibility": self._assess_compatibility(similarity_score),
            "period_difference": self._calculate_period_difference(
                result1["classification"]["approximate_construction_period"],
                result2["classification"]["approximate_construction_period"]
            )
        }
        
        return {
            "status": "success",
            "comparison": comparison,
            "building1": result1["classification"],
            "building2": result2["classification"]
        }
    
    def _calculate_style_similarity(self, style1: Dict[str, Any], style2: Dict[str, Any]) -> float:
        """Calculate similarity score between two architectural styles"""
        # Start with base score
        score = 0.0
        
        # Same primary style
        if style1["primary_architectural_style"].lower() == style2["primary_architectural_style"].lower():
            score += 0.5
        
        # Check for similar features
        features1 = style1["key_architectural_features"]
        features2 = style2["key_architectural_features"]
        
        if isinstance(features1, list) and isinstance(features2, list):
            shared_features = self._find_shared_features(features1, features2)
            feature_score = len(shared_features) / max(len(features1), len(features2))
            score += feature_score * 0.3
        
        # Check for similar materials
        materials1 = style1["primary_building_materials"]
        materials2 = style2["primary_building_materials"]
        
        if isinstance(materials1, list) and isinstance(materials2, list):
            shared_materials = self._find_shared_features(materials1, materials2)
            material_score = len(shared_materials) / max(len(materials1), len(materials2))
            score += material_score * 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _find_shared_features(self, list1: List[str], list2: List[str]) -> List[str]:
        """Find shared features between two lists"""
        if not isinstance(list1, list) or not isinstance(list2, list):
            return []
        
        # Normalize items for comparison
        norm_list1 = [str(item).lower().strip() for item in list1]
        norm_list2 = [str(item).lower().strip() for item in list2]
        
        # Find shared items
        shared = []
        for item1 in norm_list1:
            for item2 in norm_list2:
                if item1 == item2 or item1 in item2 or item2 in item1:
                    shared.append(item1)
                    break
        
        return shared
    
    def _assess_compatibility(self, similarity_score: float) -> str:
        """Assess compatibility based on similarity score"""
        if similarity_score >= 0.8:
            return "Highly compatible styles"
        elif similarity_score >= 0.6:
            return "Compatible styles with complementary elements"
        elif similarity_score >= 0.4:
            return "Moderately compatible with notable differences"
        elif similarity_score >= 0.2:
            return "Limited compatibility, significant contrasts"
        else:
            return "Contrasting styles with minimal compatibility"
    
    def _calculate_period_difference(self, period1: str, period2: str) -> Optional[str]:
        """Calculate the difference between construction periods"""
        try:
            # Extract years from period strings
            import re
            
            years1 = re.findall(r'(\d{4})', period1)
            years2 = re.findall(r'(\d{4})', period2)
            
            if not years1 or not years2:
                return "Unable to determine period difference"
            
            # Use the first year found in each
            year1 = int(years1[0])
            year2 = int(years2[0])
            
            diff = abs(year1 - year2)
            
            if diff < 10:
                return "Contemporary periods (less than 10 years apart)"
            elif diff < 25:
                return f"Close periods ({diff} years apart)"
            elif diff < 50:
                return f"Moderately separated periods ({diff} years apart)"
            elif diff < 100:
                return f"Distinctly different periods ({diff} years apart)"
            else:
                return f"Historically distant periods ({diff} years apart)"
            
        except Exception:
            return "Unable to determine period difference"
    
    def generate_style_guidelines(self, style_name: str) -> Dict[str, Any]:
        """
        Generate detailed architectural style guidelines
        
        Args:
            style_name: Name of architectural style
            
        Returns:
            Dictionary with style guidelines
        """
        # Normalize style name
        norm_style = style_name.lower().replace(" ", "_")
        
        # Check if style exists in our database
        if norm_style in self.styles:
            base_info = self.styles[norm_style]
        else:
            base_info = {}
        
        # Prepare prompt
        prompt = f"""
        Generate detailed architectural design guidelines for the {style_name} style.
        Include:
        
        1. Key defining characteristics
        2. Typical proportions and measurements
        3. Common materials and finishes
        4. Color palettes
        5. Window and door treatments
        6. Roofing details
        7. Interior design elements
        8. Landscaping recommendations
        9. Modern adaptations while preserving style integrity
        10. Regional variations
        
        Structure the response as a detailed JSON object only.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            
            # Extract content
            content = response.choices[0].message.content
            
            # Extract JSON 
            json_match = re.search(r'\{.*\}', content, re.DOTALL | re.MULTILINE)
            if json_match:
                try:
                    guidelines = json.loads(json_match.group(0))
                    
                    # Merge with our database information if available
                    if base_info:
                        if "features" in base_info and "key_defining_characteristics" not in guidelines:
                            guidelines["key_defining_characteristics"] = base_info["features"]
                        
                        if "materials" in base_info and "common_materials" not in guidelines:
                            guidelines["common_materials"] = base_info["materials"]
                    
                    return {
                        "status": "success",
                        "style_name": style_name,
                        "guidelines": guidelines
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "message": "Could not parse JSON from response"
                    }
            
            return {
                "status": "error",
                "message": "No valid guidelines found in response"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }