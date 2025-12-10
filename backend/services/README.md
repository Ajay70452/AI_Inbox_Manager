# AI Orchestration Layer - The "Secret Sauce"

This directory contains the AI orchestration system that powers intelligent email management.

## 🎯 Overview

The AI Orchestration Layer is the **core differentiator** of AI Inbox Manager. It doesn't just call LLM APIs - it intelligently:

1. **Injects Company Context** - Uses your policies, FAQs, and tone guidelines
2. **Manages Conversation History** - Understands full email threads
3. **Routes Intelligently** - Chooses the right LLM for each task
4. **Handles Retries** - Automatically recovers from API failures
5. **Ensures Quality** - Validates and parses structured outputs

## 📂 Architecture

```
services/
├── prompts.py              # Prompt templates (the foundation)
├── llm_providers.py        # LLM API clients (OpenAI, Claude, Gemini)
├── ai_orchestrator.py      # Main orchestration logic (THE SECRET SAUCE)
├── summarizer.py           # Summarization service
├── classifier.py           # Priority classification service
├── sentiment_analyzer.py   # Sentiment analysis service
├── reply_generator.py      # Auto-reply generation service
└── task_extractor.py       # Task extraction service
```

## 🧩 Components

### 1. Prompt Templates (`prompts.py`)

**Purpose**: Centralized, optimized prompts for each AI task

**Key Methods**:
- `summarization_prompt()` - Thread summarization
- `priority_classification_prompt()` - Priority detection
- `sentiment_analysis_prompt()` - Emotion detection
- `reply_generation_prompt()` - Auto-reply drafting
- `task_extraction_prompt()` - Action item extraction
- `escalation_detection_prompt()` - Alert triggering
- `reply_rewrite_prompt()` - Style transformation

**Features**:
- Context injection placeholders
- Structured output instructions (JSON)
- Company context integration
- Historical data inclusion

### 2. LLM Providers (`llm_providers.py`)

**Purpose**: Unified interface to multiple LLM providers

**Supported Providers**:
- **OpenAI** (GPT-4 Turbo, GPT-3.5)
- **Anthropic Claude** (Claude 3 Sonnet, Opus)
- **Google Gemini** (Gemini Pro)

**Key Classes**:
- `LLMProvider` - Abstract base class
- `OpenAIProvider` - OpenAI implementation
- `AnthropicProvider` - Claude implementation
- `GeminiProvider` - Gemini implementation
- `LLMFactory` - Provider factory
- `parse_json_response()` - JSON extraction utility

**Features**:
- Automatic provider selection
- JSON mode support (where available)
- Temperature control
- Token limit management

### 3. AI Orchestrator (`ai_orchestrator.py`) 🌟

**Purpose**: The "secret sauce" - coordinates all AI operations

**This is the CORE DIFFERENTIATOR** - it's what makes our system intelligent, not just a wrapper around LLMs.

**Key Responsibilities**:
1. **Context Fetching**
   - Loads user's company context (policies, FAQs, tone)
   - Fetches email thread history
   - Cleans and normalizes data

2. **Prompt Building**
   - Injects company context into prompts
   - Includes relevant conversation history
   - Manages token limits intelligently

3. **LLM Management**
   - Routes requests to appropriate provider
   - Handles API rate limits
   - Implements exponential backoff retry

4. **Response Processing**
   - Parses structured outputs (JSON)
   - Validates responses
   - Handles malformed data gracefully

**Key Methods**:
- `summarize_thread()` - Generate thread summary
- `classify_priority()` - Determine priority level
- `analyze_sentiment()` - Detect emotion/urgency
- `generate_reply()` - Create draft response
- `extract_tasks()` - Pull action items
- `rewrite_reply()` - Transform reply style
- `detect_escalation()` - Identify urgent issues

**Example Usage**:
```python
from services import AIOrchestrator

# Initialize with user context
orchestrator = AIOrchestrator(db, user)

# Generate summary with full context injection
summary = orchestrator.summarize_thread(thread_id)

# Classify with company knowledge
priority = orchestrator.classify_priority(thread_id)

# Generate contextual reply
reply = orchestrator.generate_reply(thread_id, tone="friendly")
```

### 4. Processing Services

These services wrap the orchestrator with database operations:

**SummarizationService** (`summarizer.py`)
- Generates and stores thread summaries
- Checks for existing summaries
- Supports forced regeneration

**ClassificationService** (`classifier.py`)
- Classifies email priority (urgent, customer, vendor, internal, low)
- Determines category
- Persists classifications

**SentimentAnalysisService** (`sentiment_analyzer.py`)
- Analyzes emotional tone
- Detects anger and urgency
- Returns sentiment scores (-1.0 to 1.0)

**ReplyGenerationService** (`reply_generator.py`)
- Generates context-aware replies
- Supports tone customization
- Allows style transformations (shorter, formal, friendly)

**TaskExtractionService** (`task_extractor.py`)
- Extracts action items from emails
- Identifies deadlines and owners
- Creates Task database records

## 🔄 Request Flow

```
1. API Request
   ↓
2. Processing Service (e.g., SummarizationService)
   ↓
3. AI Orchestrator
   ↓
4. Fetch Context (Company + Thread)
   ↓
5. Build Prompt (Template + Context)
   ↓
6. LLM Provider (OpenAI/Claude/Gemini)
   ↓
7. Parse & Validate Response
   ↓
8. Store in Database
   ↓
9. Return to API
```

## 🎨 Context Injection Example

Here's how company context transforms a generic prompt into an intelligent one:

**Without Context** (Generic LLM):
```
"Summarize this email thread."
```

**With Context** (Our System):
```
You are an AI assistant for Acme Corp, a SaaS company.

Company Context:
- Products: Project Management Tool, Time Tracker
- Tone: Professional and empathetic
- Key Policies: 48-hour response SLA, refunds within 30 days

Email Thread:
[Full conversation history with metadata]

Summarize this thread considering:
- Company policies
- Product context
- Tone guidelines
```

This context injection is **what makes our AI valuable** - it's not just summarizing, it's understanding your business.

## 🔧 Configuration

### Environment Variables

```env
# LLM Provider Selection
DEFAULT_LLM_PROVIDER=openai  # openai, anthropic, gemini
DEFAULT_LLM_MODEL=gpt-4-turbo-preview

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# AI Settings
AI_CONTEXT_MAX_TOKENS=8000
AI_TEMPERATURE=0.7
```

### Choosing a Provider

**OpenAI (Recommended)**
- ✅ Best JSON mode support
- ✅ Most reliable
- ✅ Fastest response times
- ❌ More expensive

**Anthropic Claude**
- ✅ Excellent instruction following
- ✅ Longer context windows
- ✅ Good for complex reasoning
- ❌ No native JSON mode

**Google Gemini**
- ✅ Cost-effective
- ✅ Multimodal capabilities
- ❌ Less consistent structured output

## 🚀 Usage Examples

### Basic Summarization

```python
from services import SummarizationService

service = SummarizationService(db, current_user)
summary = service.summarize_thread(thread_id="abc-123")

print(summary.summary_text)
# "Customer reporting login issues with SSO. Team investigating..."
```

### Priority Classification

```python
from services import ClassificationService

service = ClassificationService(db, current_user)
priority = service.classify_thread(thread_id="abc-123")

print(priority.priority_level)  # "urgent"
print(priority.category)         # "customer complaint"
```

### Reply Generation with Context

```python
from services import ReplyGenerationService

service = ReplyGenerationService(db, current_user)

# Generate with company tone
draft = service.generate_reply(thread_id="abc-123")

# Regenerate with different style
draft = service.regenerate_with_style(
    thread_id="abc-123",
    style="more empathetic"
)
```

### Task Extraction

```python
from services import TaskExtractionService

service = TaskExtractionService(db, current_user)
tasks = service.extract_tasks(thread_id="abc-123")

for task in tasks:
    print(f"- {task.title} (due: {task.due_date})")
```

## 🛡️ Error Handling

The orchestrator includes robust error handling:

```python
try:
    summary = orchestrator.summarize_thread(thread_id)
except ValueError:
    # Thread not found or no emails
    pass
except ExternalServiceError:
    # LLM API failed after retries
    pass
```

**Retry Logic**:
- 3 automatic retries with exponential backoff
- Logs all retry attempts
- Graceful degradation on total failure

## 📊 Token Management

The orchestrator automatically:
- Truncates long email bodies (max 5000 chars per email)
- Limits total context to `AI_CONTEXT_MAX_TOKENS`
- Prioritizes recent emails in long threads

## 🎯 Best Practices

### For Developers

1. **Always inject company context** - It's what makes our AI valuable
2. **Use structured prompts** - Request JSON for parseable outputs
3. **Handle edge cases** - Empty threads, missing context, API failures
4. **Log extensively** - AI debugging requires good logs
5. **Cache results** - Don't regenerate unnecessarily

### For Prompt Design

1. **Be explicit** - "Output as JSON" not "return data"
2. **Provide examples** - Show desired format
3. **Set constraints** - "Max 120 words", "Only explicit tasks"
4. **Use context wisely** - Inject relevant parts, not everything
5. **Test across providers** - Different LLMs interpret differently

## 🔮 Future Enhancements

- [ ] **Multi-turn conversations** - Interactive refinement
- [ ] **Historical learning** - Learn from user edits
- [ ] **Custom prompt library** - User-defined templates
- [ ] **Batch processing** - Process multiple threads efficiently
- [ ] **Streaming responses** - Real-time generation
- [ ] **A/B testing framework** - Test prompt variations
- [ ] **Cost tracking** - Monitor token usage per user

## 📚 Related Documentation

- [API Endpoints](../routers/ai.py)
- [Database Models](../models/)
- [Configuration](../app/config.py)
- [Main README](../../README.md)

---

**The AI Orchestration Layer is the heart of AI Inbox Manager** - it's what transforms a simple LLM wrapper into an intelligent, context-aware email assistant.
