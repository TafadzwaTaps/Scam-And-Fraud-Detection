from fastapi import APIRouter, Request, Depends, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_supabase
from models.schemas import CheckRequest, CheckResponse, NLPResult, ReportOut
from services.entity_service import (
    upsert_entity, get_reports_for_entity,
    count_recent_reports, log_check, get_keywords,
)
from services.nlp_service import get_nlp_service
from services.scoring import compute_risk_score, risk_status
from middleware.auth import get_optional_user
from utils.normalizer import normalize_value
from utils.logger import get_logger
from config import CHECK_RATE_LIMIT
from datetime import datetime

log = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["check"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/check", response_model=CheckResponse)
@limiter.limit(CHECK_RATE_LIMIT)
async def check_entity(
    request: Request,
    payload: CheckRequest,
    user: dict | None = Depends(get_optional_user),
):
    db = get_supabase()
    norm_value = normalize_value(payload.type, payload.value)

    # Load keywords from DB (falls back to hardcoded if empty)
    db_keywords = get_keywords(db)
    nlp = get_nlp_service(db_keywords if db_keywords else None)

    # Find or create entity
    entity = upsert_entity(db, payload.type, norm_value)
    entity_id = entity["id"]

    # Fetch reports
    reports = get_reports_for_entity(db, entity_id, limit=50)
    report_count = entity.get("report_count", len(reports))
    recent_count = count_recent_reports(db, entity_id, days=7)

    # NLP on value + all report descriptions
    all_text = norm_value + " " + " ".join(r["description"] for r in reports)
    nlp_result = nlp.analyse(all_text)

    # Parse entity created_at
    created_raw = entity.get("created_at")
    try:
        entity_created_at = datetime.fromisoformat(
            created_raw.replace("Z", "+00:00") if created_raw else ""
        )
    except Exception:
        entity_created_at = None

    # Scoring
    score = compute_risk_score(
        report_count=report_count,
        nlp_score=nlp_result["nlp_score"],
        recent_reports_7d=recent_count,
        entity_created_at=entity_created_at,
    )

    # Log check for analytics
    user_id = user["sub"] if user else None
    log_check(db, entity_id, score, user_id)

    # Sample reports (3 most recent)
    sample = [
        ReportOut(
            id=r["id"],
            description=r["description"],
            tags=r.get("tags") or [],
            created_at=r["created_at"],
        )
        for r in reports[:3]
    ]

    log.info(f"CHECK type={payload.type} score={score} status={risk_status(score)}")

    return CheckResponse(
        risk_score=score,
        status=risk_status(score),
        report_count=report_count,
        nlp_flags=NLPResult(
            matched_keywords=nlp_result["matched_keywords"],
            regex_matches=nlp_result["regex_matches"],
            confidence=nlp_result["confidence"],
        ),
        sample_reports=sample,
        entity_id=entity_id,
    )
