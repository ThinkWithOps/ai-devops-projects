"""Ollama client — subprocess-based, Windows-safe, UTF-8 encoding."""
import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import OLLAMA_MODEL, OLLAMA_TIMEOUT


def call_ollama(prompt: str, model: str = None, timeout: int = None) -> str | None:
    """
    Run `ollama run <model> <prompt>` via subprocess.
    Returns the response string or None on failure.
    Windows-safe: uses UTF-8 encoding explicitly.
    """
    model = model or OLLAMA_MODEL
    timeout = timeout or OLLAMA_TIMEOUT

    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return None
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        # ollama binary not found
        return None
    except Exception:
        return None


def check_ollama_available() -> bool:
    """
    Check if Ollama is installed and running by calling `ollama list`.
    Returns True if Ollama responds successfully.
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def explain_finding(
    finding_title: str,
    finding_detail: str,
    file_type: str,
    fix: str,
    model: str = None,
) -> str | None:
    """
    Ask Ollama to explain a security finding in plain English.
    Returns a 2-3 sentence explanation or None if Ollama is unavailable.
    """
    prompt = (
        f"You are a senior DevSecOps engineer explaining an infrastructure security issue to a developer.\n\n"
        f"Issue: {finding_title}\n"
        f"Detail: {finding_detail}\n"
        f"File type: {file_type}\n"
        f"Recommended fix: {fix}\n\n"
        f"Explain in 2-3 sentences:\n"
        f"1. Why this is dangerous in production\n"
        f"2. What an attacker could do if exploited\n"
        f"3. How the fix prevents this\n\n"
        f"Keep it clear and direct. No bullet points, just plain sentences."
    )
    return call_ollama(prompt, model=model)
