/**
 * PersonalizedContentDisplay component for showing personalized content.
 *
 * Requirements: 7.1, 7.2
 * - Replace chapter content with personalized version
 * - Add indicator showing content is personalized
 * - Provide option to view original content
 */

import React from "react";
import styles from "./styles.module.css";
import type { PersonalizedContentDisplayProps } from "./types";

// Icons as inline SVG components
const CheckCircleIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className={styles.indicatorIcon}
  >
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);

/**
 * PersonalizedContentDisplay component.
 *
 * Displays an indicator that content has been personalized,
 * shows the experience level used, and provides an option
 * to view the original content.
 */
export function PersonalizedContentDisplay({
  personalizedContent,
  experienceLevel,
  fromCache,
  onViewOriginal,
  className,
}: PersonalizedContentDisplayProps): React.ReactElement {
  return (
    <div className={`${styles.personalizedContentWrapper} ${className || ""}`}>
      {/* Personalized content indicator */}
      <div className={styles.personalizedIndicator}>
        <div className={styles.indicatorContent}>
          <CheckCircleIcon />
          <span className={styles.indicatorText}>
            Content personalized for{" "}
            <span className={styles.experienceLevel}>{experienceLevel}</span>{" "}
            level
            {fromCache && (
              <span className={styles.cacheIndicator}>(cached)</span>
            )}
          </span>
        </div>
        <button
          className={styles.viewOriginalButton}
          onClick={onViewOriginal}
          aria-label="View original content"
        >
          View Original
        </button>
      </div>

      {/* Personalized content */}
      <div
        className={styles.personalizedContent}
        dangerouslySetInnerHTML={{ __html: personalizedContent }}
      />
    </div>
  );
}

export default PersonalizedContentDisplay;
