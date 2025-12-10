/**
 * Background Service Worker
 *
 * Handles:
 * - Extension lifecycle
 * - Message passing between components
 * - Background API calls
 * - Authentication state management
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';
const WEB_DASHBOARD_URL = 'http://localhost:3000';


// Installation handler
chrome.runtime.onInstalled.addListener((details) => {
  console.log('AI Inbox Manager installed', details);

  if (details.reason === 'install') {
    // First install - open welcome page, which is now the popup
    chrome.tabs.create({
      url: 'popup/popup.html'
    });
  }
});

// Message handler from other components
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request);

  switch (request.action) {
    // --- Authentication ---
    case 'getAuthStatus':
      handleGetAuthStatus(sendResponse);
      return true; // Keep channel open for async response

    case 'saveAuthToken':
      handleSaveAuthToken(request.token, request.user, sendResponse);
      return true;

    case 'tokenFromDashboard':
      handleTokenFromDashboard(request.token, sendResponse);
      return true;

    case 'logout':
      handleLogout(sendResponse);
      return true;
    
    // --- UI / Navigation ---
    case 'openDashboard':
      chrome.tabs.create({ url: WEB_DASHBOARD_URL });
      break;

    // --- API Calls ---
    case 'fetchAIInsights':
      handleFetchAIInsights(request.threadId, sendResponse);
      return true;

    case 'triggerAIProcessing':
      handleTriggerAIProcessing(request.threadId, sendResponse);
      return true;

    default:
      console.warn('Unknown action received:', request.action);
      sendResponse({ error: 'Unknown action' });
      return false;
  }
});


/**
 * Get current authentication status
 */
async function handleGetAuthStatus(sendResponse) {
  try {
    const result = await chrome.storage.local.get(['authToken', 'user']);
    if (result.authToken && result.user) {
      sendResponse({
        success: true,
        isAuthenticated: true,
        token: result.authToken,
        user: result.user
      });
    } else {
      sendResponse({ success: true, isAuthenticated: false });
    }
  } catch (error) {
    console.error('Error getting auth status:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Save authentication token from login
 */
async function handleSaveAuthToken(token, user, sendResponse) {
  try {
    await chrome.storage.local.set({ authToken: token, user });

    // Notify popups that auth status has changed
    chrome.runtime.sendMessage({ action: 'authStatusChanged' }).catch(() => {
      // Ignore errors if no listeners
    });

    sendResponse({ success: true, message: 'Authentication successful!' });
  } catch (error) {
    console.error('Error saving auth token:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Save token received from the web dashboard
 */
async function handleTokenFromDashboard(token, sendResponse) {
  try {
    // Decode JWT to get user info (simple base64 decode)
    const payload = JSON.parse(atob(token.split('.')[1]));

    const user = {
      id: payload.sub,
      email: payload.email || payload.sub
    };

    await chrome.storage.local.set({ authToken: token, user });

    // Notify popups that auth status has changed
    chrome.runtime.sendMessage({ action: 'authStatusChanged' });

    sendResponse({ success: true, status: 'Token saved.' });
  } catch (error) {
    console.error('Error saving auth token from dashboard:', error);
    sendResponse({ success: false, error: error.message });
  }
}


/**
 * Clear authentication
 */
async function handleLogout(sendResponse) {
  try {
    await chrome.storage.local.remove(['authToken', 'user']);

    // Notify popups that auth status has changed
    chrome.runtime.sendMessage({ action: 'authStatusChanged' });

    sendResponse({ success: true });
  } catch (error) {
    console.error('Error during logout:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Fetch AI insights for a thread
 */
async function handleFetchAIInsights(threadId, sendResponse) {
  try {
    const { authToken } = await chrome.storage.local.get('authToken');

    if (!authToken) {
      sendResponse({ success: false, error: 'Not authenticated' });
      return;
    }

    // Fetch all AI insights for the thread
    const [summary, priority, sentiment, reply, tasks] = await Promise.allSettled([
      fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/summary`, authToken),
      fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/priority`, authToken),
      fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/sentiment`, authToken),
      fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/reply`, authToken),
      fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/tasks`, authToken)
    ]);

    sendResponse({
      success: true,
      insights: {
        summary: summary.status === 'fulfilled' ? summary.value : null,
        priority: priority.status === 'fulfilled' ? priority.value : null,
        sentiment: sentiment.status === 'fulfilled' ? sentiment.value : null,
        reply: reply.status === 'fulfilled' ? reply.value : null,
        tasks: tasks.status === 'fulfilled' ? tasks.value : null
      }
    });
  } catch (error) {
    console.error('Error fetching AI insights:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Trigger AI processing for a thread
 */
async function handleTriggerAIProcessing(threadId, sendResponse) {
  try {
    const { authToken } = await chrome.storage.local.get('authToken');

    if (!authToken) {
      sendResponse({ success: false, error: 'Not authenticated' });
      return;
    }

    const response = await fetch(`${API_BASE_URL}/workers/ai/process/trigger`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        thread_id: threadId,
        tasks: null // Process all tasks
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    sendResponse({ success: true, data });
  } catch (error) {
    console.error('Error triggering AI processing:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Helper function to fetch with auth header
 */
async function fetchWithAuth(url, token) {
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    if (response.status === 404) {
      return null; // Not found is okay - means not processed yet
    }
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Keep service worker alive
chrome.runtime.onConnect.addListener((port) => {
  console.log('Port connected:', port.name);
});
