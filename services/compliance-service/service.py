from __future__ import annotations

import re

from libs.schemas.contracts import ComplianceIssue, ComplianceResult

DEFAULT_FORBIDDEN = [
    r"\bwe guarantee\b",
    r"\bfully compliant\b",
    r"\bwill not respond\b",
    r"\bignore this request\b",
    r"\bno further action required\b",
]

DEFAULT_REQUIRED = [
    "respectfully",
    "based on the documents reviewed",
    "subject to verification",
    "without prejudice",
]

DEFAULT_SECTIONS = [
    "background",
    "analysis",
    "conclusion",
]


def check_compliance(text: str, authority: str) -> ComplianceResult:
    normalized = text.lower()
    issues: list[ComplianceIssue] = []
    forbidden_found: list[str] = []
    required_found: list[str] = []

    for pattern in DEFAULT_FORBIDDEN:
        if re.search(pattern, normalized):
            forbidden_found.append(pattern)
            issues.append(
                ComplianceIssue(
                    code="forbidden_phrase",
                    severity="high",
                    message=f"Forbidden phrase matched: {pattern}",
                )
            )

    for phrase in DEFAULT_REQUIRED:
        if phrase in normalized:
            required_found.append(phrase)
        else:
            issues.append(
                ComplianceIssue(
                    code="missing_required_term",
                    severity="medium",
                    message=f"Required legal term missing: {phrase}",
                )
            )

    if not any(section in normalized for section in DEFAULT_SECTIONS):
        issues.append(
            ComplianceIssue(
                code="format_missing_sections",
                severity="medium",
                message="Draft must contain background, analysis, and conclusion sections",
            )
        )

    if authority in {"tax", "central_bank"} and "deadline" not in normalized:
        issues.append(
            ComplianceIssue(
                code="missing_deadline_handling",
                severity="low",
                message="High-regulatory authorities should address deadlines explicitly",
            )
        )

    passed = not any(issue.severity == "high" for issue in issues)
    return ComplianceResult(
        passed=passed,
        issues=issues,
        required_terms_found=required_found,
        forbidden_terms_found=forbidden_found,
    )

