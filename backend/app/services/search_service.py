"""
BM25 Full-Text Search Service for Properties

This module provides BM25-based full-text search functionality using PostgreSQL's
built-in text search capabilities with ts_rank for relevance scoring.
"""

import re
from typing import List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import Property


def _execute_bm25_query(
    db: Session,
    query_value: str,
    limit: int,
    min_score: float,
    ids_only: bool = False,
    ts_function: str = "websearch_to_tsquery"
):
    """
    Execute a BM25 query using the provided tsquery function.
    """
    ts_expression = f"{ts_function}('english', :ts_query)"

    if ids_only:
        sql = text(f"""
            SELECT
                p.id,
                ts_rank(p.search_vector, {ts_expression}) AS relevance_score
            FROM properties p
            WHERE p.search_vector @@ {ts_expression}
                AND ts_rank(p.search_vector, {ts_expression}) >= :min_score
            ORDER BY relevance_score DESC
            LIMIT :limit
        """)
    else:
        sql = text(f"""
            SELECT
                p.*,
                ts_rank(p.search_vector, {ts_expression}) AS relevance_score
            FROM properties p
            WHERE p.search_vector @@ {ts_expression}
                AND ts_rank(p.search_vector, {ts_expression}) >= :min_score
            ORDER BY relevance_score DESC
            LIMIT :limit
        """)

    params = {
        "ts_query": query_value,
        "min_score": min_score,
        "limit": limit
    }

    result = db.execute(sql, params)
    rows = list(result)

    if ids_only:
        return [(row.id, row.relevance_score) for row in rows]

    properties_with_scores: List[Tuple[Property, float]] = []
    for row in rows:
        row_dict = dict(row._mapping)
        relevance_score = row_dict.pop("relevance_score")
        property_obj = Property(**{k: v for k, v in row_dict.items() if hasattr(Property, k)})
        properties_with_scores.append((property_obj, relevance_score))

    return properties_with_scores


def _build_fallback_tsquery(raw_query: str) -> str:
    """
    Build a fallback tsquery string that allows OR/prefix matching.
    Example: 'Oakland apartment' -> 'oakland:* | apartment:*'
    """
    tokens = re.findall(r"[A-Za-z0-9]+", raw_query.lower())
    tokens = [token for token in tokens if token]
    if not tokens:
        return ""
    return " | ".join(f"{token}:*" for token in tokens)


def bm25_search_properties(
    db: Session,
    query: str,
    limit: int = 10,
    min_score: float = 0.0
) -> List[Tuple[Property, float]]:
    """
    Perform BM25 full-text search on properties using PostgreSQL FTS.

    Uses websearch_to_tsquery for natural language matching by default and
    falls back to a broader OR-based search when no results are found.
    """
    if not query or not query.strip():
        return []

    normalized_query = query.strip()

    # Primary search using web-style parsing (handles quotes, operators, etc.)
    results = _execute_bm25_query(
        db=db,
        query_value=normalized_query,
        limit=limit,
        min_score=min_score,
        ids_only=False,
        ts_function="websearch_to_tsquery"
    )

    if results:
        return results

    # Fallback: allow OR/prefix matching to avoid zero-result scenarios
    fallback_query = _build_fallback_tsquery(normalized_query)
    if not fallback_query:
        return []

    return _execute_bm25_query(
        db=db,
        query_value=fallback_query,
        limit=limit,
        min_score=min_score,
        ids_only=False,
        ts_function="to_tsquery"
    )


def bm25_search_properties_ids_only(
    db: Session,
    query: str,
    limit: int = 10,
    min_score: float = 0.0
) -> List[Tuple[int, float]]:
    """
    Perform BM25 search and return only property IDs with scores.

    Falls back to a broader OR-based query when the primary search has no hits.
    """
    if not query or not query.strip():
        return []

    normalized_query = query.strip()

    results = _execute_bm25_query(
        db=db,
        query_value=normalized_query,
        limit=limit,
        min_score=min_score,
        ids_only=True,
        ts_function="websearch_to_tsquery"
    )

    if results:
        return results

    fallback_query = _build_fallback_tsquery(normalized_query)
    if not fallback_query:
        return []

    return _execute_bm25_query(
        db=db,
        query_value=fallback_query,
        limit=limit,
        min_score=min_score,
        ids_only=True,
        ts_function="to_tsquery"
    )


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
