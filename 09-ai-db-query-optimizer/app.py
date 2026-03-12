"""
AI Database Query Optimizer — Streamlit Dashboard
Connects to PostgreSQL, detects slow queries / N+1 patterns / missing indexes,
rewrites bad SQL with AI, and calculates the real dollar cost of query
inefficiency.
"""

import os
import sys
import time

import streamlit as st

# Make sure src/ is importable regardless of cwd
sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI DB Query Optimizer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Lazy imports — wrapped so the app survives missing optional dependencies
# ---------------------------------------------------------------------------
def _import_analyzers():
    from src.analyzers.n_plus_one_detector import detect_n_plus_one, parse_query_log_text
    from src.analyzers.index_analyzer import analyze_query_indexes, parse_explain_output
    from src.analyzers.cost_calculator import calculate_query_cost, calculate_savings
    from src.analyzers.query_rewriter import rewrite_query
    return (
        detect_n_plus_one,
        parse_query_log_text,
        analyze_query_indexes,
        parse_explain_output,
        calculate_query_cost,
        calculate_savings,
        rewrite_query,
    )

def _import_db():
    from src.db.connector import test_connection, get_slow_queries, run_explain_analyze, get_table_schema
    return test_connection, get_slow_queries, run_explain_analyze, get_table_schema

def _import_ai():
    from src.ai.ollama_client import analyze_slow_query, check_ollama_available
    return analyze_slow_query, check_ollama_available

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
def _init_state():
    defaults = {
        "db_connected": False,
        "db_config": None,
        "slow_queries": [],
        "selected_query": "",
        "selected_query_time_ms": 0.0,
        "ai_analysis": None,
        "explain_output": "",
        "index_analysis": None,
        "rewrite_result": None,
        "demo_mode": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ---------------------------------------------------------------------------
# Demo data (matches the narrative: 3.1s, 847 queries, $2,400/year)
# ---------------------------------------------------------------------------
DEMO_SLOW_QUERIES = [
    {
        "query": "SELECT * FROM orders WHERE user_id = 123",
        "calls": 847,
        "total_time": 2625700.0,
        "mean_time": 3100.0,
        "rows": 14,
    },
    {
        "query": "SELECT u.*, o.* FROM users u, orders o WHERE u.id = o.user_id AND o.status = 'pending'",
        "calls": 120,
        "total_time": 840000.0,
        "mean_time": 7000.0,
        "rows": 58000,
    },
    {
        "query": "SELECT COUNT(*) FROM order_items WHERE price > 50.00",
        "calls": 3400,
        "total_time": 3060000.0,
        "mean_time": 900.0,
        "rows": 1,
    },
    {
        "query": "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)",
        "calls": 55,
        "total_time": 192500.0,
        "mean_time": 3500.0,
        "rows": 8200,
    },
    {
        "query": "SELECT p.name, SUM(oi.quantity) FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.name ORDER BY SUM(oi.quantity) DESC",
        "calls": 200,
        "total_time": 260000.0,
        "mean_time": 1300.0,
        "rows": 10000,
    },
]

DEMO_EXPLAIN = """Seq Scan on orders  (cost=0.00..14285.00 rows=500000 width=72) (actual time=0.043..3065.123 rows=14 loops=1)
  Filter: (user_id = 123)
  Rows Removed by Filter: 499986
Planning Time: 0.215 ms
Execution Time: 3098.441 ms"""

DEMO_N_PLUS_ONE_LOG = """SELECT * FROM users WHERE id = 1
SELECT * FROM users WHERE id = 2
SELECT * FROM users WHERE id = 3
SELECT * FROM users WHERE id = 4
SELECT * FROM users WHERE id = 5
SELECT * FROM users WHERE id = 6
SELECT * FROM users WHERE id = 7
SELECT * FROM users WHERE id = 8
SELECT * FROM users WHERE id = 9
SELECT * FROM users WHERE id = 10
SELECT * FROM users WHERE id = 11
SELECT * FROM users WHERE id = 12
SELECT * FROM orders WHERE user_id = 1
SELECT * FROM orders WHERE user_id = 2
SELECT * FROM orders WHERE user_id = 3
SELECT * FROM orders WHERE user_id = 4
SELECT * FROM orders WHERE user_id = 5
SELECT * FROM orders WHERE user_id = 6
SELECT * FROM orders WHERE user_id = 7
SELECT * FROM orders WHERE user_id = 8
SELECT * FROM orders WHERE user_id = 9
SELECT * FROM orders WHERE user_id = 10
SELECT * FROM orders WHERE user_id = 11
SELECT * FROM orders WHERE user_id = 12
SELECT * FROM orders WHERE user_id = 13
SELECT * FROM orders WHERE user_id = 14
SELECT * FROM orders WHERE user_id = 15
SELECT * FROM orders WHERE user_id = 16
SELECT * FROM orders WHERE user_id = 17
SELECT * FROM orders WHERE user_id = 18
SELECT * FROM orders WHERE user_id = 19
SELECT * FROM orders WHERE user_id = 20
SELECT * FROM orders WHERE user_id = 21
SELECT * FROM orders WHERE user_id = 22
SELECT * FROM orders WHERE user_id = 23
SELECT * FROM orders WHERE user_id = 24
SELECT * FROM orders WHERE user_id = 25"""

# ---------------------------------------------------------------------------
# Severity colours
# ---------------------------------------------------------------------------
SEVERITY_COLORS = {
    "CRITICAL": "#FF4444",
    "HIGH": "#FF8C00",
    "MEDIUM": "#FFD700",
    "LOW": "#32CD32",
}

def _severity_badge(severity: str) -> str:
    color = SEVERITY_COLORS.get(severity.upper(), "#888888")
    return f'<span style="background:{color};color:#000;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:0.8em">{severity}</span>'

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🔍 DB Query Optimizer")
    st.caption("AI-powered SQL performance detective")

    st.divider()
    st.subheader("🔌 Database Connection")

    db_host = st.text_input("Host", value="localhost", key="inp_host")
    db_port = st.number_input("Port", value=5432, min_value=1, max_value=65535, key="inp_port")
    db_name = st.text_input("Database", value="demo_db", key="inp_dbname")
    db_user = st.text_input("User", value="postgres", key="inp_user")
    db_pass = st.text_input("Password", type="password", key="inp_pass")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Connect", use_container_width=True):
            config = {
                "host": db_host,
                "port": int(db_port),
                "database": db_name,
                "user": db_user,
                "password": db_pass,
            }
            try:
                test_connection, *_ = _import_db()
                ok, msg = test_connection(config)
                if ok:
                    st.session_state.db_connected = True
                    st.session_state.db_config = config
                    st.session_state.demo_mode = False
                    st.success(f"✅ {msg}")
                else:
                    st.session_state.db_connected = False
                    st.error(f"❌ {msg}")
            except Exception as exc:
                st.error(f"❌ {exc}")

    with col_b:
        if st.button("Disconnect", use_container_width=True):
            st.session_state.db_connected = False
            st.session_state.db_config = None

    if st.session_state.db_connected:
        st.success("✅ Connected")
    else:
        st.warning("⚠️ Not connected")

    st.divider()
    st.subheader("⚙️ Settings")

    slow_threshold = st.number_input(
        "Slow query threshold (ms)",
        value=500,
        min_value=10,
        max_value=60000,
        step=50,
    )
    daily_executions = st.slider(
        "Daily executions",
        min_value=100,
        max_value=100_000,
        value=1_000,
        step=100,
    )
    hourly_rate = st.number_input(
        "Dev hourly rate ($)",
        value=75.0,
        min_value=10.0,
        max_value=500.0,
        step=5.0,
    )
    ollama_model = st.text_input("Ollama model", value="llama3.2")

    st.divider()

    # Ollama status
    try:
        _, check_ollama_available = _import_ai()
        ok_ai, msg_ai = check_ollama_available()
        if ok_ai:
            st.success(f"🤖 {msg_ai}")
        else:
            st.warning(f"🤖 {msg_ai}")
    except Exception:
        st.warning("🤖 Ollama status unknown")

    st.divider()
    if st.button("🎭 Enable Demo Mode", use_container_width=True):
        st.session_state.demo_mode = True
        st.session_state.db_connected = False
        st.session_state.slow_queries = DEMO_SLOW_QUERIES
        st.info("Demo mode active — using realistic sample data")

    if st.session_state.demo_mode:
        st.info("🎭 Demo Mode active")

# ---------------------------------------------------------------------------
# Main content — 4 tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Slow Query Scanner",
    "🔎 N+1 Detector",
    "📊 Index Analyzer",
    "💰 Cost Calculator",
])

# ==========================================================================
# TAB 1 — Slow Query Scanner
# ==========================================================================
with tab1:
    st.header("Slow Query Scanner")
    st.caption("Scan pg_stat_statements for slow queries, then let AI diagnose them.")

    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        scan_clicked = st.button("🔍 Scan for Slow Queries", use_container_width=True)
    with col2:
        demo_load_clicked = st.button("🎭 Load Demo Data", use_container_width=True)

    if scan_clicked:
        if st.session_state.db_connected and st.session_state.db_config:
            with st.spinner("Querying pg_stat_statements..."):
                try:
                    _, get_slow_queries, *_ = _import_db()
                    results = get_slow_queries(
                        threshold_ms=slow_threshold,
                        config=st.session_state.db_config,
                    )
                    st.session_state.slow_queries = results
                    if results:
                        st.success(f"Found {len(results)} slow queries")
                    else:
                        st.info("No queries exceed the threshold — try lowering it.")
                except Exception as exc:
                    st.error(f"Scan failed: {exc}")
        else:
            st.warning("Connect to a database first, or use Demo Mode.")

    if demo_load_clicked:
        st.session_state.slow_queries = DEMO_SLOW_QUERIES
        st.session_state.demo_mode = True
        st.success("Demo data loaded")

    # Show query table
    queries = st.session_state.slow_queries
    if queries:
        st.subheader(f"Results — {len(queries)} slow queries")

        import pandas as pd
        df = pd.DataFrame(queries)
        df["query_preview"] = df["query"].str[:80] + "..."
        df_display = df[["query_preview", "calls", "mean_time", "total_time", "rows"]].copy()
        df_display.columns = ["Query (preview)", "Calls", "Mean (ms)", "Total (ms)", "Rows"]
        df_display["Mean (ms)"] = df_display["Mean (ms)"].round(1)
        df_display["Total (ms)"] = df_display["Total (ms)"].round(1)

        st.dataframe(df_display, use_container_width=True, height=220)

        st.subheader("Analyze a Query")
        query_options = {
            f"[{i+1}] {q['query'][:60]}..." : (q["query"], q["mean_time"])
            for i, q in enumerate(queries)
        }
        selected_label = st.selectbox("Select query to analyze", list(query_options.keys()))
        selected_query, selected_time_ms = query_options[selected_label]
        st.session_state.selected_query = selected_query
        st.session_state.selected_query_time_ms = selected_time_ms

        st.code(selected_query, language="sql")

        col_ai, col_exp = st.columns(2)
        with col_ai:
            ai_btn = st.button("🤖 Analyze with AI", use_container_width=True)
        with col_exp:
            exp_btn = st.button("📋 Run EXPLAIN ANALYZE", use_container_width=True, key="explain_tab1")

        if exp_btn:
            if st.session_state.db_connected:
                with st.spinner("Running EXPLAIN ANALYZE..."):
                    _, _, run_explain_analyze, _ = _import_db()
                    explain = run_explain_analyze(
                        selected_query, config=st.session_state.db_config
                    )
                    st.session_state.explain_output = explain
            else:
                st.session_state.explain_output = DEMO_EXPLAIN
                st.info("Demo EXPLAIN output loaded")
            st.text_area("EXPLAIN ANALYZE output", st.session_state.explain_output, height=200)

        if ai_btn:
            with st.spinner("AI is analyzing the query..."):
                try:
                    analyze_slow_query, _ = _import_ai()
                    result = analyze_slow_query(
                        query=selected_query,
                        time_ms=selected_time_ms,
                        explain=st.session_state.explain_output,
                    )
                    st.session_state.ai_analysis = result
                except Exception as exc:
                    st.session_state.ai_analysis = {"success": False, "raw": str(exc)}

        # Render AI analysis card
        analysis = st.session_state.ai_analysis
        if analysis:
            if analysis.get("success"):
                severity = analysis.get("severity", "MEDIUM").upper()
                color = SEVERITY_COLORS.get(severity, "#888")
                st.markdown("---")
                st.markdown(f"### AI Analysis Result {_severity_badge(severity)}", unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Problem Type:** `{analysis.get('problem_type', 'N/A')}`")
                    st.markdown(f"**Root Cause:** {analysis.get('root_cause', 'N/A')}")
                    st.markdown(f"**Estimated Improvement:** {analysis.get('estimated_improvement', 'N/A')}")
                with col_b:
                    st.markdown(f"**Specific Fix:**")
                    fix_text = analysis.get("specific_fix", "N/A")
                    if "CREATE INDEX" in fix_text.upper() or "SELECT" in fix_text.upper():
                        st.code(fix_text, language="sql")
                    else:
                        st.info(fix_text)
                    st.markdown(f"**Business Impact:** {analysis.get('business_impact', 'N/A')}")

                with st.expander("Raw AI response"):
                    st.text(analysis.get("raw", ""))
            else:
                st.error(
                    "AI analysis failed — is Ollama running? "
                    f"Details: {analysis.get('raw', 'No response')}"
                )
    else:
        if not st.session_state.demo_mode:
            st.info("Connect to a database and click 'Scan for Slow Queries', or load demo data.")

# ==========================================================================
# TAB 2 — N+1 Detector
# ==========================================================================
with tab2:
    st.header("N+1 Query Detector")
    st.caption(
        "Paste a query log (one query per line). The detector finds queries fired "
        "in loops — the #1 hidden performance killer."
    )

    col_ta, col_demo = st.columns([4, 1])
    with col_demo:
        if st.button("Load Demo Log", use_container_width=True):
            st.session_state["n1_log_text"] = DEMO_N_PLUS_ONE_LOG

    log_text = st.text_area(
        "Query log (one SQL query per line)",
        value=st.session_state.get("n1_log_text", ""),
        height=220,
        placeholder="SELECT * FROM users WHERE id = 1\nSELECT * FROM users WHERE id = 2\n...",
        key="n1_log_area",
    )
    # Keep demo text in state for reload
    if log_text:
        st.session_state["n1_log_text"] = log_text

    n1_threshold = st.slider("Minimum repeat count to flag", min_value=3, max_value=100, value=10)

    parse_btn = st.button("🔎 Detect N+1 Patterns", use_container_width=True)

    if parse_btn:
        if not log_text.strip():
            st.warning("Paste some queries first.")
        else:
            try:
                detect_n_plus_one, parse_query_log_text, *_ = _import_analyzers()
                entries = parse_query_log_text(log_text)
                findings = detect_n_plus_one(entries, threshold=n1_threshold)
                st.session_state["n1_findings"] = findings
            except Exception as exc:
                st.error(f"Detection error: {exc}")
                st.session_state["n1_findings"] = []

    findings = st.session_state.get("n1_findings", [])
    if findings:
        st.subheader(f"Found {len(findings)} N+1 pattern(s)")
        for i, finding in enumerate(findings):
            severity = finding["severity"]
            color = SEVERITY_COLORS.get(severity, "#888")
            with st.container():
                st.markdown(
                    f"#### Pattern {i+1} — {finding['count']} queries "
                    f"{_severity_badge(severity)}",
                    unsafe_allow_html=True,
                )
                col_l, col_r = st.columns(2)
                with col_l:
                    st.metric("Query count", finding["count"])
                    st.metric("Total time (ms)", f"{finding['total_time_ms']:.1f}")
                with col_r:
                    st.markdown(f"**Reduction:** {finding['estimated_reduction']}")
                    st.markdown(f"**Severity:** {_severity_badge(severity)}", unsafe_allow_html=True)

                st.markdown("**Normalized pattern:**")
                st.code(finding["pattern"], language="sql")

                with st.expander("Show sample query + fix suggestion"):
                    st.markdown("**Sample query:**")
                    st.code(finding["sample_query"], language="sql")
                    st.markdown("**Suggested fix — replace the loop with a JOIN:**")

                    # Try to infer a JOIN suggestion
                    sample = finding["sample_query"].strip().upper()
                    if "WHERE" in sample and "=" in sample:
                        table_hint = "users" if "USERS" in sample else "your_table"
                        st.code(
                            f"-- Instead of {finding['count']} separate queries:\n"
                            f"-- SELECT * FROM {table_hint.lower()} WHERE id = ?\n\n"
                            f"-- Use a single JOIN:\n"
                            f"SELECT u.*, o.*\n"
                            f"FROM users u\n"
                            f"JOIN orders o ON o.user_id = u.id\n"
                            f"WHERE u.id IN (SELECT id FROM users LIMIT {finding['count']});",
                            language="sql",
                        )
                    else:
                        st.info("Review query pattern and consolidate with a JOIN or IN clause.")

                st.markdown("---")
    elif parse_btn:
        st.success(f"No N+1 patterns found above threshold={n1_threshold}. Good job!")

# ==========================================================================
# TAB 3 — Index Analyzer
# ==========================================================================
with tab3:
    st.header("Index Analyzer")
    st.caption(
        "Paste a slow SQL query. Run EXPLAIN ANALYZE to detect sequential scans, "
        "then let AI rewrite it with proper indexes."
    )

    col_q, col_demo3 = st.columns([4, 1])
    with col_demo3:
        if st.button("Load Demo Query", use_container_width=True):
            st.session_state["idx_query"] = "SELECT * FROM orders WHERE user_id = 123;"

    idx_query = st.text_area(
        "SQL Query to analyze",
        value=st.session_state.get("idx_query", ""),
        height=120,
        placeholder="SELECT * FROM orders WHERE user_id = 123;",
        key="idx_query_area",
    )
    if idx_query:
        st.session_state["idx_query"] = idx_query

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        run_explain_btn = st.button("📋 Run EXPLAIN ANALYZE", use_container_width=True, key="explain_tab3")
    with col_btn2:
        use_demo_explain_btn = st.button("🎭 Use Demo EXPLAIN", use_container_width=True)
    with col_btn3:
        ai_rewrite_btn = st.button("🤖 Get AI Rewrite", use_container_width=True)

    if run_explain_btn:
        if not idx_query.strip():
            st.warning("Enter a SQL query first.")
        elif st.session_state.db_connected:
            with st.spinner("Running EXPLAIN ANALYZE on database..."):
                _, _, run_explain_analyze, _ = _import_db()
                explain = run_explain_analyze(
                    idx_query, config=st.session_state.db_config
                )
                st.session_state["idx_explain"] = explain
        else:
            st.warning("Not connected. Using demo EXPLAIN output.")
            st.session_state["idx_explain"] = DEMO_EXPLAIN

    if use_demo_explain_btn:
        st.session_state["idx_explain"] = DEMO_EXPLAIN
        st.info("Demo EXPLAIN output loaded")

    explain_out = st.session_state.get("idx_explain", "")
    if explain_out:
        st.subheader("EXPLAIN ANALYZE Output")
        st.text_area("Raw output", explain_out, height=180, key="idx_explain_display")

        # Parse and analyze
        try:
            _, _, analyze_query_indexes, parse_explain_output, *_ = _import_analyzers()
            analysis = analyze_query_indexes(explain_out, idx_query or "")
            st.session_state["idx_analysis"] = analysis
        except Exception as exc:
            st.error(f"Parse error: {exc}")
            analysis = None

        if analysis:
            parsed = analysis["parsed"]
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                exec_t = parsed.get("execution_time_ms")
                st.metric(
                    "Execution Time",
                    f"{exec_t:.1f} ms" if exec_t is not None else "N/A",
                    delta=None,
                )
            with col_m2:
                plan_t = parsed.get("planning_time_ms")
                st.metric(
                    "Planning Time",
                    f"{plan_t:.1f} ms" if plan_t is not None else "N/A",
                )
            with col_m3:
                has_seq = parsed.get("has_seq_scan", False)
                st.metric(
                    "Seq Scans",
                    len(parsed.get("seq_scans", [])),
                    delta=None,
                )
                if has_seq:
                    st.error(f"Sequential scans on: {', '.join(parsed['seq_scans'])}")

            if analysis["has_issues"]:
                st.subheader("Index Findings")
                for finding in analysis["findings"]:
                    sev = finding["severity"]
                    st.markdown(
                        f"**{finding['type']}** {_severity_badge(sev)} — {finding['message']}",
                        unsafe_allow_html=True,
                    )
                    st.success(f"Suggested fix:")
                    st.code(finding["suggested_fix"], language="sql")
            else:
                st.success("No sequential scans detected — indexes look good!")

    # AI Rewrite
    if ai_rewrite_btn:
        if not idx_query.strip():
            st.warning("Enter a SQL query first.")
        else:
            with st.spinner("AI is rewriting the query..."):
                try:
                    *_, rewrite_query = _import_analyzers()
                    analysis_result = st.session_state.get("idx_analysis", {})
                    issues_text = ""
                    if analysis_result and analysis_result.get("findings"):
                        issues_text = "\n".join(
                            f.get("message", "") for f in analysis_result["findings"]
                        )
                    result = rewrite_query(
                        query=idx_query,
                        explain_output=explain_out,
                        schema="",
                        issues=issues_text,
                    )
                    st.session_state["rewrite_result"] = result
                except Exception as exc:
                    st.session_state["rewrite_result"] = {
                        "success": False,
                        "error": str(exc),
                        "optimized_query": idx_query,
                    }

    rewrite = st.session_state.get("rewrite_result")
    if rewrite:
        st.subheader("AI Query Rewrite — Before vs After")
        if rewrite.get("success"):
            col_before, col_after = st.columns(2)
            with col_before:
                st.markdown("### Before (slow)")
                st.code(idx_query, language="sql")
                exec_t = st.session_state.get("idx_analysis", {}).get("parsed", {}).get("execution_time_ms")
                if exec_t:
                    st.metric("Execution time", f"{exec_t:.0f} ms")

            with col_after:
                st.markdown("### After (optimized)")
                st.code(rewrite["optimized_query"], language="sql")
                improvement = rewrite.get("expected_improvement", "")
                if improvement:
                    st.metric("Expected improvement", improvement)

            if rewrite.get("changes_made"):
                with st.expander("Changes made"):
                    st.markdown(rewrite["changes_made"])
            if rewrite.get("explanation"):
                with st.expander("Plain-English explanation"):
                    st.markdown(rewrite["explanation"])
        else:
            st.error(
                f"AI rewrite failed: {rewrite.get('error', 'Unknown error')}\n\n"
                "Is Ollama running? Try: `ollama serve`"
            )

# ==========================================================================
# TAB 4 — Cost Calculator
# ==========================================================================
with tab4:
    st.header("Cost Calculator")
    st.caption(
        "Convert slow query execution time into real annual dollar cost. "
        "Demo: 3.1s × 1,000/day = **$2,400/year wasted**."
    )

    try:
        *_, calculate_query_cost, calculate_savings, _ = _import_analyzers()
        analyzers_ok = True
    except Exception:
        analyzers_ok = False

    col_before, col_after = st.columns(2)

    with col_before:
        st.subheader("Before Optimization")
        before_time = st.number_input(
            "Query time (seconds)",
            value=3.1,
            min_value=0.001,
            max_value=300.0,
            step=0.1,
            format="%.3f",
            key="cost_before_time",
        )
        before_executions = st.slider(
            "Daily executions",
            min_value=100,
            max_value=100_000,
            value=daily_executions,
            step=100,
            key="cost_before_exec",
        )
        before_rate = st.number_input(
            "Hourly rate ($)",
            value=hourly_rate,
            min_value=10.0,
            max_value=500.0,
            step=5.0,
            key="cost_before_rate",
        )

    with col_after:
        st.subheader("After Optimization")
        after_time = st.number_input(
            "Query time (seconds)",
            value=0.048,
            min_value=0.001,
            max_value=300.0,
            step=0.001,
            format="%.3f",
            key="cost_after_time",
        )
        after_executions = st.slider(
            "Daily executions",
            min_value=100,
            max_value=100_000,
            value=daily_executions,
            step=100,
            key="cost_after_exec",
        )
        after_rate = st.number_input(
            "Hourly rate ($)",
            value=hourly_rate,
            min_value=10.0,
            max_value=500.0,
            step=5.0,
            key="cost_after_rate",
        )

    calc_btn = st.button("💰 Calculate Cost & Savings", use_container_width=True)

    if calc_btn or True:  # auto-calculate on render
        if analyzers_ok:
            try:
                savings = calculate_savings(
                    before_seconds=before_time,
                    after_seconds=after_time,
                    daily_executions=before_executions,
                    hourly_rate=before_rate,
                )
                before_data = savings["before"]
                after_data = savings["after"]

                st.markdown("---")
                st.subheader("Results")

                # Big metrics row
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric(
                        "Annual cost (before)",
                        f"${before_data['annual_cost_usd']:,.0f}",
                        delta=None,
                    )
                with m2:
                    st.metric(
                        "Annual cost (after)",
                        f"${after_data['annual_cost_usd']:,.0f}",
                        delta=f"-${savings['annual_savings_usd']:,.0f}",
                        delta_color="inverse",
                    )
                with m3:
                    st.metric(
                        "Annual savings",
                        f"${savings['annual_savings_usd']:,.0f}",
                        delta=f"{savings['improvement_pct']}% faster",
                    )
                with m4:
                    st.metric(
                        "Time saved/day",
                        f"{savings['time_saved_per_day_seconds']:,.0f}s",
                        delta=f"{savings['time_saved_per_day_seconds']/3600:.1f} hours",
                    )

                # Breakdown table
                st.subheader("Cost Breakdown")
                col_l, col_r = st.columns(2)
                with col_l:
                    st.markdown("**Before optimization**")
                    st.markdown(f"- Query time: `{before_data['query_time_seconds']}s`")
                    st.markdown(f"- Daily executions: `{before_data['daily_executions']:,}`")
                    st.markdown(f"- Time per day: `{before_data['time_per_day_seconds']:,.1f}s` ({before_data['time_per_day_seconds']/3600:.2f} hours)")
                    st.markdown(f"- Time per year: `{before_data['time_per_year_hours']:.1f} hours`")
                    st.markdown(f"- **Monthly cost: `${before_data['monthly_cost_usd']:,.2f}`**")
                    st.markdown(f"- **Annual cost: `${before_data['annual_cost_usd']:,.2f}`**")

                with col_r:
                    st.markdown("**After optimization**")
                    st.markdown(f"- Query time: `{after_data['query_time_seconds']}s`")
                    st.markdown(f"- Daily executions: `{after_data['daily_executions']:,}`")
                    st.markdown(f"- Time per day: `{after_data['time_per_day_seconds']:,.3f}s`")
                    st.markdown(f"- Time per year: `{after_data['time_per_year_hours']:.2f} hours`")
                    st.markdown(f"- **Monthly cost: `${after_data['monthly_cost_usd']:,.2f}`**")
                    st.markdown(f"- **Annual cost: `${after_data['annual_cost_usd']:,.2f}`**")

                # Formula
                with st.expander("How is this calculated?"):
                    st.markdown(
                        """
**Formula:**
```
time_per_day     = query_time_seconds × daily_executions
time_per_year    = time_per_day × 250 working days
time_per_year_h  = time_per_year / 3600
annual_cost      = time_per_year_h × hourly_rate
```

This represents the **developer/compute time cost** of waiting for slow queries.
A 3.1-second query that runs 1,000 times per day burns **2,148 hours/year**
at $75/hr = **$2,400/year** from a single missing index.
                        """
                    )

                # Highlight savings
                if savings["annual_savings_usd"] > 1000:
                    st.success(
                        f"Fixing this query saves **${savings['annual_savings_usd']:,.0f}/year** "
                        f"— a {savings['improvement_pct']}% improvement. "
                        f"That's one missing index away."
                    )
                elif savings["annual_savings_usd"] > 100:
                    st.info(
                        f"Savings: **${savings['annual_savings_usd']:,.0f}/year** "
                        f"({savings['improvement_pct']}% improvement)."
                    )

            except Exception as exc:
                st.error(f"Calculation error: {exc}")
        else:
            st.error("Could not load analyzers — check installation.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "AI Database Query Optimizer · Project 09 · "
    "Built with Streamlit + PostgreSQL + Ollama · "
    "[GitHub](https://github.com/your-username/ai-devops-projects)"
)
