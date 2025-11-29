/**
 * Type definitions for authentication components.
 * Requirements: 6.1, 6.2
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

export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegistrationFormData {
  email: string;
  password: string;
  confirmPassword: string;
  background: UserBackground;
}

export interface FormErrors {
  email?: string;
  password?: string;
  confirmPassword?: string;
  general?: string;
}
