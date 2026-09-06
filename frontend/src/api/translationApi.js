/**
 * Translation & Translation History API Client.
 */
import { request } from './client';

export async function translateText(text, sourceLang = 'ta', targetLang = 'ml') {
  return request('/api/translate', {
    method: 'POST',
    body: JSON.stringify({
      text,
      source_language: sourceLang,
      target_language: targetLang,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });
}

export async function getTranslationHistory(limit = 50, offset = 0) {
  return request(`/api/translation/history?limit=${limit}&offset=${offset}`);
}

export async function getTranslationHistoryItem(id) {
  return request(`/api/translation/history/${id}`);
}

export async function deleteTranslationHistoryItem(id) {
  return request(`/api/translation/history/${id}`, {
    method: 'DELETE',
  });
}

export async function getCachedPhrases(category = null, sourceLang = null, targetLang = null) {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (sourceLang) params.append('source_lang', sourceLang);
  if (targetLang) params.append('target_lang', targetLang);
  const qs = params.toString();
  return request(`/api/cache/phrases${qs ? `?${qs}` : ''}`);
}
