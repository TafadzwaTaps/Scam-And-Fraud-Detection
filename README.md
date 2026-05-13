# ScamGuard v2 – Scam & Fraud Detection Platform

Full-stack fraud detection with **Supabase PostgreSQL**, **JWT auth**, **NLP analysis**, and **modular FastAPI architecture**.

---

## Project Structure

```
scam-detector/
├── backend/
│   ├── main.py                  # FastAPI app, middleware, static serving
│   ├── config.py                # Environment variable loader
│   ├── database.py              # Supabase client singleton
│   ├── requirements.txt
│   ├── .env.example
│   ├── routers/
│   │   ├── check.py             # POST /api/v1/check  (rate-limited, public)
│   │   ├── report.py            # POST /api/v1/report (JWT required)
│   │   ├── entities.py          # GET /api/v1/entities + admin keywords
│   │   └── auth.py              # POST /api/v1/auth/login|register|logout
│   ├── services/
│   │   ├── nlp_service.py       # Regex + keyword NLP engine
│   │   ├── scoring.py           # Weighted risk scoring model
│   │   └── entity_service.py    # All Supabase data access
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── middleware/
│   │   └── auth.py              # JWT validation (Supabase HS256)
│   └── utils/
│       ├── normalizer.py        # Input normalisation + sanitisation
│       └── logger.py            # Structured logging
├── frontend/
│   └── static/
│       ├── index.html           # Bootstrap 5 SPA
│       ├── style.css
│       └── app.js               # Auth state, check/report, NLP display
└── supabase_migration.sql       # Run once in Supabase SQL Editor
```

---

## Quick Start

### 1. Supabase Setup

1. Go to [supabase.com](https://supabase.com) → your project
2. Open **SQL Editor → New Query**
3. Paste and run `supabase_migration.sql`
4. Collect your keys from **Settings → API**:
   - `SUPABASE_URL` → Project URL
   - `SUPABASE_SERVICE_KEY` → `service_role` secret key *(keep secret)*
   - `SUPABASE_JWT_SECRET` → JWT Settings → JWT Secret

### 2. Environment Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your real keys
```

`.env`:
```
SUPABASE_URL=https://xcjbevotxnrtkpayvlrx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...          # service_role key from Supabase
SUPABASE_JWT_SECRET=your-jwt-secret  # from Supabase JWT Settings
ALLOWED_ORIGINS=http://localhost:8000
CHECK_RATE_LIMIT=30/minute
```

### 3. Install & Run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000**

---

## API Reference

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Create account |
| POST | `/api/v1/auth/login` | — | Get JWT token |
| POST | `/api/v1/auth/logout` | — | Client-side logout |

### Core

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/check` | Optional | Analyse entity for fraud |
| POST | `/api/v1/report` | **Required** | Submit scam report |
| GET | `/api/v1/entities` | — | List top-risk entities |

### Admin

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/admin/keywords` | Required | List NLP keywords |
| POST | `/api/v1/admin/keywords` | Required | Add/update keyword |
| DELETE | `/api/v1/admin/keywords/{word}` | Required | Remove keyword |

---

### POST `/api/v1/check` — Response

```json
{
  "risk_score": 72.5,
  "status": "high_risk",
  "report_count": 4,
  "entity_id": "uuid",
  "nlp_flags": {
    "matched_keywords": ["send money", "gift card"],
    "regex_matches": ["send\\s+money", "urgent(ly)?"],
    "confidence": 0.84
  },
  "sample_reports": [
    { "id": "uuid", "description": "...", "tags": ["irs"], "created_at": "..." }
  ]
}
```

**Status values:** `safe` (0–29) | `suspicious` (30–59) | `high_risk` (60–100)

---

## Risk Scoring Model

```
risk_score = min(100,
    report_count_component    (0–25 pts, log scale)
  + recent_activity           (0–20 pts, reports in last 7 days)
  + nlp_score                 (0–30 pts, keyword + regex)
  + entity_age_penalty        (0–15 pts, new entities = higher risk)
  − duplicate_penalty         (reduces spam inflation)
)
```

---

## NLP Pipeline

1. **Regex patterns** — 25 compiled patterns (`send.*money`, `verify.*account`, etc.)
2. **Keyword matching** — Weighted terms loaded from Supabase `keywords` table (falls back to 23 hardcoded keywords)
3. **Confidence score** — Combined 0–1 value from both signals

To add keywords via API (requires login):
```bash
curl -X POST /api/v1/admin/keywords \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"word": "crypto wallet", "weight": 12}'
```

---

## Deployment on Render

1. Push to GitHub
2. **New → Web Service**

| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

3. Add Environment Variables in Render dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `SUPABASE_JWT_SECRET`
   - `ALLOWED_ORIGINS` → your Render URL

> No Docker needed. Render handles everything.

---

## Security

- JWT validated server-side on every protected request (HS256, Supabase secret)
- One report per user per entity (enforced at DB level via unique constraint)
- Rate limiting on `/check`: 30 req/min per IP (configurable)
- All inputs sanitised and length-capped via Pydantic validators
- Supabase Row Level Security (RLS) enabled on all tables
- No secrets hardcoded — all via environment variables
- Legal safety: reports say "reported X times", never labels anyone a scammer

---

## Health Check

`GET /health` → `{"status": "ok", "version": "2.0.0"}` — use as Render health check URL.
