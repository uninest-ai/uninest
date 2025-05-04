# app/services/ml_data_pipeline.py
from typing import List, Dict, Any, Optional, Tuple
import json
import os
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.models import Property, PropertyImage, User, UserPreference
from app.config import settings

class MLDataPipelineService:
    """Service for preparing architectural data for machine learning pipelines"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_path = os.path.join(os.getcwd(), "app/data")
        os.makedirs(self.data_path, exist_ok=True)
    
    def extract_property_features_dataset(self) -> pd.DataFrame:
        """
        Extract property features for ML model training
        
        Returns:
            DataFrame with property features
        """
        properties = self.db.query(Property).all()
        
        data = []
        for prop in properties:
            # Extract basic property data
            property_data = {
                "id": prop.id,
                "price": prop.price,
                "property_type": prop.property_type,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "area": prop.area,
                "latitude": prop.latitude,
                "longitude": prop.longitude,
                "city": prop.city
            }
            
            # Extract architectural features from labels
            if prop.labels:
                for label in prop.labels:
                    # Flatten architectural features
                    if isinstance(label, dict):
                        if label.get("type") == "primary_attribute":
                            property_data[f"feature_{label.get('name')}"] = label.get('value')
                        else:
                            property_data[f"has_{label.get('name', '')}"] = 1
            
            data.append(property_data)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save dataset for ML use
        df.to_csv(os.path.join(self.data_path, "property_features.csv"), index=False)
        
        return df
    
    def prepare_floor_plan_training_data(self, labeled_data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, str]:
        """
        Prepare floor plan annotations for ML model training
        
        Args:
            labeled_data: List of labeled floor plan data with annotations
            
        Returns:
            DataFrame with prepared data and path to saved file
        """
        # Structure expected in labeled_data:
        # [{
        #   "image_id": "123",
        #   "floor_plan_image_url": "https://...",
        #   "annotations": {
        #     "rooms": [{"type": "bedroom", "coordinates": [...]}],
        #     "walls": [...],
        #     "doors": [...],
        #     "windows": [...]
        #   }
        # }]
        
        # Prepare for ML model training
        flattened_data = []
        
        for item in labeled_data:
            base_item = {
                "image_id": item.get("image_id"),
                "image_url": item.get("floor_plan_image_url"),
                "total_rooms": len(item.get("annotations", {}).get("rooms", [])),
                "total_doors": len(item.get("annotations", {}).get("doors", [])),
                "total_windows": len(item.get("annotations", {}).get("windows", [])),
                "has_bedroom": 0,
                "has_bathroom": 0,
                "has_kitchen": 0,
                "has_living_room": 0
            }
            
            # Count room types
            for room in item.get("annotations", {}).get("rooms", []):
                room_type = room.get("type", "").lower()
                if "bedroom" in room_type:
                    base_item["has_bedroom"] = 1
                if "bathroom" in room_type or "bath" == room_type:
                    base_item["has_bathroom"] = 1
                if "kitchen" in room_type:
                    base_item["has_kitchen"] = 1
                if "living" in room_type or "family room" in room_type:
                    base_item["has_living_room"] = 1
            
            flattened_data.append(base_item)
        
        # Convert to DataFrame
        df = pd.DataFrame(flattened_data)
        
        # Save for ML pipeline
        file_path = os.path.join(self.data_path, "floor_plan_annotations.csv")
        df.to_csv(file_path, index=False)
        
        # Also save full JSON annotations for detailed ML training
        with open(os.path.join(self.data_path, "floor_plan_full_annotations.json"), "w") as f:
            json.dump(labeled_data, f)
        
        return df, file_path
    
    def generate_architectural_feature_vectors(self) -> np.ndarray:
        """
        Generate feature vectors for architectural style classification
        
        Returns:
            NumPy array of feature vectors
        """
        properties = self.db.query(Property).all()
        
        # Extract architectural style features
        feature_vectors = []
        property_ids = []
        
        for prop in properties:
            # Initialize empty feature vector
            # Features: [property_type, bedrooms, bathrooms, has_modern, has_traditional, etc.]
            feature_vector = [0] * 20  # Placeholder size
            
            # Basic numeric features
            feature_vector[0] = self._encode_property_type(prop.property_type)
            feature_vector[1] = prop.bedrooms if prop.bedrooms else 0
            feature_vector[2] = prop.bathrooms if prop.bathrooms else 0
            
            # Extract architectural styles from labels
            if prop.labels:
                for label in prop.labels:
                    if isinstance(label, dict) and label.get("name") == "architectural_style":
                        style = label.get("value", "").lower()
                        # Encode architectural style
                        if "modern" in style:
                            feature_vector[3] = 1
                        if "traditional" in style:
                            feature_vector[4] = 1
                        if "colonial" in style:
                            feature_vector[5] = 1
                        # Add more style encodings
            
            feature_vectors.append(feature_vector)
            property_ids.append(prop.id)
        
        # Convert to NumPy array
        feature_array = np.array(feature_vectors)
        
        # Save for ML use
        np.save(os.path.join(self.data_path, "architectural_features.npy"), feature_array)
        with open(os.path.join(self.data_path, "property_ids.json"), "w") as f:
            json.dump(property_ids, f)
        
        return feature_array
    
    def extract_user_preferences_dataset(self) -> pd.DataFrame:
        """
        Extract user preferences for recommendation model training
        
        Returns:
            DataFrame with user preferences
        """
        preferences = self.db.query(UserPreference).all()
        
        data = []
        for pref in preferences:
            pref_data = {
                "user_id": pref.user_id,
                "preference_key": pref.preference_key,
                "preference_value": pref.preference_value,
                "preference_category": pref.preference_category,
                "source": pref.source
            }
            data.append(pref_data)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save dataset
        df.to_csv(os.path.join(self.data_path, "user_preferences.csv"), index=False)
        
        return df
    
    def _encode_property_type(self, property_type: Optional[str]) -> int:
        """Helper to encode property types as integers"""
        if not property_type:
            return 0
            
        property_type = property_type.lower()
        if "apartment" in property_type:
            return 1
        elif "house" in property_type:
            return 2
        elif "condo" in property_type:
            return 3
        elif "townhouse" in property_type:
            return 4
        else:
            return 0  # Unknown
    
    def audit_training_data(self) -> Dict[str, Any]:
        """
        Audit training data for quality and completeness
        
        Returns:
            Audit report with statistics and quality metrics
        """
        # Check property features
        property_file = os.path.join(self.data_path, "property_features.csv")
        property_features = pd.read_csv(property_file) if os.path.exists(property_file) else None
        
        # Check floor plan annotations
        floor_plan_file = os.path.join(self.data_path, "floor_plan_annotations.csv")
        floor_plan_data = pd.read_csv(floor_plan_file) if os.path.exists(floor_plan_file) else None
        
        # Check user preferences
        preferences_file = os.path.join(self.data_path, "user_preferences.csv")
        preferences_data = pd.read_csv(preferences_file) if os.path.exists(preferences_file) else None
        
        # Generate audit report
        report = {
            "property_features": {
                "exists": property_features is not None,
                "record_count": len(property_features) if property_features is not None else 0,
                "completeness": self._calculate_completeness(property_features) if property_features is not None else 0,
                "missing_values": self._count_missing_values(property_features) if property_features is not None else {}
            },
            "floor_plan_annotations": {
                "exists": floor_plan_data is not None,
                "record_count": len(floor_plan_data) if floor_plan_data is not None else 0,
                "completeness": self._calculate_completeness(floor_plan_data) if floor_plan_data is not None else 0
            },
            "user_preferences": {
                "exists": preferences_data is not None,
                "record_count": len(preferences_data) if preferences_data is not None else 0,
                "category_distribution": self._calculate_category_distribution(preferences_data) if preferences_data is not None else {}
            }
        }
        
        return report
    
    def _calculate_completeness(self, df: Optional[pd.DataFrame]) -> float:
        """Calculate data completeness score"""
        if df is None or len(df) == 0:
            return 0.0
            
        # Calculate percentage of non-null values
        return (1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
    
    def _count_missing_values(self, df: Optional[pd.DataFrame]) -> Dict[str, int]:
        """Count missing values by column"""
        if df is None:
            return {}
            
        return df.isnull().sum().to_dict()
    
    def _calculate_category_distribution(self, df: Optional[pd.DataFrame]) -> Dict[str, int]:
        """Calculate distribution of preference categories"""
        if df is None or 'preference_category' not in df.columns:
            return {}
            
        return df['preference_category'].value_counts().to_dict()