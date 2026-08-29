/**
 * Centralized API Client for TRANSLARA Backend
 */

const API_BASE_URL = 'http://localhost:8000';

async function fetchJson(url, options = {}) {
  const res = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export async function getLanguages() {
  return fetchJson('/api/languages');
}

export async function getCapabilities() {
  return fetchJson('/api/capabilities');
}

export async function translateText(text, sourceLang = 'ta', targetLang = 'ml') {
  return fetchJson('/api/translate', {
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

export async function uploadVideo(file, sourceLang = 'ta', targetLang = 'ml') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_lang', sourceLang);
  formData.append('target_lang', targetLang);

  const res = await fetch(`${API_BASE_URL}/api/video/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to upload video');
  }
  return res.json();
}

export async function startVideoTranslation(jobId, sourceLang = 'ta', targetLang = 'ml') {
  return fetchJson('/api/video/translate', {
    method: 'POST',
    body: JSON.stringify({
      job_id: jobId,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });
}

export async function triggerDemoVideo(sourceLang = 'ta', targetLang = 'ml') {
  return fetchJson('/api/video/demo', {
    method: 'POST',
    body: JSON.stringify({
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });
}

export async function getVideoStatus(jobId) {
  return fetchJson(`/api/video/status/${jobId}`);
}

export async function getVideoHistory() {
  return fetchJson('/api/video/history');
}

export async function generateFlashcards(sourceLang = 'ta', targetLang = 'ml', category = null) {
  return fetchJson('/api/pedagogy/flashcards', {
    method: 'POST',
    body: JSON.stringify({
      source_lang: sourceLang,
      target_lang: targetLang,
      category,
    }),
  });
}

export async function generateNumeracyWorksheet(sourceLang = 'ta', targetLang = 'ml', grade = 1) {
  return fetchJson('/api/pedagogy/numeracy', {
    method: 'POST',
    body: JSON.stringify({
      source_lang: sourceLang,
      target_lang: targetLang,
      grade,
    }),
  });
}

export async function generateLiteracyWorksheet(sourceLang = 'ta', targetLang = 'ml', grade = 1) {
  return fetchJson('/api/pedagogy/literacy', {
    method: 'POST',
    body: JSON.stringify({
      source_lang: sourceLang,
      target_lang: targetLang,
      grade,
    }),
  });
}

export async function getCachedPhrases(category = null, sourceLang = null, targetLang = null) {
  const params = new URLSearchParams();
  if (category && category !== 'all') params.append('category', category);
  if (sourceLang) params.append('source_lang', sourceLang);
  if (targetLang) params.append('target_lang', targetLang);
  const qs = params.toString() ? `?${params.toString()}` : '';
  return fetchJson(`/api/cache/phrases${qs}`);
}

export async function sendChatMessage(message, sourceLang = 'ta', targetLang = 'ml') {
  return fetchJson('/api/chat/message', {
    method: 'POST',
    body: JSON.stringify({
      message,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });
}

export async function getChatHistory() {
  return fetchJson('/api/chat/history');
}

export async function clearChatHistory() {
  return fetchJson('/api/chat/history', {
    method: 'DELETE',
  });
}
