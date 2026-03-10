"""
Rich terminal UI for the AI Pipeline War Room.
Renders a live 4-panel War Room dashboard.
"""

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich import box

# Status colors
STATUS_COLORS = {
    "WAITING":      "dim white",
    "SCANNING":     "bold yellow",
    "AI_ENRICHING": "bold cyan",
    "DONE":         "bold green",
    "ERROR":        "bold red",
}

SEVERITY_COLORS = {
    "CRITICAL": "bold red",
    "HIGH":     "bold orange1",
    "MEDIUM":   "bold yellow",
    "LOW":      "dim white",
}


def _status_badge(status: str) -> Text:
    icons = {
        "WAITING":      "⏸ WAITING",
        "SCANNING":     "🔍 SCANNING...",
        "AI_ENRICHING": "🤖 AI ENRICHING...",
        "DONE":         "✅ DONE",
        "ERROR":        "❌ ERROR",
    }
    color = STATUS_COLORS.get(status, "white")
    return Text(icons.get(status, status), style=color)


def render_speed_panel(state: dict) -> Panel:
    content = Text()
    content.append(_status_badge(state.get("status", "WAITING")))
    content.append("\n\n")

    findings = state.get("findings", [])
    if not findings:
        content.append("No findings yet...\n", style="dim")
    else:
        for f in findings:
            color = SEVERITY_COLORS.get(f["severity"], "white")
            content.append(f"  [{f['severity']}] ", style=color)
            content.append(f"{f['title']}\n", style="white")
            content.append(f"  → {f['impact']}\n\n", style="dim")

    time_saved = state.get("time_saved_min", 0)
    if time_saved > 0:
        content.append(f"\n⚡ Total savings: ~{time_saved} min/run", style="bold green")

    return Panel(
        content,
        title="[bold yellow]🚀 SPEED AGENT[/bold yellow]",
        border_style="yellow",
        padding=(0, 1),
    )


def render_security_panel(state: dict) -> Panel:
    content = Text()
    content.append(_status_badge(state.get("status", "WAITING")))

    score = state.get("security_score")
    if score is not None:
        score_color = "bold green" if score >= 8 else "bold yellow" if score >= 5 else "bold red"
        content.append("   ")
        content.append(f"🛡 Score: {score}/10", style=score_color)

    content.append("\n\n")

    findings = state.get("findings", [])
    if not findings:
        content.append("No findings yet...\n", style="dim")
    else:
        for f in findings:
            color = SEVERITY_COLORS.get(f["severity"], "white")
            content.append(f"  [{f['severity']}] ", style=color)
            content.append(f"{f['title']}\n", style="white")
            content.append(f"  → {f['impact']}\n\n", style="dim")

    return Panel(
        content,
        title="[bold red]🔒 SECURITY AGENT[/bold red]",
        border_style="red",
        padding=(0, 1),
    )


def render_cost_panel(state: dict) -> Panel:
    content = Text()
    content.append(_status_badge(state.get("status", "WAITING")))
    content.append("\n\n")

    if state.get("wasted_min_per_run", 0) == 0 and state.get("status") in ("WAITING", "SCANNING"):
        content.append("Calculating costs...\n", style="dim")
    else:
        wasted = state.get("wasted_min_per_run", 0)
        runs = state.get("runs_per_month", 0)
        monthly = state.get("monthly_cost_private", 0)
        annual = state.get("annual_cost_private", 0)

        content.append(f"  Wasted per run:    ", style="dim")
        content.append(f"{wasted} min\n", style="bold white")
        content.append(f"  Runs per month:    ", style="dim")
        content.append(f"{runs:,}\n", style="bold white")
        content.append(f"  Monthly waste:     ", style="dim")
        content.append(f"${monthly:,.2f}\n", style="bold red")
        content.append(f"  Annual waste:      ", style="dim")
        content.append(f"${annual:,.2f}\n", style="bold red")

        top = state.get("top_driver", "")
        if top:
            content.append(f"\n💸 Top driver:\n  {top}", style="dim")

    return Panel(
        content,
        title="[bold green]💰 COST AGENT[/bold green]",
        border_style="green",
        padding=(0, 1),
    )


def render_commander_panel(state: dict) -> Panel:
    content = Text()
    content.append(_status_badge(state.get("status", "WAITING")))
    content.append("\n\n")

    conflicts = state.get("conflicts", [])
    if conflicts:
        content.append("CONFLICTS DETECTED:\n", style="bold red")
        for c in conflicts:
            content.append(f"\n  🚨 {c['type'].replace('_', ' ')}\n", style="bold red")
            content.append(f"  ⚡ Speed: {c['speed_wants']}\n", style="yellow")
            content.append(f"  🔒 Security: {c['security_says']}\n", style="red")
            content.append(f"  ✅ Resolution: {c['resolution']}\n", style="green")
            content.append(f"  Net result: {c['net_result']}\n", style="dim")

    battle_plan = state.get("battle_plan", [])
    if battle_plan:
        content.append("\n📋 BATTLE PLAN:\n", style="bold white")
        for item in battle_plan:
            label_color = {
                "CRITICAL": "bold red",
                "HIGH": "bold orange1",
                "MEDIUM": "bold yellow",
            }.get(item["label"], "white")
            content.append(f"\n  {item['priority']}. ", style="bold white")
            content.append(f"[{item['label']}] ", style=label_color)
            content.append(f"{item['action']}\n", style="white")
            content.append(f"     → {item['fix']}\n", style="dim")
            content.append(f"     Agents: {' '.join(item['agents'])}\n", style="dim cyan")

    ai = state.get("ai_enrichment")
    if ai:
        # Extract just the monthly savings line if present
        import re
        savings_match = re.search(r"MONTHLY_SAVINGS_ESTIMATE:\s*(\$[\d,\.]+)", ai)
        if savings_match:
            content.append(f"\n💰 AI Estimated Monthly Savings: {savings_match.group(1)}", style="bold green")

    if not conflicts and not battle_plan:
        content.append("Waiting for agents to complete...\n", style="dim")

    return Panel(
        content,
        title="[bold magenta]⚔️  COMMANDER AGENT — CONFLICT RESOLUTION[/bold magenta]",
        border_style="magenta",
        padding=(0, 1),
    )


def render_header(source_name: str, phase: str) -> Panel:
    content = Text(justify="center")
    content.append("⚔️  AI PIPELINE WAR ROOM  ⚔️\n", style="bold red")
    content.append(f"Pipeline: {source_name}  │  Phase: {phase}", style="dim")
    return Panel(content, border_style="dim red", padding=(0, 2))


def render_layout(state: dict, source_name: str, phase: str) -> Layout:
    """Build the full terminal layout from current War Room state."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="agents", size=20),
        Layout(name="commander", minimum_size=10),
    )
    layout["agents"].split_row(
        Layout(name="speed"),
        Layout(name="security"),
        Layout(name="cost"),
    )

    layout["header"].update(render_header(source_name, phase))
    layout["speed"].update(render_speed_panel(state.get("speed", {})))
    layout["security"].update(render_security_panel(state.get("security", {})))
    layout["cost"].update(render_cost_panel(state.get("cost", {})))
    layout["commander"].update(render_commander_panel(state.get("commander", {})))

    return layout


def print_final_report(state: dict, source_name: str):
    """Print a clean final War Room report to terminal (no live required)."""
    from rich.console import Console
    from rich.rule import Rule
    console = Console()

    console.print()
    console.print(Rule("[bold red]⚔️  WAR ROOM FINAL REPORT[/bold red]"))
    console.print(f"[dim]Pipeline: {source_name}[/dim]\n")

    # Speed
    console.print("[bold yellow]🚀 SPEED AGENT[/bold yellow]")
    speed = state.get("speed", {})
    for f in speed.get("findings", []):
        color = SEVERITY_COLORS.get(f["severity"], "white")
        console.print(f"  [{f['severity']}] {f['title']}", style=color)
        console.print(f"       {f['fix']}", style="dim")
    console.print(f"  ⚡ Total savings: ~{speed.get('time_saved_min', 0)} min/run\n", style="green")

    # Security
    console.print("[bold red]🔒 SECURITY AGENT[/bold red]")
    security = state.get("security", {})
    for f in security.get("findings", []):
        color = SEVERITY_COLORS.get(f["severity"], "white")
        console.print(f"  [{f['severity']}] {f['title']}", style=color)
        console.print(f"       {f['fix']}", style="dim")
    score = security.get("security_score", 10)
    score_color = "green" if score >= 8 else "yellow" if score >= 5 else "red"
    console.print(f"  🛡  Security Score: {score}/10\n", style=score_color)

    # Cost
    console.print("[bold green]💰 COST AGENT[/bold green]")
    cost = state.get("cost", {})
    console.print(f"  Wasted per run:    {cost.get('wasted_min_per_run', 0)} min")
    console.print(f"  Monthly waste:     ${cost.get('monthly_cost_private', 0):,.2f}")
    console.print(f"  Annual waste:      ${cost.get('annual_cost_private', 0):,.2f}\n")

    # Commander
    console.print("[bold magenta]⚔️  COMMANDER — BATTLE PLAN[/bold magenta]")
    commander = state.get("commander", {})
    for c in commander.get("conflicts", []):
        console.print(f"\n  🚨 CONFLICT: {c['type'].replace('_', ' ')}", style="bold red")
        console.print(f"  Resolution: {c['resolution']}", style="green")
    console.print()
    for item in commander.get("battle_plan", []):
        label_color = {"CRITICAL": "red", "HIGH": "orange1", "MEDIUM": "yellow"}.get(item["label"], "white")
        console.print(f"  {item['priority']}. [{item['label']}] {item['action']}", style=label_color)
        console.print(f"     → {item['fix']}", style="dim")
    console.print()
