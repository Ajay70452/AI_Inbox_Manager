/**
 * Gmail Detector
 *
 * Detects when a Gmail thread is opened and extracts thread information
 */

const GmailDetector = {
  /**
   * Check if we're on Gmail
   */
  isGmail() {
    return window.location.hostname === 'mail.google.com';
  },

  /**
   * Get current thread ID
   * Returns an object with both URL-based ID and legacy (hex) ID when available
   */
  getCurrentThreadId() {
    const hash = window.location.hash;
    console.log('🔍 Checking URL hash:', hash);

    let urlThreadId = null;
    let legacyThreadId = null;

    // Gmail URL formats:
    // #inbox/FMfcgzQVHMPsKldX... (new format - base64-like)
    // #inbox/19b04108a423e17d (old format - hex)
    // #label/LabelName/FMfcgzQVHMPsKldX...
    // #search/query/FMfcgzQVHMPsKldX...
    // #sent/FMfcgzQVHMPsKldX...

    const hashParts = hash.split('/');
    console.log('🔍 Hash parts:', hashParts);

    if (hashParts.length >= 2) {
      const potentialId = hashParts[hashParts.length - 1];
      console.log('🔍 Potential ID from URL:', potentialId, 'Length:', potentialId.length);

      // Match both old hex format AND new base64-like format
      const isHexFormat = /^[a-fA-F0-9]{16,}$/.test(potentialId);
      const isNewFormat = /^[A-Za-z0-9_-]{15,}$/.test(potentialId);
      console.log('🔍 Is hex format:', isHexFormat, 'Is new format:', isNewFormat);

      if (isHexFormat || isNewFormat) {
        urlThreadId = potentialId;
        console.log('✅ Found thread ID from URL:', urlThreadId);
      }
    }

    // Check DOM for data-legacy-thread-id (hex format that matches Gmail API)
    // This is what the backend stores, so it's the preferred ID for API calls
    const mainView = document.querySelector('.AO') || document.querySelector('[role="main"]');
    if (mainView) {
      const threadElement = mainView.querySelector('[data-legacy-thread-id]');
      if (threadElement) {
        legacyThreadId = threadElement.getAttribute('data-legacy-thread-id');
        console.log('✅ Found legacy thread ID from DOM:', legacyThreadId);
      }

      // Also try data-thread-perm-id if legacy not found
      if (!legacyThreadId) {
        const threadPermElement = mainView.querySelector('[data-thread-perm-id]');
        if (threadPermElement) {
          legacyThreadId = threadPermElement.getAttribute('data-thread-perm-id');
          console.log('✅ Found thread ID from DOM (data-thread-perm-id):', legacyThreadId);
        }
      }
    }

    // Fallback: Check anywhere in DOM
    if (!legacyThreadId) {
      const threadElement = document.querySelector('[data-legacy-thread-id]');
      if (threadElement && threadElement.offsetParent !== null) {
        legacyThreadId = threadElement.getAttribute('data-legacy-thread-id');
        console.log('✅ Found legacy thread ID from DOM (Fallback):', legacyThreadId);
      }
    }

    // Prefer legacy ID (hex format) as it matches what backend stores
    // But use URL ID as fallback and for change detection
    const effectiveId = legacyThreadId || urlThreadId;

    if (effectiveId) {
      console.log(`✅ Using thread ID: ${effectiveId} (legacy: ${legacyThreadId}, url: ${urlThreadId})`);
      return effectiveId;
    }

    console.log('❌ No thread ID found');
    return null;
  },

  /**
   * Get thread subject
   */
  getThreadSubject() {
    // Try multiple selectors as Gmail's DOM changes
    const selectors = [
      'h2.hP',
      '[data-legacy-thread-id] h2',
      '.ha h2'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
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
    const emailElements = document.querySelectorAll('[email]');

    emailElements.forEach(el => {
      const email = el.getAttribute('email');
      const name = el.getAttribute('name') || DOMUtils.getTextContent(el);

      if (email && !participants.find(p => p.email === email)) {
        participants.push({ name, email });
      }
    });

    return participants;
  },

  /**
   * Get thread emails count
   */
  getEmailCount() {
    // Look for the email count indicator
    const countElement = document.querySelector('[data-legacy-thread-id] .G3');
    if (countElement) {
      const text = DOMUtils.getTextContent(countElement);
      const match = text.match(/\d+/);
      return match ? parseInt(match[0]) : 1;
    }
    return 1;
  },

  /**
   * Check if current view is a thread (not inbox list)
   */
  isThreadView() {
    const threadId = this.getCurrentThreadId();
    
    // Check if we are in a thread view container
    // .AO is the main content area
    // .nH.aHU is often the thread container
    // But the most reliable way is to check if we have a thread ID in URL 
    // AND we are not in a list view (like inbox)
    
    const hash = window.location.hash;
    const isInbox = hash.startsWith('#inbox') && !hash.includes('/');
    const isLabel = hash.startsWith('#label') && hash.split('/').length === 2;
    
    // If we are strictly in inbox or label list, it's not a thread view
    if (isInbox || isLabel) {
        return false;
    }

    // If we have a thread ID, we are likely in a thread view
    return threadId !== null;
  },

  /**
   * Get the container where we should inject the sidebar
   */
  getSidebarContainer() {
    // Gmail has a right sidebar area we can use
    // Look for the main email content area
    const mainContent = document.querySelector('.AO');

    if (mainContent) {
      return mainContent.parentElement;
    }

    // Fallback to body
    return document.body;
  },

  /**
   * Watch for thread changes
   */
  watchThreadChanges(callback) {
    let lastReportedId = null;
    let lastUrlId = null;
    let checkTimeout = null;
    let waitingForDomUpdate = false;

    const reportThread = (threadId) => {
      if (threadId !== lastReportedId) {
        console.log(`🔄 Thread state changed: ${lastReportedId} -> ${threadId}`);
        lastReportedId = threadId;

        if (threadId) {
          // Give DOM a moment to settle for subject/participants
          setTimeout(() => {
            callback({
              threadId: threadId,
              subject: this.getThreadSubject(),
              participants: this.getThreadParticipants(),
              emailCount: this.getEmailCount()
            });
          }, 100);
        } else {
          callback(null);
        }
      }
    };

    const checkForLegacyId = (expectedUrlId, attempts = 0) => {
      const maxAttempts = 10;
      const legacyId = this.getLegacyThreadId();

      console.log(`🔍 Checking for legacy ID (attempt ${attempts + 1}): found ${legacyId}`);

      if (legacyId) {
        // Found the legacy ID, report it
        waitingForDomUpdate = false;
        reportThread(legacyId);
      } else if (attempts < maxAttempts) {
        // Keep waiting for DOM to update
        setTimeout(() => checkForLegacyId(expectedUrlId, attempts + 1), 100);
      } else {
        // Give up waiting, use URL ID as fallback
        console.log('⚠️ Could not find legacy ID, using URL ID:', expectedUrlId);
        waitingForDomUpdate = false;
        reportThread(expectedUrlId);
      }
    };

    const checkChange = () => {
      if (waitingForDomUpdate) {
        return; // Don't interrupt ongoing DOM wait
      }

      const isView = this.isThreadView();
      if (!isView) {
        reportThread(null);
        return;
      }

      const legacyId = this.getLegacyThreadId();
      if (legacyId) {
        reportThread(legacyId);
      }
    };

    // Debounced check for MutationObserver (fires very frequently)
    const debouncedCheck = () => {
      if (checkTimeout) {
        clearTimeout(checkTimeout);
      }
      checkTimeout = setTimeout(checkChange, 150);
    };

    // Watch DOM changes with debouncing
    const observer = new MutationObserver(debouncedCheck);

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Watch for hash changes - this is the primary navigation detection
    window.addEventListener('hashchange', () => {
      const hash = window.location.hash;
      console.log('🔗 Hash changed:', hash);

      // Clear any pending debounced check
      if (checkTimeout) {
        clearTimeout(checkTimeout);
        checkTimeout = null;
      }

      // Extract URL thread ID
      const urlId = this.getUrlThreadId();
      console.log('🔗 URL thread ID:', urlId);

      if (!urlId) {
        // No thread in URL (e.g., went back to inbox)
        lastUrlId = null;
        waitingForDomUpdate = false;
        reportThread(null);
        return;
      }

      // URL changed to a new thread OR we are re-entering the same thread
      // We should always re-check if the URL ID is present
      lastUrlId = urlId;
      waitingForDomUpdate = true;

      // Wait for DOM to update with new data-legacy-thread-id
      // This is the hex ID that matches what backend stores
      setTimeout(() => checkForLegacyId(urlId), 100);
    });

    // Check initial state
    setTimeout(checkChange, 1000);

    return observer;
  },

  /**
   * Get thread ID from URL only
   */
  getUrlThreadId() {
    const hash = window.location.hash;
    const hashParts = hash.split('/');

    if (hashParts.length >= 2) {
      const potentialId = hashParts[hashParts.length - 1];
      const isHexFormat = /^[a-fA-F0-9]{16,}$/.test(potentialId);
      const isNewFormat = /^[A-Za-z0-9_-]{15,}$/.test(potentialId);

      if (isHexFormat || isNewFormat) {
        return potentialId;
      }
    }
    return null;
  },

  /**
   * Get legacy thread ID from DOM only (hex format that matches Gmail API)
   */
  getLegacyThreadId() {
    const mainView = document.querySelector('.AO') || document.querySelector('[role="main"]');
    if (mainView) {
      const threadElement = mainView.querySelector('[data-legacy-thread-id]');
      if (threadElement) {
        return threadElement.getAttribute('data-legacy-thread-id');
      }

      const threadPermElement = mainView.querySelector('[data-thread-perm-id]');
      if (threadPermElement) {
        return threadPermElement.getAttribute('data-thread-perm-id');
      }
    }

    // Fallback
    const threadElement = document.querySelector('[data-legacy-thread-id]');
    if (threadElement && threadElement.offsetParent !== null) {
      return threadElement.getAttribute('data-legacy-thread-id');
    }

    return null;
  }
};

// Make available globally
window.GmailDetector = GmailDetector;
