"""
Embedding Service for Property Vector Search

This module handles:
- Text embedding generation using Sentence Transformers
- Cosine similarity computation
- Embedding storage and retrieval
"""

import json
import numpy as np
from typing import List, Optional, Tuple
from numpy.linalg import norm
from sqlalchemy.orm import Session
from sqlalchemy import text

import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing property embeddings."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy load the model to avoid loading on import."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model {self.model_name}: {e}")
                raise
        return self._model

    def encode_text(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Encode text into a vector embedding.

        Args:
            text: Text to encode
            normalize: Whether to normalize the embedding (recommended for cosine similarity)

        Returns:
            Numpy array of the embedding
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for encoding")
            return np.zeros(384, dtype=np.float32)  # all-MiniLM-L6-v2 dimension

        try:
            embedding = self.model.encode(
                text,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            raise

    def save_embedding(
        self,
        db: Session,
        property_id: int,
        embedding: np.ndarray
    ) -> bool:
        """
        Save embedding to database.

        Args:
            db: Database session
            property_id: Property ID
            embedding: Embedding vector

        Returns:
            True if successful, False otherwise
        """
        try:
            embedding_json = json.dumps(embedding.tolist())

            db.execute(
                text("""
                    INSERT INTO property_embeddings (id, embedding, model_name)
                    VALUES (:id, CAST(:embedding AS jsonb), :model_name)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        model_name = EXCLUDED.model_name,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "id": property_id,
                    "embedding": embedding_json,
                    "model_name": self.model_name
                }
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving embedding for property {property_id}: {e}")
            db.rollback()
            return False

    def get_embedding(
        self,
        db: Session,
        property_id: int
    ) -> Optional[np.ndarray]:
        """
        Retrieve embedding from database.

        Args:
            db: Database session
            property_id: Property ID

        Returns:
            Embedding as numpy array or None if not found
        """
        try:
            result = db.execute(
                text("""
                    SELECT embedding
                    FROM property_embeddings
                    WHERE id = :id AND model_name = :model_name
                """),
                {"id": property_id, "model_name": self.model_name}
            ).fetchone()

            if result:
                embedding_list = json.loads(result[0]) if isinstance(result[0], str) else result[0]
                return np.array(embedding_list, dtype=np.float32)
            return None
        except Exception as e:
            logger.error(f"Error retrieving embedding for property {property_id}: {e}")
            return None

    def get_all_embeddings(
        self,
        db: Session,
        property_ids: Optional[List[int]] = None
    ) -> dict:
        """
        Retrieve multiple embeddings from database.

        Args:
            db: Database session
            property_ids: Optional list of property IDs to filter by

        Returns:
            Dictionary mapping property_id to embedding
        """
        try:
            if property_ids:
                query = text("""
                    SELECT id, embedding
                    FROM property_embeddings
                    WHERE id = ANY(:ids) AND model_name = :model_name
                """)
                result = db.execute(
                    query,
                    {"ids": property_ids, "model_name": self.model_name}
                )
            else:
                query = text("""
                    SELECT id, embedding
                    FROM property_embeddings
                    WHERE model_name = :model_name
                """)
                result = db.execute(query, {"model_name": self.model_name})

            embeddings = {}
            for row in result:
                prop_id = row[0]
                embedding_list = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                embeddings[prop_id] = np.array(embedding_list, dtype=np.float32)

            return embeddings
        except Exception as e:
            logger.error(f"Error retrieving embeddings: {e}")
            return {}

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        norm_a = norm(a)
        norm_b = norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a, b) / (norm_a * norm_b))

    def vector_search(
        self,
        db: Session,
        query_text: str,
        limit: int = 50,
        property_ids: Optional[List[int]] = None
    ) -> List[Tuple[int, float]]:
        """
        Perform vector similarity search.

        Args:
            db: Database session
            query_text: Search query text
            limit: Maximum number of results
            property_ids: Optional list of property IDs to search within (for hybrid search)

        Returns:
            List of tuples (property_id, similarity_score) sorted by score
        """
        # Encode query
        query_embedding = self.encode_text(query_text, normalize=True)

        # Get all relevant embeddings
        embeddings = self.get_all_embeddings(db, property_ids)

        if not embeddings:
            logger.warning("No embeddings found for vector search")
            return []

        # Compute similarities
        similarities = []
        for prop_id, prop_embedding in embeddings.items():
            similarity = self.cosine_similarity(query_embedding, prop_embedding)
            similarities.append((prop_id, similarity))

        # Sort by similarity (descending) and limit
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]


# Global instance
_embedding_service = None


def get_embedding_service(model_name: str = 'all-MiniLM-L6-v2') -> EmbeddingService:
    """
    Get or create global embedding service instance.

    Args:
        model_name: Model name to use

    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name)
    return _embedding_service
