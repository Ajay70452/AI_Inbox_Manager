/**
 * Gmail Injector
 *
 * Injects the AI sidebar into Gmail
 */

console.log('[AI Inbox] Gmail Injector script loaded!');

let sidebarContainer = null;
let currentThreadId = null;

/**
 * Initialize Gmail integration
 */
function initGmail() {
  console.log('[AI Inbox] Initializing Gmail integration');

  if (!window.GmailDetector) {
    console.error('[AI Inbox] GmailDetector not found!');
    return;
  }

  if (!GmailDetector.isGmail()) {
    console.log('[AI Inbox] Not on Gmail, skipping');
    return;
  }

  console.log('[AI Inbox] Gmail detected, waiting for page to load...');

  // Wait for Gmail to load
  DOMUtils.waitForElement('.AO', 15000)
    .then(() => {
      console.log('[AI Inbox] Gmail loaded, setting up thread watcher');
      setupThreadWatcher();
    })
    .catch(err => {
      console.error('[AI Inbox] Gmail did not load:', err);
    });
}

/**
 * Setup thread watcher
 */
function setupThreadWatcher() {
  console.log('[AI Inbox] Setting up thread watcher...');
  
  if (!window.GmailDetector) {
    console.error('[AI Inbox] GmailDetector not available for watcher!');
    return;
  }
  
  // Test: Force inject sidebar and check for thread immediately
  setTimeout(() => {
    if (!sidebarContainer) {
      console.log('[AI Inbox] Force injecting sidebar');
      injectSidebar();
    }
    
    // Check if we're on a thread
    const currentThreadId = GmailDetector.getCurrentThreadId();
    console.log('[AI Inbox] Current thread ID:', currentThreadId);
    console.log('[AI Inbox] Is thread view:', GmailDetector.isThreadView());
    
    if (currentThreadId && GmailDetector.isThreadView()) {
      const threadInfo = {
        threadId: currentThreadId,
        subject: GmailDetector.getThreadSubject(),
        participants: GmailDetector.getThreadParticipants(),
        emailCount: GmailDetector.getEmailCount()
      };
      console.log('[AI Inbox] Thread detected:', threadInfo);
      onThreadOpened(threadInfo);
    }
  }, 3000);
  
  GmailDetector.watchThreadChanges((threadInfo) => {
    if (threadInfo) {
      console.log('[AI Inbox] Thread opened:', threadInfo);
      onThreadOpened(threadInfo);
    } else {
      console.log('[AI Inbox] Thread closed');
      onThreadClosed();
    }
  });
  
  console.log('[AI Inbox] Thread watcher setup complete');
}

/**
 * Handle thread opened
 */
function onThreadOpened(threadInfo) {
  currentThreadId = threadInfo.threadId;

  // Inject sidebar if not already present
  if (!sidebarContainer) {
    injectSidebar();
  }

  // Update sidebar with thread info
  updateSidebar(threadInfo);
}

/**
 * Handle thread closed
 */
function onThreadClosed() {
  currentThreadId = null;

  // Optionally remove sidebar or keep it visible
  // For now, we'll keep it and show a "no thread" state
  if (sidebarContainer) {
    const iframe = sidebarContainer.querySelector('iframe');
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.postMessage({
        type: 'THREAD_CLOSED'
      }, '*');
    }
  }
}

/**
 * Inject the sidebar into Gmail
 */
function injectSidebar() {
  console.log('[AI Inbox] Injecting AI sidebar...');

  // Create sidebar container
  sidebarContainer = DOMUtils.createElement('div', {
    id: 'ai-inbox-sidebar',
    className: 'ai-inbox-sidebar',
    style: {
      position: 'fixed',
      right: '0',
      top: '0',
      width: '400px',
      height: '100vh',
      zIndex: '9999',
      backgroundColor: '#ffffff',
      borderLeft: '1px solid #e0e0e0',
      boxShadow: '-2px 0 8px rgba(0,0,0,0.1)',
      display: 'flex',
      flexDirection: 'column'
    }
  });

  console.log('[AI Inbox] Sidebar container created');

  // Create iframe for sidebar content
  const iframe = DOMUtils.injectIframe('sidebar/sidebar.html', 'ai-inbox-sidebar-iframe');
  console.log('[AI Inbox] Iframe created:', iframe);
  console.log('[AI Inbox] Iframe src:', iframe.src);

  // Add load listener to debug iframe loading
  iframe.addEventListener('load', () => {
    console.log('[AI Inbox] Iframe loaded successfully');
  });

  iframe.addEventListener('error', (e) => {
    console.error('[AI Inbox] Iframe load error:', e);
  });

  sidebarContainer.appendChild(iframe);

  // Add to page
  document.body.appendChild(sidebarContainer);

  // Adjust Gmail layout to make room for sidebar
  adjustGmailLayout();

  console.log('✅ Sidebar injected successfully!');
}

/**
 * Adjust Gmail layout to accommodate sidebar
 */
function adjustGmailLayout() {
  // Add padding to the right of Gmail content
  const style = document.createElement('style');
  style.id = 'ai-inbox-layout-adjust';
  style.textContent = `
    body {
      margin-right: 400px !important;
    }
  `;
  document.head.appendChild(style);
}

/**
 * Update sidebar with thread information
 */
function updateSidebar(threadInfo) {
  const iframe = sidebarContainer?.querySelector('iframe');

  if (iframe && iframe.contentWindow) {
    // Send thread info to sidebar
    iframe.contentWindow.postMessage({
      type: 'THREAD_OPENED',
      threadInfo: threadInfo
    }, '*');
  }
}

/**
 * Listen for messages from sidebar
 */
window.addEventListener('message', (event) => {
  // Only accept messages from our extension
  if (event.source !== sidebarContainer?.querySelector('iframe')?.contentWindow) {
    return;
  }

  console.log('Message from sidebar:', event.data);

  switch (event.data.type) {
    case 'SIDEBAR_READY':
      // Sidebar loaded, send current thread if any
      if (currentThreadId) {
        const threadInfo = {
          threadId: currentThreadId,
          subject: GmailDetector.getThreadSubject(),
          participants: GmailDetector.getThreadParticipants(),
          emailCount: GmailDetector.getEmailCount()
        };
        updateSidebar(threadInfo);
      }
      break;

    case 'CLOSE_SIDEBAR':
      if (sidebarContainer) {
        sidebarContainer.remove();
        sidebarContainer = null;

        // Remove layout adjustment
        const style = document.getElementById('ai-inbox-layout-adjust');
        if (style) {
          style.remove();
        }
      }
      break;

    case 'OPEN_REPLY_EDITOR':
      // TODO: Implement reply editor integration with Gmail
      console.log('Open reply editor requested');
      break;
  }
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGmail);
} else {
  initGmail();
}
