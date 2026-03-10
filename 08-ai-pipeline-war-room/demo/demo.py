"""
AI Pipeline War Room — CLI Demo
Runs both sample pipelines with rule-based analysis (no AI needed).
Run from project root: python demo/demo.py
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from war_room import run_war_room, SAMPLE_PIPELINES, SAMPLE_DIR

SEPARATOR = "=" * 65


def print_state(state, source_name):
    speed = state["speed"]
    security = state["security"]
    cost = state["cost"]
    commander = state["commander"]

    print(f"\n  ⚔️  WAR ROOM RESULTS: {source_name}")
    print(f"  {'─' * 50}")
    print(f"  🚀 Speed:    {len(speed.get('findings', []))} bottleneck(s) | ~{speed.get('time_saved_min', 0)} min/run savings")
    print(f"  🔒 Security: {len(security.get('findings', []))} vulnerability(s) | Score: {security.get('security_score', 10)}/10")
    print(f"  💰 Cost:     ${cost.get('annual_cost_private', 0):,.2f}/year wasted (private repo)")
    print(f"  ⚔️  Conflicts: {len(commander.get('conflicts', []))} detected")

    print(f"\n  🚨 Top Issues:")
    all_findings = (
        [("🚀", f) for f in speed.get("findings", []) if f["severity"] == "HIGH"] +
        [("🔒", f) for f in security.get("findings", []) if f["severity"] == "CRITICAL"]
    )
    for icon, f in all_findings[:4]:
        print(f"    {icon} [{f['severity']}] {f['title']}")

    if commander.get("conflicts"):
        print(f"\n  ⚔️  Commander Conflict:")
        c = commander["conflicts"][0]
        print(f"    🚨 {c['type'].replace('_', ' ')}")
        print(f"    ✅ Resolution: {c['resolution'][:80]}...")

    print(f"\n  📋 Battle Plan (top 3):")
    for item in commander.get("battle_plan", [])[:3]:
        print(f"    {item['priority']}. [{item['label']}] {item['action'][:60]}")


async def run_demo():
    print(f"\n{SEPARATOR}")
    print("  ⚔️  AI PIPELINE WAR ROOM — Demo")
    print(f"{SEPARATOR}")
    print("  Running rule-based analysis on 2 sample pipelines...")
    print("  (Use --simulate nodejs to run with AI analysis)\n")

    for key, info in SAMPLE_PIPELINES.items():
        pipeline_path = os.path.join(SAMPLE_DIR, info["name"])
        if not os.path.exists(pipeline_path):
            print(f"  ⚠️  Sample not found: {pipeline_path}")
            continue

        with open(pipeline_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"\n{SEPARATOR}")
        print(f"  📂 {info['name']}")
        print(f"  {info['description']}")
        print(SEPARATOR)

        state = await run_war_room(
            content,
            source_name=info["name"],
            use_ai=False,
        )
        print_state(state, info["name"])

    print(f"\n{SEPARATOR}")
    print("  Demo complete!")
    print(f"{SEPARATOR}")
    print()
    print("  Full War Room experience:")
    print("  → python src/war_room.py --simulate nodejs")
    print("  → python src/war_room.py --file .github/workflows/ci.yml")
    print()


if __name__ == "__main__":
    asyncio.run(run_demo())
