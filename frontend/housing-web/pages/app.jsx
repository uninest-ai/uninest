// 调试日志：输出所有已加载的组件
console.log("加载的组件：", {
    HomePage: typeof window.HomePage,
    LoginPage: typeof window.LoginPage,
    RegisterPage: typeof window.RegisterPage,
    RecommendationPage: typeof window.RecommendationPage,
    PropertyProfile: typeof window.PropertyProfile,
    RoommateMatchPage: typeof window.RoommateMatchPage
  });
  
  const { useState, useEffect } = React;
  
  // 简单的加载组件
  const LoadingComponent = ({ componentName }) => {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div style={{ marginBottom: '20px' }}>加载{componentName}中...</div>
        <div style={{ width: '50px', height: '50px', border: '5px solid #f3f3f3', borderTop: '5px solid #3498db', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  };
  
  // 错误信息组件
  const ErrorComponent = ({ error, componentName }) => {
    return (
      <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <h2 style={{ color: '#e74c3c' }}>加载{componentName}时出错</h2>
        <p>{error.message || '未知错误'}</p>
        <button 
          onClick={() => window.location.reload()} 
          style={{ padding: '10px 15px', background: '#3498db', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', marginTop: '20px' }}
        >
          重新加载页面
        </button>
      </div>
    );
  };
  
  const App = () => {
    const [page, setPage] = useState(window.location.hash || '#home');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
  
    useEffect(() => {
      // 强制重新检查所有组件
      checkComponents();
      
      const handleHashChange = () => {
        // 重置错误状态
        setError(null);
        setLoading(true);
        
        // 获取基本路由（不含参数）
        const hash = window.location.hash;
        console.log("Hash changed to:", hash);
  
        // 处理特殊路由
        if (hash.startsWith('#profile/')) {
          setPage('#profile');
        } else if (hash === '#roommate-match') {
          setPage('#roommate-match');
        } else if (hash === '#roommate%20match') {
          // 重定向带空格的URL
          console.log("检测到空格编码的URL，重定向到连字符版本");
          window.location.hash = "#roommate-match";
          return; // 避免继续处理
        } else {
          setPage(hash);
        }
  
        // 500ms后关闭加载状态
        setTimeout(() => setLoading(false), 500);
      };
  
      // 如果没有 hash，设置默认值
      if (!window.location.hash) {
        window.location.hash = '#home';
      } else {
        // 初始调用以设置正确的页面
        handleHashChange();
      }
  
      window.addEventListener('hashchange', handleHashChange);
      return () => window.removeEventListener('hashchange', handleHashChange);
    }, []);
  
    // 检查所有组件是否都已定义
    const checkComponents = () => {
      const components = {
        HomePage: window.HomePage,
        LoginPage: window.LoginPage,
        RegisterPage: window.RegisterPage,
        RecommendationPage: window.RecommendationPage,
        PropertyProfile: window.PropertyProfile,
        RoommateMatchPage: window.RoommateMatchPage
      };
  
      console.log("组件状态检查:", Object.keys(components).map(key => `${key}: ${!!components[key]}`).join(', '));
  
      const missingComponents = Object.keys(components).filter(key => !components[key]);
      if (missingComponents.length > 0) {
        console.warn("缺少组件:", missingComponents.join(", "));
      }
    };
  
    // 根据当前页面渲染相应组件
    const renderPage = () => {
      // 如果正在加载，显示加载组件
      if (loading) {
        return <LoadingComponent componentName="页面" />;
      }
  
      // 如果有错误，显示错误组件
      if (error) {
        return <ErrorComponent error={error} componentName="页面" />;
      }
  
      try {
        // 根据页面路径渲染对应组件
        switch(page) {
          case '#home':
          case '':
            return window.HomePage ? React.createElement(window.HomePage) : <LoadingComponent componentName="首页" />;
          case '#login':
            return window.LoginPage ? React.createElement(window.LoginPage) : <LoadingComponent componentName="登录页" />;
          case '#register':
            return window.RegisterPage ? React.createElement(window.RegisterPage) : <LoadingComponent componentName="注册页" />;
          case '#recommendation':
            return window.RecommendationPage ? React.createElement(window.RecommendationPage) : <LoadingComponent componentName="推荐页" />;
          case '#profile':
            return window.PropertyProfile ? React.createElement(window.PropertyProfile) : <LoadingComponent componentName="资料页" />;
          case '#roommate-match':
            console.log("尝试渲染聊天页面，组件存在:", !!window.RoommateMatchPage);
            // 特殊处理聊天页面
            if (!window.RoommateMatchPage) {
              console.error("RoommateMatchPage 组件不存在！");
              return <div>
                <h2>聊天页面无法加载</h2>
                <p>RoommateMatchPage 组件未注册。请检查 roommate-match.js 是否正确加载。</p>
                <button onClick={() => window.location.reload()}>重新加载页面</button>
              </div>;
            }
            return React.createElement(window.RoommateMatchPage);
          default:
            return <div>找不到页面: {page}</div>;
        }
      } catch (err) {
        console.error("渲染页面时出错:", err);
        setError(err);
        return <ErrorComponent error={err} componentName="页面" />;
      }
    };
  
    return (
      <div>
        {renderPage()}
      </div>
    );
  };
  
  // 渲染应用程序
  try {
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(App));
    console.log("应用程序成功渲染");
  } catch (error) {
    console.error("渲染应用程序时出错:", error);
    document.getElementById('root').innerHTML = '<div style="text-align:center;padding:20px;"><h2>应用程序加载失败</h2><p>请查看控制台了解详细信息。</p></div>';
  }

