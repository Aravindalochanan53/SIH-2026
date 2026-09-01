/**
 * Pedagogy & Offline Cache API Client.
 */
import { request, API_BASE_URL } from './client';

export async function generateFlashcards(sourceLang = 'ta', targetLang = 'ml', category = null, title = null) {
  return request('/api/pedagogy/flashcards', {
    method: 'POST',
    body: JSON.stringify({
      source_lang: sourceLang,
      target_lang: targetLang,
      category,
      title,
    }),
  });
}

export async function generateNumeracyWorksheet(sourceLang = 'ta', targetLang = 'ml', grade = 1) {
  return request('/api/pedagogy/numeracy', {
    method: 'POST',
    body: JSON.stringify({
      source_lang: sourceLang,
      target_lang: targetLang,
      grade,
    }),
  });
}

export async function generateLiteracyWorksheet(sourceLang = 'ta', targetLang = 'ml', grade = 1, category = null) {
  return request('/api/pedagogy/literacy', {
    method: 'POST',
    body: JSON.stringify({
      source_lang: sourceLang,
      target_lang: targetLang,
      grade,
      category,
    }),
  });
}

export async function getCachedPhrases(category = null, sourceLang = null, targetLang = null) {
  const params = new URLSearchParams();
  if (category && category !== 'all') params.append('category', category);
  if (sourceLang) params.append('source_lang', sourceLang);
  if (targetLang) params.append('target_lang', targetLang);
  const qs = params.toString() ? `?${params.toString()}` : '';
  return request(`/api/cache/phrases${qs}`);
}

export function getPdfDownloadUrl(fileName) {
  return `${API_BASE_URL}/api/pedagogy/download/${fileName}`;
}
