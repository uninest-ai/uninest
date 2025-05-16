import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const location = useLocation();

  useEffect(() => {
    // check if there is an authentication token and user role in localStorage
    const authToken = localStorage.getItem('authToken');
    const role = localStorage.getItem('userRole');
    setIsAuthenticated(!!authToken);
    setUserRole(role);
  }, []);

  // if the authentication status is not determined, show loading
  if (isAuthenticated === null) {
    return <div>Loading...</div>;
  }

  // if not authenticated, redirect to login page, and keep the current location information so that it can be returned after login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // if the user is a landlord and visits the recommendation page, redirect to the landlord personal page
  if (userRole === 'landlord' && location.pathname === '/recommendation') {
    return <Navigate to="/landlord-profile" replace />;
  }

  // if authenticated, render the child component
  return children;
};

export default ProtectedRoute; 