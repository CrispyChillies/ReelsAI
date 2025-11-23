import axiosInstance from '@/lib/axios';
import type {
  SendMessageRequest,
  SendMessageResponse,
  ListSessionsResponse,
  GetSessionMessagesResponse,
  DeleteSessionResponse,
  RenameSessionRequest,
  RenameSessionResponse,
} from '@/types/chatbot';

const chatbotService = {
  /**
   * Send a message to the chatbot
   * POST /api/chatbot/send-message/
   */
  sendMessage: async (data: SendMessageRequest): Promise<SendMessageResponse> => {
    const response = await axiosInstance.post<SendMessageResponse>(
      '/chatbot/send-message/',
      data
    );
    return response.data;
  },

  /**
   * List all chat sessions for authenticated user
   * GET /api/chatbot/sessions/
   */
  listSessions: async (): Promise<ListSessionsResponse> => {
    const response = await axiosInstance.get<ListSessionsResponse>(
      '/chatbot/sessions/'
    );
    return response.data;
  },

  /**
   * Get messages from a specific chat session
   * GET /api/chatbot/sessions/{session_id}/messages/
   */
  getSessionMessages: async (sessionId: string): Promise<GetSessionMessagesResponse> => {
    const response = await axiosInstance.get<GetSessionMessagesResponse>(
      `/chatbot/sessions/${sessionId}/messages/`
    );
    return response.data;
  },

  /**
   * Delete a chat session and its messages
   * DELETE /api/chatbot/sessions/{session_id}/delete/
   */
  deleteSession: async (sessionId: string): Promise<DeleteSessionResponse> => {
    const response = await axiosInstance.delete<DeleteSessionResponse>(
      `/chatbot/sessions/${sessionId}/delete/`
    );
    return response.data;
  },

  /**
   * Rename a chat session
   * PATCH /api/chatbot/sessions/{session_id}/rename/
   */
  renameSession: async (
    sessionId: string,
    data: RenameSessionRequest
  ): Promise<RenameSessionResponse> => {
    const response = await axiosInstance.patch<RenameSessionResponse>(
      `/chatbot/sessions/${sessionId}/rename/`,
      data
    );
    return response.data;
  },
};

export default chatbotService;
