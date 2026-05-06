from pydantic import BaseModel, field_validator, HttpUrl
from typing import List, Optional
from datetime import datetime
import re


VALID_TYPES = {"phone", "url", "message"}


class ReportCreate(BaseModel):
    type: str
    value: str
    description: str
    tags: Optional[List[str]] = []

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v

    @field_validator("value")
    @classmethod
    def sanitize_value(cls, v: str) -> str:
        return v.strip()[:2048]

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        return v.strip()[:4000]


class CheckRequest(BaseModel):
    type: str
    value: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v

    @field_validator("value")
    @classmethod
    def sanitize_value(cls, v: str) -> str:
        return v.strip()[:2048]


class ReportOut(BaseModel):
    id: int
    description: str
    tags: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckResponse(BaseModel):
    risk_score: float
    report_count: int
    status: str           # safe | suspicious | high risk
    sample_reports: List[ReportOut]
    keyword_hits: List[str]


class ReportResponse(BaseModel):
    id: int
    entity_id: int
    message: str
