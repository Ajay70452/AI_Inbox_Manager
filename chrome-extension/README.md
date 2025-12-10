# AI Inbox Manager - Chrome Extension

Chrome extension for AI-powered email management in Gmail and Outlook.

## Features

- **AI Email Summaries** - Get instant AI-generated summaries of email threads
- **Priority Classification** - Automatically classify emails by priority (High/Medium/Low)
- **Sentiment Analysis** - Detect email sentiment and urgency
- **Task Extraction** - Automatically extract action items from emails
- **Auto-Reply Drafts** - Generate contextual reply drafts with AI
- **Quick Actions** - Send to Slack, create tasks in integrated tools

## Installation

### Development Mode

1. **Ensure Backend is Running:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Load Extension in Chrome:**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)
   - Click "Load unpacked"
   - Select the `chrome-extension` folder

3. **Verify Installation:**
   - Extension icon should appear in Chrome toolbar
   - Click icon to open settings popup

### Production Build

TODO: Add build process for production deployment to Chrome Web Store

## Usage

### First Time Setup

1. **Open Gmail or Outlook** in Chrome
2. **Login** through the sidebar that appears on the right
3. **Grant Permissions** (if prompted)
4. **Select an Email** to see AI insights

### Using the Sidebar

The AI sidebar automatically appears when you:
- Open Gmail (mail.google.com)
- Open Outlook (outlook.live.com, outlook.office.com)

**Sidebar Features:**
- **AI Summary** - Concise summary of the email thread
- **Priority Badge** - High/Medium/Low classification
- **Sentiment Badge** - Positive/Neutral/Negative
- **Extracted Tasks** - Action items with due dates
- **Auto-Reply Draft** - AI-generated response
- **Quick Actions** - Integration buttons

### Keyboard Shortcuts

TODO: Add keyboard shortcuts for common actions

## Architecture

### File Structure

```
chrome-extension/
├── manifest.json           # Extension configuration
├── background.js          # Service worker (message handling, API calls)
├── content/              # Content scripts injected into pages
│   ├── gmail-detector.js    # Gmail thread detection
│   ├── gmail-injector.js    # Gmail sidebar injection
│   ├── outlook-detector.js  # Outlook message detection
│   └── outlook-injector.js  # Outlook sidebar injection
├── sidebar/              # Sidebar UI (loaded in iframe)
│   ├── sidebar.html        # Sidebar HTML
│   ├── sidebar.css         # Sidebar styles
│   └── sidebar.js          # Sidebar logic
├── popup/               # Extension popup (settings)
│   ├── popup.html
│   ├── popup.css
│   └── popup.js
├── utils/               # Shared utilities
│   ├── dom-utils.js        # DOM manipulation helpers
│   └── api-client.js       # Backend API client
├── styles/              # Global styles
│   └── sidebar.css         # Sidebar container styles
└── icons/               # Extension icons
    ├── icon16.png
    ├── icon32.png
    ├── icon48.png
    └── icon128.png
```

### Communication Flow

```
┌──────────────┐
│   Gmail/     │
│   Outlook    │
│   Page       │
└──────┬───────┘
       │
       ├─► Content Script (Detector)
       │   └─► Detects thread changes
       │
       ├─► Content Script (Injector)
       │   └─► Injects sidebar iframe
       │
       └─► Sidebar (iframe)
           ├─► Displays AI insights
           ├─► Handles user interactions
           └─► Communicates with background
                 │
                 ├─► Background Service Worker
                 │   ├─► Manages auth tokens
                 │   └─► Makes API calls
                 │
                 └─► Backend API
                     └─► Returns AI insights
```

### Gmail Detection

The extension detects Gmail threads by:
1. Monitoring URL hash changes (`#inbox/thread-id`)
2. Watching DOM for thread containers
3. Extracting thread metadata (subject, participants, count)

**Key Selectors:**
- Thread container: `[data-legacy-thread-id]`
- Subject: `h2.hP`
- Email count: `.G3`

### Outlook Detection

The extension detects Outlook messages by:
1. Monitoring URL pathname/hash (`/id/message-id`)
2. Watching DOM for reading pane
3. Extracting message metadata

**Key Selectors:**
- Reading pane: `[role="region"][aria-label*="Reading pane"]`
- Subject: `[role="heading"]`

## API Integration

### Authentication

The extension uses JWT authentication with the backend:

1. **Login Flow:**
   - User enters credentials in sidebar
   - Extension calls `POST /api/v1/auth/login`
   - Token stored in `chrome.storage.local`
   - Token included in all subsequent API calls

2. **Token Storage:**
   ```javascript
   await chrome.storage.local.set({
     authToken: 'jwt-token',
     user: { email: 'user@example.com' }
   });
   ```

3. **Token Usage:**
   ```javascript
   const token = await chrome.storage.local.get('authToken');
   fetch(url, {
     headers: { 'Authorization': `Bearer ${token}` }
   });
   ```

### API Endpoints Used

- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/threads/{id}/summary` - Get AI summary
- `GET /api/v1/threads/{id}/priority` - Get priority classification
- `GET /api/v1/threads/{id}/sentiment` - Get sentiment analysis
- `GET /api/v1/threads/{id}/reply` - Get auto-reply draft
- `GET /api/v1/threads/{id}/tasks` - Get extracted tasks
- `POST /api/v1/workers/ai/process/trigger` - Trigger AI processing

## Configuration

### Environment

The extension connects to the backend API at:
- **Development:** `http://localhost:8000/api/v1`
- **Production:** TODO: Update with production URL

To change the API URL, update:
- `background.js` - `API_BASE_URL` constant
- `sidebar/sidebar.js` - `API_BASE_URL` constant
- `utils/api-client.js` - `baseURL` property

### Permissions

The extension requires these permissions:
- **storage** - Store auth tokens and settings
- **activeTab** - Access current tab
- **identity** - OAuth flows (future)

And host permissions for:
- Gmail: `https://mail.google.com/*`
- Outlook: `https://outlook.live.com/*`, `https://outlook.office.com/*`
- Backend API: `http://localhost:8000/*`

## Development

### Local Testing

1. **Start Backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Load Extension:**
   - Navigate to `chrome://extensions/`
   - Load unpacked extension

3. **Test in Gmail:**
   - Open Gmail
   - Login through sidebar
   - Open an email thread
   - Verify AI insights appear

4. **View Logs:**
   - Right-click sidebar → Inspect (for sidebar logs)
   - Chrome DevTools console (for content script logs)
   - `chrome://extensions/` → Extension details → Service worker (for background logs)

### Debugging

**Content Script Issues:**
- Open Chrome DevTools on Gmail/Outlook page
- Check console for errors
- Verify content scripts are injected (Sources tab)

**Sidebar Issues:**
- Right-click sidebar iframe
- Select "Inspect" to open DevTools for iframe
- Check console and network tab

**Background Script Issues:**
- Go to `chrome://extensions/`
- Find extension, click "Service worker"
- Check logs and network requests

### Common Issues

**Sidebar Not Appearing:**
1. Check that backend is running
2. Verify content scripts are loaded (Chrome DevTools > Sources)
3. Check console for JavaScript errors
4. Ensure Gmail/Outlook has loaded completely

**Authentication Failing:**
1. Verify backend API is accessible
2. Check network tab for 401 errors
3. Ensure credentials are correct
4. Check token storage in DevTools > Application > Storage

**AI Insights Not Loading:**
1. Verify thread ID is being detected correctly
2. Check if AI processing was triggered
3. Look for API errors in network tab
4. Ensure backend workers are running

## Building for Production

TODO: Add production build steps

1. Update API URLs to production
2. Minify JavaScript files
3. Optimize images
4. Create manifest.json for production
5. Create .zip for Chrome Web Store

## Future Enhancements

- [ ] Keyboard shortcuts
- [ ] Offline mode with caching
- [ ] Real-time updates via WebSocket
- [ ] Customizable sidebar position
- [ ] Dark mode support
- [ ] Email compose integration
- [ ] Batch AI processing
- [ ] Custom prompt templates
- [ ] Integration settings in sidebar
- [ ] Analytics and usage tracking

## Troubleshooting

### Extension Won't Load
- Ensure manifest.json is valid JSON
- Check file permissions
- Verify all referenced files exist

### Sidebar Styles Broken
- Check for CSS conflicts with Gmail/Outlook
- Verify all CSS files are loaded
- Use `!important` for critical styles

### API Calls Failing
- Check CORS settings on backend
- Verify API URL is correct
- Check auth token is valid

## Support

For issues or questions:
1. Check browser console for errors
2. Review network tab for failed requests
3. Check backend logs
4. Report issues on GitHub

## License

Proprietary - All rights reserved

---

**Version:** 1.0.0
**Last Updated:** 2025-11-26
