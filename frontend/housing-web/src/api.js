import axios from "axios";
import { API_BASE_URL } from "./config";

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// 登录用户
  export const loginUser = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append("grant_type", "password");
    formData.append("username", email);
    formData.append("password", password);
  
    const response = await api.post("/auth/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    const {access_token, token_type} = response.data;
    if (!access_token || !token_type) {
      throw new Error("Invalid login response: Missing access_token or token_type.");
    }

    // Store the complete token with Bearer prefix
    localStorage.setItem("authToken", `${token_type} ${access_token}`);
  
    return response.data;
  };
  
  // 注册用户
  export const registerUser = async (userData) => {
    const response = await api.post("/auth/register", userData);
    return response.data;
};

// get current user information
export const getUserProfile = async () => {
    const token = localStorage.getItem("authToken");
    if (!token) {
        throw new Error("Authorization token is missing.");
    }
    const response = await api.get("/users/me", {
      headers: {
        Authorization: token,
      },
    });
    return response.data;
  };

//analyze image
export const analyzeImage = async (file, analysisType) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post(`/images/analyze?analysis_type=${analysisType}`, formData, {
    headers: {
      Authorization: token,
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};




//check if tenant profile exists
export const checkTenantProfile = async () => {
  const token = localStorage.getItem("authToken");
    if (!token) {
      throw new Error("Authorization token is missing.");
    }
  try {
    const response = await api.get("profile/tenant", {
      headers: {
        Authorization: token,
      },
    });
    const tenantProfile = response.data;

    // 根据某个关键字段判断 profile 是否完成
    if (tenantProfile?.budget === null) {
      return null; // 未填写完整的 profile
    }
    return tenantProfile; // 返回完整的 profile

  } catch (err) {
    if (err.response?.status === 404) {
      return null; // if return 404, means tenant profile does not exist
    }
    throw err;
  }
};

//check if landlord profile exists
export const checkLandlordProfile = async () => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  try {
    const response = await api.get("profile/landlord", {
      headers: {
        Authorization: token,
      },
    });
    const landlordProfile = response.data;

    // 根据某个关键字段判断 profile 是否完成
    if (landlordProfile?.contact_phone === null) {
      return null; // 未填写完整的 profile
    }
    return landlordProfile; // 返回完整的 profile

  } catch (err) {
    if (err.response?.status === 404) {
      return null; // if return 404, means landlord profile does not exist
    }
    throw err;
  }
};


//get user type by user id
export const getUserType = async (userId) => {

  const response = await api.get(`/users/${userId}`, {
    headers: {
      Authorization: token,
    },
  });
  return response.data; // return user type
};



export const updateTenantProfile = async (profileData) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await api.put("/profile/tenant", profileData, {
    headers: {
      Authorization: token, // 确保使用正确的格式
      "Content-Type": "application/json",
    },

  });

  return response.data;
};


// upload property image
export const uploadPropertyImage = async (file, propertyId) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const formData = new FormData();
  formData.append("files", file);  // 使用 'files' 作为键名
  // formData.append("is_primary", "false");  // 设置为主图

  const response = await api.post(`/properties/${propertyId}/images`, formData, {
    headers: {
      Authorization: token,
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

// 与 AI 进行聊天
export const sendMessageToChat = async (message) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await api.post(
    "/chat/message",
    { message },
    {
      headers: {
        Authorization: token,
        "Content-Type": "application/json",
      },
    }
  );

  return response.data;
};


// 更新房东信息
export const updateLandlordProfile = async (profileData) => {
  const token = localStorage.getItem("authToken");

  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  try {
    const response = await api.put("/profile/landlord", profileData, {
      headers: {
        Authorization: token, // Use token directly since it already includes Bearer
        "Content-Type": "application/json",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error updating landlord profile:", error);
    throw error.response?.data || {
      message: "An unexpected error occurred while updating the profile.",
    };
  }
};


export const createProperty = async (propertyData) => {
  console.log("Request Data:", propertyData);
  
  const token = localStorage.getItem("authToken"); // 从 localStorage 获取用户 Token
  console.log("Authorization Token:", token);
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  try {
    // 发送 POST 请求到后端
    const response = await api.post("/properties", propertyData, {
      headers: {
        Authorization: token, 
        "Content-Type": "application/json",
      },
    });

    return response.data; // 返回后端的响应数据
  } catch (error) {
    console.error("Error creating property:", error);
    throw error.response?.data || {
      message: "An unexpected error occurred while creating the property.",
    };
  }
};




// 获取房东个人资料及其发布的房产列表
export const getLandlordProfile = async () => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  try {
    const response = await api.get("/profile/landlord", {
      headers: {
        Authorization: token,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching landlord profile:", error);
    throw error.response?.data || { message: "Failed to fetch landlord profile." };
  }
};


// 获取单个房产详情
export const getPropertyDetails = async (propertyId) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  try {
    const response = await api.get(`/properties/${propertyId}`, {
      headers: {
        Authorization: token,
      },
    });
    return response.data; // 返回房产详情，包括图片
  } catch (error) {
    console.error("Error fetching property details:", error);
    throw error.response?.data || { message: "Failed to fetch property details." };
  }
};

// 获取推荐房产
export const getPropertyRecommendations = async (limit = 10) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  try {
    const response = await api.get(`/recommendations/properties?limit=${limit}`, {
      headers: {
        Authorization: token,
      },
    });
    return response.data; // 返回推荐房产列表
  } catch (error) {
    console.error("Error fetching property recommendations:", error);
    throw error.response?.data || { message: "Failed to fetch property recommendations." };
  }
};




// 获取会话列表
export const getConversations = async () => {
  const token = localStorage.getItem("authToken");
  if (!token) throw new Error("Authorization token is missing.");

  const response = await api.get("/messages/conversations", {
    headers: { Authorization: token },
  });
  return response.data;
};

// 获取与用户的消息记录
export const getMessages = async (otherUserId) => {
  const token = localStorage.getItem("authToken");
  if (!token) throw new Error("Authorization token is missing.");

  const response = await api.get(`/messages?other_user_id=${otherUserId}`, {
    headers: { Authorization: token },
  });
  return response.data;
};

// 发送消息
export const sendMessage = async ({ content, receiver_id }) => {
  const token = localStorage.getItem("authToken");
  if (!token) throw new Error("Authorization token is missing.");

  const response = await api.post(
    "/messages",
    { content, receiver_id },
    { headers: { Authorization: token } }
  );
  return response.data;
};


export const getRoommateRecommendations = async (limit = 10) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await api.get(`/recommendations/roommates?limit=${limit}`, {
    headers: {
      Authorization: token,
    },
  });
  return response.data;
};

// 获取用户详情
export const getUserDetails = async (userId) => {
  const token = localStorage.getItem("authToken");
  if (!token) throw new Error("Authorization token is missing.");

  const response = await api.get(`/users/${userId}`, {
    headers: { Authorization: token },
  });
  return response.data;
};

// 获取房源的所有图片
export const getPropertyImages = async (propertyId) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await api.get(`/properties/${propertyId}/images`, {
    headers: {
      Authorization: token,
    },
  });

  return response.data;
};

// 删除房源图片
export const deletePropertyImage = async (propertyId, imageId) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await api.delete(`/properties/${propertyId}/images/${imageId}`, {
    headers: {
      Authorization: token,
    },
  });

  return response.data;
};

// 设置主图
export const setPrimaryImage = async (propertyId, imageId) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await api.put(`/properties/${propertyId}/images/${imageId}/primary`, null, {
    headers: {
      Authorization: token,
    },
  });

  return response.data;
};

// 删除房产
export const deleteProperty = async (propertyId) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  try {
    const response = await api.delete(`/properties/${propertyId}`, {
      headers: {
        Authorization: token,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error deleting property:", error);
    throw error.response?.data || { message: "Failed to delete property." };
  }
};

// 更新房源信息
export const updateProperty = async (propertyId, propertyData) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const response = await api.put(`/properties/${propertyId}`, propertyData, {
    headers: {
      Authorization: token,
      "Content-Type": "application/json",
    },
  });

  return response.data;
};

export const getLandlordById = async (landlordId) => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/landlords/${landlordId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch landlord data');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching landlord data:', error);
    throw error;
  }
};

// 获取用户偏好设置
export const getUserPreferences = async (category = null) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("Authorization token is missing.");
  }

  const url = category 
    ? `/api/v1/profile/preferences?category=${category}`
    : '/api/v1/profile/preferences';

  const response = await api.get(`profile/preferences`, {
    headers: {
      Authorization: token,
    },
  });
  return response.data;

};