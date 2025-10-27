# Scripts Directory - UniNest Backend

## Overview

This directory contains utility scripts for testing, benchmarking, and maintaining the UniNest backend search and recommendation system.

---

## Scripts Description

### 1. `populate_search_vectors.py`
**Purpose**: Rebuild BM25 full-text search index for all properties

**What it does**:
- Updates the `search_vector` column for all properties
- Indexes title, description, and extended_description (AI keywords)
- Required after enrichment or database changes

**When to run**:
- After fetching new properties with AI enrichment
- After updating the search_vector trigger
- When BM25 search returns no results

**Usage**:
```bash
cd backend
source venv/bin/activate
python3 scripts/populate_search_vectors.py
```

**Output**:
- Total properties with search_vector populated
- Sample BM25 query test results

---

### 2. `diagnose_bm25.py`
**Purpose**: Verify BM25 full-text search is working correctly

**What it does**:
- Checks if `search_vector` column exists and is populated
- Verifies GIN index exists
- Tests sample queries (apartment, house, Oakland, parking)
- Shows sample search_vector content

**When to run**:
- When debugging "No BM25 results found" warnings
- After running populate_search_vectors.py
- To verify search configuration

**Usage**:
```bash
python3 scripts/diagnose_bm25.py
```

**Output**:
- ✅ Status of search_vector column, index, and sample queries
- Sample property content with search_vector data

---

### 3. `precompute_embeddings.py`
**Purpose**: Pre-generate vector embeddings for all properties

**What it does**:
- Generates embeddings for properties without them
- Uses sentence-transformers (all-MiniLM-L6-v2 model)
- Stores embeddings in the database for fast vector search

**When to run**:
- After fetching new properties
- Before running benchmarks
- When vector search is slow (no pre-computed embeddings)

**Usage**:
```bash
python3 scripts/precompute_embeddings.py
```

**Output**:
- Count of properties with/without embeddings
- Progress updates as embeddings are generated

---

### 4. `benchmark_hybrid_search.py`
**Purpose**: Comprehensive benchmark of hybrid search quality and performance

**What it does**:
- Measures **Recall@10** (search quality metric)
- Measures **latency** (p50, p95, p99)
- Measures **QPS** (queries per second)
- Tests multiple search queries
- Generates resume-ready performance bullet point

**When to run**:
- After completing setup (populate + precompute)
- To measure search performance for documentation
- To compare before/after optimization

**Usage**:
```bash
python3 scripts/benchmark_hybrid_search.py
```

**Output**:
- Recall@10 scores per query
- Latency percentiles
- QPS (throughput)
- Resume bullet point
- Results saved to `benchmark_results.json`

---

### 5. `load_test_recommendations.py`
**Purpose**: HTTP load test for `/recommendations/properties` endpoint

**What it does**:
- Sends concurrent HTTP requests to the recommendations API
- Measures real-world API performance
- Tests with authentication (requires JWT token)
- Reports QPS and latency from /metrics endpoint

**When to run**:
- After benchmark_hybrid_search.py
- To test API performance under load
- Before production deployment

**Usage**:
```bash
# 1. Get auth token (login as tenant)
export AUTH_TOKEN="your_jwt_token"

# 2. Run load test
python3 scripts/load_test_recommendations.py
```

**Output**:
- QPS from /metrics endpoint
- p50/p95/p99 latencies
- Results saved to `load_test_results.json`

---

### 6. `load_test_metrics.py`
**Purpose**: Test the /metrics endpoint availability

**What it does**:
- Verifies Prometheus metrics endpoint is accessible
- Checks metric format and availability
- Tests without authentication

**When to run**:
- To verify metrics monitoring is working
- Before setting up Prometheus/Grafana
- When debugging metrics issues

**Usage**:
```bash
python3 scripts/load_test_metrics.py
```

**Output**:
- Metrics endpoint status
- Sample metrics data

---

## Recommended Workflow

### After Fetching New Properties

Run scripts in this order:

```bash
# 1. Rebuild BM25 search index
python3 scripts/populate_search_vectors.py

# 2. Verify BM25 is working
python3 scripts/diagnose_bm25.py

# 3. Pre-generate vector embeddings (optional but recommended)
python3 scripts/precompute_embeddings.py

# 4. Benchmark search performance
python3 scripts/benchmark_hybrid_search.py

# 5. (Optional) Load test API endpoint
export AUTH_TOKEN="your_token"
python3 scripts/load_test_recommendations.py
```

---

## Quick Reference

| Script | Required After Fetch? | Requires Auth? | Output File |
|--------|----------------------|----------------|-------------|
| `populate_search_vectors.py` | ✅ Yes | ❌ No | None |
| `diagnose_bm25.py` | ✅ Yes (verification) | ❌ No | None |
| `precompute_embeddings.py` | ⚠️ Recommended | ❌ No | None |
| `benchmark_hybrid_search.py` | ⚠️ Recommended | ❌ No | `benchmark_results.json` |
| `load_test_recommendations.py` | ❌ Optional | ✅ Yes | `load_test_results.json` |
| `load_test_metrics.py` | ❌ Optional | ❌ No | None |

---

## Troubleshooting

### "No BM25 results found"
1. Run `diagnose_bm25.py` to check status
2. Run `populate_search_vectors.py` to rebuild index
3. Verify trigger includes extended_description

### Low Recall@10 scores
- Verify embeddings: `SELECT COUNT(*) FROM properties WHERE embedding IS NOT NULL;`
- Check test queries match your data
- Review AI enrichment quality

### High latency
- Run `precompute_embeddings.py` (vector search is slow without them)
- Test on production-grade hardware (not dev laptop)
- Consider caching

### 401 Unauthorized (load test)
- Login as tenant user to get JWT token
- Set: `export AUTH_TOKEN="your_token"`
- Token expires after 30 days

---

## Performance Targets

**Good benchmarks for a housing search system:**

- **Recall@10**: > 0.70 (70% of relevant properties found)
- **p50 latency**: < 50ms
- **p95 latency**: < 150ms
- **p99 latency**: < 300ms
- **QPS**: > 50 (single-threaded), > 200 (production)

---

## For Resume/Documentation

After running benchmarks, use the auto-generated bullet point from `benchmark_hybrid_search.py`:

```
Implemented hybrid retrieval (Postgres BM25 + vector embeddings) with RRF fusion,
delivering Recall@10 [X.XX] while achieving p95 latency [X] ms via candidate
pruning and local cosine scoring; exposed /metrics (p50/p95/p99, QPS) endpoint
with load tests baselining QPS ~[X] and p95 ~[X] ms.
```

---

## Notes

- All scripts use the backend virtual environment
- Must activate venv before running: `source venv/bin/activate`
- Scripts connect to local database (use SSH tunnel for EC2)
- Results are saved in backend/ directory (add to .gitignore)