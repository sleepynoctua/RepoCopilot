# RepoCopilot: 代码库智能 RAG 助手

<div align="center">

[![Language](https://img.shields.io/badge/Lang-English-blue)](README.md)
[![Language](https://img.shields.io/badge/Lang-简体中文-red)](README.zh-CN.md)
[![Language](https://img.shields.io/badge/Lang-日本語-green)](README.ja.md)

**一个基于证据的、仓库无关的智能代码问答助手。**

![Status](https://img.shields.io/badge/Status-Completed-success) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)

</div>

---

**RepoCopilot** 是一个基于 **RAG（检索增强生成）** 技术的智能代码问答系统。它允许你与任何 GitHub 仓库进行对话，并提供精确到文件路径和行号的代码引用作为回答依据。

## ✨ 核心功能

1. **仓库无关与动态加载**:
    * **克隆即聊**: 只需在 UI 中粘贴 GitHub URL，系统自动克隆、索引并开始对话。
    * **一键切换**: 通过侧边栏在已下载的多个仓库之间无缝切换。

2. **混合检索引擎 (Hybrid Retrieval)**:
    * 结合 **BM25** (关键词匹配) 和 **Gemini Embeddings** (语义向量搜索) 的优势。
    * 使用 **RRF (Reciprocal Rank Fusion)** 算法融合排名，确保高精度的检索结果。

3. **智能 Agent 循环**:
    * **自我诊断**: AI 会自动评估检索到的证据是否足以回答你的问题。
    * **迭代搜索**: 如果证据不足（例如只看到函数调用没看到定义），Agent 会自动生成新的查询词来查找缺失的实现细节。

4. **证据优先的 UI 设计**:
    * 所有回答均包含可展开的 **"Evidence Sources"**（证据来源）。
    * 直接在聊天界面查看带有语法高亮的原始代码片段。

---

## 🌐 支持语言

### 🚀 深度分析 (基于 AST)

Python, C, C++, C#, Java, Go, Rust, JavaScript, TypeScript (包含 TSX), Lua。

### 📄 通用支持 (基于纯文本)

* **Web**: HTML, CSS, SCSS, LESS。

* **配置文件**: JSON, YAML, TOML, XML, .ini, .conf。
* **基础设施**: Dockerfile, .gitignore。
* **文档**: Markdown。

---

## 🚀 快速开始

### 1. 安装

```bash
# 创建并激活虚拟环境
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
# source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 (.env)

在根目录下创建 `.env` 文件 (可参考 `.env.example`):

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

### 3. 运行应用

你**不需要**手动运行任何索引脚本。Web UI 会全自动处理。

```bash
streamlit run app.py
```

### 4. 如何使用

1. **打开 UI**: 浏览器访问 `http://localhost:8501`。
2. **加载仓库**:
    * **分析本项目**: 在侧边栏选择 "RepoCopilot (Source)" 并点击 **"🔄 Switch to Selected"**。
    * **分析外部仓库**: 在 "Clone New" 区域输入 GitHub URL (例如 `https://github.com/psf/requests`) 并点击 **"⬇️ Clone & Load"**。
3. **等待索引**: 应用会自动克隆代码、清理旧数据并构建新的向量索引。
4. **开始对话**: 当侧边栏显示 **"✅ Ready!"** 时，即可开始提问。

---

## 🛠️ 技术栈

* **LLM**: DeepSeek-Chat (通过 OpenAI 兼容接口)。
* **Embeddings**: Google Gemini (`google-genai` SDK)。
* **向量数据库**: Qdrant (本地模式)。
* **搜索算法**: Rank-BM25。
* **代码解析**: Tree-sitter (基于 AST 的代码切分)。
* **前端框架**: Streamlit。

---

## 💡 常见问题 (Troubleshooting)

**Q: 出现 "Database Lock" 或 "Already accessed" 错误?**
A: 这通常是因为应用在持有文件锁时崩溃了。请在终端按 `Ctrl+C` 停止服务，然后重新运行即可释放锁。

**Q: 没有 API Key 怎么办?**
A:

* **Embeddings (搜索)**: 在 `.env` 中设置 `EMBEDDING_PROVIDER=mock`。系统将回退到仅使用关键词搜索 (BM25) 模式。
* **LLM/Chat (问答)**: 用于生成回答的 API Key (DeepSeek 或 OpenAI) 是 **必须** 提供的。如果没有 LLM 密钥，系统将无法正常工作（除非您自行修改代码以支持 Ollama 等本地模型）。

---

*最后更新: 2026-01-03*
