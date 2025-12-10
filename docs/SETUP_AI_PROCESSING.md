# AI Processing Setup Guide

## Overview
The AI Inbox Manager uses LLM APIs (OpenAI, Anthropic, or Google Gemini) to provide:
- Email summarization
- Priority classification
- Sentiment analysis
- Task extraction
- Auto-reply draft generation

## Step 1: Choose Your LLM Provider

You can use any of these providers:
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude)
- **Google** (Gemini)

## Step 2: Get API Keys

### Option A: OpenAI (Recommended for getting started)

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to "API Keys" in the left sidebar
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. Add credits to your account if needed

### Option B: Anthropic Claude

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)

### Option C: Google Gemini

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key

## Step 3: Update Backend .env

Open `backend/.env` and add your API key(s):

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key-here
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4-turbo-preview

# OR Anthropic Claude
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
# DEFAULT_LLM_PROVIDER=anthropic
# DEFAULT_LLM_MODEL=claude-3-sonnet-20240229

# OR Google Gemini
# GEMINI_API_KEY=your-gemini-key-here
# DEFAULT_LLM_PROVIDER=gemini
# DEFAULT_LLM_MODEL=gemini-pro
```

## Step 4: Restart Backend Server

After updating the .env file, restart your backend server for the changes to take effect.

## Step 5: Test AI Processing

Once configured, you can test AI features:

1. **Sync Emails**: Go to Settings → Click "Sync Now" on Gmail
2. **View AI Summaries**: Navigate to the Threads/Emails page
3. **Generate Summaries**: Click on an email thread to see AI-generated insights

## Default Models

- **OpenAI**: `gpt-4-turbo-preview` (best quality) or `gpt-3.5-turbo` (faster, cheaper)
- **Anthropic**: `claude-3-sonnet-20240229` (balanced) or `claude-3-opus-20240229` (best)
- **Gemini**: `gemini-pro` (standard model)

## Cost Considerations

- **OpenAI GPT-4**: ~$0.01-0.03 per request
- **OpenAI GPT-3.5**: ~$0.001-0.002 per request
- **Claude Sonnet**: ~$0.003-0.015 per request
- **Gemini Pro**: Free tier available, then ~$0.001 per request

Start with GPT-3.5-turbo or Gemini Pro if you want to minimize costs during testing.
