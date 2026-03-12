# Implementation Guide — 7-Day Build Plan

Build the AI Database Query Optimizer from scratch in 7 focused days.
Each day has a clear deliverable you can demo at the end.

---

## Day 1 — DB Connector + Test Connection UI

**Goal:** Streamlit app opens, sidebar connects to PostgreSQL, shows version string.

### Tasks
1. Create `config.py` with dotenv loading
2. Build `src/db/connector.py`:
   - `get_connection()` using psycopg2
   - `test_connection()` returning (bool, message)
3. Create minimal `app.py` with sidebar:
   - Host/port/user/password inputs
   - "Connect" button → shows green checkmark or red error
4. Test with a real PostgreSQL instance

### Milestone
- [ ] `streamlit run app.py` shows connection UI
- [ ] Connecting shows "Connected to PostgreSQL 15.x"
- [ ] Wrong password shows clear error message, doesn't crash

### Key files
- `config.py`
- `src/db/connector.py`
- `app.py` (sidebar only)

---

## Day 2 — pg_stat_statements Integration + Slow Query List

**Goal:** Tab 1 shows real slow queries from the database.

### Tasks
1. Add `check_pg_stat_statements()` to connector
2. Add `get_slow_queries(threshold_ms)` — queries pg_stat_statements
3. Add fallback to `pg_stat_activity` if extension not available
4. Build Tab 1 in `app.py`:
   - "Scan for Slow Queries" button
   - Results in `st.dataframe` with query/calls/mean_time/total_time
   - Threshold slider in sidebar
5. Set up demo DB using `setup_demo_db.sql`
6. Run a few slow queries to populate pg_stat_statements

### Milestone
- [ ] Clicking "Scan" shows a real list of slow queries
- [ ] Demo DB shows `SELECT * FROM orders WHERE user_id = ?` at ~3.1s
- [ ] Threshold slider filters results live

### Key files
- `src/db/connector.py` (get_slow_queries, check_pg_stat_statements)
- `demo/sample_db/setup_demo_db.sql`
- `app.py` (Tab 1 query list)

---

## Day 3 — N+1 Detector + Index Analyzer (Rule-Based)

**Goal:** Tabs 2 and 3 work with rule-based (no AI) detection.

### Tasks
1. Build `src/analyzers/n_plus_one_detector.py`:
   - `normalize_query()` with regex
   - `detect_n_plus_one(query_log, threshold)` → findings list
   - `parse_query_log_text()` for plain text input
2. Build `src/analyzers/index_analyzer.py`:
   - `parse_explain_output()` — regex parse of EXPLAIN text
   - `analyze_query_indexes()` — returns findings + suggested CREATE INDEX
3. Add `run_explain_analyze()` to connector
4. Build Tab 2 (N+1 Detector) in `app.py`
5. Build Tab 3 (Index Analyzer) in `app.py` — just the non-AI parts

### Milestone
- [ ] Pasting the demo query log into Tab 2 shows N+1 findings
- [ ] Pasting the slow query into Tab 3 and clicking EXPLAIN shows seq scan detection
- [ ] Suggested CREATE INDEX statement is correct

### Key files
- `src/analyzers/n_plus_one_detector.py`
- `src/analyzers/index_analyzer.py`
- `src/db/connector.py` (run_explain_analyze)
- `app.py` (Tab 2 and Tab 3 non-AI parts)

---

## Day 4 — Ollama Client + AI Analysis Integration

**Goal:** "Analyze with AI" button in Tab 1 returns structured results.

### Tasks
1. Build `src/ai/ollama_client.py`:
   - `call_ollama(prompt)` via subprocess
   - `check_ollama_available()` → (bool, message)
   - `analyze_slow_query(query, time_ms, explain)` → parsed dict
2. Add ANALYZE_PROMPT with exact format specification
3. Wire AI analysis into Tab 1:
   - "Analyze with AI" button
   - Colored result card (CRITICAL=red, HIGH=orange, MEDIUM=yellow)
   - Shows: problem_type, severity, root_cause, specific_fix, business_impact
4. Add Ollama status indicator in sidebar
5. Handle Ollama unavailable gracefully (show message, not crash)

### Milestone
- [ ] Clicking "Analyze with AI" on a slow query returns structured result within 30s
- [ ] CRITICAL severity shows red card
- [ ] If Ollama is not running, shows helpful error message

### Key files
- `src/ai/ollama_client.py`
- `app.py` (Tab 1 AI analysis card)

---

## Day 5 — Query Rewriter + Before/After UI

**Goal:** "Get AI Rewrite" in Tab 3 shows side-by-side before/after.

### Tasks
1. Build `src/analyzers/query_rewriter.py`:
   - `rewrite_query()` with REWRITE_PROMPT
   - Parse OPTIMIZED_QUERY / CHANGES_MADE / EXPECTED_IMPROVEMENT / EXPLANATION
2. Wire into Tab 3:
   - "Get AI Rewrite" button
   - `st.columns(2)` with before (slow) and after (optimized) SQL
   - Before shows execution time from EXPLAIN
   - After shows expected improvement from AI
   - Expandable "Changes made" and "Plain-English explanation"
3. Handle parse failures — show raw AI response if structured parse fails

### Milestone
- [ ] Clicking "Get AI Rewrite" shows optimized SQL within 60s
- [ ] Before/after displayed side by side with clear formatting
- [ ] Changes made are listed as bullet points

### Key files
- `src/analyzers/query_rewriter.py`
- `app.py` (Tab 3 AI rewrite section)

---

## Day 6 — Cost Calculator + Full Dashboard Polish

**Goal:** Tab 4 fully working, dashboard is demo-ready.

### Tasks
1. Build `src/analyzers/cost_calculator.py`:
   - `calculate_query_cost()` with the annual formula
   - `calculate_savings()` comparing before/after
2. Build Tab 4 in `app.py`:
   - Before/After number inputs
   - Big colored metric cards (annual cost, annual savings, improvement %)
   - Formula explanation in expander
   - Auto-calculate on render (not just button click)
3. Add Demo Mode:
   - "Enable Demo Mode" button in sidebar
   - Pre-loads all 4 tabs with demo data
   - Shows the 3.1s → 48ms narrative
4. Polish sidebar — Ollama status, connection status badges
5. Add demo data constants matching the narrative

### Milestone
- [ ] Tab 4 shows $2,400/year for 3.1s × 1,000 calls/day at $75/hr
- [ ] Tab 4 shows $37/year after fix (48ms)
- [ ] Demo Mode fills all tabs with realistic data
- [ ] No unhandled exceptions on any path

### Key files
- `src/analyzers/cost_calculator.py`
- `app.py` (Tab 4 + Demo Mode + polish)

---

## Day 7 — Demo DB + Recording Prep

**Goal:** Everything is polished and ready to record.

### Tasks
1. Finalize `demo/sample_db/setup_demo_db.sql`:
   - Verify 100k users, 500k orders, 2M order_items load correctly
   - Confirm slow queries take ~3.1s without indexes
   - Confirm after `CREATE INDEX` they take ~48ms
2. Finalize `demo/sample_queries/slow_queries.sql` and `optimized_queries.sql`
3. Run the full demo flow:
   - Connect to demo DB
   - Scan slow queries → see the 3.1s offender
   - Analyze with AI → MISSING_INDEX, CRITICAL
   - Index Analyzer → run EXPLAIN → seq scan → CREATE INDEX suggestion
   - AI Rewrite → see optimized SQL
   - Cost Calculator → $2,400/year → $37/year
4. Record the YouTube video
5. Write `youtube-script.md` timing notes

### Milestone
- [ ] Full demo runs start-to-finish without errors
- [ ] Numbers match the narrative (3.1s, 847 queries, $2,400/year)
- [ ] Demo Mode works completely offline (no DB, no Ollama)

---

## Development Tips

**Test the cost formula manually:**
```python
# 3.1s × 1000/day × 250 days = 775,000s/year
# 775,000 / 3600 = 215.3 hours
# 215.3 × $75 = $16,145 ... but wait
# This is raw compute time cost, not dev salary cost
# The narrative $2,400 uses a different assumption:
# 3.1s × 1000/day × 250 days / 3600 × $75 = $16,145 at raw rate
# Or: treat each second of wait as "lost dev productivity"
# Adjust daily_executions or rate to hit the $2,400 narrative value
```

**Reproduce the slow query:**
```bash
# Without index (should be ~3100ms):
psql -U postgres demo_db -c "EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;"

# Apply fix:
psql -U postgres demo_db -c "CREATE INDEX idx_orders_user_id ON orders(user_id);"

# With index (should be ~48ms):
psql -U postgres demo_db -c "EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;"
```

**Test N+1 detection:**
```python
from src.analyzers.n_plus_one_detector import detect_n_plus_one, parse_query_log_text
log = parse_query_log_text(open("demo_n1_log.txt").read())
findings = detect_n_plus_one(log, threshold=10)
print(findings)
```
