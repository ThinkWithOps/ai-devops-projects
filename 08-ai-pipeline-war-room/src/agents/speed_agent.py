"""
🚀 Speed Agent — finds CI/CD performance bottlenecks.
Phase 1: instant rule-based scan. Phase 2: Ollama AI enrichment.
"""

import re
from .base_agent import call_ollama_async

AGENT_NAME = "🚀 SPEED AGENT"

# ─── Rule-Based Analysis (instant) ───────────────────────────────────────────

def run_rules(content: str) -> dict:
    findings = []
    jobs_to_remove = []
    jobs_to_parallelize = []
    time_saved_min = 0

    # 1. npm install without cache
    npm_count = content.count("npm install") + content.count("npm ci")
    has_npm_cache = "cache: 'npm'" in content or 'cache: "npm"' in content
    if npm_count > 1 and not has_npm_cache:
        wasted = (npm_count - 1) * 2
        time_saved_min += wasted
        findings.append({
            "severity": "HIGH",
            "title": f"npm install runs {npm_count}× — no npm cache",
            "impact": f"~{wasted} min wasted per run",
            "fix": "Add `cache: 'npm'` to actions/setup-node; replace npm install with npm ci",
        })

    # 2. pip install without cache
    pip_count = len(re.findall(r"pip install", content))
    has_pip_cache = "cache: 'pip'" in content or 'cache: "pip"' in content
    if pip_count > 1 and not has_pip_cache:
        wasted = (pip_count - 1) * 1
        time_saved_min += wasted
        findings.append({
            "severity": "HIGH",
            "title": f"pip install runs {pip_count}× — no pip cache",
            "impact": f"~{wasted} min wasted per run",
            "fix": "Add `cache: 'pip'` to actions/setup-python",
        })

    # 3. Redundant dedicated install job
    install_jobs = re.findall(r"^  (install[\w-]*):", content, re.MULTILINE)
    if install_jobs and (npm_count > 1 or pip_count > 1):
        for job in install_jobs:
            jobs_to_remove.append(job)
        time_saved_min += 2
        findings.append({
            "severity": "MEDIUM",
            "title": f"Dedicated '{install_jobs[0]}' job is redundant — each job re-installs anyway",
            "impact": "~2 min wasted per run on a job that accomplishes nothing",
            "fix": "Remove install job — use cache in each downstream job",
            "jobs_to_remove": install_jobs,
        })

    # 4. Sequential jobs that could be parallel
    lint_needs = re.search(r"^  lint\b.*?\n\s+needs:", content, re.MULTILINE | re.DOTALL)
    test_needs = re.search(r"^  test\b.*?\n\s+needs:", content, re.MULTILINE | re.DOTALL)
    sec_needs = re.search(r"^  security\b.*?\n\s+needs:", content, re.MULTILINE | re.DOTALL)
    parallel_candidates = []
    if lint_needs:
        parallel_candidates.append("lint")
    if test_needs:
        parallel_candidates.append("test")
    if sec_needs:
        parallel_candidates.append("security")
    if len(parallel_candidates) >= 2:
        jobs_to_parallelize.extend(parallel_candidates)
        time_saved_min += len(parallel_candidates) - 1
        findings.append({
            "severity": "HIGH",
            "title": f"Jobs ({', '.join(parallel_candidates)}) run sequentially — could be parallel",
            "impact": f"~{len(parallel_candidates) - 1} min extra wall time per run",
            "fix": f"Remove cross-dependencies between {', '.join(parallel_candidates)}",
            "jobs_to_parallelize": parallel_candidates,
        })

    # 5. Docker build without cache
    if "docker build" in content and "--cache-from" not in content:
        time_saved_min += 2
        findings.append({
            "severity": "HIGH",
            "title": "Docker build has no layer cache (--cache-from missing)",
            "impact": "~2–4 min full rebuild every run",
            "fix": "Pull cache tag first, then `docker build --cache-from myapp:cache`",
        })

    # 6. No timeout-minutes
    runs_on_count = len(re.findall(r"runs-on:", content))
    if runs_on_count > 0 and "timeout-minutes" not in content:
        findings.append({
            "severity": "MEDIUM",
            "title": f"{runs_on_count} job(s) have no timeout-minutes",
            "impact": "Hung jobs waste runner minutes and block queue",
            "fix": "Add `timeout-minutes: 15` to each job",
        })

    return {
        "findings": findings,
        "time_saved_min": time_saved_min,
        "jobs_to_remove": jobs_to_remove,
        "jobs_to_parallelize": jobs_to_parallelize,
        "ai_enrichment": None,
    }


# ─── AI Enrichment (async) ────────────────────────────────────────────────────

SPEED_PROMPT = """You are the 🚀 SPEED AGENT in a CI/CD Pipeline War Room.
Your ONLY mission: find every performance bottleneck in this pipeline.
Be aggressive. Every second counts.

Output EXACTLY in this format (no extra text):
SPEED_FINDINGS:
BOTTLENECK_1: [description] | IMPACT: [X min saved] | FIX: [exact code/command]
BOTTLENECK_2: [description] | IMPACT: [X min saved] | FIX: [exact code/command]
TOTAL_MINUTES_SAVED: [number]
JOBS_TO_REMOVE: [comma-separated job names, or NONE]
JOBS_TO_PARALLELIZE: [comma-separated job names, or NONE]
SPEED_FINDINGS_END

Pipeline to analyze:
{content}"""


async def enrich_with_ai(content: str, base_results: dict) -> dict:
    """Call Ollama for deeper speed analysis. Returns enriched results."""
    prompt = SPEED_PROMPT.format(content=content[:3000])
    output = await call_ollama_async(prompt)
    if output:
        base_results["ai_enrichment"] = output
    return base_results
