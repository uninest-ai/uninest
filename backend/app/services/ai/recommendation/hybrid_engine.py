import numpy as np
from typing import List, Tuple, Dict, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta, timezone

from app.models import User, Property, UserPreference, TenantProfile, Interaction
from .collaborative_filtering import CollaborativeFilteringEngine
from .ml_predictor import MLPreferencePredictor

logger = logging.getLogger(__name__)

class HybridRecommendationEngine:
    """
    Hybrid recommendation system combining:
    1. Collaborative Filtering
    2. Content-Based Filtering
    3. ML-based Preference Prediction
    4. Real-time Learning and Adaptation
    """

    def __init__(self, db: Session):
        self.db = db
        self.collaborative_engine = CollaborativeFilteringEngine(db)
        self.ml_predictor = MLPreferencePredictor(db)

        # Adaptive weights for different algorithms
        self.algorithm_weights = {
            'collaborative': 0.4,
            'content_based': 0.3,
            'ml_predicted': 0.2,
            'popularity': 0.1
        }

        # Performance tracking
        self.performance_history = {}
        self.last_model_update = None

    def initialize_models(self):
        """Initialize and train all recommendation models"""
        logger.info("Initializing hybrid recommendation engine...")

        try:
            # Build collaborative filtering matrices
            self.collaborative_engine.build_user_preference_matrix()
            self.collaborative_engine.calculate_user_similarity()

            # Train ML models
            ml_metrics = self.ml_predictor.train_models()
            logger.info(f"ML model training metrics: {ml_metrics}")

            self.last_model_update = datetime.now(timezone.utc)
            logger.info("Hybrid engine initialization completed")

        except Exception as e:
            logger.error(f"Error initializing models: {e}")

    def get_hybrid_recommendations(
        self,
        user_id: int,
        limit: int = 10,
        include_explanations: bool = False
    ) -> List[Tuple[Property, float, Optional[Dict]]]:
        """
        Generate hybrid recommendations using multiple algorithms

        Args:
            user_id: Target user ID
            limit: Maximum number of recommendations
            include_explanations: Include explanation of recommendation reasoning

        Returns:
            List of (Property, score, explanation) tuples
        """
        logger.info(f"Generating hybrid recommendations for user {user_id}")

        try:
            # Get recommendations from each algorithm
            collab_recs = self._get_collaborative_recommendations(user_id, limit * 2)
            content_recs = self._get_content_based_recommendations(user_id, limit * 2)
            ml_recs = self._get_ml_enhanced_recommendations(user_id, limit * 2)
            popularity_recs = self._get_popularity_recommendations(limit)

            # Combine and score recommendations
            combined_scores = self._combine_recommendation_scores(
                user_id, collab_recs, content_recs, ml_recs, popularity_recs
            )

            # Apply real-time learning adjustments
            adjusted_scores = self._apply_realtime_learning(user_id, combined_scores)

            # Sort and limit results
            final_recommendations = sorted(
                adjusted_scores.items(),
                key=lambda x: x[1]['final_score'],
                reverse=True
            )[:limit]

            # Format results
            results = []
            for property_id, score_data in final_recommendations:
                property_obj = self.db.query(Property).filter(Property.id == property_id).first()
                if property_obj:
                    explanation = score_data if include_explanations else None
                    results.append((property_obj, score_data['final_score'], explanation))

            logger.info(f"Generated {len(results)} hybrid recommendations")
            return results

        except Exception as e:
            logger.error(f"Error generating hybrid recommendations: {e}")
            return []

    def _get_collaborative_recommendations(self, user_id: int, limit: int) -> Dict[int, float]:
        """Get collaborative filtering recommendations"""
        try:
            recs = self.collaborative_engine.get_user_recommendations(user_id, limit)
            return {prop_id: score for prop_id, score in recs}
        except Exception as e:
            logger.warning(f"Collaborative filtering failed: {e}")
            return {}

    def _get_content_based_recommendations(self, user_id: int, limit: int) -> Dict[int, float]:
        """Get content-based recommendations using enhanced preference matching"""
        try:
            # Get user preferences
            user_prefs = self.db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).all()

            if not user_prefs:
                return {}

            # Get tenant profile
            tenant_profile = self.db.query(TenantProfile).filter(
                TenantProfile.user_id == user_id
            ).first()

            # Get all active properties
            properties = self.db.query(Property).filter(Property.is_active == True).all()

            # Score each property
            property_scores = {}
            for prop in properties:
                score = self._calculate_enhanced_content_score(prop, user_prefs, tenant_profile)
                if score > 0:
                    property_scores[prop.id] = score

            # Return top scoring properties
            sorted_props = sorted(property_scores.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_props[:limit])

        except Exception as e:
            logger.warning(f"Content-based filtering failed: {e}")
            return {}

    def _calculate_enhanced_content_score(
        self,
        property_obj: Property,
        user_prefs: List[UserPreference],
        tenant_profile: Optional[TenantProfile]
    ) -> float:
        """Calculate enhanced content-based score with preference weighting"""
        score = 0.0

        # Create preference map with weights
        pref_weights = {}
        for pref in user_prefs:
            weight = self._get_preference_weight(pref.source, pref.preference_category)
            pref_weights[pref.preference_key] = {
                'value': pref.preference_value,
                'weight': weight,
                'category': pref.preference_category
            }

        # Budget matching (high weight)
        if tenant_profile and tenant_profile.budget and property_obj.price:
            budget_ratio = min(1.0, tenant_profile.budget / property_obj.price)
            if budget_ratio >= 0.8:  # Within 20% of budget
                score += 0.25 * budget_ratio

        # Property type matching
        if 'property_type' in pref_weights and property_obj.property_type:
            if pref_weights['property_type']['value'].lower() in property_obj.property_type.lower():
                score += 0.2 * pref_weights['property_type']['weight']

        # Bedroom/bathroom matching
        for attr in ['bedrooms', 'bathrooms']:
            if attr in pref_weights and getattr(property_obj, attr):
                try:
                    pref_value = float(pref_weights[attr]['value'])
                    prop_value = float(getattr(property_obj, attr))
                    if abs(pref_value - prop_value) <= 0.5:  # Allow 0.5 difference
                        score += 0.1 * pref_weights[attr]['weight']
                except (ValueError, TypeError):
                    continue

        # Location matching
        location_keys = ['location', 'city', 'neighborhood', 'area']
        for key in location_keys:
            if key in pref_weights:
                pref_location = pref_weights[key]['value'].lower()
                if property_obj.city and pref_location in property_obj.city.lower():
                    score += 0.15 * pref_weights[key]['weight']
                elif property_obj.address and pref_location in property_obj.address.lower():
                    score += 0.1 * pref_weights[key]['weight']

        # Lifestyle and amenity matching
        lifestyle_prefs = [p for p in user_prefs if p.preference_category == 'lifestyle']
        if lifestyle_prefs and property_obj.api_amenities:
            amenities_str = str(property_obj.api_amenities).lower()
            for pref in lifestyle_prefs:
                if pref.preference_value.lower() in amenities_str:
                    weight = self._get_preference_weight(pref.source, pref.preference_category)
                    score += 0.05 * weight

        return min(1.0, score)  # Cap at 1.0

    def _get_ml_enhanced_recommendations(self, user_id: int, limit: int) -> Dict[int, float]:
        """Get ML-enhanced recommendations"""
        try:
            # Get ML predictions for user
            ml_predictions = self.ml_predictor.predict_user_preferences(user_id)

            if not ml_predictions:
                return {}

            # Use ML predictions to enhance content-based scoring
            engagement_multiplier = max(0.5, ml_predictions.get('confidence', 0.5))

            # Get base content recommendations
            content_recs = self._get_content_based_recommendations(user_id, limit)

            # Apply ML enhancement
            enhanced_recs = {}
            for prop_id, score in content_recs.items():
                enhanced_score = score * engagement_multiplier

                # Boost score based on predicted preference strength
                pred_strength = ml_predictions.get('predicted_preference_strength', 0)
                if pred_strength > 3:
                    enhanced_score *= 1.2

                enhanced_recs[prop_id] = enhanced_score

            return enhanced_recs

        except Exception as e:
            logger.warning(f"ML enhancement failed: {e}")
            return {}

    def _get_popularity_recommendations(self, limit: int) -> Dict[int, float]:
        """Get popularity-based recommendations as fallback"""
        try:
            # Calculate property popularity based on interactions
            property_popularity = {}

            # Get recent interactions (last 30 days)
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)

            try:
                recent_interactions = self.db.query(Interaction).filter(
                    Interaction.timestamp > recent_cutoff
                ).all()

                for interaction in recent_interactions:
                    prop_id = interaction.property_id
                    if prop_id not in property_popularity:
                        property_popularity[prop_id] = 0

                    # Weight different interaction types
                    action_weights = {
                        'view': 1, 'click': 2, 'like': 3, 'share': 4, 'contact': 5
                    }
                    weight = action_weights.get(interaction.action, 1)
                    property_popularity[prop_id] += weight

            except Exception:
                # Fallback to basic property scoring if Interaction table issues
                properties = self.db.query(Property).filter(Property.is_active == True).all()
                for prop in properties:
                    # Simple popularity based on recent creation and price reasonableness
                    days_old = (datetime.now(timezone.utc) - prop.created_at).days
                    freshness_score = max(0, 1 - (days_old / 365))  # Newer properties score higher

                    # Price reasonableness (properties around median price score higher)
                    price_score = 0.5  # Default neutral score
                    if prop.price:
                        # Simplified price scoring
                        if 500 <= prop.price <= 3000:  # Reasonable price range
                            price_score = 0.8

                    property_popularity[prop.id] = freshness_score * 0.6 + price_score * 0.4

            # Normalize scores
            if property_popularity:
                max_score = max(property_popularity.values())
                if max_score > 0:
                    property_popularity = {
                        prop_id: score / max_score
                        for prop_id, score in property_popularity.items()
                    }

            # Return top properties
            sorted_props = sorted(property_popularity.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_props[:limit])

        except Exception as e:
            logger.warning(f"Popularity recommendations failed: {e}")
            return {}

    def _combine_recommendation_scores(
        self,
        user_id: int,
        collab_recs: Dict[int, float],
        content_recs: Dict[int, float],
        ml_recs: Dict[int, float],
        popularity_recs: Dict[int, float]
    ) -> Dict[int, Dict]:
        """Combine scores from different algorithms"""

        all_property_ids = set()
        all_property_ids.update(collab_recs.keys())
        all_property_ids.update(content_recs.keys())
        all_property_ids.update(ml_recs.keys())
        all_property_ids.update(popularity_recs.keys())

        combined_scores = {}

        for prop_id in all_property_ids:
            scores = {
                'collaborative': collab_recs.get(prop_id, 0.0),
                'content_based': content_recs.get(prop_id, 0.0),
                'ml_predicted': ml_recs.get(prop_id, 0.0),
                'popularity': popularity_recs.get(prop_id, 0.0)
            }

            # Calculate weighted final score
            final_score = sum(
                scores[algo] * self.algorithm_weights[algo]
                for algo in scores.keys()
            )

            combined_scores[prop_id] = {
                'final_score': final_score,
                'algorithm_scores': scores,
                'algorithm_weights': self.algorithm_weights.copy()
            }

        return combined_scores

    def _apply_realtime_learning(self, user_id: int, combined_scores: Dict) -> Dict:
        """Apply real-time learning adjustments based on user feedback"""
        try:
            # Get recent user interactions for learning
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)

            try:
                recent_interactions = self.db.query(Interaction).filter(
                    Interaction.user_id == user_id,
                    Interaction.timestamp > recent_cutoff
                ).all()

                # Analyze user behavior patterns
                if recent_interactions:
                    # Properties user interacted with positively
                    positive_interactions = [
                        i for i in recent_interactions
                        if i.action in ['like', 'contact', 'share']
                    ]

                    # Properties user viewed but didn't engage with
                    viewed_only = [
                        i for i in recent_interactions
                        if i.action == 'view'
                    ]

                    # Boost similar properties to positive interactions
                    for interaction in positive_interactions:
                        prop_id = interaction.property_id
                        if prop_id in combined_scores:
                            boost_factor = 1.3 if interaction.action == 'contact' else 1.1
                            combined_scores[prop_id]['final_score'] *= boost_factor
                            combined_scores[prop_id]['realtime_boost'] = boost_factor

                    # Slightly reduce scores for properties similar to viewed-only
                    # (This indicates user saw them but wasn't interested)
                    viewed_only_ids = {i.property_id for i in viewed_only}
                    positive_ids = {i.property_id for i in positive_interactions}

                    # Only penalize if viewed but no positive interaction
                    penalize_ids = viewed_only_ids - positive_ids
                    for prop_id in penalize_ids:
                        if prop_id in combined_scores:
                            combined_scores[prop_id]['final_score'] *= 0.9
                            combined_scores[prop_id]['realtime_penalty'] = 0.9

            except Exception:
                # If interaction tracking fails, continue without real-time adjustments
                pass

            return combined_scores

        except Exception as e:
            logger.warning(f"Real-time learning adjustment failed: {e}")
            return combined_scores

    def _get_preference_weight(self, source: str, category: str) -> float:
        """Get normalized preference weight (0-1 scale)"""
        weight_map = {
            'chat': 0.8,
            'image_upload': 0.6,
            'manual': 1.0,
            'inferred': 0.4
        }

        category_boost = {
            'property': 1.0,
            'location': 0.9,
            'lifestyle': 0.7,
            'tenant_ideal_home': 0.8
        }

        base_weight = weight_map.get(source, 0.5)
        boost = category_boost.get(category, 0.7)

        return min(1.0, base_weight * boost)

    def update_algorithm_weights(self, performance_feedback: Dict[str, float]):
        """Update algorithm weights based on performance feedback"""
        try:
            # Simple adaptive weight adjustment
            total_performance = sum(performance_feedback.values())

            if total_performance > 0:
                for algo in self.algorithm_weights:
                    if algo in performance_feedback:
                        # Adjust weight based on relative performance
                        relative_performance = performance_feedback[algo] / total_performance

                        # Small adjustment to prevent drastic changes
                        adjustment = (relative_performance - 0.25) * 0.1  # 0.25 = 1/4 algorithms

                        # Update weight with bounds
                        new_weight = self.algorithm_weights[algo] + adjustment
                        self.algorithm_weights[algo] = max(0.1, min(0.6, new_weight))

                # Normalize weights to sum to 1
                total_weight = sum(self.algorithm_weights.values())
                for algo in self.algorithm_weights:
                    self.algorithm_weights[algo] /= total_weight

                logger.info(f"Updated algorithm weights: {self.algorithm_weights}")

        except Exception as e:
            logger.error(f"Error updating algorithm weights: {e}")

    def should_retrain_models(self) -> bool:
        """Check if models should be retrained based on data freshness"""
        if self.last_model_update is None:
            return True

        # Retrain weekly or if significant new data
        days_since_update = (datetime.now(timezone.utc) - self.last_model_update).days

        if days_since_update >= 7:
            return True

        # Check for significant new preference data
        try:
            recent_prefs = self.db.query(UserPreference).filter(
                UserPreference.created_at > self.last_model_update
            ).count()

            if recent_prefs > 50:  # Significant new data threshold
                return True

        except Exception:
            pass

        return False