"""
Risk scoring engine for Scam & Fraud Detection.
"""

import re
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Keyword dictionary with weights (0–40 points each, capped at 40 total)
# ---------------------------------------------------------------------------
SCAM_KEYWORDS: List[Tuple[str, float]] = [
    # Financial pressure
    ("send money", 15),
    ("wire transfer", 12),
    ("gift card", 12),
    ("bitcoin payment", 12),
    ("pay now", 10),
    ("transfer funds", 12),
    # Urgency / fear
    ("urgent", 8),
    ("immediately", 8),
    ("act now", 10),
    ("limited time", 7),
    ("expire", 6),
    # Account / security threats
    ("account blocked", 14),
    ("account suspended", 14),
    ("verify now", 12),
    ("verify your account", 12),
    ("confirm your details", 10),
    ("update your information", 9),
    ("your account has been", 10),
    # Prize / lottery
    ("you have won", 13),
    ("claim your prize", 13),
    ("lottery winner", 13),
    ("selected winner", 12),
    # Credential phishing
    ("click here to login", 11),
    ("reset your password", 9),
    ("enter your password", 11),
    ("social security", 10),
    ("ssn", 8),
    ("credit card number", 11),
    # Generic deception
    ("too good to be true", 9),
    ("free money", 10),
    ("easy money", 9),
    ("make money fast", 10),
    ("work from home", 5),
    ("double your investment", 12),
    ("guaranteed return", 10),
    # Threats
    ("legal action", 8),
    ("arrest warrant", 12),
    ("irs", 7),
    ("tax refund", 7),
]

_COMPILED = [(re.compile(pattern, re.IGNORECASE), weight) for pattern, weight in SCAM_KEYWORDS]


def detect_keywords(text: str) -> Tuple[List[str], float]:
    """Return list of matched keywords and raw keyword score (0–40)."""
    hits: List[str] = []
    total_weight = 0.0

    for pattern, weight in _COMPILED:
        if pattern.search(text):
            keyword = pattern.pattern  # human-readable label
            if keyword not in hits:
                hits.append(keyword)
                total_weight += weight

    keyword_score = min(total_weight, 40.0)
    return hits, keyword_score


def compute_risk_score(keyword_score: float, report_count: int) -> float:
    """
    Risk score 0–100:
      - Up to 40 pts from keyword detection
      - Up to 60 pts from report volume (logarithmic scale)
    """
    import math

    if report_count == 0:
        report_score = 0.0
    elif report_count == 1:
        report_score = 20.0
    else:
        # log scale: 2 reports → 30, 5 → 45, 10 → 55, 50 → 60
        report_score = min(60.0, 20.0 + 15.0 * math.log2(report_count))

    return round(min(keyword_score + report_score, 100.0), 1)


def risk_status(score: float) -> str:
    if score >= 60:
        return "high risk"
    if score >= 30:
        return "suspicious"
    return "safe"
