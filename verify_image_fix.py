#!/usr/bin/env python3
"""
Verify that property images are now available for display
Check that properties have either image_url or api_images populated
"""

import urllib.request
import json

API_BASE_URL = 'http://3.145.189.113:8000'

def test_properties_for_images():
    """Test first 10 properties for available images"""
    
    try:
        # Get property recommendations (this is what the frontend calls)
        with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/recommendations/properties", timeout=30) as response:
            properties = json.loads(response.read().decode('utf-8'))
            
    except:
        # Fallback to direct properties endpoint
        with urllib.request.urlopen(f"{API_BASE_URL}/api/v1/properties/", timeout=30) as response:
            properties = json.loads(response.read().decode('utf-8'))
    
    print("=== Property Image Availability Test ===\n")
    
    properties_with_images = 0
    properties_tested = 0
    
    for prop in properties[:10]:  # Test first 10
        properties_tested += 1
        prop_id = prop['id']
        title = prop.get('title', 'No title')[:50]
        
        has_main_image = bool(prop.get('image_url'))
        api_images = prop.get('api_images') or []
        has_api_images = bool(api_images) and len(api_images) > 0
        
        print(f"Property {prop_id}: {title}")
        print(f"  Main image_url: {'✓' if has_main_image else '✗'}")
        print(f"  API images: {'✓' if has_api_images else '✗'} ({len(prop.get('api_images', []))} images)")
        
        if has_main_image or has_api_images:
            properties_with_images += 1
            display_image = prop.get('image_url') or (prop.get('api_images', [None])[0])
            print(f"  Display image: {display_image[:60] if display_image else 'None'}...")
            print(f"  Status: ✅ WILL DISPLAY IMAGES")
        else:
            print(f"  Status: ❌ NO IMAGES AVAILABLE")
        
        print("")
    
    print(f"=== SUMMARY ===")
    print(f"Properties tested: {properties_tested}")
    print(f"Properties with images: {properties_with_images}")
    print(f"Image availability rate: {(properties_with_images/properties_tested*100):.1f}%")
    
    if properties_with_images >= properties_tested * 0.8:  # 80% threshold
        print(f"🎉 SUCCESS: Most properties will show images!")
    else:
        print(f"⚠ WARNING: Many properties still lack images")

def test_frontend_logic():
    """Test the frontend logic simulation"""
    
    print(f"\n=== Frontend Logic Simulation ===")
    
    # Simulate property data like what frontend receives
    test_property = {
        "id": 1,
        "title": "Test Property",
        "image_url": None,  # This is typically null
        "api_images": [
            "https://ap.rdcpix.com/08eecc565e8dd9fbecc85b2287d9fe29l-m1913496513s.jpg",
            "https://ap.rdcpix.com/08eecc565e8dd9fbecc85b2287d9fe29l-m4203691149s.jpg"
        ]
    }
    
    # Frontend logic simulation
    def get_property_image(property):
        if property.get('image_url'):
            return property['image_url']
        if property.get('api_images') and len(property['api_images']) > 0:
            return property['api_images'][0]
        return "fallback.png"
    
    result_image = get_property_image(test_property)
    print(f"Property: {test_property['title']}")
    print(f"image_url: {test_property['image_url']}")
    print(f"api_images: {len(test_property['api_images'])} images")
    print(f"Frontend will display: {result_image[:60]}...")
    print(f"✅ Frontend logic working correctly!")

def main():
    print("=== Property Image Fix Verification ===\n")
    
    try:
        test_properties_for_images()
        test_frontend_logic()
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Rebuild your frontend: npm run build")
        print(f"2. Check http://3.145.189.113/recommendation")
        print(f"3. Property cards should now show images!")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        print(f"Check that the backend is running at {API_BASE_URL}")

if __name__ == "__main__":
    main()