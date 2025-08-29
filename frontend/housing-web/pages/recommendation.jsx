import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  GoogleMap,
  InfoWindowF,
  MarkerF,
  useLoadScript,
} from "@react-google-maps/api";
import {
  getPropertyRecommendations,
  getRoommateRecommendations,
} from "../src/api"; 

const containerStyle = {
  width: "100%",
  height: "100%",
};

const center = {
  lat: 40.44,
  lng: -79.94,
};



const RecommendationPage = () => {
  const navigate = useNavigate();
  const [properties, setProperties] = useState([]);
  const [roommates, setRoommates] = useState([]);
  const [activeMarker, setActiveMarker] = useState(null);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [mapInstance, setMapInstance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userType, setUserType] = useState(null);

  const libraries = useMemo(() => ["places", "marker"], []);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_API_KEY || "your-fallback-key",
    libraries,
    version: "weekly",
  });

  useEffect(() => {
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      navigate("/login", { state: { from: "/recommendation" } });
      return;
    }

    const userTypeFromStorage = localStorage.getItem("userType");
    setUserType(userTypeFromStorage);

    // 如果用户是房东，直接重定向到房东资料页面
    if (userTypeFromStorage === "landlord") {
      navigate("/landlord-profile");
      return;
    }

    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        const propertyData = await getPropertyRecommendations(10);
        setProperties(propertyData);

        const roommateData = await getRoommateRecommendations(10);
        setRoommates(roommateData);
      } catch (error) {
        if (
          error.response?.status === 401 ||
          error.response?.data?.detail === "Could not validate credentials" ||
          error.message === "Authorization token is missing."
        ) {
          localStorage.removeItem("authToken");
          navigate("/login", { state: { from: "/recommendation" } });
          return;
        }
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [navigate]);

  const handleActiveMarker = (markerId) => {
    // setActiveMarker(markerId === activeMarker ? null : markerId);
    setSelectedProperty(markerId === activeMarker ? null : markerId);
    
    // 如果选中了房产，将其滚动到视图中
    if (markerId !== activeMarker) {
      const element = document.getElementById(`property-${markerId}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  const handlePropertyClick = (propertyId) => {
    navigate(`/property-detail/${propertyId}`);
  };

  const handleChatClick = (roommateId) => {
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      navigate("/login", { state: { from: `/chat/${roommateId}` } });
      return;
    }
    navigate(`/chat/${roommateId}`);
  };

  const handleProfileClick = () => {
    if (userType === "landlord") {
      navigate("/landlord-profile");
    } else {
      navigate("/tenant-profile");
    }
  };

  const handleRoommateMatchClick = () => {
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      navigate("/login", { state: { from: "/roommate-match" } });
      return;
    }
    navigate("/roommate-match");
  };

  const onMapLoad = (map) => {
    setMapInstance(map);
  };

  if (loadError) {
    return <div>Error loading maps. Please try again later.</div>;
  }

  if (!isLoaded) {
    return <div>Loading maps...</div>;
  }

  if (loading) {
    return <div>Loading recommendations...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* 顶部导航栏 */}
      <div className="fixed top-0 left-0 right-0 bg-white shadow z-50">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
          <h1 className="text-2xl font-bold text-black">UniNest</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={handleRoommateMatchClick}
              className="w-10 h-10 rounded-full bg-white shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 flex items-center justify-center border-2 border-gray-200"
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-6 w-6 text-gray-600 hover:text-gray-800" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" 
                />
              </svg>
            </button>
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
      </div>

      {/* 主内容区域 */}
      <div className="flex flex-1 pt-[60px] ">
        {/* 左侧地图 */}
        <div className="flex-1 h-[calc(100vh-60px)] sticky top-[60px]">
          <GoogleMap
            mapContainerStyle={containerStyle}
            center={center}
            zoom={14}
            onLoad={onMapLoad}
            options={{
              zoomControl: true,
              streetViewControl: false,
              mapTypeControl: false,
              fullscreenControl: false,
            }}
          >
            {properties.map((property) => (
              <MarkerF
                key={property.id}
                position={{
                  lat: parseFloat(property.latitude),
                  lng: parseFloat(property.longitude),
                }}
                onClick={() => handleActiveMarker(property.id)}
                label={{
                  text: `$${property.price}\n${property.match_score}%`, // 显示房价和匹配分数
                  className: "custom-marker-label", // 自定义样式类
                }}
              >
                {activeMarker === property.id && (
                  <InfoWindowF
                    position={{
                      lat: parseFloat(property.latitude),
                      lng: parseFloat(property.longitude),
                    }}
                    onCloseClick={() => setActiveMarker(null)}
                  >
                    <div>
                      <h3>{property.title}</h3>
                      <p>
                        ${property.price} / {property.bedrooms}b {property.bathrooms}b
                      </p>
                      <p>Match Score: {property.match_score}%</p>
                      <p>{property.address}</p>
                    </div>
                  </InfoWindowF>
                )}
              </MarkerF>
            ))}
          </GoogleMap>
        </div>

        {/* 右侧房产列表 */}
        <div className="w-[400px] bg-white border-l flex flex-col overflow-y-auto">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Recommended Properties</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-4">
              {properties.map((property) => (
                <div
                  key={property.id}
                  id={`property-${property.id}`}
                  className={`bg-white rounded-lg overflow-hidden shadow transition-all duration-300 cursor-pointer
                    ${selectedProperty === property.id 
                      ? 'ring-2 ring-blue-500 shadow-lg transform scale-[1.02]' 
                      : 'hover:shadow-md'}`}
                  onClick={() => handlePropertyClick(property.id)}
                >
                  <div className="relative h-48">
                    <img
                      src={
                        property.image_url ||
                        "https://images.unsplash.com/photo-1568605114967-8130f3a36994?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80"
                      }
                      alt={property.title}
                      className="w-full h-full object-cover"
                    />
                    <div className={`absolute top-2 right-2 px-2 py-1 rounded text-sm
                      ${selectedProperty === property.id 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-black bg-opacity-70 text-white'}`}>
                      Match Score: {property.match_score}%
                    </div>
                    <div className="absolute bottom-2 left-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-sm">
                      ${property.price} / {property.bedrooms}b{" "}
                      {property.bathrooms}b
                    </div>
                  </div>
                  <div className="p-4">
                    <h3 className="text-lg font-semibold">{property.title}</h3>
                    <p className="text-gray-600 text-sm">{property.address}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 底部推荐室友头像 */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4 z-50">
        <h2 className="text-lg font-semibold mb-2 text-center">
          They are also looking for houses...
        </h2>
        <div className="flex space-x-4 overflow-x-auto">
          {roommates.map((roommate) => (
            <div key={roommate.id} className="flex-shrink-0">
              <div className="flex items-center mb-4 group">
                <div className="cursor-pointer" onClick={() => handleChatClick(roommate.id)}>
                  <img
                    src={roommate.avatar_url || "/head.png"}
                    alt={roommate.username}
                    className="w-12 h-12 rounded-full mr-4 hover:opacity-80 transition-opacity"
                  />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">{roommate.username}</h3>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RecommendationPage;