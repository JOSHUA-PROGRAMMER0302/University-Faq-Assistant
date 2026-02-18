import logging
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.scaledown_service import ScaleDownService
from backend.rag_engine import RAGEngine

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("university_faq")

app = FastAPI(
    title="University FAQ Assistant API",
    description="Smart Campus AI — Powered by ScaleDown Compression",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scaledown = ScaleDownService()
rag = RAGEngine()

sessions: dict[str, dict] = {}

UNIVERSITY_DATA = """Karunya University (KITS) operates under a Choice Based Credit System (CBCS) offering UG/PG programs with a focus on Christian values, holistic education, and strict anti-ragging policies. Key policies include mandatory 75-80% attendance, specific dress codes, a zero-tolerance approach to misconduct, and comprehensive IT/library usage guidelines.

Key Policies & Rules

Academic: 75% attendance is required to appear for examinations. The CBCS system allows flexible learning, and students can earn non-academic (NA) credits through sports or club activities.

Discipline: Ragging is strictly prohibited and constitutes a punishable, non-bailable offense. A strict dress code is enforced, and students must maintain a respectful and disciplined demeanor.

Safety & Security: The campus uses video surveillance for safety. A zero-tolerance policy exists for harassment and bullying.

Library: Books are issued for 15 days, and a "No Dues" certificate is mandatory for final exams.

IT Policy: Only licensed software is permitted; use of pirated software is forbidden.

Course Catalog & Academic Offerings

Schools: Engineering & Technology, Computer Science, Agriculture, Sciences, Arts, Media, and Management.

Programs: B.Tech, M.Tech, MBA (with 50% minimum eligibility), B.Com, B.Sc, M.Sc, and Ph.D.

Key Subjects: The curriculum includes core subjects alongside value-added courses like NSS, NCC, and personality development.

FAQ & General Information

Admission: Based on merit and entrance exams (e.g., CAT/MAT/XAT/KMAT for MBA).

Fees: Detailed in the student handbook, with specific provisions for scholarships and awards.

Contact: 1800 889 9888 / 1800 425 4300.

Support: The institution provides counseling and mentoring systems for students."""

DEFAULT_SESSION_ID = "karunya_main"


class UploadResponse(BaseModel):
    """Response model for document upload."""

    session_id: str = Field(..., description="Unique session identifier")
    original_length: int = Field(..., description="Character count of original text")
    compressed_length: int = Field(..., description="Character count after compression")
    compression_ratio: float = Field(..., description="Compression percentage achieved")
    chunk_count: int = Field(..., description="Number of indexed chunks")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")


class QuestionRequest(BaseModel):
    """Request model for asking a question."""

    session_id: str = Field(..., description="Session identifier from upload")
    question: str = Field(..., min_length=3, max_length=500, description="User question")


class AnswerResponse(BaseModel):
    """Response model for question answers."""

    question: str
    answer: str
    sources: list[str]
    confidence: float
    response_time_ms: float


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    active_sessions: int
    version: str


@app.on_event("startup")
async def startup_index() -> None:
    """Compress and index the preloaded Karunya University data on server start."""
    logger.info("Auto-indexing Karunya University data (%d chars)", len(UNIVERSITY_DATA))
    start = time.perf_counter()

    try:
        compressed = scaledown.compress(UNIVERSITY_DATA)
    except Exception as exc:
        logger.warning("ScaleDown failed during startup, using raw data: %s", exc)
        compressed = UNIVERSITY_DATA

    chunk_count = rag.index(DEFAULT_SESSION_ID, UNIVERSITY_DATA)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    compression_ratio = round((1 - len(compressed) / len(UNIVERSITY_DATA)) * 100, 2)

    sessions[DEFAULT_SESSION_ID] = {
        "original_length": len(UNIVERSITY_DATA),
        "compressed_length": len(compressed),
        "compression_ratio": compression_ratio,
        "chunk_count": chunk_count,
        "processing_time_ms": elapsed_ms,
    }
    logger.info(
        "Startup indexing complete — %d chunks, %.1f%% compression in %.0fms",
        chunk_count, compression_ratio, elapsed_ms,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="operational",
        active_sessions=len(sessions),
        version="1.0.0",
    )


@app.get("/default-session")
async def get_default_session() -> dict:
    """Return the preloaded default session info."""
    if DEFAULT_SESSION_ID not in sessions:
        raise HTTPException(status_code=503, detail="Default session not ready yet.")
    return {
        "session_id": DEFAULT_SESSION_ID,
        **sessions[DEFAULT_SESSION_ID],
    }


@app.post("/upload/text", response_model=UploadResponse)
async def upload_text(content: str) -> UploadResponse:
    """Upload raw text content for compression and indexing."""
    logger.info("Received text upload: %d characters", len(content))
    start = time.perf_counter()

    if len(content.strip()) < 50:
        raise HTTPException(status_code=400, detail="Content too short. Provide at least 50 characters.")

    try:
        compressed = scaledown.compress(content)
    except Exception as exc:
        logger.error("ScaleDown compression failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Compression service error: {exc}")

    session_id = uuid4().hex[:12]
    chunk_count = rag.index(session_id, compressed)

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    compression_ratio = round((1 - len(compressed) / len(content)) * 100, 2) if content else 0.0

    sessions[session_id] = {
        "original_length": len(content),
        "compressed_length": len(compressed),
        "compression_ratio": compression_ratio,
    }

    logger.info(
        "Session %s created — %d chunks, %.1f%% compression in %.0fms",
        session_id, chunk_count, compression_ratio, elapsed_ms,
    )

    return UploadResponse(
        session_id=session_id,
        original_length=len(content),
        compressed_length=len(compressed),
        compression_ratio=compression_ratio,
        chunk_count=chunk_count,
        processing_time_ms=elapsed_ms,
    )


@app.post("/upload/file", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """Upload a text file for compression and indexing."""
    if file.content_type and file.content_type not in (
        "text/plain",
        "text/csv",
        "text/markdown",
        "application/octet-stream",
    ):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    try:
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text.")

    return await upload_text(content)


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest) -> AnswerResponse:
    """Ask a question against the indexed university content."""
    logger.info("Question [%s]: %s", request.session_id, request.question)
    start = time.perf_counter()

    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Upload content first.")

    try:
        result = rag.search(request.session_id, request.question)
    except Exception as exc:
        logger.error("Search failed: %s", exc)
        raise HTTPException(status_code=500, detail="Search engine error.")

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    return AnswerResponse(
        question=request.question,
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"],
        response_time_ms=elapsed_ms,
    )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a session and its indexed data."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    rag.remove(session_id)
    del sessions[session_id]
    logger.info("Session %s deleted", session_id)
    return {"status": "deleted", "session_id": session_id}


@app.get("/sessions")
async def list_sessions() -> dict:
    """List all active sessions with metadata."""
    return {"sessions": sessions}


@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html."""
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
