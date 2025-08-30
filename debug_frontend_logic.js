// Debug script to test the exact frontend logic
// Run this in browser console at http://3.145.189.113/recommendation

console.log("=== Frontend Image Logic Debug ===");

// Test the getPropertyImage function logic
function testGetPropertyImage(property) {
  console.log("Testing property:", property.id, property.title);
  
  // First try property.image_url
  if (property.image_url) {
    console.log("  ✓ Using property.image_url:", property.image_url);
    return property.image_url;
  }
  
  console.log("  ✗ No property.image_url");
  
  // Fallback to first api_image
  if (property.api_images && property.api_images.length > 0) {
    console.log("  ✓ Using api_images[0]:", property.api_images[0]);
    return property.api_images[0];
  }
  
  console.log("  ✗ No api_images available");
  console.log("  → Using fallback image");
  
  // Default fallback
  return "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/450px-No_image_available.svg.png?20250720084638";
}

// Check if we can access the properties data
if (typeof window !== 'undefined') {
  console.log("Run this in the browser console at the recommendation page:");
  console.log("1. Open http://3.145.189.113/recommendation");
  console.log("2. Open browser console (F12)");
  console.log("3. Paste this code to debug:");
  
  console.log(`
// Check React component state (if using React DevTools)
// Or check network requests in Network tab

// Debug the actual property data being received
fetch('/api/v1/recommendations/properties', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('authToken')
  }
})
.then(r => r.json())
.then(properties => {
  console.log('=== API Response Debug ===');
  properties.slice(0, 3).forEach(prop => {
    console.log('Property', prop.id, ':', prop.title);
    console.log('  image_url:', prop.image_url);
    console.log('  api_images:', prop.api_images);
    console.log('  Would show:', prop.image_url || (prop.api_images && prop.api_images[0]) || 'fallback');
  });
});
`);
}

// Instructions for manual testing
console.log("\n=== Manual Testing Steps ===");
console.log("1. Rebuild frontend: cd frontend/housing-web && npm run build");
console.log("2. Clear browser cache (Ctrl+Shift+R)");
console.log("3. Check Network tab in DevTools for API responses");
console.log("4. Verify api_images field is present in the property data");