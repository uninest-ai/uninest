import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerUser } from "../src/api"; // 假设有 API 方法用于注册

const RegisterPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [username, setUsername] = useState("");
  const [userType, setUserType] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    // 验证密码和确认密码是否匹配
    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match!");
      return;
    }

    const userData = {
      email,
      username,
      user_type: userType,
      password,
      confirm_password: confirmPassword,
    };

    try {
      // 调用注册 API，将用户数据提交
      await registerUser(userData);

      // 设置成功消息
      setSuccessMessage("Registration successful! Redirecting to login...");

      // 跳转到登录页面
      setTimeout(() => {
        navigate("/login");
      }, 1000); // 延迟 2 秒跳转
    } catch (error) {
      console.error("Backend error response:", error.response?.data);
      if (error.response && error.response.data) {
        const backendError = error.response.data.detail;
        if (Array.isArray(backendError)) {
          // 如果后端返回多个错误，拼接显示
          setErrorMessage(backendError.map((err) => err.msg).join(", "));
        } else if (typeof backendError === "string") {
          // if back end returns a string error
          setErrorMessage(backendError);
        } else {
          setErrorMessage("Registration failed. Please try again.");
        }
      } else {
        setErrorMessage("Registration failed. Please try again.");
      }
    }
  };


  const navigateToLogin = (e) => {
    e.preventDefault();
    navigate("/login"); // 跳转到登录页面
  };

  return (
    <div className="register-container">
      <div className="register-header">
        <h2>Register</h2>
      </div>

      <div className="register-form">
        <form onSubmit={handleSubmit}>
          {/* Email 输入框 */}
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              className="form-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          {/* Username 输入框 */}
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              className="form-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
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
              required
            />
          </div>

          {/* Confirm Password 输入框 */}
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              className="form-control"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          {/* 用户类型选择 */}
          <div className="form-group">
            <label>I am</label>
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  name="userType"
                  value="tenant"
                  checked={userType === "tenant"}
                  onChange={(e) => setUserType(e.target.value)}
                />
                Tenant
              </label>
              <label>
                <input
                  type="radio"
                  name="userType"
                  value="landlord"
                  checked={userType === "landlord"}
                  onChange={(e) => setUserType(e.target.value)}
                />
                Landlord
              </label>
            </div>
          </div>


          {/* 注册按钮 */}
          <button
            type="submit"
            className="register-button"
            disabled={!email || !password || !username || !confirmPassword}
          >
            Register
          </button>


        </form>

        {/* 成功或错误消息 */}
        {successMessage && <p className="success-message">{successMessage}</p>}
        {errorMessage && <p className="error-message">{errorMessage}</p>}
      </div>
    </div>
  );
};

export default RegisterPage;