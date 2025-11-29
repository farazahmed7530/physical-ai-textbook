/**
 * ChatProvider context for managing chat state across the application.
 *
 * This provider:
 * - Manages selected text state for contextual questions
 * - Provides the chat widget and text selector to all pages
 * - Handles API endpoint configuration
 *
 * Requirements: 3.1, 3.2
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { ChatWidget } from "./ChatWidget";
import { TextSelector } from "./TextSelector";

interface ChatContextValue {
  /** Currently selected text for context */
  selectedText: string | null;
  /** Set the selected text */
  setSelectedText: (text: string | null) => void;
  /** Clear the selected text */
  clearSelectedText: () => void;
  /** Open the chat widget */
  openChat: () => void;
  /** Whether the chat is open */
  isChatOpen: boolean;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export interface ChatProviderProps {
  children: React.ReactNode;
  /** API endpoint for the chat service */
  apiEndpoint?: string;
  /** User ID for authenticated users */
  userId?: string;
  /** Whether text selection feature is enabled */
  enableTextSelection?: boolean;
}

/**
 * ChatProvider component that wraps the application with chat functionality.
 */
export function ChatProvider({
  children,
  apiEndpoint,
  userId,
  enableTextSelection = true,
}: ChatProviderProps): React.ReactElement {
  const [selectedText, setSelectedText] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);

  const clearSelectedText = useCallback(() => {
    setSelectedText(null);
  }, []);

  const openChat = useCallback(() => {
    setIsChatOpen(true);
  }, []);

  const handleTextSelected = useCallback((text: string) => {
    setSelectedText(text);
    setIsChatOpen(true);
  }, []);

  const contextValue = useMemo<ChatContextValue>(
    () => ({
      selectedText,
      setSelectedText,
      clearSelectedText,
      openChat,
      isChatOpen,
    }),
    [selectedText, clearSelectedText, openChat, isChatOpen]
  );

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
      {enableTextSelection && (
        <TextSelector onTextSelected={handleTextSelected} enabled={true} />
      )}
      <ChatWidget
        apiEndpoint={apiEndpoint}
        userId={userId}
        selectedText={selectedText || undefined}
        onClearSelectedText={clearSelectedText}
      />
    </ChatContext.Provider>
  );
}

/**
 * Hook to access the chat context.
 */
export function useChatContext(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChatContext must be used within a ChatProvider");
  }
  return context;
}

export default ChatProvider;
