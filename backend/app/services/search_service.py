"""
BM25 Full-Text Search Service for Properties

This module provides BM25-based full-text search functionality using PostgreSQL's
built-in text search capabilities with ts_rank for relevance scoring.
"""

from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import Property


def bm25_search_properties(
    db: Session,
    query: str,
    limit: int = 10,
    min_score: float = 0.0
) -> List[Tuple[Property, float]]:
    """
    Perform BM25 full-text search on properties using PostgreSQL FTS.

    Args:
        db: Database session
        query: Search query string
        limit: Maximum number of results to return
        min_score: Minimum relevance score threshold

    Returns:
        List of tuples containing (Property object, relevance_score)
        Sorted by relevance score in descending order

    Note:
        Uses PostgreSQL's ts_rank for BM25-like relevance scoring.
        The search_vector column must exist (created by migration).
    """
    # Construct the SQL query with ts_rank for BM25-like scoring
    sql = text("""
        SELECT
            p.*,
            ts_rank(p.search_vector, plainto_tsquery('english', :query)) AS relevance_score
        FROM properties p
        WHERE p.search_vector @@ plainto_tsquery('english', :query)
            AND ts_rank(p.search_vector, plainto_tsquery('english', :query)) >= :min_score
        ORDER BY relevance_score DESC
        LIMIT :limit
    """)

    # Execute query
    result = db.execute(
        sql,
        {
            "query": query,
            "min_score": min_score,
            "limit": limit
        }
    )

    # Process results
    properties_with_scores = []
    for row in result:
        # Convert row to dictionary
        row_dict = dict(row._mapping)
        relevance_score = row_dict.pop('relevance_score')

        # Create Property object from remaining fields
        property_obj = Property(**{k: v for k, v in row_dict.items() if hasattr(Property, k)})

        properties_with_scores.append((property_obj, relevance_score))

    return properties_with_scores


def bm25_search_properties_ids_only(
    db: Session,
    query: str,
    limit: int = 10,
    min_score: float = 0.0
) -> List[Tuple[int, float]]:
    """
    Perform BM25 search and return only property IDs with scores.

    This is more efficient when you only need IDs (e.g., for hybrid search).

    Args:
        db: Database session
        query: Search query string
        limit: Maximum number of results to return
        min_score: Minimum relevance score threshold

    Returns:
        List of tuples containing (property_id, relevance_score)
        Sorted by relevance score in descending order
    """
    sql = text("""
        SELECT
            p.id,
            ts_rank(p.search_vector, plainto_tsquery('english', :query)) AS relevance_score
        FROM properties p
        WHERE p.search_vector @@ plainto_tsquery('english', :query)
            AND ts_rank(p.search_vector, plainto_tsquery('english', :query)) >= :min_score
        ORDER BY relevance_score DESC
        LIMIT :limit
    """)

    result = db.execute(
        sql,
        {
            "query": query,
            "min_score": min_score,
            "limit": limit
        }
    )

    return [(row.id, row.relevance_score) for row in result]


def test_bm25_search(db: Session, query: str) -> None:
    """
    Test function to verify BM25 search is working correctly.

    Prints search results with scores to console.
    """
    print(f"\n{'='*60}")
    print(f"BM25 Search Test: '{query}'")
    print(f"{'='*60}")

    results = bm25_search_properties(db, query, limit=5)

    if not results:
        print("No results found.")
        return

    for i, (prop, score) in enumerate(results, 1):
        print(f"\n{i}. {prop.title} (Score: {score:.4f})")
        print(f"   ID: {prop.id}")
        print(f"   Price: ${prop.price}")
        print(f"   Description: {prop.description[:100]}...")

    print(f"\n{'='*60}\n")