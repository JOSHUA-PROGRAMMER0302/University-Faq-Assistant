import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("university_faq.rag")

CHUNK_SIZE = 80
CHUNK_OVERLAP = 20
TOP_K = 3


class RAGEngine:

    def __init__(self) -> None:
        self._vectorizers: dict[str, TfidfVectorizer] = {}
        self._matrices: dict[str, object] = {}
        self._chunks: dict[str, list[str]] = {}

    def index(self, session_id: str, text: str) -> int:
        chunks = self._chunk_text(text)
        if not chunks:
            raise ValueError("Text produced no indexable chunks.")

        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(chunks)

        self._vectorizers[session_id] = vectorizer
        self._matrices[session_id] = matrix
        self._chunks[session_id] = chunks

        logger.info("Indexed %d chunks for session %s", len(chunks), session_id)
        return len(chunks)

    def search(self, session_id: str, query: str, top_k: int = TOP_K) -> dict:
        if session_id not in self._vectorizers:
            raise KeyError(f"Session '{session_id}' not found in index.")

        query_vec = self._vectorizers[session_id].transform([query])
        scores = cosine_similarity(query_vec, self._matrices[session_id]).flatten()

        ranked_indices = scores.argsort()[::-1][:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices):
            if scores[idx] <= 0:
                continue
            results.append({
                "rank": rank + 1,
                "chunk": self._chunks[session_id][idx],
                "score": round(float(scores[idx]), 4),
            })

        if not results:
            return {
                "answer": "I couldn't find relevant information for your question. Please try rephrasing.",
                "sources": [],
                "confidence": 0.0,
            }

        answer = self._build_answer(query, results)
        avg_score = sum(r["score"] for r in results) / len(results)

        return {
            "answer": answer,
            "sources": [r["chunk"][:200] for r in results],
            "confidence": round(float(avg_score), 4),
        }

    def remove(self, session_id: str) -> None:
        self._vectorizers.pop(session_id, None)
        self._matrices.pop(session_id, None)
        self._chunks.pop(session_id, None)
        logger.info("Removed session %s from index", session_id)

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
        import re
        sections = re.split(r'\n{2,}', text)
        chunks: list[str] = []
        for section in sections:
            section = section.strip()
            if not section or len(section) < 20:
                continue
            words = section.split()
            if len(words) <= chunk_size:
                chunks.append(section)
            else:
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
        answer = (
            f"Based on the university documentation, here is what I found:\n\n"
            f"{results[0]['chunk']}\n\n"
        )

        if len(results) > 1:
            answer += "Additional context:\n"
            for r in results[1:]:
                answer += f"• {r['chunk'][:250]}\n"

        return answer.strip()
