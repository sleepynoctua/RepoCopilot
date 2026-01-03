from typing import List
import os
import numpy as np
from openai import OpenAI

class EmbeddingService:
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self, model: str = None):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("EMBEDDING_API_BASE") or os.getenv("OPENAI_API_BASE")
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

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        # New SDK Method: models.embed_content
        # Note: 'text-embedding-004' usually returns 768 dimensions
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=texts
            )
            # The result object structure depends on batch size, 
            # usually result.embeddings is a list of objects with .values
            return [e.values for e in result.embeddings]
        except Exception as e:
            print(f"Gemini Embedding Error: {e}")
            raise e

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
    use_mock: bool = False,
    provider: str = None
) -> EmbeddingService:
    effective_provider = provider or os.getenv("EMBEDDING_PROVIDER", "mock").lower()
    
    if use_mock or effective_provider == "mock":
        # Gemini 004 is 768, OpenAI is 1536
        return MockEmbeddingService(dim=768 if effective_provider == "gemini" else 1536)
    
    if effective_provider == "gemini":
        return GeminiEmbeddingService()
    
    return OpenAIEmbeddingService()