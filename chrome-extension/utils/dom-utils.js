/**
 * DOM Utility Functions
 *
 * Helper functions for DOM manipulation and element detection
 */

const DOMUtils = {
  /**
   * Wait for an element to appear in the DOM
   */
  waitForElement(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
      const element = document.querySelector(selector);

      if (element) {
        resolve(element);
        return;
      }

      const observer = new MutationObserver((mutations, obs) => {
        const element = document.querySelector(selector);
        if (element) {
          obs.disconnect();
          resolve(element);
        }
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`Element ${selector} not found within ${timeout}ms`));
      }, timeout);
    });
  },

  /**
   * Create element with attributes and children
   */
  createElement(tag, attributes = {}, children = []) {
    const element = document.createElement(tag);

    Object.entries(attributes).forEach(([key, value]) => {
      if (key === 'className') {
        element.className = value;
      } else if (key === 'style' && typeof value === 'object') {
        Object.assign(element.style, value);
      } else if (key.startsWith('data-')) {
        element.setAttribute(key, value);
      } else {
        element[key] = value;
      }
    });

    children.forEach(child => {
      if (typeof child === 'string') {
        element.appendChild(document.createTextNode(child));
      } else if (child instanceof Node) {
        element.appendChild(child);
      }
    });

    return element;
  },

  /**
   * Debounce function calls
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * Get text content safely
   */
  getTextContent(element) {
    if (!element) return '';
    return element.textContent?.trim() || '';
  },

  /**
   * Check if element is visible
   */
  isVisible(element) {
    if (!element) return false;

    const style = window.getComputedStyle(element);
    return style.display !== 'none' &&
           style.visibility !== 'hidden' &&
           style.opacity !== '0';
  },

  /**
   * Inject iframe
   */
  injectIframe(src, containerId, styles = {}) {
    const iframe = this.createElement('iframe', {
      src: chrome.runtime.getURL(src),
      id: containerId,
      style: {
        border: 'none',
        width: '100%',
        height: '100%',
        ...styles
      }
    });

    return iframe;
  }
};

// Make available globally in content scripts
window.DOMUtils = DOMUtils;
