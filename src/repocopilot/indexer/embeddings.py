from typing import List
import os
import time
import numpy as np
from openai import OpenAI


class EmbeddingService:
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, model: str = None):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("EMBEDDING_API_BASE") or os.getenv("OPENAI_API_BASE"),
        )
        self.model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        texts = [t.replace("\n", " ") for t in texts]
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [data.embedding for data in response.data]


class GeminiEmbeddingService(EmbeddingService):
    def __init__(self, model: str = None):
        from google import genai

        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set in environment variables.")

        # New SDK Client
        self.client = genai.Client(api_key=self.api_key)
        self.model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        # Default to 1M TPM if not set
        self.tpm_limit = int(os.getenv("GEMINI_TPM_LIMIT", 1000000))

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        # Internal batching for the API (Gemini allows max 100 per request)
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Estimate tokens to stay under TPM limit (Approx: 1 token ~ 4 chars)
            batch_tokens = sum(len(t) for t in batch) // 4

            # Wait time (seconds) to respect the TPM limit
            # (batch_tokens / tpm_limit) * 60 seconds
            wait_time = (
                (batch_tokens / self.tpm_limit) * 60 if self.tpm_limit > 0 else 0
            )

            try:
                # Synchronous call
                result = self.client.models.embed_content(
                    model=self.model, contents=batch
                )

                # Extract results
                all_embeddings.extend([e.values for e in result.embeddings])

                # Simple pacing between batches to stay under TPM
                if i + batch_size < len(texts) or wait_time > 0.1:
                    time.sleep(wait_time)

            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"⚠️ Gemini Rate Limit Hit (TPM={self.tpm_limit}). Error: {e}")
                else:
                    print(f"Gemini Embedding Error: {e}")
                raise e

        return all_embeddings


class MockEmbeddingService(EmbeddingService):
    def __init__(self, dim: int = 1536):
        self.dim = dim

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        rng = np.random.default_rng()
        embeddings = rng.random((len(texts), self.dim))
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return (embeddings / norms).tolist()


def get_embedding_service(
    use_mock: bool = False, provider: str = None
) -> EmbeddingService:
    effective_provider = provider or os.getenv("EMBEDDING_PROVIDER", "mock").lower()

    if use_mock or effective_provider == "mock":
        # Gemini 004 is 768, OpenAI is 1536
        return MockEmbeddingService(dim=768 if effective_provider == "gemini" else 1536)

    if effective_provider == "gemini":
        return GeminiEmbeddingService()

    return OpenAIEmbeddingService()
