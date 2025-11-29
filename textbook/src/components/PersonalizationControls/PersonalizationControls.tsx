/**
 * PersonalizationControls component that combines all personalization UI elements.
 *
 * Requirements: 7.1, 7.2, 7.3
 * - Provides personalize button for chapter pages
 * - Shows personalized content with indicator
 * - Handles missing profile data with modal prompt
 */

import { useAuth } from "@site/src/components/AuthProvider";
import React, { useCallback, useState } from "react";
import { PersonalizeButton } from "./PersonalizeButton";
import { PersonalizedContentDisplay } from "./PersonalizedContentDisplay";
import { ProfileIncompleteModal } from "./ProfileIncompleteModal";
import styles from "./styles.module.css";
import type { PersonalizationState } from "./types";

// Icons as inline SVG components
const AlertIcon = () => (
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

const CloseIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

interface PersonalizationControlsProps {
  /** The chapter ID */
  chapterId: string;
  /** The original chapter content (HTML string) */
  originalContent: string;
  /** Callback to render content - receives either original or personalized content */
  onContentChange?: (content: string, isPersonalized: boolean) => void;
  /** Custom class name */
  className?: string;
}

/**
 * PersonalizationControls component.
 *
 * Manages the complete personalization flow including:
 * - Personalize button with loading state
 * - Error handling and display
 * - Profile incomplete modal
 * - Personalized content indicator with view original option
 */
export function PersonalizationControls({
  chapterId,
  originalContent,
  onContentChange,
  className,
}: PersonalizationControlsProps): React.ReactElement | null {
  const { isAuthenticated, user } = useAuth();

  const [state, setState] = useState<PersonalizationState>({
    isLoading: false,
    error: null,
    personalizedContent: null,
    experienceLevel: null,
    fromCache: false,
    isShowingPersonalized: false,
  });

  const [showProfileModal, setShowProfileModal] = useState(false);

  // Handle successful personalization
  const handlePersonalize = useCallback(
    (content: string) => {
      setState((prev) => ({
        ...prev,
        personalizedContent: content,
        isShowingPersonalized: true,
        error: null,
        // Note: experienceLevel and fromCache would ideally come from the API response
        // For now, we'll set defaults - the PersonalizeButton could be enhanced to pass these
        experienceLevel: "personalized",
        fromCache: false,
      }));
      onContentChange?.(content, true);
    },
    [onContentChange]
  );

  // Handle personalization error
  const handleError = useCallback((errorMessage: string) => {
    // Check if it's a profile incomplete error
    if (errorMessage.startsWith("PROFILE_INCOMPLETE:")) {
      setShowProfileModal(true);
      return;
    }

    setState((prev) => ({
      ...prev,
      error: errorMessage,
      isShowingPersonalized: false,
    }));
  }, []);

  // Handle viewing original content
  const handleViewOriginal = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isShowingPersonalized: false,
    }));
    onContentChange?.(originalContent, false);
  }, [originalContent, onContentChange]);

  // Handle re-personalizing (switching back to personalized view)
  const handleShowPersonalized = useCallback(() => {
    if (state.personalizedContent) {
      setState((prev) => ({
        ...prev,
        isShowingPersonalized: true,
      }));
      onContentChange?.(state.personalizedContent, true);
    }
  }, [state.personalizedContent, onContentChange]);

  // Dismiss error
  const handleDismissError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  }, []);

  // Handle profile completion navigation
  const handleCompleteProfile = useCallback(() => {
    setShowProfileModal(false);
    // Navigate to profile/registration page
    // This could be enhanced to open a profile edit modal or navigate to a settings page
    window.location.href = "/profile";
  }, []);

  // Don't render if user is not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className={`${styles.controlsContainer} ${className || ""}`}>
      {/* Error message */}
      {state.error && (
        <div className={styles.errorMessage}>
          <AlertIcon />
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

      {/* Personalized content indicator or personalize button */}
      {state.isShowingPersonalized && state.personalizedContent ? (
        <PersonalizedContentDisplay
          personalizedContent=""
          experienceLevel={state.experienceLevel || "personalized"}
          fromCache={state.fromCache}
          onViewOriginal={handleViewOriginal}
        />
      ) : (
        <>
          <PersonalizeButton
            chapterId={chapterId}
            originalContent={originalContent}
            onPersonalize={handlePersonalize}
            onError={handleError}
          />
          {/* Show "View Personalized" button if we have cached personalized content */}
          {state.personalizedContent && !state.isShowingPersonalized && (
            <button
              className={styles.viewOriginalButton}
              onClick={handleShowPersonalized}
              aria-label="View personalized content"
            >
              View Personalized
            </button>
          )}
        </>
      )}

      {/* Profile incomplete modal */}
      <ProfileIncompleteModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
        onCompleteProfile={handleCompleteProfile}
      />
    </div>
  );
}

export default PersonalizationControls;
