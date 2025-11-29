/**
 * Root theme component that wraps the entire Docusaurus site.
 *
 * This component adds the ChatWidget and AuthProvider to all pages by wrapping
 * the root of the React tree.
 *
 * Requirements: 3.1, 6.1, 6.2
 */

import { AuthProvider } from "@site/src/components/AuthProvider";
import { ChatProvider } from "@site/src/components/ChatWidget";
import { API_BASE_URL, API_ENDPOINTS, FEATURES } from "@site/src/config";
import React from "react";

interface RootProps {
  children: React.ReactNode;
}

/**
 * Root component that wraps the entire site with auth and chat functionality.
 */
export default function Root({ children }: RootProps): React.ReactElement {
  return (
    <AuthProvider apiEndpoint={API_BASE_URL}>
      <ChatProvider
        apiEndpoint={API_ENDPOINTS.chat}
        enableTextSelection={FEATURES.enableTextSelection}
      >
        {children}
      </ChatProvider>
    </AuthProvider>
  );
}
