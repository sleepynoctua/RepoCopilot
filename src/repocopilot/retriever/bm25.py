import json
import os
from typing import List
from rank_bm25 import BM25Okapi
import re
from ..common.schema import CodeChunk


class BM25Retriever:
    def __init__(self):
        self.bm25 = None
        self.chunks = []

    def index(self, chunks: List[CodeChunk]):
        self.chunks = chunks
        tokenized_corpus = [self._tokenize(chunk.content) for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k: int = 5) -> List[CodeChunk]:
        if not self.bm25:
            # Try to lazy load or raise error
            raise ValueError("Index not built! Call load() first.")

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :top_k
        ]

        return [self.chunks[i] for i in top_indices]

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\w+", text)]

    def save(self, path: str):
        # We NO LONGER pickle the BM25 object. We only save the data as JSON.
        # This completely eliminates pickle errors.
        json_path = path.replace(".pkl", ".json")

        # Serialize chunks to primitive dicts
        chunks_data = [c.model_dump(mode="json") for c in self.chunks]

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

    def load(self, path: str):
        # Load from JSON and REBUILD the index in-memory (it's fast)
        json_path = path.replace(".pkl", ".json")

        if not os.path.exists(json_path):
            # Fallback check for old pkl just in case, but prioritize JSON
            if os.path.exists(path):
                print(
                    f"⚠️ Legacy pickle found at {path}, but JSON expected. Please rebuild index."
                )
            raise FileNotFoundError(f"Index data not found at {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)

        # Reconstruct objects
        self.chunks = [CodeChunk(**c) for c in chunks_data]

        # Rebuild BM25 on the fly
        self.index(self.chunks)
