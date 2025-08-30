#!/usr/bin/env python3
"""
Generate SQL statements to create PropertyImage records from api_images
This approach generates SQL that can be executed directly on the database.
"""

import urllib.request
import urllib.error
import json

API_BASE_URL = 'http://3.145.189.113:8000'

def get_all_properties():
    """Get all properties from the API"""
    try:
        with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/properties/", timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching properties: {e}")
        return []

def generate_image_migration_sql():
    """Generate SQL statements to migrate api_images to PropertyImage records"""
    
    properties = get_all_properties()
    if not properties:
        print("No properties found")
        return
    
    print("=== Property Image Migration SQL ===\n")
    
    sql_statements = []
    fallback_statements = []
    
    # Fallback images
    fallback_images = [
        "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",
        "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",
        "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",
        "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb",
        "https://images.unsplash.com/photo-1519452465094-7d23f0b4a4b1?w=800&h=600&fit=crop&crop=entropy&cs=tinysrgb"
    ]
    
    properties_with_images = 0
    properties_needing_migration = 0
    
    for prop in properties[:20]:  # Process first 20 properties
        prop_id = prop['id']
        
        # Get detailed property info
        try:
            with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/properties/{prop_id}", timeout=30) as response:
                details = json.loads(response.read().decode('utf-8'))
                
            api_images = details.get('api_images', [])
            
            if api_images and len(api_images) > 0:
                properties_with_images += 1
                
                # Check if property already has PropertyImage records
                try:
                    with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/properties/{prop_id}/images", timeout=30) as response:
                        existing_images = json.loads(response.read().decode('utf-8'))
                        
                    if len(existing_images) > 0:
                        print(f"-- Property {prop_id} already has {len(existing_images)} images, skipping")
                        continue
                        
                except:
                    pass  # Assume no existing images
                
                properties_needing_migration += 1
                print(f"-- Property {prop_id}: {prop.get('title', 'No title')[:50]}")
                print(f"-- {len(api_images)} API images found")
                
                for i, image_url in enumerate(api_images):
                    is_primary = 'true' if i == 0 else 'false'
                    sql = f"""INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES ({prop_id}, '{image_url}', {is_primary}, NULL, NOW());"""
                    sql_statements.append(sql)
                
                # Update property image_url if null
                if not details.get('image_url'):
                    sql = f"""UPDATE properties SET image_url = '{api_images[0]}' WHERE id = {prop_id} AND image_url IS NULL;"""
                    sql_statements.append(sql)
                
                print("")
            
            else:
                # No API images, create fallback
                prop_type = details.get('property_type', 'apartment')
                
                if prop_type == 'apartment':
                    fallback_url = fallback_images[3]
                elif prop_type == 'house':
                    fallback_url = fallback_images[0]
                elif prop_type == 'condo':
                    fallback_url = fallback_images[2]
                else:
                    fallback_url = fallback_images[1]
                
                fallback_sql = f"""INSERT INTO property_images (property_id, image_url, is_primary, labels, created_at) 
VALUES ({prop_id}, '{fallback_url}', true, '["fallback_image"]', NOW());"""
                fallback_statements.append(fallback_sql)
                
                # Update property image_url
                if not details.get('image_url'):
                    update_sql = f"""UPDATE properties SET image_url = '{fallback_url}' WHERE id = {prop_id} AND image_url IS NULL;"""
                    fallback_statements.append(update_sql)
        
        except Exception as e:
            print(f"Error processing property {prop_id}: {e}")
    
    # Output SQL statements
    print(f"=== MIGRATION SQL STATEMENTS ===")
    print(f"-- Properties with API images: {properties_with_images}")
    print(f"-- Properties needing migration: {properties_needing_migration}")
    print(f"-- SQL statements to execute: {len(sql_statements)}\n")
    
    if sql_statements:
        print("-- Migrate API images to PropertyImage records")
        for sql in sql_statements:
            print(sql)
    
    print(f"\n-- Fallback images SQL statements: {len(fallback_statements)}")
    if fallback_statements:
        print("\n-- Add fallback images for properties without API images")
        for sql in fallback_statements[:10]:  # Show first 10
            print(sql)
        if len(fallback_statements) > 10:
            print(f"-- ... and {len(fallback_statements) - 10} more fallback statements")
    
    # Save to file
    with open('image_migration.sql', 'w') as f:
        f.write("-- Property Image Migration SQL\n")
        f.write("-- Generated automatically\n\n")
        f.write("-- Migrate API images to PropertyImage records\n")
        for sql in sql_statements:
            f.write(sql + "\n")
        f.write("\n-- Add fallback images\n")
        for sql in fallback_statements:
            f.write(sql + "\n")
    
    print(f"\n✓ SQL statements saved to image_migration.sql")
    print(f"Execute this file on your database to migrate images.")

def main():
    generate_image_migration_sql()

if __name__ == "__main__":
    main()