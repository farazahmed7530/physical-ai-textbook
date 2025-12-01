/**
 * Better Auth Configuration
 * https://www.better-auth.com/
 *
 * Using Better Auth React client for Docusaurus
 */

import { API_BASE_URL } from "@site/src/config";
import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
  baseURL: API_BASE_URL,
});

export type Session = typeof authClient.$Infer.Session;
