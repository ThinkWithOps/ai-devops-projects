# ⚔️ AI Pipeline War Room — Project 08

> **3 AI agents analyze your CI/CD pipeline simultaneously. A Commander resolves their conflicts. You get a prioritized battle plan — with real dollar amounts.**

Part of the [AI+DevOps Series](https://github.com/ThinkWithOps/ai-devops-projects) | Project 8 of 12

---

## 🚨 The Problem

Most teams only optimize CI/CD for one thing — speed.

But your slow pipeline is also:
- **Leaking credentials** into Git history (one breach = $4.5M average cost)
- **Wasting real money** — $0.016/min per Ubuntu runner, every commit, all year
- **Blocking developers** with sequential jobs that could run in parallel

And the worst part? Speed fixes and Security requirements **conflict with each other**.

Remove a slow install job? Security says that's where you need your secret scanner.

Who decides?

## ⚔️ The Solution

**3 specialized AI agents run in parallel. A Commander resolves their conflicts.**

```
              YOUR PIPELINE YAML
                     ↓
    ┌──────────────────────────────────┐
    │   asyncio.gather() — PARALLEL   │
    ├──────────┬──────────┬────────────┤
    │ 🚀 Speed │ 🔒 Sec   │ 💰 Cost   │
    │ Agent    │ Agent    │ Agent     │
    └──────────┴──────────┴────────────┘
                     ↓
              ⚔️  Commander Agent
              (conflict resolution)
                     ↓
           📋 Prioritized Battle Plan
```

---

## 🎬 YouTube Video

[Watch the full demo](https://youtu.be/MJNYzRRVIXw) — Project 08 in the AI+DevOps Series

---

## ✨ The 3 Agents + Commander

### 🚀 Speed Agent
Scans for performance bottlenecks:
- `npm install` / `pip install` running without cache (×3, ×4...)
- Sequential jobs that could run in parallel
- Docker builds without `--cache-from`
- No `timeout-minutes` on jobs
- Redundant install jobs

**Output:** Bottleneck list + estimated minutes saved per fix

### 🔒 Security Agent
Scans for vulnerabilities — and it's dramatic about it:
- Hardcoded AWS keys, Docker passwords, GitHub tokens
- `permissions: write-all` — GITHUB_TOKEN with full write access
- No secret scanning (gitleaks/trufflehog) in pipeline
- Actions not pinned to commit SHA
- No container image scanning post-build

**Output:** Vulnerability list + severity rating + security score (0–10)

### 💰 Cost Agent
Calculates real dollar waste (GitHub Actions: $0.016/min private repos):
- Wasted minutes per run × runs per month × team size
- Monthly and annual dollar projections
- Top cost driver identification

**Output:** Actual dollar amounts — not just "it's slow"

### ⚔️ Commander Agent
Receives all 3 reports. Finds conflicts. Resolves them explicitly:

> *"Speed recommends removing 'install-deps' job — saves 2 min/run.
> Security requires a pre-build gate for secret scanning.
> Commander decision: Repurpose as 'security-gate' — remove npm install, add gitleaks. Net: saves install waste AND adds missing secret scan."*

**Output:** Prioritized 5-point battle plan with tradeoff reasoning

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/download) installed and running

### 3 Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Pull AI model
ollama pull llama3.2

# 3. Run the War Room
python src/war_room.py --simulate nodejs
```

---

## 📋 All Commands

| Command | What it does |
|---------|-------------|
| `python src/war_room.py --simulate nodejs` | Run with slow Node.js sample (hardcoded secrets + 4× npm install) |
| `python src/war_room.py --simulate python` | Run with slow Python sample (exposed tokens + sequential jobs) |
| `python src/war_room.py --file ci.yml` | Analyze your own pipeline |
| `python src/war_room.py --simulate nodejs --no-ai` | Rule-based only — instant, no Ollama |
| `python src/war_room.py --simulate nodejs --save-report` | Save markdown report |
| `python src/war_room.py --file ci.yml --team-size 20 --commits-per-day 8` | Custom cost assumptions |
| `python demo/demo.py` | Run both samples in sequence (no AI) |

---

## 📊 Sample Results — Node.js Pipeline

```
🚀 SPEED AGENT
  [HIGH] npm install runs 4× — no npm cache     → saves 6 min/run
  [HIGH] Sequential lint + test — could parallel → saves 2 min/run
  [HIGH] Docker build without --cache-from       → saves 2 min/run
  [MEDIUM] No timeout-minutes on 4 jobs
  Total savings: ~8 min/run

🔒 SECURITY AGENT
  [CRITICAL] Hardcoded AWS Access Key ID detected
  [CRITICAL] Hardcoded Docker registry password
  [HIGH] permissions: write-all
  [HIGH] No secret scanning step
  [MEDIUM] 4 actions not pinned to commit SHA
  Security Score: 1/10

💰 COST AGENT
  Wasted per run:    8 min
  Runs per month:    1,100 (10 devs × 5 commits/day × 22 days)
  Monthly waste:     $140.80 (private repo rate)
  Annual waste:      $1,689.60

⚔️ COMMANDER — CONFLICTS
  🚨 CONFLICT: REMOVAL VS SECURITY
  Speed: Remove 'install-deps' (redundant)
  Security: Keep as security gate for secret scanning
  ✅ Resolution: Repurpose as 'security-gate', add gitleaks step

  🚨 CONFLICT: SPEED VS BREACH COST
  Speed: Optimize for 8 min/run savings ($1,689/year)
  Security: Credentials exposed — breach cost = $4.5M average
  ✅ Resolution: Fix credentials FIRST (free), then optimize speed

📋 BATTLE PLAN:
  1. [CRITICAL] Rotate AWS credentials + Docker password immediately
  2. [CRITICAL] Move secrets to GitHub Secrets (${{ secrets.X }})
  3. [HIGH] Add npm cache + replace npm install with npm ci
  4. [HIGH] Repurpose install-deps → security-gate with gitleaks
  5. [HIGH] Parallelize lint + test jobs
```

---

## 🏗️ Architecture

```
08-ai-pipeline-war-room/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py       # Shared Ollama call (asyncio + thread pool)
│   │   ├── speed_agent.py      # Performance bottleneck scanner
│   │   ├── security_agent.py   # Security vulnerability scanner
│   │   ├── cost_agent.py       # Dollar cost calculator
│   │   └── commander_agent.py  # Conflict resolution + battle plan
│   ├── war_room.py             # Main orchestrator (asyncio)
│   └── rich_ui.py              # Rich terminal War Room dashboard
├── demo/
│   ├── demo.py
│   └── sample_pipelines/
│       ├── slow_nodejs_pipeline.yml   (AWS keys + 4× npm install)
│       └── slow_python_pipeline.yml   (exposed tokens + sequential)
├── reports/                    # Generated reports (gitignored)
└── requirements.txt
```

**Async flow:**

```python
# All 3 agents dispatch simultaneously — Python doesn't block
speed_result, security_result, cost_result = await asyncio.gather(
    speed_agent.enrich_with_ai(content, speed_base),
    security_agent.enrich_with_ai(content, security_base),
    cost_agent.enrich_with_ai(content, cost_base),
)
# Commander runs after all 3 complete
commander_result = await commander_agent.enrich_with_ai(...)
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core logic, asyncio orchestration |
| asyncio | Parallel agent execution |
| concurrent.futures.ThreadPoolExecutor | Non-blocking Ollama subprocess calls |
| Ollama + Llama 3.2 | Each agent's specialized AI prompt |
| Rich | Live terminal War Room dashboard (Layout + Live) |
| re | Rule-based detection (instant, no AI needed) |

**Cost: $0 — runs 100% locally.**

---

## 🔧 Challenges & Solutions

### 1. asyncio + blocking subprocess (Ollama)

`subprocess.run()` is blocking — it freezes asyncio. Can't just `await` it.

**Solution:** `loop.run_in_executor(ThreadPoolExecutor(max_workers=4), ...)` dispatches each Ollama call to a thread. Python's asyncio event loop stays responsive, Rich keeps updating, all 3 agents appear to run simultaneously.

### 2. Commander needs structured output from agents

LLMs don't reliably follow exact output formats. If Commander can't parse agent outputs, conflict detection fails.

**Solution:** Two-phase approach — rule-based detection always runs first and produces structured dicts. Ollama enriches on top. Commander uses the structured dicts for conflict detection, not the LLM free text.

### 3. The "conflict" must be real, not manufactured

If Speed and Security don't actually conflict, the Commander has nothing dramatic to say.

**Solution:** Sample pipelines are carefully designed so Speed's top recommendation (remove the redundant install job) directly conflicts with Security's requirement (that job is the natural place for a secret scanning gate).

### 4. Rich Live + Windows terminal

Rich's `Live` display can fail on Windows terminals that don't support ANSI.

**Solution:** `--no-live` flag falls back to plain terminal output. All results still display, just without the live dashboard.

---

## 🪟 Windows Notes

- Run from project root: `ai-devops-projects/08-ai-pipeline-war-room/`
- Ollama must be running before you start (check system tray)
- Warm up Ollama first: `ollama run llama3.2 "hello"`
- If Rich Live display breaks: add `--no-live` flag
- `encoding='utf-8'` is set on all subprocess calls to prevent UnicodeDecodeError

---

## 📝 License

MIT License — use it, modify it, build on it.

---

## ⚠️ Important Notes

- The sample pipelines contain intentionally broken security patterns for demo purposes. Do not use them in production.
- AI analysis requires Ollama running locally. Rule-based analysis (`--no-ai`) works offline.
- Cost calculations use GitHub-published pricing. Verify current rates at [github.com/pricing](https://github.com/pricing).

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) — local LLM runtime
- [Meta](https://llama.meta.com) — Llama 3.2 model
- [Rich](https://github.com/Textualize/rich) — terminal UI library
- [GitHub Actions pricing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions) — cost data

---

## 🔗 Related Projects

| # | Project | Link |
|---|---------|------|
| 01 | AI Docker Security Scanner | [View](../01-ai-docker-scanner) |
| 02 | AI K8s Pod Debugger | [View](../02-ai-k8s-debugger) |
| 03 | AI AWS Cost Detective | [View](../03-ai-aws-cost-detective) |
| 04 | AI GitHub Actions Healer | [View](../04-ai-github-actions-healer) |
| 05 | AI Terraform Generator | [View](../05-ai-terraform-generator) |
| 06 | AI Incident Commander | [View](../06-ai-local-incident-commander) |
| 07 | AI Log Analyzer | [View](../07-ai-log-analyzer) |
| **08** | **AI Pipeline War Room** ← you are here | — |
| 09 | AI DB Query Optimizer | Coming soon |
| 10 | AI Infrastructure Auditor | Coming soon |
| 11 | AI Security Compliance Checker | Coming soon |
| 12 | AI Deployment Predictor | Coming soon |

---

## 📧 Contact

**ThinkWithOps** — Building AI+DevOps tools, one project at a time.

- 🐙 GitHub: [github.com/ThinkWithOps](https://github.com/ThinkWithOps)
- 💼 LinkedIn: [LinkedIn](https://www.linkedin.com/in/b-vijaya/)
- 📺 YouTube: [YouTube](https://youtube.com/@ThinkWithOps)

---

⭐ **Star this repo** if it saved you time — it helps the series grow!
