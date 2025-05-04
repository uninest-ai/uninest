import React, { useState, useRef } from "react";
import axios from "axios";
import { createProperty, uploadPropertyImage } from "../src/api"; // 引入封装的 API 方法
import { useNavigate } from "react-router-dom"; // 添加 useNavigate

const UploadProperty = () => {
  const navigate = useNavigate(); // 添加导航 hook
  const fileInputRef = useRef(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    price: "",
    description: "",
    property_type: "house",
    bedrooms: "1",
    bathrooms: "1",
    area: "",
    address: "",
    city: "Pittsburgh", // 固定值
  });

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // 处理图片选择
  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      // 创建预览URL
      const previewUrl = URL.createObjectURL(file);
      setImagePreview(previewUrl);
    }
  };

  // 触发文件选择
  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  // 处理表单输入
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  // 提交表单
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      // 1. 获取地理位置信息
      const geoResponse = await axios.get(
        `https://nominatim.openstreetmap.org/search?format=json&q=${formData.address},${formData.city}`
      );

      const { lat, lon } = geoResponse.data[0] || {};
      if (!lat || !lon) {
        throw new Error("Unable to fetch geolocation. Please check the address.");
      }

      // 2. 构建房产数据
      const propertyData = {
        ...formData,
        price: parseFloat(formData.price),
        bedrooms: parseInt(formData.bedrooms),
        bathrooms: parseFloat(formData.bathrooms),
        area: parseFloat(formData.area) || 0,
        latitude: parseFloat(lat),
        longitude: parseFloat(lon),
        labels: [],
      };

      // 3. 创建房产信息
      const propertyResponse = await createProperty(propertyData);
      setSuccessMessage("Property information saved successfully!");

      // 4. 如果有选择图片，上传图片
      if (selectedImage && propertyResponse.id) {
        setUploadingImage(true);
        try {
          // 使用 API 函数上传图片
          await uploadPropertyImage(selectedImage, propertyResponse.id);
          setSuccessMessage("Property and image uploaded successfully!");
        } catch (imageError) {
          console.error("Error uploading image:", imageError);
          setErrorMessage("Property saved but failed to upload image. You can add images later.");
        } finally {
          setUploadingImage(false);
        }
      }

      // 5. 延迟跳转到 landlord profile 页面
      setTimeout(() => {
        navigate("/landlord-profile");
      }, 1500);

    } catch (error) {
      console.error("Error creating property:", error);
      setErrorMessage(error.response?.data?.detail || "Failed to create property.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-2xl p-6 bg-white rounded-lg shadow-md">
        <h2 className="mb-6 text-xl font-bold text-center">Upload Property</h2>
        <form onSubmit={handleSubmit}>
          {/* 图片上传区域 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Property Image
            </label>
            <div className="flex flex-col items-center justify-center">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageSelect}
                accept="image/*"
                className="hidden"
              />
              <div 
                className="w-full h-48 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 transition-colors"
                onClick={handleUploadClick}
              >
                {imagePreview ? (
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="max-h-full max-w-full object-contain"
                  />
                ) : (
                  <div className="text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <p className="mt-1 text-sm text-gray-600">
                      Click to select an image
                    </p>
                  </div>
                )}
              </div>
              {selectedImage && (
                <p className="mt-2 text-sm text-gray-500">
                  Selected: {selectedImage.name}
                </p>
              )}
            </div>
          </div>

          {/* Title */}
          <div className="mb-4">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
              Title
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              className="w-full px-4 py-2 mt-1 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          {/* Price */}
          <div className="mb-4">
            <label htmlFor="price" className="block text-sm font-medium text-gray-700">
              Price ($)
            </label>
            <input
              type="number"
              id="price"
              name="price"
              value={formData.price}
              onChange={handleInputChange}
              className="w-full px-4 py-2 mt-1 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          {/* Description */}
          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows="4"
              className="w-full px-4 py-2 mt-1 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              required
            ></textarea>
          </div>

          {/* Property Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">Property Type</label>
            <div className="flex gap-4">
              {["house", "apartment", "both"].map((type) => (
                <label key={type} className="flex items-center">
                  <input
                    type="radio"
                    name="property_type"
                    value={type}
                    checked={formData.property_type === type}
                    onChange={handleInputChange}
                    className="mr-2"
                  />
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </label>
              ))}
            </div>
          </div>

          {/* Bedrooms */}
          <div className="mb-4">
            <label htmlFor="bedrooms" className="block text-sm font-medium text-gray-700">
              Bedrooms
            </label>
            <select
              id="bedrooms"
              name="bedrooms"
              value={formData.bedrooms}
              onChange={handleInputChange}
              className="w-full px-4 py-2 mt-1 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              required
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
                <option key={num} value={num}>
                  {num}
                </option>
              ))}
            </select>
          </div>

          {/* Bathrooms */}
          <div className="mb-4">
            <label htmlFor="bathrooms" className="block text-sm font-medium text-gray-700">
              Bathrooms
            </label>
            <select
              id="bathrooms"
              name="bathrooms"
              value={formData.bathrooms}
              onChange={handleInputChange}
              className="w-full px-4 py-2 mt-1 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              required
            >
              {[1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5].map((num) => (
                <option key={num} value={num}>
                  {num}
                </option>
              ))}
            </select>
          </div>

          {/* Area */}
          <div className="mb-4">
            <label htmlFor="area" className="block text-sm font-medium text-gray-700">
              Area (sq ft)
            </label>
            <input
              type="number"
              id="area"
              name="area"
              value={formData.area}
              onChange={handleInputChange}
              className="w-full px-4 py-2 mt-1 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter area in square feet"
              required
            />
          </div>

          {/* Address */}
          <div className="mb-4">
            <label htmlFor="address" className="block text-sm font-medium text-gray-700">
              Address
            </label>
            <input
              type="text"
              id="address"
              name="address"
              value={formData.address}
              onChange={handleInputChange}
              className="w-full px-4 py-2 mt-1 border rounded-md focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            style={{
              backgroundColor: loading || uploadingImage ? "#333" : "#000",
              color: "#fff",
              padding: "0.5rem 1rem",
              borderRadius: "0.375rem",
              cursor: loading || uploadingImage ? "not-allowed" : "pointer",
            }}
            disabled={loading || uploadingImage}
          >
            {loading ? "Creating Property..." : 
            uploadingImage ? "Uploading Image..." : 
            "Create Property"}
          </button>
        </form>

        {/* Error Message */}
        {errorMessage && (
          <div className="mt-4 text-sm text-red-600">
            <strong>Error: </strong>
            {errorMessage}
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div className="mt-4 text-sm text-green-600">
            <strong>Success: </strong>
            {successMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadProperty;