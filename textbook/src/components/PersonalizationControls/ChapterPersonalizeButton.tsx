/**
 * ChapterPersonalizeButton - A self-contained personalization button for MDX pages.
 *
 * This component automatically extracts content from the page and handles
 * the personalization flow without requiring props from MDX.
 */

import { useAuth } from "@site/src/components/AuthProvider";
import { API_BASE_URL } from "@site/src/config";
import React, { useCallback, useRef, useState } from "react";
import styles from "./styles.module.css";

interface ChapterPersonalizeButtonProps {
  chapterId: string;
}

/**
 * Simple markdown to HTML converter for basic formatting.
 * Handles headers, bold, italic, lists, code blocks, and links.
 */
function markdownToHtml(markdown: string): string {
  let html = markdown;

  // Escape HTML entities first
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code blocks (must be done before other formatting)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="language-${
      lang || "text"
    }">${code.trim()}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Headers
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

  // Unordered lists
  html = html.replace(/^\* (.+)$/gm, "<li>$1</li>");
  html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");

  // Paragraphs (double newlines)
  html = html.replace(/\n\n+/g, "</p><p>");
  html = `<p>${html}</p>`;

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, "");
  html = html.replace(/<p>(<h[1-6]>)/g, "$1");
  html = html.replace(/(<\/h[1-6]>)<\/p>/g, "$1");
  html = html.replace(/<p>(<pre>)/g, "$1");
  html = html.replace(/(<\/pre>)<\/p>/g, "$1");
  html = html.replace(/<p>(<ul>)/g, "$1");
  html = html.replace(/(<\/ul>)<\/p>/g, "$1");

  return html;
}

export function ChapterPersonalizeButton({
  chapterId,
}: ChapterPersonalizeButtonProps): React.ReactElement | null {
  const { isAuthenticated, token } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPersonalized, setIsPersonalized] = useState(false);
  const originalContentRef = useRef<string | null>(null);

  // Reset state when chapterId changes (navigating to a new page)
  useEffect(() => {
    setIsPersonalized(false);
    setError(null);
    originalContentRef.current = null;
  }, [chapterId]);

  const handlePersonalize = useCallback(async () => {
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

      // Store original content for restoration (capture fresh content if not personalized)
      if (!originalContentRef.current || !isPersonalized) {
        originalContentRef.current = articleEl.innerHTML;
      }

      const mainContent = articleEl.textContent || "Chapter content";

      const response = await fetch(`${API_BASE_URL}/api/personalize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          chapter_id: chapterId,
          content: mainContent.substring(0, 8000), // Limit content size
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Request failed: ${response.status}`
        );
      }

      const data = await response.json();

      // Convert markdown to HTML and replace page content
      const htmlContent = markdownToHtml(data.personalized_content);

      articleEl.innerHTML =
        `<div class="${styles.personalizedBanner}">
          <span>✨ Personalized for your experience level</span>
          <button class="${styles.viewOriginalBtn}" id="view-original-btn">View Original</button>
        </div>` + `<div class="personalized-content">${htmlContent}</div>`;

      setIsPersonalized(true);

      // Add click handler for view original button after a short delay
      setTimeout(() => {
        const viewOriginalBtn = document.getElementById("view-original-btn");
        if (viewOriginalBtn) {
          viewOriginalBtn.onclick = () => {
            if (articleEl && originalContentRef.current) {
              articleEl.innerHTML = originalContentRef.current;
              setIsPersonalized(false);
              // Don't reset originalContentRef - keep it for next personalization
            }
          };
        }
      }, 100);
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
        disabled={isLoading || isPersonalized}
      >
        {isLoading
          ? "⏳ Personalizing..."
          : isPersonalized
          ? "✅ Personalized"
          : "✨ Personalize for Me"}
      </button>
      {error && <p style={{ color: "red", fontSize: "12px" }}>{error}</p>}
    </div>
  );
}

export default ChapterPersonalizeButton;
