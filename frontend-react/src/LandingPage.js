// LandingPage.js
import React from 'react';

function LandingPage() {
  const handleLogin = () => {
    window.location.href = "/auth/login";
  };

  return (
    <div className="landing-page">
      <h1 className="title">PDF Chat Assistant</h1>
      <button className="login-button" onClick={handleLogin}>Login</button>
    </div>
  );
}

export default LandingPage;