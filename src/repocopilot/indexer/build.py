import os
from typing import List
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from ..common.schema import CodeChunk
from .crawler import RepositoryCrawler
from .parser import CodeParser
from .embeddings import get_embedding_service
from ..retriever.bm25 import BM25Retriever


class IndexBuilder:
    def __init__(
        self,
        repo_path: str,
        output_dir: str = "data",
        collection_name: str = "repo_code",
        use_mock_embedding: bool = False,
        provider: str = None,
        ignore_dirs: List[str] = None,
    ):
        self.repo_path = repo_path
        self.output_dir = output_dir
        self.collection_name = collection_name

        # Ensure output dir exists
        os.makedirs(output_dir, exist_ok=True)

        # Initialize components
        self.embedding_service = get_embedding_service(
            use_mock=use_mock_embedding, provider=provider
        )
        # Get vector size by doing a dummy embedding
        dummy_vector = self.embedding_service.get_embeddings(["test"])[0]
        vector_size = len(dummy_vector)
        print(f"📡 Using Embedding Provider with vector size: {vector_size}")

        self.crawler = RepositoryCrawler(repo_path, ignore_dirs=ignore_dirs)
        self.parser = CodeParser()

        # Initialize Qdrant (Persistent mode)
        qdrant_path = os.path.join(output_dir, "qdrant")
        self.client = QdrantClient(path=qdrant_path)

        # Check if collection exists
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
        if exists:
            # Check if vector size matches, if not, recreate
            collection_info = self.client.get_collection(self.collection_name)
            if collection_info.config.params.vectors.size != vector_size:
                print(
                    f"⚠️ Vector size mismatch ({collection_info.config.params.vectors.size} != {vector_size})."
                )
                # Close client before physical delete
                self.client.close()
                import shutil

                print(f"🧹 Physically removing {qdrant_path} for clean rebuild...")
                shutil.rmtree(qdrant_path, ignore_errors=True)

                # Re-init client
                self.client = QdrantClient(path=qdrant_path)
                print(f"🆕 Creating new collection with size {vector_size}...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size, distance=Distance.COSINE
                    ),
                )

    def build(self):
        print(f"🚀 Starting index build for {self.repo_path}...")

        all_chunks: List[CodeChunk] = []

        # 1. Crawl and Parse
        print("📂 Crawling and parsing files...")
        file_paths = list(self.crawler.scan())

        for path in tqdm(file_paths, desc="Parsing"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    code = f.read()

                # Get relative path for cleaner metadata
                rel_path = os.path.relpath(path, self.repo_path)
                chunks = self.parser.extract_structures(code, rel_path)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"⚠️ Error processing {path}: {e}")

        print(f"✅ Found {len(all_chunks)} chunks.")

        if not all_chunks:
            return

        # 2. Embed & Index Vector
        print("🧠 Generating embeddings & Vector Indexing...")
        batch_size = 100
        points = []

        for i in tqdm(range(0, len(all_chunks), batch_size), desc="Embedding"):
            batch = all_chunks[i : i + batch_size]
            texts = [c.content for c in batch]
            vectors = self.embedding_service.get_embeddings(texts)

            for chunk, vector in zip(batch, vectors):
                points.append(
                    PointStruct(
                        id=chunk.id,
                        vector=vector,
                        # CRITICAL: Use mode='json' to ensure payload is primitive types (no Enums)
                        payload=chunk.model_dump(mode="json", exclude={"id"}),
                    )
                )

        self.client.upsert(collection_name=self.collection_name, points=points)
        print(f"💾 Vector index saved to {os.path.join(self.output_dir, 'qdrant')}")
        print(f"💾 Vector index saved to {os.path.join(self.output_dir, 'qdrant')}")

        # 3. Build & Save BM25
        print("📚 Building BM25 index...")
        bm25_retriever = BM25Retriever()
        bm25_retriever.index(all_chunks)

        # Save as JSON (the retriever handles the extension replacement, but let's be explicit)
        bm25_path = os.path.join(
            self.output_dir, "bm25.pkl"
        )  # Keeper .pkl in var name for compat, but underlying saves .json
        bm25_retriever.save(bm25_path)
        print(f"💾 BM25 index saved to {bm25_path.replace('.pkl', '.json')}")

        print("🎉 Indexing complete!")

        # Verify count
        count = self.client.count(collection_name=self.collection_name)
        print(f"📈 Total vectors in collection: {count.count}")

        # Explicitly close the client to release file locks
        self.client.close()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    # Check settings from .env
    provider = os.getenv("EMBEDDING_PROVIDER", "mock")
    use_mock = provider == "mock"

    # Test on the current project itself
    builder = IndexBuilder(repo_path=".", use_mock_embedding=use_mock)
    builder.build()
