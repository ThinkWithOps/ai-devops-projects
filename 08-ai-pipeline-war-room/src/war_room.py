"""
AI Pipeline War Room — Main Orchestrator (Project 08)
3 AI agents analyze your pipeline simultaneously.
Commander resolves conflicts and delivers the battle plan.

Usage:
  python src/war_room.py --simulate nodejs
  python src/war_room.py --file .github/workflows/ci.yml
  python src/war_room.py --simulate python --no-ai --save-report
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime

# Add src/ to path when running as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import speed_agent, security_agent, cost_agent, commander_agent

# ─── Embedded Sample Pipelines ────────────────────────────────────────────────

SAMPLE_PIPELINES = {
    "nodejs": {
        "name": "slow_nodejs_pipeline.yml",
        "description": "Node.js app — hardcoded AWS keys, npm install ×4, sequential jobs",
    },
    "python": {
        "name": "slow_python_pipeline.yml",
        "description": "Python API — Docker password exposed, pip install ×3, no secret scanning",
    },
}

SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "demo", "sample_pipelines"
)

# ─── War Room Orchestrator ────────────────────────────────────────────────────

async def run_war_room(
    content: str,
    source_name: str,
    use_ai: bool = True,
    team_size: int = 10,
    commits_per_dev_per_day: int = 5,
    on_update=None,
) -> dict:
    """
    Run all 3 agents in parallel, then Commander resolves conflicts.
    on_update(state) is called after each phase to refresh the UI.
    """

    state = {
        "speed":     {"status": "SCANNING", "findings": [], "time_saved_min": 0, "jobs_to_remove": [], "jobs_to_parallelize": []},
        "security":  {"status": "SCANNING", "findings": [], "security_score": 10, "critical_jobs": []},
        "cost":      {"status": "SCANNING", "wasted_min_per_run": 0, "runs_per_month": 0, "monthly_cost_private": 0, "annual_cost_private": 0, "top_driver": ""},
        "commander": {"status": "WAITING", "conflicts": [], "battle_plan": [], "ai_enrichment": None},
    }

    if on_update:
        on_update(state, "🔍 Rule-Based Scan")

    # ── Phase 1: Rule-based analysis (all 3 agents — instant) ────────────────
    speed_base = speed_agent.run_rules(content)
    state["speed"].update({**speed_base, "status": "AI_ENRICHING" if use_ai else "DONE"})

    security_base = security_agent.run_rules(content)
    state["security"].update({**security_base, "status": "AI_ENRICHING" if use_ai else "DONE"})

    cost_base = cost_agent.run_rules(content, team_size=team_size,
                                     commits_per_dev_per_day=commits_per_dev_per_day)
    state["cost"].update({**cost_base, "status": "AI_ENRICHING" if use_ai else "DONE"})

    if on_update:
        on_update(state, "🤖 AI Enrichment" if use_ai else "📋 Generating Battle Plan")

    # ── Phase 2: AI enrichment (all 3 agents in parallel via asyncio) ────────
    if use_ai:
        speed_enriched, security_enriched, cost_enriched = await asyncio.gather(
            speed_agent.enrich_with_ai(content, speed_base),
            security_agent.enrich_with_ai(content, security_base),
            cost_agent.enrich_with_ai(content, cost_base),
        )
        state["speed"].update({**speed_enriched, "status": "DONE"})
        state["security"].update({**security_enriched, "status": "DONE"})
        state["cost"].update({**cost_enriched, "status": "DONE"})
    else:
        state["speed"]["status"] = "DONE"
        state["security"]["status"] = "DONE"
        state["cost"]["status"] = "DONE"

    if on_update:
        on_update(state, "⚔️  Commander Resolving Conflicts")

    # ── Phase 3: Commander conflict resolution ────────────────────────────────
    state["commander"]["status"] = "SCANNING"
    if on_update:
        on_update(state, "⚔️  Commander Resolving Conflicts")

    conflicts = commander_agent.find_conflicts(speed_base, security_base, cost_base)
    battle_plan = commander_agent.build_battle_plan(speed_base, security_base, cost_base, conflicts)
    state["commander"].update({"conflicts": conflicts, "battle_plan": battle_plan,
                                "status": "AI_ENRICHING" if use_ai else "DONE"})

    if on_update:
        on_update(state, "⚔️  Commander AI Analysis")

    if use_ai:
        commander_result = await commander_agent.enrich_with_ai(
            speed_base, security_base, cost_base, conflicts, battle_plan
        )
        state["commander"].update({**commander_result, "status": "DONE"})
    else:
        state["commander"]["status"] = "DONE"

    if on_update:
        on_update(state, "✅ War Room Complete")

    return state


def generate_report(state: dict, source_name: str) -> str:
    """Generate markdown War Room report."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    speed = state["speed"]
    security = state["security"]
    cost = state["cost"]
    commander = state["commander"]

    report = f"""# ⚔️ AI Pipeline War Room Report
**Pipeline:** {source_name}
**Generated:** {ts}

---

## Summary

| Agent | Findings | Key Metric |
|-------|---------|------------|
| 🚀 Speed | {len(speed.get('findings', []))} bottlenecks | ~{speed.get('time_saved_min', 0)} min/run savings |
| 🔒 Security | {len(security.get('findings', []))} vulnerabilities | Score: {security.get('security_score', 10)}/10 |
| 💰 Cost | ${cost.get('annual_cost_private', 0):,.0f}/year wasted | ${cost.get('monthly_cost_private', 0):,.2f}/month |

---

## 🚀 Speed Agent Findings

"""
    for f in speed.get("findings", []):
        report += f"### [{f['severity']}] {f['title']}\n"
        report += f"- **Impact:** {f['impact']}\n"
        report += f"- **Fix:** {f['fix']}\n\n"

    report += f"**Total time savings: ~{speed.get('time_saved_min', 0)} min/run**\n\n---\n\n"

    report += "## 🔒 Security Agent Findings\n\n"
    for f in security.get("findings", []):
        report += f"### [{f['severity']}] {f['title']}\n"
        report += f"- **Impact:** {f['impact']}\n"
        report += f"- **Fix:** {f['fix']}\n\n"
    report += f"**Security Score: {security.get('security_score', 10)}/10**\n\n---\n\n"

    report += "## 💰 Cost Agent Report\n\n"
    report += f"| Metric | Value |\n|--------|-------|\n"
    report += f"| Wasted per run | {cost.get('wasted_min_per_run', 0)} min |\n"
    report += f"| Runs per month | {cost.get('runs_per_month', 0):,} |\n"
    report += f"| Monthly waste (private) | ${cost.get('monthly_cost_private', 0):,.2f} |\n"
    report += f"| **Annual waste (private)** | **${cost.get('annual_cost_private', 0):,.2f}** |\n\n"
    report += f"Top driver: {cost.get('top_driver', '')}\n\n---\n\n"

    report += "## ⚔️ Commander — Conflicts & Battle Plan\n\n"
    for c in commander.get("conflicts", []):
        report += f"### 🚨 Conflict: {c['type'].replace('_', ' ')}\n"
        report += f"- **Speed wants:** {c['speed_wants']}\n"
        report += f"- **Security says:** {c['security_says']}\n"
        report += f"- **Resolution:** {c['resolution']}\n"
        report += f"- **Net result:** {c['net_result']}\n\n"

    report += "### 📋 Battle Plan\n\n"
    for item in commander.get("battle_plan", []):
        report += f"**{item['priority']}. [{item['label']}] {item['action']}**\n"
        report += f"- Fix: {item['fix']}\n"
        report += f"- Agents: {' '.join(item['agents'])}\n"
        report += f"- Why: {item['why']}\n\n"

    if commander.get("ai_enrichment"):
        report += f"---\n\n## 🤖 Commander AI Assessment\n\n{commander['ai_enrichment']}\n\n"

    report += "---\n\n*Generated by AI Pipeline War Room — Project 08 of the AI+DevOps Series*\n"
    return report


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="⚔️  AI Pipeline War Room — 3 agents analyze your pipeline simultaneously"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Path to pipeline YAML file")
    group.add_argument("--simulate", choices=["nodejs", "python"],
                       help="Run with a built-in slow pipeline sample")
    parser.add_argument("--no-ai", action="store_true", help="Skip Ollama (rule-based only — much faster)")
    parser.add_argument("--save-report", action="store_true", help="Save markdown report to reports/")
    parser.add_argument("--team-size", type=int, default=10, help="Team size for cost calculation (default: 10)")
    parser.add_argument("--commits-per-day", type=int, default=5, help="Commits per dev per day (default: 5)")
    parser.add_argument("--no-live", action="store_true", help="Disable Rich live display (plain output)")
    args = parser.parse_args()

    # Load pipeline content
    if args.simulate:
        sample = SAMPLE_PIPELINES[args.simulate]
        pipeline_path = os.path.join(SAMPLE_DIR, sample["name"])
        if not os.path.exists(pipeline_path):
            print(f"❌ Sample file not found: {pipeline_path}")
            sys.exit(1)
        with open(pipeline_path, "r", encoding="utf-8") as f:
            content = f.read()
        source_name = sample["name"]
        print(f"\n📂 Loading sample: {sample['name']}")
        print(f"   {sample['description']}\n")
    else:
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
        source_name = os.path.basename(args.file)
        print(f"\n📂 Analyzing: {source_name}\n")

    use_ai = not args.no_ai

    # Try Rich Live display, fallback to plain output
    use_live = not args.no_live
    try:
        from rich.live import Live
        from rich_ui import render_layout, print_final_report
        _rich_available = True
    except ImportError:
        _rich_available = False
        use_live = False

    if use_live and _rich_available:
        _live_state = {}
        _live_phase = ["Initializing"]

        from rich_ui import render_layout, print_final_report

        def on_update(state, phase):
            _live_state.update(state)
            _live_phase[0] = phase

        with Live(render_layout({}, source_name, "Initializing"), refresh_per_second=4) as live:
            def update_live(state, phase):
                on_update(state, phase)
                live.update(render_layout(state, source_name, phase))

            if use_ai:
                print("🤖 AI enabled — Ollama calls dispatched in parallel (30–90s)")

            state = asyncio.run(run_war_room(
                content, source_name,
                use_ai=use_ai,
                team_size=args.team_size,
                commits_per_dev_per_day=args.commits_per_day,
                on_update=update_live,
            ))

        print("\n")
        print_final_report(state, source_name)

    else:
        # Plain terminal output
        print("⚔️  AI PIPELINE WAR ROOM")
        print("=" * 60)
        if use_ai:
            print("🤖 AI enabled — Ollama calls dispatched in parallel...\n")
        else:
            print("⚡ Rule-based mode (--no-ai)\n")

        state = asyncio.run(run_war_room(
            content, source_name,
            use_ai=use_ai,
            team_size=args.team_size,
            commits_per_dev_per_day=args.commits_per_day,
        ))

        if _rich_available:
            from rich_ui import print_final_report
            print_final_report(state, source_name)
        else:
            # Minimal fallback
            print("\n🚀 SPEED:", len(state["speed"]["findings"]), "bottlenecks found,",
                  state["speed"]["time_saved_min"], "min/run savings")
            print("🔒 SECURITY:", len(state["security"]["findings"]), "vulnerabilities,",
                  f"score: {state['security']['security_score']}/10")
            print("💰 COST: $" + f"{state['cost']['annual_cost_private']:,.2f}/year wasted")
            print("⚔️  COMMANDER:", len(state["commander"]["conflicts"]), "conflict(s),",
                  len(state["commander"]["battle_plan"]), "battle plan items")

    # Save report
    if args.save_report:
        os.makedirs("reports", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"reports/war_room_{ts}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(generate_report(state, source_name))
        print(f"\n📄 Report saved: {path}")


if __name__ == "__main__":
    main()
