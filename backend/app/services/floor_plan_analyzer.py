# app/services/floor_plan_analyzer.py
import base64
import json
import re
from typing import Dict, Any, List
from openai import OpenAI
from app.config import settings
from scipy import ndimage
import cv2
import numpy as np
import os

class FloorPlanAnalysisService:
    """Service for analyzing floor plan images using basic computer vision"""
    
    def __init__(self):
        # No need for model initialization anymore
        pass
        
    def analyze_floor_plan(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze a floor plan image using basic computer vision
        
        Args:
            image_bytes: Floor plan image data in bytes
            
        Returns:
            Dictionary containing extracted architectural features
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area to identify rooms
            min_area = 1000  # Minimum area to be considered a room
            rooms = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
            
            # Calculate room areas
            room_areas = [cv2.contourArea(room) for room in rooms]
            
            # Calculate approximate square footage
            # Assuming we know the scale of the floor plan (e.g., pixels per foot)
            pixels_per_foot = 10  # This would need calibration
            total_sq_footage = sum(room_areas) / (pixels_per_foot ** 2)
            
            # Calculate basic metrics
            aspect_ratios = [self._calculate_aspect_ratio(room) for room in rooms]
            avg_aspect_ratio = sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 0
            
            return {
                "status": "success",
                "analysis": {
                    "total_square_footage": round(total_sq_footage, 2),
                    "room_count": len(rooms),
                    "room_areas": [round(area / (pixels_per_foot ** 2), 2) for area in room_areas],
                    "average_room_size": round(total_sq_footage / len(rooms), 2) if rooms else 0,
                    "average_aspect_ratio": round(avg_aspect_ratio, 2),
                    "layout_efficiency_score": self._calculate_basic_efficiency_score(rooms, room_areas),
                    "natural_light_potential": self._analyze_basic_light_potential(rooms, img.shape)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _calculate_aspect_ratio(self, contour):
        """Calculate aspect ratio of a room"""
        x, y, w, h = cv2.boundingRect(contour)
        return w / h if h != 0 else 0
    
    def _calculate_basic_efficiency_score(self, rooms, room_areas):
        """Calculate a basic efficiency score based on room sizes and shapes"""
        if not rooms:
            return 0
            
        # Simple scoring based on room size distribution
        avg_area = sum(room_areas) / len(room_areas)
        size_variance = sum((area - avg_area) ** 2 for area in room_areas) / len(room_areas)
        
        # Normalize score between 0 and 100
        score = 100 * (1 / (1 + size_variance / (avg_area ** 2)))
        return round(score, 2)
    
    def _analyze_basic_light_potential(self, rooms, img_shape):
        """Analyze basic natural light potential based on room positions"""
        if not rooms:
            return 0
            
        # Simple scoring based on room positions relative to image edges
        # Assuming rooms closer to edges have better light potential
        scores = []
        for room in rooms:
            x, y, w, h = cv2.boundingRect(room)
            # Calculate distance to nearest edge
            dist_to_edge = min(x, y, img_shape[1] - (x + w), img_shape[0] - (y + h))
            # Normalize score (closer to edge = higher score)
            score = 100 * (1 - dist_to_edge / max(img_shape))
            scores.append(score)
            
        return round(sum(scores) / len(scores), 2)
    
    def generate_optimization_suggestions(self, floor_plan_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate architectural optimization suggestions based on floor plan analysis
        
        Args:
            floor_plan_analysis: Analysis results from analyze_floor_plan
            
        Returns:
            List of optimization suggestions with confidence scores
        """
        # Convert analysis to string for prompt
        analysis_str = json.dumps(floor_plan_analysis)
        
        prompt = f"""
        Based on this floor plan analysis:
        {analysis_str}
        
        Generate optimization suggestions to improve:
        1. Space efficiency
        2. Natural light
        3. Traffic flow
        4. Construction cost efficiency
        5. Energy efficiency
        
        For each suggestion, provide:
        - A detailed description
        - Implementation difficulty (1-5)
        - Potential impact score (1-5)
        - Estimated cost impact (%, + for increase, - for savings)
        
        Return as a structured JSON list of suggestions.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON 
            json_match = re.search(r'\[.*\]', content, re.DOTALL | re.MULTILINE)
            if json_match:
                try:
                    suggestions = json.loads(json_match.group(0))
                    return suggestions
                except json.JSONDecodeError:
                    return []
            return []
            
        except Exception:
            return []
    
    def analyze_construction_materials(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze construction materials visible in property images
        
        Args:
            image_bytes: Image data in bytes
            
        Returns:
            Dictionary containing identified materials and sustainability metrics
        """
        # Implementation similar to other methods
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """
        Analyze this property image and identify construction materials.
        For each material, provide:
        1. Material type
        2. Estimated cost tier (low, medium, high)
        3. Sustainability score (1-10)
        4. Durability rating (1-10)
        5. Maintenance requirements
        
        Return as structured JSON.
        """
        
        # Implementation would continue similar to analyze_floor_plan
        # For brevity, returning placeholder
        return {
            "status": "success",
            "materials": [
                {
                    "type": "Example material",
                    "cost_tier": "medium",
                    "sustainability": 7,
                    "durability": 8,
                    "maintenance": "Low maintenance, periodic sealing"
                }
            ]
        }
        
# -----
'''
# app/services/floor_plan_analyzer.py
import base64
import json
import re
from typing import Dict, Any, List
from openai import OpenAI
from app.config import settings
from scipy import ndimage
import cv2
import numpy as np
import torch
from transformers import SegformerFeatureExtractor, SegformerForSemanticSegmentation
import os

class FloorPlanAnalysisService:
    """Service for analyzing floor plan images using specialized computer vision models"""
    
    def __init__(self):
        # Load specialized floor plan segmentation model
        self.feature_extractor = SegformerFeatureExtractor.from_pretrained(
            "nvidia/segformer-b0-finetuned-floorplans",
            use_auth_token=os.getenv("HUGGINGFACE_TOKEN")
        )
        self.model = SegformerForSemanticSegmentation.from_pretrained("nvidia/segformer-b0-finetuned-floorplans")
        
    def analyze_floor_plan(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze a floor plan image using specialized computer vision
        
        Args:
            image_bytes: Floor plan image data in bytes
            
        Returns:
            Dictionary containing extracted architectural features
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Preprocess image
            inputs = self.feature_extractor(images=img, return_tensors="pt")
            
            # Get segmentation predictions
            outputs = self.model(**inputs)
            logits = outputs.logits
            
            # Process segmentation results
            predicted_mask = logits.argmax(dim=1).squeeze().cpu().numpy()
            
            # Extract room information (room count, types, sizes)
            labeled_mask, num_rooms = ndimage.label(predicted_mask == 1)  # Assuming 1 is the label for rooms
            room_sizes = ndimage.sum(np.ones_like(labeled_mask), labeled_mask, range(1, num_rooms + 1))
            
            # Calculate approximate square footage
            # Assuming we know the scale of the floor plan (e.g., pixels per foot)
            pixels_per_foot = 10  # This would need calibration
            total_sq_footage = sum(room_sizes) / (pixels_per_foot ** 2)
            
            # Analyze room adjacency and traffic flow
            # This would involve analyzing the relationships between segmented rooms
            
            return {
                "status": "success",
                "analysis": {
                    "total_square_footage": round(total_sq_footage, 2),
                    "room_count": num_rooms,
                    "room_sizes": room_sizes.tolist(),
                    "layout_efficiency_score": self._calculate_efficiency_score(labeled_mask, room_sizes),
                    "traffic_flow": self._analyze_traffic_flow(labeled_mask),
                    "natural_light_potential": self._analyze_natural_light(labeled_mask)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_optimization_suggestions(self, floor_plan_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate architectural optimization suggestions based on floor plan analysis
        
        Args:
            floor_plan_analysis: Analysis results from analyze_floor_plan
            
        Returns:
            List of optimization suggestions with confidence scores
        """
        # Convert analysis to string for prompt
        analysis_str = json.dumps(floor_plan_analysis)
        
        prompt = f"""
        Based on this floor plan analysis:
        {analysis_str}
        
        Generate optimization suggestions to improve:
        1. Space efficiency
        2. Natural light
        3. Traffic flow
        4. Construction cost efficiency
        5. Energy efficiency
        
        For each suggestion, provide:
        - A detailed description
        - Implementation difficulty (1-5)
        - Potential impact score (1-5)
        - Estimated cost impact (%, + for increase, - for savings)
        
        Return as a structured JSON list of suggestions.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON 
            json_match = re.search(r'\[.*\]', content, re.DOTALL | re.MULTILINE)
            if json_match:
                try:
                    suggestions = json.loads(json_match.group(0))
                    return suggestions
                except json.JSONDecodeError:
                    return []
            return []
            
        except Exception:
            return []
    
    def analyze_construction_materials(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze construction materials visible in property images
        
        Args:
            image_bytes: Image data in bytes
            
        Returns:
            Dictionary containing identified materials and sustainability metrics
        """
        # Implementation similar to other methods
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """
        Analyze this property image and identify construction materials.
        For each material, provide:
        1. Material type
        2. Estimated cost tier (low, medium, high)
        3. Sustainability score (1-10)
        4. Durability rating (1-10)
        5. Maintenance requirements
        
        Return as structured JSON.
        """
        
        # Implementation would continue similar to analyze_floor_plan
        # For brevity, returning placeholder
        return {
            "status": "success",
            "materials": [
                {
                    "type": "Example material",
                    "cost_tier": "medium",
                    "sustainability": 7,
                    "durability": 8,
                    "maintenance": "Low maintenance, periodic sealing"
                }
            ]
        }
        
'''