/**
 * Application configuration for the Physical AI Textbook frontend.
 *
 * This file centralizes all configuration values, making it easy to
 * update for different deployment environments.
 */

// Backend API URL - Update this for production deployment
// For local development: http://localhost:8000
// For Render deployment: https://your-app-name.onrender.com
export const API_BASE_URL =
  typeof window !== "undefined" && window.location.hostname !== "localhost"
    ? "https://physical-ai-textbook-api.onrender.com" // Production - UPDATE THIS
    : "http://localhost:8000"; // Development

// API Endpoints
export const API_ENDPOINTS = {
  // Chat
  chat: `${API_BASE_URL}/api/chat`,

  // Authentication
  register: `${API_BASE_URL}/api/auth/register`,
  login: `${API_BASE_URL}/api/auth/login`,
  logout: `${API_BASE_URL}/api/auth/logout`,
  me: `${API_BASE_URL}/api/auth/me`,

  // Personalization
  personalize: `${API_BASE_URL}/api/personalize`,
  invalidatePersonalization: `${API_BASE_URL}/api/personalize/invalidate`,

  // Translation
  translate: `${API_BASE_URL}/api/translate`,
  rtlCss: `${API_BASE_URL}/api/translate/rtl-css`,
  invalidateTranslation: `${API_BASE_URL}/api/translate/invalidate`,

  // Health
  health: `${API_BASE_URL}/health`,
};

// Feature flags
export const FEATURES = {
  enableTextSelection: true,
  enablePersonalization: true,
  enableTranslation: true,
  enableAuth: true,
};

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  FEATURES,
};
