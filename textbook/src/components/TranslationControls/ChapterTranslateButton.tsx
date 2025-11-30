/**
 * ChapterTranslateButton - A self-contained translation button for MDX pages.
 *
 * This component automatically extracts content from the page and handles
 * the translation flow without requiring props from MDX.
 */

import { useAuth } from "@site/src/components/AuthProvider";
import { API_BASE_URL } from "@site/src/config";
import React, { useCallback, useRef, useState } from "react";
import styles from "./styles.module.css";

interface ChapterTranslateButtonProps {
  chapterId: string;
}

export function ChapterTranslateButton({
  chapterId,
}: ChapterTranslateButtonProps): React.ReactElement | null {
  const { isAuthenticated, token } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isTranslated, setIsTranslated] = useState(false);
  const originalContentRef = useRef<string | null>(null);

  const handleTranslate = useCallback(async () => {
    if (!isAuthenticated || !token || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      // Get the main content from the page
      const articleEl =
        document.querySelector("article") ||
        document.querySelector(".markdown");

      if (!articleEl) {
        throw new Error("Could not find article content");
      }

      // Store original content for restoration
      if (!originalContentRef.current) {
        originalContentRef.current = articleEl.innerHTML;
      }

      const mainContent = articleEl.textContent || "Chapter content";

      const response = await fetch(`${API_BASE_URL}/api/translate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          chapter_id: chapterId,
          content: mainContent.substring(0, 8000), // Limit content size
          language: "ur", // Urdu
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Request failed: ${response.status}`
        );
      }

      const data = await response.json();

      // The translated_content already includes RTL wrapper from backend
      articleEl.innerHTML =
        `<div class="${styles.translatedBanner}">
          <span>🌐 Translated to Urdu</span>
          <button class="${styles.viewOriginalBtn}" id="view-original-translation-btn">View Original</button>
        </div>` + data.translated_content;

      // Add click handler for view original button
      const viewOriginalBtn = document.getElementById(
        "view-original-translation-btn"
      );
      if (viewOriginalBtn && originalContentRef.current) {
        viewOriginalBtn.onclick = () => {
          if (articleEl && originalContentRef.current) {
            articleEl.innerHTML = originalContentRef.current;
            setIsTranslated(false);
          }
        };
      }

      setIsTranslated(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Translation failed";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, token, chapterId, isLoading]);

  if (!isAuthenticated) {
    return (
      <button
        className={styles.translateButton}
        disabled
        title="Sign in to translate"
      >
        🔒 Sign in to Translate
      </button>
    );
  }

  return (
    <div>
      <button
        className={styles.translateButton}
        onClick={handleTranslate}
        disabled={isLoading || isTranslated}
      >
        {isLoading
          ? "⏳ Translating..."
          : isTranslated
          ? "✅ Translated"
          : "🌐 Translate to Urdu"}
      </button>
      {error && <p style={{ color: "red", fontSize: "12px" }}>{error}</p>}
    </div>
  );
}

export default ChapterTranslateButton;
