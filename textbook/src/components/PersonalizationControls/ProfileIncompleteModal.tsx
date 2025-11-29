/**
 * ProfileIncompleteModal component for prompting users to complete their profile.
 *
 * Requirements: 7.3
 * - Detect users without background data
 * - Prompt to complete profile before personalization
 */

import React, { useCallback, useEffect } from "react";
import styles from "./styles.module.css";
import type { ProfileIncompleteModalProps } from "./types";

// Icons as inline SVG components
const UserAlertIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className={styles.modalIcon}
  >
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
    <line x1="12" y1="17" x2="12" y2="17.01" />
    <line x1="12" y1="13" x2="12" y2="15" />
  </svg>
);

/**
 * ProfileIncompleteModal component.
 *
 * Displays a modal prompting users to complete their profile
 * before they can use the personalization feature.
 */
export function ProfileIncompleteModal({
  isOpen,
  onClose,
  onCompleteProfile,
}: ProfileIncompleteModalProps): React.ReactElement | null {
  // Handle escape key to close modal
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      // Prevent body scroll when modal is open
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) {
    return null;
  }

  // Handle click on overlay to close
  const handleOverlayClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className={styles.modalOverlay}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="profile-incomplete-title"
    >
      <div className={styles.modalContent}>
        <UserAlertIcon />
        <h2 id="profile-incomplete-title" className={styles.modalTitle}>
          Complete Your Profile
        </h2>
        <p className={styles.modalText}>
          To personalize content for your experience level, we need to know a
          bit about your background. Please complete your profile with your
          software and hardware experience.
        </p>
        <div className={styles.modalButtons}>
          <button
            className={styles.modalButtonSecondary}
            onClick={onClose}
            aria-label="Close and continue without personalization"
          >
            Maybe Later
          </button>
          <button
            className={styles.modalButtonPrimary}
            onClick={onCompleteProfile}
            aria-label="Go to profile settings to complete your background information"
          >
            Complete Profile
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProfileIncompleteModal;
