# RepoCopilot: Agentic RAG for Codebases

<div align="center">

[![Language](https://img.shields.io/badge/Lang-English-blue)](README.md)
[![Language](https://img.shields.io/badge/Lang-简体中文-red)](README.zh-CN.md)
[![Language](https://img.shields.io/badge/Lang-日本語-green)](README.ja.md)

**An intelligent, repo-agnostic code assistant grounded in evidence.**

![Status](https://img.shields.io/badge/Status-Completed-success) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)

</div>

---

**RepoCopilot** is an intelligent code Q&A assistant based on **Retrieval-Augmented Generation (RAG)**. It allows you to chat with any GitHub repository, providing answers grounded in actual source code with precise file and line citations.

## ✨ Core Features

1. **Repo-Agnostic & Dynamic**:
    * **Clone & Chat**: Simply paste a GitHub URL in the UI to automatically clone, index, and start chatting with a new repository.
    * **One-Click Switching**: Seamlessly switch between downloaded repositories via the sidebar.

2. **Hybrid Retrieval Engine**:
    * Combines **BM25** (keyword matching) and **Gemini Embeddings** (semantic search).
    * Uses **RRF (Reciprocal Rank Fusion)** to merge results for high precision.

3. **Agentic RAG Loop**:
    * **Self-Diagnosis**: The AI evaluates if the retrieved code is sufficient to answer your question.
    * **Iterative Search**: Automatically refines search queries to find missing implementation details (e.g., finding a class definition after seeing its usage).

4. **Evidence-First UI**:
    * Answers include expandable **"Evidence Sources"**.
    * View original source code snippets with syntax highlighting directly in the chat.

---

## 🌐 Supported Languages

### 🚀 Deep Analysis (AST-based)

Python, C, C++, C#, Java, Go, Rust, JavaScript, TypeScript (incl. TSX), Lua.

### 📄 General Support (Text-based)

* **Web**: HTML, CSS, SCSS, LESS.

* **Configs**: JSON, YAML, TOML, XML, .ini, .conf.
* **Infrastructure**: Dockerfile, .gitignore.
* **Docs**: Markdown.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the root directory (copy from `.env.example`):

```env
# Chat LLM (DeepSeek or OpenAI Recommended)
OPENAI_API_KEY=your_key_here
OPENAI_API_BASE=https://api.deepseek.com
MODEL_NAME=deepseek-chat

# Embeddings (Google Gemini Recommended)
GOOGLE_API_KEY=your_google_key_here
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=models/embedding-001

# QDRANT
QDRANT_PATH=./data/qdrant
```

### 3. Run the Application

You **do not** need to run any manual indexing scripts. The Web UI handles everything.

```bash
streamlit run app.py
```

### 4. How to Use

1. **Open the UI**: Go to `http://localhost:8501`.
2. **Load a Repository**:
    * **Analyze this project**: Select "RepoCopilot (Source)" in the sidebar and click **"🔄 Switch to Selected"**.
    * **Analyze external repo**: Enter a GitHub URL (e.g., `https://github.com/psf/requests`) in the "Clone New" section and click **"⬇️ Clone & Load"**.
3. **Wait for Indexing**: The app will automatically clone the code, clear old data, and build the new vector index.
4. **Chat**: Once the sidebar says **"✅ Ready!"**, you can start asking questions.

---

## 🛠️ Technical Stack

* **LLM**: DeepSeek-Chat (via OpenAI-compatible API).
* **Embeddings**: Google Gemini (`google-genai` SDK).
* **Vector DB**: Qdrant (Local Mode).
* **Search**: Rank-BM25.
* **Parsing**: Tree-sitter (AST-based chunking).
* **Frontend**: Streamlit.

---

## 💡 Troubleshooting

**Q: "Database Lock" or "Already accessed" error?**
A: This happens if the app crashes while holding a file lock. Restart the Streamlit server (`Ctrl+C` then run again) to release it.

**Q: Running without API Keys?**
A:

* **Embeddings**: Set `EMBEDDING_PROVIDER=mock` in `.env`. The system will fall back to keyword search (BM25) only.
* **LLM/Chat**: An API key (DeepSeek or OpenAI) is **mandatory** to generate answers. The system cannot function without an LLM key unless you modify the code to support a local provider like Ollama.

---

*Last Updated: 2026-01-03*
