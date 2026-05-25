FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --no-compile --root-user-action=ignore -r requirements.txt \
    && find /usr/local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true


FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local /usr/local

COPY . .

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
