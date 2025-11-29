/**
 * Type definitions for TranslationControls.
 * Requirements: 8.1, 8.3
 */

export interface TranslatedContentResponse {
  chapter_id: string;
  translated_content: string;
  language: string;
  from_cache: boolean;
  has_rtl_formatting: boolean;
}

export interface TranslateButtonProps {
  /** The chapter ID to translate */
  chapterId: string;
  /** The original content to translate */
  originalContent: string;
  /** Callback when translation completes */
  onTranslate: (content: string) => void;
  /** Callback when an error occurs */
  onError?: (error: string) => void;
  /** Custom class name */
  className?: string;
  /** Whether the button is disabled */
  disabled?: boolean;
}

export interface TranslatedContentDisplayProps {
  /** The translated content to display */
  translatedContent: string;
  /** The target language */
  language: string;
  /** Whether the content was loaded from cache */
  fromCache: boolean;
  /** Callback to view original content */
  onViewOriginal: () => void;
  /** Custom class name */
  className?: string;
}

export interface TranslationState {
  /** Whether translation is in progress */
  isLoading: boolean;
  /** Error message if translation failed */
  error: string | null;
  /** The translated content */
  translatedContent: string | null;
  /** The target language */
  language: string | null;
  /** Whether content was from cache */
  fromCache: boolean;
  /** Whether showing translated content */
  isShowingTranslated: boolean;
}
