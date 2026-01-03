# RepoCopilot: コードベースのためのエージェント型RAG

<div align="center">

[![Language](https://img.shields.io/badge/Lang-English-blue)](README.md)
[![Language](https://img.shields.io/badge/Lang-简体中文-red)](README.zh-CN.md)
[![Language](https://img.shields.io/badge/Lang-日本語-green)](README.ja.md)

**根拠に基づいた、リポジトリに依存しないインテリジェントなコードアシスタント。**

![Status](https://img.shields.io/badge/Status-Completed-success) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)

</div>

---

**RepoCopilot** は、**検索拡張生成 (RAG)** に基づくインテリジェントなコードQ&Aアシスタントです。GitHub上のあらゆるリポジトリと対話することができ、実際のソースコードに基づいた正確なファイルパスと行番号の引用を提供します。

## ✨ 主な機能

1. **リポジトリ非依存 & 動的読み込み**:
    * **Clone & Chat**: UIにGitHubのURLを貼り付けるだけで、自動的にクローン、インデックス作成を行い、新しいリポジトリとの対話を開始できます。
    * **ワンクリック切り替え**: サイドバーから、ダウンロード済みのリポジトリ間をシームレスに切り替えることができます。

2. **ハイブリッド検索エンジン**:
    * **BM25** (キーワードマッチング) と **Gemini Embeddings** (意味検索) の強みを組み合わせています。
    * **RRF (Reciprocal Rank Fusion)** アルゴリズムを使用して結果を統合し、高い精度を実現します。

3. **エージェント型 RAG ループ**:
    * **自己診断**: AIは、検索されたコードが質問に答えるのに十分かどうかを自動的に評価します。
    * **反復検索**: 証拠が不足している場合（例：関数呼び出しは見つかったが定義が見つからない場合）、エージェントは自動的に新しい検索クエリを生成して、不足している実装の詳細を探します。

4. **証拠重視のUI**:
    * 回答には展開可能な **"Evidence Sources"**（証拠ソース）が含まれます。
    * シンタックスハイライト付きの元のソースコードスニペットをチャット内で直接確認できます。

---

## 🚀 クイックスタート

### 1. インストール

```bash
# 仮想環境の作成と有効化
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
# source .venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. 設定 (.env)

ルートディレクトリに `.env` ファイルを作成します (`.env.example` をコピー):

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

### 3. アプリケーションの実行

手動でインデックス作成スクリプトを実行する必要はありません。Web UIがすべて処理します。

```bash
streamlit run app.py
```

### 4. 使い方

1. **UIを開く**: ブラウザで `http://localhost:8501` にアクセスします。
2. **リポジトリの読み込み**:
    * **このプロジェクトを分析**: サイドバーで "RepoCopilot (Source)" を選択し、**"🔄 Switch to Selected"** をクリックします。
    * **外部リポジトリを分析**: "Clone New" セクションにGitHub URL (例: `https://github.com/psf/requests`) を入力し、**"⬇️ Clone & Load"** をクリックします。
3. **インデックス作成を待機**: アプリは自動的にコードをクローンし、古いデータをクリアして、新しいベクトルインデックスを構築します。
4. **チャット開始**: サイドバーに **"✅ Ready!"** と表示されたら、質問を開始できます。

---

## 🛠️ 技術スタック

* **LLM**: DeepSeek-Chat (OpenAI互換API経由)。
* **Embeddings**: Google Gemini (`google-genai` SDK)。
* **Vector DB**: Qdrant (ローカルモード)。
* **Search**: Rank-BM25。
* **Parsing**: Tree-sitter (ASTベースのチャンキング)。
* **Frontend**: Streamlit。

---

## 💡 トラブルシューティング

**Q: "Database Lock" または "Already accessed" エラーが発生しますか？**
A: これは、アプリがファイルロックを保持したままクラッシュした場合に発生します。Streamlitサーバーを再起動（`Ctrl+C` してから再実行）してロックを解除してください。

**Q: APIキーなしで実行できますか？**
A:

* **Embeddings (検索)**: `.env` で `EMBEDDING_PROVIDER=mock` を設定してください。キーワード検索 (BM25) のみにフォールバックします。
* **LLM/Chat (回答)**: 回答を生成するための API キー (DeepSeek または OpenAI) は **必須** です。LLM キーがない場合、システムは動作しません（Ollama などのローカルモデルをサポートするようにコードを修正しない限り）。

---

*最終更新: 2026-01-03*
