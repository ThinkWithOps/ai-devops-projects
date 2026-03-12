"""N+1 Query Detector — finds queries fired in loops."""
import re
from collections import defaultdict


def normalize_query(query: str) -> str:
    """Strip literal values to find structurally identical queries."""
    q = re.sub(r"'[^']*'", "?", query)
    q = re.sub(r"\b\d+\b", "?", q)
    return re.sub(r"\s+", " ", q).strip().upper()


def detect_n_plus_one(query_log: list, threshold: int = 10) -> list:
    """
    Detect N+1 query patterns from a query log.

    Parameters
    ----------
    query_log : list of dicts
        Each entry must have at minimum: {"query": str}.
        Optional fields: {"duration_ms": float, "timestamp": str}.
    threshold : int
        Minimum number of identical (normalised) queries to flag.

    Returns
    -------
    list of finding dicts:
        {
            "pattern": str,             # normalised SQL template
            "count": int,               # number of times fired
            "sample_query": str,        # one real example query
            "severity": str,            # CRITICAL / HIGH / MEDIUM
            "estimated_reduction": str, # e.g. "847 queries → 1 with JOIN"
            "total_time_ms": float,     # sum of all execution times
        }
    """
    groups: dict = defaultdict(list)
    for entry in query_log:
        normalized = normalize_query(entry["query"])
        groups[normalized].append(entry)

    findings = []
    for pattern, entries in groups.items():
        if len(entries) >= threshold:
            count = len(entries)
            severity = "CRITICAL" if count > 100 else "HIGH" if count > 20 else "MEDIUM"
            findings.append(
                {
                    "pattern": pattern,
                    "count": count,
                    "sample_query": entries[0]["query"],
                    "severity": severity,
                    "estimated_reduction": f"{count} queries → 1 with JOIN",
                    "total_time_ms": round(
                        sum(e.get("duration_ms", 0) for e in entries), 3
                    ),
                }
            )

    return sorted(findings, key=lambda x: x["count"], reverse=True)


def parse_query_log_text(raw_text: str) -> list:
    """
    Parse a plain-text query log (one query per line) into a list of dicts
    compatible with detect_n_plus_one().

    Lines starting with '--' or '#' are treated as comments and skipped.
    Empty lines are skipped.
    """
    entries = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("--") or stripped.startswith("#"):
            continue
        entries.append({"query": stripped, "duration_ms": 0})
    return entries
