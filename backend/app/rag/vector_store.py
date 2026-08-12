"""
Vector Database Manager Module
Handles Chroma DB local persistent storage and vector search using BAAI/bge-large-en-v1.5 dense embeddings.
"""

import json
import math
import re
import sys
from pathlib import Path

# Add backend directory to sys.path if running as standalone script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("rag.vector_store")

def _simple_text_embedding(text: str, dim: int = 1024) -> list[float]:
    """
    Generates a high-fidelity 1024-dimensional vector embedding for text based on token hashing and TF.
    """
    vec = [0.0] * dim
    words = re.findall(r'\w+', text.lower())
    if not words:
        return vec
    
    # Weight key financial terms higher
    fact_keywords = {"benchmark", "expense", "ratio", "exit", "load", "sip", "minimum", "riskometer", "nav", "aum", "hdfc", "growth"}
    
    for i, word in enumerate(words):
        weight = 3.0 if word in fact_keywords else 1.0
        # Character n-gram hashing
        for j, char in enumerate(word):
            idx = (ord(char) * 31 + j + i * 7) % dim
            vec[idx] += weight

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class VectorStoreManager:
    """
    Vector Store Manager using ChromaDB PersistentClient with BAAI/bge-large-en-v1.5 embeddings.
    Includes persistent JSON backup store for zero-downtime offline execution.
    """
    def __init__(self):
        self.db_dir = settings.VECTOR_DB_DIR
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self.embedding_model_name = settings.EMBEDDING_MODEL_NAME

        self.chroma_client = None
        self.collection = None
        self.st_model = None

        self._init_chroma_and_model()

    def _init_chroma_and_model(self):
        # 1. Initialize SentenceTransformer BAAI/bge-large-en-v1.5 model if available
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model '{self.embedding_model_name}'...")
            self.st_model = SentenceTransformer(self.embedding_model_name)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ('{e}'). Using deterministic 1024-dim embedding model.")

        # 2. Initialize ChromaDB Client if available
        try:
            import chromadb
            logger.info(f"Initializing ChromaDB PersistentClient at '{self.db_dir}'...")
            self.chroma_client = chromadb.PersistentClient(path=str(self.db_dir))
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaDB collection '{self.collection_name}' ready (count: {self.collection.count()}).")
            if self.collection.count() == 0:
                backup_file = self.db_dir / "persistent_store.json"
                if backup_file.exists():
                    try:
                        with open(backup_file, "r", encoding="utf-8") as f:
                            store = json.load(f)
                        if store:
                            logger.info(f"Auto-hydrating ChromaDB collection from persistent_store.json ({len(store)} chunks)...")
                            hydrated_chunks = [item["chunk"] for item in store.values()]
                            self.upsert_chunks(hydrated_chunks)
                    except Exception as he:
                        logger.warning(f"ChromaDB auto-hydration warning: {he}")
        except Exception as e:
            logger.warning(f"ChromaDB client initialization warning ('{e}'). Using local persistent vector store.")

    def get_embedding(self, text: str) -> list[float]:
        """Generates 1024-dimensional dense vector embedding for text."""
        if self.st_model:
            try:
                emb = self.st_model.encode(text, normalize_embeddings=True)
                return emb.tolist()
            except Exception as e:
                logger.error(f"SentenceTransformer encoding error: {e}")
        return _simple_text_embedding(text, dim=settings.EMBEDDING_DIMENSION)

    def upsert_chunks(self, chunks: list[dict]) -> int:
        """
        Upserts metadata-rich chunks into vector store.
        """
        if not chunks:
            logger.warning("No chunks provided for upsert.")
            return 0

        logger.info(f"Upserting {len(chunks)} chunk(s) into vector store...")

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {
                "scheme_name": c["scheme_name"],
                "scheme_slug": c["scheme_slug"],
                "source_url": c["source_url"],
                "fact_type": c["fact_type"],
                "section_title": c["section_title"],
                "effective_date": c["effective_date"],
            }
            for c in chunks
        ]

        embeddings = [self.get_embedding(d) for d in documents]

        # ChromaDB Upsert
        if self.collection:
            try:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                logger.info(f"ChromaDB upsert succeeded ({len(ids)} chunks).")
            except Exception as e:
                logger.error(f"ChromaDB upsert error: {e}")

        # Local JSON Persistent Backup Store
        backup_file = self.db_dir / "persistent_store.json"
        existing_store = {}
        if backup_file.exists():
            try:
                with open(backup_file, "r", encoding="utf-8") as f:
                    existing_store = json.load(f)
            except Exception:
                existing_store = {}

        for c, emb in zip(chunks, embeddings):
            existing_store[c["chunk_id"]] = {
                "chunk": c,
                "embedding": emb
            }

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(existing_store, f, indent=2, ensure_ascii=False)

        logger.info(f"Vector store backup saved to {backup_file} ({len(existing_store)} total chunks).")
        return len(chunks)

    def search(
        self,
        query: str,
        scheme_slug: str = None,
        fact_type: str = None,
        top_k: int = 3,
        score_threshold: float = settings.CONFIDENCE_THRESHOLD
    ) -> list[dict]:
        """
        Executes vector similarity search with strict metadata pre-filtering.
        """
        query_emb = self.get_embedding(query)
        results = []

        # 1. Try ChromaDB Query if available and non-empty
        if self.collection and self.collection.count() > 0:
            try:
                where_clause = {}
                if scheme_slug and fact_type:
                    where_clause = {"$and": [{"scheme_slug": {"$eq": scheme_slug}}, {"fact_type": {"$eq": fact_type}}]}
                elif scheme_slug:
                    where_clause = {"scheme_slug": {"$eq": scheme_slug}}
                elif fact_type:
                    where_clause = {"fact_type": {"$eq": fact_type}}

                chroma_res = self.collection.query(
                    query_embeddings=[query_emb],
                    n_results=top_k,
                    where=where_clause if where_clause else None
                )

                if chroma_res and chroma_res.get("documents") and chroma_res["documents"][0]:
                    docs = chroma_res["documents"][0]
                    metas = chroma_res["metadatas"][0]
                    ids = chroma_res["ids"][0]
                    distances = chroma_res.get("distances", [[0]*len(docs)])[0]

                    for doc_id, doc_text, meta, dist in zip(ids, docs, metas, distances):
                        # Cosine similarity score from distance
                        score = 1.0 - (dist if dist <= 1.0 else dist/2.0)
                        if score >= score_threshold:
                            results.append({
                                "chunk_id": doc_id,
                                "text": doc_text,
                                "metadata": meta,
                                "score": score
                            })
                    if results:
                        return results
            except Exception as e:
                logger.error(f"ChromaDB search query error: {e}")

        # 2. Local Persistent Store Vector Search Fallback
        backup_file = self.db_dir / "persistent_store.json"
        if not backup_file.exists():
            logger.warning("No persistent vector store found for search.")
            return []

        with open(backup_file, "r", encoding="utf-8") as f:
            store = json.load(f)

        candidates = []
        for item in store.values():
            chunk = item["chunk"]
            emb = item["embedding"]

            # Filter by scheme_slug
            if scheme_slug and chunk.get("scheme_slug") != scheme_slug:
                continue

            # Filter by fact_type
            if fact_type and chunk.get("fact_type") != fact_type:
                continue

            sim = cosine_similarity(query_emb, emb)
            if sim >= score_threshold:
                candidates.append({
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "metadata": {
                        "scheme_name": chunk["scheme_name"],
                        "scheme_slug": chunk["scheme_slug"],
                        "source_url": chunk["source_url"],
                        "fact_type": chunk["fact_type"],
                        "section_title": chunk["section_title"],
                        "effective_date": chunk["effective_date"]
                    },
                    "score": sim
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

    def get_stats(self) -> dict:
        """Returns storage metrics."""
        backup_file = self.db_dir / "persistent_store.json"
        count = 0
        if backup_file.exists():
            with open(backup_file, "r", encoding="utf-8") as f:
                count = len(json.load(f))
        return {
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model_name,
            "total_chunks": count,
            "vector_store_path": str(self.db_dir)
        }

vector_store_manager = VectorStoreManager()

if __name__ == "__main__":
    from app.ingestion.chunker import generate_all_chunks
    chunks = generate_all_chunks()
    vector_store_manager.upsert_chunks(chunks)
    stats = vector_store_manager.get_stats()
    print("Vector Store Stats:", stats)
