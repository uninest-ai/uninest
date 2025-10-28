import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeImage, sendMessageToChatFull, getChatPreferences, updateTenantProfile } from "../src/api";
import { UserIcon } from '@heroicons/react/24/solid';

const PreferencePage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [responses, setResponses] = useState({
    step1: "",
    step2: "",
    step3: "",
  });
 
  const [budget, setBudget] = useState(""); // user budget
  const [preferredLocation, setPreferredLocation] = useState("Manhattan"); // default location
  const [termsAccepted, setTermsAccepted] = useState(false); // user accept terms
  const [analyzeResult, setAnalyzeResult] = useState(null); // image analysis result
  const [chatMessages, setChatMessages] = useState([
    { sender: "bot", text: "Let's talk about what kind of room you like!" }
  ]); // chat record with initial welcome message
  const [userMessage, setUserMessage] = useState(""); // user input message
  const [imagePreview, setImagePreview] = useState(null); // image preview state
  const [errorMessage, setErrorMessage] = useState(""); // error message state
  const [isImageLoading, setIsImageLoading] = useState(false); // image analysis loading state
  const [isChatLoading, setIsChatLoading] = useState(false); // chat response loading state
  const [userPreferences, setUserPreferences] = useState([]); // user preferences from chat

  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (!token) {
      alert("You need to log in first.");
      navigate("/login");
    }
  }, [navigate]);

  // location and latitude and longitude mapping (NYC neighborhoods)
  const locationCoordinates = {
    "Manhattan": { lat: 40.7831, lng: -73.9712 },
    "Brooklyn": { lat: 40.6782, lng: -73.9442 },
    "Queens": { lat: 40.7282, lng: -73.7949 },
    "Bronx": { lat: 40.8448, lng: -73.8648 },
    "Upper East Side": { lat: 40.7736, lng: -73.9566 },
    "Upper West Side": { lat: 40.7870, lng: -73.9754 },
    "East Village": { lat: 40.7265, lng: -73.9815 },
    "Williamsburg": { lat: 40.7081, lng: -73.9571 },
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

      setIsImageLoading(true);
      setErrorMessage("");

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
    } finally {
      setIsImageLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!userMessage.trim()) {
      setErrorMessage("Please enter a message.");
      return;
    }

    try {
      setIsChatLoading(true);
      setErrorMessage("");

      setChatMessages((prevMessages) => [
        ...prevMessages,
        { sender: "user", text: userMessage },
      ]);

      const response = await sendMessageToChatFull(userMessage);
      const aiResponse = response?.response || "Sorry, I couldn't process that.";
      const preferences = response?.preferences || [];

      setChatMessages((prevMessages) => [
        ...prevMessages,
        { sender: "bot", text: aiResponse },
      ]);

      // Update preferences if new ones are returned
      if (preferences.length > 0) {
        setUserPreferences(preferences);
      }

      setUserMessage("");
    } catch (error) {
      console.error("Error during chat:", error);
      setErrorMessage("An error occurred while sending your message.");
    } finally {
      setIsChatLoading(false);
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
        <label htmlFor="preferredLocation">Preferred Location (Current version only applicable in New York) </label>
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
          className="w-full px-4 py-2 text-white bg-black rounded disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
          onClick={handleSubmitImage}
          disabled={isImageLoading}
        >
          {isImageLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing...
            </>
          ) : (
            "Continue"
          )}
        </button>
      </div>
    </div>
  );

  // render chat interface
  const renderChat = () => (
    <div className="flex flex-col items-center justify-between h-screen bg-gray-100">
      {/* title and description */}
      <div className="w-full max-w-4xl p-6">
        <h1 className="mb-2 text-3xl font-bold">Preference,</h1>
        <p className="mb-4 text-gray-600">Talk about your preferences.</p>
      </div>

      {/* Main content area with chat and preferences side by side */}
      <div className="w-full max-w-4xl flex-1 flex gap-4 px-6">
        {/* chat box */}
        <div className="flex-1 p-6 bg-white rounded-lg shadow overflow-y-auto">
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
        {isChatLoading && (
          <div className="flex justify-start mb-4">
            <div className="w-8 h-8 mr-2 bg-gray-300 rounded-full"></div>
            <div className="px-4 py-2 bg-gray-200 text-black rounded-lg">
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Thinking...
              </div>
            </div>
          </div>
        )}
        </div>

        {/* Preferences panel */}
        <div className="w-80 p-4 bg-white rounded-lg shadow overflow-y-auto">
          <h3 className="text-lg font-semibold mb-3">Your Preferences</h3>
          {userPreferences.length === 0 ? (
            <p className="text-gray-500 text-sm">No preferences collected yet. Chat with the AI to discover your ideal home!</p>
          ) : (
            <div className="space-y-2">
              {userPreferences.map((pref, index) => (
                <div key={index} className="p-3 bg-gray-50 rounded border border-gray-200">
                  <div className="font-medium text-sm text-gray-700">{pref.key}</div>
                  <div className="text-sm text-gray-600 mt-1">{pref.value}</div>
                  {pref.category && (
                    <span className="inline-block mt-2 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                      {pref.category}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* input box and send button */}
      <div className="w-full max-w-4xl p-6">
        <div className="flex items-center">
          <input
            type="text"
            value={userMessage}
            onChange={(e) => setUserMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !isChatLoading) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder="Let's talk about your ideal house!"
            className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            disabled={isChatLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isChatLoading}
            className="ml-4 px-4 py-2 text-white bg-black rounded-lg hover:bg-gray-800 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            SEND
          </button>
        </div>
        {errorMessage && (
          <div className="text-red-500 text-sm mt-2">{errorMessage}</div>
        )}
      </div>
  
      {/* Next button */}
      <div className="w-full max-w-4xl p-6">
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