# Prompt Used to Generate This Project

The following prompt was used to generate all files in Project 09 — AI Database Query Optimizer.

---

## Project Prompt

Build ALL files for Project 09 "AI Database Query Optimizer" in the directory
`09-ai-db-query-optimizer/`. This folder already exists.

**IMPORTANT OVERRIDE:** Use **Streamlit dashboard** (NOT Rich terminal) as the UI.

---

## Project Overview

A live database detective that connects to a real PostgreSQL database, analyzes slow queries,
detects N+1 patterns, finds missing indexes, rewrites bad SQL with AI, and calculates real
dollar cost of query inefficiency.

**The demo story:**
- A query LOOKS fine. It runs. Dashboard loads. But AI finds: 847 queries fired instead of 1,
  3.2s wasted per page load, $2,400/year in wasted compute.
- Show live: 3.1s query → AI analyzes → add index → 48ms. 98% improvement on screen.

---

## Folder Structure

```
09-ai-db-query-optimizer/
├── src/
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── n_plus_one_detector.py
│   │   ├── index_analyzer.py
│   │   ├── query_rewriter.py
│   │   └── cost_calculator.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connector.py
│   │   └── query_interceptor.py
│   └── ai/
│       ├── __init__.py
│       └── ollama_client.py
├── demo/
│   ├── sample_queries/
│   │   ├── slow_queries.sql
│   │   └── optimized_queries.sql
│   └── sample_db/
│       └── setup_demo_db.sql
├── .github/
│   ├── START_HERE.md
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── youtube-script.md
│   ├── LINKEDIN_POST.md
│   ├── THUMBNAIL.md
│   └── prompt-for-files.md
├── app.py              ← Streamlit main app
├── config.py           ← DB config, thresholds, Ollama settings
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Key Requirements

### config.py
- Load DB_CONFIG, OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT from environment
- Thresholds: SLOW_QUERY_THRESHOLD_MS, N_PLUS_ONE_THRESHOLD
- Cost: AVG_DEV_HOURLY_RATE, DAILY_EXECUTIONS_DEFAULT

### src/db/connector.py
- get_connection(), test_connection(), get_slow_queries(threshold_ms)
- get_table_indexes(), run_explain_analyze(), get_table_schema()
- check_pg_stat_statements()
- All functions return empty / False / error string on failure — never raise to caller

### src/db/query_interceptor.py
- QueryInterceptor class wrapping a psycopg2 connection
- execute(), get_slow_queries(), clear_log(), get_n_plus_one_candidates()

### src/analyzers/
- n_plus_one_detector.py: normalize_query(), detect_n_plus_one()
- index_analyzer.py: parse_explain_output(), analyze_query_indexes()
- cost_calculator.py: calculate_query_cost(), calculate_savings()
- query_rewriter.py: rewrite_query() using call_ollama()

### src/ai/ollama_client.py
- call_ollama() via subprocess (synchronous, Windows-compatible)
- analyze_slow_query() with ANALYZE_PROMPT
- check_ollama_available()

### app.py — Streamlit (4 tabs)
1. Slow Query Scanner: scan pg_stat_statements, AI analyze button, colored result card
2. N+1 Detector: paste query log, detect patterns, show fix suggestions
3. Index Analyzer: paste SQL, run EXPLAIN, show seq scans, AI rewrite before/after
4. Cost Calculator: before/after time inputs, annual cost metrics, formula explanation

### Demo Mode
- Works without any database connection
- Pre-loaded with: 3.1s query, 847 N+1 count, $2,400/year cost
- "Enable Demo Mode" button in sidebar

### Demo Database
- users (100k rows), orders (500k), order_items (2M), products (10k)
- NO indexes on foreign keys — intentional for the demo
- Slow views: slow_user_orders, slow_product_stats, slow_recent_activity

### Sample Queries
- 5 slow queries demonstrating: N+1, missing index, bad JOIN, full scan, subquery
- 5 optimized versions with explanation and required indexes

---

## Important Notes

1. All files complete and copy-paste ready — no TODOs in code
2. Windows compatibility: encoding='utf-8' on subprocess calls
3. Demo mode works with no DB and no Ollama
4. Never raise unhandled exceptions — wrap all DB calls in try/except
5. Use psycopg2-binary in requirements (avoids Windows compilation)
6. Do not write to root README.md
7. Demo values: slow query = 3.1s, N+1 = 847, after fix = 48ms, annual cost = $2,400

---

## .github/ Files

- START_HERE.md: 5-minute setup guide
- IMPLEMENTATION_GUIDE.md: 7-day build plan (Day 1-7 with milestones)
- youtube-script.md: Full word-for-word script, 5 title options, timestamps, video metadata
- LINKEDIN_POST.md: 4 post options with first comment section
- THUMBNAIL.md: AI image prompt, ASCII layout, Canva step-by-step guide, color hex codes
- prompt-for-files.md: This file (the generation prompt)
