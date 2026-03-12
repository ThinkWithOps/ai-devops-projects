# YouTube Script — AI Database Query Optimizer

## Title
**"Your App Has Been Lying to You — AI Found 847 Hidden Queries"**

## 5 Alternative Titles
- "I Let AI Analyze My Database — It Found $2,400/Year I Was Throwing Away"
- "3 Seconds → 48ms: AI Found the Query That Was Killing My App"
- "847 Queries Were Firing on Every Page Load — AI Found It in 4 Seconds"
- "Your DBA Missed This. AI Didn't. (Database Query Optimizer)"
- "The Silent Killer in Every App: N+1 Queries (AI Found Mine)"

## Video Metadata

**File name:** `09-ai-db-query-optimizer.mp4`

**Description:**
```
Your app has a hidden performance killer. It looks fine. Queries run. Dashboard loads.
But underneath? 847 database queries fire on every page load — costing $2,400/year
from one missing index.

I built an AI tool that detects N+1 query patterns, finds missing indexes via EXPLAIN ANALYZE,
rewrites your SQL using a local AI model, and calculates the real dollar cost of slow queries.
No API keys needed — runs 100% local with Ollama.

Live demo: 3.1-second query → AI analyzes it → add one index → 48ms. 98% improvement.

All code is open source. Connect to your PostgreSQL database for real analysis, or try Demo Mode to explore the tool first.

⭐ GitHub: https://github.com/your-username/ai-devops-projects
📂 Project 09 folder: 09-ai-db-query-optimizer/

🛠️ Tech Stack:
- Streamlit (dashboard)
- PostgreSQL + psycopg2 (database)
- Ollama + llama3.2 (local AI, no API key)
- Python 3.11+

Timestamps:
0:00 — Hook: the query that looked fine
0:15 — The N+1 problem explained
0:45 — Demo Part 1: Crime Scene (Slow Query Scanner)
2:30 — Demo Part 2: The Verdict (Index Analyzer + AI)
4:00 — Demo Part 3: The Fix (before/after + cost)
4:45 — Results: 3.1s → 48ms, $2,400 → $37/year
5:15 — Where to get the code

Next video: AI Infrastructure Auditor
```

**Tags (30):**
```
database optimization, postgresql, sql performance, n+1 queries, missing index,
explain analyze, query optimizer, ai developer tools, ollama, llama3.2,
streamlit, python, devops, database tuning, slow queries, pg_stat_statements,
index analyzer, query rewriter, database detective, sql rewrite, ai tools,
developer productivity, backend optimization, database performance,
python postgresql, psycopg2, local ai, open source devops, cost optimization,
ai devops projects
```

---

## Full Script

---

### HOOK (0:00 – 0:15)

**[SCREEN: Run the slow query in psql. Clock visible. 3.1 seconds pass.]**

**VOICEOVER:**
"Your app has been lying to you.

That dashboard that loads in 3 seconds? Underneath it, 847 database queries are firing — every single page load.

Your DBA never caught it. Your monitoring missed it. AI found it in 4 seconds."

---

### PROBLEM (0:15 – 0:45)

**[SCREEN: Show the 'innocent' query in VS Code or pgAdmin]**

```sql
SELECT * FROM orders WHERE user_id = 123
```

**VOICEOVER:**
"This query looks completely fine. It runs. It returns the right data. But when your ORM loops through 847 users — it fires this query 847 separate times.

That's the N+1 problem. One query becomes N+1 queries. 14 milliseconds per query, 847 times — that's 11 seconds in database round-trips per request.

And here's the other crime."

**[SCREEN: Switch to EXPLAIN ANALYZE output]**

```
Seq Scan on orders
(actual time=0.043..3098.441 rows=14 loops=1)
Filter: (user_id = 123)
Rows Removed by Filter: 499,986
Execution Time: 3,098 ms
```

**VOICEOVER:**
"To find 14 orders for user 123, PostgreSQL read all 500,000 rows in the table. Every. Single. Time.

Not because the query is wrong. Because someone forgot to add an index.

Most developers never see this until production is on fire. Today I'm going to show you a tool that finds it for you — using AI."

---

### DEMO PART 1 — THE CRIME SCENE (0:45 – 2:30)

**[SCREEN: Open terminal, run `streamlit run app.py`, browser opens]**

**VOICEOVER:**
"Here's the AI Database Query Optimizer I built. Let me show you what it finds."

**[SCREEN: Sidebar — click "Enable Demo Mode"]**
**[SCREEN: Table appears instantly — 5 slow queries loaded]**

**VOICEOVER:**
"These are the 5 slowest queries from a typical production database — 100,000 users, 500,000 orders, 2 million order items. Look at the top one."

**[SCREEN: Row 0 highlighted — SELECT * FROM orders WHERE user_id = 123, Mean: 3100ms, Calls: 847]**

**VOICEOVER:**
"This query ran 847 times. Average time: 3,100 milliseconds. That's 3 seconds. Every. Single. Time.

Looks innocent — just fetching orders for a user. But something is seriously wrong."

**[SCREEN: Click the query in the dropdown to select it]**
**[SCREEN: Full SQL appears: `SELECT * FROM orders WHERE user_id = 123`]**

**VOICEOVER:**
"This is the culprit. Let's ask AI what's actually wrong with it."

**[SCREEN: Click "Analyze with AI" button — spinner appears]**

**VOICEOVER:**
"I'm using Ollama running locally — no API keys, no cloud, completely private. It's analyzing the query plus the EXPLAIN output..."

**[SCREEN: AI result card appears — RED background, CRITICAL badge]**

```
PROBLEM_TYPE: MISSING_INDEX
SEVERITY: CRITICAL
ROOT_CAUSE: Sequential scan on orders table reads 500,000 rows to return 14.
SPECIFIC_FIX: CREATE INDEX idx_orders_user_id ON orders(user_id);
ESTIMATED_IMPROVEMENT: 98% faster, 3,100ms → 48ms
BUSINESS_IMPACT: Running 1,000x/day at $75/hr — this costs $2,400/year
```

**VOICEOVER:**
"MEDIUM. FULL_TABLE_SCAN. AI found it in under 10 seconds and even calculated the business impact: $1,500 per year from one missing index.

But let's verify it. Let's look at the actual EXPLAIN output."

---

### DEMO PART 2 — THE VERDICT (2:30 – 4:00)

**[SCREEN: Click Tab 3 — Index Analyzer]**
**[SCREEN: Paste the slow query into the text area]**
**[SCREEN: Click "Run EXPLAIN ANALYZE"]**

**VOICEOVER:**
"The Index Analyzer shows you the EXPLAIN output — what PostgreSQL actually does when it runs this query."

**[SCREEN: EXPLAIN output appears in text area]**
**[SCREEN: Red alert appears: "Sequential scan on orders — full table read on every query"]**
**[SCREEN: Suggested fix highlighted in green box]**

```sql
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

**VOICEOVER:**
"Confirmed. Sequential scan on orders. 500,000 rows read. 14 rows returned.

The tool has already generated the exact CREATE INDEX statement to fix it. Now let's see what AI would rewrite the query to look like."

**[SCREEN: Click "Get AI Rewrite" button]**

**VOICEOVER:**
"This sends the query, the EXPLAIN output, and the detected issue to the local AI model..."

**[SCREEN: Before/After side by side]**

**Before (left column):**
```sql
SELECT * FROM orders WHERE user_id = 123
-- Execution time: 3,098 ms
```

**After (right column):**
```sql
SELECT id, amount, status, created_at
FROM orders
WHERE user_id = 123
ORDER BY created_at DESC;
-- Expected: 98% faster (with index)
```

**VOICEOVER:**
"AI rewrote it to select only the columns you actually need — which reduces I/O even more once the index is in place. And it explained exactly why, in plain English."

---

### DEMO PART 3 — THE FIX (4:00 – 4:45)

**[SCREEN: Click Tab 4 — Cost Calculator]**

**VOICEOVER:**
"Before we apply the fix — let's see the real cost."

**[SCREEN: Enter values: Before=3.1s, Daily=1000, Rate=$75]**
**[SCREEN: Big metric cards appear]**

```
Annual cost (before):   $2,400
Annual cost (after):    $37
Annual savings:         $2,363
Improvement:            98.5% faster
```

**VOICEOVER:**
"$2,400 per year. From one missing index. Now let's see what happens after the fix."

**[SCREEN: Update Cost Calculator — After=0.048s]**

```
Annual cost (before):  $2,400/year
Annual cost (after):   $37/year
Savings:               $2,363/year
Improvement:           98.5% faster
```

**VOICEOVER:**
"$37 a year. One index — one line of SQL — and you save $2,363 every year. The database was already doing the work. It just didn't have a shortcut to find the data quickly."

---

### RESULTS (4:45 – 5:15)

**[SCREEN: Results summary slide or dashboard screenshot]**

**VOICEOVER:**
"One missing index. One AI tool. $2,363 saved per year.

The query went from 3 seconds to 48 milliseconds — and the tool found it, explained it, and generated the fix automatically.

All code is open source. Connect it to your PostgreSQL database and it scans your real slow queries. No database? Use Demo Mode to explore the tool first.

Project 09 of my 12-project AI DevOps series. Local AI only. No API keys. No cloud. No cost."

---

### CTA (5:15 – 5:30)

**[SCREEN: GitHub repository page]**

**VOICEOVER:**
"The full source code is on GitHub — link in the description. Star the repo if you want to see the rest of the series.

Next up: Project 10 — the AI Infrastructure Auditor. It analyzes Terraform configurations, finds security gaps, calculates the cost of over-provisioned resources, and suggests right-sizing fixes.

If you're building with PostgreSQL, drop a comment — what's the worst slow query you've ever found in production?

See you in the next one."

---

## Production Notes

- Record at 1920×1080, 60fps
- Use OBS Studio or Camtasia
- Record voice separately for cleaner audio
- Click "Enable Demo Mode" in sidebar before recording — no DB setup needed
- Have Ollama pre-warmed (run one query before recording so model is loaded)
- Estimated total run time: 5:30
- Target thumbnail moment: the CRITICAL red card at 2:00 mark
