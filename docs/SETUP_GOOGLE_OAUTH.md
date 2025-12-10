# Google OAuth Setup Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top
3. Click "New Project"
4. Enter project name: "AI Inbox Manager"
5. Click "Create"

## Step 2: Enable Gmail API

1. In the left sidebar, go to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type
3. Click "Create"
4. Fill in the required fields:
   - App name: AI Inbox Manager
   - User support email: your email
   - Developer contact email: your email
5. Click "Save and Continue"
6. On "Scopes" page, click "Add or Remove Scopes"
7. Add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly` (Read emails)
   - `https://www.googleapis.com/auth/gmail.send` (Send emails)
   - `https://www.googleapis.com/auth/userinfo.email` (Get user email)
   - `https://www.googleapis.com/auth/userinfo.profile` (Get user profile)
8. Click "Update" then "Save and Continue"
9. On "Test users" page, add your Gmail address
10. Click "Save and Continue"

## Step 4: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Enter name: "AI Inbox Manager - Web"
5. Add Authorized redirect URIs:
   - `http://localhost:8000/api/v1/auth/google/callback`
   - `http://localhost:3000/auth/callback` (for frontend)
6. Click "Create"
7. Copy the **Client ID** and **Client Secret**

## Step 5: Update Backend .env

Update your `backend/.env` file:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

## Step 6: Restart Backend Server

After updating the .env file, restart the backend server for changes to take effect.

## Testing

1. Go to http://localhost:3000/dashboard/settings
2. Click "Authorize Gmail"
3. You should see Google's OAuth consent screen
4. Grant permissions
5. You'll be redirected back to your application

## Production Setup

For production:
1. Change OAuth consent screen to "In Production" (requires verification)
2. Update redirect URIs to use your production domain
3. Update GOOGLE_REDIRECT_URI in .env to production URL
