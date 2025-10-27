#!/usr/bin/env python3
"""
Diagnostic script to check BM25 search configuration.

This will help identify why BM25 is returning 0 results.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text, inspect
from app.database import SessionLocal
from app.models import Property


def check_search_vector_column(db):
    """Check if search_vector column exists."""
    print("\n" + "=" * 60)
    print("1. Checking if search_vector column exists...")
    print("=" * 60)

    try:
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('properties')]

        if 'search_vector' in columns:
            print("✅ search_vector column EXISTS")
            return True
        else:
            print("❌ search_vector column MISSING")
            print("\n   The migration may not have been run.")
            print("   Run: alembic upgrade head")
            return False
    except Exception as e:
        print(f"❌ Error checking column: {e}")
        return False


def check_search_vector_populated(db):
    """Check if search_vector is populated."""
    print("\n" + "=" * 60)
    print("2. Checking if search_vector is populated...")
    print("=" * 60)

    try:
        # Count properties with NULL search_vector
        result = db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(search_vector) as populated,
                COUNT(*) - COUNT(search_vector) as null_count
            FROM properties
        """))

        row = result.fetchone()
        total = row.total
        populated = row.populated
        null_count = row.null_count

        print(f"   Total properties: {total}")
        print(f"   Populated search_vector: {populated}")
        print(f"   NULL search_vector: {null_count}")

        if null_count > 0:
            print(f"\n⚠️  WARNING: {null_count} properties have NULL search_vector")
            print("   BM25 search will not find these properties!")
            return False
        else:
            print("✅ All properties have search_vector populated")
            return True

    except Exception as e:
        print(f"❌ Error checking population: {e}")
        return False


def check_gin_index(db):
    """Check if GIN index exists."""
    print("\n" + "=" * 60)
    print("3. Checking if GIN index exists...")
    print("=" * 60)

    try:
        result = db.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'properties'
                AND indexname LIKE '%search_vector%'
        """))

        indexes = result.fetchall()

        if indexes:
            print("✅ GIN index found:")
            for idx in indexes:
                print(f"   - {idx.indexname}")
            return True
        else:
            print("⚠️  No GIN index found for search_vector")
            print("   Search will be slow but should still work")
            return False

    except Exception as e:
        print(f"❌ Error checking index: {e}")
        return False


def sample_search_vectors(db):
    """Show sample search_vector content."""
    print("\n" + "=" * 60)
    print("4. Sample search_vector content...")
    print("=" * 60)

    try:
        result = db.execute(text("""
            SELECT
                id,
                title,
                LEFT(description, 50) as description_preview,
                search_vector::text as search_vector_text
            FROM properties
            WHERE search_vector IS NOT NULL
            LIMIT 3
        """))

        rows = result.fetchall()

        if not rows:
            print("❌ No properties with search_vector found")
            return

        for row in rows:
            print(f"\nProperty ID {row.id}:")
            print(f"   Title: {row.title}")
            print(f"   Description: {row.description_preview}...")
            print(f"   Search Vector: {row.search_vector_text[:100]}...")

    except Exception as e:
        print(f"❌ Error sampling search vectors: {e}")


def test_bm25_queries(db):
    """Test BM25 with sample queries."""
    print("\n" + "=" * 60)
    print("5. Testing BM25 with sample queries...")
    print("=" * 60)

    test_queries = [
        "apartment",
        "house",
        "Oakland",
        "parking",
    ]

    for query in test_queries:
        try:
            result = db.execute(text("""
                SELECT COUNT(*) as match_count
                FROM properties
                WHERE search_vector @@ plainto_tsquery('english', :query)
            """), {"query": query})

            count = result.scalar()
            status = "✅" if count > 0 else "❌"
            print(f"   {status} '{query}': {count} matches")

        except Exception as e:
            print(f"   ❌ '{query}': Error - {e}")


def check_sample_property_content(db):
    """Check actual content of properties."""
    print("\n" + "=" * 60)
    print("6. Sample property content (title + description)...")
    print("=" * 60)

    try:
        result = db.execute(text("""
            SELECT
                id,
                title,
                description,
                COALESCE(title, '') || ' ' || COALESCE(description, '') as combined_text
            FROM properties
            WHERE is_active = true
            LIMIT 5
        """))

        rows = result.fetchall()

        for row in rows:
            print(f"\nProperty ID {row.id}:")
            print(f"   Title: {row.title}")
            print(f"   Description: {row.description[:100] if row.description else 'NULL'}...")
            print(f"   Combined length: {len(row.combined_text)} chars")

            if len(row.combined_text.strip()) < 10:
                print("   ⚠️  WARNING: Very little text content!")

    except Exception as e:
        print(f"❌ Error checking content: {e}")


def main():
    print("=" * 60)
    print("🔍 BM25 SEARCH DIAGNOSTICS")
    print("=" * 60)

    db = SessionLocal()

    try:
        has_column = check_search_vector_column(db)

        if not has_column:
            print("\n" + "=" * 60)
            print("DIAGNOSIS: Migration not run")
            print("=" * 60)
            print("\nFIX:")
            print("   1. cd /home/ec2-user/uninest/backend")
            print("   2. alembic upgrade head")
            print("   3. Restart backend: docker-compose restart backend")
            return

        is_populated = check_search_vector_populated(db)
        has_index = check_gin_index(db)

        sample_search_vectors(db)
        check_sample_property_content(db)
        test_bm25_queries(db)

        # Final diagnosis
        print("\n" + "=" * 60)
        print("📋 DIAGNOSIS SUMMARY")
        print("=" * 60)

        if not is_populated:
            print("\n❌ PROBLEM: search_vector not populated")
            print("\nFIX: Run the populate script:")
            print("   python scripts/populate_search_vectors.py")

        elif has_column and is_populated and has_index:
            print("\n✅ BM25 configuration looks good!")
            print("\nIf you're still seeing 'No BM25 results', check:")
            print("   1. Property content quality (title + description)")
            print("   2. Query terms match property content")
            print("   3. min_score threshold in hybrid_search.py")

        else:
            print("\n⚠️  Partial configuration - review issues above")

    finally:
        db.close()


if __name__ == "__main__":
    main()