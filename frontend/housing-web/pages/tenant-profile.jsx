import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { checkTenantProfile, getUserProfile, getUserPreferences } from '../src/api';

const TenantProfile = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [preferences, setPreferences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfileData = async () => {
      try {
        setLoading(true);
        // 获取用户基本信息、租客资料和偏好设置
        const [userData, tenantData, preferencesData] = await Promise.all([
          getUserProfile(),
          checkTenantProfile(),
          getUserPreferences()
        ]);
        
        setUserProfile(userData);
        setProfile(tenantData);
        setPreferences(preferencesData);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching profile:', err);
        setError('Failed to load profile data');
        setLoading(false);
      }
    };

    fetchProfileData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userType');
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
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
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/recommendation")}
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
              onClick={() => navigate("/tenant-profile")}
              className="w-12 h-12 rounded-full bg-white shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 flex items-center justify-center border-2 border-gray-200"
            >
              <img
                src="/tenant-avatar.png"
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

      <div className="max-w-4xl mx-auto px-4 mt-16">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* 个人资料头部 */}
          <div className="relative h-48 bg-gradient-to-r from-gray-800 to-black">
            <div className="absolute -bottom-16 left-8">
              <div className="w-32 h-32 rounded-full border-4 border-white bg-white shadow-lg overflow-hidden">
                <img
                  src="../head.png"
                  alt="Profile"
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          </div>

          {/* 个人信息部分 */}
          <div className="pt-20 px-8 pb-8">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  {userProfile?.username || 'User'}
                </h1>
                <p className="text-gray-600 mt-1">{userProfile?.email}</p>
                <div className="mt-4 space-y-2">
                  <p className="text-gray-700">
                    <span className="font-semibold">Budget:</span>{' '}
                    ${profile?.budget}
                  </p>
                  <p className="text-gray-700">
                    <span className="font-semibold">Preferred Location:</span>{' '}
                    {profile?.preferred_location}
                  </p>

                </div>
              </div>
              <div className="space-y-2">
                <button
                  onClick={() => navigate('/preference')}
                  className="!bg-black w-full px-4 py-2 bg-[#000000] text-white rounded-lg hover:bg-[#1a1a1a] transition-colors"
                >
                  Edit Profile
                </button>
                <button
                  onClick={handleLogout}
                  className="!bg-black w-full px-4 py-2 bg-[#000000] text-white rounded-lg hover:bg-[#1a1a1a] transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>

            {/* 偏好设置部分 */}
            <div className="mt-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">My Preferences</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {preferences.map((pref, index) => (
                  <div
                    key={index}
                    className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 capitalize">
                        {pref.preference_key.replace(/_/g, ' ')}
                      </h3>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                        {pref.preference_category}
                      </span>
                    </div>
                    <p className="text-gray-600 mt-1">
                      {typeof pref.preference_value === 'boolean' 
                        ? (pref.preference_value ? 'Yes' : 'No')
                        : pref.preference_value}
                    </p>
                  </div>
                ))}
                {(!preferences || preferences.length === 0) && (
                  <div className="col-span-2 p-8 text-center bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-gray-500">No preferences set yet.</p>
                    <button
                      onClick={() => navigate('/preference')}
                      className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Set Preferences
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* 账户信息 */}
            <div className="mt-8 border-t pt-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4 text-center">Account Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg text-center">
                  <p className="text-gray-600">
                    <span className="font-semibold">Account Type:</span> Tenant
                  </p>
                  <p className="text-gray-600 mt-2">
                    <span className="font-semibold">Member Since:</span>{' '}
                    {new Date(profile?.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenantProfile;