import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error
import joblib
import os
import logging
from datetime import datetime, timedelta, timezone

from app.models import User, Property, UserPreference, TenantProfile, Interaction

logger = logging.getLogger(__name__)

class MLPreferencePredictor:
    """
    Machine Learning-based preference prediction system
    Predicts user preferences from behavioral patterns and incomplete profiles
    """

    def __init__(self, db: Session):
        self.db = db
        self.preference_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.rating_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.model_path = "backend/app/services/ai/models"
        self.is_trained = False

        # Ensure model directory exists
        os.makedirs(self.model_path, exist_ok=True)

    def extract_user_features(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Extract comprehensive user features for ML prediction

        Args:
            user_id: Target user ID

        Returns:
            Dictionary of user features
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            # Get tenant profile
            tenant_profile = self.db.query(TenantProfile).filter(
                TenantProfile.user_id == user_id
            ).first()

            # Get user preferences
            preferences = self.db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).all()

            # Get user interactions
            interactions = self.db.query(Interaction).filter(
                Interaction.user_id == user_id
            ).all()

            # Base features
            features = {
                'user_id': user_id,
                'account_age_days': (datetime.now(timezone.utc) - user.created_at).days,
                'budget': tenant_profile.budget if tenant_profile and tenant_profile.budget else 0,
                'has_location_pref': 1 if tenant_profile and tenant_profile.preferred_location else 0,
                'preference_count': len(preferences),
                'interaction_count': len(interactions)
            }

            # Preference category counts
            pref_categories = ['property', 'location', 'lifestyle', 'tenant_ideal_home']
            for category in pref_categories:
                count = sum(1 for p in preferences if p.preference_category == category)
                features[f'{category}_pref_count'] = count

            # Preference source distribution
            pref_sources = ['chat', 'image_upload', 'manual', 'inferred']
            for source in pref_sources:
                count = sum(1 for p in preferences if p.source == source)
                features[f'{source}_pref_count'] = count

            # Interaction pattern features
            if interactions:
                # Recent activity (last 7 days)
                recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
                recent_interactions = [i for i in interactions if i.timestamp > recent_cutoff]
                features['recent_interaction_count'] = len(recent_interactions)

                # Interaction type distribution
                interaction_types = ['view', 'click', 'like', 'share', 'comment', 'contact']
                for int_type in interaction_types:
                    count = sum(1 for i in interactions if i.action == int_type)
                    features[f'{int_type}_count'] = count

                # Average session features (if we have duration data)
                durations = [i.duration for i in interactions if hasattr(i, 'duration') and i.duration]
                if durations:
                    features['avg_session_duration'] = np.mean(durations)
                    features['max_session_duration'] = max(durations)
                else:
                    features['avg_session_duration'] = 0
                    features['max_session_duration'] = 0
            else:
                # No interactions - set defaults
                for key in ['recent_interaction_count', 'avg_session_duration', 'max_session_duration']:
                    features[key] = 0
                for int_type in ['view', 'click', 'like', 'share', 'comment', 'contact']:
                    features[f'{int_type}_count'] = 0

            # Property viewing patterns
            viewed_properties = self.db.query(Property).join(Interaction).filter(
                Interaction.user_id == user_id,
                Interaction.action == 'view'
            ).all()

            if viewed_properties:
                # Price range analysis
                prices = [p.price for p in viewed_properties if p.price]
                if prices:
                    features['avg_viewed_price'] = np.mean(prices)
                    features['min_viewed_price'] = min(prices)
                    features['max_viewed_price'] = max(prices)
                    features['price_variance'] = np.var(prices)
                else:
                    for key in ['avg_viewed_price', 'min_viewed_price', 'max_viewed_price', 'price_variance']:
                        features[key] = 0

                # Property type preferences (inferred from views)
                property_types = [p.property_type for p in viewed_properties if p.property_type]
                if property_types:
                    type_counts = pd.Series(property_types).value_counts()
                    features['most_viewed_property_type'] = type_counts.index[0]
                    features['property_type_diversity'] = len(type_counts)
                else:
                    features['most_viewed_property_type'] = 'unknown'
                    features['property_type_diversity'] = 0

                # Bedroom preferences (inferred)
                bedrooms = [p.bedrooms for p in viewed_properties if p.bedrooms]
                if bedrooms:
                    features['avg_viewed_bedrooms'] = np.mean(bedrooms)
                    features['preferred_bedroom_count'] = max(set(bedrooms), key=bedrooms.count)
                else:
                    features['avg_viewed_bedrooms'] = 0
                    features['preferred_bedroom_count'] = 0
            else:
                # No viewed properties
                for key in ['avg_viewed_price', 'min_viewed_price', 'max_viewed_price', 'price_variance',
                           'property_type_diversity', 'avg_viewed_bedrooms', 'preferred_bedroom_count']:
                    features[key] = 0
                features['most_viewed_property_type'] = 'unknown'

            return features

        except Exception as e:
            logger.error(f"Error extracting features for user {user_id}: {e}")
            return None

    def prepare_training_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare training data for preference prediction models

        Returns:
            Tuple of (feature_df, target_df)
        """
        logger.info("Preparing ML training data...")

        # Get all users with preferences
        users_with_prefs = self.db.query(User).join(UserPreference).distinct().all()

        if not users_with_prefs:
            logger.warning("No users with preferences found for training")
            return pd.DataFrame(), pd.DataFrame()

        # Extract features for all users
        all_features = []
        all_targets = []

        for user in users_with_prefs:
            features = self.extract_user_features(user.id)
            if features is None:
                continue

            # Get user preferences as targets
            preferences = self.db.query(UserPreference).filter(
                UserPreference.user_id == user.id
            ).all()

            # Create target vectors for different prediction tasks
            targets = {
                'user_id': user.id,
                'has_property_type_pref': 0,
                'has_location_pref': 0,
                'has_budget_pref': 0,
                'has_lifestyle_pref': 0,
                'preference_strength': len(preferences),
                'engagement_level': 0  # Will be calculated based on interactions
            }

            # Analyze preference categories
            for pref in preferences:
                if pref.preference_category == 'property':
                    targets['has_property_type_pref'] = 1
                elif pref.preference_category == 'location':
                    targets['has_location_pref'] = 1
                elif pref.preference_category == 'lifestyle':
                    targets['has_lifestyle_pref'] = 1

            # Calculate engagement level
            interaction_count = features.get('interaction_count', 0)
            recent_interactions = features.get('recent_interaction_count', 0)

            if interaction_count > 10:
                targets['engagement_level'] = 3  # High
            elif interaction_count > 3:
                targets['engagement_level'] = 2  # Medium
            elif interaction_count > 0:
                targets['engagement_level'] = 1  # Low
            else:
                targets['engagement_level'] = 0  # None

            all_features.append(features)
            all_targets.append(targets)

        if not all_features:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to DataFrames
        feature_df = pd.DataFrame(all_features)
        target_df = pd.DataFrame(all_targets)

        logger.info(f"Prepared training data: {len(feature_df)} samples, {len(feature_df.columns)} features")
        return feature_df, target_df

    def preprocess_features(self, feature_df: pd.DataFrame, is_training: bool = True) -> np.ndarray:
        """
        Preprocess features for ML models

        Args:
            feature_df: Feature DataFrame
            is_training: Whether this is training data (affects fitting of scalers)

        Returns:
            Processed feature array
        """
        # Handle categorical features
        categorical_features = ['most_viewed_property_type']

        for col in categorical_features:
            if col in feature_df.columns:
                if is_training:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    feature_df[col] = self.label_encoders[col].fit_transform(feature_df[col].astype(str))
                else:
                    if col in self.label_encoders:
                        # Handle unknown categories
                        unique_values = set(self.label_encoders[col].classes_)
                        feature_df[col] = feature_df[col].astype(str).apply(
                            lambda x: x if x in unique_values else 'unknown'
                        )
                        feature_df[col] = self.label_encoders[col].transform(feature_df[col])

        # Remove non-numeric columns
        numeric_features = feature_df.select_dtypes(include=[np.number])

        # Handle missing values
        numeric_features = numeric_features.fillna(0)

        # Scale features
        if is_training:
            scaled_features = self.scaler.fit_transform(numeric_features)
        else:
            scaled_features = self.scaler.transform(numeric_features)

        return scaled_features

    def train_models(self) -> Dict[str, float]:
        """
        Train ML models for preference prediction

        Returns:
            Dictionary of model performance metrics
        """
        logger.info("Training ML preference prediction models...")

        # Prepare training data
        feature_df, target_df = self.prepare_training_data()

        if feature_df.empty or target_df.empty:
            logger.warning("No training data available")
            return {}

        # Preprocess features
        X = self.preprocess_features(feature_df, is_training=True)

        if X.shape[0] == 0:
            logger.warning("No valid features after preprocessing")
            return {}

        # Prepare targets for preference strength prediction
        y_preference = target_df['preference_strength'].values
        y_engagement = target_df['engagement_level'].values

        # Split data
        X_train, X_test, y_pref_train, y_pref_test, y_eng_train, y_eng_test = train_test_split(
            X, y_preference, y_engagement, test_size=0.2, random_state=42
        )

        metrics = {}

        try:
            # Train preference strength model
            self.preference_model.fit(X_train, y_pref_train)
            pref_pred = self.preference_model.predict(X_test)
            pref_mse = mean_squared_error(y_pref_test, pref_pred)
            metrics['preference_mse'] = pref_mse

            # Train engagement level model
            self.rating_model.fit(X_train, y_eng_train)
            eng_pred = self.rating_model.predict(X_test)
            eng_mse = mean_squared_error(y_eng_test, eng_pred)
            metrics['engagement_mse'] = eng_mse

            # Feature importance
            feature_importance = self.preference_model.feature_importances_
            metrics['top_feature_importance'] = float(np.max(feature_importance))

            self.is_trained = True
            logger.info(f"Model training completed. Metrics: {metrics}")

            # Save models
            self.save_models()

        except Exception as e:
            logger.error(f"Error training models: {e}")
            metrics['error'] = str(e)

        return metrics

    def predict_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Predict missing preferences for a user

        Args:
            user_id: Target user ID

        Returns:
            Dictionary of predicted preferences and confidence scores
        """
        if not self.is_trained:
            if not self.load_models():
                logger.warning("No trained models available for prediction")
                return {}

        try:
            # Extract user features
            features = self.extract_user_features(user_id)
            if not features:
                return {}

            # Convert to DataFrame and preprocess
            feature_df = pd.DataFrame([features])
            X = self.preprocess_features(feature_df, is_training=False)

            if X.shape[0] == 0:
                return {}

            # Make predictions
            preference_strength = self.preference_model.predict(X)[0]
            engagement_level = self.rating_model.predict(X)[0]

            # Generate prediction confidence
            confidence = min(1.0, max(0.1, engagement_level / 3.0))

            predictions = {
                'predicted_preference_strength': float(preference_strength),
                'predicted_engagement_level': float(engagement_level),
                'confidence': float(confidence),
                'should_request_more_prefs': preference_strength < 3,
                'user_engagement_tier': self._get_engagement_tier(engagement_level)
            }

            # Feature importance for explanation
            if hasattr(self.preference_model, 'feature_importances_'):
                top_feature_idx = np.argmax(self.preference_model.feature_importances_)
                predictions['key_factor_index'] = int(top_feature_idx)

            return predictions

        except Exception as e:
            logger.error(f"Error predicting preferences for user {user_id}: {e}")
            return {}

    def _get_engagement_tier(self, engagement_level: float) -> str:
        """Convert engagement level to tier description"""
        if engagement_level >= 2.5:
            return "high"
        elif engagement_level >= 1.5:
            return "medium"
        elif engagement_level >= 0.5:
            return "low"
        else:
            return "new"

    def save_models(self):
        """Save trained models to disk"""
        try:
            joblib.dump(self.preference_model, os.path.join(self.model_path, 'preference_model.pkl'))
            joblib.dump(self.rating_model, os.path.join(self.model_path, 'rating_model.pkl'))
            joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
            joblib.dump(self.label_encoders, os.path.join(self.model_path, 'label_encoders.pkl'))

            logger.info("Models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {e}")

    def load_models(self) -> bool:
        """Load trained models from disk"""
        try:
            model_files = {
                'preference_model.pkl': 'preference_model',
                'rating_model.pkl': 'rating_model',
                'scaler.pkl': 'scaler',
                'label_encoders.pkl': 'label_encoders'
            }

            for filename, attr_name in model_files.items():
                filepath = os.path.join(self.model_path, filename)
                if os.path.exists(filepath):
                    setattr(self, attr_name, joblib.load(filepath))
                else:
                    logger.warning(f"Model file not found: {filename}")
                    return False

            self.is_trained = True
            logger.info("Models loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False