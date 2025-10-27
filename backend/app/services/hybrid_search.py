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


def price_weighted_rerank(
    fused_results: List[Tuple[int, float]],
    properties: List[Property],
    target_price: float = None,
    price_weight: float = 0.4
) -> List[Tuple[int, float]]:
    """
    Rerank search results by combining relevance scores with price matching.

    Args:
        fused_results: List of (property_id, rrf_score) tuples from RRF fusion
        properties: List of Property objects
        target_price: Target price for matching (if None, uses median of results)
        price_weight: Weight for price score (0.0-1.0). Higher = price matters more.
                     Default 0.4 means 40% price, 60% relevance.

    Returns:
        Reranked list of (property_id, combined_score) tuples
    """
    if not fused_results or not properties:
        return fused_results

    # Create property map
    prop_map = {prop.id: prop for prop in properties}

    # Get all prices
    prices = [prop_map[pid].price for pid, _ in fused_results if pid in prop_map]
    if not prices:
        return fused_results

    # If no target price provided, use median as target
    if target_price is None:
        prices_sorted = sorted(prices)
        target_price = prices_sorted[len(prices_sorted) // 2]

    # Calculate price range for normalization (±50% of target)
    price_range = target_price * 0.5

    # Normalize RRF scores to 0-1
    rrf_scores = [score for _, score in fused_results]
    max_rrf = max(rrf_scores) if rrf_scores else 1.0
    min_rrf = min(rrf_scores) if rrf_scores else 0.0
    rrf_range = max_rrf - min_rrf if max_rrf > min_rrf else 1.0

    reranked = []
    for prop_id, rrf_score in fused_results:
        if prop_id not in prop_map:
            continue

        prop = prop_map[prop_id]

        # Normalize RRF score to 0-1
        norm_rrf_score = (rrf_score - min_rrf) / rrf_range if rrf_range > 0 else 0.5

        # Calculate price score (1.0 = perfect match, decreases with distance)
        price_diff = abs(prop.price - target_price)
        if price_diff <= price_range:
            # Within range: linear decay from 1.0 to 0.0
            price_score = 1.0 - (price_diff / price_range)
        else:
            # Outside range: exponential decay
            price_score = max(0.0, 0.5 * (1.0 - (price_diff - price_range) / target_price))

        # Combine scores with weighting
        combined_score = (1 - price_weight) * norm_rrf_score + price_weight * price_score

        reranked.append((prop_id, combined_score))

    # Sort by combined score
    reranked.sort(key=lambda x: x[1], reverse=True)

    logger.info(f"Price-weighted reranking: target=${target_price:.0f}, weight={price_weight}")
    return reranked


def hybrid_search(
    db: Session,
    query: str,
    limit: int = 10,
    bm25_limit: int = 200,
    vector_limit: int = 50,
    rrf_k: int = 60,
    min_bm25_score: float = 0.0,
    target_price: float = None,
    price_weight: float = 0.4
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
        limit=bm25_limit * 2,  # Get more candidates to filter for quality
        min_score=min_bm25_score
    )

    # Filter for quality properties (must have coordinates)
    if bm25_results:
        quality_property_ids = db.query(Property.id).filter(
            Property.id.in_([pid for pid, _ in bm25_results]),
            Property.latitude.isnot(None),
            Property.longitude.isnot(None),
            Property.is_active == True
        ).all()
        quality_ids = {pid for (pid,) in quality_property_ids}
        bm25_results = [(pid, score) for pid, score in bm25_results if pid in quality_ids][:bm25_limit]
        logger.info(f"Filtered to {len(bm25_results)} quality properties with coordinates")

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

    # Step 4.5: Price-weighted reranking (fetch more for reranking)
    # Fetch 2x limit properties for reranking to ensure diversity
    rerank_limit = limit * 3
    top_ids_for_rerank = [prop_id for prop_id, _ in fused_results[:rerank_limit]]
    properties_for_rerank = db.query(Property).filter(Property.id.in_(top_ids_for_rerank)).all()

    if target_price is not None or price_weight > 0:
        logger.info(f"Applying price-weighted reranking (weight={price_weight})")
        fused_results = price_weighted_rerank(
            fused_results=fused_results[:rerank_limit],
            properties=properties_for_rerank,
            target_price=target_price,
            price_weight=price_weight
        )

    # Step 5: Retrieve property details for top results after reranking
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