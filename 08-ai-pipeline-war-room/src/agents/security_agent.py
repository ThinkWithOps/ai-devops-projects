"""
🔒 Security Agent — finds CI/CD security vulnerabilities.
Phase 1: instant rule-based scan. Phase 2: Ollama AI enrichment.
"""

import re
from .base_agent import call_ollama_async

AGENT_NAME = "🔒 SECURITY AGENT"

# ─── Secret Patterns ──────────────────────────────────────────────────────────

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "CRITICAL", "Hardcoded AWS Access Key ID"),
    (r"(?i)(aws_secret_access_key|aws_secret)\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}", "CRITICAL", "Hardcoded AWS Secret Key"),
    (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"${}]{6,}", "CRITICAL", "Hardcoded password"),
    (r"(?i)(token|api_key|apikey|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}", "HIGH", "Hardcoded token/API key"),
    (r"ghp_[A-Za-z0-9]{36}", "CRITICAL", "Hardcoded GitHub Personal Access Token"),
    (r"(?i)docker.*password.*[:=]\s*[^\s${}]{6,}", "CRITICAL", "Hardcoded Docker registry password"),
]

# ─── Rule-Based Analysis (instant) ───────────────────────────────────────────

def run_rules(content: str) -> dict:
    findings = []
    critical_jobs = []   # Jobs security depends on — Speed cannot remove these
    security_score = 10  # Start perfect, deduct per issue

    # 1. Hardcoded secrets
    for pattern, severity, label in SECRET_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            deduction = 3 if severity == "CRITICAL" else 2
            security_score -= deduction
            findings.append({
                "severity": severity,
                "title": f"{label} detected in pipeline YAML",
                "impact": "Credentials exposed in Git history — immediate breach risk",
                "fix": "Use GitHub Secrets: `${{ secrets.MY_SECRET }}` — rotate credentials NOW",
            })

    # 2. Over-permissioned token
    if "permissions: write-all" in content:
        security_score -= 2
        findings.append({
            "severity": "HIGH",
            "title": "`permissions: write-all` — GITHUB_TOKEN has full write access",
            "impact": "Compromised workflow can write to any branch, publish packages, create releases",
            "fix": "Use least-privilege: `permissions: contents: read` (or per-job permissions)",
        })
    elif re.search(r"permissions:\s*\n\s+\w+:\s*write", content):
        security_score -= 1
        findings.append({
            "severity": "MEDIUM",
            "title": "GITHUB_TOKEN has write permissions — review if all write scopes are needed",
            "impact": "Broader blast radius if workflow is compromised",
            "fix": "Scope permissions to minimum required per job",
        })

    # 3. No secret scanning step
    has_secret_scan = any(t in content.lower() for t in ["gitleaks", "trufflehog", "git-secrets", "detect-secrets", "secret-scan"])
    if not has_secret_scan:
        security_score -= 2
        findings.append({
            "severity": "HIGH",
            "title": "No secret scanning step in pipeline",
            "impact": "Developers can accidentally commit credentials — pipeline won't catch it",
            "fix": "Add gitleaks step: `uses: gitleaks/gitleaks-action@v2`",
        })

    # 4. Actions not pinned to SHA
    action_refs = re.findall(r"uses: [\w/.-]+@(v?\d[\w.]*)", content)
    unpinned = [r for r in action_refs if not re.match(r"[0-9a-f]{40}", r)]
    if len(unpinned) >= 2:
        security_score -= 1
        findings.append({
            "severity": "MEDIUM",
            "title": f"{len(unpinned)} action(s) use tag refs (not SHA-pinned)",
            "impact": "Tag can be moved — supply chain attack risk if upstream is compromised",
            "fix": "Pin to full commit SHA: `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683`",
        })

    # 5. No OIDC — using long-lived credentials for cloud
    has_oidc = "id-token: write" in content or "configure-aws-credentials" in content
    has_aws_keys = any(p in content for p in ["AWS_ACCESS_KEY_ID", "aws_access_key"])
    if has_aws_keys and not has_oidc:
        security_score -= 2
        findings.append({
            "severity": "HIGH",
            "title": "Long-lived AWS credentials used — OIDC not configured",
            "impact": "Leaked keys give permanent AWS access — OIDC tokens expire in minutes",
            "fix": "Use OIDC: `aws-actions/configure-aws-credentials` with role-to-assume",
        })

    # 6. No container image scanning after Docker build
    if "docker build" in content and not any(t in content.lower() for t in ["trivy", "snyk", "grype", "anchore", "docker scout"]):
        security_score -= 1
        findings.append({
            "severity": "MEDIUM",
            "title": "Docker image built but not scanned for vulnerabilities",
            "impact": "Known CVEs shipped to production without detection",
            "fix": "Add Trivy scan: `uses: aquasecurity/trivy-action@master`",
        })

    # Track which jobs handle security (Speed cannot remove these)
    for job_pattern in ["security", "scan", "audit", "secret"]:
        jobs = re.findall(rf"^  ({job_pattern}[\w-]*):", content, re.MULTILINE | re.IGNORECASE)
        critical_jobs.extend(jobs)
    # Also mark install jobs as potential security gates
    install_jobs = re.findall(r"^  (install[\w-]*):", content, re.MULTILINE)
    if not has_secret_scan and install_jobs:
        # install job could be repurposed as security gate
        critical_jobs.extend(install_jobs)

    security_score = max(0, security_score)

    return {
        "findings": findings,
        "security_score": security_score,
        "critical_jobs": list(set(critical_jobs)),
        "ai_enrichment": None,
    }


# ─── AI Enrichment (async) ────────────────────────────────────────────────────

SECURITY_PROMPT = """You are the 🔒 SECURITY AGENT in a CI/CD Pipeline War Room.
Your ONLY mission: find every security vulnerability. Be DRAMATIC about risks.
Every vulnerability is a potential breach. Assume attackers are watching.

Output EXACTLY in this format (no extra text):
SECURITY_FINDINGS:
VULN_1: [description] | SEVERITY: [CRITICAL/HIGH/MEDIUM] | JOB: [job name or GLOBAL]
VULN_2: [description] | SEVERITY: [CRITICAL/HIGH/MEDIUM] | JOB: [job name or GLOBAL]
SECURITY_SCORE: [0-10, 10=perfect]
CRITICAL_JOBS: [jobs that CANNOT be removed — security depends on them, comma-separated, or NONE]
IMMEDIATE_ACTION: [one sentence — what to do RIGHT NOW]
SECURITY_FINDINGS_END

Pipeline to analyze:
{content}"""


async def enrich_with_ai(content: str, base_results: dict) -> dict:
    """Call Ollama for deeper security analysis. Returns enriched results."""
    prompt = SECURITY_PROMPT.format(content=content[:3000])
    output = await call_ollama_async(prompt)
    if output:
        base_results["ai_enrichment"] = output
    return base_results
