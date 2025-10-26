"""
Embedding Scheduler Service

Automatically precompute embeddings for new properties on a schedule.
"""

import logging
from datetime import datetime
from app.database import SessionLocal
from app.models import Property
from app.services.embedding_service import get_embedding_service
from sqlalchemy import text

logger = logging.getLogger(__name__)


def update_embeddings_for_new_properties():
    """
    Update embeddings for properties that don't have them yet.
    This is designed to run periodically (e.g., every hour or daily).
    """
    logger.info("=" * 60)
    logger.info("Starting scheduled embedding update")
    logger.info(f"Time: {datetime.now()}")
    logger.info("=" * 60)

    db = SessionLocal()
    embedding_service = get_embedding_service()

    try:
        # Find properties without embeddings
        result = db.execute(
            text("""
                SELECT p.id, p.title, p.description
                FROM properties p
                LEFT JOIN property_embeddings pe ON p.id = pe.id
                WHERE p.is_active = TRUE
                AND pe.id IS NULL
            """)
        )

        properties_without_embeddings = result.fetchall()

        if not properties_without_embeddings:
            logger.info("✅ All active properties have embeddings")
            return {
                "success": True,
                "message": "No new properties to process",
                "processed": 0
            }

        logger.info(f"Found {len(properties_without_embeddings)} properties without embeddings")

        created = 0
        errors = 0

        for prop_id, title, description in properties_without_embeddings:
            try:
                # Combine title and description
                text_to_embed = f"{title or ''} {description or ''}".strip()

                if not text_to_embed:
                    logger.warning(f"Property {prop_id} has no text content, skipping")
                    continue

                # Generate embedding
                embedding = embedding_service.encode_text(text_to_embed, normalize=True)

                # Save to database
                success = embedding_service.save_embedding(
                    db=db,
                    property_id=prop_id,
                    embedding=embedding
                )

                if success:
                    created += 1
                    logger.info(f"✅ Created embedding for property {prop_id}")
                else:
                    errors += 1
                    logger.error(f"❌ Failed to save embedding for property {prop_id}")

            except Exception as e:
                logger.error(f"❌ Error processing property {prop_id}: {e}")
                errors += 1
                continue

        logger.info("=" * 60)
        logger.info("Scheduled embedding update complete")
        logger.info(f"✅ Embeddings created: {created}")
        logger.info(f"❌ Errors: {errors}")
        logger.info("=" * 60)

        return {
            "success": True,
            "message": f"Processed {created + errors} properties",
            "created": created,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Fatal error during scheduled embedding update: {e}")
        return {
            "success": False,
            "message": str(e),
            "created": 0,
            "errors": 1
        }
    finally:
        db.close()