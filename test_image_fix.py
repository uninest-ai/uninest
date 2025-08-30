#!/usr/bin/env python3
"""
Test Image Fix Implementation
Simple implementation to directly create PropertyImage records via API calls.
Since we can't execute SQL directly, we'll use API endpoints to create the images.
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time

API_BASE_URL = 'http://3.145.189.113:8000'

def test_current_state():
    """Test current state of property images"""
    print("=== Current State Test ===")
    
    # Test a few properties
    test_properties = [1, 2, 3, 27]
    
    for prop_id in test_properties:
        try:
            # Get property details
            with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/properties/{prop_id}", timeout=30) as response:
                details = json.loads(response.read().decode('utf-8'))
            
            # Get property images
            with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/properties/{prop_id}/images", timeout=30) as response:
                images = json.loads(response.read().decode('utf-8'))
            
            api_images = details.get('api_images', [])
            print(f"Property {prop_id}:")
            print(f"  Title: {details.get('title', 'No title')}")
            print(f"  API images: {len(api_images)}")
            print(f"  PropertyImage records: {len(images)}")
            print(f"  Property image_url: {'Yes' if details.get('image_url') else 'No'}")
            
            if api_images:
                print(f"  First API image: {api_images[0][:60]}...")
            
            print("")
            
        except Exception as e:
            print(f"Error testing property {prop_id}: {e}")
    
    return True

def check_image_upload_endpoint():
    """Check if we can use the image upload endpoint to create PropertyImage records"""
    print("=== Checking Available Endpoints ===")
    
    # Check what endpoints are available
    endpoints_to_test = [
        "/api/v1/properties/1/images",  # GET images
        "/docs",  # API documentation
    ]
    
    for endpoint in endpoints_to_test:
        try:
            req = urllib.request.Request(f"{API_BASE_URL}{endpoint}")
            with urllib.request.urlopen(req, timeout=10) as response:
                print(f"✓ {endpoint} - Available (Status: {response.getcode()})")
        except urllib.error.HTTPError as e:
            print(f"✗ {endpoint} - HTTP Error {e.code}")
        except Exception as e:
            print(f"✗ {endpoint} - Error: {str(e)}")

def create_property_image_record(property_id, image_url, is_primary=False):
    """
    Attempt to create a PropertyImage record using available endpoints.
    Since there's no direct PropertyImage creation endpoint, we'll need to use
    the property image upload endpoint with a workaround.
    """
    
    # This would require a multipart form upload, which is complex with urllib
    # For now, we'll document what needs to be done
    print(f"Would create PropertyImage for property {property_id}: {image_url[:50]}...")
    return True

def implement_frontend_fallback():
    """
    Since we can't easily create PropertyImage records via API,
    let's modify the frontend to use api_images as fallback
    """
    
    print("=== Frontend Fallback Solution ===")
    print("Since direct PropertyImage creation is complex via API,")
    print("the better approach is to modify the frontend to use api_images")
    print("when no PropertyImage records exist.")
    print("")
    print("Modifications needed in property-detail.jsx:")
    print("1. Check if property.images is empty")
    print("2. If empty, use property.api_images as fallback")
    print("3. Display api_images with proper formatting")
    
    return True

def create_frontend_fix():
    """Create a JavaScript snippet to fix the frontend"""
    
    frontend_fix = """
// Frontend fix for property-detail.jsx
// Add this logic to handle missing PropertyImage records

const getPropertyImages = () => {
  // First try to use PropertyImage records
  if (images && images.length > 0) {
    return images;
  }
  
  // Fallback to api_images from property details
  if (property.api_images && property.api_images.length > 0) {
    return property.api_images.map((url, index) => ({
      id: `api-${index}`,
      image_url: url,
      is_primary: index === 0,
      labels: ['api_image']
    }));
  }
  
  // No images available
  return [];
};

// Usage in component:
const displayImages = getPropertyImages();
"""
    
    with open('frontend_image_fix.js', 'w') as f:
        f.write(frontend_fix)
    
    print("✓ Frontend fix saved to frontend_image_fix.js")
    return True

def main():
    print("=== Image Fix Test & Implementation ===\n")
    
    # Step 1: Test current state
    test_current_state()
    
    # Step 2: Check available endpoints
    check_image_upload_endpoint()
    
    # Step 3: Create frontend fix
    create_frontend_fix()
    
    print("\n=== RECOMMENDATIONS ===")
    print("1. IMMEDIATE FIX: Update frontend to use api_images as fallback")
    print("2. LONG TERM: Add admin endpoint for PropertyImage migration")
    print("3. The SQL file 'image_migration.sql' can be executed on the database")
    print("   to permanently migrate api_images to PropertyImage records")
    
    print(f"\n🔧 Next Steps:")
    print("- Apply the frontend fix from frontend_image_fix.js")
    print("- Or execute the SQL migration on the database")
    print("- Or restart backend to load the new admin endpoint")

if __name__ == "__main__":
    main()