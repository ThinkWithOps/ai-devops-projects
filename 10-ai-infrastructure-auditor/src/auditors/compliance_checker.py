"""CIS-inspired compliance score calculator."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import SEVERITY_ORDER, COMPLIANCE_DEDUCTIONS


def calculate_compliance_score(findings: list[dict]) -> dict:
    """
    Calculate a CIS-inspired compliance score (0–100) from a list of findings.

    Returns a dict:
    {
        "score": int,               # 0–100
        "grade": str,               # A / B / C / D / F
        "breakdown": dict,          # {"CRITICAL": n, "HIGH": n, ...}
        "total_findings": int,
        "top_3_urgent": list[dict], # top 3 by severity
        "passed": bool,             # score >= 70
    }
    """
    score = 100
    breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for f in findings:
        sev = f.get("severity", "LOW")
        breakdown[sev] = breakdown.get(sev, 0) + 1
        score -= COMPLIANCE_DEDUCTIONS.get(sev, 0)

    score = max(0, score)

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    # Sort by severity: CRITICAL first, then HIGH, MEDIUM, LOW
    critical_first = sorted(
        findings,
        key=lambda x: SEVERITY_ORDER.get(x.get("severity", "LOW"), 4),
    )
    top_3 = critical_first[:3]

    return {
        "score": score,
        "grade": grade,
        "breakdown": breakdown,
        "total_findings": len(findings),
        "top_3_urgent": [
            {
                "title": f["title"],
                "severity": f["severity"],
                "fix": f["fix"],
            }
            for f in top_3
        ],
        "passed": score >= 70,
    }
