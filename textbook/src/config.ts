/**
 * Application configuration for the Physical AI Textbook frontend.
 *
 * This file centralizes all configuration values, making it easy to
 * update for different deployment environments.
 */

// Detect if running in browser and check hostname
const isProduction = (): boolean => {
  if (typeof window === "undefined") return false;
  return window.location.hostname !== "localhost";
};

// Backend API URL
export const API_BASE_URL = isProduction()
  ? "https://faraz7530-physical-ai-textbook-api.hf.space"
  : "http://localhost:8000";

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
