/**
 * API Client
 *
 * Handles all communication with the backend API
 */

const APIClient = {
  baseURL: 'http://localhost:8000/api/v1',

  /**
   * Get authentication token
   */
  async getAuthToken() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { action: 'getAuthToken' },
        (response) => {
          resolve(response?.token || null);
        }
      );
    });
  },

  /**
   * Save authentication token
   */
  async saveAuthToken(token) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { action: 'saveAuthToken', token },
        (response) => {
          resolve(response?.success || false);
        }
      );
    });
  },

  /**
   * Logout
   */
  async logout() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { action: 'logout' },
        (response) => {
          resolve(response?.success || false);
        }
      );
    });
  },

  /**
   * Fetch AI insights for a thread
   */
  async fetchAIInsights(threadId) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { action: 'fetchAIInsights', threadId },
        (response) => {
          if (response?.success) {
            resolve(response.insights);
          } else {
            reject(new Error(response?.error || 'Failed to fetch AI insights'));
          }
        }
      );
    });
  },

  /**
   * Trigger AI processing for a thread
   */
  async triggerAIProcessing(threadId) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { action: 'triggerAIProcessing', threadId },
        (response) => {
          if (response?.success) {
            resolve(response.data);
          } else {
            reject(new Error(response?.error || 'Failed to trigger AI processing'));
          }
        }
      );
    });
  },

  /**
   * Make authenticated API request
   */
  async request(endpoint, options = {}) {
    const token = await this.getAuthToken();

    if (!token) {
      throw new Error('Not authenticated');
    }

    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers
    };

    const response = await fetch(url, {
      ...options,
      headers
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid
        await this.logout();
        throw new Error('Authentication expired. Please login again.');
      }
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Login with email and password
   */
  async login(email, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    await this.saveAuthToken(data.access_token);

    return data;
  },

  /**
   * Sign up new user
   */
  async signup(email, password, fullName) {
    const response = await fetch(`${this.baseURL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    const data = await response.json();
    await this.saveAuthToken(data.access_token);

    return data;
  },

  /**
   * Send a reply to a thread
   */
  async sendReply(threadId, body, html = false) {
    return this.request('/emails/reply', {
      method: 'POST',
      body: JSON.stringify({
        thread_id: threadId,
        body: body,
        html: html
      })
    });
  },

  /**
   * Send a new email
   */
  async sendEmail(to, subject, body, provider, options = {}) {
    return this.request('/emails/send', {
      method: 'POST',
      body: JSON.stringify({
        to,
        subject,
        body,
        provider,
        cc: options.cc,
        bcc: options.bcc,
        html: options.html || false
      })
    });
  }
};

// Make available globally in content scripts
window.APIClient = APIClient;
