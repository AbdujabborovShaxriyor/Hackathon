from __future__ import annotations

import re

from libs.schemas.contracts import ClassificationResult

AUTHORITY_PATTERNS = {
    "tax": [r"\btax\b", r"\bvat\b", r"\brevenue\b", r"\breturn\b", r"\baudit\b", r"\bwithholding\b"],
    "prosecutor": [r"\bprosecutor\b", r"\binvestigation\b", r"\bcriminal\b", r"\bsubpoena\b", r"\bcase\b"],
    "central_bank": [r"\bcentral bank\b", r"\bbank\b", r"\bcompliance\b", r"\bmonetary\b", r"\blicens"],
    "court": [r"\bcourt\b", r"\bjudge\b", r"\bhearing\b", r"\border\b", r"\blitigation\b"],
}

RISK_TERMS = {
    20: [r"\bdeadline\b", r"\bwithin \d+ days\b", r"\bimmediately\b"],
    25: [r"\bsanction\b", r"\bfine\b", r"\bpenalty\b"],
    30: [r"\bsuspension\b", r"\brevocation\b", r"\bfreeze\b"],
    35: [r"\bcriminal\b", r"\bprosecutor\b", r"\braid\b", r"\bsearch warrant\b"],
}


def classify_text(text: str) -> ClassificationResult:
    normalized = text.lower()
    authority_scores: dict[str, int] = {}
    for authority, patterns in AUTHORITY_PATTERNS.items():
        score = sum(1 for pattern in patterns if re.search(pattern, normalized))
        authority_scores[authority] = score

    authority = max(authority_scores, key=authority_scores.get)
    if authority_scores[authority] == 0:
        authority = "other"

    risk_score = 15 + authority_scores.get(authority, 0) * 12
    labels: list[str] = [authority]
    rationale_bits = [f"Authority signals: {authority_scores}"]

    for points, patterns in RISK_TERMS.items():
        if any(re.search(pattern, normalized) for pattern in patterns):
            risk_score += points
            labels.append(f"risk_{points}")
            rationale_bits.append(f"Matched risk terms worth {points} points")

    if len(text) > 8000:
        risk_score += 10
        labels.append("long_request")
        rationale_bits.append("Large request body increases review complexity")

    risk_score = max(0, min(100, risk_score))
    return ClassificationResult(
        authority=authority,
        risk_score=risk_score,
        rationale="; ".join(rationale_bits),
        labels=sorted(set(labels)),
    )

