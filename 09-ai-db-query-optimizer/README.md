# 🔍 AI Database Query Optimizer

> AI-powered database detective that connects to your PostgreSQL database, finds slow queries, detects N+1 patterns, and rewrites bad SQL — in seconds instead of hours.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue)](https://postgresql.org)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.2-green)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Table of Contents

- [Problem Statement](#problem-statement)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Results](#results)
- [Challenges & Learnings](#challenges--learnings)
- [Installation & Usage](#installation--usage)

---

<a id="problem-statement"></a>
## 🎯 Problem Statement

Most applications have slow queries nobody knows about:

- An ORM fires **847 individual SELECT statements** for one page load — the classic N+1 pattern
- A missing index turns a 48ms query into a **3.1-second disaster**
- Nobody notices until production is on fire
- By then, the app has burned **$2,400/year** in wasted compute — from one missing index

**Meanwhile your users are waiting and your team is debugging blind.**

This tool is a live database detective. Connect it to your PostgreSQL database, and it finds the crimes your ORM committed silently — then shows you the exact fix.

---

<a id="tech-stack"></a>
## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core scripting |
| Streamlit 1.32+ | Web dashboard UI |
| PostgreSQL + psycopg2-binary | Database connection + pg_stat_statements |
| Ollama (Llama 3.2) | Local AI for query analysis and rewriting |
| `sqlparse` | SQL parsing and formatting |
| `python-dotenv` | Environment variable management |
| `re` (stdlib) | Query normalization and pattern detection |
| `subprocess` (stdlib) | Ollama integration |

**100% local — no API costs, no data sent to cloud.**

---

<a id="architecture"></a>
## 🏗️ Architecture

```
PostgreSQL Database
        │
        ▼
  DB Connector
  (pg_stat_statements / fallback)
        │
        ▼
  Slow Query List
  (ranked by execution time)
        │
        ├─────────────────────┬────────────────────┐
        ▼                     ▼                    ▼
  N+1 Detector          Index Analyzer        Cost Calculator
  (normalize SQL,       (EXPLAIN ANALYZE,     (time × calls
   group patterns,       seq scan detection,   × rate = $)
   flag loops)           CREATE INDEX fix)
        │                     │                    │
        └─────────────────────┴────────────────────┘
                              │
                              ▼
                      AI Analysis (Ollama)
                      Query Rewrite + Diagnosis
                              │
                              ▼
                   Streamlit Dashboard
                   (before/after, cost saved)
```

**Supported detection types:**
- **N+1 Queries** — repeated identical queries fired in loops by ORMs
- **Missing Indexes** — sequential scans on large tables
- **Inefficient JOINs** — cartesian products, implicit joins
- **Full Table Scans** — unindexed WHERE clauses on millions of rows

---

<a id="results"></a>
## 📊 Results

| Metric | Before (Manual) | After (AI Optimizer) |
|--------|----------------|----------------------|
| Time to find slow queries | 2-4 hours | < 30 seconds |
| N+1 detection | Never caught | Automatic |
| Index recommendations | DBA review (days) | Instant CREATE INDEX |
| Query rewrite | Hours of research | AI-generated instantly |
| Dollar cost visibility | Never calculated | Real $ shown per query |
| API cost | $0 | $0 (100% local) |

**Live demo numbers:**

```
BEFORE:
  Query:   SELECT * FROM orders WHERE user_id = 123
  Method:  Sequential scan — reads all 500,000 rows
  Time:    3,100 ms
  Cost:    $2,400/year (1,000 calls/day × $75/hr dev rate)

AFTER (one missing index):
  CREATE INDEX idx_orders_user_id ON orders(user_id);

  Query:   SELECT * FROM orders WHERE user_id = 123
  Method:  Index scan — reads 14 matching rows directly
  Time:    48 ms
  Cost:    $37/year

  Improvement: 98.5% faster  |  $2,363/year saved
```

---

<a id="challenges--learnings"></a>
## 🧠 Challenges & Learnings

**1. pg_stat_statements setup**
The extension must be added to `postgresql.conf` before slow queries appear. Added graceful fallback to `pg_stat_activity` for live running queries when the extension is missing.

**2. N+1 false positives**
Normalized queries must strip both string literals AND integers to match ORM patterns accurately. `WHERE id = 1` and `WHERE id = 42` are the same structural pattern — stripping only strings misses numeric parameters.

**3. EXPLAIN ANALYZE on write queries**
Wrapping EXPLAIN ANALYZE in a transaction that rolls back prevents side effects when analyzing UPDATE/DELETE queries. Easy to miss, breaks demo badly if not handled.

**4. Windows psycopg2**
The source package requires Visual C++ Build Tools. Used `psycopg2-binary` in requirements to avoid compilation entirely.

**5. Streamlit + blocking Ollama calls**
Streamlit runs on a single thread. Used `st.spinner()` around Ollama subprocess calls to keep the UI responsive and give clear feedback that AI is working.

---

<a id="installation--usage"></a>
## 🚀 Installation & Usage

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (optional — demo mode works without it)
- Ollama installed and running

### Step 1: Clone the repo

```bash
git clone https://github.com/ThinkWithOps/ai-devops-projects.git
cd ai-devops-projects/09-ai-db-query-optimizer
```

### Step 2: Install dependencies + Ollama model

```bash
pip install -r requirements.txt

# Download Ollama: https://ollama.ai/download
ollama pull llama3.2
```

### Step 3: Configure environment

```bash
cp .env.example .env
# Edit .env with your DB credentials
```

### Step 4: (Optional) Set up demo database

```bash
psql -U postgres -c "CREATE DATABASE demo_db;"
psql -U postgres demo_db < demo/sample_db/setup_demo_db.sql
```

### Step 5: Launch the dashboard

```bash
streamlit run app.py
```

Browser opens at `http://localhost:8501` automatically.

> **No PostgreSQL?** Click **"Enable Demo Mode"** in the sidebar. All 4 features work with built-in demo data — 3.1s query, 847 N+1 pattern, $2,400/year waste shown live.

---

### Command Reference

```
streamlit run app.py                              Start the dashboard
pip install -r requirements.txt                   Install Python deps
ollama pull llama3.2                              Download AI model
psql -U postgres demo_db < setup_demo_db.sql      Set up demo database
cp .env.example .env                              Create config file
```

---

## 📁 Project Structure

```
09-ai-db-query-optimizer/
├── app.py                          # Streamlit dashboard (main entry point)
├── config.py                       # DB config, thresholds, Ollama settings
├── src/
│   ├── analyzers/
│   │   ├── n_plus_one_detector.py  # Groups identical queries, flags loops
│   │   ├── index_analyzer.py       # Parses EXPLAIN output, finds seq scans
│   │   ├── query_rewriter.py       # Sends query to AI, parses rewritten SQL
│   │   └── cost_calculator.py      # time × executions × rate = dollar cost
│   ├── db/
│   │   ├── connector.py            # psycopg2 connection, pg_stat_statements
│   │   └── query_interceptor.py    # Wraps connection, times every query
│   └── ai/
│       └── ollama_client.py        # Subprocess call to ollama CLI
├── demo/
│   ├── sample_db/
│   │   └── setup_demo_db.sql       # Creates users/orders/items (no indexes)
│   └── sample_queries/
│       ├── slow_queries.sql        # 5 intentionally bad queries with comments
│       └── optimized_queries.sql   # Fixed versions with explanation
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🎬 YouTube Video

**Watch the full tutorial:** [https://youtu.be/7FtKm-qKsaI]

---

## 📝 License

MIT License — feel free to use in your own projects!

---

## ⚠️ Important Notes

**This is a query analysis and AI suggestion tool:**
- For learning and demonstration purposes
- Always review AI suggestions before implementing in production
- Test fixes in dev environment first
- AI rewrites are ~90% accurate but not infallible — always verify

---

## 🙏 Acknowledgments

- **Ollama** — Making local AI accessible
- **Meta** — For Llama models
- **Streamlit** — Beautiful web UI with zero frontend code
- **PostgreSQL** — For pg_stat_statements extension

---

## 🔗 Related Projects

**Previous in series:**
- Project 01: AI Docker Scanner
- Project 02: AI K8s Debugger
- Project 03: AI AWS Cost Detective
- Project 04: AI GitHub Actions Healer
- Project 05: AI Terraform Generator
- Project 06: AI Local Incident Commander
- Project 07: AI Log Analyzer
- Project 08: AI Pipeline War Room

**Next in series:**
- Project 10: Coming soon

---

## 📧 Contact

**YouTube:** [ThinkWithOps](https://youtube.com/@thinkwithops)
**GitHub:** [ThinkWithOps](https://github.com/ThinkWithOps)

---

**⭐ If this saved you time debugging queries, please star the repo!**
