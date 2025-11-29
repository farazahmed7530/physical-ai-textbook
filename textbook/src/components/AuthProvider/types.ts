/**
 * Type definitions for AuthProvider.
 * Requirements: 6.2
 */

export interface UserBackground {
  software_experience: "beginner" | "intermediate" | "advanced";
  hardware_experience: "beginner" | "intermediate" | "advanced";
  programming_languages: string[];
  robotics_experience: boolean;
  ai_experience: boolean;
}

export interface User {
  id: string;
  email: string;
  software_experience?: string;
  hardware_experience?: string;
  programming_languages?: string[];
  robotics_experience: boolean;
  ai_experience: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
}

export interface AuthResponse {
  user: User;
  token: TokenResponse;
}

export interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (
    email: string,
    password: string,
    background: UserBackground
  ) => Promise<void>;
  refreshToken: () => Promise<void>;
}

export interface AuthProviderProps {
  children: React.ReactNode;
  apiEndpoint: string;
}
