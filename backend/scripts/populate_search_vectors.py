#!/usr/bin/env python3
"""
Populate search_vector column for all properties.

This script manually updates the search_vector column if:
1. The migration was run but search_vector is NULL
2. Properties were added before the trigger was created
3. You want to rebuild the search index

Usage:
    python scripts/populate_search_vectors.py
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import SessionLocal


def populate_search_vectors(force: bool = False):
    """Populate search_vector for all properties."""
    print("=" * 60)
    print("🔄 POPULATING SEARCH VECTORS")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Check current state
        print("\n1. Checking current state...")
        result = db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(search_vector) as populated,
                COUNT(*) - COUNT(search_vector) as null_count
            FROM properties
        """))

        row = result.fetchone()
        total = row.total
        before_populated = row.populated
        before_null = row.null_count

        print(f"   Total properties: {total}")
        print(f"   Currently populated: {before_populated}")
        print(f"   Currently NULL: {before_null}")

        if before_null == 0 and not force:
            print("\n✅ All properties already have search_vector populated!")
            print("   Use --force to rebuild the search index anyway.")
            return

        # Populate search_vector
        if force:
            print("\n2. Force-rebuilding search_vector for all properties...")
        else:
            print(f"\n2. Populating search_vector for {before_null} properties...")

        # Include both description AND extended_description for maximum searchability
        # This ensures AI-generated keywords are searchable
        update_sql = """
            UPDATE properties
            SET search_vector =
                setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(extended_description, '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(address, '')), 'C') ||
                setweight(to_tsvector('english', COALESCE(city, '')), 'C')
        """
        if not force:
            update_sql += "\n            WHERE search_vector IS NULL"

        db.execute(text(update_sql))

        db.commit()
        print("   ✅ Update executed")

        # Verify results
        print("\n3. Verifying results...")
        result = db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(search_vector) as populated,
                COUNT(*) - COUNT(search_vector) as null_count
            FROM properties
        """))

        row = result.fetchone()
        after_populated = row.populated
        after_null = row.null_count

        print(f"   Total properties: {total}")
        print(f"   Now populated: {after_populated}")
        print(f"   Still NULL: {after_null}")

        print("\n" + "=" * 60)
        print("✅ COMPLETED")
        print("=" * 60)
        updated_count = after_populated - before_populated if not force else after_populated
        print(f"   Updated: {updated_count} properties")

        if after_null == 0:
            print("\n🎉 Success! All properties now have search_vector populated.")
            print("   BM25 search should now work correctly.")
        else:
            print(f"\n⚠️  Warning: {after_null} properties still have NULL search_vector")
            print("   This may be because they have no text content.")

        # Test a sample query
        print("\n4. Testing BM25 search...")
        result = db.execute(text("""
            SELECT COUNT(*) as match_count
            FROM properties
            WHERE search_vector @@ plainto_tsquery('english', 'apartment')
        """))

        count = result.scalar()
        print(f"   Query 'apartment': {count} matches")

        if count > 0:
            print("   ✅ BM25 search is working!")
        else:
            print("   ⚠️  No matches found - check property content quality")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Populate or rebuild properties.search_vector values")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild search_vector for all properties even if already populated"
    )
    args = parser.parse_args()

    populate_search_vectors(force=args.force)

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Run diagnostics to verify: python scripts/diagnose_bm25.py")
    print("2. Run benchmark again: python scripts/benchmark_hybrid_search.py")


if __name__ == "__main__":
    main()
