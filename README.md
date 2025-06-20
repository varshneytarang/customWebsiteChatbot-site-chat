# Web QA Chatbot

A Chrome extension that turns any webpage into an interactive chatbot. It extracts content from the active tab and allows users to ask questions about it via a Python-based LLM backend.

---

## 🔍 Features

- Extracts content from the active browser tab  
- Sends it to a backend running a Python LLM or API call  
- Receives and displays intelligent answers in the popup  
- Handles dynamic or login-protected sites using Playwright  
- Built as a lightweight, fast Chrome extension

---

## 🛠️ Tech Stack

| Part             | Tech                                      |
|------------------|-------------------------------------------|
| **Frontend**      | HTML, CSS, JavaScript (Vanilla)            |
| **Extension**     | Chrome Extension (Manifest v3)             |
| **Backend**       | Node.js + Python (Bridge)                  |
| **LLM Engine**    | Python script using Gemini or local LLM    |
| **Scraping Tool** | Playwright with persistent sessions        |

---

## 📁 Folder Structure

```
AIBOT_EXTENSION/
├── backend/
│   ├── answerGeneration.py       # LLM answer generation
│   ├── scrapeTheLink.py          # Web scraping with Playwright
│   ├── index.js                  # Backend API server
│   ├── package.json              # Node.js dependencies
├── frontend/
│   ├── manifest.json             # Chrome extension config
│   ├── popup.html                # Extension UI
│   ├── popup.js                  # JS to handle UI logic
│   └── popup.css                 # Styling
```

---

## 🚀 How It Works

1. User clicks the extension → popup opens  
2. `popup.js` sends the active tab URL/content to `backend/index.js`  
3. Backend triggers Python script (`scrapeTheLink.py`) to extract data  
4. That data is passed to `answerGeneration.py` using an LLM  
5. The answer is returned to the popup and shown to the user

---

## 🧪 Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/web-qa-chatbot.git
cd web-qa-chatbot
```

---

### 2. Create and Activate Conda Environment

```bash
conda create -n chatbot_env python=3.10
conda activate chatbot_env
```

---

### 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
playwright install
```

---

### 4. Setup and Run Backend (Node.js + Python Bridge)

```bash
cd backend
npm install
node index.js
```

---

### 5. Load the Chrome Extension

1. Open `chrome://extensions/`
2. Enable **Developer Mode**
3. Click **Load unpacked**
4. Select the `frontend/` folder

---

## 🧠 Notes

- Use `playwright_profile/` to persist login sessions
- Backend must be running for the chatbot to work
- Can be integrated with any LLM: OpenAI, Gemini, Llama, Falcon, Mistral (via HuggingFace/local)

---

