#!/usr/bin/env python3
"""
Compare two benchmark results to show performance improvements.

Usage:
    # Compare baseline vs latest
    python scripts/compare_benchmarks.py benchmark_results/benchmark_baseline.json benchmark_results.json

    # Compare any two benchmarks
    python scripts/compare_benchmarks.py benchmark_results/benchmark_20250127_120000.json benchmark_results/benchmark_20250127_150000.json
"""

import json
import sys
from typing import Dict


def load_benchmark(filepath: str) -> Dict:
    """Load benchmark JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def calculate_delta(before: float, after: float, metric_name: str = "") -> Dict:
    """
    Calculate delta and format improvement.

    Returns:
        {
            'delta': absolute change,
            'delta_pct': percentage change,
            'improved': True/False,
            'symbol': '↑' or '↓'
        }
    """
    delta = after - before
    delta_pct = (delta / before * 100) if before != 0 else 0

    # For latency, lower is better
    latency_metrics = ['p50', 'p95', 'p99', 'mean', 'median']
    is_latency = any(lat in metric_name.lower() for lat in latency_metrics)

    improved = (delta < 0) if is_latency else (delta > 0)
    symbol = '↓' if delta < 0 else '↑'

    return {
        'delta': delta,
        'delta_pct': delta_pct,
        'improved': improved,
        'symbol': symbol
    }


def compare_benchmarks(baseline_path: str, optimized_path: str):
    """Compare two benchmark results and print comparison table."""

    print("=" * 80)
    print("📊 BENCHMARK COMPARISON")
    print("=" * 80)

    baseline = load_benchmark(baseline_path)
    optimized = load_benchmark(optimized_path)

    print(f"\n📌 Baseline:  {baseline.get('timestamp', 'N/A')}")
    print(f"📌 Optimized: {optimized.get('timestamp', 'N/A')}")

    # Environment comparison
    if 'metadata' in baseline and 'metadata' in optimized:
        baseline_meta = baseline['metadata']
        optimized_meta = optimized['metadata']

        # Database size
        baseline_size = baseline_meta.get('database_size', 'N/A')
        optimized_size = optimized_meta.get('database_size', 'N/A')
        print(f"\n📦 Database: {baseline_size} → {optimized_size} properties")

        # Environment check
        baseline_env = baseline_meta.get('environment', {})
        optimized_env = optimized_meta.get('environment', {})

        if baseline_env and optimized_env:
            print(f"\n🖥️  Environment:")
            print(f"   Baseline:  {baseline_env.get('hostname', 'N/A')} | "
                  f"Python {baseline_env.get('python_version', 'N/A')} | "
                  f"{baseline_env.get('cpu_count', 'N/A')} CPUs | "
                  f"{baseline_env.get('memory_gb', 'N/A')} GB RAM")
            print(f"   Optimized: {optimized_env.get('hostname', 'N/A')} | "
                  f"Python {optimized_env.get('python_version', 'N/A')} | "
                  f"{optimized_env.get('cpu_count', 'N/A')} CPUs | "
                  f"{optimized_env.get('memory_gb', 'N/A')} GB RAM")

            # Warn if environments differ
            if (baseline_env.get('hostname') != optimized_env.get('hostname') or
                baseline_env.get('cpu_count') != optimized_env.get('cpu_count')):
                print(f"\n   ⚠️  WARNING: Different environments detected!")
                print(f"   Performance comparison may not be fair.")
                print(f"   Recommendation: Run both benchmarks on same machine.")

    # Retrieval Quality Comparison
    print("\n" + "=" * 80)
    print("🎯 RETRIEVAL QUALITY")
    print("=" * 80)

    baseline_recall = baseline['recall']
    optimized_recall = optimized['recall']

    # Average metrics
    metrics = [
        ('Recall@10', baseline_recall['average_recall@10'], optimized_recall['average_recall@10']),
        ('Precision@10', baseline_recall['average_precision@10'], optimized_recall['average_precision@10'])
    ]

    print(f"\n{'Metric':<20} {'Baseline':>10} {'Optimized':>10} {'Change':>15}")
    print("-" * 80)

    for metric_name, baseline_val, optimized_val in metrics:
        delta_info = calculate_delta(baseline_val, optimized_val, metric_name)
        change_str = f"{delta_info['symbol']}{abs(delta_info['delta_pct']):.1f}%"
        color = "✅" if delta_info['improved'] else "⚠️"

        print(f"{metric_name:<20} {baseline_val:>10.3f} {optimized_val:>10.3f} {change_str:>12} {color}")

    # Performance Comparison
    print("\n" + "=" * 80)
    print("⚡ PERFORMANCE")
    print("=" * 80)

    baseline_perf = baseline['performance']
    optimized_perf = optimized['performance']

    perf_metrics = [
        ('QPS', baseline_perf['qps'], optimized_perf['qps']),
        ('p50 latency (ms)', baseline_perf['latency_ms']['p50'], optimized_perf['latency_ms']['p50']),
        ('p95 latency (ms)', baseline_perf['latency_ms']['p95'], optimized_perf['latency_ms']['p95']),
        ('p99 latency (ms)', baseline_perf['latency_ms']['p99'], optimized_perf['latency_ms']['p99'])
    ]

    print(f"\n{'Metric':<20} {'Baseline':>10} {'Optimized':>10} {'Change':>15}")
    print("-" * 80)

    for metric_name, baseline_val, optimized_val in perf_metrics:
        delta_info = calculate_delta(baseline_val, optimized_val, metric_name)
        change_str = f"{delta_info['symbol']}{abs(delta_info['delta']):.1f}"
        color = "✅" if delta_info['improved'] else "⚠️"

        print(f"{metric_name:<20} {baseline_val:>10.1f} {optimized_val:>10.1f} {change_str:>12} {color}")

    # Generate Resume Bullet Point
    print("\n" + "=" * 80)
    print("📝 RESUME BULLET POINT")
    print("=" * 80)

    recall_delta = calculate_delta(
        baseline_recall['average_recall@10'],
        optimized_recall['average_recall@10']
    )

    precision_delta = calculate_delta(
        baseline_recall['average_precision@10'],
        optimized_recall['average_precision@10']
    )

    p95_delta = calculate_delta(
        baseline_perf['latency_ms']['p95'],
        optimized_perf['latency_ms']['p95'],
        'p95'
    )

    qps_delta = calculate_delta(
        baseline_perf['qps'],
        optimized_perf['qps']
    )

    bullet = f"""
Implemented hybrid retrieval (Postgres BM25 + vector embeddings) with RRF fusion,
delivering Precision@10 {baseline_recall['average_precision@10']:.2f}→{optimized_recall['average_precision@10']:.2f}
(+{precision_delta['delta_pct']:.0f}pp) while cutting p95 latency ↓{abs(p95_delta['delta']):.0f} ms
via candidate pruning and local cosine scoring; exposed /metrics (p50/p95/p99, QPS)
and added LRU caching, with load tests baselining QPS ~{optimized_perf['qps']:.0f} req/s
and p95 ~{optimized_perf['latency_ms']['p95']:.0f} ms.
    """.strip()

    print(f"\n{bullet}\n")

    # Summary
    print("=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    print(f"Precision@10: {precision_delta['symbol']}{abs(precision_delta['delta_pct']):.1f}% {'✅ IMPROVED' if precision_delta['improved'] else '⚠️ DEGRADED'}")
    print(f"p95 Latency:  {p95_delta['symbol']}{abs(p95_delta['delta']):.1f} ms {'✅ IMPROVED' if p95_delta['improved'] else '⚠️ DEGRADED'}")
    print(f"QPS:          {qps_delta['symbol']}{abs(qps_delta['delta']):.1f} req/s {'✅ IMPROVED' if qps_delta['improved'] else '⚠️ DEGRADED'}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_benchmarks.py <baseline.json> <optimized.json>")
        print("\nExample:")
        print("  python scripts/compare_benchmarks.py \\")
        print("    benchmark_results/benchmark_baseline.json \\")
        print("    benchmark_results.json")
        sys.exit(1)

    baseline_path = sys.argv[1]
    optimized_path = sys.argv[2]

    compare_benchmarks(baseline_path, optimized_path)


if __name__ == "__main__":
    main()
