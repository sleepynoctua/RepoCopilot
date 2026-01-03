import os
import sys
import argparse

# Add src to python path so we can import repocopilot
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.repocopilot.retriever.engine import HybridRetriever


def main():
    parser = argparse.ArgumentParser(description="RepoCopilot Search CLI")
    parser.add_argument("query", type=str, help="The search query")
    parser.add_argument(
        "--top_k", type=int, default=5, help="Number of results to return"
    )
    parser.add_argument(
        "--use_real_embedding",
        action="store_true",
        help="Use real OpenAI embeddings (requires API key)",
    )

    args = parser.parse_args()

    print(f"🔍 Searching for: '{args.query}'...")

    # Initialize retriever
    # Note: Using mock embedding by default for testing
    retriever = HybridRetriever(
        bm25_path="data/bm25.pkl",
        qdrant_path="data/qdrant",
        use_mock_embedding=not args.use_real_embedding,
    )

    results = retriever.search(args.query, top_k=args.top_k)

    if not results:
        print("❌ No results found.")
        return

    print(f"\n✅ Found {len(results)} results:\n")
    for i, res in enumerate(results):
        chunk = res.chunk
        print("-" * 40)
        print(f"Result #{i + 1} | Score: {res.score:.4f} | Source: {res.source}")
        print(f"File: {chunk.file_path} (Lines {chunk.start_line}-{chunk.end_line})")
        print(f"Type: {chunk.type} | Name: {chunk.name or 'N/A'}")
        print("-" * 20)
        # Print first few lines of content
        content_lines = chunk.content.splitlines()
        preview = "\n".join(content_lines[:10])
        if len(content_lines) > 10:
            preview += "\n..."
        print(preview)
        print("-" * 40)
        print()


if __name__ == "__main__":
    main()
