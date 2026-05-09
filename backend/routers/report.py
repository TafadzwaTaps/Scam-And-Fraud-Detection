from fastapi import APIRouter, Depends, HTTPException, status

from database import get_supabase
from models.schemas import ReportCreate, ReportResponse
from services.entity_service import (
    upsert_entity, get_reports_for_entity, count_recent_reports,
    insert_report, update_entity_score, user_already_reported, get_keywords,
)
from services.nlp_service import get_nlp_service
from services.scoring import compute_risk_score, risk_status
from middleware.auth import get_current_user
from utils.normalizer import normalize_value, sanitize_text
from utils.logger import get_logger
from datetime import datetime

log = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["report"])


@router.post("/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(
    payload: ReportCreate,
    user: dict = Depends(get_current_user),
):
    db = get_supabase()
    user_id: str = user["sub"]

    norm_value = normalize_value(payload.type, payload.value)
    description = sanitize_text(payload.description)

    # Find or create entity
    entity = upsert_entity(db, payload.type, norm_value)
    entity_id = entity["id"]

    # Prevent duplicate reports from same user
    if user_already_reported(db, entity_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted a report for this entity.",
        )

    # Insert report
    insert_report(db, entity_id, user_id, description, payload.tags)

    # Recompute score
    reports = get_reports_for_entity(db, entity_id, limit=50)
    recent_count = count_recent_reports(db, entity_id, days=7)

    db_keywords = get_keywords(db)
    nlp = get_nlp_service(db_keywords if db_keywords else None)
    all_text = norm_value + " " + " ".join(r["description"] for r in reports)
    nlp_result = nlp.analyse(all_text)

    created_raw = entity.get("created_at")
    try:
        entity_created_at = datetime.fromisoformat(
            created_raw.replace("Z", "+00:00") if created_raw else ""
        )
    except Exception:
        entity_created_at = None

    new_count = len(reports)
    score = compute_risk_score(
        report_count=new_count,
        nlp_score=nlp_result["nlp_score"],
        recent_reports_7d=recent_count,
        entity_created_at=entity_created_at,
    )

    update_entity_score(db, entity_id, score, new_count)

    log.info(f"REPORT submitted entity={entity_id} user={user_id} score={score}")

    return ReportResponse(
        id=reports[0]["id"] if reports else "",
        entity_id=entity_id,
        risk_score=score,
        message="Report submitted successfully. Thank you for helping protect the community.",
    )
