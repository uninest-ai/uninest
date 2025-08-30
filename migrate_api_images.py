#!/usr/bin/env python3
"""
API Images Migration Script
Migrate image URLs from api_images JSON field to PropertyImage records.
"""

import os
import sys
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Property, PropertyImage
from app.config import settings

def migrate_api_images():
    """Migrate api_images from properties to PropertyImage records"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=== API Images Migration Script ===\n")
        
        # Get all properties with api_images
        properties_with_images = db.query(Property).filter(
            Property.api_images.is_not(None),
            Property.api_images != "[]"
        ).all()
        
        print(f"Found {len(properties_with_images)} properties with API images")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        total_images = 0
        
        for prop in properties_with_images:
            try:
                print(f"\nProcessing Property ID {prop.id}: {prop.title}")
                
                # Check if images already exist for this property
                existing_images = db.query(PropertyImage).filter(
                    PropertyImage.property_id == prop.id
                ).count()
                
                if existing_images > 0:
                    print(f"  Skipping - {existing_images} images already exist")
                    skipped_count += 1
                    continue
                
                # Parse api_images JSON
                api_images = prop.api_images
                if isinstance(api_images, str):
                    try:
                        api_images = json.loads(api_images)
                    except json.JSONDecodeError:
                        print(f"  Error: Invalid JSON in api_images: {api_images}")
                        error_count += 1
                        continue
                
                if not api_images or not isinstance(api_images, list):
                    print(f"  No valid images found")
                    continue
                
                print(f"  Found {len(api_images)} API images")
                
                # Create PropertyImage records
                images_created = 0
                for i, image_url in enumerate(api_images):
                    if not image_url or not isinstance(image_url, str):
                        continue
                        
                    # Create PropertyImage record
                    property_image = PropertyImage(
                        property_id=prop.id,
                        image_url=image_url,
                        is_primary=(i == 0),  # First image is primary
                        labels=None,
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(property_image)
                    images_created += 1
                    total_images += 1
                    print(f"    Added image {i+1}: {image_url[:60]}...")
                
                if images_created > 0:
                    # Update property's main image_url if it's null
                    if not prop.image_url:
                        prop.image_url = api_images[0]
                        print(f"  Updated property image_url to: {api_images[0][:60]}...")
                    
                    db.commit()
                    migrated_count += 1
                    print(f"  ✓ Successfully created {images_created} images")
                else:
                    print(f"  No valid image URLs to process")
                
            except Exception as e:
                print(f"  ✗ Error processing property {prop.id}: {str(e)}")
                db.rollback()
                error_count += 1
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"MIGRATION SUMMARY")
        print(f"{'='*50}")
        print(f"Properties processed: {len(properties_with_images)}")
        print(f"Successfully migrated: {migrated_count}")
        print(f"Skipped (already had images): {skipped_count}")
        print(f"Errors: {error_count}")
        print(f"Total images created: {total_images}")
        print(f"Success rate: {(migrated_count/(migrated_count + error_count)*100):.1f}%" if (migrated_count + error_count) > 0 else "N/A")
        
        # Verify results
        print(f"\n=== Verification ===")
        total_properties = db.query(Property).count()
        properties_with_property_images = db.query(Property).join(PropertyImage).distinct().count()
        total_property_images = db.query(PropertyImage).count()
        
        print(f"Total properties in database: {total_properties}")
        print(f"Properties with PropertyImage records: {properties_with_property_images}")
        print(f"Total PropertyImage records: {total_property_images}")
        print(f"Properties with coverage: {(properties_with_property_images/total_properties*100):.1f}%")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        db.rollback()
        return False
    
    finally:
        db.close()
    
    return True

def add_fallback_images():
    """Add fallback placeholder images for properties without any images"""
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print(f"\n=== Adding Fallback Images ===")
        
        # Fallback image URLs (using Unsplash for realistic property photos)
        fallback_images = [
            "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Modern house
            "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Beautiful home
            "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Contemporary house
            "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Apartment building
            "https://images.unsplash.com/photo-1519452465094-7d23f0b4a4b1?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",  # Studio apartment
        ]
        
        # Find properties without images
        properties_without_images = db.query(Property).outerjoin(PropertyImage).filter(
            PropertyImage.id.is_(None)
        ).all()
        
        print(f"Found {len(properties_without_images)} properties without images")
        
        fallback_added = 0
        
        for prop in properties_without_images:
            # Choose fallback image based on property type
            if prop.property_type == 'apartment':
                fallback_url = fallback_images[3]  # Apartment building
            elif prop.property_type == 'studio':
                fallback_url = fallback_images[4]  # Studio
            elif prop.property_type == 'house':
                fallback_url = fallback_images[0]  # Modern house
            elif prop.property_type == 'condo':
                fallback_url = fallback_images[2]  # Contemporary house
            else:
                fallback_url = fallback_images[1]  # Default beautiful home
            
            try:
                # Create fallback PropertyImage
                property_image = PropertyImage(
                    property_id=prop.id,
                    image_url=fallback_url,
                    is_primary=True,
                    labels=["fallback_image"],
                    created_at=datetime.utcnow()
                )
                
                db.add(property_image)
                
                # Update property's main image_url if it's null
                if not prop.image_url:
                    prop.image_url = fallback_url
                
                fallback_added += 1
                print(f"  Added fallback image for Property {prop.id}: {prop.title[:50]}...")
                
            except Exception as e:
                print(f"  Error adding fallback for Property {prop.id}: {str(e)}")
        
        if fallback_added > 0:
            db.commit()
            print(f"✓ Successfully added {fallback_added} fallback images")
        else:
            print("No fallback images needed")
        
    except Exception as e:
        print(f"Fallback images failed: {str(e)}")
        db.rollback()
        return False
    
    finally:
        db.close()
    
    return True

def main():
    """Main migration function"""
    print("Starting API images migration process...")
    
    # Step 1: Migrate API images
    if not migrate_api_images():
        print("Migration failed!")
        return
    
    # Step 2: Add fallback images
    if not add_fallback_images():
        print("Fallback images failed!")
        return
    
    print(f"\n🎉 Migration completed successfully!")
    print("All properties should now have images available.")

if __name__ == "__main__":
    main()