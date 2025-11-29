/**
 * TranslatedContentDisplay component for showing translated content.
 *
 * Requirements: 8.1, 8.3
 * - Replace chapter content with translated version
 * - Apply RTL styling to container
 * - Provide option to view original content
 */

import React from "react";
import styles from "./styles.module.css";
import type { TranslatedContentDisplayProps } from "./types";

// Icons as inline SVG components
const TranslateCheckIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className={styles.indicatorIcon}
  >
    <path d="M5 8l6 6" />
    <path d="M4 14l6-6 2-3" />
    <path d="M2 5h12" />
    <path d="M7 2v3" />
    <circle cx="17" cy="17" r="5" />
    <path d="M15 17l1.5 1.5 3-3" />
  </svg>
);

// Language display names
const LANGUAGE_NAMES: Record<string, string> = {
  ur: "اردو (Urdu)",
  en: "English",
};

/**
 * TranslatedContentDisplay component.
 *
 * Displays an indicator that content has been translated,
 * shows the target language, and provides an option
 * to view the original content.
 * Applies RTL styling for Urdu content.
 */
export function TranslatedContentDisplay({
  translatedContent,
  language,
  fromCache,
  onViewOriginal,
  className,
}: TranslatedContentDisplayProps): React.ReactElement {
  const isRTL = language === "ur";
  const languageDisplayName = LANGUAGE_NAMES[language] || language;

  return (
    <div className={`${styles.translatedContentWrapper} ${className || ""}`}>
      {/* Translated content indicator */}
      <div className={styles.translatedIndicator}>
        <div className={styles.indicatorContent}>
          <TranslateCheckIcon />
          <span className={styles.indicatorText}>
            Content translated to{" "}
            <span className={styles.languageLabel}>{languageDisplayName}</span>
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

      {/* Translated content with RTL support */}
      <div
        className={`${styles.translatedContent} ${
          isRTL ? styles.rtlContent : ""
        }`}
        dir={isRTL ? "rtl" : "ltr"}
        dangerouslySetInnerHTML={{ __html: translatedContent }}
      />
    </div>
  );
}

export default TranslatedContentDisplay;
