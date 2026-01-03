import pickle
from typing import List
from rank_bm25 import BM25Okapi
import re
from ..common.schema import CodeChunk


class BM25Retriever:
    def __init__(self):
        self.bm25 = None
        self.chunks = []  # We need to store chunks to return them, BM25 only stores stats

    def index(self, chunks: List[CodeChunk]):
        self.chunks = chunks
        tokenized_corpus = [self._tokenize(chunk.content) for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k: int = 5) -> List[CodeChunk]:
        if not self.bm25:
            raise ValueError("Index not built!")

        tokenized_query = self._tokenize(query)
        # Get top_n raw scores
        scores = self.bm25.get_scores(tokenized_query)

        # Sort and get top_k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :top_k
        ]

        return [self.chunks[i] for i in top_indices]

    def _tokenize(self, text: str) -> List[str]:
        # Simple regex tokenizer for code
        # Splits on whitespace and punctuation, keeps words
        return [w.lower() for w in re.findall(r"\w+", text)]

    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)

    def load(self, path: str):
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.chunks = data["chunks"]


if __name__ == "__main__":
    # Test
    c1 = CodeChunk(
        id="1",
        content="def hello(): print('world')",
        file_path="a.py",
        start_line=1,
        end_line=1,
        type="function",
    )
    c2 = CodeChunk(
        id="2",
        content="class World: pass",
        file_path="b.py",
        start_line=1,
        end_line=1,
        type="class",
    )

    retriever = BM25Retriever()
    retriever.index([c1, c2])
    results = retriever.search("hello function")
    print(f"Top result: {results[0].content}")
