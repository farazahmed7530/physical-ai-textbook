/**
 * Type definitions for the ChatWidget component.
 */

export interface Source {
  chapter_id: string;
  section_title: string;
  page_url: string;
  relevance_score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  is_fallback?: boolean;
  timestamp: Date;
}

export interface ChatRequest {
  query: string;
  selected_text?: string;
  user_id?: string;
}

export interface ChatResponse {
  response: string;
  sources: Source[];
  is_fallback: boolean;
}

export interface ChatWidgetProps {
  apiEndpoint?: string;
  userId?: string;
  selectedText?: string;
  onClearSelectedText?: () => void;
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  isOpen: boolean;
}
