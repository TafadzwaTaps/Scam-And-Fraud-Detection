"""
Weighted risk scoring model.

risk_score = min(100,
    (report_count_component)      +   # up to 25 pts
    (recent_reports_component)    +   # up to 20 pts
    (nlp_score)                   +   # up to 30 pts
    (entity_age_penalty)          +   # up to 15 pts
    (duplicate_penalty_reduction)     # reduces score for spam
)

Status thresholds:
  safe        0  – 29
  suspicious  30 – 59
  high_risk   60 – 100
"""
from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta
from typing import Optional


def compute_risk_score(
    report_count: int,
    nlp_score: float,                    # 0–30
    recent_reports_7d: int = 0,
    entity_created_at: Optional[datetime] = None,
    duplicate_penalty: float = 0.0,      # 0–10 reduction
) -> float:

    # 1. Report count component (log scale, 0–25)
    if report_count == 0:
        rc_score = 0.0
    elif report_count == 1:
        rc_score = 10.0
    else:
        rc_score = min(25.0, 10.0 + 8.0 * math.log2(report_count))

    # 2. Recent activity weight (0–20)
    if recent_reports_7d == 0:
        recent_score = 0.0
    elif recent_reports_7d == 1:
        recent_score = 8.0
    else:
        recent_score = min(20.0, 8.0 + 6.0 * math.log2(recent_reports_7d))

    # 3. NLP score already 0–30 (passed in from NLP service)
    nlp = min(nlp_score, 30.0)

    # 4. Entity age penalty: brand-new entities with any report = higher risk
    #    Max 15 pts for entities < 24h old, tapering to 0 over 30 days
    age_penalty = 0.0
    if entity_created_at and report_count > 0:
        age_days = (datetime.now(timezone.utc) - entity_created_at).total_seconds() / 86400
        if age_days < 1:
            age_penalty = 15.0
        elif age_days < 30:
            age_penalty = max(0.0, 15.0 * (1 - age_days / 30))

    raw = rc_score + recent_score + nlp + age_penalty - duplicate_penalty
    return round(max(0.0, min(100.0, raw)), 1)


def risk_status(score: float) -> str:
    if score >= 60:
        return "high_risk"
    if score >= 30:
        return "suspicious"
    return "safe"
