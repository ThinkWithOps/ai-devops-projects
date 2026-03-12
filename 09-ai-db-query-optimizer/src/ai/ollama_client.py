"""Ollama API client — synchronous calls for Streamlit compatibility."""
import re
import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import OLLAMA_MODEL, OLLAMA_TIMEOUT


def call_ollama(prompt: str, model: str = None, timeout: int = None) -> str | None:
    """
    Call Ollama via subprocess (synchronous — compatible with Streamlit).

    Parameters
    ----------
    prompt  : str  — the full prompt to send
    model   : str  — Ollama model name (defaults to config OLLAMA_MODEL)
    timeout : int  — seconds before giving up (defaults to config OLLAMA_TIMEOUT)

    Returns
    -------
    Response string, or None if Ollama is unavailable / timed out / errored.
    """
    model = model or OLLAMA_MODEL
    timeout = timeout or OLLAMA_TIMEOUT

    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        # ollama binary not found on PATH
        return None
    except Exception:
        return None


def check_ollama_available() -> tuple:
    """
    Check if Ollama is available and the configured model is present.

    Returns (bool, message_str)
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        if result.returncode == 0:
            output = result.stdout
            if OLLAMA_MODEL in output:
                return True, f"Ollama ready — model '{OLLAMA_MODEL}' available"
            else:
                return (
                    False,
                    f"Ollama running but model '{OLLAMA_MODEL}' not found. "
                    f"Run: ollama pull {OLLAMA_MODEL}",
                )
        return False, "Ollama returned an error"
    except FileNotFoundError:
        return False, "Ollama not found. Install from https://ollama.com"
    except subprocess.TimeoutExpired:
        return False, "Ollama check timed out"
    except Exception as exc:
        return False, f"Ollama check failed: {exc}"


# ---------------------------------------------------------------------------
# Named prompts — used directly in app.py for the Slow Query Scanner tab
# ---------------------------------------------------------------------------

ANALYZE_PROMPT = """You are a PostgreSQL performance detective. Analyze this slow query.

QUERY:
{query}

EXECUTION TIME: {time_ms}ms
EXPLAIN ANALYZE:
{explain}

Respond EXACTLY in this format:
PROBLEM_TYPE: [N+1_QUERY | MISSING_INDEX | INEFFICIENT_JOIN | FULL_TABLE_SCAN | OTHER]
SEVERITY: [CRITICAL | HIGH | MEDIUM | LOW]
ROOT_CAUSE: [one sentence]
SPECIFIC_FIX: [exact fix — SQL statement or config change]
ESTIMATED_IMPROVEMENT: [e.g. "90% faster, 3.1s → 48ms"]
BUSINESS_IMPACT: [plain English, e.g. "This runs 1000x/day — costs $2,400/year"]"""


def analyze_slow_query(query: str, time_ms: float, explain: str = "") -> dict:
    """
    Ask Ollama to analyse a slow query.

    Returns
    -------
    dict:
        {
            "success": bool,
            "problem_type": str,
            "severity": str,
            "root_cause": str,
            "specific_fix": str,
            "estimated_improvement": str,
            "business_impact": str,
            "raw": str,
        }
    On failure: {"success": False, "raw": None}
    """
    prompt = ANALYZE_PROMPT.format(
        query=query[:1500],
        time_ms=time_ms,
        explain=explain[:2000] if explain else "Not available",
    )

    response = call_ollama(prompt)
    if not response:
        return {"success": False, "raw": None}

    def extract(key: str) -> str:
        m = re.search(rf"{key}:\s*(.+)", response)
        return m.group(1).strip() if m else ""

    return {
        "success": True,
        "problem_type": extract("PROBLEM_TYPE"),
        "severity": extract("SEVERITY"),
        "root_cause": extract("ROOT_CAUSE"),
        "specific_fix": extract("SPECIFIC_FIX"),
        "estimated_improvement": extract("ESTIMATED_IMPROVEMENT"),
        "business_impact": extract("BUSINESS_IMPACT"),
        "raw": response,
    }
