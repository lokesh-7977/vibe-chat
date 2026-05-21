# ContextOS Backend Challenge

## Hiring Lens

You are applying for an AI Engineer role. I am reviewing this as both a Principal Software Engineer and a VP of Engineering.

I am not looking for a toy chatbot or a CRUD demo with an LLM bolted on top. I want to see whether you can design and implement a backend that feels like the foundation of a real product:

- multi-tenant
- observable
- secure
- extensible
- AI-native
- production-aware

The strongest submissions show good product judgment, backend fundamentals, and mature AI systems thinking.

## Product Vision

Build **ContextOS**, an AI-native team communication platform for modern engineering and business teams.

At a product level, think of it as:

- Slack for realtime collaboration
- Notion AI for team knowledge
- Perplexity-style retrieval across internal context
- an AI operations layer that can reason over conversations, documents, tasks, and long-term memory

The platform should allow teams to chat, collaborate in rooms, upload files, search by meaning, and invoke AI agents that understand conversation history, documents, prior decisions, and shared team context.

## What I Want To Evaluate

I am primarily looking for evidence of strength in these areas:

1. Backend architecture
2. API design quality
3. Data modeling
4. Realtime systems thinking
5. Retrieval and memory design
6. AI workflow orchestration
7. Security and access control
8. Production readiness
9. Tradeoff awareness
10. Clear technical communication

## Core Problem Statement

Design and implement the backend for a realtime, AI-native collaboration platform where:

- users can communicate in 1:1 chats and shared rooms
- rooms contain persistent context, members, documents, decisions, and tasks
- AI agents can answer questions using room history and uploaded documents
- semantic search works across conversations and knowledge artifacts
- long-term memory is controllable and scoped to user, room, project, or organization
- the system is designed as if it could grow into a production service

## Functional Requirements

### 1. Identity and Access

Support:

- user registration and login
- JWT-based auth
- refresh tokens
- organization and room membership
- role-based access control

At minimum, model roles such as:

- admin
- member
- viewer

The backend should make permission checks explicit, especially for:

- room access
- document access
- AI context access
- admin analytics endpoints

### 2. Realtime Collaboration

Implement a realtime communication layer for:

- direct messages
- group rooms
- typing indicators
- presence or online status
- message history retrieval
- threaded replies
- reactions
- message edits and deletes

The key goal is not just pushing messages over sockets. I want to see whether your backend models conversation state like a real system.

### 3. AI Assistant Per Room

Each room should support an AI assistant that can respond to prompts such as:

- `@ai summarize the last 100 messages`
- `@ai what decisions did we make yesterday?`
- `@ai create tasks from this conversation`
- `@ai find where we discussed payment gateway failures`
- `@ai answer using uploaded documents only`

Strong implementations separate:

- user message handling
- tool selection or intent classification
- retrieval
- prompt assembly
- response generation
- persistence of AI runs and outputs

### 4. Semantic Retrieval

Use vector search to support retrieval across chat and documents.

Expected capabilities:

- search by meaning, not just keywords
- retrieve similar prior messages
- ground AI answers in room context
- support questions such as:
  - "Find the discussion about OAuth bugs"
  - "What did Lokesh say about deployment?"
  - "Where did we decide to postpone the billing migration?"

If using PostgreSQL, `pgvector` is the preferred direction.

### 5. Document-Aware RAG

Users should be able to upload PDFs, markdown files, or other text-heavy documents and query them conversationally.

Suggested pipeline:

1. Upload document
2. Extract text
3. Chunk content
4. Generate embeddings
5. Store chunks and metadata
6. Retrieve relevant chunks during AI calls
7. Return grounded answers with source references

The important part is not only ingestion. It is how the backend makes those documents useful inside room context.

### 6. Memory System

Add editable memory scoped to:

- user
- room
- project
- organization

Examples:

- this room is about frontend architecture
- this project uses FastAPI and Next.js
- this team prefers short release summaries

Memory should be:

- inspectable
- updatable
- deletable
- clearly scoped

If the AI remembers something, users must have a way to control it.

### 7. Task and Decision Extraction

AI should be able to derive structured outputs from conversations, including:

- action items
- owners
- due dates
- meeting summaries
- decision logs

Persist these artifacts so they become first-class product data, not just transient model output.

### 8. Admin and Observability Endpoints

Expose backend support for an admin dashboard that can report on:

- active users
- rooms
- document volume
- AI requests
- token usage
- failed runs
- message volume
- cost tracking

This is a strong signal of product maturity.

## Recommended Tech Stack

Use this as the default direction unless you have a strong reason to justify alternatives.

### Backend

- FastAPI
- Python
- SQLAlchemy or SQLModel
- PostgreSQL
- pgvector
- Redis
- Socket.IO or WebSocket-based realtime layer
- LangGraph for agent workflows
- LangChain only where it helps rather than as architecture glue

### AI

- OpenAI or Gemini APIs
- embedding pipeline for messages and documents
- streaming model responses

### Infra

- Docker
- Docker Compose
- background jobs with Celery, RQ, or an equivalent worker model
- CI with GitHub Actions

## Suggested Data Model

Your schema should cover at least these concepts:

- `users`
- `organizations`
- `rooms`
- `room_members`
- `messages`
- `message_threads`
- `message_reactions`
- `documents`
- `document_chunks`
- `embeddings`
- `ai_runs`
- `ai_memories`
- `tasks`
- `decisions`
- `notifications`
- `audit_logs`

You do not need every table fully implemented on day one, but I expect the model shape to be intentional.

## Architecture Expectations

I expect the backend to be organized in a way that can scale. A strong project usually separates:

- API routers
- domain services
- data access or repositories
- models and schemas
- AI orchestration workflows
- infrastructure concerns such as config, caching, logging, and background processing


## Non-Functional Requirements

Your submission should demonstrate awareness of:

- clean error handling
- rate limiting
- structured logging
- request tracing or observability hooks
- idempotency where relevant
- pagination
- input validation
- secure secrets handling
- deployment configuration
- testability

Bonus points for:

- streaming AI responses
- cancellation or retry handling for AI runs
- backpressure awareness
- caching strategies
- multi-tenant boundary protection

## Evaluation Rubric

I will evaluate the work roughly in this order:

### Excellent

- clear modular backend architecture
- strong schema design
- thoughtful AI workflow orchestration
- grounded retrieval strategy
- good security defaults
- production-aware error handling and observability
- convincing explanation of tradeoffs

### Weak

- everything placed in one file
- AI calls with no retrieval or memory design
- vague schemas
- no permission model
- no persistence strategy for AI outputs
- no tests or no path to testing
- no explanation of operational concerns

## MVP Delivery Order

If you are building iteratively, I would recommend this order:

1. Auth and user model
2. Rooms and memberships
3. Realtime messaging and pagination
4. AI run model and streaming responses
5. Message embeddings and semantic search
6. Document ingestion and RAG
7. LangGraph workflow orchestration
8. Memory system
9. Task and decision extraction
10. Admin analytics and production hardening

## What A Strong Candidate Says In Review

The best candidates can explain the system like this:

> I built an AI-native collaboration backend where realtime messaging, semantic retrieval, document-aware RAG, and room-scoped agents work together. The architecture separates API, service, persistence, and AI workflow layers. The system supports room permissions, streaming responses, editable memory, vector search over messages and documents, and persistent AI artifacts such as tasks, summaries, and decision logs. I also designed for operational realism with background jobs, structured logging, caching, and deployable service boundaries.

## Resume Version

Built a production-grade AI-native collaboration backend with realtime messaging, semantic retrieval, document-aware RAG, room-scoped AI agents, editable memory, task extraction, and observability using FastAPI, PostgreSQL, pgvector, Redis, LangGraph, and Docker.

## Final Guidance

Do not build "just a chatbot."

Build the backend like you are creating the first serious version of a company product that has:

- realtime collaboration
- durable context
- retrieval-backed intelligence
- explicit permissions
- operational maturity

That is the difference between a portfolio demo and an interview-winning AI engineering system.
