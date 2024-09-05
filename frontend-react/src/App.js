// App.js
import React, { useState, useEffect } from 'react';
import LandingPage from './LandingPage';
import ChatInterface from './ChatInterface';
import Cookies from 'js-cookie';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    const checkLoginStatus = () => {
      const encodedUserInfo = Cookies.get('userinfo');
      if (encodedUserInfo) {
        const decodedUserInfo = JSON.parse(atob(encodedUserInfo));
        setUserInfo(decodedUserInfo);
        setIsLoggedIn(true);
        Cookies.remove('userinfo', { path: '/' }); // Adjust path if needed
      }
    };

    checkLoginStatus();
  }, []);

  const handleLogout = async () => {
    const sessionHint = Cookies.get('session_hint');
    window.location.href = `/auth/logout?session_hint=${sessionHint}`;
  };

  return (
    <div className="app-container">
      {isLoggedIn ? (
        <ChatInterface userInfo={userInfo} onLogout={handleLogout} />
      ) : (
        <LandingPage />
      )}
    </div>
  );
}

export default App;