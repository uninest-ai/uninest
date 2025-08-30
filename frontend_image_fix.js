
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
