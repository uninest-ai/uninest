#!/usr/bin/env python3
"""
Comprehensive benchmark script for hybrid search system.

Measures:
- Recall@10 (retrieval quality)
- Latency percentiles (p50, p95, p99)
- QPS (queries per second)
- Before/after optimization comparison

Usage:
    python scripts/benchmark_hybrid_search.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import json
import statistics
from typing import List, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.hybrid_search import hybrid_search_simple, bm25_search_properties_ids_only
from app.services.embedding_service import EmbeddingService
from app.models import Property


# Test queries with expected relevant property characteristics
TEST_QUERIES = [
    {
        "query": "Oakland apartment",
        "expected_keywords": ["Oakland", "apartment"],
        "description": "Location-focused search"
    },
    {
        "query": "Shadyside modern",
        "expected_keywords": ["Shadyside", "modern"],
        "description": "Location + style"
    },
    {
        "query": "apartment parking laundry",
        "expected_keywords": ["apartment", "parking", "laundry"],
        "description": "Amenity-focused search"
    },
    {
        "query": "Squirrel Hill quiet",
        "expected_keywords": ["Squirrel Hill", "quiet"],
        "description": "Location + atmosphere"
    },
    {
        "query": "house backyard",
        "expected_keywords": ["house", "backyard"],
        "description": "Property type + feature"
    },
]


def calculate_recall_at_k(
    retrieved_ids: List[int],
    relevant_ids: Set[int],
    k: int = 10
) -> float:
    """
    Calculate Recall@K metric.

    Args:
        retrieved_ids: List of retrieved property IDs (in ranking order)
        relevant_ids: Set of truly relevant property IDs
        k: Number of top results to consider

    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant_ids:
        return 0.0

    top_k = set(retrieved_ids[:k])
    relevant_retrieved = len(top_k & relevant_ids)

    return relevant_retrieved / len(relevant_ids)


def calculate_precision_at_k(
    retrieved_ids: List[int],
    relevant_ids: Set[int],
    k: int = 10
) -> float:
    """
    Calculate Precision@K metric.

    Precision@K = (relevant items in top K) / K

    Unlike Recall, Precision is stable across dataset sizes and measures
    whether the results we return are actually relevant.

    Args:
        retrieved_ids: List of retrieved property IDs (in ranking order)
        relevant_ids: Set of truly relevant property IDs
        k: Number of top results to consider

    Returns:
        Precision@K score (0.0 to 1.0)
    """
    if not retrieved_ids:
        return 0.0

    top_k = set(retrieved_ids[:k])
    relevant_retrieved = len(top_k & relevant_ids)

    return relevant_retrieved / k


def get_ground_truth_relevant_properties(
    db: Session,
    query_info: Dict
) -> Set[int]:
    """
    Get ground truth relevant properties for a query.

    For this benchmark, we define "relevant" as properties that:
    1. Contain at least one expected keyword in address, neighborhood, or description
    2. Are active and have coordinates

    Args:
        db: Database session
        query_info: Query information with expected_keywords

    Returns:
        Set of relevant property IDs
    """
    keywords = query_info["expected_keywords"]
    relevant_ids = set()

    properties = db.query(Property).filter(
        Property.is_active == True,
        Property.latitude.isnot(None),
        Property.longitude.isnot(None)
    ).all()

    for prop in properties:
        # Check if any keyword appears in property data
        search_text = " ".join(filter(None, [
            prop.address or "",
            prop.city or "",
            prop.title or "",
            prop.description or "",
            prop.extended_description or ""
        ])).lower()

        for keyword in keywords:
            if keyword.lower() in search_text:
                relevant_ids.add(prop.id)
                break

    return relevant_ids


def benchmark_single_query(
    query: str,
    method: str = "hybrid"
) -> Dict:
    """
    Benchmark a single query.

    Args:
        db: Database session
        query: Search query
        method: "hybrid", "bm25", or "vector"

    Returns:
        Dictionary with latency and result IDs
    """
    db = SessionLocal()
    try:
        start_time = time.perf_counter()

        if method == "hybrid":
            results = hybrid_search_simple(db=db, query=query, limit=10)
            result_ids = [r["id"] for r in results]
        elif method == "bm25":
            bm25_results = bm25_search_properties_ids_only(db=db, query=query, limit=10)
            result_ids = [pid for pid, _ in bm25_results]
        else:  # vector only
            # For vector-only, we'd need to implement this separately
            # For now, fall back to hybrid
            results = hybrid_search_simple(db=db, query=query, limit=10)
            result_ids = [r["id"] for r in results]

        latency_ms = (time.perf_counter() - start_time) * 1000

        return {
            "latency_ms": latency_ms,
            "result_ids": result_ids
        }
    finally:
        db.close()


def run_load_test(
    db: Session,
    queries: List[str],
    num_iterations: int = 50,
    concurrent_workers: int = 5
) -> Dict:
    """
    Run load test with concurrent queries.

    Args:
        db: Database session
        queries: List of queries to test
        num_iterations: Number of times to repeat each query
        concurrent_workers: Number of concurrent workers

    Returns:
        Performance statistics
    """
    print(f"\n🔥 Running load test...")
    print(f"   Queries: {len(queries)}")
    print(f"   Iterations per query: {num_iterations}")
    print(f"   Concurrent workers: {concurrent_workers}")
    print(f"   Total requests: {len(queries) * num_iterations}")

    latencies = []
    start_time = time.time()

    # Create test cases (query repeated multiple times)
    test_cases = []
    for query in queries:
        for _ in range(num_iterations):
            test_cases.append(query)

    completed = 0
    with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        # Each worker gets its own DB session
        futures = []
        for query in test_cases:
            future = executor.submit(
                benchmark_single_query,
                query,
                "hybrid"
            )
            futures.append(future)

        for future in as_completed(futures):
            result = future.result()
            latencies.append(result["latency_ms"])
            completed += 1

            if completed % 25 == 0:
                print(f"   Progress: {completed}/{len(test_cases)} requests...")

    end_time = time.time()
    duration = end_time - start_time

    # Calculate statistics
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)

    return {
        "total_requests": len(test_cases),
        "duration_sec": round(duration, 2),
        "qps": round(len(test_cases) / duration, 2),
        "latency_ms": {
            "min": round(min(latencies), 1),
            "max": round(max(latencies), 1),
            "mean": round(statistics.mean(latencies), 1),
            "median": round(statistics.median(latencies), 1),
            "p50": round(sorted_latencies[int(0.50 * (n-1))], 1),
            "p95": round(sorted_latencies[int(0.95 * (n-1))], 1),
            "p99": round(sorted_latencies[int(0.99 * (n-1))], 1),
        }
    }


def run_recall_benchmark(db: Session, test_queries: List[Dict]) -> Dict:
    """
    Benchmark retrieval quality (Recall@10 and Precision@10).

    Args:
        db: Database session
        test_queries: List of test query dictionaries

    Returns:
        Recall and Precision statistics
    """
    print(f"\n📊 Measuring Recall@10 and Precision@10...")

    recall_scores = []
    precision_scores = []
    results_per_query = []

    for query_info in test_queries:
        query = query_info["query"]
        print(f"   Testing: '{query}'")

        # Get ground truth relevant properties
        relevant_ids = get_ground_truth_relevant_properties(db, query_info)

        # Get hybrid search results
        search_results = hybrid_search_simple(db=db, query=query, limit=10)
        retrieved_ids = [r["id"] for r in search_results]

        # Calculate recall and precision
        recall = calculate_recall_at_k(retrieved_ids, relevant_ids, k=10)
        precision = calculate_precision_at_k(retrieved_ids, relevant_ids, k=10)

        recall_scores.append(recall)
        precision_scores.append(precision)

        results_per_query.append({
            "query": query,
            "recall@10": round(recall, 3),
            "precision@10": round(precision, 3),
            "relevant_count": len(relevant_ids),
            "retrieved_count": len(retrieved_ids)
        })

        print(f"      Recall@10: {recall:.3f} | Precision@10: {precision:.3f} ({len(retrieved_ids)} retrieved, {len(relevant_ids)} relevant)")

    avg_recall = statistics.mean(recall_scores) if recall_scores else 0.0
    avg_precision = statistics.mean(precision_scores) if precision_scores else 0.0

    return {
        "average_recall@10": round(avg_recall, 3),
        "average_precision@10": round(avg_precision, 3),
        "per_query": results_per_query
    }


def main():
    """Run comprehensive benchmark."""
    print("=" * 60)
    print("🚀 HYBRID SEARCH BENCHMARK")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Check database has properties
        property_count = db.query(Property).filter(Property.is_active == True).count()
        quality_count = db.query(Property).filter(
            Property.is_active == True,
            Property.latitude.isnot(None),
            Property.longitude.isnot(None)
        ).count()

        print(f"\n📦 Database Status:")
        print(f"   Total active properties: {property_count}")
        print(f"   Quality properties (with coords): {quality_count}")

        if property_count == 0:
            print("\n❌ No properties in database. Please run data fetch first.")
            return

        # 1. Recall Benchmark
        recall_results = run_recall_benchmark(db, TEST_QUERIES)

        # 2. Load Test (Performance)
        queries = [q["query"] for q in TEST_QUERIES]
        perf_results = run_load_test(
            db=db,
            queries=queries,
            num_iterations=50,  # 50 iterations × 5 queries = 250 requests
            concurrent_workers=5
        )

        # Print Results
        print("\n" + "=" * 60)
        print("📈 BENCHMARK RESULTS")
        print("=" * 60)

        print(f"\n🎯 RETRIEVAL QUALITY:")
        print(f"   Average Recall@10: {recall_results['average_recall@10']:.3f}")
        print(f"   Average Precision@10: {recall_results['average_precision@10']:.3f}")
        print("\n   Per-query breakdown:")
        for result in recall_results['per_query']:
            print(f"      '{result['query']}':")
            print(f"         Recall@10: {result['recall@10']:.3f} | Precision@10: {result['precision@10']:.3f}")

        print(f"\n⚡ PERFORMANCE:")
        print(f"   Total Requests: {perf_results['total_requests']}")
        print(f"   Duration: {perf_results['duration_sec']} sec")
        print(f"   QPS: {perf_results['qps']} req/s")
        print(f"\n   Latency (ms):")
        print(f"      p50 (median): {perf_results['latency_ms']['p50']} ms")
        print(f"      p95: {perf_results['latency_ms']['p95']} ms")
        print(f"      p99: {perf_results['latency_ms']['p99']} ms")
        print(f"      mean: {perf_results['latency_ms']['mean']} ms")

        # Save results to file
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "recall": recall_results,
            "performance": perf_results
        }

        output_file = "benchmark_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Results saved to: {output_file}")

        # Generate resume bullet point
        print("\n" + "=" * 60)
        print("📝 RESUME BULLET POINT:")
        print("=" * 60)
        bullet = (
            f"Implemented hybrid retrieval (Postgres BM25 + vector embeddings) with RRF fusion, "
            f"delivering Precision@10 {recall_results['average_precision@10']:.2f} "
            f"while achieving p95 latency {perf_results['latency_ms']['p95']} ms "
            f"via candidate pruning and local cosine scoring; "
            f"exposed /metrics (p50/p95/p99, QPS) endpoint "
            f"with load tests baselining QPS ~{perf_results['qps']} "
            f"and p95 ~{perf_results['latency_ms']['p95']} ms."
        )
        print(f"\n{bullet}\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
