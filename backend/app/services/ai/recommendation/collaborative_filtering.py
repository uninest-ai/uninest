import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import logging

from app.models import User, Property, UserPreference, TenantProfile, Interaction

logger = logging.getLogger(__name__)

class CollaborativeFilteringEngine:
    """
    Advanced collaborative filtering recommendation engine
    Combines user-based and item-based collaborative filtering with content features
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_preference_matrix = None
        self.user_similarity_matrix = None
        self.property_feature_matrix = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')

    def build_user_preference_matrix(self) -> pd.DataFrame:
        """
        Build user-preference matrix with TF-IDF weighting
        Returns: DataFrame with users as rows, preference features as columns
        """
        logger.info("Building user preference matrix...")

        # Get all user preferences
        preferences = self.db.query(UserPreference).all()

        if not preferences:
            logger.warning("No user preferences found")
            return pd.DataFrame()

        # Create preference documents for each user
        user_docs = defaultdict(list)
        for pref in preferences:
            # Create weighted preference text based on source and category
            weight = self._get_preference_weight(pref.source, pref.preference_category)

            # Repeat preference text based on weight for TF-IDF
            weighted_text = f"{pref.preference_key}_{pref.preference_value} " * weight
            user_docs[pref.user_id].append(weighted_text)

        # Combine preferences into documents
        user_preference_docs = {}
        for user_id, prefs in user_docs.items():
            user_preference_docs[user_id] = " ".join(prefs)

        if not user_preference_docs:
            return pd.DataFrame()

        # Create TF-IDF matrix
        user_ids = list(user_preference_docs.keys())
        docs = [user_preference_docs[uid] for uid in user_ids]

        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(docs)

            # Convert to DataFrame
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            self.user_preference_matrix = pd.DataFrame(
                tfidf_matrix.toarray(),
                index=user_ids,
                columns=feature_names
            )

            logger.info(f"Built preference matrix: {self.user_preference_matrix.shape}")
            return self.user_preference_matrix

        except Exception as e:
            logger.error(f"Error building preference matrix: {e}")
            return pd.DataFrame()

    def _get_preference_weight(self, source: str, category: str) -> int:
        """Calculate preference weight based on source and category"""
        weight_map = {
            'chat': 3,
            'image_upload': 2,
            'manual': 4,
            'inferred': 1
        }

        category_boost = {
            'property': 1.5,
            'location': 1.3,
            'lifestyle': 1.2,
            'tenant_ideal_home': 1.4
        }

        base_weight = weight_map.get(source, 1)
        boost = category_boost.get(category, 1.0)

        return max(1, int(base_weight * boost))

    def calculate_user_similarity(self) -> np.ndarray:
        """
        Calculate user-user similarity matrix using cosine similarity
        Returns: Similarity matrix with enhanced features
        """
        if self.user_preference_matrix is None or self.user_preference_matrix.empty:
            logger.warning("No preference matrix available for similarity calculation")
            return np.array([])

        logger.info("Calculating user similarity matrix...")

        # Add demographic features
        enhanced_matrix = self._add_demographic_features()

        # Calculate cosine similarity
        self.user_similarity_matrix = cosine_similarity(enhanced_matrix)

        logger.info(f"Calculated similarity matrix: {self.user_similarity_matrix.shape}")
        return self.user_similarity_matrix

    def _add_demographic_features(self) -> np.ndarray:
        """Add demographic features to preference matrix"""
        if self.user_preference_matrix.empty:
            return np.array([])

        # Get tenant profiles for demographic data
        user_ids = self.user_preference_matrix.index.tolist()
        profiles = self.db.query(TenantProfile).filter(
            TenantProfile.user_id.in_(user_ids)
        ).all()

        # Create demographic feature matrix
        demographic_features = []

        for user_id in user_ids:
            profile = next((p for p in profiles if p.user_id == user_id), None)

            if profile:
                # Normalize budget (scale to 0-1)
                budget_norm = min(1.0, (profile.budget or 0) / 5000.0) if profile.budget else 0

                # Location encoding (simple hash-based)
                location_feat = hash(profile.preferred_location or "") % 100 / 100.0

                features = [budget_norm, location_feat]
            else:
                features = [0.0, 0.0]

            demographic_features.append(features)

        # Combine preference and demographic features
        demographic_array = np.array(demographic_features)
        preference_array = self.user_preference_matrix.values

        # Weight demographic features less than preferences
        demographic_weight = 0.3
        preference_weight = 0.7

        enhanced_matrix = np.hstack([
            preference_array * preference_weight,
            demographic_array * demographic_weight
        ])

        return enhanced_matrix

    def predict_property_rating(self, user_id: int, property_id: int, k: int = 10) -> float:
        """
        Predict user rating for a property using collaborative filtering

        Args:
            user_id: Target user ID
            property_id: Target property ID
            k: Number of similar users to consider

        Returns:
            Predicted rating (0-1 scale)
        """
        if (self.user_similarity_matrix is None or
            self.user_preference_matrix is None or
            self.user_preference_matrix.empty):
            return 0.5  # Default neutral rating

        try:
            # Find user index in matrix
            if user_id not in self.user_preference_matrix.index:
                return self._content_based_fallback(user_id, property_id)

            user_idx = self.user_preference_matrix.index.get_loc(user_id)

            # Get user similarities
            user_similarities = self.user_similarity_matrix[user_idx]

            # Get property interactions from similar users
            property_interactions = self._get_property_interactions(property_id)

            if not property_interactions:
                return self._content_based_fallback(user_id, property_id)

            # Find k most similar users who interacted with this property
            similar_users = []
            for other_user_id, interaction_score in property_interactions.items():
                if other_user_id == user_id:
                    continue

                if other_user_id in self.user_preference_matrix.index:
                    other_idx = self.user_preference_matrix.index.get_loc(other_user_id)
                    similarity = user_similarities[other_idx]

                    similar_users.append((similarity, interaction_score))

            # Sort by similarity and take top k
            similar_users.sort(key=lambda x: x[0], reverse=True)
            top_similar = similar_users[:k]

            if not top_similar:
                return self._content_based_fallback(user_id, property_id)

            # Calculate weighted average rating
            total_similarity = sum(sim for sim, _ in top_similar)
            if total_similarity == 0:
                return 0.5

            weighted_rating = sum(sim * rating for sim, rating in top_similar) / total_similarity

            # Normalize to 0-1 scale
            return max(0.0, min(1.0, weighted_rating))

        except Exception as e:
            logger.error(f"Error predicting rating for user {user_id}, property {property_id}: {e}")
            return 0.5

    def _get_property_interactions(self, property_id: int) -> Dict[int, float]:
        """Get user interactions with a specific property"""
        try:
            # Check if Interaction table exists and get interactions
            interactions = self.db.query(Interaction).filter(
                Interaction.property_id == property_id
            ).all()

            interaction_scores = {}
            for interaction in interactions:
                # Convert interaction type to score
                score = self._interaction_to_score(interaction.action)

                # Accumulate scores for users with multiple interactions
                if interaction.user_id in interaction_scores:
                    interaction_scores[interaction.user_id] = max(
                        interaction_scores[interaction.user_id], score
                    )
                else:
                    interaction_scores[interaction.user_id] = score

            return interaction_scores

        except Exception as e:
            logger.warning(f"Could not get interactions for property {property_id}: {e}")
            return {}

    def _interaction_to_score(self, action: str) -> float:
        """Convert interaction action to numerical score"""
        action_scores = {
            'view': 0.3,
            'click': 0.5,
            'like': 0.8,
            'share': 0.9,
            'comment': 0.7,
            'contact': 1.0
        }
        return action_scores.get(action.lower(), 0.3)

    def _content_based_fallback(self, user_id: int, property_id: int) -> float:
        """Fallback to content-based rating when collaborative filtering fails"""
        try:
            # Get user preferences
            user_prefs = self.db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).all()

            # Get property details
            property_obj = self.db.query(Property).filter(
                Property.id == property_id
            ).first()

            if not property_obj or not user_prefs:
                return 0.5

            # Simple content matching
            match_score = 0.0
            total_prefs = len(user_prefs)

            for pref in user_prefs:
                if self._matches_property(pref, property_obj):
                    match_score += 1.0

            return match_score / total_prefs if total_prefs > 0 else 0.5

        except Exception as e:
            logger.error(f"Content-based fallback error: {e}")
            return 0.5

    def _matches_property(self, preference: UserPreference, property_obj: Property) -> bool:
        """Check if a preference matches a property feature"""
        pref_key = preference.preference_key.lower()
        pref_value = preference.preference_value.lower()

        # Property type matching
        if pref_key == 'property_type' and property_obj.property_type:
            return pref_value in property_obj.property_type.lower()

        # Bedroom matching
        if pref_key == 'bedrooms' and property_obj.bedrooms:
            try:
                return int(pref_value) == property_obj.bedrooms
            except ValueError:
                return False

        # Location matching
        if pref_key in ['location', 'city', 'neighborhood']:
            if property_obj.city and pref_value in property_obj.city.lower():
                return True
            if property_obj.address and pref_value in property_obj.address.lower():
                return True

        return False

    def get_user_recommendations(self, user_id: int, limit: int = 10) -> List[Tuple[int, float]]:
        """
        Get property recommendations for a user using collaborative filtering

        Args:
            user_id: Target user ID
            limit: Maximum number of recommendations

        Returns:
            List of (property_id, predicted_rating) tuples
        """
        try:
            # Get all active properties
            properties = self.db.query(Property).filter(
                Property.is_active == True
            ).all()

            if not properties:
                return []

            # Predict ratings for all properties
            predictions = []
            for prop in properties:
                rating = self.predict_property_rating(user_id, prop.id)
                predictions.append((prop.id, rating))

            # Sort by predicted rating and return top recommendations
            predictions.sort(key=lambda x: x[1], reverse=True)
            return predictions[:limit]

        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {e}")
            return []

    def update_model(self):
        """Update the collaborative filtering model with new data"""
        logger.info("Updating collaborative filtering model...")
        self.build_user_preference_matrix()
        if not self.user_preference_matrix.empty:
            self.calculate_user_similarity()
        logger.info("Model update completed")