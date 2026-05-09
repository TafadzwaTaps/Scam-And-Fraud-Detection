from fastapi import APIRouter, Depends, HTTPException, status, Query

from database import get_supabase
from models.schemas import KeywordIn
from services.entity_service import list_top_entities, upsert_keyword, delete_keyword, get_keywords
from services.nlp_service import get_nlp_service
from middleware.auth import get_current_user
from utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["entities"])


@router.get("/entities")
async def get_entities(limit: int = Query(default=20, le=100)):
    db = get_supabase()
    return list_top_entities(db, limit)


# ── Admin: keyword management ──────────────────────────────────────────────
# Protected by JWT; in production add an admin role check here.

@router.get("/admin/keywords")
async def list_keywords(user: dict = Depends(get_current_user)):
    db = get_supabase()
    return get_keywords(db)


@router.post("/admin/keywords", status_code=status.HTTP_201_CREATED)
async def add_keyword(payload: KeywordIn, user: dict = Depends(get_current_user)):
    db = get_supabase()
    result = upsert_keyword(db, payload.word.lower().strip(), payload.weight)
    # Refresh NLP service with new keywords
    get_nlp_service(get_keywords(db))
    log.info(f"Keyword upserted: '{payload.word}' weight={payload.weight}")
    return result


@router.delete("/admin/keywords/{word}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_keyword(word: str, user: dict = Depends(get_current_user)):
    db = get_supabase()
    delete_keyword(db, word.lower().strip())
    get_nlp_service(get_keywords(db))
    log.info(f"Keyword deleted: '{word}'")
