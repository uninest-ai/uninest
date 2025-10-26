#!/bin/bash
# Test recommendations endpoint to verify it's using hybrid search

echo "=========================================="
echo "Testing Recommendations Endpoint"
echo "=========================================="
echo ""

# Test if you have a valid auth token
echo "1. Testing with authentication..."
echo ""

# You need to replace this with a real token from localStorage
TOKEN="Bearer YOUR_TOKEN_HERE"

echo "Endpoint: http://localhost:8000/api/v1/recommendations/properties?limit=3"
echo ""

curl -X GET "http://localhost:8000/api/v1/recommendations/properties?limit=3" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" | jq '.[0] | {id, title, description: (.description | .[0:100]), match_score}'

echo ""
echo "=========================================="
echo "Check if:"
echo "1. Description shows real property data (not fake/fallback)"
echo "2. match_score is around 3% (not 1-2%)"
echo "3. If you get 401 error, update the TOKEN variable above"
echo "=========================================="