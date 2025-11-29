/**
 * ChapterTranslateButton - A self-contained translation button for MDX pages.
 *
 * This component automatically extracts content from the page and handles
 * the translation flow without requiring props from MDX.
 */

import { useAuth } from "@site/src/components/AuthProvider";
import { API_BASE_URL } from "@site/src/config";
import React, { useCallback, useState } from "react";
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

  const handleTranslate = useCallback(async () => {
    if (!isAuthenticated || !token || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      // Get the main content from the page
      const mainContent =
        document.querySelector("article")?.textContent ||
        document.querySelector(".markdown")?.textContent ||
        "Chapter content";

      const response = await fetch(`${API_BASE_URL}/api/translate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          chapter_id: chapterId,
          content: mainContent.substring(0, 5000), // Limit content size
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

      // Replace page content with translated version (RTL for Urdu)
      const articleEl =
        document.querySelector("article") ||
        document.querySelector(".markdown");
      if (articleEl && data.translated_content) {
        articleEl.innerHTML =
          `<div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 10px 15px; border-radius: 8px; margin-bottom: 20px; font-size: 14px;">🌐 Translated to Urdu</div>` +
          `<div dir="rtl" style="text-align: right; font-family: 'Noto Nastaliq Urdu', serif; white-space: pre-wrap;">${data.translated_content}</div>`;
      }
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
        disabled={isLoading}
      >
        {isLoading ? "⏳ Translating..." : "🌐 Translate to Urdu"}
      </button>
      {error && <p style={{ color: "red", fontSize: "12px" }}>{error}</p>}
    </div>
  );
}

export default ChapterTranslateButton;
