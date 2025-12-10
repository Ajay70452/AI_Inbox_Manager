/**
 * Sidebar Logic
 *
 * Handles all sidebar functionality including:
 * - Authentication
 * - Displaying AI insights
 * - User interactions
 */

console.log('🚀 Sidebar script loaded!');

const API_BASE_URL = 'http://localhost:8000/api/v1';

// State
let currentThread = null;
let authToken = null;
let isAuthenticated = false;
let currentLoadingThreadId = null; // Track which thread is currently being loaded

// DOM Elements
const elements = {
  authSection: null,
  mainContent: null,
  noThread: null,
  loading: null,
  insightsContent: null,
  loginForm: null,
  authError: null,
  logoutBtn: null
};

/**
 * Initialize sidebar
 */
function init() {
  console.log('🎬 Sidebar initializing...');

  // Get DOM elements
  elements.authSection = document.getElementById('auth-section');
  elements.mainContent = document.getElementById('main-content');
  elements.noThread = document.getElementById('no-thread');
  elements.loading = document.getElementById('loading');
  elements.insightsContent = document.getElementById('insights-content');
  elements.loginForm = document.getElementById('login-form');
  elements.authError = document.getElementById('auth-error');
  elements.logoutBtn = document.getElementById('logout-btn');

  console.log('✅ DOM elements loaded:', {
    authSection: !!elements.authSection,
    mainContent: !!elements.mainContent,
    noThread: !!elements.noThread,
    loading: !!elements.loading,
    insightsContent: !!elements.insightsContent
  });

  // Setup event listeners
  setupEventListeners();

  // Check authentication
  checkAuth();

  // Notify parent that sidebar is ready
  window.parent.postMessage({ type: 'SIDEBAR_READY' }, '*');
  
  console.log('✅ Sidebar initialization complete');
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
  // Close sidebar
  document.getElementById('close-sidebar')?.addEventListener('click', () => {
    window.parent.postMessage({ type: 'CLOSE_SIDEBAR' }, '*');
  });

  // Login form
  elements.loginForm?.addEventListener('submit', handleLogin);

  // Logout
  elements.logoutBtn?.addEventListener('click', handleLogout);

  // Regenerate buttons
  document.getElementById('regenerate-summary')?.addEventListener('click', () => {
    regenerateInsight('summary');
  });

  document.getElementById('regenerate-reply')?.addEventListener('click', () => {
    regenerateInsight('reply');
  });

  // Reply actions
  document.getElementById('edit-reply')?.addEventListener('click', editReply);
  document.getElementById('copy-reply')?.addEventListener('click', copyReply);
  document.getElementById('send-reply')?.addEventListener('click', sendReply);
  document.getElementById('cancel-edit')?.addEventListener('click', cancelEdit);
  document.getElementById('save-edit')?.addEventListener('click', saveAndSendReply);

  // Quick actions
  document.getElementById('send-to-slack')?.addEventListener('click', sendToSlack);
  document.getElementById('create-task')?.addEventListener('click', createTask);

  // Listen for messages from parent
  window.addEventListener('message', handleMessage);
}

/**
 * Check authentication status
 */
async function checkAuth() {
  try {
    const result = await chrome.storage.local.get(['authToken', 'user']);

    if (result.authToken) {
      authToken = result.authToken;
      isAuthenticated = true;
      showMainContent();
    } else {
      showAuthSection();
    }
  } catch (error) {
    console.error('Error checking auth:', error);
    showAuthSection();
  }
}

/**
 * Handle login
 */
async function handleLogin(e) {
  e.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  try {
    elements.authError.style.display = 'none';

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();

    // Save token
    await chrome.storage.local.set({
      authToken: data.access_token,
      user: { email }
    });

    authToken = data.access_token;
    isAuthenticated = true;

    showMainContent();
  } catch (error) {
    console.error('Login error:', error);
    elements.authError.textContent = 'Login failed. Please check your credentials.';
    elements.authError.style.display = 'block';
  }
}

/**
 * Handle logout
 */
async function handleLogout() {
  await chrome.storage.local.remove(['authToken', 'user']);
  authToken = null;
  isAuthenticated = false;
  currentThread = null;
  showAuthSection();
}

/**
 * Show auth section
 */
function showAuthSection() {
  elements.authSection.style.display = 'flex';
  elements.mainContent.style.display = 'none';
  elements.logoutBtn.style.display = 'none';
}

/**
 * Show main content
 */
function showMainContent() {
  elements.authSection.style.display = 'none';
  elements.mainContent.style.display = 'block';
  elements.logoutBtn.style.display = 'flex';

  if (currentThread) {
    loadThreadInsights(currentThread);
  } else {
    showNoThread();
  }
}

/**
 * Show no thread state
 */
function showNoThread() {
  elements.noThread.style.display = 'flex';
  elements.loading.style.display = 'none';
  elements.insightsContent.style.display = 'none';
}

/**
 * Show loading state
 */
function showLoading() {
  elements.noThread.style.display = 'none';
  elements.loading.style.display = 'flex';
  elements.insightsContent.style.display = 'none';
}

/**
 * Show insights
 */
function showInsights() {
  elements.noThread.style.display = 'none';
  elements.loading.style.display = 'none';
  elements.insightsContent.style.display = 'block';
}

/**
 * Handle messages from parent window
 */
function handleMessage(event) {
  const { type, threadInfo } = event.data;

  console.log('Sidebar received message:', type, threadInfo);

  switch (type) {
    case 'THREAD_OPENED':
      onThreadOpened(threadInfo);
      break;

    case 'THREAD_CLOSED':
      onThreadClosed();
      break;
  }
}

/**
 * Handle thread opened
 */
function onThreadOpened(threadInfo) {
  const previousThreadId = currentThread?.threadId;
  currentThread = threadInfo;

  if (!isAuthenticated) {
    console.log('📧 Thread opened but not authenticated, skipping load');
    return;
  }

  // Update thread info display
  document.getElementById('thread-subject').textContent = threadInfo.subject;
  document.getElementById('thread-meta').textContent = `${threadInfo.emailCount} messages`;

  // Clear previous insights immediately to show loading state
  clearInsightsDisplay();

  // Always load insights when thread opened message is received
  // Even if it's the same thread (user may have navigated away and back)
  console.log(`📧 Thread opened: ${threadInfo.threadId} (previous: ${previousThreadId})`);
  loadThreadInsights(threadInfo);
}

/**
 * Clear all insights display (reset to empty/loading state)
 */
function clearInsightsDisplay() {
  // Clear summary
  const summaryContent = document.getElementById('summary-content');
  if (summaryContent) summaryContent.innerHTML = '<p class="placeholder">Loading...</p>';

  // Clear priority
  const priorityBadge = document.getElementById('priority-badge');
  if (priorityBadge) {
    priorityBadge.textContent = '-';
    priorityBadge.className = 'badge';
  }

  // Clear sentiment
  const sentimentBadge = document.getElementById('sentiment-badge');
  if (sentimentBadge) {
    sentimentBadge.textContent = '-';
    sentimentBadge.className = 'badge';
  }

  // Clear tasks
  const tasksContent = document.getElementById('tasks-content');
  if (tasksContent) tasksContent.innerHTML = '<p class="placeholder">Loading...</p>';
  const taskCount = document.getElementById('task-count');
  if (taskCount) taskCount.textContent = '0';

  // Clear reply
  const replyPreview = document.getElementById('reply-preview');
  if (replyPreview) {
    replyPreview.innerHTML = '<p class="placeholder">Loading...</p>';
    replyPreview.style.display = 'block';
  }
  const replyEditor = document.getElementById('reply-editor');
  if (replyEditor) {
    replyEditor.value = '';
    replyEditor.style.display = 'none';
  }
  const replyActions = document.getElementById('reply-actions');
  if (replyActions) replyActions.style.display = 'none';
  const editActions = document.getElementById('reply-edit-actions');
  if (editActions) editActions.style.display = 'none';
}

/**
 * Handle thread closed
 */
function onThreadClosed() {
  currentThread = null;

  if (isAuthenticated) {
    showNoThread();
  }
}

/**
 * Load thread AI insights
 */
async function loadThreadInsights(threadInfo, retryCount = 0) {
  const MAX_RETRIES = 3;
  const threadId = threadInfo.threadId;
  currentLoadingThreadId = threadId;

  console.log(`🔄 loadThreadInsights called for thread: ${threadId} (retry: ${retryCount})`);
  showLoading();

  try {
    // Fetch AI insights from backend
    console.log(`📡 Fetching insights for thread: ${threadId}`);
    const insights = await fetchAIInsights(threadId);
    console.log(`✅ Received insights for thread: ${threadId}`, insights);

    // Check if user switched to a different thread while we were loading
    if (currentLoadingThreadId !== threadId) {
      console.log(`⚠️ Thread changed during loading (was: ${threadId}, now: ${currentLoadingThreadId}), ignoring results`);
      return;
    }

    console.log('Loaded insights:', insights);

    // Check if we have insights (if summary is missing, we probably need to process)
    if (!insights.summary && !insights.priority) {
      if (retryCount >= MAX_RETRIES) {
        console.log('❌ Max retries reached, showing error');
        showInsights();
        displayError('Unable to load AI insights. The email may not be synced yet.');
        return;
      }

      console.log('🤔 No insights found (null responses), triggering AI processing...');

      // Show processing state
      const content = document.getElementById('summary-content');
      if (content) content.innerHTML = '<p class="placeholder">🤖 AI is analyzing this email...</p>';

      const triggerResult = await triggerAIProcessing(threadId);

      // If trigger failed, don't retry
      if (!triggerResult) {
        console.log('❌ AI processing trigger failed, not retrying');
        showInsights();
        displayError('Unable to process this email. It may not be synced to the backend yet.');
        return;
      }

      // Retry after a delay to allow processing to complete
      console.log('⏳ Waiting for AI processing...');
      setTimeout(() => {
        // Only retry if still on the same thread
        if (currentThread?.threadId === threadId) {
          loadThreadInsights(threadInfo, retryCount + 1);
        }
      }, 5000);
      return;
    }

    // Final check before displaying - make sure we're still on the same thread
    if (currentLoadingThreadId !== threadId) {
      console.log(`⚠️ Thread changed before display (was: ${threadId}, now: ${currentLoadingThreadId}), ignoring`);
      return;
    }

    // Display insights
    displaySummary(insights.summary);
    displayPriority(insights.priority);
    displaySentiment(insights.sentiment);
    displayTasks(insights.tasks);
    displayReply(insights.reply);

    showInsights();
  } catch (error) {
    // Check if thread changed - don't show error for stale requests
    if (currentLoadingThreadId !== threadId) {
      console.log(`⚠️ Thread changed during error (was: ${threadId}, now: ${currentLoadingThreadId}), ignoring`);
      return;
    }

    console.error('Error loading insights:', error);

    // Check if insights don't exist - trigger AI processing (with retry limit)
    if ((error.message.includes('404') || error.message.includes('not found')) && retryCount < MAX_RETRIES) {
      console.log('No insights found, triggering AI processing...');
      const triggerResult = await triggerAIProcessing(threadId);

      if (!triggerResult) {
        showInsights();
        displayError('Unable to process this email. It may not be synced to the backend yet.');
        return;
      }

      // Retry after a delay
      setTimeout(() => {
        // Only retry if still on the same thread
        if (currentThread?.threadId === threadId) {
          loadThreadInsights(threadInfo, retryCount + 1);
        }
      }, 3000);
    } else {
      showInsights();
      displayError('Failed to load AI insights. Please try again.');
    }
  }
}

/**
 * Handle authentication error (401)
 */
async function handleAuthError() {
  console.log('🔒 Authentication error, logging out...');
  authToken = null;
  isAuthenticated = false;
  
  // Clear storage
  await chrome.storage.local.remove(['authToken', 'user']);
  
  // Show login screen
  showAuthSection();
  
  // Show error message
  if (elements.authError) {
    elements.authError.textContent = 'Session expired. Please sign in again.';
    elements.authError.style.display = 'block';
  }
}

/**
 * Fetch AI insights from backend
 */
async function fetchAIInsights(threadId) {
  console.log('🔍 Fetching AI insights for thread:', threadId);
  console.log('🔑 Auth token available:', !!authToken);
  
  if (!authToken) {
    throw new Error('Not authenticated');
  }

  const headers = {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json'
  };

  console.log('📡 Making API requests...');

  // Helper to handle fetch with auth check
  const fetchWithAuth = async (url) => {
    const res = await fetch(url, { headers });
    if (res.status === 401) {
      await handleAuthError();
      throw new Error('Unauthorized');
    }
    return res;
  };

  // Fetch all insights in parallel
  const [summary, priority, sentiment, reply, tasks] = await Promise.allSettled([
    fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/summary`).then(r => {
      console.log('Summary response:', r.status);
      return r.ok ? r.json() : null;
    }),
    fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/priority`).then(r => {
      console.log('Priority response:', r.status);
      return r.ok ? r.json() : null;
    }),
    fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/sentiment`).then(r => {
      console.log('Sentiment response:', r.status);
      return r.ok ? r.json() : null;
    }),
    fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/reply`).then(r => {
      console.log('Reply response:', r.status);
      return r.ok ? r.json() : null;
    }),
    fetchWithAuth(`${API_BASE_URL}/threads/${threadId}/tasks`).then(r => {
      console.log('Tasks response:', r.status);
      return r.ok ? r.json() : null;
    })
  ]);

  console.log('✅ API responses received');

  return {
    summary: summary.status === 'fulfilled' ? summary.value : null,
    priority: priority.status === 'fulfilled' ? priority.value : null,
    sentiment: sentiment.status === 'fulfilled' ? sentiment.value : null,
    reply: reply.status === 'fulfilled' ? reply.value : null,
    tasks: tasks.status === 'fulfilled' ? tasks.value : null
  };
}

/**
 * Trigger AI processing for thread
 * @returns {boolean} true if successful, false otherwise
 */
async function triggerAIProcessing(threadId) {
  console.log('🤖 Triggering AI processing for thread:', threadId);
  console.log('🤖 Thread ID format check - Length:', threadId.length, 'Is hex:', /^[a-f0-9]+$/i.test(threadId));

  if (!authToken) {
    console.error('❌ No auth token for AI processing');
    return false;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/workers/ai/process/trigger`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ thread_id: threadId })
    });

    console.log('🤖 AI processing trigger response:', response.status);

    if (response.status === 401) {
      await handleAuthError();
      return false;
    }

    if (response.ok) {
      const result = await response.json();
      console.log('✅ AI processing triggered:', result);
      return true;
    } else {
      const errorText = await response.text();
      console.error('❌ AI processing failed:', response.status, errorText);

      // Parse error for more details
      try {
        const errorJson = JSON.parse(errorText);
        if (errorJson.detail && errorJson.detail.includes('Thread not found')) {
          console.error('⚠️ Thread not found in backend. This could mean:');
          console.error('   1. Email not synced yet - try syncing emails first');
          console.error('   2. Thread ID format mismatch - expected hex format like "19b04108a423e17d"');
          console.error('   3. Gmail API sync failed - check backend logs');
        }
      } catch (e) {
        // Ignore parse error
      }

      return false;
    }
  } catch (error) {
    console.error('Failed to trigger AI processing:', error);
    return false;
  }
}

/**
 * Display summary
 */
function displaySummary(summary) {
  const content = document.getElementById('summary-content');

  if (summary && summary.summary_text) {
    content.innerHTML = `<p>${escapeHtml(summary.summary_text)}</p>`;
  } else {
    content.innerHTML = '<p class="placeholder">No summary available</p>';
  }
}

/**
 * Display priority
 */
function displayPriority(priority) {
  const badge = document.getElementById('priority-badge');

  if (priority && priority.priority_level) {
    const level = priority.priority_level.toLowerCase();
    badge.textContent = priority.priority_level;
    badge.className = `badge priority-${level}`;
  } else {
    badge.textContent = '-';
    badge.className = 'badge';
  }
}

/**
 * Display sentiment
 */
function displaySentiment(sentiment) {
  const badge = document.getElementById('sentiment-badge');

  if (sentiment && sentiment.sentiment_label) {
    const label = sentiment.sentiment_label.toLowerCase();
    badge.textContent = sentiment.sentiment_label;
    badge.className = `badge sentiment-${label}`;
  } else {
    badge.textContent = '-';
    badge.className = 'badge';
  }
}

/**
 * Display tasks
 */
function displayTasks(tasks) {
  const container = document.getElementById('tasks-content');
  const countBadge = document.getElementById('task-count');

  if (tasks && tasks.length > 0) {
    countBadge.textContent = tasks.length;

    container.innerHTML = tasks.map(task => `
      <div class="task-item">
        <input type="checkbox" class="task-checkbox">
        <div class="task-content">
          <div class="task-title">${escapeHtml(task.title)}</div>
          <div class="task-meta">
            ${task.due_date ? `Due: ${new Date(task.due_date).toLocaleDateString()}` : 'No due date'}
            ${task.extracted_owner ? ` • Owner: ${escapeHtml(task.extracted_owner)}` : ''}
          </div>
        </div>
      </div>
    `).join('');
  } else {
    countBadge.textContent = '0';
    container.innerHTML = '<p class="placeholder">No tasks extracted</p>';
  }
}

/**
 * Display reply draft
 */
function displayReply(reply) {
  const preview = document.getElementById('reply-preview');
  const editor = document.getElementById('reply-editor');
  const actions = document.getElementById('reply-actions');
  const editActions = document.getElementById('reply-edit-actions');

  if (reply && reply.draft_text) {
    preview.innerHTML = `<p>${escapeHtml(reply.draft_text)}</p>`;
    editor.value = reply.draft_text;
    preview.style.display = 'block';
    editor.style.display = 'none';
    actions.style.display = 'flex';
    editActions.style.display = 'none';
  } else {
    preview.innerHTML = '<p class="placeholder">No draft available</p>';
    preview.style.display = 'block';
    editor.style.display = 'none';
    actions.style.display = 'none';
    editActions.style.display = 'none';
  }
}

/**
 * Display error message
 */
function displayError(message) {
  const content = document.getElementById('summary-content');
  content.innerHTML = `<p style="color: #c5221f;">${escapeHtml(message)}</p>`;
}

/**
 * Regenerate insight
 */
async function regenerateInsight(type) {
  if (!currentThread) return;

  console.log(`Regenerating ${type}...`);
  // TODO: Implement regeneration API call
}

/**
 * Edit reply - switch to edit mode
 */
function editReply() {
  const preview = document.getElementById('reply-preview');
  const editor = document.getElementById('reply-editor');
  const actions = document.getElementById('reply-actions');
  const editActions = document.getElementById('reply-edit-actions');

  // Switch to edit mode
  preview.style.display = 'none';
  editor.style.display = 'block';
  actions.style.display = 'none';
  editActions.style.display = 'flex';

  // Focus the editor
  editor.focus();
}

/**
 * Cancel edit - return to preview mode
 */
function cancelEdit() {
  const preview = document.getElementById('reply-preview');
  const editor = document.getElementById('reply-editor');
  const actions = document.getElementById('reply-actions');
  const editActions = document.getElementById('reply-edit-actions');

  // Switch back to preview mode
  preview.style.display = 'block';
  editor.style.display = 'none';
  actions.style.display = 'flex';
  editActions.style.display = 'none';
}

/**
 * Copy reply to clipboard
 */
async function copyReply() {
  const preview = document.getElementById('reply-preview');
  const replyText = preview.textContent.trim();

  if (!replyText || replyText === 'No draft available') {
    console.error('No reply text available');
    return;
  }

  try {
    await navigator.clipboard.writeText(replyText);
    // Show success feedback
    const btn = document.getElementById('copy-reply');
    const originalText = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => {
      btn.textContent = originalText;
    }, 2000);
  } catch (error) {
    console.error('Failed to copy:', error);
  }
}

/**
 * Send reply - send the current draft via API
 */
async function sendReply() {
  if (!currentThread) {
    console.error('No current thread');
    return;
  }

  const editor = document.getElementById('reply-editor');
  const preview = document.getElementById('reply-preview');

  // Get text from editor if editing, otherwise from preview
  const isEditing = editor.style.display !== 'none';
  const replyText = isEditing ? editor.value.trim() : preview.textContent.trim();

  if (!replyText || replyText === 'No draft available' || replyText === 'Loading...') {
    console.error('No reply text available');
    return;
  }

  // Copy to clipboard and notify user
  const btn = document.getElementById('send-reply');
  const originalText = btn.textContent;
  btn.disabled = true;

  try {
    // Copy to clipboard
    await navigator.clipboard.writeText(replyText);

    // Show success feedback
    btn.textContent = 'Copied!';
    btn.classList.add('success');

    // Also show a message to guide user
    console.log('Reply copied to clipboard! Click "Reply" in Gmail to paste and send.');

    setTimeout(() => {
      btn.textContent = originalText;
      btn.disabled = false;
      btn.classList.remove('success');
    }, 2000);
  } catch (error) {
    console.error('Failed to copy reply:', error);

    // Show error feedback
    btn.textContent = 'Failed';
    btn.classList.add('error');

    setTimeout(() => {
      btn.textContent = originalText;
      btn.disabled = false;
      btn.classList.remove('error');
    }, 3000);

    // Display error message
    displayError(`Failed to send reply: ${error.message}`);
  }
}

/**
 * Save edit and send reply
 */
async function saveAndSendReply() {
  if (!currentThread) {
    console.error('No current thread');
    return;
  }

  const editor = document.getElementById('reply-editor');
  const replyText = editor.value.trim();

  if (!replyText) {
    console.error('No reply text available');
    return;
  }

  // Copy to clipboard
  const btn = document.getElementById('save-edit');
  const originalText = btn.textContent;
  btn.disabled = true;

  try {
    // Copy edited reply to clipboard
    await navigator.clipboard.writeText(replyText);

    // Update preview with edited text
    const preview = document.getElementById('reply-preview');
    preview.innerHTML = `<p>${escapeHtml(replyText)}</p>`;

    // Show success feedback
    btn.textContent = 'Copied!';
    btn.classList.add('success');

    console.log('Reply copied to clipboard! Click "Reply" in Gmail to paste and send.');

    setTimeout(() => {
      // Switch back to preview mode
      cancelEdit();
      btn.textContent = originalText;
      btn.disabled = false;
      btn.classList.remove('success');
    }, 2000);
  } catch (error) {
    console.error('Failed to send reply:', error);

    // Show error feedback
    btn.textContent = 'Failed';
    btn.classList.add('error');

    setTimeout(() => {
      btn.textContent = originalText;
      btn.disabled = false;
      btn.classList.remove('error');
    }, 3000);

    // Display error message
    displayError(`Failed to send reply: ${error.message}`);
  }
}

/**
 * Send to Slack
 */
function sendToSlack() {
  console.log('Send to Slack clicked');
  // TODO: Implement Slack integration
}

/**
 * Create task
 */
function createTask() {
  console.log('Create task clicked');
  // TODO: Implement task creation
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Initialize on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
