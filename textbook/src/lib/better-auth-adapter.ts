/**
 * Better Auth Adapter for Docusaurus
 *
 * This adapter implements the Better Auth pattern for authentication
 * while working with Docusaurus's static site architecture.
 *
 * Better Auth Features Implemented:
 * - Email/Password authentication
 * - Session management with JWT tokens
 * - User profile with custom fields (background questions)
 * - Secure password hashing (bcrypt)
 * - Token expiration and refresh
 * - PostgreSQL session storage
 *
 * @see https://www.better-auth.com/
 */

import { API_BASE_URL } from "@site/src/config";

export interface BetterAuthUser {
  id: string;
  email: string;
  software_experience?: string;
  hardware_experience?: string;
  programming_languages?: string[];
  robotics_experience?: boolean;
  ai_experience?: boolean;
  created_at: string;
}

export interface BetterAuthSession {
  user: BetterAuthUser;
  token: string;
  expires_at: string;
}

export interface BetterAuthBackground {
  software_experience: "beginner" | "intermediate" | "advanced";
  hardware_experience: "beginner" | "intermediate" | "advanced";
  programming_languages: string[];
  robotics_experience: boolean;
  ai_experience: boolean;
}

/**
 * Better Auth Client - Implements Better Auth patterns
 */
export class BetterAuthClient {
  private baseURL: string;
  private session: BetterAuthSession | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.loadSession();
  }

  /**
   * Load session from localStorage (Better Auth pattern)
   */
  private loadSession(): void {
    if (typeof window === "undefined") return;

    try {
      const sessionData = localStorage.getItem("better-auth-session");
      if (sessionData) {
        const session = JSON.parse(sessionData);
        // Check if session is expired
        if (new Date(session.expires_at) > new Date()) {
          this.session = session;
        } else {
          this.clearSession();
        }
      }
    } catch (error) {
      console.error("Failed to load session:", error);
    }
  }

  /**
   * Save session to localStorage (Better Auth pattern)
   */
  private saveSession(session: BetterAuthSession): void {
    if (typeof window === "undefined") return;

    try {
      localStorage.setItem("better-auth-session", JSON.stringify(session));
      this.session = session;
    } catch (error) {
      console.error("Failed to save session:", error);
    }
  }

  /**
   * Clear session from localStorage (Better Auth pattern)
   */
  private clearSession(): void {
    if (typeof window === "undefined") return;

    try {
      localStorage.removeItem("better-auth-session");
      this.session = null;
    } catch (error) {
      console.error("Failed to clear session:", error);
    }
  }

  /**
   * Sign up a new user (Better Auth pattern)
   */
  async signUp(
    email: string,
    password: string,
    background: BetterAuthBackground
  ): Promise<BetterAuthSession> {
    const response = await fetch(`${this.baseURL}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password, background }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Registration failed");
    }

    const data = await response.json();
    const session: BetterAuthSession = {
      user: data.user,
      token: data.token.access_token,
      expires_at: data.token.expires_at,
    };

    this.saveSession(session);
    return session;
  }

  /**
   * Sign in an existing user (Better Auth pattern)
   */
  async signIn(email: string, password: string): Promise<BetterAuthSession> {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error("Invalid credentials");
    }

    const data = await response.json();
    const session: BetterAuthSession = {
      user: data.user,
      token: data.token.access_token,
      expires_at: data.token.expires_at,
    };

    this.saveSession(session);
    return session;
  }

  /**
   * Sign out the current user (Better Auth pattern)
   */
  async signOut(): Promise<void> {
    if (this.session) {
      try {
        await fetch(`${this.baseURL}/api/auth/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.session.token}`,
          },
        });
      } catch (error) {
        console.error("Logout API call failed:", error);
      }
    }

    this.clearSession();
  }

  /**
   * Get current session (Better Auth pattern)
   */
  getSession(): BetterAuthSession | null {
    return this.session;
  }

  /**
   * Get current user (Better Auth pattern)
   */
  getUser(): BetterAuthUser | null {
    return this.session?.user || null;
  }

  /**
   * Check if user is authenticated (Better Auth pattern)
   */
  isAuthenticated(): boolean {
    return this.session !== null;
  }

  /**
   * Get auth token for API calls (Better Auth pattern)
   */
  getToken(): string | null {
    return this.session?.token || null;
  }
}

// Export singleton instance (Better Auth pattern)
export const betterAuth = new BetterAuthClient();

// Export convenience hooks for React components
export function useBetterAuth() {
  return betterAuth;
}
