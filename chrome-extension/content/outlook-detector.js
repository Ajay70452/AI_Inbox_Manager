/**
 * Outlook Detector
 *
 * Detects when an Outlook thread is opened and extracts thread information
 */

const OutlookDetector = {
  /**
   * Check if we're on Outlook
   */
  isOutlook() {
    const hostname = window.location.hostname;
    return hostname.includes('outlook.live.com') ||
           hostname.includes('outlook.office.com') ||
           hostname.includes('outlook.office365.com');
  },

  /**
   * Get current message/thread ID from URL
   */
  getCurrentThreadId() {
    // Outlook URL format varies
    // https://outlook.live.com/mail/0/inbox/id/AQMK...
    // https://outlook.office.com/mail/inbox/id/AQMK...

    const hash = window.location.hash;
    const pathname = window.location.pathname;

    // Try hash first
    if (hash.includes('/id/')) {
      const match = hash.match(/\/id\/([^/]+)/);
      return match ? match[1] : null;
    }

    // Try pathname
    if (pathname.includes('/id/')) {
      const match = pathname.match(/\/id\/([^/]+)/);
      return match ? match[1] : null;
    }

    return null;
  },

  /**
   * Get thread subject
   */
  getThreadSubject() {
    // Outlook subject selectors
    const selectors = [
      '[aria-label*="Subject"] span',
      'div[role="heading"]',
      '.ReadingPaneSubject',
      'h1[class*="subject"]'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element && DOMUtils.getTextContent(element)) {
        return DOMUtils.getTextContent(element);
      }
    }

    return 'Unknown Subject';
  },

  /**
   * Get thread participants
   */
  getThreadParticipants() {
    const participants = [];

    // Look for sender info
    const senderElements = document.querySelectorAll('[aria-label*="From:"], [aria-label*="Sender:"]');

    senderElements.forEach(el => {
      const text = DOMUtils.getTextContent(el);
      // Try to extract email if present
      const emailMatch = text.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/);

      if (emailMatch) {
        participants.push({
          name: text.replace(emailMatch[0], '').trim(),
          email: emailMatch[0]
        });
      } else {
        participants.push({
          name: text,
          email: null
        });
      }
    });

    return participants;
  },

  /**
   * Get thread emails count
   */
  getEmailCount() {
    // Outlook usually shows conversation count
    const countElements = document.querySelectorAll('[aria-label*="messages"]');

    for (const el of countElements) {
      const text = DOMUtils.getTextContent(el);
      const match = text.match(/(\d+)\s+messages?/i);
      if (match) {
        return parseInt(match[1]);
      }
    }

    return 1;
  },

  /**
   * Check if current view is a message (not inbox list)
   */
  isMessageView() {
    const threadId = this.getCurrentThreadId();
    const hasReadingPane = document.querySelector('[role="region"][aria-label*="Reading pane"]') !== null ||
                           document.querySelector('.ReadingPane') !== null;

    return threadId !== null || hasReadingPane;
  },

  /**
   * Get the container where we should inject the sidebar
   */
  getSidebarContainer() {
    // Outlook has a reading pane we can extend
    const readingPane = document.querySelector('[role="region"][aria-label*="Reading pane"]') ||
                        document.querySelector('.ReadingPane') ||
                        document.querySelector('[role="main"]');

    if (readingPane) {
      return readingPane.parentElement;
    }

    // Fallback to body
    return document.body;
  },

  /**
   * Watch for message changes
   */
  watchMessageChanges(callback) {
    let lastThreadId = this.getCurrentThreadId();

    // Watch URL changes
    const observer = new MutationObserver(DOMUtils.debounce(() => {
      const currentThreadId = this.getCurrentThreadId();

      if (currentThreadId !== lastThreadId) {
        lastThreadId = currentThreadId;

        if (currentThreadId && this.isMessageView()) {
          setTimeout(() => {
            callback({
              threadId: currentThreadId,
              subject: this.getThreadSubject(),
              participants: this.getThreadParticipants(),
              emailCount: this.getEmailCount()
            });
          }, 500);
        } else {
          callback(null);
        }
      }
    }, 300));

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Also watch for hash/pathname changes
    const checkURL = () => {
      const currentThreadId = this.getCurrentThreadId();

      if (currentThreadId !== lastThreadId) {
        lastThreadId = currentThreadId;

        setTimeout(() => {
          if (currentThreadId && this.isMessageView()) {
            callback({
              threadId: currentThreadId,
              subject: this.getThreadSubject(),
              participants: this.getThreadParticipants(),
              emailCount: this.getEmailCount()
            });
          } else {
            callback(null);
          }
        }, 500);
      }
    };

    window.addEventListener('hashchange', checkURL);
    window.addEventListener('popstate', checkURL);

    // Check initial state
    if (lastThreadId && this.isMessageView()) {
      setTimeout(() => {
        callback({
          threadId: lastThreadId,
          subject: this.getThreadSubject(),
          participants: this.getThreadParticipants(),
          emailCount: this.getEmailCount()
        });
      }, 1000);
    }

    return observer;
  }
};

// Make available globally
window.OutlookDetector = OutlookDetector;
