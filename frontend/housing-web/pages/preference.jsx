import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeImage, sendMessageToChat, updateTenantProfile } from "../src/api";
import { UserIcon } from '@heroicons/react/24/solid';

const PreferencePage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [responses, setResponses] = useState({
    step1: "",
    step2: "",
    step3: "",
  });
 
  const [budget, setBudget] = useState(""); // user budget
  const [preferredLocation, setPreferredLocation] = useState("Oakland"); // default location
  const [termsAccepted, setTermsAccepted] = useState(false); // user accept terms
  const [analyzeResult, setAnalyzeResult] = useState(null); // image analysis result
  const [chatMessages, setChatMessages] = useState([]); // chat record
  const [userMessage, setUserMessage] = useState(""); // user input message
  const [imagePreview, setImagePreview] = useState(null); // image preview state
  const [errorMessage, setErrorMessage] = useState(""); // error message state

  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (!token) {
      alert("You need to log in first.");
      navigate("/login");
    }
  }, [navigate]);

  // location and latitude and longitude mapping
  const locationCoordinates = {
    "Oakland": { lat: 40.4418, lng: -79.9561 },
    "Shadyside": { lat: 40.4520, lng: -79.9343 },
    "Squirrel Hill": { lat: 40.4384, lng: -79.9221 },
    "Greenfield": { lat: 40.4268, lng: -79.9390 },
    "Point Breeze": { lat: 40.4446, lng: -79.9081 },
    "Regent Square": { lat: 40.4290, lng: -79.8956 },
    "Bloomfield": { lat: 40.4633, lng: -79.9496 },
    "Friendship": { lat: 40.4583, lng: -79.9398 },
  };
  

  const handleSubmitProfile = async () => {
    try {
      const { lat, lng } = locationCoordinates[preferredLocation];
      const profileData = {
        budget: budget,
        preferred_location: preferredLocation,
        preferred_core_lat: lat,
        preferred_core_lng: lng,
      };

      console.log("Submitting profile data:", profileData); // 调试用
      await updateTenantProfile(profileData);

      setCurrentStep(2); // 跳转到图片分析步骤
    } catch (error) {
      if (error.response) {
        setErrorMessage(error.response.data.detail || "Failed to submit profile.");
      } else {
        setErrorMessage("An unexpected error occurred. Please try again.");
      }
      console.error("Error during profile submission:", error);
    }
  };

  const handleSubmitImage = async () => {
    try {
      const fileInput = document.getElementById("fileUpload");
      if (!fileInput.files.length) {
        setErrorMessage("Please upload a file.");
        return;
      }

      const file = fileInput.files[0];
      const result = await analyzeImage(file, "tenant_preference");
      console.log("Image analysis result:", result);

      setAnalyzeResult(result);
      setErrorMessage(""); 
      setCurrentStep(3);
    } catch (error) {
      console.error("Error during image analysis:", error);
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === "string") {
          setErrorMessage(error.response.data.detail);
        } else if (Array.isArray(error.response.data.detail)) {
          setErrorMessage(error.response.data.detail.map(d => d.msg).join("; "));
        } else {
          setErrorMessage("Server error: " + JSON.stringify(error.response.data.detail));
        }
      } else if (error.message === "Authorization token is missing for analyzeImage.") {
        setErrorMessage("Please log in to analyze images.");
      } else {
        setErrorMessage("An error occurred while analyzing the image. Please try again.");
      }
    }
  };

  const handleSendMessage = async () => {
    if (!userMessage.trim()) {
      setErrorMessage("Please enter a message.");
      return;
    }

    try {
      setChatMessages((prevMessages) => [
        ...prevMessages,
        { sender: "user", text: userMessage },
      ]);

      const response = await sendMessageToChat(userMessage);
      const aiResponse = response?.response || "Sorry, I couldn't process that.";

      setChatMessages((prevMessages) => [
        ...prevMessages,
        { sender: "bot", text: aiResponse },
      ]);

      setUserMessage("");
      setErrorMessage(""); // 清除错误消息
    } catch (error) {
      console.error("Error during chat:", error);
      setErrorMessage("An error occurred while sending your message.");
    }
  };

  // render tenant information form
  const renderProfileForm = () => (
    <div className="register-form" style={{ maxWidth: "400px" }}>
      <h2>Preference</h2>
      <h3>Budget and Preferred Location</h3>
      <p>We will match you with an apartment based on your preferences.</p>
      <div className="form-group">
        <label htmlFor="budget">Budget (USD)</label>
        <input
          type="number"
          id="budget"
          className="form-control"
          value={budget}
          onChange={(e) => setBudget(e.target.value)}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="preferredLocation">Preferred Location</label>
        <select
          id="preferredLocation"
          className="form-control"
          value={preferredLocation}
          onChange={(e) => setPreferredLocation(e.target.value)}
        >
          {Object.keys(locationCoordinates).map((location) => (
            <option key={location} value={location}>
              {location}
            </option>
          ))}
        </select>
      </div>
      <div className="form-checkbox">
        <input
          type="checkbox"
          id="termsAccept"
          checked={termsAccepted}
          onChange={() => setTermsAccepted(!termsAccepted)}
        />
        <label htmlFor="termsAccept">I accept the terms</label>
      </div>
      {errorMessage && (
        <div className="text-red-500 text-sm mt-2">{errorMessage}</div>
      )}
      <button
        onClick={handleSubmitProfile}
        className="register-button"
        disabled={!termsAccepted || !budget}
      >
        Continue
      </button>
    </div>
  );

  // render image analysis form
  const renderImageAnalysis = () => (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <div className="flex justify-between w-full max-w-2xl p-4">
        <h1 className="text-3xl font-bold">Preference,</h1>
        <button className="p-2 bg-gray-200 rounded-full">
          <UserIcon className="w-6 h-6 text-gray-600" />
        </button>
      </div>
      <div className="w-full max-w-xl p-6 bg-white rounded-lg shadow">
        <h3 className="mb-4 text-lg font-semibold">Image Upload</h3>
        <p className="mb-4 text-gray-600">
          Please upload a picture of what you think is your favorite building
        </p>
        <input
          type="file"
          id="fileUpload"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files[0];
            if (file) {
              const previewUrl = URL.createObjectURL(file);
              setImagePreview(previewUrl);
            }
          }}
        />
        <div 
          className="flex items-center justify-center w-full h-48 mb-4 bg-gray-200 rounded-lg cursor-pointer hover:bg-gray-300 transition-colors overflow-hidden"
          onClick={() => document.getElementById('fileUpload').click()}
        >
          {imagePreview ? (
            <img 
              src={imagePreview} 
              alt="Preview" 
              className="w-full h-full object-cover"
            />
          ) : (
            <span className="text-4xl text-gray-400">📷</span>
          )}
        </div>
        {errorMessage && (
          <div className="text-red-500 text-sm mb-4">{errorMessage}</div>
        )}
        <button
          className="w-full px-4 py-2 text-white bg-black rounded"
          onClick={handleSubmitImage}
        >
          Continue
        </button>
      </div>
    </div>
  );

  // render chat interface
  const renderChat = () => (
    <div className="flex flex-col items-center justify-between h-screen bg-gray-100">
      {/* title and description */}
      <div className="w-full max-w-2xl p-6">
        <h1 className="mb-2 text-3xl font-bold">Preference,</h1>
        <p className="mb-4 text-gray-600">Talk about your preferences.</p>
      </div>
  
      {/* chat box */}
      <div className="w-full max-w-2xl flex-1 p-6 bg-white rounded-lg shadow overflow-y-auto">
        {chatMessages.map((msg, index) => (
          <div
            key={index}
            className={`flex mb-4 ${
              msg.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {/* avatar */}
            {msg.sender === "bot" && (
              <div className="w-8 h-8 mr-2 bg-gray-300 rounded-full"></div>
            )}
            <div
              className={`px-4 py-2 rounded-lg ${
                msg.sender === "user"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-black"
              }`}
            >
              {msg.text}
            </div>
            {/* user avatar */}
            {msg.sender === "user" && (
              <img
                src="../head.png"
                alt="User Avatar"
                className="w-8 h-8 ml-2 rounded-full"
              />
            )}
          </div>
        ))}
      </div>
  
      {/* input box and send button */}
      <div className="w-full max-w-2xl p-6">
        <div className="flex items-center">
          <input
            type="text"
            value={userMessage}
            onChange={(e) => setUserMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder="Let's talk about your ideal house!"
            className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSendMessage}
            className="ml-4 px-4 py-2 text-white bg-black rounded-lg hover:bg-gray-800"
          >
            SEND
          </button>
        </div>
        {errorMessage && (
          <div className="text-red-500 text-sm mt-2">{errorMessage}</div>
        )}
      </div>
  
      {/* Next button */}
      <div className="w-full max-w-2xl p-6">
        <button
          className="w-full px-4 py-2 text-white bg-black rounded-lg hover:bg-gray-800"
          onClick={() => navigate("/recommendation")}
        >
          NEXT
        </button>
      </div>
    </div>
  );

  return (
    <div className="register-container">
      {currentStep === 1 && renderProfileForm()}
      {currentStep === 2 && renderImageAnalysis()}
      {currentStep === 3 && renderChat()}
    </div>
  );
};

export default PreferencePage;