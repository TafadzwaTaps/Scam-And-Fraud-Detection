from __future__ import annotations
from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional
from datetime import datetime
import re

VALID_TYPES = {"phone", "url", "message"}


# ── Input schemas ──────────────────────────────────────────────────────────

class CheckRequest(BaseModel):
    type: str
    value: str

    @field_validator("type")
    @classmethod
    def val_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v

    @field_validator("value")
    @classmethod
    def val_value(cls, v: str) -> str:
        return v.strip()[:2048]


class ReportCreate(BaseModel):
    type: str
    value: str
    description: str
    tags: Optional[List[str]] = []

    @field_validator("type")
    @classmethod
    def val_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v

    @field_validator("value")
    @classmethod
    def val_value(cls, v: str) -> str:
        return v.strip()[:2048]

    @field_validator("description")
    @classmethod
    def val_desc(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Description must be at least 10 characters.")
        return v[:4000]

    @field_validator("tags")
    @classmethod
    def val_tags(cls, v: list) -> list:
        return [t.strip().lower()[:50] for t in (v or []) if t.strip()][:10]


# ── Output schemas ─────────────────────────────────────────────────────────

class ReportOut(BaseModel):
    id: str
    description: str
    tags: List[str]
    created_at: datetime


class NLPResult(BaseModel):
    matched_keywords: List[str]
    regex_matches: List[str]
    confidence: float          # 0.0 – 1.0


class CheckResponse(BaseModel):
    risk_score: float
    status: str                # safe | suspicious | high_risk
    report_count: int
    nlp_flags: NLPResult
    sample_reports: List[ReportOut]
    entity_id: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    entity_id: str
    risk_score: float
    message: str


class KeywordIn(BaseModel):
    word: str
    weight: float

    @field_validator("weight")
    @classmethod
    def val_weight(cls, v: float) -> float:
        if not (0 < v <= 20):
            raise ValueError("Weight must be between 0 and 20")
        return v
