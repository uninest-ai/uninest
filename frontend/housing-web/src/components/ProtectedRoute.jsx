import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const location = useLocation();

  useEffect(() => {
    // 检查localStorage中是否有认证令牌和用户角色
    const authToken = localStorage.getItem('authToken');
    const role = localStorage.getItem('userRole');
    setIsAuthenticated(!!authToken);
    setUserRole(role);
  }, []);

  // 如果认证状态尚未确定，显示加载中
  if (isAuthenticated === null) {
    return <div>Loading...</div>;
  }

  // 如果未认证，重定向到登录页面，并保留当前位置信息以便登录后返回
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 如果是房东访问推荐页面，重定向到房东个人页面
  if (userRole === 'landlord' && location.pathname === '/recommendation') {
    return <Navigate to="/landlord-profile" replace />;
  }

  // 如果已认证，渲染子组件
  return children;
};

export default ProtectedRoute; 