/**
 * TranslationControls component for managing content translation.
 *
 * Requirements: 8.1, 8.3
 * - Orchestrates translation button and content display
 * - Manages translation state
 * - Handles errors gracefully
 */

import React, { useCallback, useState } from "react";
import { TranslateButton } from "./TranslateButton";
import { TranslatedContentDisplay } from "./TranslatedContentDisplay";
import styles from "./styles.module.css";
import type { TranslationState } from "./types";

// Error icon as inline SVG
const ErrorIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className={styles.errorIcon}
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

// Close icon for dismissing errors
const CloseIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

interface TranslationControlsProps {
  /** The chapter ID */
  chapterId: string;
  /** The original chapter content */
  originalContent: string;
  /** Custom class name */
  className?: string;
}

/**
 * TranslationControls component.
 *
 * Provides a complete translation UI including:
 * - Translate button for triggering translation
 * - Error display with dismiss option
 * - Translated content display with RTL support
 * - Option to view original content
 */
export function TranslationControls({
  chapterId,
  originalContent,
  className,
}: TranslationControlsProps): React.ReactElement {
  const [state, setState] = useState<TranslationState>({
    isLoading: false,
    error: null,
    translatedContent: null,
    language: null,
    fromCache: false,
    isShowingTranslated: false,
  });

  const handleTranslate = useCallback((content: string) => {
    setState((prev) => ({
      ...prev,
      translatedContent: content,
      language: "ur",
      fromCache: false,
      isShowingTranslated: true,
      error: null,
    }));
  }, []);

  const handleError = useCallback((error: string) => {
    setState((prev) => ({
      ...prev,
      error,
      isLoading: false,
    }));
  }, []);

  const handleViewOriginal = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isShowingTranslated: false,
    }));
  }, []);

  const handleDismissError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  }, []);

  return (
    <div className={className}>
      {/* Error message */}
      {state.error && (
        <div className={styles.errorMessage} role="alert">
          <ErrorIcon />
          <span>{state.error}</span>
          <button
            className={styles.dismissError}
            onClick={handleDismissError}
            aria-label="Dismiss error"
          >
            <CloseIcon />
          </button>
        </div>
      )}

      {/* Show translated content or controls */}
      {state.isShowingTranslated && state.translatedContent ? (
        <TranslatedContentDisplay
          translatedContent={state.translatedContent}
          language={state.language || "ur"}
          fromCache={state.fromCache}
          onViewOriginal={handleViewOriginal}
        />
      ) : (
        <div className={styles.controlsContainer}>
          <TranslateButton
            chapterId={chapterId}
            originalContent={originalContent}
            onTranslate={handleTranslate}
            onError={handleError}
            disabled={state.isLoading}
          />
        </div>
      )}
    </div>
  );
}

export default TranslationControls;
