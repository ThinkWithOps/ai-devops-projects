"""Index Analyzer — finds missing indexes from EXPLAIN ANALYZE output."""
import re


def parse_explain_output(explain_text: str) -> dict:
    """Parse EXPLAIN ANALYZE output into structured data."""
    result = {
        "seq_scans": [],
        "index_scans": [],
        "estimated_rows": None,
        "actual_rows": None,
        "execution_time_ms": None,
        "planning_time_ms": None,
        "has_seq_scan": False,
    }

    for line in explain_text.splitlines():
        # Sequential scans
        if "Seq Scan" in line:
            result["has_seq_scan"] = True
            table_match = re.search(r"Seq Scan on (\w+)", line)
            if table_match:
                table = table_match.group(1)
                if table not in result["seq_scans"]:
                    result["seq_scans"].append(table)

        # Index scans
        if "Index Scan" in line or "Index Only Scan" in line:
            table_match = re.search(
                r"Index (?:Only )?Scan(?: Backward)? using (\w+) on (\w+)", line
            )
            if table_match:
                result["index_scans"].append(
                    {
                        "index": table_match.group(1),
                        "table": table_match.group(2),
                    }
                )

        # Row estimates
        rows_match = re.search(r"rows=(\d+)", line)
        if rows_match and result["estimated_rows"] is None:
            result["estimated_rows"] = int(rows_match.group(1))

        # Actual rows
        actual_match = re.search(r"actual.*?rows=(\d+)", line)
        if actual_match and result["actual_rows"] is None:
            result["actual_rows"] = int(actual_match.group(1))

        # Execution time
        time_match = re.search(r"Execution Time: ([\d.]+) ms", line)
        if time_match:
            result["execution_time_ms"] = float(time_match.group(1))

        # Planning time
        plan_match = re.search(r"Planning Time: ([\d.]+) ms", line)
        if plan_match:
            result["planning_time_ms"] = float(plan_match.group(1))

    return result


def analyze_query_indexes(explain_text: str, query: str) -> dict:
    """
    Analyse EXPLAIN ANALYZE output and return index findings.

    Returns
    -------
    dict:
        {
            "parsed": dict,         # from parse_explain_output()
            "findings": list,       # list of finding dicts
            "has_issues": bool,
        }

    Each finding dict:
        {
            "type": str,            # e.g. "MISSING_INDEX"
            "severity": str,        # HIGH / MEDIUM / LOW
            "table": str,
            "suggested_columns": list[str],
            "explain_time_ms": float | None,
            "message": str,
            "suggested_fix": str,   # ready-to-run SQL
        }
    """
    parsed = parse_explain_output(explain_text)
    findings = []

    if parsed["has_seq_scan"] and parsed["seq_scans"]:
        for table in parsed["seq_scans"]:
            # Extract columns from WHERE clause
            where_cols = re.findall(
                r"WHERE\s+(?:\w+\.)?(\w+)\s*[=<>!]", query, re.IGNORECASE
            )
            # Also catch AND conditions
            and_cols = re.findall(
                r"AND\s+(?:\w+\.)?(\w+)\s*[=<>!]", query, re.IGNORECASE
            )
            all_cols = list(dict.fromkeys(where_cols + and_cols))  # deduplicate, preserve order

            # Estimate severity by timing
            exec_time = parsed.get("execution_time_ms")
            if exec_time and exec_time > 1000:
                severity = "CRITICAL"
            elif exec_time and exec_time > 200:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            col_str = "_".join(all_cols) if all_cols else "col"
            col_list = ", ".join(all_cols) if all_cols else "your_column"

            findings.append(
                {
                    "type": "MISSING_INDEX",
                    "severity": severity,
                    "table": table,
                    "suggested_columns": all_cols,
                    "explain_time_ms": exec_time,
                    "message": (
                        f"Sequential scan on '{table}' — full table read on every query"
                    ),
                    "suggested_fix": (
                        f"CREATE INDEX idx_{table}_{col_str} ON {table}({col_list});"
                    ),
                }
            )

    return {
        "parsed": parsed,
        "findings": findings,
        "has_issues": len(findings) > 0,
    }
