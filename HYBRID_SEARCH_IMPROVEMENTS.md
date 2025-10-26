# Hybrid Search Improvements

## Changes Made

### 1. Simplified Query Generation (`recommendations.py`)

**Before:**
```
Query: "Oakland modern suburban spacious welcoming large windows two-car garage front lawn gabled roof porch apartment quiet"
Result: Too complex, BM25 returns 0 results
```

**After:**
```
Query: "Oakland apartment modern quiet"
Result: Focused query, better BM25 matching
```

**How it works:**
- **Priority 1**: Location (Oakland)
- **Priority 2**: Property type (apartment, house, etc.) - max 1-2
- **Priority 3**: Important keywords (modern, quiet) - max 2-3
- **Limit**: Top 5 terms maximum

### 2. Quality Filtering (`hybrid_search.py`)

**Before:** Returns all properties including those without coordinates

**After:** Only returns properties with:
- ✅ Valid latitude/longitude (can be shown on map)
- ✅ Active status (`is_active = True`)

Based on your data:
- Total properties: 114
- With coordinates: 49
- **Quality properties returned: 49** (43% of total)

## Benefits

### Better Matching
- Simplified queries → More BM25 matches
- Example: "Oakland apartment" matches 6 properties vs. 0 with complex query

### Better Quality
- All results have coordinates → Can display on map
- Filters out incomplete data automatically

## Test Commands

### Test simplified query:
```bash
# This should now return results
curl -X GET "http://localhost:8000/api/v1/properties/hybrid-search?q=Oakland+apartment&limit=5" | jq '[.[] | {title, match_score: (.scores.hybrid_rrf * 100 | round)}]'
```

### Test recommendations with auth:
```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/properties?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '[.[] | {title, match_score, has_coords: (.latitude != null)}]'
```

Expected: All results have `has_coords: true`

## Restart to Apply

```bash
docker-compose restart backend
```

Then test at: `http://3.145.189.113/recommendation`

## Query Examples

User preferences → Generated query:
- `preferred_location: Oakland` + prefs `modern, spacious, apartment` → `"Oakland apartment modern"`
- `preferred_location: Shadyside` + prefs `house, quiet, family` → `"Shadyside house quiet"`
- No preferences → `"apartment house"` (default)

Much cleaner and more effective!
