/**
 * PersonalizeButton component for triggering content personalization.
 *
 * Requirements: 7.1
 * - Build button component for chapter pages
 * - Show loading state during personalization
 * - Handle errors gracefully
 */

import { useAuth } from "@site/src/components/AuthProvider";
import React, { useCallback, useState } from "react";
import styles from "./styles.module.css";
import type {
  PersonalizeButtonProps,
  PersonalizedContentResponse,
} from "./types";

// API endpoint configuration
import { API_BASE_URL } from "@site/src/config";
const API_ENDPOINT = API_BASE_URL;

// Icons as inline SVG components
const PersonalizeIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

/**
 * PersonalizeButton component.
 *
 * Triggers content personalization based on user background.
 * Shows loading state during API call and handles errors gracefully.
 */
export function PersonalizeButton({
  chapterId,
  originalContent,
  onPersonalize,
  onError,
  className,
  disabled = false,
}: PersonalizeButtonProps): React.ReactElement | null {
  const { isAuthenticated, token } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handlePersonalize = useCallback(async () => {
    if (!isAuthenticated || !token || isLoading) return;

    setIsLoading(true);

    try {
      const response = await fetch(`${API_ENDPOINT}/api/personalize`, {
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

        // Check if it's an incomplete profile error (422)
        if (response.status === 422) {
          throw new Error("PROFILE_INCOMPLETE:" + errorMessage);
        }

        throw new Error(errorMessage);
      }

      const data: PersonalizedContentResponse = await response.json();
      onPersonalize(data.personalized_content);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Personalization failed";
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [
    isAuthenticated,
    token,
    chapterId,
    originalContent,
    onPersonalize,
    onError,
    isLoading,
  ]);

  // Don't render if user is not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return (
    <button
      className={`${styles.personalizeButton} ${className || ""}`}
      onClick={handlePersonalize}
      disabled={disabled || isLoading}
      aria-label={
        isLoading
          ? "Personalizing content..."
          : "Personalize content for my experience level"
      }
      title="Adapt content to your experience level"
    >
      {isLoading ? (
        <>
          <span className={styles.spinner} />
          Personalizing...
        </>
      ) : (
        <>
          <PersonalizeIcon />
          Personalize for Me
        </>
      )}
    </button>
  );
}

export default PersonalizeButton;
