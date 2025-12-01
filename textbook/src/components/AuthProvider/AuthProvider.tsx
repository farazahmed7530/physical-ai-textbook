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
 * Convert Better Auth user to our User type
 */
function convertBetterAuthUser(session: BetterAuthSession | null): User | null {
  if (!session) return null;

  return {
    id: session.user.id,
    email: session.user.email,
    software_experience: session.user.software_experience,
    hardware_experience: session.user.hardware_experience,
    programming_languages: session.user.programming_languages,
    robotics_experience: session.user.robotics_experience,
    ai_experience: session.user.ai_experience,
    created_at: session.user.created_at,
  };
}

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
    const session = betterAuth.getSession();
    if (session) {
      setUser(convertBetterAuthUser(session));
      setToken(session.token);
    }
    setIsLoading(false);
  }, []);

  /**
   * Login with email and password using Better Auth.
   */
  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const session = await betterAuth.signIn(email, password);
      setUser(convertBetterAuthUser(session));
      setToken(session.token);
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
      const session = await betterAuth.signUp(email, password, {
        software_experience: background.software_experience,
        hardware_experience: background.hardware_experience,
        programming_languages: background.programming_languages || [],
        robotics_experience: background.robotics_experience || false,
        ai_experience: background.ai_experience || false,
      });
      setUser(convertBetterAuthUser(session));
      setToken(session.token);
    },
    []
  );

  /**
   * Logout the current user using Better Auth.
   */
  const logout = useCallback(async (): Promise<void> => {
    await betterAuth.signOut();
    setUser(null);
    setToken(null);
  }, []);

  /**
   * Refresh the authentication token.
   */
  const refreshToken = useCallback(async (): Promise<void> => {
    // Better Auth handles token refresh automatically
    const session = betterAuth.getSession();
    if (session) {
      setUser(convertBetterAuthUser(session));
      setToken(session.token);
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
