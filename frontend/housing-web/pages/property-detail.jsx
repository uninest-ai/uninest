import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getPropertyDetails, getPropertyImages } from "../src/api";
import { GoogleMap, LoadScript, Marker, MarkerF } from '@react-google-maps/api';

const mapContainerStyle = {
  width: '100%',
  height: '400px',
  borderRadius: '0.5rem'
};

const googleMapsApiKey = import.meta.env.VITE_GOOGLE_API_KEY;

const PropertyDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [property, setProperty] = useState(null);
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userType, setUserType] = useState(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [mapCenter, setMapCenter] = useState(null);

  useEffect(() => {
    // 从 localStorage 获取用户类型
    const userTypeFromStorage = localStorage.getItem("userType");
    setUserType(userTypeFromStorage);

    const fetchPropertyData = async () => {
      try {
        setLoading(true);
        const [propertyData, imagesData] = await Promise.all([
          getPropertyDetails(id),
          getPropertyImages(id)
        ]);
        
        console.log("Property Data:", propertyData);
        console.log("Images Data:", imagesData);
        
        setProperty(propertyData);
        setImages(imagesData);
        
        // 设置地图中心点
        if (propertyData.latitude && propertyData.longitude) {
          setMapCenter({
            lat: parseFloat(propertyData.latitude),
            lng: parseFloat(propertyData.longitude)
          });
        }
        
        setLoading(false);
      } catch (err) {
        console.error("Error fetching property data:", err);
        setError(err.message || "Failed to load property data");
        setLoading(false);
      }
    };

    if (id) {
      fetchPropertyData();
    }
    
  }, [id]);

  const handleProfileClick = () => {
    if (userType === "landlord") {
      navigate("/landlord-profile");
    } else {
      navigate("/tenant-profile");
    }
  };

  const handleBackToRecommendations = () => {
    navigate("/recommendation"); // 返回推荐页面
  };

  const handlePrevImage = () => {
    setCurrentImageIndex((prev) => (prev > 0 ? prev - 1 : images.length - 1));
  };

  const handleNextImage = () => {
    setCurrentImageIndex((prev) => (prev < images.length - 1 ? prev + 1 : 0));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-500">
          <h2 className="text-xl font-bold">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Property not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      {/* 顶部导航栏 */}
      <div className="fixed top-0 left-0 right-0 bg-white shadow z-50">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
          <h1 
            onClick={() => navigate("/recommendation")}
            className="text-2xl font-bold text-black cursor-pointer hover:text-gray-700 transition-colors"
          >
            UniNest
          </h1>
          <button
            onClick={handleProfileClick}
            className="w-12 h-12 rounded-full bg-white shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 flex items-center justify-center border-2 border-gray-200"
          >
            <img
              src={userType === "landlord" ? "/landlord-avatar.png" : "/tenant-avatar.png"}
              alt="Profile"
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.src = "../head.png";
              }}
            />
          </button>
        </div>
      </div>

      {/* 页面内容 */}
      <div className="max-w-6xl mx-auto px-4 pt-20">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* 图片展示区域 */}
          <div className="relative h-96">
            {images.length > 0 ? (
              <>
                <img
                  src={images[currentImageIndex].image_url}
                  alt={`Property ${currentImageIndex + 1}`}
                  className="w-full h-full object-cover"
                />
                {images.length > 1 && (
                  <>
                    <button
                      onClick={handlePrevImage}
                      className="absolute left-4 top-1/2 transform -translate-y-1/2 !bg-black bg-opacity-50 text-white p-2 rounded-full"
                    >
                      ❮
                    </button>
                    <button
                      onClick={handleNextImage}
                      className="absolute right-4 top-1/2 transform -translate-y-1/2 !bg-black bg-opacity-50 text-white p-2 rounded-full"
                    >
                      ❯
                    </button>
                  </>
                )}
              </>
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gray-200">
                No images available
              </div>
            )}
          </div>

          {/* 缩略图区域 */}
          {images.length > 1 && (
            <div className="flex overflow-x-auto p-4 gap-4">
              {images.map((image, index) => (
                <img
                  key={index}
                  src={image.image_url}
                  alt={`Thumbnail ${index + 1}`}
                  className={`h-20 w-20 object-cover cursor-pointer rounded ${
                    currentImageIndex === index ? "border-2 border-blue-500" : ""
                  }`}
                  onClick={() => setCurrentImageIndex(index)}
                />
              ))}
            </div>
          )}

          {/* 房产信息 */}
          <div className="p-6">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-2xl font-bold text-black">{property.title}</h1>
                <p className="text-gray-800 mt-2">{property.address}</p>
              </div>
              <div className="text-2xl font-bold text-black">
                ${property.price.toLocaleString()}
              </div>
            </div>

            {/* 基本信息 */}
            <div className="mt-6 grid grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-500">Bedrooms</h3>
                <p className="mt-1 text-lg font-semibold text-black">
                  {property?.bedrooms || property?.num_bedrooms || "N/A"}
                </p>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-500">Bathrooms</h3>
                <p className="mt-1 text-lg font-semibold text-black">
                  {property?.bathrooms || property?.num_bathrooms || "N/A"}
                </p>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-500">Area</h3>
                <p className="mt-1 text-lg font-semibold text-black">
                  {property?.area || property?.square_feet || "N/A"} sq ft
                </p>
              </div>
            </div>

            {/* 详细描述 */}
            <div className="mt-6">
              <h2 className="text-lg font-semibold text-black">Description</h2>
              <p className="mt-2 text-gray-800 whitespace-pre-line">
                {property.description}
              </p>
            </div>

            {/* 其他特性 */}
            {property.labels && property.labels.length > 0 && (
              <div className="mt-6">
                <h2 className="text-lg font-semibold text-black">Features</h2>
                <div className="mt-2 flex flex-wrap gap-2">
                  {property.labels.map((label, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-gray-200 text-black rounded-full text-sm"
                    >
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 位置信息和地图 */}
            <div className="mt-6">
              <h2 className="text-lg font-semibold text-black mb-4">Location</h2>
              <p className="text-gray-800 mb-4">
                {property.address}
              </p>
              
              {mapCenter && (
                <div className="w-full h-[400px] rounded-lg overflow-hidden shadow-md">
                  <LoadScript googleMapsApiKey={googleMapsApiKey}>
                    <GoogleMap
                      mapContainerStyle={mapContainerStyle}
                      zoom={15}
                      center={mapCenter}
                    >
                      <MarkerF
                        position={mapCenter}
                        title={property.title}
                      />
                    </GoogleMap>
                  </LoadScript>
                </div>
              )}
            </div>

            {/* 房东信息 */}
            <div className="mt-8 border-t pt-6">
              <h2 className="text-lg font-semibold text-black mb-4">Landlord Information</h2>
              <div className="bg-gray-50 rounded-lg p-6">
                {/* Landlord Name */}
                {property.landlord_name && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-gray-500">Landlord</h3>
                    <p className="mt-1 text-black flex items-center">
                      {property.landlord_name}
                      {property.landlord_verification && (
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          <svg className="mr-1.5 h-2 w-2 text-green-400" fill="currentColor" viewBox="0 0 8 8">
                            <circle cx="4" cy="4" r="3" />
                          </svg>
                          Verified
                        </span>
                      )}
                    </p>
                  </div>
                )}

                {/* Company Name */}
                {property.landlord_company && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-gray-500">Company</h3>
                    <p className="mt-1 text-black">{property.landlord_company}</p>
                  </div>
                )}
                
                {/* Contact Information */}
                {property.landlord_contact && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-gray-500">Contact</h3>
                    <p className="mt-1 text-black">
                      <a 
                        href={`tel:${property.landlord_contact}`}
                        className="text-blue-600 hover:text-blue-800 flex items-center"
                      >
                        <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                        {property.landlord_contact}
                      </a>
                    </p>
                  </div>
                )}
                
                {/* Description/About */}
                {property.landlord_description && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">About the Landlord</h3>
                    <p className="mt-1 text-black whitespace-pre-line">
                      {property.landlord_description}
                    </p>
                  </div>
                )}

                {/* Contact Button */}
                {/* <div className="mt-6">
                  <button
                    onClick={() => navigate(`/chat?landlord=${property.landlord_name}`)}
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    Message Landlord
                  </button>
                </div> */}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertyDetail;