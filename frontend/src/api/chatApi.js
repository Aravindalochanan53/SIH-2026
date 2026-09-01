/**
 * AI Chatbot API Client for TRANSLARA.
 */
import { request } from './client';

export async function sendChatMessage(message, sourceLang = 'ta', targetLang = 'ml', sessionId = null) {
  return request('/api/chat/message', {
    method: 'POST',
    body: JSON.stringify({
      message,
      source_lang: sourceLang,
      target_lang: targetLang,
      session_id: sessionId,
    }),
  });
}

export async function getChatSessions() {
  return request('/api/chat/sessions');
}

export async function getChatSessionDetails(sessionId) {
  return request(`/api/chat/sessions/${sessionId}`);
}

export async function deleteChatSession(sessionId) {
  return request(`/api/chat/sessions/${sessionId}`, {
    method: 'DELETE',
  });
}

export async function getChatHistory() {
  return request('/api/chat/history');
}

export async function clearChatHistory() {
  return request('/api/chat/history', {
    method: 'DELETE',
  });
}
