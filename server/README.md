## Server (FastAPI)

Run locally:

```powershell
cd server
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\uvicorn main:app --reload
```

Swagger:

- `http://127.0.0.1:8000/docs`

Alembic:

```powershell
cd server
.\.venv\Scripts\alembic upgrade head
```

## Streaming AI actions (SSE)

Endpoint:

- `POST /api/v1/channels/{channel_id}/ai/actions/stream`

Requires:

- `NVAPI_API_KEY` (NVIDIA Integrate API key for chat completions)

The response is `text/event-stream` with events like:

- `intent_detected`, `source_loading`, `retrieval_started`, `retrieval_completed`
- `generation_started`, `token`, `generation_completed`, `error`

## Secure file serving (Cloudflare R2)

This backend never stores signed URLs. It stores only the R2 `object_key` and generates short-lived URLs on demand.

Endpoints:

- `POST /api/v1/uploads/presign` → returns `object_key` + presigned **PUT** `upload_url`
- `GET /api/v1/uploads/image-url?key=<object_key>` → returns a presigned **GET** URL (expires via `R2_PRESIGN_EXPIRES_SECONDS`, default 3600s)

### R2 CORS (required for browser uploads)

Set these CORS rules on your R2 bucket (Cloudflare dashboard → R2 → bucket → Settings → CORS):

```json
[
  {
    "AllowedOrigins": ["http://localhost:3000"],
    "AllowedMethods": ["GET", "PUT", "HEAD"],
    "AllowedHeaders": ["content-type"],
    "ExposeHeaders": ["etag"],
    "MaxAgeSeconds": 3600
  }
]
```
