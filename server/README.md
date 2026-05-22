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
