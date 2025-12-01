/**
 * AuthProvider component for authentication state management.
 *
 * ✨ BETTER AUTH IMPLEMENTATION ✨
 * This component uses Better Auth patterns for authentication
 * https://www.better-auth.com/
 *
 * Requirements: 6.2
 * - Implement authentication state management with Better Auth
 * - Handle token storage and refresh
 * - Provide auth hooks for components
 */

import { authClient } from "@site/src/lib/auth";
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
  User,
  UserBackground,
} from "./types";

/**
 * Auth context with default values.
 */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * AuthProvider component using Better Auth.
 */
export function AuthProvider({
  children,
}: AuthProviderProps): React.ReactElement {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Initialize auth state from Better Auth session on mount.
   */
  useEffect(() => {
    // Better Auth React client handles session automatically
    // We'll check session state when needed
    setIsLoading(false);
  }, []);

  /**
   * Login with email and password using Better Auth.
   */
  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const { data, error } = await authClient.signIn.email({
        email,
        password,
      });

      if (error) {
        throw new Error(error.message || "Login failed");
      }

      // Update local state with Better Auth session data
      if (data?.user) {
        setUser({
          id: data.user.id,
          email: data.user.email,
          software_experience: (data.user as any).software_experience,
          hardware_experience: (data.user as any).hardware_experience,
          programming_languages: (data.user as any).programming_languages,
          robotics_experience: (data.user as any).robotics_experience,
          ai_experience: (data.user as any).ai_experience,
          created_at: data.user.createdAt.toISOString(),
        });
        setToken(data.token || null);
      }
    },
    []
  );

  /**
   * Register a new user using Better Auth.
   */
  const register = useCallback(
    async (
      email: string,
      password: string,
      background: UserBackground
    ): Promise<void> => {
      const { data, error } = await authClient.signUp.email({
        email,
        password,
        name: email.split("@")[0], // Use email prefix as name
        // Add background data as custom fields
        ...background,
      });

      if (error) {
        throw new Error(error.message || "Registration failed");
      }

      // Update local state with Better Auth session data
      if (data?.user) {
        setUser({
          id: data.user.id,
          email: data.user.email,
          software_experience: background.software_experience,
          hardware_experience: background.hardware_experience,
          programming_languages: background.programming_languages || [],
          robotics_experience: background.robotics_experience || false,
          ai_experience: background.ai_experience || false,
          created_at: data.user.createdAt.toISOString(),
        });
        setToken(data.token || null);
      }
    },
    []
  );

  /**
   * Logout the current user using Better Auth.
   */
  const logout = useCallback(async (): Promise<void> => {
    await authClient.signOut();
    setUser(null);
    setToken(null);
  }, []);

  /**
   * Refresh the authentication token.
   */
  const refreshToken = useCallback(async (): Promise<void> => {
    // Better Auth handles token refresh automatically
    // Just check if we still have a valid session
    const { data: session } = await authClient.getSession();
    if (session?.user) {
      setUser({
        id: session.user.id,
        email: session.user.email,
        software_experience: (session.user as any).software_experience,
        hardware_experience: (session.user as any).hardware_experience,
        programming_languages: (session.user as any).programming_languages,
        robotics_experience: (session.user as any).robotics_experience,
        ai_experience: (session.user as any).ai_experience,
        created_at: session.user.createdAt.toISOString(),
      });
      setToken((session as any).token || null);
    } else {
      await logout();
      throw new Error("Session expired");
    }
  }, [logout]);

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
