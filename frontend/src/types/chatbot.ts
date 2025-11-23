export type MessageType = 'human' | 'ai' | 'system' | 'tool';

export interface ChatMessage {
  id: string;
  message_type: MessageType;
  content: string;
  timestamp: string;
  used_rag_tool: boolean;
  tool_calls_made: boolean;
  confidence: number | null;
  task_type: string | null;
  metadata: Record<string, any>;
}

export interface ChatSession {
  session_id: string;
  created_at: string;
  updated_at: string;
  title: string | null;
  message_count: number;
  last_message_timestamp: string | null;
  last_message_preview: string | null;
}

export interface SendMessageRequest {
  message: string;
  session_id?: string;
}

export interface SendMessageResponse {
  success: boolean;
  message: string;
  session_id: string;
  data?: Record<string, any>;
  task?: string;
  confidence?: number;
  timestamp: string;
  user_message_id?: string;
  ai_message_id?: string;
}

export interface ListSessionsResponse {
  session_count: number;
  sessions: ChatSession[];
}

export interface GetSessionMessagesResponse {
  session_id: string;
  message_count: number;
  messages: ChatMessage[];
}

export interface DeleteSessionResponse {
  success: boolean;
  message: string;
  deleted_messages: number;
}

export interface RenameSessionRequest {
  title: string;
}

export interface RenameSessionResponse {
  success: boolean;
  message: string;
  session_id: string;
  old_title: string;
  new_title: string;
}
