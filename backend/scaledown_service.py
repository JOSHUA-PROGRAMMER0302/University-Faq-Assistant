import logging
import os
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("university_faq.scaledown")

SCALEDOWN_API_URL = "https://api.scaledownai.com/v1/compress"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5


class ScaleDownService:
    """Client for the ScaleDown text-compression API with retry and fallback logic."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self._api_key = api_key or os.getenv("SCALEDOWN_API_KEY", "")
        self._base_url = base_url or os.getenv("SCALEDOWN_API_URL", SCALEDOWN_API_URL)
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        """Build an HTTP session with automatic retries."""
        session = requests.Session()
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def compress(self, text: str) -> str:
        """Compress text via ScaleDown API; falls back to local extraction on failure."""
        if not text or not text.strip():
            raise ValueError("Cannot compress empty text.")

        if not self._api_key:
            logger.warning("No SCALEDOWN_API_KEY set — using local fallback compression")
            return self._fallback_compress(text)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "text": text,
            "mode": "extractive",
            "target_ratio": 0.4,
        }

        start = time.perf_counter()
        try:
            response = self._session.post(
                self._base_url,
                json=payload,
                headers=headers,
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            compressed = data.get("compressed_text", data.get("result", text))
            elapsed = round((time.perf_counter() - start) * 1000, 1)
            logger.info(
                "ScaleDown compression: %d → %d chars (%.1f%%) in %dms",
                len(text), len(compressed),
                (1 - len(compressed) / len(text)) * 100,
                elapsed,
            )
            return compressed

        except requests.exceptions.Timeout:
            logger.error("ScaleDown API timed out after %ds", DEFAULT_TIMEOUT)
            return self._fallback_compress(text)

        except requests.exceptions.ConnectionError as exc:
            logger.error("ScaleDown connection error: %s", exc)
            return self._fallback_compress(text)

        except requests.exceptions.HTTPError as exc:
            logger.error("ScaleDown HTTP error %s: %s", exc.response.status_code, exc)
            if exc.response.status_code == 401:
                raise PermissionError("Invalid ScaleDown API key.") from exc
            return self._fallback_compress(text)

        except Exception as exc:
            logger.error("Unexpected ScaleDown error: %s", exc)
            return self._fallback_compress(text)

    def _fallback_compress(self, text: str) -> str:
        """Local extractive compression: keep sentences with high information density."""
        logger.info("Running local fallback compression on %d chars", len(text))
        sentences = self._split_sentences(text)

        if len(sentences) <= 5:
            return text

        scored = []
        for sent in sentences:
            words = sent.split()
            unique_ratio = len(set(w.lower() for w in words)) / max(len(words), 1)
            length_score = min(len(words) / 20, 1.0)
            keyword_hits = sum(
                1 for w in words
                if w.lower() in {
                    "policy", "requirement", "deadline", "fee", "exam",
                    "course", "credit", "grade", "admission", "scholarship",
                    "registration", "attendance", "hostel", "library",
                    "semester", "gpa", "certificate", "regulation",
                    "eligibility", "apply", "procedure", "document",
                    "campus", "department", "faculty", "student",
                }
            )
            keyword_score = min(keyword_hits / 3, 1.0)
            score = (unique_ratio * 0.3) + (length_score * 0.3) + (keyword_score * 0.4)
            scored.append((score, sent))

        scored.sort(key=lambda x: x[0], reverse=True)
        target_count = max(3, int(len(scored) * 0.4))
        kept = scored[:target_count]
        kept.sort(key=lambda x: sentences.index(x[1]))

        compressed = " ".join(s for _, s in kept)
        logger.info(
            "Fallback compression: %d → %d chars (%.1f%%)",
            len(text), len(compressed),
            (1 - len(compressed) / len(text)) * 100,
        )
        return compressed

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences on common delimiters."""
        import re
        raw = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in raw if len(s.strip()) > 10]
