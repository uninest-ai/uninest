// frontend/housing-web/src/api.js
import axios from "axios";
// API_BASE_URL from config.js will be "" (empty string) if .env is set to VITE_API_BASE_URL=""
// and vite.config.js doesn't override it.
import { API_BASE_URL } from "./config";

// 创建 axios 实例
// baseURL 将会是 "", 因为我们会在每个请求中手动添加 API_PREFIX
const api = axios.create({
    baseURL: API_BASE_URL, // Should be ""
    headers: {
        "Content-Type": "application/json",
    },
});

// 定义统一的 API 路径前缀
const API_PREFIX = "/api/v1";

// 辅助函数：获取 token
const getToken = () => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    // 可以选择抛出错误，或者让每个函数自行处理
    // console.warn("Authorization token is missing.");
  }
  return token;
};

// 登录用户
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

// 注册用户
export const registerUser = async (userData) => {
  const response = await api.post(`${API_PREFIX}/auth/register`, userData);
  return response.data;
};

// 获取当前用户信息
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

// 分析图片
export const analyzeImage = async (file, analysisType) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for analyzeImage.");

  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post(`${API_PREFIX}/images/analyze?analysis_type=${analysisType}`, formData, {
    headers: {
      Authorization: token,
      "Content-Type": "multipart/form-data", // 通常由 axios 根据 FormData 自动设置，但明确指出无害
    },
  });
  return response.data;
};

// 检查租户资料是否存在且完整
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
    // 根据某个关键字段判断 profile 是否完成 (示例逻辑，请根据实际情况调整)
    if (tenantProfile?.budget === null || typeof tenantProfile?.budget === 'undefined') {
      return null; // 未填写完整的 profile
    }
    return tenantProfile;
  } catch (err) {
    if (err.response?.status === 404) {
      return null; // 404 表示租户资料不存在
    }
    console.error("Error checking tenant profile:", err);
    throw err;
  }
};

// 检查房东资料是否存在且完整
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
    // 根据某个关键字段判断 profile 是否完成 (示例逻辑，请根据实际情况调整)
    if (landlordProfile?.contact_phone === null || typeof landlordProfile?.contact_phone === 'undefined') {
      return null; // 未填写完整的 profile
    }
    return landlordProfile;
  } catch (err) {
    if (err.response?.status === 404) {
      return null; // 404 表示房东资料不存在
    }
    console.error("Error checking landlord profile:", err);
    throw err;
  }
};

// 根据用户ID获取用户类型 (注意：原代码中 token 未定义，已修复)
export const getUserType = async (userId) => {
  const token = getToken(); // 获取 token
  if (!token && userId) { // 如果是获取他人信息，可能不需要token，取决于后端API设计
    // 如果获取他人信息不需要token，则移除此处的token检查和header
    // 但通常获取用户信息需要权限
     throw new Error("Authorization token is missing for getUserType.");
  }

  const headers = {};
  if (token) { // 仅当 token 存在时才添加到 headers
    headers.Authorization = token;
  }
  
  const response = await api.get(`${API_PREFIX}/users/${userId}`, { headers });
  return response.data;
};

// 更新租户资料
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

// 上传房产图片
export const uploadPropertyImage = async (file, propertyId) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for uploadPropertyImage.");

  const formData = new FormData();
  formData.append("files", file); // 后端 FastAPI UploadFile 参数名通常是 'file' 或 'files'

  const response = await api.post(`${API_PREFIX}/properties/${propertyId}/images`, formData, {
    headers: {
      Authorization: token,
      // "Content-Type": "multipart/form-data", // Axios 会自动设置
    },
  });
  return response.data;
};

// 与 AI 进行聊天
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

// 更新房东信息
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

// 创建房产
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

// 获取房东个人资料及其发布的房产列表
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

// 获取单个房产详情
export const getPropertyDetails = async (propertyId) => {
  const token = getToken(); 
  // 对于公共房源详情，token 可能不是必需的，取决于您的后端 API 设计
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

// 获取推荐房产
export const getPropertyRecommendations = async (limit = 10) => {
  const token = getToken();
  // 推荐房产是否需要 token 取决于您的业务逻辑
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

// 获取会话列表
export const getConversations = async () => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for getConversations.");

  const response = await api.get(`${API_PREFIX}/messages/conversations`, {
    headers: { Authorization: token },
  });
  return response.data;
};

// 获取与用户的消息记录
export const getMessages = async (otherUserId) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for getMessages.");

  const response = await api.get(`${API_PREFIX}/messages?other_user_id=${otherUserId}`, {
    headers: { Authorization: token },
  });
  return response.data;
};

// 发送消息
export const sendMessage = async ({ content, receiver_id }) => {
  const token = getToken();
  if (!token) throw new Error("Authorization token is missing for sendMessage.");

  const response = await api.post(`${API_PREFIX}/messages`, { content, receiver_id }, {
    headers: { Authorization: token },
  });
  return response.data;
};

// 获取室友推荐
export const getRoommateRecommendations = async (limit = 10) => {
  const token = getToken();
  // 室友推荐是否需要 token 取决于您的业务逻辑
  // if (!token) throw new Error("Authorization token is missing for getRoommateRecommendations.");

  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = token;
  }
  
  const response = await api.get(`${API_PREFIX}/recommendations/roommates?limit=${limit}`, { headers });
  return response.data;
};

// 获取用户详情
export const getUserDetails = async (userId) => {
  const token = getToken();
  // 获取他人详情是否需要 token 取决于您的业务逻辑
  // if (!token) throw new Error("Authorization token is missing for getUserDetails.");

  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = token;
  }

  const response = await api.get(`${API_PREFIX}/users/${userId}`, { headers });
  return response.data;
};

// 获取房源的所有图片
export const getPropertyImages = async (propertyId) => {
  const token = getToken();
  // 获取图片是否需要 token 取决于您的业务逻辑
  // if (!token) throw new Error("Authorization token is missing for getPropertyImages.");

  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = token;
  }

  const response = await api.get(`${API_PREFIX}/properties/${propertyId}/images`, { headers });
  return response.data;
};

// 删除房源图片
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

// 设置主图
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

// 删除房产
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

// 更新房源信息
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

// 使用 fetch 的 getLandlordById 函数
export const getLandlordById = async (landlordId) => {
  try {
    // import.meta.env.VITE_API_BASE_URL 应该是 ""
    // API_PREFIX 是 "/api/v1"
    // 所以最终路径是 "/api/v1/landlords/${landlordId}"
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}${API_PREFIX}/landlords/${landlordId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // 如果这个接口需要 token，也需要在这里添加
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

// 获取用户偏好设置
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

// 导出所有 API 函数
export default api; // 如果其他地方需要直接使用配置好的 axios 实例
