"""Query Interceptor — wraps a psycopg2 connection to record timing for every query."""
import re
import time
from collections import defaultdict
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import N_PLUS_ONE_THRESHOLD


class QueryInterceptor:
    """
    Wraps a psycopg2 connection and records execution timing for every query.
    Use .execute() instead of cursor.execute() to get automatic timing.
    """

    def __init__(self, connection):
        self.connection = connection
        self.query_log: list = []  # list of {query, duration_ms, timestamp}

    def execute(self, query: str, params=None):
        """
        Execute a query, record its timing, and return the cursor result rows.
        Returns list of rows (tuples) or empty list on failure.
        """
        cur = self.connection.cursor()
        start = time.perf_counter()
        try:
            cur.execute(query, params)
            duration_ms = (time.perf_counter() - start) * 1000
            try:
                rows = cur.fetchall()
            except Exception:
                rows = []
            self.query_log.append(
                {
                    "query": query,
                    "duration_ms": round(duration_ms, 3),
                    "timestamp": datetime.utcnow().isoformat(),
                    "params": params,
                }
            )
            return rows
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            self.query_log.append(
                {
                    "query": query,
                    "duration_ms": round(duration_ms, 3),
                    "timestamp": datetime.utcnow().isoformat(),
                    "params": params,
                    "error": str(exc),
                }
            )
            return []
        finally:
            try:
                cur.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Log access helpers
    # ------------------------------------------------------------------

    def get_slow_queries(self, threshold_ms: float = 500) -> list:
        """Return entries from query_log whose duration_ms exceeds threshold_ms."""
        return [e for e in self.query_log if e.get("duration_ms", 0) >= threshold_ms]

    def clear_log(self):
        """Reset the query log."""
        self.query_log = []

    # ------------------------------------------------------------------
    # N+1 detection
    # ------------------------------------------------------------------

    def get_n_plus_one_candidates(self, threshold: int = None) -> list:
        """
        Group structurally identical queries (normalised — literals stripped).
        Returns list of groups where count > threshold, sorted by count desc.

        Each entry:
        {
            "pattern": str,
            "count": int,
            "queries": list[dict],   # raw log entries
            "total_time_ms": float,
        }
        """
        threshold = threshold if threshold is not None else N_PLUS_ONE_THRESHOLD
        groups: dict = defaultdict(list)

        for entry in self.query_log:
            normalised = _normalize_query(entry["query"])
            groups[normalised].append(entry)

        candidates = []
        for pattern, entries in groups.items():
            if len(entries) >= threshold:
                candidates.append(
                    {
                        "pattern": pattern,
                        "count": len(entries),
                        "queries": entries,
                        "total_time_ms": round(
                            sum(e.get("duration_ms", 0) for e in entries), 3
                        ),
                    }
                )

        return sorted(candidates, key=lambda x: x["count"], reverse=True)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _normalize_query(query: str) -> str:
    """Strip literal values from a query to find structurally identical queries."""
    q = re.sub(r"'[^']*'", "?", query)          # string literals
    q = re.sub(r"\b\d+\b", "?", q)              # integer literals
    q = re.sub(r"\b\d+\.\d+\b", "?", q)         # float literals
    q = re.sub(r"\s+", " ", q)                  # normalise whitespace
    return q.strip().upper()
