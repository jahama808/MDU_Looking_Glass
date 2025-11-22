// API Configuration
// Automatically uses the correct server address whether accessing locally or remotely

const getApiBaseUrl = () => {
  // If we're in development mode and accessing via localhost, use localhost
  // Otherwise, use the current hostname with port 5000
  const hostname = window.location.hostname;

  // If accessing via localhost or 127.0.0.1, keep using localhost
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:5000';
  }

  // Otherwise, use the actual server hostname/IP with port 5000
  return `http://${hostname}:5000`;
};

export const API_BASE_URL = getApiBaseUrl();

// Helper function to get headers with auth token
export const getAuthHeaders = (token) => {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};
