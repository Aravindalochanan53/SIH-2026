/**
 * Authentication API Client for TRANSLARA (MSSQL Backend).
 */
import { request, setAuthToken } from './client';

export async function registerUser({ name, email, password, role = 'teacher', preferred_source_lang = 'ta', preferred_target_lang = 'ml' }) {
  const data = await request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      name,
      email,
      password,
      role,
      preferred_source_lang,
      preferred_target_lang,
    }),
  });
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function loginUser({ email, password }) {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function getCurrentUser() {
  return request('/api/auth/me');
}

export function logoutUser() {
  setAuthToken(null);
}
