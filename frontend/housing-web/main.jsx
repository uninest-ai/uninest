import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './pages/App';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import RecommendationPage from './pages/RecommendationPage';
import PropertyProfile from './pages/PropertyProfile';
import RoommateMatchPage from './pages/RoommateMatchPage';
import EditPropertyPage from './pages/edit-property';

// 注册组件到全局 window 对象
window.HomePage = HomePage;
window.LoginPage = LoginPage;
window.RegisterPage = RegisterPage;
window.RecommendationPage = RecommendationPage;
window.PropertyProfile = PropertyProfile;
window.RoommateMatchPage = RoommateMatchPage;
window.EditPropertyPage = EditPropertyPage;

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
); 