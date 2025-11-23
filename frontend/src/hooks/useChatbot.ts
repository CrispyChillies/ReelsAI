import { useState } from 'react';
import chatbotService from '@/services/chatbotService';
import type {
  ChatSession,
  ChatMessage,
  SendMessageRequest,
  SendMessageResponse,
} from '@/types/chatbot';

export function useChatbot() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (
    data: SendMessageRequest
  ): Promise<SendMessageResponse | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await chatbotService.sendMessage(data);
      return response;
    } catch (err: any) {
      const errorMsg = err?.response?.data?.error || 'Failed to send message';
      setError(errorMsg);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    sendMessage,
    isLoading,
    error,
  };
}

export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await chatbotService.listSessions();
      setSessions(response.sessions);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.error || 'Failed to fetch sessions';
      setError(errorMsg);
      setSessions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sessionId: string): Promise<boolean> => {
    setError(null);
    try {
      await chatbotService.deleteSession(sessionId);
      // Remove from local state
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));
      return true;
    } catch (err: any) {
      const errorMsg = err?.response?.data?.error || 'Failed to delete session';
      setError(errorMsg);
      return false;
    }
  };

  const renameSession = async (
    sessionId: string,
    newTitle: string
  ): Promise<boolean> => {
    setError(null);
    try {
      const response = await chatbotService.renameSession(sessionId, {
        title: newTitle,
      });
      // Update local state
      setSessions(prev =>
        prev.map(s =>
          s.session_id === sessionId ? { ...s, title: response.new_title } : s
        )
      );
      return true;
    } catch (err: any) {
      const errorMsg = err?.response?.data?.error || 'Failed to rename session';
      setError(errorMsg);
      return false;
    }
  };

  return {
    sessions,
    isLoading,
    error,
    fetchSessions,
    deleteSession,
    renameSession,
  };
}

export function useChatMessages(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMessages = async () => {
    if (!sessionId) {
      setMessages([]);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await chatbotService.getSessionMessages(sessionId);
      setMessages(response.messages);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.error || 'Failed to fetch messages';
      setError(errorMsg);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  };

  const addMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  };

  const clearMessages = () => {
    setMessages([]);
  };

  return {
    messages,
    isLoading,
    error,
    fetchMessages,
    addMessage,
    clearMessages,
  };
}
