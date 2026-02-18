# 🎓 University FAQ Assistant

**Smart Campus AI — Powered by ScaleDown Compression**

A production-ready AI-powered FAQ assistant for universities. Upload course catalogs, policies, or any campus documentation — the system compresses, indexes, and answers student questions in real-time using semantic search.

---

## Architecture

```
university-faq-assistant/
│
├── backend/
│   ├── main.py                 # FastAPI server — endpoints, CORS, Pydantic models
│   ├── scaledown_service.py    # ScaleDown API client with retry & fallback compression
│   ├── rag_engine.py           # In-memory RAG: chunking → embeddings → FAISS search
│   └── __init__.py
│
├── frontend/
│   ├── app.py                  # Streamlit UI — dark glassmorphism dashboard
│   ├── styles.css              # Custom fintech-style CSS
│   └── __init__.py
│
├── requirements.txt
├── LICENSE
└── README.md
```

### Data Flow

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Streamlit   │────▶│  FastAPI Backend  │────▶│  ScaleDown   │
│  Frontend    │◀────│  /upload  /ask    │◀────│  API         │
└──────────────┘     └────────┬─────────┘     └──────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   RAG Engine       │
                    │  ┌──────────────┐  │
                    │  │ Sentence     │  │
                    │  │ Transformers │  │
                    │  └──────┬───────┘  │
                    │  ┌──────▼───────┐  │
                    │  │    FAISS     │  │
                    │  │  (in-memory) │  │
                    │  └──────────────┘  │
                    └───────────────────┘
```

---

## Features

- **Text Compression** — ScaleDown API integration with intelligent local fallback
- **Semantic Search** — FAISS + sentence-transformers for accurate retrieval
- **In-Memory RAG** — No database required; pure speed
- **Modern UI** — Dark glassmorphism, animated metrics, ChatGPT-style chat
- **Suggested FAQs** — One-click common questions
- **Compression Metrics** — Real-time stats on compression ratio, token reduction, response time
- **Dark/Light Toggle** — Theme switching from sidebar
- **Session Management** — Upload, query, and clear sessions independently

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables (optional)

```bash
export SCALEDOWN_API_KEY="your-api-key"
```

If no API key is set, the system uses an intelligent local fallback compressor.

### 3. Start the Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Start the Frontend

```bash
streamlit run frontend/app.py
```

### 5. Open in Browser

Navigate to `http://localhost:8501`

---

## API Endpoints

| Method   | Endpoint              | Description                            |
|----------|-----------------------|----------------------------------------|
| `GET`    | `/health`             | Service health check                   |
| `POST`   | `/upload/text`        | Upload raw text for compression        |
| `POST`   | `/upload/file`        | Upload a text file                     |
| `POST`   | `/ask`                | Ask a question against indexed content |
| `DELETE`  | `/session/{id}`      | Delete a session                       |
| `GET`    | `/sessions`           | List all active sessions               |

---

## Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Backend   | FastAPI, Pydantic, Uvicorn        |
| Search    | FAISS, sentence-transformers      |
| Compress  | ScaleDown API                     |
| Frontend  | Streamlit, Custom CSS             |
| ML Model  | all-MiniLM-L6-v2                  |

---

## Built By

**JOSHUA ISRAEL**

---

## License

See [LICENSE](LICENSE) for details.