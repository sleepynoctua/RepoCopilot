from typing import List, Dict, Any
from ..retriever.engine import HybridRetriever
from ..common.schema import SearchResult
from .llm import LLMClient
from .prompt import SYSTEM_PROMPT


class RepoCopilotAgent:
    def __init__(
        self, retriever: HybridRetriever, llm: LLMClient, max_retries: int = 2
    ):
        self.retriever = retriever
        self.llm = llm
        self.max_retries = max_retries

    def answer(self, query: str) -> Dict[str, Any]:
        """
        Agentic RAG pipeline: Retrieve -> Evaluate -> (Optional Re-retrieve) -> Generate
        Returns:
            Dict: {
                "content": str,   # The LLM's answer
                "sources": List[SearchResult] # The code chunks used
            }
        """
        all_results: List[SearchResult] = []
        current_query = query

        for attempt in range(self.max_retries + 1):
            print(
                f"🕵️ Attempt {attempt + 1}: Retrieving context for '{current_query}'..."
            )
            # Increase top_k to 10 to capture more definition chunks, not just usage
            new_results = self.retriever.search(current_query, top_k=10)

            # Log retrieved files for debugging
            found_files = {res.chunk.file_path for res in new_results}
            print(
                f"📄 Found {len(new_results)} chunks across {len(found_files)} files: {', '.join(list(found_files)[:3])}..."
            )

            # Merge results and avoid duplicates
            seen_ids = {res.chunk.id for res in all_results}
            for res in new_results:
                if res.chunk.id not in seen_ids:
                    all_results.append(res)
                    seen_ids.add(res.chunk.id)

            if not all_results:
                return {
                    "content": "I couldn't find any relevant code in the repository.",
                    "sources": [],
                }

            # Build current context string
            context_str = self._build_context(all_results)

            # Check if we have enough info
            if attempt < self.max_retries:
                print("🤔 Evaluating evidence sufficiency...")
                eval_result = self.llm.evaluate_sufficiency(query, context_str)

                if eval_result.get("sufficient"):
                    print("✅ Evidence is sufficient.")
                    break
                else:
                    missing = eval_result.get("missing_info", "Unknown")
                    current_query = eval_result.get("suggested_query", query)
                    print(f"⚠️ Insufficient evidence. Missing: {missing}")
                    print(f"🔄 Retrying with optimized query: '{current_query}'")
            else:
                print(
                    "⏳ Reached max retries. Generating answer with available context."
                )

        # Final Answer Generation
        print("🤖 Generating final answer...")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {query}\n\n{context_str}"},
        ]

        answer_text = self.llm.chat(messages)

        return {"content": answer_text, "sources": all_results}

    def close(self):
        """Release retriever resources."""
        if self.retriever:
            self.retriever.close()

    def _build_context(self, results: List[SearchResult]) -> str:
        """
        Format retrieved chunks into a single string for the LLM.
        """
        context_parts = ["--- Code Context ---"]

        for i, res in enumerate(results):
            chunk = res.chunk
            part = (
                f"[Chunk {i + 1}]\n"
                f"File: {chunk.file_path} (Lines {chunk.start_line}-{chunk.end_line})\n"
                f"Type: {chunk.type}\n"
                f"Content:\n{chunk.content}\n"
            )
            context_parts.append(part)

        context_parts.append("-------------------")
        return "\n\n".join(context_parts)
