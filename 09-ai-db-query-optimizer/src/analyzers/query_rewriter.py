"""Query Rewriter — uses AI to rewrite bad SQL into optimized SQL."""
import re

from ..ai.ollama_client import call_ollama

REWRITE_PROMPT = """You are a senior PostgreSQL performance engineer. Rewrite this slow SQL query.

ORIGINAL QUERY:
{query}

EXPLAIN ANALYZE OUTPUT:
{explain_output}

TABLE SCHEMA (if available):
{schema}

DETECTED ISSUES:
{issues}

Respond in EXACTLY this format (no other text):
OPTIMIZED_QUERY:
[your optimized SQL here]
END_QUERY

CHANGES_MADE:
[bullet list of what you changed and why]

EXPECTED_IMPROVEMENT:
[percentage improvement estimate, e.g. "60-80% faster"]

EXPLANATION:
[plain English explanation a junior dev can understand]"""


def rewrite_query(
    query: str,
    explain_output: str = "",
    schema: str = "",
    issues: str = "",
) -> dict:
    """
    Ask Ollama to rewrite a slow query.

    Returns
    -------
    dict:
        {
            "success": bool,
            "optimized_query": str,
            "changes_made": str,
            "expected_improvement": str,
            "explanation": str,
            "raw_response": str,
            "error": str,   # only present on failure
        }
    """
    prompt = REWRITE_PROMPT.format(
        query=query,
        explain_output=explain_output[:2000] if explain_output else "Not available",
        schema=schema[:1000] if schema else "Not available",
        issues=issues if issues else "General optimization needed",
    )

    response = call_ollama(prompt)
    if not response:
        return {
            "success": False,
            "error": "Ollama unavailable — is it running? (ollama serve)",
            "optimized_query": query,
            "changes_made": "",
            "expected_improvement": "",
            "explanation": "",
            "raw_response": "",
        }

    optimized = re.search(
        r"OPTIMIZED_QUERY:\s*(.*?)\s*END_QUERY", response, re.DOTALL
    )
    changes = re.search(
        r"CHANGES_MADE:\s*(.*?)\s*EXPECTED_IMPROVEMENT:", response, re.DOTALL
    )
    improvement = re.search(
        r"EXPECTED_IMPROVEMENT:\s*(.*?)\s*EXPLANATION:", response, re.DOTALL
    )
    explanation = re.search(r"EXPLANATION:\s*(.*?)$", response, re.DOTALL)

    return {
        "success": True,
        "optimized_query": optimized.group(1).strip() if optimized else query,
        "changes_made": changes.group(1).strip() if changes else response,
        "expected_improvement": improvement.group(1).strip() if improvement else "Unknown",
        "explanation": explanation.group(1).strip() if explanation else "",
        "raw_response": response,
    }
