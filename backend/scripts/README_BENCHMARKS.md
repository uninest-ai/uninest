# Hybrid Search Benchmarking Guide

## Overview

Two benchmarking scripts are available to measure the performance of the hybrid search system:

1. **benchmark_hybrid_search.py** - Comprehensive benchmark (requires DB access)
2. **load_test_recommendations.py** - Simple HTTP load test (no DB required)

## Quick Start

### Option 1: Full Benchmark (Recommended)

Measures both **retrieval quality** (Recall@10) and **performance** (latency, QPS).

```bash
# Make sure backend is running
cd /path/to/backend

# Run comprehensive benchmark
python scripts/benchmark_hybrid_search.py
```

**Output includes:**
- ✅ Recall@10 (average and per-query)
- ✅ Latency percentiles (p50, p95, p99)
- ✅ QPS (queries per second)
- ✅ Resume-ready bullet point
- ✅ Results saved to `benchmark_results.json`

---

### Option 2: HTTP Load Test (Simple)

Tests the `/recommendations/properties` endpoint via HTTP.

```bash
# 1. Start backend
docker-compose up -d

# 2. Get auth token (login as tenant user)
# Visit http://localhost:8000/docs and use /auth/login
# Copy the access_token

# 3. Set token and run test
export AUTH_TOKEN="your_jwt_token_here"
python scripts/load_test_recommendations.py
```

**Output includes:**
- ✅ QPS from /metrics endpoint
- ✅ p50/p95/p99 latencies
- ✅ Results saved to `load_test_results.json`

---

## Understanding the Metrics

### Recall@10
**What it is:** Percentage of relevant properties found in top 10 results

**Interpretation:**
- `0.80` (80%) = Good - Most relevant properties are found
- `0.60` (60%) = Acceptable - Room for improvement
- `< 0.50` = Poor - Search quality needs work

**Example:**
- Query: "Oakland apartment"
- 20 truly relevant properties exist
- Search returns 16 of them in top 10
- Recall@10 = 16/20 = 0.80

### Latency Percentiles

- **p50 (median):** 50% of requests are faster than this
- **p95:** 95% of requests are faster than this (common SLA target)
- **p99:** 99% of requests are faster than this (catches outliers)

**Good targets for search:**
- p50: < 50 ms
- p95: < 150 ms
- p99: < 300 ms

### QPS (Queries Per Second)

Throughput metric - how many queries the system can handle per second.

**Typical ranges:**
- Single-threaded: 10-50 QPS
- Multi-threaded: 50-200 QPS
- Production systems: 200+ QPS

---

## What to Put on Resume

After running the benchmark, use the auto-generated bullet point:

```
Implemented hybrid retrieval (Postgres BM25 + vector embeddings) with RRF fusion,
delivering Recall@10 [X.XX] while achieving p95 latency [X] ms via candidate
pruning and local cosine scoring; exposed /metrics (p50/p95/p99, QPS) endpoint
with load tests baselining QPS ~[X] and p95 ~[X] ms.
```

**Example:**
```
Implemented hybrid retrieval (Postgres BM25 + vector embeddings) with RRF fusion,
delivering Recall@10 0.78 while achieving p95 latency 142 ms via candidate
pruning and local cosine scoring; exposed /metrics (p50/p95/p99, QPS) endpoint
with load tests baselining QPS ~87 and p95 ~142 ms.
```

---

## Comparing Before/After Optimizations

To show improvement, run benchmarks before and after optimization:

### Step 1: Baseline (Before)
```bash
# Run benchmark with current code
python scripts/benchmark_hybrid_search.py

# Save results
mv benchmark_results.json benchmark_baseline.json
```

### Step 2: Make Optimization
```python
# Example: Add caching, improve query parsing, etc.
```

### Step 3: After
```bash
# Run benchmark again
python scripts/benchmark_hybrid_search.py

# Compare results
python scripts/compare_benchmarks.py benchmark_baseline.json benchmark_results.json
```

### Step 4: Resume Bullet
```
Implemented hybrid retrieval with RRF fusion, improving Recall@10 [0.65→0.78] (+13pp)
while cutting p95 latency ↓45ms via candidate pruning; exposed /metrics endpoint
with load tests baselining QPS ~87 and p95 ~142ms.
```

---

## Advanced: Custom Test Queries

Edit `benchmark_hybrid_search.py` to add your own test queries:

```python
TEST_QUERIES = [
    {
        "query": "your custom query",
        "expected_keywords": ["keyword1", "keyword2"],
        "description": "What this query tests"
    },
    # Add more...
]
```

---

## Troubleshooting

### "No properties in database"
```bash
# Fetch properties first
curl -X POST http://3.145.189.113:8000/admin/fetch-properties \
    -H "X-Admin-Key: Admin123456"
```

### "401 Unauthorized" in HTTP load test
```bash
# Make sure you're logged in and have valid token
export AUTH_TOKEN="your_token_here"
```

### Low Recall scores
- Check if embeddings are precomputed: `SELECT COUNT(*) FROM properties WHERE embedding IS NOT NULL;`
- Verify test queries match your data: adjust TEST_QUERIES
- Improve search query generation in recommendations.py

### High latency
- Check if embeddings are precomputed (vector search is slow without them)
- Run on production-grade hardware (not dev laptop)
- Consider caching frequently accessed results

---

## Files Generated

- `benchmark_results.json` - Full benchmark results
- `load_test_results.json` - HTTP load test results

Both contain timestamp, metrics, and can be used for historical comparison.