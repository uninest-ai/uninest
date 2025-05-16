// frontend/housing-web/src/api.js
import axios from "axios";
// API_BASE_URL from config.js will be "" (empty string) if .env is set to VITE_API_BASE_URL=""
// and vite.config.js doesn't override it.
import { API_BASE_URL } from "./config";

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL, 
    headers: {
        "Content-Type": "application/json",
    },
});

// Define a unified API path prefix
const API_PREFIX = "/api/v1";

// Helper function: get token
const getToken = () => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    // We can throw an error, or let each function handle it
    // console.warn("Authorization token is missing.");
  }
  return token;
};

// Login user
export const loginUser = async (email, password) => {
  const formData = new URLSearchParams();
  formData.append("grant_type", "password");
  formData.append("username", email);
  formData.append("password", password);

  const response = await api.post(`${API_PREFIX}/auth/login`, formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  const { access_token, token_type } = response.data;
  if (!access_token || !token_type) {
    throw new Error("Invalid login response: Missing access_token or token_type.");
  }

  localStorage.setItem("authToken", `${token_type} ${access_token}`);
  return response.data;
};

// Register user
export const registerUser = async (userData) => {
  const response = await api.post(`${API_PREFIX}/auth/register`, userData);
  return response.data;
};

// Get current user information
export const getUserProfile = async () => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for getUserProfile.");
  
  const response = await api.get(`${API_PREFIX}/users/me`, {
    headers: {
      Authorization: token,
    },
  });
  return response.data;
};

// Analyze image
export const analyzeImage = async (file, analysisType) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for analyzeImage.");

  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post(`${API_PREFIX}/images/analyze?analysis_type=${analysisType}`, formData, {
    headers: {
      Authorization: token,
      "Content-Type": "multipart/form-data", 
    },
  });
  return response.data;
};

// Check if tenant profile exists and is complete
export const checkTenantProfile = async () => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for checkTenantProfile.");
  
  try {
    const response = await api.get(`${API_PREFIX}/profile/tenant`, {
      headers: {
        Authorization: token,
      },
    });
    const tenantProfile = response.data;
    // The profile is complete if the budget is not null
    if (tenantProfile?.budget === null || typeof tenantProfile?.budget === 'undefined') {
      return null; // The profile is not complete
    }
    return tenantProfile;
  } catch (err) {
    if (err.response?.status === 404) {
      return null; // 404 means the tenant profile does not exist
    }
    console.error("Error checking tenant profile:", err);
    throw err;
  }
};

// Check if landlord profile exists and is complete
export const checkLandlordProfile = async () => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for checkLandlordProfile.");

  try {
    const response = await api.get(`${API_PREFIX}/profile/landlord`, {
      headers: {
        Authorization: token,
      },
    });
    const landlordProfile = response.data;
    // The profile is complete if the contact_phone is not null
    if (landlordProfile?.contact_phone === null || typeof landlordProfile?.contact_phone === 'undefined') {
      return null; // The profile is not complete
    }
    return landlordProfile;
  } catch (err) {
    if (err.response?.status === 404) {
      return null; // 404 means the landlord profile does not exist
    }
    console.error("Error checking landlord profile:", err);
    throw err;
  }
};

// Get user type (注意：原代码中 token 未定义，已修复)
export const getUserType = async (userId) => {
  const token = getToken(); // 获取 token
  if (!token && userId) { // If getting other user's information, it may not need token, depending on the backend API design
    // If getting other user's information does not need token, remove the token check and header here
    // But usually getting user information needs permission
     throw new Error("Authorization token is missing for getUserType.");
  }

  const headers = {};
  if (token) { // Only add to headers when token exists
    headers.Authorization = token;
  }
  
  const response = await api.get(`${API_PREFIX}/users/${userId}`, { headers });
  return response.data;
};

// Update tenant profile
export const updateTenantProfile = async (profileData) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for updateTenantProfile.");

  const response = await api.put(`${API_PREFIX}/profile/tenant`, profileData, {
    headers: {
      Authorization: token,
    },
  });
  return response.data;
};

// Upload property image
export const uploadPropertyImage = async (file, propertyId) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for uploadPropertyImage.");

  const formData = new FormData();
  formData.append("files", file); // The backend FastAPI UploadFile parameter name is usually 'file' or 'files'

  const response = await api.post(`${API_PREFIX}/properties/${propertyId}/images`, formData, {
    headers: {
      Authorization: token,
      // "Content-Type": "multipart/form-data", // Axios 会自动设置
    },
  });
  return response.data;
};

// Chat with AI
export const sendMessageToChat = async (message) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for sendMessageToChat.");

  const response = await api.post(`${API_PREFIX}/chat/message`, { message }, {
    headers: {
      Authorization: token,
    },
  });
  return response.data;
};

// Update landlord information
export const updateLandlordProfile = async (profileData) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for updateLandlordProfile.");

  try {
    const response = await api.put(`${API_PREFIX}/profile/landlord`, profileData, {
      headers: {
        Authorization: token,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error updating landlord profile:", error.response?.data || error.message);
    throw error.response?.data || { message: "An unexpected error occurred while updating the profile." };
  }
};

// Create property
export const createProperty = async (propertyData) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for createProperty.");

  try {
    const response = await api.post(`${API_PREFIX}/properties`, propertyData, {
      headers: {
        Authorization: token,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error creating property:", error.response?.data || error.message);
    throw error.response?.data || { message: "An unexpected error occurred while creating the property." };
  }
};

// Get landlord personal information and their published properties list
export const getLandlordProfile = async () => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for getLandlordProfile.");

  try {
    const response = await api.get(`${API_PREFIX}/profile/landlord`, {
      headers: {
        Authorization: token,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching landlord profile:", error.response?.data || error.message);
    throw error.response?.data || { message: "Failed to fetch landlord profile." };
  }
};

// Get single property details
export const getPropertyDetails = async (propertyId) => {
  const token = getToken(); 
  // For public property details, token may not be required, depending on your backend API design
  // if (!token) throw new Error("Authorization token is missing for getPropertyDetails.");

  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = token;
  }

  try {
    const response = await api.get(`${API_PREFIX}/properties/${propertyId}`, { headers });
    return response.data;
  } catch (error) {
    console.error("Error fetching property details:", error.response?.data || error.message);
    throw error.response?.data || { message: "Failed to fetch property details." };
  }
};

// Get property recommendations
export const getPropertyRecommendations = async (limit = 10) => {
  const token = getToken();
  // Whether property recommendations need token depends on your business logic
  // if (!token) throw new Error("Authorization token is missing for getPropertyRecommendations.");
  
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = token;
  }

  try {
    const response = await api.get(`${API_PREFIX}/recommendations/properties?limit=${limit}`, { headers });
    return response.data;
  } catch (error) {
    console.error("Error fetching property recommendations:", error.response?.data || error.message);
    throw error.response?.data || { message: "Failed to fetch property recommendations." };
  }
};

// Get conversation list
export const getConversations = async () => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for getConversations.");

  const response = await api.get(`${API_PREFIX}/messages/conversations`, {
    headers: { Authorization: token },
  });
  return response.data;
};

// Get messages with other user
export const getMessages = async (otherUserId) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for getMessages.");

  const response = await api.get(`${API_PREFIX}/messages?other_user_id=${otherUserId}`, {
    headers: { Authorization: token },
  });
  return response.data;
};

// Send message
export const sendMessage = async ({ content, receiver_id }) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for sendMessage.");

  const response = await api.post(`${API_PREFIX}/messages`, { content, receiver_id }, {
    headers: { Authorization: token },
  });
  return response.data;
};

// Get roommate recommendations
export const getRoommateRecommendations = async (limit = 10) => {
  const token = getToken();
  // Whether roommate recommendations need token depends on your business logic
  // if (!token) throw new Error("Authorization token is missing for getRoommateRecommendations.");

  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = token;
  }
  
  const response = await api.get(`${API_PREFIX}/recommendations/roommates?limit=${limit}`, { headers });
  return response.data;
};

// Get user details
export const getUserDetails = async (userId) => {
  const token = getToken();
  // Whether getting other user's details needs token depends on your business logic
  // if (!token) throw new Error("Authorization token is missing for getUserDetails.");

  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = token;
  }

  const response = await api.get(`${API_PREFIX}/users/${userId}`, { headers });
  return response.data;
};

// Get all property images
export const getPropertyImages = async (propertyId) => {
  const token = getToken();
  // Whether getting property images needs token depends on your business logic
  // if (!token) throw new Error("Authorization token is missing for getPropertyImages.");

  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = token;
  }

  const response = await api.get(`${API_PREFIX}/properties/${propertyId}/images`, { headers });
  return response.data;
};

// Delete property image
export const deletePropertyImage = async (propertyId, imageId) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for deletePropertyImage.");

  const response = await api.delete(`${API_PREFIX}/properties/${propertyId}/images/${imageId}`, {
    headers: {
      Authorization: token,
    },
  });
  return response.data;
};

// Set primary image
export const setPrimaryImage = async (propertyId, imageId) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for setPrimaryImage.");

  const response = await api.put(`${API_PREFIX}/properties/${propertyId}/images/${imageId}/primary`, null, {
    headers: {
      Authorization: token,
    },
  });
  return response.data;
};

// Delete property
export const deleteProperty = async (propertyId) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for deleteProperty.");

  try {
    const response = await api.delete(`${API_PREFIX}/properties/${propertyId}`, {
      headers: {
        Authorization: token,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error deleting property:", error.response?.data || error.message);
    throw error.response?.data || { message: "Failed to delete property." };
  }
};

// Update property information
export const updateProperty = async (propertyId, propertyData) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for updateProperty.");

  const response = await api.put(`${API_PREFIX}/properties/${propertyId}`, propertyData, {
    headers: {
      Authorization: token,
      // "Content-Type": "application/json", // Axios 会自动为 JSON 对象设置
    },
  });
  return response.data;
};

// Use fetch's getLandlordById function
export const getLandlordById = async (landlordId) => {
  try {
    // import.meta.env.VITE_API_BASE_URL 应该是 ""
    // API_PREFIX 是 "/api/v1"
    // So the final path is "/api/v1/landlords/${landlordId}"
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}${API_PREFIX}/landlords/${landlordId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // If this interface needs token, it also needs to be added here
        // const token = getToken();
        // if (token) headers.Authorization = token;
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Failed to fetch landlord data and parse error.' }));
      throw new Error(errorData.message || 'Failed to fetch landlord data');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching landlord data:', error.message);
    throw error;
  }
};

// Get user preferences
export const getUserPreferences = async (category = null) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for getUserPreferences.");

  const requestPath = category
    ? `${API_PREFIX}/profile/preferences?category=${category}`
    : `${API_PREFIX}/profile/preferences`;

  const response = await api.get(requestPath, {
    headers: {
      Authorization: token,
    },
  });
  return response.data;
};

// Export all API functions
export default api; // If other places need to use the configured axios instance directly
