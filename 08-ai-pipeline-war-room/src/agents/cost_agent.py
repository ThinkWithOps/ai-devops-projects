"""
💰 Cost Agent — calculates real dollar cost of wasted CI/CD runner minutes.
GitHub Actions pricing (as of 2025):
  Ubuntu runner: $0.008/min (public repos: free)
  Ubuntu runner: $0.016/min (private repos — 2× multiplier)
Phase 1: instant math-based calculation. Phase 2: Ollama AI enrichment.
"""

import re
from .base_agent import call_ollama_async

AGENT_NAME = "💰 COST AGENT"

# GitHub Actions pricing (USD per minute)
RATE_PUBLIC = 0.008    # free for public repos, but use for illustration
RATE_PRIVATE = 0.016   # private repos — 2× multiplier


# ─── Rule-Based Calculation (instant) ────────────────────────────────────────

def run_rules(content: str, team_size: int = 10, commits_per_dev_per_day: int = 5) -> dict:
    """Calculate exact dollar waste from detected inefficiencies."""
    waste_breakdown = []
    total_wasted_min_per_run = 0

    # 1. Redundant npm installs
    npm_count = content.count("npm install") + content.count("npm ci")
    has_npm_cache = "cache: 'npm'" in content or 'cache: "npm"' in content
    if npm_count > 1 and not has_npm_cache:
        redundant = npm_count - 1
        wasted = redundant * 2.0  # each unnecessary install ≈ 2 min
        total_wasted_min_per_run += wasted
        waste_breakdown.append({
            "cause": f"npm install ×{npm_count} (no cache)",
            "wasted_min_per_run": wasted,
            "fix": "cache: 'npm' → saves {:.0f} min/run".format(wasted),
        })

    # 2. Redundant pip installs
    pip_count = len(re.findall(r"pip install", content))
    has_pip_cache = "cache: 'pip'" in content or 'cache: "pip"' in content
    if pip_count > 1 and not has_pip_cache:
        redundant = pip_count - 1
        wasted = redundant * 1.0  # pip slightly faster than npm
        total_wasted_min_per_run += wasted
        waste_breakdown.append({
            "cause": f"pip install ×{pip_count} (no cache)",
            "wasted_min_per_run": wasted,
            "fix": "cache: 'pip' → saves {:.0f} min/run".format(wasted),
        })

    # 3. Sequential jobs that could be parallel
    parallel_candidates = []
    for job in ["lint", "test", "security", "check"]:
        if re.search(rf"^  {job}\b.*?\n\s+needs:", content, re.MULTILINE | re.DOTALL):
            parallel_candidates.append(job)
    if len(parallel_candidates) >= 2:
        wasted = (len(parallel_candidates) - 1) * 2.0  # each extra sequential stage ≈ 2 min
        total_wasted_min_per_run += wasted
        waste_breakdown.append({
            "cause": f"Sequential jobs ({', '.join(parallel_candidates)}) not parallelized",
            "wasted_min_per_run": wasted,
            "fix": "Parallelize → saves {:.0f} min/run".format(wasted),
        })

    # 4. Docker rebuild without cache
    if "docker build" in content and "--cache-from" not in content:
        wasted = 2.5
        total_wasted_min_per_run += wasted
        waste_breakdown.append({
            "cause": "Docker full rebuild (no --cache-from)",
            "wasted_min_per_run": wasted,
            "fix": "--cache-from → saves ~2.5 min/run",
        })

    # 5. Redundant install job (runs but downstream jobs re-install)
    install_jobs = re.findall(r"^  (install[\w-]*):", content, re.MULTILINE)
    if install_jobs and (npm_count > 1 or pip_count > 1):
        wasted = 2.0
        total_wasted_min_per_run += wasted
        waste_breakdown.append({
            "cause": f"Redundant '{install_jobs[0]}' job (ignored by downstream)",
            "wasted_min_per_run": wasted,
            "fix": "Remove job → saves 2 min/run",
        })

    # Monthly / Annual projections
    working_days_per_month = 22
    runs_per_month = team_size * commits_per_dev_per_day * working_days_per_month

    wasted_min_per_month = total_wasted_min_per_run * runs_per_month

    monthly_cost_public = wasted_min_per_month * RATE_PUBLIC
    monthly_cost_private = wasted_min_per_month * RATE_PRIVATE
    annual_cost_public = monthly_cost_public * 12
    annual_cost_private = monthly_cost_private * 12

    # Top cost driver
    top_driver = max(waste_breakdown, key=lambda x: x["wasted_min_per_run"]) if waste_breakdown else None

    return {
        "waste_breakdown": waste_breakdown,
        "wasted_min_per_run": round(total_wasted_min_per_run, 1),
        "runs_per_month": runs_per_month,
        "wasted_min_per_month": round(wasted_min_per_month),
        "monthly_cost_public": round(monthly_cost_public, 2),
        "monthly_cost_private": round(monthly_cost_private, 2),
        "annual_cost_public": round(annual_cost_public, 2),
        "annual_cost_private": round(annual_cost_private, 2),
        "top_driver": top_driver["cause"] if top_driver else "No significant waste detected",
        "team_size": team_size,
        "commits_per_dev_per_day": commits_per_dev_per_day,
        "ai_enrichment": None,
    }


# ─── AI Enrichment (async) ────────────────────────────────────────────────────

COST_PROMPT = """You are the 💰 COST AGENT in a CI/CD Pipeline War Room.
Your ONLY mission: calculate the REAL dollar cost of this pipeline's inefficiencies.

GitHub Actions rates: Ubuntu = $0.008/min (public), $0.016/min (private repos).
Assume: 10 developers, 5 commits per developer per day, 22 working days/month.

Pre-calculated estimates:
- Wasted minutes per run: {wasted_min_per_run}
- Runs per month: {runs_per_month}
- Monthly waste (private repo): ${monthly_private}
- Annual waste (private repo): ${annual_private}

Output EXACTLY in this format (no extra text):
COST_FINDINGS:
WASTED_MIN_PER_RUN: {wasted_min_per_run}
RUNS_PER_MONTH: {runs_per_month}
WASTED_MIN_PER_MONTH: [calculated]
MONTHLY_WASTE_PRIVATE: ${monthly_private}
ANNUAL_WASTE_PRIVATE: ${annual_private}
TOP_COST_DRIVER: [single biggest waste item]
BIGGEST_WIN: [single optimization that saves the most money]
COST_FINDINGS_END

Pipeline to analyze:
{content}"""


async def enrich_with_ai(content: str, base_results: dict) -> dict:
    """Call Ollama for AI cost analysis enrichment."""
    prompt = COST_PROMPT.format(
        content=content[:2000],
        wasted_min_per_run=base_results["wasted_min_per_run"],
        runs_per_month=base_results["runs_per_month"],
        monthly_private=base_results["monthly_cost_private"],
        annual_private=base_results["annual_cost_private"],
    )
    output = await call_ollama_async(prompt)
    if output:
        base_results["ai_enrichment"] = output
    return base_results
