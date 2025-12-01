/**
 * ChatWidget component for the RAG chatbot.
 *
 * This component provides an interactive chat interface that:
 * - Displays a message list with user and assistant messages
 * - Handles message sending and receiving
 * - Shows loading states and error handling
 * - Supports selected text context for contextual questions
 * - Automatically includes current page context
 *
 * Requirements: 3.1
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import styles from "./styles.module.css";
import type {
  ChatMessage,
  ChatResponse,
  ChatWidgetProps,
  Source,
} from "./types";

/**
 * Get the current page context (title and content excerpt).
 */
function getCurrentPageContext(): { title: string; content: string } | null {
  if (typeof document === "undefined") return null;

  // Get page title from breadcrumb or h1
  const breadcrumb = document.querySelector(".breadcrumbs__link--active");
  const h1 = document.querySelector("article h1, .markdown h1");
  const title = breadcrumb?.textContent || h1?.textContent || document.title;

  // Get main content excerpt
  const article =
    document.querySelector("article") || document.querySelector(".markdown");
  const content = article?.textContent?.substring(0, 2000) || "";

  return { title: title.trim(), content: content.trim() };
}

// Default API endpoint - can be overridden via props
const DEFAULT_API_ENDPOINT = "http://localhost:8000/api/chat";

// Icons as inline SVG components
const ChatIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const CloseIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);

/**
 * Generate a unique ID for messages.
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * ChatWidget component.
 */
export function ChatWidget({
  apiEndpoint = DEFAULT_API_ENDPOINT,
  userId,
  selectedText,
  onClearSelectedText,
}: ChatWidgetProps): React.ReactElement {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  /**
   * Send a message to the chat API.
   */
  const sendMessage = useCallback(
    async (query: string) => {
      if (!query.trim() || isLoading) return;

      // Clear any previous error
      setError(null);

      // Add user message
      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        content: query,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setInputValue("");
      setIsLoading(true);

      try {
        // Get current page context
        const pageContext = getCurrentPageContext();

        // Build context string - include page content if available
        let contextText = selectedText || undefined;
        if (pageContext && pageContext.content) {
          // If we have selected text, prepend page title
          // If no selected text, use page content as context
          if (contextText) {
            contextText = `[Page: ${pageContext.title}]\n${contextText}`;
          } else {
            contextText = `[Page: ${pageContext.title}]\n${pageContext.content}`;
          }
        }

        const response = await fetch(apiEndpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query,
            selected_text: contextText,
            user_id: userId || undefined,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.detail || `Request failed with status ${response.status}`
          );
        }

        const data: ChatResponse = await response.json();

        // Add assistant message
        const assistantMessage: ChatMessage = {
          id: generateId(),
          role: "assistant",
          content: data.response,
          sources: data.sources,
          is_fallback: data.is_fallback,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "An unexpected error occurred";
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [apiEndpoint, userId, selectedText, isLoading]
  );

  /**
   * Handle form submission.
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  /**
   * Handle key press in input.
   */
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  /**
   * Toggle chat open/closed.
   */
  const toggleChat = () => {
    setIsOpen((prev) => !prev);
  };

  /**
   * Render a source link.
   */
  const renderSource = (source: Source, index: number) => (
    <a
      key={index}
      href={source.page_url}
      className={styles.sourceLink}
      target="_blank"
      rel="noopener noreferrer"
    >
      {source.section_title} ({source.chapter_id})
    </a>
  );

  /**
   * Render a message.
   */
  const renderMessage = (message: ChatMessage) => (
    <div
      key={message.id}
      className={`${styles.message} ${
        message.role === "user" ? styles.userMessage : styles.assistantMessage
      }`}
    >
      <div>{message.content}</div>
      {message.is_fallback && (
        <div className={styles.fallbackIndicator}>
          ⚠️ No relevant content found in the textbook
        </div>
      )}
      {message.sources && message.sources.length > 0 && (
        <div className={styles.sources}>
          <div className={styles.sourcesLabel}>Sources:</div>
          {message.sources.map(renderSource)}
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Chat toggle button */}
      <button
        className={styles.chatToggle}
        onClick={toggleChat}
        aria-label={isOpen ? "Close chat" : "Open chat"}
        title={isOpen ? "Close chat" : "Ask a question about the textbook"}
      >
        {isOpen ? <CloseIcon /> : <ChatIcon />}
      </button>

      {/* Chat container */}
      {isOpen && (
        <div
          className={styles.chatContainer}
          role="dialog"
          aria-label="Chat with AI assistant"
        >
          {/* Header */}
          <div className={styles.chatHeader}>
            <h3 className={styles.chatTitle}>Ask about the textbook</h3>
            <button
              className={styles.closeButton}
              onClick={toggleChat}
              aria-label="Close chat"
            >
              <CloseIcon />
            </button>
          </div>

          {/* Context banner - shows selected text or current page */}
          {selectedText && (
            <div className={styles.selectedTextBanner}>
              <span className={styles.selectedTextLabel}>Context:</span>
              <span className={styles.selectedTextContent}>{selectedText}</span>
              {onClearSelectedText && (
                <button
                  className={styles.clearSelectedText}
                  onClick={onClearSelectedText}
                  aria-label="Clear selected text"
                >
                  <CloseIcon />
                </button>
              )}
            </div>
          )}

          {/* Messages */}
          <div className={styles.messagesContainer}>
            {messages.length === 0 && !isLoading && (
              <div className={styles.welcomeMessage}>
                <div className={styles.welcomeTitle}>Welcome! 👋</div>
                <div className={styles.welcomeText}>
                  Ask me anything about Physical AI and Humanoid Robotics. I'll
                  search the textbook and provide relevant answers with sources.
                </div>
              </div>
            )}

            {messages.map(renderMessage)}

            {isLoading && (
              <div className={styles.loadingMessage}>
                <div className={styles.loadingDots}>
                  <div className={styles.loadingDot} />
                  <div className={styles.loadingDot} />
                  <div className={styles.loadingDot} />
                </div>
              </div>
            )}

            {error && (
              <div className={styles.errorMessage}>
                <span>⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form className={styles.inputContainer} onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              className={styles.input}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your question..."
              disabled={isLoading}
              aria-label="Chat message input"
            />
            <button
              type="submit"
              className={styles.sendButton}
              disabled={!inputValue.trim() || isLoading}
              aria-label="Send message"
            >
              <SendIcon />
            </button>
          </form>
        </div>
      )}
    </>
  );
}

export default ChatWidget;
