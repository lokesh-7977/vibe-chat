# Stage 1: system build dependencies
FROM python:3.11-alpine AS base

RUN apk add --no-cache gcc musl-dev linux-headers libffi-dev openssl-dev

WORKDIR /app

# Stage 2: download Python wheels only
FROM base AS download

COPY requirements.txt .
RUN pip download --no-cache-dir --root-user-action=ignore \
    -r requirements.txt -d /wheels

# Stage 3: install packages from local wheels
FROM base AS install

COPY requirements.txt .
COPY --from=download /wheels /wheels
RUN pip install --no-cache-dir --no-compile --root-user-action=ignore \
    --no-index --find-links /wheels -r requirements.txt \
    && rm -rf /wheels

# Stage 4: strip unnecessary files
FROM install AS strip

RUN find /usr/local \
    \( -name "*.pyc" -o -name "*.pyo" \) -delete \
    && find /usr/local/lib/python3.11 -name "test*" -type d -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf /usr/local/lib/python3.11/site-packages/pip \
    /usr/local/lib/python3.11/site-packages/setuptools \
    /usr/local/lib/python3.11/site-packages/_pytest 2>/dev/null || true \
    && find /usr/local/lib/python3.11/site-packages -name "*.txt" -o -name "*.md" -o -name "*.rst" | xargs rm -f 2>/dev/null || true

# Stage 5: final runtime image
FROM python:3.11-alpine

WORKDIR /app

COPY --from=strip /usr/local /usr/local
COPY . .

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
