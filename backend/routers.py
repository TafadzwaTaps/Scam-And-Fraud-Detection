from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Entity, Report
from schemas import ReportCreate, CheckRequest, CheckResponse, ReportResponse, ReportOut
from detection import detect_keywords, compute_risk_score, risk_status

router = APIRouter(prefix="/api/v1", tags=["scam-detection"])


# ---------------------------------------------------------------------------
# POST /report
# ---------------------------------------------------------------------------
@router.post("/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def submit_report(payload: ReportCreate, db: Session = Depends(get_db)):
    """Store a scam/fraud report linked to an entity."""

    # Upsert entity
    entity = db.query(Entity).filter(
        Entity.type == payload.type,
        Entity.value == payload.value,
    ).first()

    if not entity:
        entity = Entity(type=payload.type, value=payload.value)
        db.add(entity)
        db.flush()   # get entity.id before adding report

    # Persist report
    tags_str = ",".join(t.strip().lower() for t in payload.tags if t.strip())
    report = Report(
        entity_id=entity.id,
        description=payload.description,
        tags=tags_str,
    )
    db.add(report)

    # Recompute entity risk score
    # Count all reports (including the new one)
    all_descriptions = " ".join(r.description for r in entity.reports) + " " + payload.description
    _, kw_score = detect_keywords(all_descriptions + " " + payload.value)
    report_count = len(entity.reports) + 1
    entity.risk_score = compute_risk_score(kw_score, report_count)

    db.commit()
    db.refresh(report)

    return ReportResponse(id=report.id, entity_id=entity.id, message="Report submitted successfully.")


# ---------------------------------------------------------------------------
# POST /check
# ---------------------------------------------------------------------------
@router.post("/check", response_model=CheckResponse)
def check_entity(payload: CheckRequest, db: Session = Depends(get_db)):
    """Analyse an entity and return a risk assessment."""

    entity = db.query(Entity).filter(
        Entity.type == payload.type,
        Entity.value == payload.value,
    ).first()

    # Keyword detection on the value itself
    kw_hits, kw_score = detect_keywords(payload.value)

    if entity:
        report_count = len(entity.reports)
        # Also scan descriptions for keywords
        all_text = " ".join(r.description for r in entity.reports) + " " + payload.value
        kw_hits_all, kw_score_all = detect_keywords(all_text)
        kw_hits = list(set(kw_hits + kw_hits_all))
        kw_score = kw_score_all
        score = compute_risk_score(kw_score, report_count)

        sample = sorted(entity.reports, key=lambda r: r.created_at, reverse=True)[:3]
        sample_out = [
            ReportOut(
                id=r.id,
                description=r.description,
                tags=[t for t in r.tags.split(",") if t],
                created_at=r.created_at,
            )
            for r in sample
        ]
    else:
        report_count = 0
        score = compute_risk_score(kw_score, 0)
        sample_out = []

    return CheckResponse(
        risk_score=score,
        report_count=report_count,
        status=risk_status(score),
        sample_reports=sample_out,
        keyword_hits=kw_hits,
    )


# ---------------------------------------------------------------------------
# GET /entities  (convenience — list recently flagged entities)
# ---------------------------------------------------------------------------
@router.get("/entities")
def list_entities(limit: int = 20, db: Session = Depends(get_db)):
    entities = (
        db.query(Entity)
        .order_by(Entity.risk_score.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [
        {
            "id": e.id,
            "type": e.type,
            "value": e.value,
            "risk_score": e.risk_score,
            "report_count": len(e.reports),
            "created_at": e.created_at,
        }
        for e in entities
    ]
