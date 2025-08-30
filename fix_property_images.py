#!/usr/bin/env python3
"""
Property Images Fix Script
Fix missing property images by creating an API endpoint and calling it.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time

API_BASE_URL = 'http://3.145.189.113:8000'

def get_all_properties():
    """Get all properties from the API"""
    try:
        with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/properties/", timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching properties: {e}")
        return []

def check_property_images(property_id):
    """Check if property has images"""
    try:
        with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/properties/{property_id}/images", timeout=30) as response:
            images = json.loads(response.read().decode('utf-8'))
            return len(images) > 0, images
    except Exception as e:
        print(f"Error checking images for property {property_id}: {e}")
        return False, []

def get_property_details(property_id):
    """Get detailed property information including api_images"""
    try:
        with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/properties/{property_id}", timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching property {property_id} details: {e}")
        return None

def main():
    print("=== Property Images Fix Analysis ===\n")
    
    # Get all properties
    print("Fetching all properties...")
    properties = get_all_properties()
    
    if not properties:
        print("No properties found or API error")
        return
    
    print(f"Found {len(properties)} properties\n")
    
    properties_without_images = []
    properties_with_api_images = []
    properties_with_property_images = []
    
    for prop in properties[:10]:  # Check first 10 properties
        prop_id = prop['id']
        print(f"Checking Property {prop_id}: {prop.get('title', 'No title')[:50]}...")
        
        # Check if has PropertyImage records
        has_images, images = check_property_images(prop_id)
        
        if has_images:
            print(f"  ✓ Has {len(images)} PropertyImage records")
            properties_with_property_images.append(prop_id)
        else:
            print(f"  ✗ No PropertyImage records")
            
            # Get detailed property info to check api_images
            details = get_property_details(prop_id)
            if details and details.get('api_images'):
                api_images = details['api_images']
                print(f"  📷 Has {len(api_images)} API images: {api_images[0][:50] if api_images else 'None'}...")
                properties_with_api_images.append({
                    'id': prop_id,
                    'title': prop.get('title', ''),
                    'api_images': api_images
                })
            else:
                print(f"  🚫 No API images either")
                properties_without_images.append(prop_id)
        
        time.sleep(0.5)  # Rate limiting
    
    # Summary
    print(f"\n{'='*60}")
    print(f"ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Total properties analyzed: {len(properties[:10])}")
    print(f"Properties with PropertyImage records: {len(properties_with_property_images)}")
    print(f"Properties with API images (need migration): {len(properties_with_api_images)}")
    print(f"Properties without any images: {len(properties_without_images)}")
    
    # Show properties that need migration
    if properties_with_api_images:
        print(f"\n📷 PROPERTIES NEEDING IMAGE MIGRATION:")
        for prop in properties_with_api_images:
            print(f"  ID {prop['id']}: {prop['title'][:40]} - {len(prop['api_images'])} images")
    
    # Create migration endpoint call example
    if properties_with_api_images:
        print(f"\n🔧 MIGRATION SOLUTION:")
        print("Create an admin endpoint to migrate API images to PropertyImage records:")
        print("POST /api/v1/admin/migrate-images")
        print("\nExample implementation needed in backend/app/routes/admin_sync.py")
    
    # Save results for reference
    results = {
        'analyzed': len(properties[:10]),
        'with_property_images': len(properties_with_property_images),
        'need_migration': len(properties_with_api_images),
        'no_images': len(properties_without_images),
        'migration_candidates': properties_with_api_images
    }
    
    with open('image_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis results saved to image_analysis_results.json")

if __name__ == "__main__":
    main()