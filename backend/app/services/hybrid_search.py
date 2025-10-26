"""
Hybrid Search Service combining BM25 and Vector Search

This module implements:
- BM25 text search (keyword matching)
- Vector semantic search (meaning-based)
- Reciprocal Rank Fusion (RRF) for result merging
"""

from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.services.search_service import bm25_search_properties_ids_only
from app.services.embedding_service import get_embedding_service
from app.models import Property

import logging

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    rankings: List[List[Tuple[int, float]]],
    k: int = 60
) -> List[Tuple[int, float]]:
    """
    Reciprocal Rank Fusion (RRF) algorithm for combining multiple ranked lists.

    RRF formula: score(d) = sum(1 / (k + rank(d)))
    where rank(d) is the position of document d in each ranking list.

    Args:
        rankings: List of ranked results, each is a list of (id, score) tuples
        k: Constant to avoid division by zero (default: 60, common in literature)

    Returns:
        List of (id, fused_score) tuples sorted by fused score

    Example:
        ranking1 = [(1, 0.9), (2, 0.8), (3, 0.7)]  # BM25 results
        ranking2 = [(2, 0.95), (1, 0.85), (4, 0.75)]  # Vector results
        fused = reciprocal_rank_fusion([ranking1, ranking2])
        # Result: [(2, high_score), (1, high_score), (3, low_score), (4, low_score)]
    """
    scores = {}

    for ranking in rankings:
        for rank, (item_id, _original_score) in enumerate(ranking):
            # RRF score: 1 / (k + rank)
            # rank starts at 0, so position is rank + 1
            rrf_contribution = 1.0 / (k + rank + 1)

            if item_id in scores:
                scores[item_id] += rrf_contribution
            else:
                scores[item_id] = rrf_contribution

    # Sort by RRF score (descending)
    fused_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return fused_results


def hybrid_search(
    db: Session,
    query: str,
    limit: int = 10,
    bm25_limit: int = 200,
    vector_limit: int = 50,
    rrf_k: int = 60,
    min_bm25_score: float = 0.0
) -> List[Dict]:
    """
    Perform hybrid search combining BM25 and vector search with RRF fusion.

    Search Strategy:
    1. BM25 Search: Get top K_bm25 results (keyword matching) - Fast retrieval
    2. Vector Search on BM25 Candidates: Semantic search within BM25 results
    3. Global Vector Search: Get additional top K_vector results (catch long-tail)
    4. RRF Fusion: Merge BM25 and vector rankings using RRF

    Args:
        db: Database session
        query: Search query string
        limit: Final number of results to return
        bm25_limit: Number of results to fetch from BM25 (candidate pool)
        vector_limit: Number of results to fetch from global vector search
        rrf_k: RRF constant (default: 60)
        min_bm25_score: Minimum BM25 score threshold

    Returns:
        List of property dictionaries with hybrid scores
    """
    if not query or not query.strip():
        logger.warning("Empty query provided to hybrid search")
        return []

    embedding_service = get_embedding_service()

    # Step 1: BM25 Search - Get candidate pool
    logger.info(f"Performing BM25 search with limit={bm25_limit}")
    bm25_results = bm25_search_properties_ids_only(
        db=db,
        query=query.strip(),
        limit=bm25_limit,
        min_score=min_bm25_score
    )

    # If no BM25 results, we'll rely purely on vector search
    if not bm25_results:
        logger.warning("No BM25 results found - using vector search only")
        bm25_results = []  # Empty list for RRF fusion
        bm25_ids = []
    else:
        bm25_ids = [prop_id for prop_id, _ in bm25_results]
        logger.info(f"Found {len(bm25_ids)} BM25 candidates")

    # Step 2: Vector Search within BM25 candidates (hybrid recall)
    # Only if we have BM25 candidates
    if bm25_ids:
        logger.info(f"Performing vector search on {len(bm25_ids)} BM25 candidates")
        vector_results_filtered = embedding_service.vector_search(
            db=db,
            query_text=query.strip(),
            limit=bm25_limit,  # Search within all BM25 results
            property_ids=bm25_ids  # Restrict to BM25 candidates
        )
    else:
        vector_results_filtered = []

    # Step 3: Global Vector Search (long-tail recall)
    # Always perform this - it will return results even if BM25 failed
    logger.info(f"Performing global vector search with limit={vector_limit}")
    vector_results_global = embedding_service.vector_search(
        db=db,
        query_text=query.strip(),
        limit=vector_limit if not bm25_ids else vector_limit,  # Use more results if BM25 failed
        property_ids=None  # Search entire database
    )

    # Combine vector results (remove duplicates, prefer filtered)
    vector_ids_filtered = {prop_id for prop_id, _ in vector_results_filtered}
    vector_results_combined = vector_results_filtered.copy()

    for prop_id, score in vector_results_global:
        if prop_id not in vector_ids_filtered:
            vector_results_combined.append((prop_id, score))

    logger.info(f"Combined vector results: {len(vector_results_combined)} properties")

    # Step 4: RRF Fusion
    logger.info("Performing RRF fusion")
    fused_results = reciprocal_rank_fusion(
        rankings=[bm25_results, vector_results_combined],
        k=rrf_k
    )

    # Step 5: Retrieve property details for top results
    top_ids = [prop_id for prop_id, _ in fused_results[:limit]]
    properties = db.query(Property).filter(Property.id.in_(top_ids)).all()

    # Create a mapping for quick lookup
    property_map = {prop.id: prop for prop in properties}

    # Build response with scores
    response = []
    for prop_id, hybrid_score in fused_results[:limit]:
        if prop_id not in property_map:
            continue

        prop = property_map[prop_id]

        # Get individual scores for transparency
        bm25_score = next((score for pid, score in bm25_results if pid == prop_id), 0.0)
        vector_score = next((score for pid, score in vector_results_combined if pid == prop_id), 0.0)

        property_dict = {
            "id": prop.id,
            "title": prop.title,
            "description": prop.description,
            "price": prop.price,
            "address": prop.address,
            "city": prop.city,
            "latitude": prop.latitude,
            "longitude": prop.longitude,
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "property_type": prop.property_type,
            "area": prop.area,
            "amenities": prop.api_amenities,
            "labels": prop.labels,
            "image_url": prop.image_url,
            "api_images": prop.api_images,
            "scores": {
                "hybrid_rrf": float(hybrid_score),
                "bm25": float(bm25_score),
                "vector": float(vector_score)
            }
        }
        response.append(property_dict)

    logger.info(f"Returning {len(response)} hybrid search results")
    return response


def hybrid_search_simple(
    db: Session,
    query: str,
    limit: int = 10
) -> List[Dict]:
    """
    Simplified hybrid search with reasonable defaults.

    This is a convenience wrapper around hybrid_search() with good default parameters.

    Args:
        db: Database session
        query: Search query string
        limit: Number of results to return

    Returns:
        List of property dictionaries with hybrid scores
    """
    return hybrid_search(
        db=db,
        query=query,
        limit=limit,
        bm25_limit=200,  # Large candidate pool
        vector_limit=50,  # Moderate global search
        rrf_k=60,  # Standard RRF constant
        min_bm25_score=0.0  # No filtering
    )