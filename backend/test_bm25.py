"""
Test script for BM25 search functionality
Run this inside the Docker container: docker-compose exec backend python test_bm25.py
"""

from app.database import SessionLocal
from app.services.search_service import bm25_search_properties, test_bm25_search

def main():
    db = SessionLocal()

    try:
        # Test queries
        test_queries = [
            "apartment",
            "spacious bedroom",
            "modern kitchen",
            "near campus",
            "parking garage"
        ]

        print("\n" + "="*70)
        print("BM25 SEARCH FUNCTION TEST")
        print("="*70)

        for query in test_queries:
            print(f"\n{'='*70}")
            print(f"Query: '{query}'")
            print(f"{'='*70}")

            results = bm25_search_properties(db, query, limit=5)

            if not results:
                print("❌ No results found.")
                continue

            print(f"✅ Found {len(results)} results:\n")

            for i, (prop, score) in enumerate(results, 1):
                print(f"{i}. {prop.title}")
                print(f"   ID: {prop.id} | Score: {score:.4f} | Price: ${prop.price}")
                print(f"   Description: {prop.description[:80]}...")
                print()

        # Test with min_score threshold
        print(f"\n{'='*70}")
        print("Testing with min_score=0.1")
        print(f"{'='*70}")
        results = bm25_search_properties(db, "apartment", limit=10, min_score=0.1)
        print(f"Results with score >= 0.1: {len(results)} properties")

        # Test IDs only function
        from app.services.search_service import bm25_search_properties_ids_only
        print(f"\n{'='*70}")
        print("Testing bm25_search_properties_ids_only()")
        print(f"{'='*70}")
        ids_with_scores = bm25_search_properties_ids_only(db, "bedroom", limit=5)
        print(f"Results: {ids_with_scores}")

        print(f"\n{'='*70}")
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
