/**
 * Languages & Subsystem Discovery API Client.
 */
import { request } from './client';

export async function getLanguages() {
  return request('/api/languages');
}

export async function getCapabilities() {
  return request('/api/capabilities');
}

export async function getHealth() {
  return request('/health');
}
