# 🎓 EduTube AI — Watch. Learn. Ask. Master.
Search educational videos, watch them in an embedded player, and ask a video-aware AI Teacher. Includes transcript RAG, notes, summary, quizzes, weak-topic detection, a dashboard and Watch Later/History.

## Architecture
React + Vite + TypeScript (frontend) → FastAPI (backend) → SQLite via SQLAlchemy.
`backend/app`: `main.py` (routes, auth), `yt.py` (YouTube search/transcript, demo fallback), `rag.py` (chunking + retrieval), `ai.py` (OpenAIProvider / DemoProvider), `db.py` (models), `demo.py` (sample videos + transcripts).
RAG: transcript → sections → word chunks (60 words, 15 overlap) → bag-of-words cosine retrieval (top-3) → AI Teacher prompt.

## Quick start (Windows)
Double-click `run_windows.bat` (needs Python 3.10+ and Node 18+). It installs everything and opens http://localhost:5173.

## Setup (Windows, manual)
Backend:
```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```
Frontend (new terminal):
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. Tests: `cd backend && pytest`.

## Environment (backend/.env)
`OPENAI_API_KEY` (optional), `YOUTUBE_API_KEY` (YouTube Data API v3, optional), `SECRET_KEY` (any long random string).
Keys are read only by the backend. Without them the app runs in **Demo Mode** (sample videos/transcripts, extractive answers).

## Troubleshooting
- "Cannot reach the server": start the backend on port 8000.
- Transcript unavailable: some videos disable captions; the Teacher falls back to general knowledge.
- Quiz questions are cloze-style, generated from the transcript.

## Future scope
FAISS/Chroma embeddings, Tailwind redesign and component split.

## Features
Search, embedded player, video-aware AI Teacher (3 levels), transcript RAG, summary, notes, exam prep/viva (LLM when key set), quizzes (LLM or transcript-based), weak-topic detection, learning path, dashboard charts, playlists, history, watch later, profile, notifications, dark mode, Demo Mode.
