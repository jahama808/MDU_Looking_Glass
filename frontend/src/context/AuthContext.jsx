import { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [sessionToken, setSessionToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  // Check if user is already logged in on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('session_token');
    const storedUser = localStorage.getItem('user');

    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:5000/api/auth/check', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setSessionToken(token);
        setAuthenticated(true);
      } else {
        // Session expired or invalid
        logout();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = (userData, token) => {
    setUser(userData);
    setSessionToken(token);
    setAuthenticated(true);
    localStorage.setItem('session_token', token);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const logout = async () => {
    const token = sessionToken || localStorage.getItem('session_token');

    if (token) {
      try {
        await fetch('http://localhost:5000/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          credentials: 'include',
        });
      } catch (error) {
        console.error('Logout request failed:', error);
      }
    }

    setUser(null);
    setSessionToken(null);
    setAuthenticated(false);
    localStorage.removeItem('session_token');
    localStorage.removeItem('user');
  };

  const value = {
    user,
    sessionToken,
    authenticated,
    loading,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
