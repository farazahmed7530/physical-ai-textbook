/**
 * Better Auth Configuration
 * https://www.better-auth.com/
 */

import { API_BASE_URL } from "@site/src/config";
import { betterAuth } from "better-auth/client";

export const authClient = betterAuth({
  baseURL: API_BASE_URL,
  // Better Auth will use these endpoints
  endpoints: {
    signIn: "/api/auth/login",
    signUp: "/api/auth/register",
    signOut: "/api/auth/logout",
    getSession: "/api/auth/session",
  },
});

export type Session = typeof authClient.$Infer.Session;
