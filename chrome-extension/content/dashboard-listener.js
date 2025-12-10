/**
 * Content script for the web dashboard.
 *
 * This script runs on the web dashboard pages and listens for the
 * authentication token in localStorage. When found, it sends it to
 * the background script.
 */

console.log('Dashboard listener content script loaded.');

const AUTH_STORAGE_KEY = 'auth-storage';
const EXTENSION_TOKEN_KEY = 'extension_auth_token';
const EXTENSION_USER_KEY = 'extension_auth_user';

function checkAuth() {
  try {
    // First check for extension-specific auth (from extension login)
    const extensionToken = localStorage.getItem(EXTENSION_TOKEN_KEY);
    const extensionUserStr = localStorage.getItem(EXTENSION_USER_KEY);
    
    if (extensionToken && extensionUserStr) {
      console.log('Found extension auth token in localStorage.');
      const user = JSON.parse(extensionUserStr);
      
      chrome.runtime.sendMessage({
        action: 'saveAuthToken',
        token: extensionToken,
        user: user
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('Error sending token to background:', chrome.runtime.lastError.message);
        } else {
          console.log('Extension token sent to background script:', response);
          // Clear the tokens after successful send
          localStorage.removeItem(EXTENSION_TOKEN_KEY);
          localStorage.removeItem(EXTENSION_USER_KEY);
        }
      });
      return;
    }
    
    // Fallback to regular auth storage
    const authDataString = localStorage.getItem(AUTH_STORAGE_KEY);
    if (authDataString) {
      const authData = JSON.parse(authDataString);
      const token = authData?.state?.token;

      if (token) {
        console.log('Found auth token in dashboard localStorage.');
        chrome.runtime.sendMessage({
          action: 'tokenFromDashboard',
          token: token
        }, (response) => {
          if (chrome.runtime.lastError) {
            console.error('Error sending token to background:', chrome.runtime.lastError.message);
          } else {
            console.log('Token sent to background script:', response?.status);
          }
        });
      }
    }
  } catch (error) {
    console.error('Error reading auth from localStorage:', error);
  }
}

// Check for auth immediately on load
checkAuth();

// Check again after a short delay (in case page is still loading)
setTimeout(checkAuth, 500);
setTimeout(checkAuth, 1000);
setTimeout(checkAuth, 2000);

// Also check when storage changes (e.g., after login)
window.addEventListener('storage', (event) => {
  if (event.key === AUTH_STORAGE_KEY || event.key === EXTENSION_TOKEN_KEY) {
    console.log('Auth storage changed, checking for token...');
    checkAuth();
  }
});
