"""
⚔️  Commander Agent — resolves conflicts between Speed, Security, and Cost agents.
Produces a prioritized 5-point battle plan with explicit tradeoff reasoning.
"""

from .base_agent import call_ollama_async

AGENT_NAME = "⚔️  COMMANDER"


# ─── Rule-Based Conflict Detection (instant) ─────────────────────────────────

def find_conflicts(speed_report: dict, security_report: dict, cost_report: dict) -> list:
    """
    Find conflicts where Speed's recommendations conflict with Security's requirements.
    Returns list of conflict dicts with explicit resolution reasoning.
    """
    conflicts = []

    speed_remove = set(speed_report.get("jobs_to_remove", []))
    speed_parallel = set(speed_report.get("jobs_to_parallelize", []))
    security_critical = set(security_report.get("critical_jobs", []))

    # Conflict 1: Speed wants to remove a job that Security depends on
    removal_conflicts = speed_remove & security_critical
    for job in removal_conflicts:
        conflicts.append({
            "type": "REMOVAL_VS_SECURITY",
            "severity": "CRITICAL",
            "speed_wants": f"Remove '{job}' job (redundant install job)",
            "security_says": f"'{job}' must persist — it's the designated security gate for secret scanning",
            "resolution": (
                f"KEEP '{job}' but REPURPOSE it: remove npm install, add gitleaks secret scan. "
                f"Rename to 'security-gate'. Saves install waste while adding security coverage."
            ),
            "net_result": "Saves ~2 min install waste + adds secret scanning — both agents win",
        })

    # Conflict 2: Speed wants to parallelize security-adjacent jobs
    if "security" in speed_parallel and security_report.get("findings"):
        critical_security = [f for f in security_report["findings"] if f["severity"] == "CRITICAL"]
        if critical_security:
            conflicts.append({
                "type": "PARALLEL_VS_SECURITY_GATE",
                "severity": "HIGH",
                "speed_wants": "Run security job in parallel with test (no ordering)",
                "security_says": "CRITICAL vulnerabilities found — security must be a gate, not parallel",
                "resolution": (
                    "Run security AFTER lint+test complete (not before), but parallel with build. "
                    "Security failures block the build, maintaining the gate without slowing dev jobs."
                ),
                "net_result": "~1 min slower than full parallel, but maintains security posture",
            })

    # Conflict 3: Speed saves time but Cost shows the savings are small vs security risk
    if cost_report["wasted_min_per_run"] > 0 and security_report.get("findings"):
        critical_vulns = [f for f in security_report["findings"] if f["severity"] == "CRITICAL"]
        if critical_vulns:
            conflicts.append({
                "type": "SPEED_VS_BREACH_COST",
                "severity": "CRITICAL",
                "speed_wants": f"Optimize for {cost_report['wasted_min_per_run']} min/run savings",
                "security_says": "Pipeline has CRITICAL credentials exposed — breach cost >> runner savings",
                "resolution": (
                    f"Annual runner savings: ${cost_report['annual_cost_private']:.0f}. "
                    f"Average breach cost: $4.5M (IBM 2024). "
                    f"Fix credentials FIRST (zero cost), then optimize speed."
                ),
                "net_result": "Security fix is priority-zero — it's free and the risk is existential",
            })

    return conflicts


def build_battle_plan(speed_report: dict, security_report: dict,
                      cost_report: dict, conflicts: list) -> list:
    """Build prioritized 5-point battle plan from all agent reports."""
    plan = []

    # Always lead with CRITICAL security if present
    critical_findings = [f for f in security_report.get("findings", []) if f["severity"] == "CRITICAL"]
    for finding in critical_findings[:2]:
        plan.append({
            "priority": 1,
            "label": "CRITICAL",
            "action": finding["title"],
            "fix": finding["fix"],
            "agents": ["🔒 Security", "💰 Cost"],
            "why": "Breach risk >> any performance gain",
        })

    # Highest-impact speed fix
    high_speed = [f for f in speed_report.get("findings", []) if f["severity"] == "HIGH"]
    if high_speed:
        top = high_speed[0]
        plan.append({
            "priority": len(plan) + 1,
            "label": "HIGH",
            "action": top["title"],
            "fix": top["fix"],
            "agents": ["🚀 Speed", "💰 Cost"],
            "why": f"Saves ${cost_report['annual_cost_private']:.0f}/year in runner costs",
        })

    # Conflict resolution (if any)
    for conflict in conflicts[:1]:
        plan.append({
            "priority": len(plan) + 1,
            "label": "HIGH",
            "action": f"Resolve conflict: {conflict['type'].replace('_', ' ')}",
            "fix": conflict["resolution"],
            "agents": ["⚔️  Commander"],
            "why": conflict["net_result"],
        })

    # Remaining speed fixes
    for f in high_speed[1:3]:
        if len(plan) >= 5:
            break
        plan.append({
            "priority": len(plan) + 1,
            "label": "MEDIUM",
            "action": f['title'],
            "fix": f['fix'],
            "agents": ["🚀 Speed"],
            "why": f["impact"],
        })

    # Fill to 5 with medium security findings
    medium_security = [f for f in security_report.get("findings", []) if f["severity"] in ("HIGH", "MEDIUM")]
    for f in medium_security:
        if len(plan) >= 5:
            break
        plan.append({
            "priority": len(plan) + 1,
            "label": "MEDIUM",
            "action": f['title'],
            "fix": f['fix'],
            "agents": ["🔒 Security"],
            "why": f["impact"],
        })

    return plan[:5]


# ─── AI Enrichment (async) ────────────────────────────────────────────────────

COMMANDER_PROMPT = """You are the ⚔️ COMMANDER AGENT in a CI/CD Pipeline War Room.
Three specialist agents have analyzed this pipeline. Your job is to RESOLVE CONFLICTS
between them and produce the final battle plan.

SPEED AGENT REPORT:
Bottlenecks: {speed_count} found | Time saved: {time_saved} min/run
Jobs to remove: {jobs_remove}
Jobs to parallelize: {jobs_parallel}

SECURITY AGENT REPORT:
Vulnerabilities: {security_count} found | Score: {security_score}/10
Critical jobs (cannot remove): {critical_jobs}

COST AGENT REPORT:
Wasted: {wasted_min} min/run | Monthly loss: ${monthly_cost}
Annual loss: ${annual_cost}

CONFLICTS DETECTED: {conflict_count}
{conflict_text}

Produce your final assessment in EXACTLY this format:
COMMANDER_ASSESSMENT:
CONFLICT_WINNER: [Speed/Security/Both — who wins each conflict and WHY in one sentence each]
BATTLE_PLAN:
1. [CRITICAL/HIGH/MEDIUM] [Action] — [agents that agree]
2. [action]
3. [action]
4. [action]
5. [action]
MONTHLY_SAVINGS_ESTIMATE: $[amount]
COMMANDER_ASSESSMENT_END"""


async def enrich_with_ai(speed_report: dict, security_report: dict,
                         cost_report: dict, conflicts: list, base_plan: list) -> dict:
    """Call Ollama for Commander-level synthesis and conflict resolution."""

    conflict_text = "\n".join(
        f"  CONFLICT: {c['speed_wants']} VS {c['security_says']}"
        for c in conflicts
    ) if conflicts else "  No conflicts detected"

    prompt = COMMANDER_PROMPT.format(
        speed_count=len(speed_report.get("findings", [])),
        time_saved=speed_report.get("time_saved_min", 0),
        jobs_remove=", ".join(speed_report.get("jobs_to_remove", [])) or "none",
        jobs_parallel=", ".join(speed_report.get("jobs_to_parallelize", [])) or "none",
        security_count=len(security_report.get("findings", [])),
        security_score=security_report.get("security_score", 10),
        critical_jobs=", ".join(security_report.get("critical_jobs", [])) or "none",
        wasted_min=cost_report.get("wasted_min_per_run", 0),
        monthly_cost=cost_report.get("monthly_cost_private", 0),
        annual_cost=cost_report.get("annual_cost_private", 0),
        conflict_count=len(conflicts),
        conflict_text=conflict_text,
    )

    output = await call_ollama_async(prompt)
    return {
        "conflicts": conflicts,
        "battle_plan": base_plan,
        "ai_enrichment": output,
    }
