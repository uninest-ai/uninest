#!/usr/bin/env python3
"""
Run Image Migration
Call the admin endpoint to migrate API images to PropertyImage records.
"""

import urllib.request
import urllib.parse
import urllib.error
import json

API_BASE_URL = 'http://3.145.189.113:8000'
ADMIN_KEY = 'Admin123456'

def run_migration():
    """Run the image migration via admin endpoint"""
    
    endpoint = f"{API_BASE_URL}/api/v1/admin/migrate-images"
    
    try:
        # Create request with admin key
        req = urllib.request.Request(
            endpoint,
            method='POST',
            headers={
                'X-Admin-Key': ADMIN_KEY,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        
        print("Starting image migration...")
        print(f"Calling: {endpoint}")
        
        # Make the request
        with urllib.request.urlopen(req, timeout=60) as response:
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
            
            print("\n=== MIGRATION RESULTS ===")
            print(f"Success: {result.get('success', False)}")
            print(f"Message: {result.get('message', 'No message')}")
            print(f"Migrated Properties: {result.get('migrated_properties', 0)}")
            print(f"Total Images Created: {result.get('total_images_created', 0)}")
            print(f"Fallback Images Added: {result.get('fallback_images_added', 0)}")
            print(f"Skipped Properties: {result.get('skipped_properties', 0)}")
            
            # Show verification stats
            verification = result.get('verification', {})
            if verification:
                print(f"\n=== VERIFICATION ===")
                print(f"Total Active Properties: {verification.get('total_active_properties', 0)}")
                print(f"Properties with Images: {verification.get('properties_with_images', 0)}")
                print(f"Total Property Images: {verification.get('total_property_images', 0)}")
                print(f"Coverage: {verification.get('coverage_percentage', 0)}%")
            
            # Show errors if any
            errors = result.get('errors', [])
            if errors:
                print(f"\n=== ERRORS ({len(errors)}) ===")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"- {error}")
                if len(errors) > 5:
                    print(f"... and {len(errors) - 5} more errors")
            
            return result.get('success', False)
            
    except urllib.error.HTTPError as e:
        error_data = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {error_data}")
        return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_image_display():
    """Test that a property now has images"""
    
    # Test property 27 which we know has api_images
    test_property_id = 27
    
    try:
        # Get property images
        images_url = f"{API_BASE_URL}/api/v1/properties/{test_property_id}/images"
        with urllib.request.urlopen(images_url, timeout=30) as response:
            images = json.loads(response.read().decode('utf-8'))
            
        print(f"\n=== TEST PROPERTY {test_property_id} IMAGES ===")
        if images:
            print(f"✓ Found {len(images)} images!")
            for i, img in enumerate(images):
                print(f"  Image {i+1}: {img.get('image_url', 'No URL')[:60]}...")
                print(f"    Primary: {img.get('is_primary', False)}")
        else:
            print("✗ No images found")
            
        return len(images) > 0
        
    except Exception as e:
        print(f"Error testing images: {str(e)}")
        return False

def main():
    print("=== UniNest Image Migration Tool ===\n")
    
    # Step 1: Run migration
    success = run_migration()
    
    if success:
        print("\n✓ Migration completed successfully!")
        
        # Step 2: Test image display
        print("\n" + "="*50)
        if test_image_display():
            print("\n🎉 SUCCESS! Images are now available for display!")
            print("\nYour frontend should now show property images instead of 'No images available'.")
        else:
            print("\n⚠ Migration completed but test property still has no images.")
    else:
        print("\n✗ Migration failed!")
        
        # Try to check if endpoint exists
        try:
            status_url = f"{API_BASE_URL}/api/v1/admin/status"
            with urllib.request.urlopen(status_url, timeout=10) as response:
                print("\nBackend is responding. The migrate-images endpoint might not be available yet.")
                print("You may need to restart the backend to load the new endpoint.")
        except:
            print("\nBackend is not responding. Please ensure the backend is running.")

if __name__ == "__main__":
    main()