#!/usr/bin/env python3
"""
Print recently added properties from the database.

Usage:
    python scripts/print_properties.py
    python scripts/print_properties.py --limit 20 --city "New York"
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from app.database import SessionLocal
from app.models import Property
from datetime import datetime, timedelta
from sqlalchemy import desc

def print_properties(limit: int = 10, city: str = None, recent_hours: int = None):
    """
    Print properties from the database.

    Args:
        limit: Number of properties to display
        city: Filter by city name
        recent_hours: Only show properties added in the last N hours
    """
    db = SessionLocal()

    try:
        print("=" * 80)
        print("🏠 PROPERTY LISTING")
        print("=" * 80)

        # Build query
        query = db.query(Property).filter(Property.is_active == True)

        if city:
            query = query.filter(Property.city.ilike(f"%{city}%"))

        if recent_hours:
            cutoff_time = datetime.utcnow() - timedelta(hours=recent_hours)
            query = query.filter(Property.created_at >= cutoff_time)

        # Order by most recent first
        query = query.order_by(desc(Property.created_at))

        properties = query.limit(limit).all()

        if not properties:
            print(f"\n❌ No properties found matching criteria")
            if city:
                print(f"   City filter: {city}")
            if recent_hours:
                print(f"   Added in last {recent_hours} hours")
            return

        print(f"\nFound {len(properties)} properties")
        if city:
            print(f"Filtered by city: {city}")
        if recent_hours:
            print(f"Added in last {recent_hours} hours")
        print("-" * 80)

        for i, prop in enumerate(properties, 1):
            print(f"\n[{i}] Property ID: {prop.id}")
            print(f"    Title: {prop.title or 'N/A'}")
            print(f"    Price: ${prop.price}/month")
            print(f"    Type: {prop.property_type or 'N/A'}")
            print(f"    Beds/Baths: {prop.bedrooms or '?'} BR / {prop.bathrooms or '?'} BA")
            print(f"    Address: {prop.address or 'N/A'}")
            print(f"    City: {prop.city or 'N/A'}")

            if prop.latitude and prop.longitude:
                print(f"    Coordinates: ({prop.latitude:.4f}, {prop.longitude:.4f})")
            else:
                print(f"    Coordinates: ❌ Missing")

            if prop.description:
                desc_preview = prop.description[:100] + "..." if len(prop.description) > 100 else prop.description
                print(f"    Description: {desc_preview}")

            if prop.created_at:
                print(f"    Created: {prop.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

            # Check for embedding
            from sqlalchemy import text
            embedding_result = db.execute(
                text("SELECT id FROM property_embeddings WHERE id = :prop_id"),
                {"prop_id": prop.id}
            ).fetchone()
            has_embedding = embedding_result is not None
            print(f"    Vector Embedding: {'✅ Present' if has_embedding else '❌ Missing'}")

        print("\n" + "=" * 80)
        print(f"Total properties shown: {len(properties)}")

        # Get total count with filters
        total_count = query.count() if limit < 1000 else len(properties)
        if total_count > len(properties):
            print(f"Total matching properties in DB: {total_count}")

        print("=" * 80)

    finally:
        db.close()


def print_city_statistics():
    """Print statistics grouped by city."""
    db = SessionLocal()

    try:
        print("\n" + "=" * 80)
        print("📊 PROPERTIES BY CITY")
        print("=" * 80)

        from sqlalchemy import func

        # Group by city
        city_stats = db.query(
            Property.city,
            func.count(Property.id).label('count'),
            func.avg(Property.price).label('avg_price'),
            func.min(Property.price).label('min_price'),
            func.max(Property.price).label('max_price')
        ).filter(
            Property.is_active == True
        ).group_by(
            Property.city
        ).order_by(
            desc('count')
        ).all()

        if not city_stats:
            print("\n❌ No properties found")
            return

        print(f"\n{'City':<20} {'Count':>8} {'Avg Price':>12} {'Min':>10} {'Max':>10}")
        print("-" * 80)

        for stat in city_stats:
            city_name = stat.city or "Unknown"
            print(
                f"{city_name:<20} {stat.count:>8} "
                f"${stat.avg_price:>11,.2f} ${stat.min_price:>9,.2f} ${stat.max_price:>9,.2f}"
            )

        total = sum(stat.count for stat in city_stats)
        print("-" * 80)
        print(f"{'TOTAL':<20} {total:>8}")
        print("=" * 80)

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Print properties from the database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of properties to display (default: 10)'
    )

    parser.add_argument(
        '--city',
        type=str,
        help='Filter by city name (e.g., "New York", "Brooklyn")'
    )

    parser.add_argument(
        '--recent-hours',
        type=int,
        help='Only show properties added in the last N hours'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics grouped by city'
    )

    args = parser.parse_args()

    if args.stats:
        print_city_statistics()
    else:
        print_properties(
            limit=args.limit,
            city=args.city,
            recent_hours=args.recent_hours
        )


if __name__ == "__main__":
    main()
