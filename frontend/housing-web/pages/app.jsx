
  
  const { useState, useEffect } = React;
  
  // loading component
  const LoadingComponent = ({ componentName }) => {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div style={{ marginBottom: '20px' }}>loading {componentName}...</div>
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
  
  // error component
  const ErrorComponent = ({ error, componentName }) => {
    return (
      <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <h2 style={{ color: '#e74c3c' }}>error loading {componentName}</h2>
        <p>{error.message || 'unknown error'}</p>
        <button 
          onClick={() => window.location.reload()} 
          style={{ padding: '10px 15px', background: '#3498db', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', marginTop: '20px' }}
        >
          reload page
        </button>
      </div>
    );
  };
  
  const App = () => {
    const [page, setPage] = useState(window.location.hash || '#home');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
  
    useEffect(() => {

      checkComponents();
      
      const handleHashChange = () => {
        // reset error and loading
        setError(null);
        setLoading(true);
        
        // get basic route (without parameters)
        const hash = window.location.hash;
        console.log("Hash changed to:", hash);
  
        // handle special routes
        if (hash.startsWith('#profile/')) {
          setPage('#profile');
        } else if (hash === '#roommate-match') {
          setPage('#roommate-match');
        } else if (hash === '#roommate%20match') {
          // redirect URL with space
          console.log("detected URL with space, redirect to hyphen version");
          window.location.hash = "#roommate-match";
          return; // avoid continue processing
        } else {
          setPage(hash);
        }
  
        // close loading after 500ms
        setTimeout(() => setLoading(false), 500);
      };
  
      // if no hash, set default value
      if (!window.location.hash) {
        window.location.hash = '#home';
      } else {
        // initial call to set the correct page
        handleHashChange();
      }
  
      window.addEventListener('hashchange', handleHashChange);
      return () => window.removeEventListener('hashchange', handleHashChange);
    }, []);
  
    // check all components are defined
    const checkComponents = () => {
      const components = {
        HomePage: window.HomePage,
        LoginPage: window.LoginPage,
        RegisterPage: window.RegisterPage,
        RecommendationPage: window.RecommendationPage,
        PropertyProfile: window.PropertyProfile,
        RoommateMatchPage: window.RoommateMatchPage
      };
  
      console.log("component status check:", Object.keys(components).map(key => `${key}: ${!!components[key]}`).join(', '));
  
      const missingComponents = Object.keys(components).filter(key => !components[key]);
      if (missingComponents.length > 0) {
        console.warn("missing components:", missingComponents.join(", "));
      }
    };
  
    // render corresponding component based on current page
    const renderPage = () => {
      // if loading, show loading component
      if (loading) {
        return <LoadingComponent componentName="page" />;
      }
  
      // if there is an error, show error component
      if (error) {
        return <ErrorComponent error={error} componentName="page" />;
      }
  
      try {
        // render corresponding component based on page path
        switch(page) {
          case '#home':
          case '':
            return window.HomePage ? React.createElement(window.HomePage) : <LoadingComponent componentName="home page" />;
          case '#login':
            return window.LoginPage ? React.createElement(window.LoginPage) : <LoadingComponent componentName="login page" />;
          case '#register':
            return window.RegisterPage ? React.createElement(window.RegisterPage) : <LoadingComponent componentName="register page" />;
          case '#recommendation':
            return window.RecommendationPage ? React.createElement(window.RecommendationPage) : <LoadingComponent componentName="recommendation page" />;
          case '#profile':
            return window.PropertyProfile ? React.createElement(window.PropertyProfile) : <LoadingComponent componentName="profile page" />;
          case '#roommate-match':
            // special handling for chat page
            if (!window.RoommateMatchPage) {
              console.error("RoommateMatchPage component not found!");
              return <div>
                <h2> chat page not found</h2>
                <p>RoommateMatchPage component not registered. Please check roommate-match.js is loaded correctly.</p>
                <button onClick={() => window.location.reload()}>reload page</button>
              </div>;
            }
            return React.createElement(window.RoommateMatchPage);
          default:
            return <div>page not found: {page}</div>;
        }
      } catch (err) {
        console.error("error rendering page:", err);
        setError(err);
        return <ErrorComponent error={err} componentName="page" />;
      }
    };
  
    return (
      <div>
        {renderPage()}
      </div>
    );
  };
  
  // render application
  try {
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(App));
    console.log("application rendered successfully");
  } catch (error) {
    console.error("error rendering application:", error);
    document.getElementById('root').innerHTML = '<div style="text-align:center;padding:20px;"><h2>application failed to load</h2><p>please check console for details.</p></div>';
  }

