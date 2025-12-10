/**
 * Outlook Injector
 *
 * Injects the AI sidebar into Outlook
 */

let sidebarContainer = null;
let currentThreadId = null;

/**
 * Initialize Outlook integration
 */
function initOutlook() {
  console.log('AI Inbox Manager: Initializing Outlook integration');

  if (!OutlookDetector.isOutlook()) {
    console.log('Not on Outlook, skipping');
    return;
  }

  // Wait for Outlook to load
  DOMUtils.waitForElement('[role="main"]', 15000)
    .then(() => {
      console.log('Outlook loaded, setting up message watcher');
      setupMessageWatcher();
    })
    .catch(err => {
      console.error('Outlook did not load:', err);
    });
}

/**
 * Setup message watcher
 */
function setupMessageWatcher() {
  OutlookDetector.watchMessageChanges((messageInfo) => {
    if (messageInfo) {
      console.log('Message opened:', messageInfo);
      onMessageOpened(messageInfo);
    } else {
      console.log('Message closed');
      onMessageClosed();
    }
  });
}

/**
 * Handle message opened
 */
function onMessageOpened(messageInfo) {
  currentThreadId = messageInfo.threadId;

  // Inject sidebar if not already present
  if (!sidebarContainer) {
    injectSidebar();
  }

  // Update sidebar with message info
  updateSidebar(messageInfo);
}

/**
 * Handle message closed
 */
function onMessageClosed() {
  currentThreadId = null;

  // Keep sidebar visible with "no message" state
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
 * Inject the sidebar into Outlook
 */
function injectSidebar() {
  console.log('Injecting AI sidebar');

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

  // Create iframe for sidebar content
  const iframe = DOMUtils.injectIframe('sidebar/sidebar.html', 'ai-inbox-sidebar-iframe');

  sidebarContainer.appendChild(iframe);

  // Add to page
  document.body.appendChild(sidebarContainer);

  // Adjust Outlook layout to make room for sidebar
  adjustOutlookLayout();

  console.log('Sidebar injected');
}

/**
 * Adjust Outlook layout to accommodate sidebar
 */
function adjustOutlookLayout() {
  // Add padding to the right of Outlook content
  const style = document.createElement('style');
  style.id = 'ai-inbox-layout-adjust';
  style.textContent = `
    body {
      margin-right: 400px !important;
    }
    [role="main"] {
      margin-right: 0 !important;
    }
  `;
  document.head.appendChild(style);
}

/**
 * Update sidebar with message information
 */
function updateSidebar(messageInfo) {
  const iframe = sidebarContainer?.querySelector('iframe');

  if (iframe && iframe.contentWindow) {
    // Send message info to sidebar
    iframe.contentWindow.postMessage({
      type: 'THREAD_OPENED',
      threadInfo: messageInfo
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
      // Sidebar loaded, send current message if any
      if (currentThreadId) {
        const messageInfo = {
          threadId: currentThreadId,
          subject: OutlookDetector.getThreadSubject(),
          participants: OutlookDetector.getThreadParticipants(),
          emailCount: OutlookDetector.getEmailCount()
        };
        updateSidebar(messageInfo);
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
      // TODO: Implement reply editor integration with Outlook
      console.log('Open reply editor requested');
      break;
  }
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initOutlook);
} else {
  initOutlook();
}
