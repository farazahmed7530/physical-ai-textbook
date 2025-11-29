/**
 * ChapterPersonalizeButton - A self-contained personalization button for MDX pages.
 *
 * This component automatically extracts content from the page and handles
 * the personalization flow without requiring props from MDX.
 */

import { useAuth } from "@site/src/components/AuthProvider";
import { API_BASE_URL } from "@site/src/config";
import React, { useCallback, useState } from "react";
import styles from "./styles.module.css";

interface ChapterPersonalizeButtonProps {
  chapterId: string;
}

export function ChapterPersonalizeButton({
  chapterId,
}: ChapterPersonalizeButtonProps): React.ReactElement | null {
  const { isAuthenticated, token } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [personalizedContent, setPersonalizedContent] = useState<string | null>(
    null
  );

  const handlePersonalize = useCallback(async () => {
    if (!isAuthenticated || !token || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      // Get the main content from the page
      const mainContent =
        document.querySelector("article")?.textContent ||
        document.querySelector(".markdown")?.textContent ||
        "Chapter content";

      const response = await fetch(`${API_BASE_URL}/api/personalize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          chapter_id: chapterId,
          content: mainContent.substring(0, 5000), // Limit content size
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Request failed: ${response.status}`
        );
      }

      const data = await response.json();
      setPersonalizedContent(data.personalized_content);

      // Replace page content with personalized version
      const articleEl =
        document.querySelector("article") ||
        document.querySelector(".markdown");
      if (articleEl && data.personalized_content) {
        articleEl.innerHTML =
          `<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 10px 15px; border-radius: 8px; margin-bottom: 20px; font-size: 14px;">✨ Personalized for your experience level</div>` +
          `<div style="white-space: pre-wrap;">${data.personalized_content}</div>`;
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Personalization failed";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, token, chapterId, isLoading]);

  if (!isAuthenticated) {
    return (
      <button
        className={styles.personalizeButton}
        disabled
        title="Sign in to personalize"
      >
        🔒 Sign in to Personalize
      </button>
    );
  }

  return (
    <div>
      <button
        className={styles.personalizeButton}
        onClick={handlePersonalize}
        disabled={isLoading}
      >
        {isLoading ? "⏳ Personalizing..." : "✨ Personalize for Me"}
      </button>
      {error && <p style={{ color: "red", fontSize: "12px" }}>{error}</p>}
    </div>
  );
}

export default ChapterPersonalizeButton;
