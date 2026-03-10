"""
Base agent — shared Ollama call utilities for all War Room agents.
"""

import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Shared thread pool — all 3 agents dispatch here simultaneously.
# Ollama queues them internally, but Python does NOT block.
_executor = ThreadPoolExecutor(max_workers=4)


def call_ollama_sync(prompt: str, timeout: int = 180) -> str | None:
    """Blocking Ollama call. Used by run_in_executor."""
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return None
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None
    except Exception:
        return None


async def call_ollama_async(prompt: str, timeout: int = 180) -> str | None:
    """Non-blocking Ollama call. Run via thread pool so asyncio stays responsive."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        lambda: call_ollama_sync(prompt, timeout),
    )
