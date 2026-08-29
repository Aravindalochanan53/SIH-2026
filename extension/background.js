/**
 * TRANSLARA — Background Service Worker (Manifest V3).
 */

chrome.runtime.onInstalled.addListener(() => {
  console.log('[TRANSLARA] Background service worker initialized.');
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'PING') {
    sendResponse({ status: 'PONG', app: 'TRANSLARA' });
  }
});
