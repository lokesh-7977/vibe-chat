# Backend Architecture Guide

## Overview

This backend follows a layered architecture so each part of the codebase has one clear responsibility.

Instead of putting everything inside one route file, the project is split into:

- `routes` for HTTP endpoints
- `dependencies` for dependency injection
- `controllers` for request-to-service delegation
- `services` for business logic
- `repositories` for database access
- `schemas` for request and response models
- `db/models` for SQLAlchemy models
- `core` for shared app configuration and security helpers
- `utils` for reusable helpers like token generation and username generation

This structure makes the code easier to read, test, debug, and extend as the project grows.

---

## Current Folder Structure

```text
backend/
|-- app/
|   |-- api/
|   |   |-- dependencies/
|   |   |   `-- auth.py
|   |   |-- routes/
|   |   |   |-- auth.py
|   |   |   `-- health.py
|   |   `-- router.py
|   |-- controllers/
|   |   `-- auth_controller.py
|   |-- core/
|   |   |-- config.py
|   |   `-- security.py
|   |-- db/
|   |   |-- migrations/
|   |   |-- models/
|   |   |   `-- user.py
|   |   |-- base.py
|   |   `-- session.py
|   |-- repositories/
|   |   `-- user_repository.py
|   |-- schemas/
|   |   |-- auth.py
|   |   |-- common.py
|   |   `-- user.py
|   |-- services/
|   |   `-- auth_service.py
|   |-- utils/
|   |   |-- create_access_token.py
|   |   |-- create_refresh_token.py
|   |   |-- generate_username.py
|   |   `-- verify_refresh_token.py
|   `-- main.py
|-- docker-compose.yml
|-- alembic.ini
|-- main.py
`-- requirement.txt
```

---

## Layer Responsibilities

### 1. Routes

Location:

- `app/api/routes/auth.py`
- `app/api/routes/health.py`

Purpose:

- define HTTP endpoints
- accept request payloads
- define response models and status codes
- call the controller

Routes should **not** contain:

- SQL queries
- password hashing
- token generation logic
- commit/refresh logic
- business rules

Example:

```python
@router.post("/register")
def register_user(user: UserCreate, request: Request, controller: AuthControllerDep):
    return controller.register_user(user=user, request=request)
```

This keeps the route layer thin and easy to understand.

---

### 2. Dependencies

Location:

- `app/api/dependencies/auth.py`

Purpose:

- build objects required by the route layer
- wire together repository, service, and controller
- centralize dependency injection

Current flow:

```python
db -> UserRepository -> AuthService -> AuthController
```

This means routes do not manually construct service objects.

---

### 3. Controllers

Location:

- `app/controllers/auth_controller.py`

Purpose:

- act as the bridge between routes and services
- receive route input and forward it to the correct service method

Current controller behavior:

- `register_user()` delegates to `AuthService.register_user()`
- `login_user()` delegates to `AuthService.login_user()`
- `refresh_token()` delegates to `AuthService.refresh_token()`
- `delete_account()` delegates to `AuthService.delete_account()`
- `logout_user()` delegates to `AuthService.logout_user()`

Why keep a controller:

- it gives routes a stable entry point
- it prevents routes from depending directly on business logic details
- it gives room to add orchestration later without bloating routes

Right now the controller is intentionally thin. That is normal.

---

### 4. Services

Location:

- `app/services/auth_service.py`

Purpose:

- contain the real business logic
- enforce auth-related rules
- coordinate repository, security helpers, session handling, and token creation

Current service responsibilities:

- register user
- validate duplicate email
- generate username
- hash password
- create JWT access token
- create refresh token
- store session values
- verify login credentials
- refresh token handling
- soft delete account
- logout session clearing

This is the best place for app rules because it is independent from HTTP routing details and DB query details.

---

### 5. Repositories

Location:

- `app/repositories/user_repository.py`

Purpose:

- isolate all database access
- keep SQLAlchemy queries out of routes and services

Current repository methods:

- `get_by_email()`
- `get_active_by_email()`
- `get_by_id()`
- `get_active_by_id()`
- `create()`
- `save()`

This helps because:

- services stay focused on business logic
- DB queries are reusable
- future DB changes are easier to contain

---

### 6. Schemas

Location:

- `app/schemas/user.py`
- `app/schemas/auth.py`
- `app/schemas/common.py`

Purpose:

- define request and response shapes
- validate incoming data
- standardize output format

Examples:

- `UserCreate` for register input
- `UserLogin` for login input
- `UserResponse` for returned user data
- `AuthTokensResponse` for auth success responses
- `ApiResponse[T]` as the common response wrapper

---

### 7. Models

Location:

- `app/db/models/user.py`

Purpose:

- define how data is stored in the database
- map Python objects to database tables

This is the SQLAlchemy model layer.

Current `User` model includes fields such as:

- `id`
- `full_name`
- `username`
- `email`
- `password`
- `is_active`
- `is_verified`
- `is_deleted`
- `created_at`
- `updated_at`

---

### 8. Core

Location:

- `app/core/config.py`
- `app/core/security.py`

Purpose:

- application settings
- environment loading
- password hashing and verification

Examples:

- `get_settings()` loads app configuration
- `hash_password()` hashes raw passwords
- `verify_password()` verifies entered passwords

---

### 9. Utils

Location:

- `app/utils/create_access_token.py`
- `app/utils/create_refresh_token.py`
- `app/utils/verify_refresh_token.py`
- `app/utils/generate_username.py`

Purpose:

- hold focused reusable helpers
- avoid duplicating helper logic inside services

---

## Request Flow

Here is the request flow for `POST /auth/register`:

1. Client sends request to the route.
2. Route receives `UserCreate` payload and `Request`.
3. Route gets `AuthController` from dependency injection.
4. Controller calls `AuthService.register_user()`.
5. Service asks `UserRepository` whether the email already exists.
6. Service generates username and hashes password.
7. Repository creates and commits the user.
8. Service creates access token and refresh token.
9. Service stores session values on `request.session`.
10. Service returns `ApiResponse[AuthTokensResponse]`.
11. Route returns the response to the client.

Flow summary:

```text
HTTP Request
  -> Route
  -> Dependency
  -> Controller
  -> Service
  -> Repository
  -> Database
  -> Service
  -> Controller
  -> Route
  -> HTTP Response
```

---

## Why This Architecture Is Useful

### Before layering

If everything is inside `auth.py`, one file ends up handling:

- endpoint definitions
- validation
- SQL queries
- hashing
- session logic
- token logic
- error handling

That becomes hard to maintain.

### After layering

Each layer has one job:

- routes know HTTP
- controllers know where to send the request
- services know the business rules
- repositories know the database

Benefits:

- easier to read
- easier to test
- easier to debug
- easier to reuse logic
- easier to add new features
- easier for teams to work on the code

This is especially useful when the app grows to include:

- chat rooms
- messages
- profile management
- email verification
- password reset
- notifications
- admin features

---

## Configuration

Settings are loaded from `app/core/config.py`.

Important config values currently supported:

- `APP_NAME`
- `APP_VERSION`
- `ENVIRONMENT`
- `API_PREFIX`
- `DEBUG`
- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`

Example `.env` template:

```env
APP_NAME=ContextOS Backend
APP_VERSION=0.1.0
ENVIRONMENT=development
API_PREFIX=/api/v1
DEBUG=true
DATABASE_URL=postgresql://localuser:localpassword@localhost:5432/chatapp_db
SECRET_KEY=change-me-before-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

If your local project is using a different prefix such as `/api`, update `API_PREFIX` in `.env`.

---

## Command Reference

All commands below are intended to be run from the backend root:

```powershell
cd C:\Users\Lokesh Medharametla\OneDrive\Desktop\Chat-app\backend
```

### 1. Create virtual environment

```powershell
python -m venv .venv
```

### 2. Activate virtual environment

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```powershell
pip install -r requirement.txt
```

### 4. Start PostgreSQL with Docker

```powershell
docker compose up -d
```

### 5. Stop PostgreSQL

```powershell
docker compose down
```

### 6. View running containers

```powershell
docker compose ps
```

### 7. View PostgreSQL logs

```powershell
docker compose logs db
```

### 8. Apply migrations

```powershell
alembic upgrade head
```

### 9. Create a new migration

```powershell
alembic revision -m "describe_change"
```

### 10. Create an auto-generated migration

```powershell
alembic revision --autogenerate -m "describe_change"
```

### 11. Roll back one migration

```powershell
alembic downgrade -1
```

### 12. Show current migration version

```powershell
alembic current
```

### 13. Show migration history

```powershell
alembic history
```

### 14. Run the API server

```powershell
uvicorn main:app --reload
```

### 15. Run the API server on a custom host and port

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 16. Quick syntax sanity check

```powershell
python -m compileall app
```

### 17. Run an import sanity check

```powershell
python -c "from app.main import app; print(app.title)"
```

### 18. Check installed packages

```powershell
pip list
```

### 19. Freeze dependencies

```powershell
pip freeze
```

### 20. Open interactive PostgreSQL shell in container

```powershell
docker exec -it chatapp-postgres psql -U localuser -d chatapp_db
```

### 21. Show all tables in PostgreSQL

Run this inside `psql`:

```sql
\dt
```

### 22. Show users table schema in PostgreSQL

Run this inside `psql`:

```sql
\d users
```

---

## Useful API Test Commands

These examples assume the backend is running on port `8000`.

If your `API_PREFIX` is `/api/v1`, use `/api/v1/auth/...`.

If your `API_PREFIX` is `/api`, use `/api/auth/...`.

### Health check

```powershell
curl http://localhost:8000/
```

### Register

```powershell
curl -X POST "http://localhost:8000/api/v1/auth/register" `
  -H "Content-Type: application/json" `
  -d "{\"full_name\":\"Lokesh\",\"email\":\"lokesh@example.com\",\"password\":\"secret123\"}"
```

### Login

```powershell
curl -X POST "http://localhost:8000/api/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"lokesh@example.com\",\"password\":\"secret123\"}"
```

### Refresh token

```powershell
curl -X POST "http://localhost:8000/api/v1/auth/refresh"
```

### Delete account

```powershell
curl -X DELETE "http://localhost:8000/api/v1/auth/delete-account"
```

### Logout

```powershell
curl -X POST "http://localhost:8000/api/v1/auth/logout"
```

Note:

- session-based endpoints depend on the session cookie being preserved by the client
- plain `curl` examples may need cookie handling for refresh, delete-account, and logout

Example with cookie jar:

```powershell
curl -c cookies.txt -b cookies.txt -X POST "http://localhost:8000/api/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"lokesh@example.com\",\"password\":\"secret123\"}"
```

---

## How To Add a New Feature

Example: adding chat room creation

### Step 1. Add schema

Create:

- `app/schemas/room.py`

Define request and response models there.

### Step 2. Add model

Create:

- `app/db/models/room.py`

Define the SQLAlchemy model.

### Step 3. Add repository

Create:

- `app/repositories/room_repository.py`

Put all DB queries there.

### Step 4. Add service

Create:

- `app/services/room_service.py`

Put business rules there.

### Step 5. Add controller

Create:

- `app/controllers/room_controller.py`

Delegate route calls to the service.

### Step 6. Add dependency

Create:

- `app/api/dependencies/room.py`

Wire repository -> service -> controller.

### Step 7. Add route

Create:

- `app/api/routes/rooms.py`

Keep it thin like auth routes.

### Step 8. Register route

Update:

- `app/api/router.py`

Include the new router.

### Step 9. Add migration

```powershell
alembic revision --autogenerate -m "create rooms table"
alembic upgrade head
```

---

## Rules To Follow In This Project

### Route rules

- do not write SQL in routes
- do not commit transactions in routes
- do not hash passwords in routes
- do not create tokens in routes

### Controller rules

- keep controllers thin
- use controllers as the entry point from route to service
- avoid putting database queries directly in controllers

### Service rules

- keep all business logic here
- coordinate repositories and helper functions here
- raise HTTP/business errors here when appropriate

### Repository rules

- keep database access here
- avoid business decisions here
- avoid request/session handling here

### Schema rules

- use Pydantic models for input and output
- keep API shape explicit

---

## Common Problems and Fixes

### Problem: Internal server error on register

Possible causes:

- DB is not running
- migration is not applied
- schema/model mismatch
- token serialization issue

Useful commands:

```powershell
docker compose ps
alembic current
python -m compileall app
```

### Problem: Email already exists after a failed register request

This usually means the DB insert succeeded but something failed after commit.

Check:

- response schema matches model
- token generation works
- session middleware is configured

### Problem: `Database unavailable`

This usually means PostgreSQL is not reachable.

Fix:

```powershell
docker compose up -d
docker compose logs db
```

### Problem: Session not being stored

Check:

- `SessionMiddleware` is enabled in `app/main.py`
- `SECRET_KEY` is set
- `https_only=True` may affect local non-HTTPS behavior depending on client setup

---

## Summary

This backend architecture is designed to keep the codebase clean as the project grows.

Short version:

- `routes` handle HTTP
- `dependencies` build objects
- `controllers` bridge route to service
- `services` contain business logic
- `repositories` handle database access
- `schemas` define API input and output
- `models` define DB structure

If you keep following this pattern, adding modules like rooms, messages, profiles, and notifications will stay organized instead of turning one route file into a large mixed-logic file.
