# vibe-chat

Monorepo layout:

- `server/` – FastAPI backend (Swagger at `/docs`)
- `client/` – Next.js web app

## Run server

```powershell
cd server
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\uvicorn main:app --reload
```

## Run client

```powershell
cd client
pnpm install
pnpm dev
```
