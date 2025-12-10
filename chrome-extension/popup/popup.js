/**
 * Popup Logic
 */

// DOM Elements
const elements = {
  loggedIn: null,
  loggedOut: null,
  userEmail: null,
  logoutBtn: null,
  loginBtn: null, // Added
  sidebarEnabled: null,
  autoProcess: null
};

/**
 * Initialize popup
 */
function init() {
  console.log('Popup initializing...');

  // Get DOM elements
  elements.loggedIn = document.getElementById('logged-in');
  elements.loggedOut = document.getElementById('logged-out');
  elements.userEmail = document.getElementById('user-email');
  elements.logoutBtn = document.getElementById('logout-btn');
  elements.loginBtn = document.getElementById('login-btn'); // Added
  elements.sidebarEnabled = document.getElementById('sidebar-enabled');
  elements.autoProcess = document.getElementById('auto-process');

  // Setup event listeners
  setupEventListeners();

  // Load state
  loadAuthStatus();
  loadSettings();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Login
  elements.loginBtn?.addEventListener('click', handleLogin);

  // Logout
  elements.logoutBtn?.addEventListener('click', handleLogout);

  // Settings
  elements.sidebarEnabled?.addEventListener('change', saveSetting);
  elements.autoProcess?.addEventListener('change', saveSetting);

  // Links
  document.getElementById('open-dashboard')?.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.runtime.sendMessage({ action: 'openDashboard' });
  });

  document.getElementById('view-docs')?.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'https://github.com/your-repo/ai-inbox-manager' });
  });

  document.getElementById('report-issue')?.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'https://github.com/your-repo/ai-inbox-manager/issues' });
  });
}

/**
 * Handle login button click
 */
function handleLogin() {
  // Open the web dashboard login page with extension source parameter
  const loginUrl = 'http://localhost:3000/login?source=extension';
  
  // Open in a new window
  chrome.windows.create({
    url: loginUrl,
    type: 'popup',
    width: 500,
    height: 700
  });
}

/**
 * Load authentication status from background
 */
async function loadAuthStatus() {
  try {
    // Ask the background script for the auth status
    const response = await chrome.runtime.sendMessage({ action: 'getAuthStatus' });
    if (response && response.isAuthenticated) {
      // Logged in
      elements.loggedIn.style.display = 'flex';
      elements.loggedOut.style.display = 'none';
      elements.userEmail.textContent = response.user.email || 'User';
    } else {
      // Logged out
      elements.loggedIn.style.display = 'none';
      elements.loggedOut.style.display = 'flex';
    }
  } catch (error) {
    console.error('Error loading auth status:', error);
    elements.loggedIn.style.display = 'none';
    elements.loggedOut.style.display = 'flex';
  }
}

/**
 * Load settings
 */
async function loadSettings() {
  try {
    const result = await chrome.storage.local.get(['sidebarEnabled', 'autoProcess']);

    elements.sidebarEnabled.checked = result.sidebarEnabled !== false; // Default true
    elements.autoProcess.checked = result.autoProcess !== false; // Default true
  } catch (error) {
    console.error('Error loading settings:', error);
  }
}

/**
 * Save setting
 */
async function saveSetting(e) {
  const setting = e.target.id;
  const value = e.target.checked;

  try {
    await chrome.storage.local.set({ [setting]: value });
    console.log(`Setting ${setting} saved:`, value);
  } catch (error) {
    console.error('Error saving setting:', error);
  }
}

/**
 * Handle logout
 */
async function handleLogout() {
  try {
    // Ask background to log out
    await chrome.runtime.sendMessage({ action: 'logout' });
    loadAuthStatus();
  } catch (error) {
    console.error('Error during logout:', error);
  }
}

// Listen for auth changes from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'authStatusChanged') {
    loadAuthStatus();
  }
});


// Initialize on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
