# Site Chat Extension

Site Chat is a Chrome extension that converts any open webpage into a context-aware AI chat experience.

The extension extracts page text, prepares a retrieval pipeline on the backend, and answers follow-up questions with memory continuity per browser tab. It also supports a Research mode that can force web-augmented responses when needed.

## Project Highlights

- Tab-scoped conversational memory for stable multi-turn chat
- Dual response modes:
	- Normal response: primary page-context flow
	- Research response: always runs web-augmented flow
- Context relevance scoring returned as structured JSON
- Source URL payload returned separately for frontend rendering
- Optional web fallback using Tavily when context relevance is low
- Structured output formatting in UI:
	- paragraphs
	- lists
	- code blocks
	- clickable sources

## Product Flow

1. Extension loads and extracts text from active tab.
2. Backend prepares a retrieval chain for that tab.
3. User asks a question from popup chat.
4. Backend computes context relevance score.
5. Backend selects route:
	 - Normal mode + high relevance: answer from page chain.
	 - Normal mode + low relevance: web-augmented fallback.
	 - Research mode: web-augmented path every time.
6. Frontend renders answer, relevance chip, and source links.

## Architecture

Frontend
- Chrome Extension (Manifest v3)
- Popup UI: modern chat layout with mode switch, metadata, and source links

Backend
- Flask API
- LangChain conversational retrieval chains
- Groq chat model
- Optional Tavily web search integration

Prompt System
- Prompt modules under backend/PROMPTS
- Separate prompts for:
	- standard QA
	- context rating
	- long descriptive research reports

## Folder Structure

```text
aibot_extension/
	backend/
		app.py
		context_rating_service.py
		web_search_service.py
		PROMPTS/
			system_prompt.py
			context_rating_prompt.py
			research_report_prompt.py
	frontend/
		manifest.json
		service_worker.js
		intro.html
		intro.css
		loader.html
		loading.js
		popup.html
		popup.css
		popup1.js
```

## API Endpoints

POST /prepareIt
- input: extracted page text, tab id
- output: chain preparation status

POST /askIt
- input:
	- question
	- tab id
	- current page url
	- response mode
- output:
	- answer
	- context_rating
	- used_web_fallback
	- web_sources
	- answer_urls
	- response_mode

## Response Payload Design

answer_urls is intentionally separate from answer text for clean frontend rendering.

Example:

```json
{
	"answer": "...",
	"context_rating": {
		"relevance_score": 78,
		"relevance_label": "high",
		"reason": "Most key terms were present in page context."
	},
	"used_web_fallback": false,
	"web_sources": [],
	"answer_urls": {
		"count": 1,
		"items": [
			{
				"title": "Current page",
				"url": "https://example.com",
				"source_type": "page_context"
			}
		]
	},
	"response_mode": "normal"
}
```

## UI Motion and Interaction System

The extension UI is lightweight but intentionally animated:

- Intro card entrance animation
- Loader transition while context is prepared
- Message enter animation in chat stream
- Animated typing/processing indicators
- Styled metadata chips for relevance
- Source links rendered directly under each answer

## Setup

### 1) Python Environment

Use your preferred virtual environment and install dependencies:

```bash
cd backend
pip install flask python-dotenv langchain langchain-groq langchain-community sentence-transformers faiss-cpu tavily-python nltk torch pypdf python-docx pypdfium2 rapidocr-onnxruntime pillow
```

Notes:
- `pypdf` and `python-docx` support PDF/DOCX upload parsing.
- `pypdfium2` + `rapidocr-onnxruntime` provide OCR fallback when PDFs have no usable text layer.

### 2) Environment Variables

Create or update backend/.env:

```env
GROQ_API_KEY="your_groq_key"
GROQ_MODEL="llama-3.1-8b-instant"
TAVILY_API_KEY="your_tavily_key_optional"
```

Notes:
- GROQ_API_KEY is required.
- TAVILY_API_KEY is optional but required for web fallback search.

### 3) Run Backend

```bash
cd backend
python app.py
```

### 4) Load Extension

1. Open chrome://extensions
2. Enable Developer mode
3. Click Load unpacked
4. Select frontend folder

## Modes

Normal response
- Uses page-context chain by default
- Falls back to web context when relevance is low

Research response
- Forces web-augmented flow
- Uses report-style prompt structure for more descriptive outputs

## Current Status

Implemented
- Tab-scoped chains and shared memory continuity
- Context relevance scoring
- URL metadata contract for frontend links
- Web fallback service integration
- Research report prompt module

Planned enhancements
- Collapsible source blocks in chat
- Optional citation numbering in answer body
- Persistent conversation export per tab
