from typing import List
from qdrant_client import QdrantClient
from ..common.schema import CodeChunk, SearchResult
from ..indexer.embeddings import EmbeddingService, get_embedding_service


class VectorRetriever:
    def __init__(
        self,
        storage_path: str = "data/qdrant",
        collection_name: str = "repo_code",
        embedding_service: EmbeddingService = None,
        use_mock_embedding: bool = True,
    ):
        self.client = QdrantClient(path=storage_path)
        self.collection_name = collection_name
        self.embedding_service = embedding_service or get_embedding_service(
            use_mock=use_mock_embedding
        )

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        # 1. Generate embedding for the query
        try:
            query_vector = self.embedding_service.get_embeddings([query])[0]
        except Exception as e:
            print(f"⚠️ Embedding generation failed: {e}")
            return []

        # 2. Search in Qdrant using query_points (modern API)
        try:
            results = self.client.query_points(
                collection_name=self.collection_name, query=query_vector, limit=top_k
            ).points
        except Exception as e:
            # Gracefully handle missing collection or connection errors
            print(f"⚠️ Vector search failed: {e}")
            return []

        # 3. Convert to SearchResult
        search_results = []
        for res in results:
            chunk = CodeChunk(id=str(res.id), **res.payload)
            search_results.append(
                SearchResult(chunk=chunk, score=res.score, source="vector")
            )

        return search_results

    def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
