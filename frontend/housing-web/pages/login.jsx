import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { loginUser, checkLandlordProfile, checkTenantProfile, getUserProfile } from "../src/api"; // 引入 API 方法

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const location = useLocation();

  // 获取用户尝试访问的页面 
  const from = location.state?.from?.pathname || "/recommendation";
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    // 检查输入是否为空
    if (!email || !password) {
        setError("Email and password are required.");
        return;
    }

    try {
      // 调用登录 API
      const response = await loginUser(email, password);
      const { access_token, token_type } = response;

      // 保存 token 到 localStorage
      const authToken = `${token_type} ${access_token}`;
      localStorage.setItem("authToken", authToken);
      setMessage("Login successful! Redirecting...");

      // check user personal profile
      setTimeout( async() => {
        try {       
            //if there is no profile, get user type and navigate to corresponding profile page
            const userProfile = await getUserProfile();
            const userType = userProfile["user_type"];
            
            // 存储用户类型到 localStorage
            localStorage.setItem("userType", userType);

            if (userType === "tenant") {
                const tenantProfile = await checkTenantProfile();
                if (tenantProfile) {
                    // 重定向到用户尝试访问的页面或推荐页面
                    navigate(from, { replace: true });
                    return;
                }
                navigate("/preference");
            } else if (userType === "landlord") {
                const landlordProfile = await checkLandlordProfile();
                if (landlordProfile) {
                    // 重定向到用户尝试访问的页面或推荐页面
                    navigate(from, { replace: true });
                    return;
                }
                navigate("/agent-register");
            }
        } catch (err) {
            console.error("Error checking user profile:", err);
            if (err.response?.status === 401) {
              setError("Session expired or unauthorized. Please log in again.");
              localStorage.removeItem("authToken"); // 清除无效的 token
              navigate("/login"); // 重定向到登录页面
            } else {
              setError("An error occurred while fetching user profile.");
            }
          }
      }, 1000);
    } catch (err) {
        console.error("Login failed:", err.response?.data);
        if (err.response?.status === 422) {
          setError("Invalid username or password. Please check your credentials.");
        } else if (err.response?.status === 401) {
            setError("Session expired or unauthorized. Please log in again.");
            localStorage.removeItem("authToken"); // 清除无效的 token
            navigate("/login"); // 重定向到登录页面
        } else {
          setError("An error occurred. Please try again.");
        }
      }
  };

  const navigateToRegister = () => {
    navigate("/register");
  };

  return (
    <div className="login-container">
      <div className="login-header">
        <h2>Log in</h2>
      </div>

      <div className="login-form">
        <form onSubmit={handleLogin}>
          {/* Email 输入框 */}
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              className="form-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>

          {/* Password 输入框 */}
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          {/* 登录按钮 */}
          <button type="submit" className="login-button">
            Log In
          </button>
        </form>

        {/* 成功或错误消息 */}
        {message && <p className="alert alert-success">{message}</p>}
        {error && <p className="alert alert-danger">{error}</p>}

        {/* 跳转到注册页面 */}
        <div className="register-options">
          <span>Don't have an account?</span>
          <a onClick={navigateToRegister}>Register</a>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;