# 🎓 University FAQ Assistant

**Smart Campus AI — Powered by ScaleDown Compression + Semantic Search**

A production-ready AI-powered FAQ assistant for Karunya University (KITS). The system compresses university policy documents, indexes them with FAISS vector search, and answers student questions instantly through a modern glassmorphism web interface — all served from a single FastAPI server.

---

## Architecture

```
university-faq-assistant/
│
├── backend/
│   ├── main.py                 # FastAPI server — API + static file serving
│   ├── scaledown_service.py    # ScaleDown API client with retry & fallback
│   ├── rag_engine.py           # In-memory RAG: chunking → embeddings → FAISS
│   └── __init__.py
│
├── frontend/
│   ├── index.html              # Main HTML — Tailwind CSS + glassmorphism
│   ├── css/
│   │   └── styles.css          # Custom dark/light theme, glass cards, animations
│   └── js/
│       ├── api.js              # API client module
│       ├── chat.js             # Chat UI, typing indicators, toasts, badges
│       └── app.js              # Main controller, theme toggle, analytics
│
├── requirements.txt
├── LICENSE
└── README.md
```

### Data Flow

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────┐
│   HTML/JS/CSS   │────▶│   FastAPI Backend     │────▶│  ScaleDown   │
│   Frontend      │◀────│   /ask  /health       │◀────│  API         │
│   (port 8000)   │     │   + Static Files      │     └──────────────┘
└─────────────────┘     └──────────┬───────────┘
                                   │
                         ┌─────────▼─────────┐
                         │    RAG Engine      │
                         │ ┌───────────────┐  │
                         │ │  Sentence     │  │
                         │ │  Transformers │  │
                         │ │ MiniLM-L6-v2  │  │
                         │ └───────┬───────┘  │
                         │ ┌───────▼───────┐  │
                         │ │  FAISS Index  │  │
                         │ │  (in-memory)  │  │
                         │ └───────────────┘  │
                         └───────────────────┘
```

---

## Features

- **Text Compression** — ScaleDown API with intelligent local fallback compressor
- **Semantic Search (RAG)** — FAISS + sentence-transformers for contextual retrieval
- **In-Memory Engine** — No database required; pure speed, zero config
- **Pre-loaded Data** — Karunya University policies auto-indexed on startup
- **Modern Web UI** — Glassmorphism dark theme with Tailwind CSS
- **ChatGPT-style Chat** — Typing indicators, confidence badges, source chips
- **Suggested FAQs** — 8 one-click question buttons
- **Dark/Light Toggle** — Theme switching from sidebar
- **Live Analytics** — Sidebar shows query count, avg confidence, response time
- **Compression Metrics** — Real-time stats displayed in metric cards
- **Toast Notifications** — Success/error feedback on every action
- **Single Server** — Backend API + frontend served on the same port

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/JOSHUA-PROGRAMMER0302/University-Faq-Assistant.git
cd University-Faq-Assistant
pip install -r requirements.txt
```

### 2. Set Environment Variables (optional)

```bash
export SCALEDOWN_API_KEY="your-api-key"
```

If no API key is set, the system uses a local fallback compressor automatically.

### 3. Run

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Open in Browser

Navigate to **http://localhost:8000** — that's it, one server for everything.

---

## API Endpoints

| Method   | Endpoint              | Description                                |
|----------|-----------------------|--------------------------------------------|
| `GET`    | `/`                   | Serve the frontend UI                      |
| `GET`    | `/health`             | Service health check                       |
| `GET`    | `/default-session`    | Pre-loaded Karunya session info            |
| `POST`   | `/ask`               | Ask a question (JSON: `session_id`, `question`) |
| `GET`    | `/sessions`           | List all active sessions                   |
| `DELETE`  | `/session/{id}`      | Delete a session                           |

### Example

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"session_id": "karunya_main", "question": "What is the attendance policy?"}'
```

---

## Tech Stack

| Layer      | Technology                                     |
|------------|------------------------------------------------|
| Backend    | FastAPI, Pydantic, Uvicorn                     |
| Search     | FAISS (`IndexFlatIP`), sentence-transformers   |
| Compress   | ScaleDown API + Local Fallback                 |
| Frontend   | HTML, Tailwind CSS, Vanilla JavaScript         |
| ML Model   | `all-MiniLM-L6-v2` (384-dim embeddings)       |
| Styling    | Glassmorphism, CSS animations, dark/light mode |

---

## How RAG Works

1. **Chunking** — University text is split into 80-word overlapping windows (20-word overlap)
2. **Embedding** — Each chunk is encoded into a 384-dim vector using `all-MiniLM-L6-v2`
3. **Indexing** — Vectors are L2-normalized and stored in a FAISS `IndexFlatIP` index
4. **Query** — User question is embedded → top-3 similar chunks retrieved → answer composed

---

## Built By

**JOSHUA ISRAEL**

---

## License

See [LICENSE](LICENSE) for details.