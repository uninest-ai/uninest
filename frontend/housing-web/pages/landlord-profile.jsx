import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getLandlordProfile, getPropertyDetails, deleteProperty, getPropertyImages } from "../src/api";

const LandlordProfilePage = () => {
  const [profileData, setProfileData] = useState({
    name: "",
    company_name: "",
    contact_phone: "",
    description: "",
    verification_status: false,
    user_id: null,
    rating: 4.8,
    listed_properties: [], // dynamic loaded property list
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [propertyImages, setPropertyImages] = useState({}); // store images for each property
  const [deleteConfirm, setDeleteConfirm] = useState(null); // store property id to delete
  const [username, setUsername] = useState(""); // store username

  const navigate = useNavigate();

  const fetchLandlordProfile = async () => {
    // check if logged in
    const authToken = localStorage.getItem("authToken");
    if (!authToken) {
      console.log("No auth token found, redirecting to login");
      navigate("/login", { state: { from: "/landlord-profile" } });
      return;
    }

    try {
      console.log("Fetching landlord profile with token:");
      const data = await getLandlordProfile();
      console.log("Received landlord profile data:", data);
      
      if (!data) {
        console.log("No profile data received, redirecting to agent-register");
        navigate("/agent-register");
        return;
      }

      // get user info
      const userInfo = localStorage.getItem("userInfo");
      let extractedUsername = "";
      if (userInfo) {
        try {
          const parsedUserInfo = JSON.parse(userInfo);
          extractedUsername = parsedUserInfo.email || "";
          console.log("Extracted username from localStorage:", extractedUsername);
        } catch (e) {
          console.error("Error parsing user info from localStorage:", e);
        }
      }
      setUsername(extractedUsername);

      // set more complete profile info
      setProfileData({
        name: data.company_name || "Unknown Landlord",
        company_name: data.company_name || "",
        contact_phone: data.contact_phone || "",
        description: data.description || "",
        verification_status: data.verification_status || false,
        user_id: data.user_id || null,
        rating: 4.8, // temporarily fixed value
        listed_properties: data.listed_properties || [],
      });

      // dynamic load images for each property
      const images = {};
      for (const property of data.listed_properties || []) {
        try {
          const propertyImages = await getPropertyImages(property.id);
          // find primary image, if no primary image, use first image, if no image, use default image
          const primaryImage = propertyImages.find(img => img.is_primary) || propertyImages[0];
          images[property.id] = primaryImage ? primaryImage.image_url : "https://placehold.co/600x400?text=No+Image";
        } catch (err) {
          console.error(`Failed to fetch images for property ${property.id}:`, err);
          images[property.id] = "https://placehold.co/600x400?text=No+Image";
        }
      }
      setPropertyImages(images);
    } catch (err) {
      console.error("Error fetching landlord profile:", err);
      if (err.response?.status === 401) {
        console.log("Unauthorized access, redirecting to login");
        navigate("/login", { state: { from: "/landlord-profile" } });
        return;
      }
      setError(err.message || "Failed to fetch landlord profile.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLandlordProfile();
  }, []);

  const handleEditProfile = () => {
    navigate("/agent-register"); 
  };

  const handlePostNewProperty = () => {
    navigate("/upload-property"); 
  };

  const handlePropertyClick = (propertyId) => {
    navigate(`/property-detail/${propertyId}`); 
  };

  const handleEditClick = (e, propertyId) => {
    e.stopPropagation(); // prevent event bubbling to card click
    navigate(`/edit-property/${propertyId}`); 
  };

  const handleDeleteClick = (e, propertyId) => {
    e.stopPropagation(); // prevent event bubbling to card click
    setDeleteConfirm(propertyId);
  };

  const handleConfirmDelete = async (propertyId) => {
    try {
      console.log("Attempting to delete property:", propertyId);
      await deleteProperty(propertyId);
      console.log("Property deleted successfully");
      // get landlord profile again to update list
      await fetchLandlordProfile();
      setDeleteConfirm(null); // close confirm dialog
    } catch (err) {
      console.error("Error deleting property:", err);
      let errorMessage = "Failed to delete property. ";
      
      if (err.response) {
        // server returned error response
        console.error("Server response:", err.response.data);
        errorMessage += `Server error: ${err.response.data.message || err.response.statusText}`;
      } else if (err.request) {
        // request sent but no response
        console.error("No response received:", err.request);
        errorMessage += "No response received from server. Please check your connection.";
      } else {
        // request configuration error
        console.error("Request configuration error:", err.message);
        errorMessage += err.message;
      }
      
      setError(errorMessage);
      setDeleteConfirm(null); // close confirm dialog
    }
  };

  const handleLogout = () => {
    // clear auth info in local storage
    localStorage.removeItem("authToken");
    localStorage.removeItem("userInfo");
    // redirect to login page
    navigate("/login"); 
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div style={{ color: "red" }}>Error: {error}</div>;
  }

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f5f5f5", padding: "20px" }}>
      {/* Top Navigation Bar */}
      <div
        style={{
          backgroundColor: "white",
          padding: "15px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderRadius: "8px",
          marginBottom: "20px",
          boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
        }}
      >
        <div className="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
          <h1 
            onClick={() => navigate("/recommendation")}
            className="text-2xl font-bold text-black cursor-pointer hover:text-gray-700 transition-colors"
          >
            UniNest
          </h1>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          {/* <button
            onClick={() => navigate("/recommendation")}
            style={{
              padding: "10px 15px",
              backgroundColor: "#333",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Back to Home
          </button> */}
          <button
            onClick={handleLogout}
            style={{
              padding: "10px 15px",
              backgroundColor: "#dc3545",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          gap: "20px",
          flexWrap: "wrap",
        }}
      >
        {/* Left Side - Profile Information */}
        <div
          style={{
            flex: "0 0 300px",
            backgroundColor: "white",
            padding: "20px",
            borderRadius: "8px",
            boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div style={{ textAlign: "center", marginBottom: "20px" }}>
            <div style={{ 
              width: "100px", 
              height: "100px", 
              borderRadius: "50%", 
              backgroundColor: "#f0f0f0",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "40px",
              fontWeight: "bold",
              color: "#007bff",
              margin: "0 auto 15px auto"
            }}>
              {profileData.company_name ? profileData.company_name.charAt(0).toUpperCase() : "?"}
            </div>
            <h2 style={{ margin: "0 0 5px 0", fontSize: "22px", fontWeight: "bold" }}>{profileData.company_name}</h2>
            {/* <p style={{ color: "#666", marginBottom: "10px" }}>Username: {username}</p> */}
            {/* <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "15px" }}>
              <span style={{ marginRight: "5px", fontWeight: "bold" }}>{profileData.rating}</span>
              <span style={{ color: "#ffc107" }}>★★★★★</span>
            </div> */}
          </div>

          <div style={{ marginBottom: "20px" }}>
            <div style={{ marginBottom: "15px" }}>
              {/* <h3 style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "5px" }}>Contact Information</h3> */}
              <p style={{ margin: "0 0 5px 0" }}><strong>Phone:</strong> {profileData.contact_phone || "Not provided"}</p>
              <p style={{ margin: "0" }}><strong>Email:</strong> {username || "Not provided"}</p>
            </div>
            
            <div style={{ marginBottom: "15px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "5px" }}>Description</h3>
              <p style={{ margin: "0", color: "#555" }}>{profileData.description || "No description provided."}</p>
            </div>
            
            {/* <div style={{ marginBottom: "15px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "5px" }}>Verification Status</h3>
              <p style={{ 
                margin: "0", 
                color: profileData.verification_status ? "green" : "orange",
                fontWeight: "bold"
              }}>
                {profileData.verification_status ? "Verified ✓" : "Not Verified"}
              </p>
            </div> */}
          </div>

          {/* Edit Profile Button */}
          <button
            onClick={handleEditProfile}
            style={{
              padding: "10px 20px",
              backgroundColor: "#333",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              marginBottom: "15px",
              fontWeight: "bold",
            }}
          >
            Edit Profile
          </button>

          {/* Post New Property Button */}
          <button
            onClick={handlePostNewProperty}
            style={{
              padding: "10px 20px",
              backgroundColor: "#333",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            Post New Property
          </button>
        </div>

        {/* Right Side - Property List */}
        <div
          style={{
            flex: "1",
            backgroundColor: "white",
            padding: "20px",
            borderRadius: "8px",
            boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
          }}
        >
          <h3>My Properties</h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: "20px",
            }}
          >
            {profileData.listed_properties.map((property) => (
              <div
                key={property.id}
                style={{
                  border: "1px solid #e0e0e0",
                  borderRadius: "8px",
                  overflow: "hidden",
                  cursor: "pointer",
                }}
                onClick={() => handlePropertyClick(property.id)}
              >
                <div className="relative h-48">
                  <img
                    src={propertyImages[property.id] || "https://via.placeholder.com/280x180"}
                    alt="Property"
                    className="w-full h-full object-cover"
                  />
                  <div style={{ position: "absolute", top: "0.5rem", right: "0.5rem", display: "flex", gap: "0.5rem" }}>
                    <button
                      onClick={(e) => handleEditClick(e, property.id)}
                      style={{
                        padding: "0.25rem 0.75rem",
                        backgroundColor: "#28a745",
                        color: "white",
                        border: "none",
                        borderRadius: "0.375rem",
                        fontSize: "0.875rem",
                        cursor: "pointer",
                        transition: "background-color 0.3s",
                      }}
                      onMouseOver={(e) => (e.target.style.backgroundColor = "#218838")}
                      onMouseOut={(e) => (e.target.style.backgroundColor = "#28a745")}
                    >
                      Edit
                    </button>
                    <button
                      onClick={(e) => handleDeleteClick(e, property.id)}
                      style={{
                        padding: "0.25rem 0.75rem",
                        backgroundColor: "#dc3545",
                        color: "white",
                        border: "none",
                        borderRadius: "0.375rem",
                        fontSize: "0.875rem",
                        cursor: "pointer",
                        transition: "background-color 0.3s",
                      }}
                      onMouseOver={(e) => (e.target.style.backgroundColor = "#c82333")}
                      onMouseOut={(e) => (e.target.style.backgroundColor = "#dc3545")}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div style={{ padding: "15px" }}>
                  <h4>${property.price} / month</h4>
                  <p>
                    {property.bedrooms} bd | {property.bathrooms} ba | {property.area} sqft
                  </p>
                  <p>{property.address}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* delete confirm dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Confirm Delete</h3>
            <p className="text-gray-600 mb-6">Are you sure you want to delete this property? This action cannot be undone.</p>
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={() => handleConfirmDelete(deleteConfirm)}
                style={{
                  backgroundColor: "black", 
                  color: "white",
                  padding: "0.5rem 1rem", 
                  borderRadius: "0.375rem", 
                  cursor: "pointer", 
                  transition: "background-color 0.3s", 
                }}
                onMouseOver={(e) => (e.target.style.backgroundColor = "gray")} 
                onMouseOut={(e) => (e.target.style.backgroundColor = "black")} 
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LandlordProfilePage;