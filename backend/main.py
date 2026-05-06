import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import router

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Scam & Fraud Detection API",
    description="Report and check phone numbers, URLs, and messages for fraud.",
    version="1.0.0",
)

# CORS – tighten origins in production via env var
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    init_db()


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
app.include_router(router)

# ---------------------------------------------------------------------------
# Serve static frontend
# Resolve paths absolutely so they work regardless of cwd when uvicorn runs.
# Layout expected:
#   <project_root>/
#     backend/main.py   ← __file__
#     frontend/index.html
#     frontend/static/
# ---------------------------------------------------------------------------
_BACKEND_DIR  = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_BACKEND_DIR, ".."))
FRONTEND_DIR  = os.path.join(_PROJECT_ROOT, "frontend")
STATIC_DIR    = os.path.join(FRONTEND_DIR, "static")
INDEX_FILE    = os.path.join(FRONTEND_DIR, "index.html")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    if os.path.isfile(INDEX_FILE):
        return FileResponse(INDEX_FILE)
    return JSONResponse(
        {"detail": "Frontend not found. API is running — visit /docs for the API."},
        status_code=200,
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
