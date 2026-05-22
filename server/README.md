## Server (FastAPI)

Run locally:

```powershell
cd server
..\.\.venv\Scripts\uvicorn main:app --reload
```

Swagger:

- `http://127.0.0.1:8000/docs`

Alembic:

```powershell
cd server
..\.\.venv\Scripts\alembic upgrade head
```

## Streaming AI actions (SSE)

Endpoint:

- `POST /api/v1/channels/{channel_id}/ai/actions/stream`

Requires:

- `GROQ_API_KEY` (Groq chat + Whisper ASR)
- `HF_API_TOKEN` (Hugging Face Inference API embeddings)

The response is `text/event-stream` with events like:

- `intent_detected`, `source_loading`, `retrieval_started`, `retrieval_completed`
- `generation_started`, `token`, `generation_completed`, `error`
