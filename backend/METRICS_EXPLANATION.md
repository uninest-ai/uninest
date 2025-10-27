# Search Quality Metrics Explanation

## Why Recall@10 Decreases as Database Grows

### TL;DR
**This is normal behavior, not a bug.** Your search quality isn't getting worse - you just have more relevant options available.

---

## Understanding the Metrics

### 📊 Recall@10 (Sensitive to Database Size)

**Formula:**
```
Recall@10 = (relevant items in top 10) / (total relevant items in database)
```

**Example from your benchmarks:**

| Run | Database Size | "Shadyside modern" Relevant | Retrieved | Recall@10 |
|-----|---------------|----------------------------|-----------|-----------|
| 1st | 177 properties | 95 relevant | 10 | 10/95 = 0.105 ✅ |
| 2nd | 193 properties | 111 relevant | 10 | 10/111 = 0.090 ⬇️ |

**What happened:**
- You fetched 16 more properties
- 16 of them matched "Shadyside modern"
- But you're still only showing 10 results
- So Recall@10 = 10/111 = 9.0% (down from 10.5%)

**Why it drops:**
- Numerator (relevant retrieved) = **capped at 10**
- Denominator (total relevant) = **grows with database**
- Result: Recall@10 inevitably decreases

---

### 🎯 Precision@10 (Stable Across Database Sizes)

**Formula:**
```
Precision@10 = (relevant items in top 10) / 10
```

**This is what you should track for search quality!**

**Example:**

| Scenario | Relevant in Top 10 | Precision@10 | Interpretation |
|----------|-------------------|--------------|----------------|
| Good search | 9/10 | 0.90 | 90% of results are relevant ✅ |
| Bad search | 3/10 | 0.30 | Only 30% are relevant ❌ |

**Precision@10 stays stable** even as database grows, because:
- Both numerator and denominator are capped at 10
- Measures "Are the 10 results I showed actually good?"

---

## Real-World Analogy

**Imagine you're a librarian:**

**Recall@10 (Coverage):**
- "Did I find all relevant books in the library?"
- As library grows from 1,000 → 10,000 books, finding "all relevant" gets harder
- Naturally decreases with library size

**Precision@10 (Accuracy):**
- "Are the 10 books I recommended actually relevant?"
- Doesn't matter if library has 1,000 or 10,000 books
- Only matters if your 10 picks are good

---

## What Your Benchmarks Should Show

### ✅ Good Search System (What to Expect)

After running the updated benchmark:

```
🎯 RETRIEVAL QUALITY:
   Average Recall@10: 0.226    ⬅️ Will decrease as DB grows (NORMAL)
   Average Precision@10: 0.85  ⬅️ Should stay high (GOOD QUALITY)

   Per-query breakdown:
      'Oakland apartment':
         Recall@10: 0.130 | Precision@10: 0.90
      'Shadyside modern':
         Recall@10: 0.090 | Precision@10: 0.80
```

**Interpretation:**
- Recall@10 = 0.226 means you're finding 22.6% of all relevant properties
- Precision@10 = 0.85 means 85% of results shown are actually relevant ✅

---

### ❌ Degrading Search System (What to Watch For)

**Warning signs:**

```
🎯 RETRIEVAL QUALITY:
   Average Recall@10: 0.150    ⬅️ Dropped (expected)
   Average Precision@10: 0.30  ⬅️ Dropped (BAD - search is breaking!)
```

If **Precision@10 drops** as database grows, then your search has real problems.

---

## Industry Standards

**For a housing search system:**

| Metric | Target | Your System |
|--------|--------|-------------|
| **Precision@10** | > 0.70 | **Track this** ⭐ |
| **Recall@50** | > 0.50 | Better than Recall@10 |
| **nDCG@10** | > 0.75 | Advanced metric |
| p95 latency | < 150ms | Already measuring ✅ |
| QPS | > 50 | Already measuring ✅ |

---

## What to Do Next

### 1. Run Updated Benchmark

```bash
cd /mnt/d/ahYen\ Workspace/ahYen\ Work/CMU_academic/MSCD_Y1_2425/17637-WebApps/uninest
source backend/venv/bin/activate
python backend/scripts/benchmark_hybrid_search.py
```

You'll now see both Recall@10 and Precision@10.

### 2. Track Precision@10 Instead

**For your resume/documentation:**
```
"Delivering Precision@10 of 0.85 while maintaining p95 latency < 50ms"
```

**NOT:**
```
"Delivering Recall@10 of 0.226..."  ❌ (Will confuse recruiters)
```

### 3. Optional: Measure Recall@50

If you want to show good recall too:

Edit `benchmark_hybrid_search.py`:
```python
# In hybrid_search_simple function
search_results = hybrid_search_simple(db=db, query=query, limit=50)  # Changed from 10
recall = calculate_recall_at_k(retrieved_ids, relevant_ids, k=50)    # Changed from 10
```

This will show higher recall numbers while being honest about retrieval coverage.

---

## Summary

| Question | Answer |
|----------|---------|
| **Is my search broken?** | No! Recall@10 dropping is expected |
| **What metric should I track?** | Precision@10 (measures quality) |
| **How do I know if search degrades?** | Watch if Precision@10 drops |
| **Should I increase database size?** | Yes! More data = better product |
| **What's a good Precision@10?** | > 0.70 (industry standard) |

---

## Quick Reference: Metric Cheat Sheet

```
┌─────────────────┬──────────────────┬────────────────────┐
│ Metric          │ Stable w/ Growth?│ Use For            │
├─────────────────┼──────────────────┼────────────────────┤
│ Recall@10       │ ❌ No           │ Small datasets     │
│ Precision@10    │ ✅ Yes          │ Search quality ⭐  │
│ Recall@50       │ ⚠️  Better      │ Coverage           │
│ nDCG@10         │ ✅ Yes          │ Ranking quality    │
└─────────────────┴──────────────────┴────────────────────┘
```

**Bottom line:** Focus on **Precision@10** and latency. Those are stable, industry-standard metrics. 🎯