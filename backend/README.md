# ScamGuard – Scam & Fraud Detection

A production-ready FastAPI + Bootstrap web application that lets users **check** phone numbers, URLs, and message text for fraud signals, and **report** scams to build a community-powered database.

---

## Project Structure

```
scam-detector/
├── backend/
│   ├── main.py          # FastAPI app entry point + static file serving
│   ├── routers.py       # API endpoints (/report, /check, /entities)
│   ├── models.py        # SQLAlchemy ORM models (Entity, Report)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── detection.py     # Keyword detection + risk scoring engine
│   ├── database.py      # DB engine, session factory, init_db()
│   └── requirements.txt
└── frontend/
    ├── index.html       # Single-page Bootstrap UI
    └── static/
        ├── css/style.css
        └── js/app.js
```

---

## Features

| Feature | Detail |
|---|---|
| **Check endpoint** | `POST /api/v1/check` – Returns risk score 0–100, status, keyword hits, sample reports |
| **Report endpoint** | `POST /api/v1/report` – Stores community reports linked to entities |
| **Entities endpoint** | `GET /api/v1/entities` – Lists highest-risk entries |
| **Keyword detection** | 35+ scam keywords with weighted scoring (send money, urgent, account blocked…) |
| **Risk engine** | Keyword score (0–40) + logarithmic report-volume score (0–60) |
| **Frontend** | Bootstrap 5, responsive, animated result panel, progress bar |

---

## Local Development

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Clone / unzip the project
cd scam-detector

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Run the development server (SQLite by default)
cd backend
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

The SQLite database file `scam_detector.db` is created automatically in the `backend/` directory on first run.

---

## API Reference

### `POST /api/v1/report`

Submit a scam report.

**Request body:**
```json
{
  "type": "phone",          // "phone" | "url" | "message"
  "value": "+18005551234",
  "description": "Called claiming to be the IRS and demanded gift cards.",
  "tags": ["irs", "phone-scam"]
}
```

**Response (201):**
```json
{ "id": 1, "entity_id": 1, "message": "Report submitted successfully." }
```

---

### `POST /api/v1/check`

Check an entity for fraud risk.

**Request body:**
```json
{ "type": "url", "value": "https://suspicious-site.com/verify-account" }
```

**Response (200):**
```json
{
  "risk_score": 72.5,
  "report_count": 3,
  "status": "high risk",
  "keyword_hits": ["verify your account", "account blocked"],
  "sample_reports": [
    {
      "id": 2,
      "description": "Fake bank site asking for credentials.",
      "tags": ["phishing", "bank"],
      "created_at": "2025-01-15T10:30:00"
    }
  ]
}
```

**Status values:** `safe` (0–29) | `suspicious` (30–59) | `high risk` (60–100)

---

### `GET /api/v1/entities?limit=20`

List top-risk entities ordered by risk score descending.

---

## Deployment on Render

### 1. Push to GitHub
Push this project to a GitHub repository.

### 2. Create a Web Service on Render
- Go to [render.com](https://render.com) → **New → Web Service**
- Connect your GitHub repo
- Set the following:

| Setting | Value |
|---|---|
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

### 3. Environment Variables (Render → Environment tab)

| Variable | Value |
|---|---|
| `DATABASE_URL` | Your PostgreSQL connection string (from Render Postgres or external) |
| `ALLOWED_ORIGINS` | Your frontend URL e.g. `https://yourapp.onrender.com` |

> **Tip:** Add a Render PostgreSQL database from **New → PostgreSQL** and copy the "Internal Database URL" into `DATABASE_URL`.

### 4. SQLite (free tier / quick start)
If you skip `DATABASE_URL`, the app falls back to SQLite. Note: Render's free tier has an ephemeral filesystem — **data will be lost on redeploy**. Use PostgreSQL for persistence.

---

## Security Notes

- All inputs are validated and length-limited via Pydantic schemas.
- HTML is escaped on the frontend before rendering.
- CORS origins are configurable via the `ALLOWED_ORIGINS` environment variable.
- No authentication is required for the MVP — add OAuth/JWT if needed for production write access.
- Keyword detection runs server-side and cannot be bypassed by the client.

---

## Extending the Keyword List

Edit `backend/detection.py` – the `SCAM_KEYWORDS` list:

```python
SCAM_KEYWORDS: List[Tuple[str, float]] = [
    ("your new keyword", 10),  # (regex pattern, weight 0–40)
    ...
]
```

Weights are capped at **40 total** from keyword detection; up to **60 points** come from report volume.

---

## Health Check

`GET /health` → `{ "status": "ok" }` — use this for Render's health check URL.

---

## License

MIT
