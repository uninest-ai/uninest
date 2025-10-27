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
# Realistic user queries with detailed preferences and price constraints
TEST_QUERIES = [
    {
        "query": "Oakland apartment two-car garage well-maintained landscaping quiet, target_price: 1000.0",
        "expected_keywords": ["Oakland", "apartment", "garage", "quiet"],
        "description": "Location + amenities + atmosphere with price constraint"
    },
    {
        "query": "Shadyside modern studio hardwood floors natural light near CMU, target_price: 1200.0",
        "expected_keywords": ["Shadyside", "modern", "studio", "hardwood"],
        "description": "Location + style + features with price constraint"
    },
    {
        "query": "Squirrel Hill 2-bedroom apartment parking laundry in-unit pet-friendly, target_price: 1500.0",
        "expected_keywords": ["Squirrel Hill", "apartment", "parking", "laundry", "pet"],
        "description": "Location + size + amenities + pet-friendly with price constraint"
    },
    {
        "query": "Pittsburgh house backyard quiet neighborhood good schools family-friendly, target_price: 2000.0",
        "expected_keywords": ["house", "backyard", "quiet", "family"],
        "description": "Property type + features + family needs with price constraint"
    },
    {
        "query": "Oakland walking distance CMU furnished utilities included student housing, target_price: 800.0",
        "expected_keywords": ["Oakland", "CMU", "furnished", "utilities", "student"],
        "description": "Student-focused search with location and budget constraint"
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
    concurrent_workers: int = 5,
    method: str = "hybrid"
) -> Dict:
    """
    Run load test with concurrent queries.

    Args:
        db: Database session
        queries: List of queries to test
        num_iterations: Number of times to repeat each query
        concurrent_workers: Number of concurrent workers
        method: Search method ("hybrid" or "bm25")

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
                method
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


def run_recall_benchmark(db: Session, test_queries: List[Dict], method: str = "hybrid") -> Dict:
    """
    Benchmark retrieval quality (Recall@10 and Precision@10).

    Args:
        db: Database session
        test_queries: List of test query dictionaries
        method: Search method ("hybrid" or "bm25")

    Returns:
        Recall and Precision statistics
    """
    print(f"\n📊 Measuring Recall@10 and Precision@10 ({method.upper()})...")

    recall_scores = []
    precision_scores = []
    results_per_query = []

    for query_info in test_queries:
        query = query_info["query"]
        print(f"\n   Testing: '{query}'")

        # Get ground truth relevant properties
        relevant_ids = get_ground_truth_relevant_properties(db, query_info)

        # Get search results based on method
        if method == "bm25":
            bm25_results = bm25_search_properties_ids_only(db=db, query=query, limit=10)
            retrieved_ids = [pid for pid, _ in bm25_results]
        else:  # hybrid
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

        # Show sample properties that participate in the search
        if retrieved_ids:
            print(f"\n      📋 Sample Retrieved Properties (top 3):")
            sample_props = db.query(Property).filter(Property.id.in_(retrieved_ids[:3])).all()
            for i, prop in enumerate(sample_props, 1):
                print(f"\n         [{i}] Property ID: {prop.id}")
                print(f"             Title: {prop.title[:80] if prop.title else 'N/A'}...")
                print(f"             Address: {prop.address or 'N/A'}, {prop.city or 'N/A'}")
                print(f"             Price: ${prop.price}/mo | Type: {prop.property_type or 'N/A'}")

                # Show searchable text (what BM25 uses)
                print(f"             📝 Searchable Text (BM25):")
                if prop.description:
                    print(f"                Description: {prop.description[:100]}...")
                if prop.extended_description:
                    print(f"                AI Keywords: {prop.extended_description[:100]}...")

                # Show amenities and labels (additional context)
                if prop.api_amenities:
                    amenities = prop.api_amenities if isinstance(prop.api_amenities, list) else []
                    print(f"             🏷️  Amenities: {', '.join(amenities[:5])}")
                if prop.labels:
                    labels = prop.labels if isinstance(prop.labels, list) else []
                    print(f"             🔖 Image Labels: {', '.join(str(l) for l in labels[:5])}")

                # Show embedding status (for vector search)
                has_embedding = hasattr(prop, 'embedding') and prop.embedding is not None
                print(f"             🔢 Vector Embedding: {'✅ Present' if has_embedding else '❌ Missing'}")

    avg_recall = statistics.mean(recall_scores) if recall_scores else 0.0
    avg_precision = statistics.mean(precision_scores) if precision_scores else 0.0

    return {
        "average_recall@10": round(avg_recall, 3),
        "average_precision@10": round(avg_precision, 3),
        "per_query": results_per_query
    }


def main():
    """Run comprehensive benchmark comparing BM25 vs Hybrid."""
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark search system")
    parser.add_argument("--method", choices=["bm25", "hybrid", "both"], default="both",
                       help="Which method to benchmark (default: both)")
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 SEARCH BENCHMARK")
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

        queries = [q["query"] for q in TEST_QUERIES]

        # Determine which methods to run
        methods_to_run = []
        if args.method == "both":
            methods_to_run = ["bm25", "hybrid"]
        else:
            methods_to_run = [args.method]

        all_results = {}

        for method in methods_to_run:
            print(f"\n{'='*60}")
            print(f"📊 BENCHMARKING: {method.upper()}")
            print(f"{'='*60}")

            # 1. Recall Benchmark
            recall_results = run_recall_benchmark(db, TEST_QUERIES, method=method)

            # 2. Load Test (Performance)
            perf_results = run_load_test(
                db=db,
                queries=queries,
                num_iterations=50,
                concurrent_workers=5,
                method=method
            )

            all_results[method] = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "recall": recall_results,
                "performance": perf_results
            }

        # Save results to file
        import os
        import platform
        import psutil

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_dir = "benchmark_results"
        os.makedirs(results_dir, exist_ok=True)

        # Add metadata for environment tracking
        metadata = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "database_size": property_count,
            "quality_properties": quality_count,
            "environment": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "cpu_count": psutil.cpu_count(),
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "hostname": platform.node()
            }
        }

        # Save individual results
        for method, result in all_results.items():
            result["metadata"] = metadata

            # Save method-specific file
            method_file = os.path.join(results_dir, f"benchmark_{method}_{timestamp}.json")
            with open(method_file, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 {method.upper()} results saved: {method_file}")

        # If both methods were run, compare them automatically
        if len(methods_to_run) == 2:
            print("\n" + "=" * 60)
            print("📊 BM25 vs HYBRID COMPARISON")
            print("=" * 60)

            bm25_res = all_results["bm25"]
            hybrid_res = all_results["hybrid"]

            # Quality comparison
            print(f"\n🎯 RETRIEVAL QUALITY:")
            print(f"{'Metric':<20} {'BM25':>10} {'Hybrid':>10} {'Improvement':>12}")
            print("-" * 60)

            bm25_prec = bm25_res['recall']['average_precision@10']
            hybrid_prec = hybrid_res['recall']['average_precision@10']
            prec_delta = ((hybrid_prec - bm25_prec) / bm25_prec * 100) if bm25_prec > 0 else 0
            print(f"{'Precision@10':<20} {bm25_prec:>10.3f} {hybrid_prec:>10.3f} {prec_delta:>11.1f}% {'✅' if prec_delta > 0 else '⚠️'}")

            # Performance comparison
            print(f"\n⚡ PERFORMANCE:")
            print(f"{'Metric':<20} {'BM25':>10} {'Hybrid':>10} {'Change':>12}")
            print("-" * 60)

            bm25_p95 = bm25_res['performance']['latency_ms']['p95']
            hybrid_p95 = hybrid_res['performance']['latency_ms']['p95']
            p95_delta = hybrid_p95 - bm25_p95
            print(f"{'p95 latency (ms)':<20} {bm25_p95:>10.1f} {hybrid_p95:>10.1f} {p95_delta:>11.1f} {'⚠️' if p95_delta > 0 else '✅'}")

            bm25_qps = bm25_res['performance']['qps']
            hybrid_qps = hybrid_res['performance']['qps']
            qps_delta = hybrid_qps - bm25_qps
            print(f"{'QPS':<20} {bm25_qps:>10.1f} {hybrid_qps:>10.1f} {qps_delta:>11.1f} {'✅' if qps_delta > 0 else '⚠️'}")

            # Resume bullet
            print("\n" + "=" * 60)
            print("📝 RESUME BULLET POINT:")
            print("=" * 60)
            bullet = (
                f"Implemented hybrid retrieval (Postgres BM25 + vector embeddings) with RRF fusion, "
                f"delivering Precision@10 {bm25_prec:.2f}→{hybrid_prec:.2f} "
                f"({prec_delta:+.0f}pp) at p95 latency ~{hybrid_p95:.0f}ms "
                f"via candidate pruning and local cosine scoring; "
                f"exposed /metrics (p50/p95/p99, QPS) endpoint "
                f"with load tests baselining QPS ~{hybrid_qps:.0f} req/s."
            )
            print(f"\n{bullet}\n")
        else:
            # Single method - print its results
            method = methods_to_run[0]
            result = all_results[method]

            print("\n" + "=" * 60)
            print(f"📈 {method.upper()} RESULTS")
            print("=" * 60)

            print(f"\n🎯 RETRIEVAL QUALITY:")
            print(f"   Precision@10: {result['recall']['average_precision@10']:.3f}")
            print(f"   Recall@10: {result['recall']['average_recall@10']:.3f}")

            print(f"\n⚡ PERFORMANCE:")
            print(f"   p95: {result['performance']['latency_ms']['p95']:.1f} ms")
            print(f"   QPS: {result['performance']['qps']:.1f} req/s")

    finally:
        db.close()


if __name__ == "__main__":
    main()
