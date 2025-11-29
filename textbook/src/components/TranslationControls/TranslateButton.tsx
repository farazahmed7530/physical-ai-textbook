/**
 * TranslateButton component for triggering content translation to Urdu.
 *
 * Requirements: 8.1
 * - Build button component for chapter pages
 * - Show loading state during translation
 * - Handle errors gracefully
 */

import { useAuth } from "@site/src/components/AuthProvider";
import React, { useCallback, useState } from "react";
import styles from "./styles.module.css";
import type { TranslateButtonProps, TranslatedContentResponse } from "./types";

// API endpoint configuration
const API_ENDPOINT =
  process.env.REACT_APP_API_ENDPOINT || "http://localhost:8000";

// Translate icon as inline SVG component
const TranslateIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M5 8l6 6" />
    <path d="M4 14l6-6 2-3" />
    <path d="M2 5h12" />
    <path d="M7 2v3" />
    <path d="M22 22l-5-10-5 10" />
    <path d="M14 18h6" />
  </svg>
);

/**
 * TranslateButton component.
 *
 * Triggers content translation to Urdu based on chapter content.
 * Shows loading state during API call and handles errors gracefully.
 */
export function TranslateButton({
  chapterId,
  originalContent,
  onTranslate,
  onError,
  className,
  disabled = false,
}: TranslateButtonProps): React.ReactElement | null {
  const { isAuthenticated, token } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleTranslate = useCallback(async () => {
    if (!isAuthenticated || !token || isLoading) return;

    setIsLoading(true);

    try {
      const response = await fetch(`${API_ENDPOINT}/api/translate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          chapter_id: chapterId,
          content: originalContent,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage =
          errorData.detail || `Request failed with status ${response.status}`;
        throw new Error(errorMessage);
      }

      const data: TranslatedContentResponse = await response.json();
      onTranslate(data.translated_content);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Translation failed";
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [
    isAuthenticated,
    token,
    chapterId,
    originalContent,
    onTranslate,
    onError,
    isLoading,
  ]);

  // Don't render if user is not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return (
    <button
      className={`${styles.translateButton} ${className || ""}`}
      onClick={handleTranslate}
      disabled={disabled || isLoading}
      aria-label={
        isLoading ? "Translating content..." : "Translate content to Urdu"
      }
      title="Translate content to Urdu (اردو)"
    >
      {isLoading ? (
        <>
          <span className={styles.spinner} />
          Translating...
        </>
      ) : (
        <>
          <TranslateIcon />
          Translate to Urdu
        </>
      )}
    </button>
  );
}

export default TranslateButton;
