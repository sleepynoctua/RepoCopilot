from typing import List, Dict
from .bm25 import BM25Retriever
from .vector import VectorRetriever
from ..common.schema import SearchResult, CodeChunk


class HybridRetriever:
    def __init__(
        self,
        bm25_path: str = "data/bm25.pkl",
        qdrant_path: str = "data/qdrant",
        use_mock_embedding: bool = True,
    ):
        # Initialize BM25
        self.bm25 = BM25Retriever()
        try:
            self.bm25.load(bm25_path)
        except FileNotFoundError:
            print(f"⚠️ BM25 index not found at {bm25_path}. BM25 search will fail.")

        # Initialize Vector Store
        self.vector = VectorRetriever(
            storage_path=qdrant_path, use_mock_embedding=use_mock_embedding
        )

    def search(self, query: str, top_k: int = 5, k: int = 60) -> List[SearchResult]:
        """
        Perform hybrid search using RRF fusion.

        Args:
            query: The search query string.
            top_k: Number of final results to return.
            k: RRF constant (usually 60).
        """
        # 1. Parallel Retrieval (Sequential for now)
        try:
            # BM25 returns raw CodeChunks, wrap them in SearchResult
            bm25_chunks = self.bm25.search(query, top_k=top_k * 2)
            bm25_results = [
                SearchResult(chunk=c, score=0.0, source="bm25") for c in bm25_chunks
            ]
        except Exception as e:
            print(f"⚠️ BM25 search failed: {e}")
            bm25_results = []

        try:
            vector_results = self.vector.search(query, top_k=top_k * 2)
        except Exception as e:
            print(f"⚠️ Vector search failed: {e}")
            vector_results = []

        # 2. RRF Fusion
        return self._rrf_fusion(bm25_results, vector_results, k=k, limit=top_k)

    def _rrf_fusion(
        self,
        list1: List[SearchResult],
        list2: List[SearchResult],
        k: int = 60,
        limit: int = 5,
    ) -> List[SearchResult]:
        """
        Reciprocal Rank Fusion.
        Score = 1 / (k + rank_in_list1) + 1 / (k + rank_in_list2)
        """
        fused_scores: Dict[str, float] = {}
        chunk_map: Dict[str, CodeChunk] = {}

        # Helper to process a result list
        def process_list(results: List[SearchResult]):
            for rank, result in enumerate(results):
                chunk_id = result.chunk.id
                if chunk_id not in chunk_map:
                    chunk_map[chunk_id] = result.chunk
                    fused_scores[chunk_id] = 0.0

                fused_scores[chunk_id] += 1.0 / (k + rank + 1)

        process_list(list1)
        process_list(list2)

        # Sort by fused score
        sorted_ids = sorted(
            fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True
        )

        # Format output
        final_results = []
        for chunk_id in sorted_ids[:limit]:
            final_results.append(
                SearchResult(
                    chunk=chunk_map[chunk_id],
                    score=fused_scores[chunk_id],
                    source="hybrid",
                )
            )

        return final_results

    def close(self):
        """Release resources."""
        if self.vector:
            self.vector.close()
