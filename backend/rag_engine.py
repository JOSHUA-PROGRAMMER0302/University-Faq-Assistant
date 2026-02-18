import logging
from typing import Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("university_faq.rag")

CHUNK_SIZE = 80
CHUNK_OVERLAP = 20
TOP_K = 3
MODEL_NAME = "all-MiniLM-L6-v2"


class RAGEngine:
    """In-memory Retrieval-Augmented Generation engine using FAISS and sentence-transformers."""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        logger.info("Loading embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()
        self._indices: dict[str, faiss.IndexFlatIP] = {}
        self._chunks: dict[str, list[str]] = {}

    def index(self, session_id: str, text: str) -> int:
        """Chunk, embed, and index compressed text for a session."""
        chunks = self._chunk_text(text)
        if not chunks:
            raise ValueError("Text produced no indexable chunks.")

        embeddings = self._encode(chunks)
        faiss.normalize_L2(embeddings)

        index = faiss.IndexFlatIP(self._dimension)
        index.add(embeddings)

        self._indices[session_id] = index
        self._chunks[session_id] = chunks

        logger.info("Indexed %d chunks for session %s", len(chunks), session_id)
        return len(chunks)

    def search(self, session_id: str, query: str, top_k: int = TOP_K) -> dict:
        """Search indexed chunks and return a contextual answer."""
        if session_id not in self._indices:
            raise KeyError(f"Session '{session_id}' not found in index.")

        query_vec = self._encode([query])
        faiss.normalize_L2(query_vec)

        scores, ids = self._indices[session_id].search(query_vec, top_k)

        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], ids[0])):
            if idx < 0:
                continue
            results.append({
                "rank": rank + 1,
                "chunk": self._chunks[session_id][idx],
                "score": round(float(score), 4),
            })

        if not results:
            return {
                "answer": "I couldn't find relevant information for your question. Please try rephrasing.",
                "sources": [],
                "confidence": 0.0,
            }

        answer = self._build_answer(query, results)
        avg_score = np.mean([r["score"] for r in results])

        return {
            "answer": answer,
            "sources": [r["chunk"][:200] for r in results],
            "confidence": round(float(avg_score), 4),
        }

    def remove(self, session_id: str) -> None:
        """Remove a session's index and chunks from memory."""
        self._indices.pop(session_id, None)
        self._chunks.pop(session_id, None)
        logger.info("Removed session %s from index", session_id)

    def _encode(self, texts: list[str]) -> np.ndarray:
        """Encode text list into normalized numpy embeddings."""
        return self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=False,
        ).astype("float32")

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
        """Split text into overlapping word-level chunks."""
        words = text.split()
        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            if len(chunk.strip()) > 20:
                chunks.append(chunk.strip())
            start += chunk_size - overlap
        return chunks

    @staticmethod
    def _build_answer(query: str, results: list[dict]) -> str:
        """Compose a readable answer from retrieved chunks."""
        context_block = "\n\n".join(
            f"[Source {r['rank']}] (relevance {r['score']:.0%})\n{r['chunk']}"
            for r in results
        )

        answer = (
            f"Based on the university documentation, here is what I found:\n\n"
            f"{results[0]['chunk']}\n\n"
        )

        if len(results) > 1:
            answer += "Additional context:\n"
            for r in results[1:]:
                answer += f"• {r['chunk'][:250]}\n"

        return answer.strip()
