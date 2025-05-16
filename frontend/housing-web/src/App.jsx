import React, { useState, useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import "./style.css";
import LoginPage from "../pages/login";
import HomePage from "../pages/Homepage";
import ProfilePage from "../pages/profile";
import RecommendationPage from "../pages/recommendation";
import RegisterPage from "../pages/register";
import RoommatePage from "../pages/roommate-match";
import PropertyDetail from "../pages/property-detail";
import LandlordPage from "../pages/landlord-profile";
import PreferencePage from "../pages/preference";
import AgentPage from "../pages/agent-register";
import UploadPropertyPage from "../pages/upload-property";
import TenantProfile from "../pages/tenant-profile";
import ProtectedRoute from "./components/ProtectedRoute";
import ChatPage from "../pages/chat";
import EditPropertyPage from "../pages/edit-property";
const App = () => {
  const [loading, setLoading] = useState(true);
 
  // Simulate loading after page loading
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false),20 ); // Simulate loading 0.02 seconds
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    // Loading animation
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          flexDirection: "column",
        }}
      >
        <h2>UniNest</h2>
        <div
          style={{
            width: "50px",
            height: "50px",
            border: "5px solid #f3f3f3",
            borderTop: "5px solid #3498db",
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
          }}
        ></div>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
      </div>
    );
  }

  return (
    <Routes>
      {/* Redirect root path to recommendation page */}
      <Route path="/" element={<Navigate to="/recommendation" replace />} />
      
      {/* Public routes - no authentication required */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/homepage" element={<HomePage />} />
      
      {/* Protected routes - require authentication */}
      <Route 
        path="/recommendation" 
        element={
          <ProtectedRoute>
            <RecommendationPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/profile" 
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/roommate-match" 
        element={
          <ProtectedRoute>
            <RoommatePage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/property-detail/:id" 
        element={
          <ProtectedRoute>
            <PropertyDetail />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/landlord-profile" 
        element={
          <ProtectedRoute>
            <LandlordPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/preference" 
        element={
          <ProtectedRoute>
            <PreferencePage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/agent-register" 
        element={
          <ProtectedRoute>
            <AgentPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/upload-property" 
        element={
          <ProtectedRoute>
            <UploadPropertyPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/tenant-profile" 
        element={
          <ProtectedRoute>
            <TenantProfile />
          </ProtectedRoute>
        } 
      />
      < Route 
        path="/edit-property/:id" 
        element={
          <ProtectedRoute>
            <EditPropertyPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/chat/:userId" 
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        } 
      />
    </Routes>
  );
};

export default App;