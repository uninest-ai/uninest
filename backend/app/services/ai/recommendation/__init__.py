"""
AI-powered recommendation system for UniNest

This module provides advanced recommendation capabilities including:
- Collaborative filtering based on user similarity
- Content-based filtering with preference weighting
- Machine learning-based preference prediction
- Hybrid recommendations combining multiple algorithms
- Real-time learning and adaptation
"""

from .collaborative_filtering import CollaborativeFilteringEngine
from .ml_predictor import MLPreferencePredictor
from .hybrid_engine import HybridRecommendationEngine

__all__ = [
    'CollaborativeFilteringEngine',
    'MLPreferencePredictor',
    'HybridRecommendationEngine'
]