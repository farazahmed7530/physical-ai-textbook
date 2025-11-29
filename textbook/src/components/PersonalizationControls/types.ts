/**
 * Type definitions for PersonalizationControls.
 * Requirements: 7.1, 7.2, 7.3
 */

export interface PersonalizedContentResponse {
  chapter_id: string;
  user_id: string;
  personalized_content: string;
  experience_level: string;
  from_cache: boolean;
}

export interface PersonalizeButtonProps {
  /** The chapter ID to personalize */
  chapterId: string;
  /** The original content to personalize */
  originalContent: string;
  /** Callback when personalization completes */
  onPersonalize: (content: string) => void;
  /** Callback when an error occurs */
  onError?: (error: string) => void;
  /** Custom class name */
  className?: string;
  /** Whether the button is disabled */
  disabled?: boolean;
}

export interface PersonalizedContentDisplayProps {
  /** The personalized content to display */
  personalizedContent: string;
  /** The experience level used for personalization */
  experienceLevel: string;
  /** Whether the content was loaded from cache */
  fromCache: boolean;
  /** Callback to view original content */
  onViewOriginal: () => void;
  /** Custom class name */
  className?: string;
}

export interface PersonalizationState {
  /** Whether personalization is in progress */
  isLoading: boolean;
  /** Error message if personalization failed */
  error: string | null;
  /** The personalized content */
  personalizedContent: string | null;
  /** The experience level used */
  experienceLevel: string | null;
  /** Whether content was from cache */
  fromCache: boolean;
  /** Whether showing personalized content */
  isShowingPersonalized: boolean;
}

export interface ProfileIncompleteModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback to close the modal */
  onClose: () => void;
  /** Callback to navigate to profile completion */
  onCompleteProfile: () => void;
}
