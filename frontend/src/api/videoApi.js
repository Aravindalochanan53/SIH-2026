/**
 * Video Dubbing & Subtitling API Client for TRANSLARA.
 */
import { request, API_BASE_URL } from './client';

export async function uploadVideo(file, sourceLang = 'ta', targetLang = 'ml') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_lang', sourceLang);
  formData.append('target_lang', targetLang);

  return request('/api/video/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function startVideoTranslation(jobId, sourceLang = 'ta', targetLang = 'ml') {
  return request('/api/video/translate', {
    method: 'POST',
    body: JSON.stringify({
      job_id: jobId,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });
}

export async function triggerDemoVideo(sourceLang = 'ta', targetLang = 'ml') {
  return request('/api/video/demo', {
    method: 'POST',
    body: JSON.stringify({
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });
}

export async function getVideoStatus(jobId) {
  return request(`/api/video/status/${jobId}`);
}

export async function getVideoHistory() {
  return request('/api/video/history');
}

export function getSubtitleUrl(jobId, format = 'vtt', mode = 'dual') {
  return `${API_BASE_URL}/api/video/subtitles/${jobId}?format=${format}&mode=${mode}`;
}
