"""PostgreSQL connector — handles all database interactions."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from config import DB_CONFIG


def get_connection(config: dict = None):
    """Return a psycopg2 connection using DB_CONFIG. Returns None on failure."""
    if not PSYCOPG2_AVAILABLE:
        return None
    cfg = config or DB_CONFIG
    try:
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            connect_timeout=10,
            options="-c client_encoding=UTF8",
        )
        return conn
    except Exception:
        return None


def test_connection(config: dict = None) -> tuple:
    """
    Test database connection.
    Returns (True, success_message) or (False, error_message).
    """
    if not PSYCOPG2_AVAILABLE:
        return False, "psycopg2 not installed. Run: pip install psycopg2-binary"

    cfg = config or DB_CONFIG
    try:
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            connect_timeout=10,
            options="-c client_encoding=UTF8",
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        short_version = version.split(",")[0] if version else "PostgreSQL"
        return True, f"Connected to {short_version}"
    except Exception as e:
        error = str(e)
        if "password authentication" in error.lower():
            return False, "Authentication failed — check username/password"
        elif "could not connect" in error.lower() or "connection refused" in error.lower():
            return False, f"Connection refused — is PostgreSQL running on {cfg['host']}:{cfg['port']}?"
        elif "does not exist" in error.lower():
            return False, f"Database '{cfg['database']}' does not exist"
        else:
            return False, f"Connection error: {error}"


def get_slow_queries(threshold_ms: float = 500, config: dict = None) -> list:
    """
    Fetch slow queries from pg_stat_statements.
    Falls back to pg_stat_activity if pg_stat_statements is unavailable.
    Returns list of dicts: {query, calls, total_time, mean_time, rows}
    """
    conn = get_connection(config)
    if not conn:
        return []

    results = []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Try pg_stat_statements first
        has_pg_stat = check_pg_stat_statements(config)

        if has_pg_stat:
            cur.execute(
                """
                SELECT
                    query,
                    calls,
                    total_exec_time AS total_time,
                    mean_exec_time  AS mean_time,
                    rows
                FROM pg_stat_statements
                WHERE mean_exec_time > %s
                  AND query NOT LIKE '%%pg_stat%%'
                  AND query NOT LIKE '%%EXPLAIN%%'
                ORDER BY mean_exec_time DESC
                LIMIT 50;
                """,
                (threshold_ms,),
            )
        else:
            # Fallback: pg_stat_activity (only shows currently running queries)
            cur.execute(
                """
                SELECT
                    query,
                    1 AS calls,
                    EXTRACT(EPOCH FROM (now() - query_start)) * 1000 AS total_time,
                    EXTRACT(EPOCH FROM (now() - query_start)) * 1000 AS mean_time,
                    0 AS rows
                FROM pg_stat_activity
                WHERE state = 'active'
                  AND query NOT LIKE '%%pg_stat%%'
                  AND query_start IS NOT NULL
                  AND EXTRACT(EPOCH FROM (now() - query_start)) * 1000 > %s
                ORDER BY mean_time DESC
                LIMIT 50;
                """,
                (threshold_ms,),
            )

        rows = cur.fetchall()
        for row in rows:
            results.append({
                "query": row["query"] or "",
                "calls": int(row["calls"] or 0),
                "total_time": float(row["total_time"] or 0),
                "mean_time": float(row["mean_time"] or 0),
                "rows": int(row["rows"] or 0),
            })

        cur.close()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return results


def get_table_indexes(table_name: str, config: dict = None) -> list:
    """
    Return list of index dicts for a given table.
    Each dict: {index_name, index_def, is_unique, is_primary}
    """
    conn = get_connection(config)
    if not conn:
        return []

    results = []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT
                i.relname   AS index_name,
                pg_get_indexdef(ix.indexrelid) AS index_def,
                ix.indisunique  AS is_unique,
                ix.indisprimary AS is_primary
            FROM
                pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i  ON i.oid = ix.indexrelid
            WHERE
                t.relname = %s
                AND t.relkind = 'r'
            ORDER BY i.relname;
            """,
            (table_name,),
        )
        rows = cur.fetchall()
        for row in rows:
            results.append({
                "index_name": row["index_name"],
                "index_def": row["index_def"],
                "is_unique": bool(row["is_unique"]),
                "is_primary": bool(row["is_primary"]),
            })
        cur.close()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return results


def run_explain_analyze(query: str, config: dict = None) -> str:
    """
    Run EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) on a query.
    Returns the plan as a string, or an error message string.
    """
    conn = get_connection(config)
    if not conn:
        return "Error: Could not connect to database"

    try:
        # Strip trailing semicolons to wrap safely
        clean_query = query.strip().rstrip(";")
        cur = conn.cursor()
        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {clean_query}")
        rows = cur.fetchall()
        output = "\n".join(row[0] for row in rows)
        cur.close()
        return output
    except Exception as e:
        return f"Error running EXPLAIN ANALYZE: {str(e)}"
    finally:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass


def get_table_schema(table_name: str, config: dict = None) -> list:
    """
    Return column info for a table.
    Each dict: {column_name, data_type, is_nullable, column_default}
    """
    conn = get_connection(config)
    if not conn:
        return []

    results = []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s
              AND table_schema = 'public'
            ORDER BY ordinal_position;
            """,
            (table_name,),
        )
        rows = cur.fetchall()
        for row in rows:
            results.append({
                "column_name": row["column_name"],
                "data_type": row["data_type"],
                "is_nullable": row["is_nullable"],
                "column_default": row["column_default"],
            })
        cur.close()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return results


def check_pg_stat_statements(config: dict = None) -> bool:
    """Check if pg_stat_statements extension is enabled. Returns bool."""
    conn = get_connection(config)
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements';"
        )
        row = cur.fetchone()
        cur.close()
        return row is not None
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass
