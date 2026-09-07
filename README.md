# AlphaLens

An AI-powered Binance market intelligence agent. Ask natural-language questions about crypto markets — "Is BTC bullish right now?" — and AlphaLens fetches live Binance data, runs technical analysis, and returns structured insights.

**Hackathon:** Binance Agent OS Mini Hackathon 2026 · **Track:** Agent OS — AI Agent Integration

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript 6, Vite 8, Tailwind CSS 4, shadcn/ui, TanStack Query, React Router |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2, Pydantic 2, pydantic-ai |
| Database | SQLite (aiosqlite) — auto-created, zero config |
| LLM | OpenRouter API (default model: `minimax/minimax-m3:free`) |
| Market Data | Binance REST API (public endpoints, no auth required for market data) |

---

## Prerequisites

- **Python** 3.12 or later
- **Node.js** 22 or later (LTS recommended)
- **npm** (bundled with Node.js)
- **uv** — Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **OpenRouter API key** — free tier available at [openrouter.ai](https://openrouter.ai)

No database installation needed. SQLite is embedded.

---

## Project Structure

```
AlphaLens/
├── backend/
│   ├── app/
│   │   ├── agent/          # AI agent logic, tools, prompts
│   │   ├── api/routes/     # FastAPI route handlers
│   │   ├── auth/           # JWT authentication
│   │   ├── binance/        # Binance REST API client
│   │   ├── core/           # Config, logging, exceptions
│   │   ├── db/             # SQLAlchemy models, database setup
│   │   ├── schemas/        # Pydantic request/response models
│   │   └── main.py         # FastAPI app factory
│   ├── tests/              # pytest test suite
│   ├── pyproject.toml      # Python dependencies
│   ├── uv.lock             # Locked dependencies
│   └── .env                # Environment variables (gitignored)
├── frontend/
│   ├── src/
│   │   ├── api/            # API client functions
│   │   ├── components/     # React components (chat, analysis, UI)
│   │   ├── contexts/       # React contexts (auth)
│   │   ├── hooks/          # Custom hooks (chat streaming, history)
│   │   ├── pages/          # Route pages (Chat, Analyze, Settings, Auth)
│   │   ├── router/         # React Router config
│   │   ├── types/          # TypeScript type definitions
│   │   └── lib/            # Utilities (formatting, cn)
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/BrainlessDip/AlphaLens
cd AlphaLens
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment and install dependencies
uv sync

# Create your .env file
cp .env.example .env   # if no .env.example, create .env manually (see Environment Variables below)
```

Edit `backend/.env` and set at minimum:

```
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
```

### 3. Frontend setup

```bash
cd ../frontend

# Install dependencies
npm install
```

### 4. Start the project

Open **two terminals**:

**Terminal 1 — Backend:**

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

### 5. Open the app

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| API docs (ReDoc) | http://localhost:8000/redoc |

Register an account at http://localhost:5173/register, then log in. The chat and analysis features will work immediately — Binance public market data requires no API keys.

---

## Environment Variables

Create `backend/.env` with these values:

```bash
# Application
APP_ENV=development
LOG_LEVEL=INFO

# Database (SQLite — no install needed)
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# OpenRouter LLM (required — get a key at https://openrouter.ai)
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
OPENROUTER_MODEL=minimax/minimax-m3:free
OPENROUTER_APP_URL=
OPENROUTER_APP_TITLE=

# JWT (change this in production)
JWT_SECRET_KEY=change-me-to-a-long-random-string-at-least-32-chars

# Binance REST API (optional — public market data works without keys)
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_BASE_URL=https://api.binance.com
BINANCE_REQUEST_TIMEOUT=10.0
```

**Required:** `OPENROUTER_API_KEY` — without this the LLM cannot respond.

**Optional:** `BINANCE_API_KEY` / `BINANCE_API_SECRET` — only needed if you extend AlphaLens to access private Binance endpoints. Public market data (prices, klines, order books) works without them.

---

## Available Commands

### Backend

```bash
cd backend

# Run development server with auto-reload
uv run uvicorn app.main:app --reload --port 8000

# Run all tests
uv run pytest tests/ -v

# Run tests (quiet output)
uv run pytest tests/ -q

# Install/update dependencies
uv sync

# Add a new dependency
uv add <package>

# Add a dev dependency
uv add --group dev <package>
```

### Frontend

```bash
cd frontend

# Start development server (http://localhost:5173)
npm run dev

# Type-check and build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

---

## How It Works

```
User question
    ↓
React frontend → POST /api/v1/agent/chat
    ↓
FastAPI backend → authenticate user → invoke AI agent
    ↓
AI agent (pydantic-ai + OpenRouter) → select tools → call Binance REST API
    ↓
Live market data returned → agent analyzes → streams response back
    ↓
React frontend renders streaming analysis with tool activity, market cards, follow-up suggestions
```

The agent can call these Binance tools during a conversation:

| Tool | Binance Endpoint | Purpose |
|------|-----------------|---------|
| `get_ticker` | `GET /api/v3/ticker/price` | Current price |
| `get_24h_stats` | `GET /api/v3/ticker/24hr` | 24h price change, volume |
| `get_klines` | `GET /api/v3/klines` | Candlestick data (1m to 1d) |
| `get_order_book` | `GET /api/v3/depth` | Bid/ask depth |
| `get_recent_trades` | `GET /api/v3/trades` | Recent trade flow |
| `get_exchange_info` | `GET /api/v3/exchangeInfo` | Symbol validation |
| `get_indicators` | Computed from klines | SMA, EMA, RSI, volatility |

---

## Troubleshooting

### Backend won't start

**"ModuleNotFoundError: No module named 'app'"**
You're not in the `backend/` directory. Run `cd backend` first.

**"OPENROUTER_API_KEY not set" or LLM errors**
Make sure `backend/.env` contains a valid `OPENROUTER_API_KEY`. Get a free key at [openrouter.ai](https://openrouter.ai).

**"port 8000 already in use"**
Another process is using the port. Kill it or use a different port:
```bash
uv run uvicorn app.main:app --reload --port 8001
```
If you change the port, also update `FRONTEND_URL` in `.env` if CORS issues arise.

### Frontend won't start

**"Module not found" errors after git pull**
Reinstall dependencies:
```bash
cd frontend
rm -rf node_modules
npm install
```

**API requests fail / CORS errors**
Make sure the backend is running on port 8000. The Vite dev server proxies `/api` requests to `http://localhost:8000` automatically.

### Database issues

**"no such table" errors**
The SQLite database is auto-created on backend startup. If it gets corrupted, delete it and restart:
```bash
rm backend/app.db
# Restart the backend — it recreates the database automatically
```

### Chat returns empty or errors

**LLM not responding**
Check that `OPENROUTER_API_KEY` is valid and the model (`OPENROUTER_MODEL`) is available on OpenRouter. Free models may have rate limits.

**Binance data unavailable**
Binance public API may be temporarily down or rate-limited. Check https://status.binance.com. The health endpoint at `GET /api/v1/health` reports Binance connectivity status.

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/health` | No | Health check + Binance status |
| `POST` | `/api/v1/auth/register` | No | Create account |
| `POST` | `/api/v1/auth/login` | No | Login, returns JWT |
| `GET` | `/api/v1/chats` | Yes | List conversations (search, pagination) |
| `POST` | `/api/v1/chats` | Yes | Create new conversation |
| `GET` | `/api/v1/chats/{id}` | Yes | Get conversation with messages |
| `PATCH` | `/api/v1/chats/{id}` | Yes | Rename conversation |
| `DELETE` | `/api/v1/chats/{id}` | Yes | Delete conversation |
| `POST` | `/api/v1/chats/{id}/share` | Yes | Create read-only share link |
| `GET` | `/api/v1/chats/{id}/shared` | No | Read shared conversation (token required) |
| `POST` | `/api/v1/agent/chat` | Yes | Stream chat with AI agent (SSE) |
| `POST` | `/api/v1/agent/analyze` | Yes | Structured market analysis |

---

## License

This project was created for the Binance Agent OS Mini Hackathon 2026.

---

---

# Technical Design and Implementation Paper

The remainder of this document describes the architecture, design decisions, and implementation details of AlphaLens.

---

# Abstract

AlphaLens is an AI-powered market intelligence agent designed to help users understand cryptocurrency markets through natural-language interaction.

Instead of exposing users to a large collection of exchange APIs, dashboards, indicators, and technical terminology, AlphaLens provides a conversational interface where users can ask questions such as:

> "Is BTC looking bullish right now?"

> "What is happening with ETH?"

> "Compare BTC and ETH market conditions."

> "What market data supports your conclusion?"

The core idea is not to build another chatbot that simply generates financial text.

AlphaLens is an actual tool-using AI agent.

The agent receives a user's question, determines what information is required, accesses the appropriate Binance capabilities through Binance Agent OS, interprets the returned market information, and produces a structured explanation.

Binance Agent OS provides the connection between AI agents and Binance capabilities, exposing market-data and trading while providing permission controls over what an agent can access.

AlphaLens focuses primarily on market intelligence and analysis rather than autonomous trading. This allows the project to demonstrate the core agent architecture while keeping the system focused, understandable, and safer.

---

# 1. Introduction

Traditional cryptocurrency market applications generally expose information through dashboards.

Users must manually inspect:

* current price
* price changes
* volume
* order books
* candlesticks
* market trends
* technical indicators
* multiple trading pairs
* account information

The information exists, but understanding it requires the user to combine many different pieces of data.

AlphaLens approaches the problem differently.

Instead of asking:

> "Which API endpoint should I call?"

the user asks:

> "What's happening with Bitcoin?"

The AI agent determines what information it needs.

This creates an agentic workflow:

```text
User Question
      ↓
AI Agent
      ↓
Determine required information
      ↓
Select Binance tools
      ↓
Call Binance API
      ↓
Receive live Binance data
      ↓
Analyze the information
      ↓
Generate explanation
      ↓
User
```

The important distinction is that AlphaLens does not hard-code one API call for every question.

The AI agent decides how to investigate the question.

---

# 2. What Is Binance Agent OS?

Binance Agent OS is a platform and toolkit for connecting AI agents to Binance services.

According to Binance, Agent OS allows AI agents to access capabilities including market data, account information, and supported trading functionality.

Binance currently provides these capabilities through a standardized API, while other Agent OS integrations cover additional functionality.

---

# 3. What Is the AI Agent?

The AI agent is the central component of AlphaLens.

It is important to distinguish the AI agent from Binance Agent OS.

They are different concepts.

### AI Agent

The AI agent is the reasoning layer.

It:

* understands the user's request
* determines what information is necessary
* selects appropriate tools
* calls those tools
* interprets their results
* reasons over the collected information
* produces the final response

### Binance Agent OS

Agent OS provides the Binance-side infrastructure that allows an authorized AI agent to interact with Binance capabilities.

Therefore:

```text
LLM
= Brain

Binance Agent OS
= Binance agent infrastructure

FastAPI
= Application backend / Orchestrator

React
= User interface

Binance
= Data and execution infrastructure
```

The interesting part of AlphaLens is the interaction between these components.

---

# 4. AlphaLens Architecture

The high-level architecture is:

```text
                         ┌──────────────────────┐
                         │        User          │
                         │  Natural Language    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     React + TS       │
                         │      Frontend        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │       Backend        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │          AI AGENT            │
                    │                              │
                    │ Understand                   │
                    │ Plan                         │
                    │ Select tools                 │
                    │ Call tools                   │
                    │ Analyze results               │
                    │ Generate response             │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │         Binance API          │
                    │                              │
                    │ Structured tool access       │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │       Binance       │
                         │ Market Infrastructure│
                         └──────────────────────┘
```

The architecture intentionally separates responsibilities.

---

# 5. The Agent Loop

The central mechanism of AlphaLens is the agent loop.

A normal chatbot works approximately like this:

```text
Question
   ↓
LLM
   ↓
Answer
```

AlphaLens works differently:

```text
Question
   ↓
LLM
   ↓
Does external information need to be retrieved?
   ↓
Yes
   ↓
Select tool
   ↓
Call Binance API
   ↓
Receive result
   ↓
Interpret result
   ↓
Need more information?
   ├── Yes → Call another tool
   │
   └── No
        ↓
     Analyze
        ↓
     Answer
```

This is what makes the application agentic.

The model is not merely generating an answer from its existing knowledge.

It can gather current information before answering.

---

# 6. Example: "Is BTC Bullish?"

Suppose a user asks:

```text
Is BTC looking bullish right now?
```

AlphaLens first interprets the question.

The agent may determine that it needs information such as:

```text
BTC current price
24h price movement
24h volume
market activity
recent market structure
```

The agent then selects appropriate Binance tools.

Conceptually:

```text
User
 │
 │ "Is BTC looking bullish right now?"
 ▼
AI Agent
 │
 ├── Need current BTC data
 │
 ├── Select market-data tools
 │
 ▼
Binance API
 │
 ├── price data
 ├── volume data
 └── other relevant market information
 │
 ▼
AI Agent
 │
 ├── interpret data
 ├── compare signals
 ├── identify conflicting evidence
 └── determine confidence
 │
 ▼
Final response
```

The important point is that the agent decides which tools are relevant instead of the frontend manually executing a fixed sequence.

---

# 8. Tool Discovery

AlphaLens does not permanently hard-code the number or ordering of Binance tools.

Instead, the client can discover the tools exposed by Binance.

Conceptually:

```text
API Server
     │
     │ tools/list
     ▼
Available Tools
     │
     ├── Market data
     ├── Account information
     ├── Trading capabilities
     └── Other permitted capabilities
```

The agent can then select tools based on their names and schemas.

This is important because the server-side tool catalogue can evolve.

The application should therefore treat Binance's tool catalogue as the source of truth.

---

# 9. Authentication Architecture

AlphaLens needs two different authentication layers.

### Layer 1 — AlphaLens Authentication

This identifies the user inside the AlphaLens application.

For example:

```text
User
 ↓
AlphaLens JWT
 ↓
FastAPI
```

### Layer 2 — Binance Agentic OAuth

This authorizes AlphaLens to access Binance on behalf of that user.

```text
AlphaLens User
      ↓
Binance OAuth
      ↓
Binance authorization
      ↓
Binance access token
      ↓
Binance API
```

These should never be treated as the same credential.

The AlphaLens JWT identifies the application user.

The Binance OAuth token authorizes access to that user's Binance Agentic connection.

---

# 10. Binance OAuth Flow

The Binance Agentic OAuth integration uses an Authorization Code flow with PKCE.

The discovered Binance authorization metadata supports:

```text
response_type:
code

grant_type:
authorization_code

PKCE:
S256
```

The token endpoint authentication method is currently:

```text
none
```

The flow is therefore:

```text
AlphaLens User
      │
      │ Click "Connect Binance"
      ▼
FastAPI
      │
      ├── Generate state
      ├── Generate code_verifier
      ├── Generate code_challenge
      └── Store OAuth transaction
      │
      ▼
Binance Authorization
      │
      │ User authenticates
      │ User approves access
      ▼
AlphaLens Callback
      │
      ├── Validate state
      ├── Recover user
      └── Exchange code
      │
      ▼
Binance Token Endpoint
      │
      ▼
Access Token
Refresh Token
      │
      ▼
Secure server-side storage
```

The current authorization direction also emphasizes OAuth 2.1-style authorization, PKCE, and Client ID Metadata Documents.

---

# 11. Client ID Metadata Document

Instead of inventing a traditional Binance OAuth client ID, AlphaLens uses a Client ID Metadata Document URL.

Conceptually:

```text
BINANCE_OAUTH_CLIENT_METADATA_URL
        │
        ▼
https://alphalens.example.com/
.well-known/
oauth-client-metadata.json
```

The endpoint provides metadata describing AlphaLens as an OAuth client.

For example:

```json
{
  "client_name": "AlphaLens",
  "grant_types": [
    "authorization_code",
    "refresh_token"
  ],
  "response_types": [
    "code"
  ],
  "token_endpoint_auth_method": "none",
  "application_type": "web",
  "client_id": "https://alphalens.example.com/.well-known/oauth-client-metadata.json",
  "client_uri": "https://alphalens.example.com",
  "redirect_uris": [
    "https://alphalens.example.com/api/v1/binance/auth/callback"
  ]
}
```

The exact metadata values must follow the behavior accepted by Binance rather than being invented.

The critical concept is:

```text
client_id
=
metadata document URL
```

rather than a traditional secret-based client registration.

The OAuth 2.1 specification specifically describes a shift toward Client ID Metadata Documents as the preferred registration model.

---

# 12. PKCE Security

AlphaLens uses PKCE to protect the OAuth authorization flow.

The backend generates a random:

```text
code_verifier
```

and derives:

```text
code_challenge =
BASE64URL(
    SHA256(code_verifier)
)
```

The authorization request sends:

```text
code_challenge
code_challenge_method=S256
```

The original verifier remains server-side.

After Binance returns the authorization code, AlphaLens sends:

```text
code
code_verifier
```

to the token endpoint.

The browser never receives the verifier as application data.

This protects the authorization-code exchange from code interception.

---

# 13. OAuth State Protection

PKCE protects the authorization-code exchange, while OAuth state protects the application authorization transaction against CSRF and replay.

Every connection attempt generates a cryptographically random state.

The backend stores:

```text
state
user_id
code_verifier
created_at
expires_at
consumed
```

Conceptually:

```text
User A
  │
  ├── state = random_A
  └── verifier = verifier_A

User B
  │
  ├── state = random_B
  └── verifier = verifier_B
```

When Binance redirects back:

```text
callback?code=...&state=random_A
```

the backend verifies:

```text
state exists
state belongs to current transaction
state belongs to correct user
state has not expired
state has not been consumed
```

Only then is the authorization code exchanged.

---

# 14. Multi-User Token Isolation

A critical security requirement is that every AlphaLens user must have an independent Binance connection.

The database relationship is conceptually:

```text
User A
 └── BinanceConnection A
      ├── access_token
      ├── refresh_token
      └── expires_at

User B
 └── BinanceConnection B
      ├── access_token
      ├── refresh_token
      └── expires_at
```

There must never be:

```text
GLOBAL_BINANCE_ACCESS_TOKEN
```

The backend determines the current AlphaLens user first.

Then:

```text
current_user
      ↓
BinanceConnection(user_id)
      ↓
user's token
      ↓
Binance API
```

This guarantees that one user cannot accidentally execute API requests using another user's Binance authorization.

---

# 15. Token Storage

Binance OAuth tokens are sensitive credentials.

They are never returned to the frontend.

They are never stored in:

```text
localStorage
sessionStorage
React state
URL parameters
browser cookies created specifically for raw Binance tokens
```

The frontend only receives safe connection information.

For example:

```json
{
  "connected": true,
  "expires_at": "2026-09-03T12:30:00Z",
  "needs_reauth": false
}
```

The actual token remains on the backend.

---

# 16. Database Model

AlphaLens stores the Binance connection separately from the application user.

Conceptually:

```text
binance_oauth_connections

id
user_id
access_token
refresh_token
expires_at
created_at
updated_at
```

A relationship exists:

```text
User 1 ─────────── 1 BinanceOAuthConnection
```

The implementation follows the existing SQLAlchemy and database architecture of the FastAPI application.

No unnecessary authentication infrastructure is introduced.

---

# 17. Token Refresh

Access tokens expire.

Therefore AlphaLens supports refresh tokens when Binance provides them.

Before an API request:

```text
Is access token still valid?
        │
        ├── Yes
        │    ↓
        │  API request
        │
        └── No
             ↓
          Refresh token
             ↓
          New access token
             ↓
          Update database
             ↓
          API request
```

The backend also handles the case where Binance returns:

```text
401 Unauthorized
```

The recovery mechanism is:

```text
API request
    ↓
401
    ↓
Refresh token
    ↓
Update stored credentials
    ↓
Retry original API request once
```

There is deliberately no infinite retry loop.

---

# 20. FastAPI Backend

FastAPI acts as the application's orchestration layer.

Current API structure:

```text
GET  /api/v1/health

POST /api/v1/agent/chat
POST /api/v1/agent/analyze

GET  /api/v1/binance/auth
GET  /api/v1/binance/auth/callback
GET  /api/v1/binance/auth/status
POST /api/v1/binance/auth/logout
```

The backend responsibilities are:

```text
Authentication
OAuth
Token management
API communication
Agent orchestration
API responses
Error handling
```

The backend intentionally prevents the frontend from directly communicating with Binance using sensitive credentials.

---

# 21. React Frontend

The frontend is responsible for the user experience.

Technology:

```text
React
TypeScript
Vite
Tailwind CSS
shadcn/ui
React Router
TanStack Query
```

The application contains several major areas.

### Dashboard

Provides:

* project introduction
* market intelligence entry point
* quick questions
* Binance connection status

### Chat

Allows users to interact naturally with the AI agent.

Example:

```text
User:
What's happening with BTC?

Agent:
I'll check the current Binance market conditions...
```

### Market Analysis

Provides a structured analysis interface.

Example:

```text
Symbol:
BTCUSDT

Question:
Is BTC bullish right now?
```

The result can contain:

```text
Current Price
Price Change
24h Volume
Market Observations
AI Analysis
Confidence & Limitations
```

### Settings

Provides:

```text
Binance connection
Connection status
Application status
Logout/disconnect
```

---

# 22. Chat Architecture

The chat request travels through the following path:

```text
React
   ↓
POST /api/v1/agent/chat
   ↓
FastAPI
   ↓
Authenticated user
   ↓
AI Agent
   ↓
Binance API
   ↓
Tool results
   ↓
AI reasoning
   ↓
Streaming response
   ↓
React chat UI
```

The frontend does not need to understand Binance's internal API tools.

It only understands the agent interface.

This keeps the frontend simple.

---

# 23. Structured Market Analysis

AlphaLens also exposes a structured analysis endpoint.

Conceptually:

```text
POST /api/v1/agent/analyze
```

with:

```json
{
  "symbol": "BTCUSDT",
  "question": "Is BTC currently bullish?"
}
```

The backend then:

```text
Receive symbol
      ↓
Receive question
      ↓
AI Agent
      ↓
Determine required market data
      ↓
Binance API
      ↓
Collect relevant information
      ↓
Analyze
      ↓
Return structured result
```

The structured response contains:

```text
symbol
current_price
price_change
volume_info
market_observations
agent_analysis
confidence_and_limitations
```

This makes the agent's reasoning useful for both conversational and structured interfaces.

---

# 24. Confidence and Limitations

Financial analysis is inherently uncertain.

AlphaLens therefore does not present AI-generated market interpretation as guaranteed truth.

The agent should distinguish between:

```text
Observed data
```

and:

```text
Interpretation
```

For example:

```text
Observed:
BTC is up over the selected period and trading volume has increased.

Interpretation:
These conditions are consistent with short-term bullish momentum.

Limitation:
This does not guarantee continued upward movement.
```

The system should avoid presenting probabilistic analysis as certainty.

---

# 25. No Fake Data

A core product principle is:

> If AlphaLens says it is analyzing the current market, the data should come from Binance or another explicitly identified live source.

The system does not fabricate:

* current prices
* volume
* market conditions
* trading activity
* account information

The agent is only allowed to reason from the information available to it.

---

# 26. Security Model

Because AlphaLens interacts with financial infrastructure, security is a first-class design requirement.

The system protects:

### Application authentication

Users must be authenticated before accessing their Binance connection.

### OAuth

Protected using:

```text
Authorization Code
PKCE S256
State
```

### Token storage

Tokens remain server-side.

### User isolation

Every token is associated with an application user.

### API requests

Authenticated using:

```http
Authorization: Bearer <access_token>
```

### Logging

The application never logs:

```text
access_token
refresh_token
authorization_code
code_verifier
Authorization header
client secrets
```

### Retry behavior

401 recovery performs at most one refresh and retry.

---

# 27. Permission Model

Binance Agent OS provides permission controls for connected agents.

Binance describes Agent OS as permissioned infrastructure where users can control what an agent can access and can disconnect agents or use an emergency stop.

AlphaLens therefore follows a least-privilege approach.

For the initial market-intelligence experience, the agent should only request or use capabilities necessary for analysis.

The project does not require autonomous trading to demonstrate the agent architecture.

This keeps the scope focused:

```text
Market Intelligence
       ↓
Current data
       ↓
Reasoning
       ↓
Explanation
```

rather than:

```text
Market Intelligence
       ↓
Autonomous trading
       ↓
Financial execution
```

---

# 28. Why We Are Not Building a Traditional Trading Bot

AlphaLens is intentionally different from a traditional trading bot.

A traditional trading bot might work like:

```text
if RSI < 30:
    buy()
```

AlphaLens instead allows natural-language reasoning:

```text
User:
Why does BTC currently look weak?

Agent:
1. Determine relevant data
2. Retrieve current data
3. Compare signals
4. Identify conflicting evidence
5. Explain the conclusion
```

The objective is intelligence and interaction rather than simply implementing a fixed strategy.

---

# 29. Agent Decision Process

The agent can be understood as a decision pipeline.

### Step 1 — Understand

Parse the user's request.

```text
"What is happening with BTC?"
```

becomes:

```text
Asset = BTC
Intent = market analysis
Time context = current
```

### Step 2 — Plan

Determine what information is needed.

```text
Need:
- current price
- recent movement
- volume
- potentially additional market information
```

### Step 3 — Select Tools

Choose appropriate Binance API tools.

### Step 4 — Execute

Call those tools.

### Step 5 — Observe

Receive their responses.

### Step 6 — Reason

Interpret the information.

### Step 7 — Respond

Produce a concise explanation.

This cycle can repeat if more information is required.

---

# 30. Agent Memory

AlphaLens does not need permanent memory for every conversation.

The agent can operate using:

```text
Current user message
+
Relevant conversation context
+
Live Binance data
```

This reduces unnecessary storage of sensitive information.

If conversation history is stored, it should be separated from Binance credentials.

---

# 31. Error Handling

The system handles failures at multiple layers.

### OAuth errors

Examples:

```text
Invalid state
Expired state
Authorization denied
Missing authorization code
Token exchange failed
```

### Binance errors

Examples:

```text
Unauthorized
Rate limited
Service unavailable
Invalid tool request
```

### API errors

Examples:

```text
Initialization failure
Tool not found
Invalid arguments
API error
```

### AI errors

Examples:

```text
Model unavailable
Tool selection failure
Malformed tool arguments
```

The user should receive a useful error message without exposing internal credentials or stack traces.

---

# 32. Testing Strategy

Testing is divided into several layers.

## Unit Tests

Test:

```text
PKCE generation
OAuth state generation
state expiration
state consumption
token parsing
token refresh
API request construction
API error handling
```

## Integration Tests

Mock Binance endpoints and verify:

```text
authorization
callback
token exchange
refresh
API initialization
tool discovery
tool invocation
```

## Security Tests

Verify:

```text
tokens are never returned
tokens are never logged
users cannot access each other's tokens
state cannot be reused
expired state is rejected
401 cannot trigger infinite retries
```

## Frontend Tests

Verify:

```text
routes
authentication state
chat streaming
loading states
errors
OAuth callback
responsive UI
```

---

# 33. End-to-End Flow

The complete AlphaLens experience is:

```text
                    USER
                      │
                      ▼
             ┌─────────────────┐
             │   React / UI    │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │     FastAPI     │
             └────────┬────────┘
                      │
             ┌────────┴─────────┐
             │                  │
             ▼                  ▼
       Application          Binance OAuth
       Authentication             │
             │                    ▼
             │             Binance Account
             │                    │
             │                    ▼
             │             OAuth Tokens
             │                    │
             └─────────┬──────────┘
                       │
                       ▼
                 ┌─────────────┐
                 │  AI AGENT   │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ Binance API │
                 └──────┬──────┘
                        │
                        ▼
                    BINANCE
                        │
                        ▼
                   Market Data
                        │
                        ▼
                 AI Interpretation
                        │
                        ▼
                    Response
                        │
                        ▼
                      USER
```

---

# 34. Example Complete Interaction

### User

```text
Is BTC bullish right now?
```

### Agent

First determines:

```text
Intent:
Current BTC market analysis
```

Then decides it needs current Binance market information.

### Tool layer

The agent calls the appropriate Binance API tools.

### Binance

Returns current market information.

### Agent

Analyzes:

```text
price movement
volume
market activity
other relevant observations
```

### Agent response

The final answer might look conceptually like:

```text
BTC currently shows moderately bullish short-term conditions.

The main supporting signals are positive recent price movement
and elevated trading activity.

However, the evidence is not conclusive because short-term momentum
can reverse quickly.

Confidence: Moderate.
```

The important part is that the response is based on live tool results rather than fabricated market information.

---

# 35. Why This Is an Agent Rather Than a Chatbot

This distinction is central to the project.

A chatbot:

```text
User
 ↓
LLM
 ↓
Text
```

AlphaLens:

```text
User
 ↓
LLM
 ↓
Reason about required information
 ↓
Select external tools
 ↓
Call tools
 ↓
Observe results
 ↓
Reason again
 ↓
Generate answer
```

The agent can therefore interact with an external environment.

This follows the fundamental agentic model where AI agents use structured tools to interact with external services.

---

# 36. Why FastAPI?

FastAPI provides a lightweight orchestration layer between the frontend, AI model, OAuth system, database, and Binance API.

It provides:

* async request handling
* dependency injection
* Pydantic validation
* API documentation
* clean route separation
* compatibility with Python AI tooling

The backend architecture remains simple:

```text
Routes
  ↓
Services
  ↓
Database / API / AI
```

This avoids putting business logic directly inside frontend components.

---

# 37. Why React and TypeScript?

React provides the interactive interface while TypeScript provides type safety.

The UI is divided into reusable components:

```text
Layout
Navigation
Chat
Message
MarketAnalysis
ConnectionStatus
Settings
LoadingState
ErrorState
```

The frontend communicates only with the AlphaLens API.

It does not directly manage Binance OAuth tokens.

---

# 38. Deployment Architecture

A production deployment can use:

```text
                 Internet
                    │
                    ▼
             ┌─────────────┐
             │ Reverse Proxy│
             └──────┬──────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
       React               FastAPI
       Frontend              │
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
                 Database          Binance API
                                      │
                                      ▼
                                   Binance
```

The OAuth client metadata endpoint must be publicly reachable in production.

The configured redirect URI must correspond exactly to the deployed callback endpoint.

---

# 39. Configuration

Deployment-specific settings are provided through environment variables.

Conceptually:

```text
BINANCE_OAUTH_AUTHORIZATION_URL=https://accounts.binance.com/agentic-oauth/authorize

BINANCE_OAUTH_TOKEN_URL=https://accounts.binance.com/oauth-agentic/token

BINANCE_OAUTH_CLIENT_METADATA_URL=https://your-domain.com/.well-known/oauth-client-metadata.json

BINANCE_OAUTH_REDIRECT_URI=https://your-domain.com/api/v1/binance/auth/callback
```

The application does not hard-code deployment URLs.

No traditional Binance API secret is required for this Agentic OAuth architecture unless Binance's actual protocol requires otherwise.

---

# 40. Important Design Principle: Don't Guess Binance Protocol Behavior

Because Agent OS and Binance's API capabilities are actively evolving, AlphaLens does not assume undocumented behavior.

Whenever protocol behavior is unclear, the implementation checks:

```text
OAuth metadata
Protected Resource metadata
Binance documentation
Actual server behavior
```

This is particularly important for:

```text
transport
redirect URI rules
client metadata
scopes
token refresh
tool schemas
```

The official Binance endpoint and current protocol metadata are treated as authoritative sources.

---

# 41. Future Extensions

The architecture allows AlphaLens to grow without redesigning the entire system.

Potential future capabilities include:

### Portfolio Intelligence

```text
Analyze my portfolio.
```

### Risk Analysis

```text
What are the biggest risks in my current positions?
```

### Market Monitoring

```text
Alert me when BTC conditions change significantly.
```

### Multi-Asset Analysis

```text
Compare BTC, ETH and SOL.
```

### Trading Assistance

With explicit permissions:

```text
Prepare a trade based on my strategy.
```

Actual trade execution should remain separately permissioned and protected.

Binance Agent OS itself is designed around permissioned agent access, allowing users to control capabilities and revoke access.

---

# 42. Future Agent Architecture

The long-term architecture could become:

```text
                        AlphaLens Agent
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
        Market Data       Portfolio         Risk Engine
             │                │                │
             └────────────────┼────────────────┘
                              │
                              ▼
                       Decision Engine
                              │
                              ▼
                       User Approval
                              │
                              ▼
                       Binance Agent OS
                              │
                              ▼
                           Binance
```

The same agent architecture can support increasingly complex workflows while preserving permission boundaries.

---

# 43. Project Philosophy

AlphaLens follows five principles.

## 1. Ask, Don't Navigate

Users should be able to ask questions instead of manually navigating dashboards.

## 2. Data Before Conclusions

The agent should retrieve relevant information before making claims about the current market.

## 3. Tools Before Hallucinations

When live information is required, the agent should use tools rather than relying on stale model knowledge.

## 4. Permissions Before Actions

Financial actions should always respect explicit authorization and permission boundaries.

## 5. Explain Uncertainty

The agent should distinguish observations from interpretations and communicate limitations.

---

# 44. Security Philosophy

The system follows a simple rule:

> The AI should have only the access it needs to perform its job.

The architecture therefore separates:

```text
User identity
        ≠
Binance authorization
        ≠
AI reasoning
        ≠
API transport
```

Each layer has a clear responsibility.

This makes the system easier to audit, test, and extend.

---

# 45. Final Architecture Summary

AlphaLens can be summarized as:

```text
┌───────────────────────────────────────────────────┐
│                     USER                          │
│                                                   │
│ "Is BTC bullish right now?"                       │
└───────────────────────┬───────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                 REACT FRONTEND                    │
│                                                   │
│ Chat / Analysis / Settings                        │
└───────────────────────┬───────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                    FASTAPI                        │
│                                                   │
│ Authentication / API / Agent orchestration        │
└───────────────────────┬───────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                   AI AGENT                        │
│                                                   │
│ Understand → Plan → Select → Call → Observe       │
│                         ↑                         │
│                         └────── Reason ───────────┤
└───────────────────────┬───────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│              BINANCE API                          │
│                                                   │
│ Structured external tools                         │
└───────────────────────┬───────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                    BINANCE                        │
│                                                   │
│ Live market/account capabilities                   │
└───────────────────────────────────────────────────┘
```

---

# 46. Conclusion

AlphaLens demonstrates how an AI application can move beyond simple text generation and become a genuine tool-using agent.

The project combines:

```text
LLM
+
Agent reasoning
+
Binance Agent OS
+
OAuth
+
FastAPI
+
React
```

The AI model acts as the reasoning engine.

Binance provides structured access to market data and trading capabilities.

OAuth provides user authorization.

FastAPI provides secure orchestration and credential isolation.

React provides the user-facing experience.

Together they form an architecture in which a user can ask a natural-language question, the agent can determine what information it needs, retrieve that information from Binance, reason over the results, and return an understandable answer.

The central innovation is therefore not simply:

> "AI that talks about crypto."

It is:

> **An AI agent that can investigate the live market through Binance's agent infrastructure and turn raw exchange capabilities into useful, natural-language market intelligence.**

That is the core of AlphaLens.
