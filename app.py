import streamlit as st
import os
import gc
import shutil
import git
from dotenv import load_dotenv

# Import our core components
from src.repocopilot.retriever.engine import HybridRetriever
from src.repocopilot.agent.llm import LLMClient
from src.repocopilot.agent.core import RepoCopilotAgent
from src.repocopilot.indexer.build import IndexBuilder

# 1. LOAD DOTENV FIRST
load_dotenv(override=True)

# 2. Page Config
st.set_page_config(page_title="RepoCopilot", page_icon="🤖", layout="wide")

# --- CSS HACK TO HIDE INPUT INSTRUCTIONS ---
st.markdown(
    """
<style>
    div[data-testid="InputInstructions"] {
        display: none !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- PERSISTENCE HELPERS ---
STATE_FILE = ".repo_state"


def save_repo_state(path, name):
    """Saves the current repo info to disk."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(f"{path}|{name}")
    except Exception as e:
        print(f"Failed to save state: {e}")


def load_repo_state():
    """Loads the last active repo info from disk."""
    default_path = "."
    default_name = "RepoCopilot (Source)"
    if not os.path.exists(STATE_FILE):
        return default_path, default_name
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if "|" in content:
                path, name = content.split("|", 1)
                if os.path.exists(path):
                    return path, name
    except Exception:
        pass
    return default_path, default_name


# 3. Helper Functions
def get_local_repos():
    if not os.path.exists("repos"):
        os.makedirs("repos")
    return [d for d in os.listdir("repos") if os.path.isdir(os.path.join("repos", d))]


def clone_repo(url):
    repo_name = url.split("/")[-1].replace(".git", "")
    target_path = os.path.join("repos", repo_name)
    if os.path.exists(target_path):
        return (
            target_path,
            f"Repository '{repo_name}' already exists. Using cached copy.",
        )
    try:
        git.Repo.clone_from(url, target_path)
        return target_path, f"Successfully cloned '{repo_name}'."
    except Exception as e:
        raise Exception(f"Failed to clone repository: {e}")


def rebuild_index(target_path):
    if os.path.exists("data/qdrant"):
        shutil.rmtree("data/qdrant", ignore_errors=True)

    # Clean up both potential files
    if os.path.exists("data/bm25.pkl"):
        os.remove("data/bm25.pkl")
    if os.path.exists("data/bm25.json"):
        os.remove("data/bm25.json")

    provider = os.getenv("EMBEDDING_PROVIDER", "mock")
    # Rule for RepoCopilot self-indexing
    ignore_list = None
    if target_path == "." or target_path == os.getcwd():
        ignore_list = ["repos", "data", ".venv", "__pycache__", ".git"]

    builder = IndexBuilder(
        repo_path=target_path,
        use_mock_embedding=(provider == "mock"),
        ignore_dirs=ignore_list,
    )
    builder.build()

    # Validation: Check for JSON file
    if not os.path.exists("data/bm25.json"):
        raise Exception(
            "Indexing failed: 'data/bm25.json' was not created. Found 0 files?"
        )


@st.cache_resource
def init_agent(repo_path_hash):
    gc.collect()
    provider = os.getenv("EMBEDDING_PROVIDER", "mock")
    use_mock = provider == "mock"
    retriever = HybridRetriever(
        bm25_path="data/bm25.pkl",
        qdrant_path="data/qdrant",
        use_mock_embedding=use_mock,
    )
    llm = LLMClient()
    return RepoCopilotAgent(retriever, llm)


def perform_switch(target_path, display_name, status_container):
    """Executes the sequence to switch the active repository."""
    try:
        # 1. Close existing agent
        current_repo = st.session_state.get("current_repo_path", ".")
        try:
            old_agent = init_agent(current_repo)
            if old_agent:
                old_agent.close()
        except Exception:
            pass

        # 2. Clear Cache
        init_agent.clear()

        # 3. Rebuild Index
        status_container.write("🧠 Rebuilding Index...")
        rebuild_index(target_path)

        # 4. Update State
        st.session_state.current_repo_path = target_path
        st.session_state.selected_repo_name = display_name
        st.session_state.messages = []

        # 5. Persist
        save_repo_state(target_path, display_name)

        status_container.update(label="✅ Ready!", state="complete", expanded=False)
        st.rerun()
    except Exception as e:
        status_container.update(label="❌ Error", state="error")
        st.sidebar.error(str(e))


# 4. Session State Initialization
if "current_repo_path" not in st.session_state:
    saved_path, saved_name = load_repo_state()
    st.session_state.current_repo_path = saved_path
    st.session_state.selected_repo_name = saved_name

# 5. Sidebar Logic
with st.sidebar:
    st.title("📂 Repository")
    st.subheader("Switch Existing")
    local_repos = get_local_repos()
    options = ["RepoCopilot (Source)"] + local_repos

    curr_idx = 0
    if st.session_state.selected_repo_name in options:
        curr_idx = options.index(st.session_state.selected_repo_name)

    selected_repo = st.selectbox(
        "Select Repository:", options, index=curr_idx, key="sb_repo_select"
    )

    if st.button("🔄 Switch to Selected", use_container_width=True):
        status_box = st.status("🚀 Switching...", expanded=True)
        if selected_repo == "RepoCopilot (Source)":
            perform_switch(".", "RepoCopilot (Source)", status_box)
        else:
            perform_switch(
                os.path.join("repos", selected_repo), selected_repo, status_box
            )

    st.divider()
    st.subheader("Clone New")
    with st.form("clone_form", clear_on_submit=False):
        repo_url = st.text_input(
            "GitHub URL:", placeholder="https://github.com/user/repo"
        )
        clone_btn = st.form_submit_button("⬇️ Clone & Load", use_container_width=True)

    if clone_btn:
        if not repo_url:
            st.error("Enter a URL first.")
        else:
            status_box = st.status("🚀 Cloning...", expanded=True)
            try:
                status_box.write("⬇️ Git Cloning...")
                path, msg = clone_repo(repo_url)
                status_box.write(msg)
                perform_switch(path, os.path.basename(path), status_box)
            except Exception as e:
                status_box.update(label="❌ Clone Failed", state="error")
                st.error(str(e))

    st.divider()
    st.info(f"Active: **{st.session_state.selected_repo_name}**")
    st.caption(f"🤖 Model: {os.getenv('MODEL_NAME', '⚠️ NOT SET')}")
    st.caption(f"🧠 Embed: {os.getenv('EMBEDDING_PROVIDER', 'mock')}")

# 6. Main Agent Initialization
try:
    agent = init_agent(st.session_state.current_repo_path)
except Exception as e:
    st.error(f"Configuration Error: {e}")
    agent = None

# 7. Main Chat Interface
st.title("🤖 RepoCopilot")

if not agent:
    st.warning("System not ready. Please select a repository.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Hello! I'm ready to discuss **{st.session_state.selected_repo_name}**.",
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 View Evidence Sources"):
                for i, res in enumerate(message["sources"]):
                    chunk = res.chunk
                    st.markdown(
                        f"**{chunk.file_path} (Lines {chunk.start_line}-{chunk.end_line})**"
                    )
                    st.code(chunk.content, language="python")

if prompt := st.chat_input("Ask about the code..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🕵️ Analyzing...", expanded=True) as status:
            try:
                result = agent.answer(prompt)
                response_text = result["content"]
                sources = result["sources"]
                status.update(label="✅ Done!", state="complete", expanded=False)
            except Exception as e:
                status.update(label="❌ Error", state="error")
                response_text = f"Error: {str(e)}"
                sources = []

        st.markdown(response_text)

        if sources:
            with st.expander("📚 View Evidence Sources"):
                for i, res in enumerate(sources):
                    chunk = res.chunk
                    st.markdown(
                        f"**{chunk.file_path} (Lines {chunk.start_line}-{chunk.end_line})**"
                    )
                    st.code(chunk.content, language="python")

        st.session_state.messages.append(
            {"role": "assistant", "content": response_text, "sources": sources}
        )
        st.rerun()
