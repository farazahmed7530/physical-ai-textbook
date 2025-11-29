/**
 * AuthProvider component for authentication state management.
 *
 * Requirements: 6.2
 * - Implement authentication state management
 * - Handle token storage and refresh
 * - Provide auth hooks for components
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type {
  AuthContextValue,
  AuthProviderProps,
  AuthResponse,
  User,
  UserBackground,
} from "./types";

const TOKEN_STORAGE_KEY = "auth_token";
const USER_STORAGE_KEY = "auth_user";
const TOKEN_EXPIRY_KEY = "auth_token_expiry";

/**
 * Auth context with default values.
 */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Check if we're in a browser environment.
 */
function isBrowser(): boolean {
  return typeof window !== "undefined";
}

/**
 * Get stored token from localStorage.
 */
function getStoredToken(): string | null {
  if (!isBrowser()) return null;
  try {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);

    if (token && expiry) {
      const expiryDate = new Date(expiry);
      if (expiryDate > new Date()) {
        return token;
      }
      // Token expired, clear storage
      clearStorage();
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Get stored user from localStorage.
 */
function getStoredUser(): User | null {
  if (!isBrowser()) return null;
  try {
    const userJson = localStorage.getItem(USER_STORAGE_KEY);
    return userJson ? JSON.parse(userJson) : null;
  } catch {
    return null;
  }
}

/**
 * Store auth data in localStorage.
 */
function storeAuthData(token: string, user: User, expiresAt: string): void {
  if (!isBrowser()) return;
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiresAt);
  } catch {
    // Storage might be full or disabled
    console.warn("Failed to store auth data");
  }
}

/**
 * Clear auth data from localStorage.
 */
function clearStorage(): void {
  if (!isBrowser()) return;
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  } catch {
    // Ignore errors
  }
}

/**
 * AuthProvider component.
 */
export function AuthProvider({
  children,
  apiEndpoint,
}: AuthProviderProps): React.ReactElement {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Initialize auth state from storage on mount.
   */
  useEffect(() => {
    const storedToken = getStoredToken();
    const storedUser = getStoredUser();

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(storedUser);
    }
    setIsLoading(false);
  }, []);

  /**
   * Handle successful authentication response.
   */
  const handleAuthSuccess = useCallback((response: AuthResponse) => {
    const { user: authUser, token: tokenData } = response;
    setUser(authUser);
    setToken(tokenData.access_token);
    storeAuthData(tokenData.access_token, authUser, tokenData.expires_at);
  }, []);

  /**
   * Login with email and password.
   */
  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const response = await fetch(`${apiEndpoint}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error("Invalid credentials");
      }

      const data: AuthResponse = await response.json();
      handleAuthSuccess(data);
    },
    [apiEndpoint, handleAuthSuccess]
  );

  /**
   * Register a new user.
   */
  const register = useCallback(
    async (
      email: string,
      password: string,
      background: UserBackground
    ): Promise<void> => {
      const response = await fetch(`${apiEndpoint}/api/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password, background }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Registration failed");
      }

      const data: AuthResponse = await response.json();
      handleAuthSuccess(data);
    },
    [apiEndpoint, handleAuthSuccess]
  );

  /**
   * Logout the current user.
   */
  const logout = useCallback(async (): Promise<void> => {
    if (token) {
      try {
        await fetch(`${apiEndpoint}/api/auth/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });
      } catch {
        // Ignore logout API errors, still clear local state
      }
    }

    setUser(null);
    setToken(null);
    clearStorage();
  }, [apiEndpoint, token]);

  /**
   * Refresh the authentication token.
   */
  const refreshToken = useCallback(async (): Promise<void> => {
    if (!token) {
      throw new Error("No token to refresh");
    }

    try {
      const response = await fetch(`${apiEndpoint}/api/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        // Token refresh failed, logout
        await logout();
        throw new Error("Session expired");
      }

      const data: AuthResponse = await response.json();
      handleAuthSuccess(data);
    } catch (error) {
      await logout();
      throw error;
    }
  }, [apiEndpoint, token, logout, handleAuthSuccess]);

  const contextValue: AuthContextValue = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    login,
    logout,
    register,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
}

/**
 * Hook to access auth context.
 * @throws Error if used outside AuthProvider
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

/**
 * Hook to check if user is authenticated.
 */
export function useIsAuthenticated(): boolean {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}

/**
 * Hook to get current user.
 */
export function useCurrentUser(): User | null {
  const { user } = useAuth();
  return user;
}

export default AuthProvider;
