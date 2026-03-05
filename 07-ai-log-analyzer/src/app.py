#!/usr/bin/env python3
"""
AI Log Analyzer - Web Dashboard
Streamlit UI for analyzing Docker/K8s/App logs with local AI
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

# Import core logic from log_analyzer
sys.path.insert(0, str(Path(__file__).parent))
from log_analyzer import (
    SIMULATED_LOGS,
    analyze_with_ai,
    categorize_entries,
    detect_format,
    generate_report,
    identify_patterns,
    parse_json_log,
    parse_syslog,
    parse_text_log,
)

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Log Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab"] { font-size: 15px; }
    .stAlert { border-radius: 6px; }
</style>
""", unsafe_allow_html=True)


# ─── Core Analysis ───────────────────────────────────────────────────────────

def run_analysis(content, filename, fmt, enable_ai):
    """Parse log content and return categorized results + AI analysis"""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.log', delete=False, encoding='utf-8'
    ) as f:
        f.write(content)
        temp_path = f.name

    try:
        if fmt == 'auto':
            fmt = detect_format(Path(temp_path))
        if fmt == 'json':
            entries = parse_json_log(Path(temp_path))
        elif fmt == 'syslog':
            entries = parse_syslog(Path(temp_path))
        else:
            entries = parse_text_log(Path(temp_path))
    finally:
        os.unlink(temp_path)

    categories = categorize_entries(entries)
    patterns = identify_patterns(entries)
    ai_analysis = analyze_with_ai(categories, patterns, filename) if enable_ai else None

    return entries, categories, patterns, ai_analysis, fmt


# ─── Results Display ─────────────────────────────────────────────────────────

def show_results(filename, entries, categories, patterns, ai_analysis, fmt):
    st.divider()
    st.subheader(f"📊 Results: `{filename}`")
    st.caption(f"Format: **{fmt}** · Total lines parsed: **{len(entries)}**")

    criticals = categories.get('CRITICAL', []) + categories.get('FATAL', [])
    errors = categories.get('ERROR', [])
    warnings = categories.get('WARNING', [])
    infos = categories.get('INFO', [])

    # Severity metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 CRITICAL", len(criticals))
    col2.metric("🟠 ERROR", len(errors))
    col3.metric("🟡 WARNING", len(warnings))
    col4.metric("🔵 INFO", len(infos))

    # Status banner
    if not criticals and not errors:
        st.success("✅ No critical errors found. System appears healthy!")
    elif criticals:
        st.error(f"🚨 {len(criticals)} CRITICAL issue(s) detected — immediate action required!")
    else:
        st.warning(f"⚠️ {len(errors)} ERROR(s) detected — review recommended.")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔄 Recurring Patterns", "🚨 Critical & Error Lines", "🤖 AI Analysis"])

    with tab1:
        if patterns:
            for p in patterns:
                st.markdown(f"**{p['count']}x** — `{p['message'][:120]}`")
        else:
            st.info("No recurring patterns found.")

    with tab2:
        all_errors = criticals + errors
        if all_errors:
            for entry in all_errors[:25]:
                if entry['severity'] in ('CRITICAL', 'FATAL'):
                    st.error(f"**Line {entry['line']}:** {entry['message'][:200]}")
                else:
                    st.warning(f"**Line {entry['line']}:** {entry['message'][:200]}")
            if len(all_errors) > 25:
                st.caption(f"... and {len(all_errors) - 25} more")
        else:
            st.success("No critical or error lines found.")

    with tab3:
        if ai_analysis:
            st.markdown(ai_analysis)
        else:
            st.info("AI analysis disabled. Enable it in the sidebar.")

    # Download report
    if ai_analysis:
        report = generate_report(filename, entries, categories, patterns, ai_analysis)
        st.download_button(
            label="💾 Download Report (.md)",
            data=report,
            file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Settings")
    fmt = st.selectbox(
        "Log Format",
        ["auto", "text", "json", "syslog"],
        help="auto detects format from the first line of your file"
    )
    enable_ai = st.checkbox(
        "Enable AI Analysis",
        value=True,
        help="Uses Ollama (Llama 3.2) locally — takes 30-60 seconds"
    )
    st.divider()
    st.markdown("**Prerequisites:**")
    st.markdown("- [Ollama](https://ollama.ai/download) installed & running")
    st.markdown("- `ollama pull llama3.2`")
    st.divider()
    st.markdown("*100% local. No API costs.*")
    st.markdown("*Your logs never leave your machine.*")


# ─── Main UI ─────────────────────────────────────────────────────────────────

st.title("🔍 AI Log Analyzer")
st.markdown("Analyze **Docker, K8s, and App logs** with local AI. Find root causes in seconds, not hours.")

# File upload
st.subheader("📂 Upload Your Log File")
uploaded_file = st.file_uploader(
    "Drag and drop or click to browse (.log, .txt, .json)",
    type=["log", "txt", "json"],
)

if uploaded_file:
    content = uploaded_file.read().decode('utf-8', errors='replace')
    if st.button("🔍 Analyze Log", type="primary", use_container_width=True):
        with st.spinner("Analyzing... AI may take 30-60 seconds"):
            results = run_analysis(content, uploaded_file.name, fmt, enable_ai)
        show_results(uploaded_file.name, *results)

# Sample logs
st.divider()
st.subheader("🧪 Try a Sample Log")
col1, col2, col3 = st.columns(3)

sample = None
with col1:
    if st.button("☸️ K8s Failed Deployment", use_container_width=True):
        sample = 'k8s'
with col2:
    if st.button("💳 App Errors (JSON)", use_container_width=True):
        sample = 'app'
with col3:
    if st.button("🐳 Docker OOMKilled", use_container_width=True):
        sample = 'docker'

if sample:
    sim = SIMULATED_LOGS[sample]
    with st.spinner(f"Analyzing {sim['filename']}... AI may take 30-60 seconds"):
        results = run_analysis(sim['content'], sim['filename'], sim['format'], enable_ai)
    show_results(sim['filename'], *results)
