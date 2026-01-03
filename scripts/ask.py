import os
import sys
import argparse
from dotenv import load_dotenv

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.repocopilot.retriever.engine import HybridRetriever
from src.repocopilot.agent.llm import LLMClient
from src.repocopilot.agent.core import RepoCopilotAgent


def main():
    # Load environment variables from .env
    load_dotenv()

    parser = argparse.ArgumentParser(description="RepoCopilot Q&A CLI")
    parser.add_argument("question", type=str, help="The question about the codebase")
    parser.add_argument(
        "--use_real_embedding",
        action="store_true",
        help="Use real embeddings for retrieval",
    )

    args = parser.parse_args()

    # 1. Initialize Components
    # Using mock embedding if specified, otherwise real ones
    retriever = HybridRetriever(
        bm25_path="data/bm25.pkl",
        qdrant_path="data/qdrant",
        use_mock_embedding=not args.use_real_embedding,
    )

    llm = LLMClient()  # Will use values from .env automatically
    agent = RepoCopilotAgent(retriever, llm)

    # 2. Execute Q&A
    print(f"\n❓ Question: {args.question}")
    print("-" * 50)

    try:
        answer = agent.answer(args.question)
        print(f"\n💡 Answer:\n{answer}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if "api_key" in str(e).lower():
            print("Hint: Please make sure OPENAI_API_KEY is set in your .env file.")


if __name__ == "__main__":
    main()
