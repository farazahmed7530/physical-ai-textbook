/**
 * TextSelector utility for capturing user text selections.
 *
 * This component:
 * - Listens for text selection events on the page
 * - Captures selected text and passes it to the chat context
 * - Shows a tooltip/button when text is selected
 *
 * Requirements: 3.2
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import styles from "./TextSelector.module.css";

export interface TextSelectorProps {
  /** Callback when text is selected and user wants to ask about it */
  onTextSelected: (text: string) => void;
  /** Whether the selector is enabled */
  enabled?: boolean;
  /** Container element to listen for selections (defaults to document) */
  containerRef?: React.RefObject<HTMLElement>;
}

interface SelectionPosition {
  x: number;
  y: number;
}

/**
 * TextSelector component that shows a tooltip when text is selected.
 */
export function TextSelector({
  onTextSelected,
  enabled = true,
  containerRef,
}: TextSelectorProps): React.ReactElement | null {
  const [selectedText, setSelectedText] = useState<string>("");
  const [position, setPosition] = useState<SelectionPosition | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  /**
   * Get the selected text from the window selection.
   */
  const getSelectedText = useCallback((): string => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      return "";
    }
    return selection.toString().trim();
  }, []);

  /**
   * Calculate position for the tooltip based on selection.
   */
  const calculatePosition = useCallback((): SelectionPosition | null => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return null;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    // Position tooltip above the selection, centered
    return {
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
    };
  }, []);

  /**
   * Handle mouse up event to check for text selection.
   */
  const handleMouseUp = useCallback(() => {
    if (!enabled) return;

    // Small delay to ensure selection is complete
    setTimeout(() => {
      const text = getSelectedText();

      if (text && text.length > 0) {
        const pos = calculatePosition();
        if (pos) {
          setSelectedText(text);
          setPosition(pos);
          setIsVisible(true);
        }
      } else {
        setIsVisible(false);
        setSelectedText("");
        setPosition(null);
      }
    }, 10);
  }, [enabled, getSelectedText, calculatePosition]);

  /**
   * Handle click outside to hide tooltip.
   */
  const handleClickOutside = useCallback(
    (e: MouseEvent) => {
      if (
        tooltipRef.current &&
        !tooltipRef.current.contains(e.target as Node)
      ) {
        // Check if there's still a selection
        const text = getSelectedText();
        if (!text) {
          setIsVisible(false);
          setSelectedText("");
          setPosition(null);
        }
      }
    },
    [getSelectedText]
  );

  /**
   * Handle the "Ask about this" button click.
   */
  const handleAskClick = useCallback(() => {
    if (selectedText) {
      onTextSelected(selectedText);
      // Clear selection
      window.getSelection()?.removeAllRanges();
      setIsVisible(false);
      setSelectedText("");
      setPosition(null);
    }
  }, [selectedText, onTextSelected]);

  /**
   * Handle keyboard shortcut (Ctrl/Cmd + Shift + A).
   */
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;

      // Ctrl/Cmd + Shift + A to ask about selection
      if (
        (e.ctrlKey || e.metaKey) &&
        e.shiftKey &&
        e.key.toLowerCase() === "a"
      ) {
        const text = getSelectedText();
        if (text) {
          e.preventDefault();
          onTextSelected(text);
          window.getSelection()?.removeAllRanges();
          setIsVisible(false);
          setSelectedText("");
          setPosition(null);
        }
      }
    },
    [enabled, getSelectedText, onTextSelected]
  );

  // Set up event listeners
  useEffect(() => {
    if (!enabled) return;

    const container = containerRef?.current || document;

    container.addEventListener("mouseup", handleMouseUp);
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      container.removeEventListener("mouseup", handleMouseUp);
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [enabled, containerRef, handleMouseUp, handleClickOutside, handleKeyDown]);

  // Handle scroll to hide tooltip
  useEffect(() => {
    const handleScroll = () => {
      if (isVisible) {
        setIsVisible(false);
      }
    };

    window.addEventListener("scroll", handleScroll, true);
    return () => window.removeEventListener("scroll", handleScroll, true);
  }, [isVisible]);

  if (!isVisible || !position) {
    return null;
  }

  return (
    <div
      ref={tooltipRef}
      className={styles.tooltip}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
      }}
    >
      <button
        className={styles.askButton}
        onClick={handleAskClick}
        aria-label="Ask about selected text"
      >
        <span className={styles.askIcon}>💬</span>
        <span>Ask about this</span>
      </button>
      <div className={styles.tooltipArrow} />
    </div>
  );
}

export default TextSelector;
