#!/usr/bin/env python3
"""
Precompute Property Embeddings Script

This script generates vector embeddings for all properties in the database
and stores them in the property_embeddings table for fast hybrid search.

Usage:
    # From project root
    docker-compose exec backend python scripts/precompute_embeddings.py

    # With options
    docker-compose exec backend python scripts/precompute_embeddings.py --batch-size 50 --model all-MiniLM-L6-v2
"""

import argparse
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Property
from app.services.embedding_service import get_embedding_service
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def precompute_embeddings(
    batch_size: int = 100,
    model_name: str = 'all-MiniLM-L6-v2',
    skip_existing: bool = True
):
    """
    Precompute embeddings for all properties.

    Args:
        batch_size: Number of properties to process in each batch
        model_name: Sentence transformer model to use
        skip_existing: Skip properties that already have embeddings
    """
    logger.info("="*60)
    logger.info("Property Embeddings Precomputation")
    logger.info("="*60)
    logger.info(f"Model: {model_name}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Skip existing: {skip_existing}")
    logger.info("")

    db = SessionLocal()

    try:
        # Initialize embedding service
        logger.info("Loading embedding model...")
        embedding_service = get_embedding_service(model_name)
        logger.info("✅ Model loaded successfully")

        # Get all active properties
        logger.info("\nFetching properties from database...")
        properties = db.query(Property).filter(Property.is_active == True).all()
        total_properties = len(properties)

        if total_properties == 0:
            logger.warning("No active properties found in database!")
            return

        logger.info(f"Found {total_properties} active properties")

        # Get existing embeddings if skip_existing is True
        existing_ids = set()
        if skip_existing:
            result = db.execute(
                text("SELECT id FROM property_embeddings WHERE model_name = :model"),
                {"model": model_name}
            )
            existing_ids = {row[0] for row in result}
            logger.info(f"Found {len(existing_ids)} existing embeddings (will skip)")

        # Process properties in batches
        processed = 0
        created = 0
        skipped = 0
        errors = 0

        logger.info(f"\nProcessing {total_properties} properties...")
        logger.info("-" * 60)

        for i in range(0, total_properties, batch_size):
            batch = properties[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_properties + batch_size - 1) // batch_size

            logger.info(f"\nBatch {batch_num}/{total_batches} ({len(batch)} properties)")

            for prop in batch:
                try:
                    # Skip if embedding already exists
                    if skip_existing and prop.id in existing_ids:
                        skipped += 1
                        processed += 1
                        continue

                    # Combine title and description for embedding
                    text_to_embed = f"{prop.title or ''} {prop.description or ''}".strip()

                    if not text_to_embed:
                        logger.warning(f"Property {prop.id} has no text content, skipping")
                        skipped += 1
                        processed += 1
                        continue

                    # Generate embedding
                    embedding = embedding_service.encode_text(text_to_embed, normalize=True)

                    # Save to database
                    success = embedding_service.save_embedding(
                        db=db,
                        property_id=prop.id,
                        embedding=embedding
                    )

                    if success:
                        created += 1
                    else:
                        errors += 1
                        logger.error(f"Failed to save embedding for property {prop.id}")

                    processed += 1

                    # Progress update
                    if processed % 10 == 0:
                        progress = (processed / total_properties) * 100
                        logger.info(
                            f"Progress: {processed}/{total_properties} ({progress:.1f}%) | "
                            f"Created: {created} | Skipped: {skipped} | Errors: {errors}"
                        )

                except Exception as e:
                    logger.error(f"Error processing property {prop.id}: {e}")
                    errors += 1
                    processed += 1
                    continue

        # Final summary
        logger.info("\n" + "="*60)
        logger.info("PRECOMPUTATION COMPLETE")
        logger.info("="*60)
        logger.info(f"Total properties processed: {processed}")
        logger.info(f"✅ Embeddings created: {created}")
        logger.info(f"⏭️  Skipped (already exist): {skipped}")
        logger.info(f"❌ Errors: {errors}")
        logger.info("="*60)

        # Verify final count
        result = db.execute(
            text("SELECT COUNT(*) FROM property_embeddings WHERE model_name = :model"),
            {"model": model_name}
        )
        total_embeddings = result.fetchone()[0]
        logger.info(f"\nTotal embeddings in database: {total_embeddings}")

    except Exception as e:
        logger.error(f"Fatal error during precomputation: {e}")
        raise
    finally:
        db.close()
        logger.info("\nDatabase connection closed")


def verify_embeddings(model_name: str = 'all-MiniLM-L6-v2'):
    """
    Verify embedding count and display statistics.

    Args:
        model_name: Model name to check
    """
    logger.info("="*60)
    logger.info("Embeddings Verification")
    logger.info("="*60)

    db = SessionLocal()

    try:
        # Count embeddings
        result = db.execute(
            text("SELECT COUNT(*) FROM property_embeddings WHERE model_name = :model"),
            {"model": model_name}
        )
        embedding_count = result.fetchone()[0]

        # Count active properties
        active_properties = db.query(Property).filter(Property.is_active == True).count()

        # Coverage
        coverage = (embedding_count / active_properties * 100) if active_properties > 0 else 0

        logger.info(f"Model: {model_name}")
        logger.info(f"Active properties: {active_properties}")
        logger.info(f"Embeddings: {embedding_count}")
        logger.info(f"Coverage: {coverage:.1f}%")

        if coverage < 100:
            logger.warning(f"\n⚠️  Missing embeddings for {active_properties - embedding_count} properties")
            logger.info("Run precompute script without --skip-existing to update all")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Precompute property embeddings for hybrid search",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of properties to process per batch (default: 100)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='all-MiniLM-L6-v2',
        help='Sentence transformer model name (default: all-MiniLM-L6-v2)'
    )

    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Recompute embeddings for properties that already have them'
    )

    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify embedding statistics without computing'
    )

    args = parser.parse_args()

    if args.verify_only:
        verify_embeddings(model_name=args.model)
    else:
        precompute_embeddings(
            batch_size=args.batch_size,
            model_name=args.model,
            skip_existing=not args.no_skip_existing
        )


if __name__ == "__main__":
    main()
