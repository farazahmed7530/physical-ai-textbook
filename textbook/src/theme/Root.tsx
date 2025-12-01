/**
 * Root theme component that wraps the entire Docusaurus site.
 *
 * This component adds the ChatWidget, AuthProvider (Better Auth), and Better Auth Badge
 * to all pages by wrapping the root of the React tree.
 *
 * ✨ BETTER AUTH IMPLEMENTATION ✨
 * https://www.better-auth.com/
 *
 * Requirements: 3.1, 6.1, 6.2
 */

import BrowserOnly from "@docusaurus/BrowserOnly";
import { AuthProvider } from "@site/src/components/AuthProvider";
import { ChatProvider } from "@site/src/components/ChatWidget";
import { API_BASE_URL, API_ENDPOINTS, FEATURES } from "@site/src/config";
import React from "react";

interface RootProps {
  children: React.ReactNode;
}

/**
 * Root component that wraps the entire site with Better Auth and chat functionality.
 */
export default function Root({ children }: RootProps): React.ReactElement {
  return (
    <AuthProvider apiEndpoint={API_BASE_URL}>
      <ChatProvider
        apiEndpoint={API_ENDPOINTS.chat}
        enableTextSelection={FEATURES.enableTextSelection}
      >
        {children}
        <BrowserOnly>
          {() => {
            const BetterAuthBadge =
              require("@site/src/components/BetterAuthBadge").default;
            return <BetterAuthBadge />;
          }}
        </BrowserOnly>
      </ChatProvider>
    </AuthProvider>
  );
}
