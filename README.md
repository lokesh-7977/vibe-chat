# vibe-chat

Monorepo layout:

- `server/` – FastAPI backend (Swagger at `/docs`)
- `client/` – Next.js web app

## Run server

```powershell
cd server
..\.\.venv\Scripts\uvicorn main:app --reload
```

## Run client

```powershell
cd client
pnpm install
pnpm dev
```
