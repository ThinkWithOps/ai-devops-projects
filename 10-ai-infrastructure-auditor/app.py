"""
AI Infrastructure Auditor — DevSecOps Platform
Project 10 of 12 — AI + DevOps Portfolio Series
"""
import os
import sys
import json

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scanner.scan_runner import run_workspace_scan, save_scan_history, load_scan_history
from src.ai.ollama_client import check_ollama_available, explain_finding

# ------------------------------------------------------------------ #
# Page configuration
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="AI Infrastructure Auditor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
# Custom CSS
# ------------------------------------------------------------------ #
st.markdown("""
<style>
.finding-critical { border-left: 4px solid #ff4444; padding: 8px 12px; margin: 4px 0; background: rgba(255,68,68,0.05); }
.finding-high { border-left: 4px solid #ff8800; padding: 8px 12px; margin: 4px 0; background: rgba(255,136,0,0.05); }
.finding-medium { border-left: 4px solid #ffcc00; padding: 8px 12px; margin: 4px 0; background: rgba(255,204,0,0.05); }
.finding-low { border-left: 4px solid #888888; padding: 8px 12px; margin: 4px 0; background: rgba(136,136,136,0.05); }
.metric-card { text-align: center; padding: 16px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
# Constants
# ------------------------------------------------------------------ #
SEVERITY_COLORS = {
    "CRITICAL": "#FF4B4B",
    "HIGH": "#FF8C00",
    "MEDIUM": "#FFC300",
    "LOW": "#4CAF50",
}

SEVERITY_EMOJI = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}

FILE_TYPE_ICONS = {
    "kubernetes": "🔵",
    "docker_compose": "🐳",
    "terraform": "🟠",
}

_BASE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_WORKSPACE = os.path.join(_BASE, "sample_ecommerce_app", "infra")

# ------------------------------------------------------------------ #
# Session state initialisation
# ------------------------------------------------------------------ #
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None
if "ai_cache" not in st.session_state:
    st.session_state.ai_cache = {}
if "ollama_available" not in st.session_state:
    st.session_state.ollama_available = False


# ------------------------------------------------------------------ #
# Helper: render file tree recursively
# ------------------------------------------------------------------ #
def _render_tree(node: dict, indent: int = 0) -> None:
    prefix = "&nbsp;" * (indent * 4)
    for key, val in node.items():
        if isinstance(val, dict):
            st.markdown(f"{prefix}📁 **{key}**", unsafe_allow_html=True)
            _render_tree(val, indent + 1)
        else:
            icon = FILE_TYPE_ICONS.get(val, "📄")
            st.markdown(f"{prefix}{icon} `{key}`", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
# Helper: grade colour
# ------------------------------------------------------------------ #
def _grade_color(grade: str) -> str:
    return {
        "A": "#4CAF50",
        "B": "#8BC34A",
        "C": "#FFC300",
        "D": "#FF8C00",
        "F": "#FF4B4B",
    }.get(grade, "#FFFFFF")


# ------------------------------------------------------------------ #
# Sidebar
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("## 🔍 AI Infrastructure Auditor")
    st.markdown("---")

    # --- Workspace selection ---
    st.markdown("**WORKSPACE**")
    workspace_choice = st.radio(
        "Select workspace",
        options=["Sample Ecommerce App", "Custom Path"],
        key="workspace_radio",
        label_visibility="collapsed",
    )

    workspace_path = SAMPLE_WORKSPACE
    if workspace_choice == "Custom Path":
        custom_path = st.text_input(
            "Workspace path",
            placeholder="e.g. C:/projects/my-infra",
            key="custom_workspace_path",
        )
        if custom_path.strip():
            workspace_path = custom_path.strip()

    run_clicked = st.button(
        "🚀 Run Audit",
        use_container_width=True,
        type="primary",
        key="run_audit_btn",
    )

    st.markdown("---")

    # --- File tree (shown after scan) ---
    if st.session_state.scan_result is not None:
        st.markdown("**📁 WORKSPACE TREE**")
        file_tree = st.session_state.scan_result.get("file_tree", {})
        if file_tree:
            _render_tree(file_tree)
        else:
            st.caption("No IaC files found.")
        st.markdown("---")

    # --- Ollama status ---
    st.markdown("**OLLAMA STATUS**")
    ollama_ok = check_ollama_available()
    st.session_state.ollama_available = ollama_ok
    if ollama_ok:
        st.success("✅ Ollama ready — llama3.2")
    else:
        st.warning("⚠️ Ollama offline — AI disabled")

    st.markdown("---")

    # --- Scan history ---
    st.markdown("**SCAN HISTORY**")
    history_file = os.path.join(_BASE, "scan_history.json")
    history = load_scan_history(history_file)
    if not history:
        st.caption("No previous scans.")
    else:
        for entry in history[:3]:
            ts = entry.get("scanned_at", "")[:16].replace("T", " ")
            score = entry.get("score", "?")
            grade = entry.get("grade", "?")
            total = entry.get("total_findings", "?")
            critical = entry.get("critical", 0)
            st.markdown(
                f"**{ts}**  \n"
                f"Score: `{score}/100` Grade: `{grade}`  \n"
                f"Findings: `{total}` · Critical: `{critical}`"
            )
            st.markdown("&nbsp;")

# ------------------------------------------------------------------ #
# Run audit on button click
# ------------------------------------------------------------------ #
if run_clicked:
    try:
        with st.spinner("🔍 Scanning workspace..."):
            result = run_workspace_scan(workspace_path)
        save_scan_history(result, history_file=os.path.join(_BASE, "scan_history.json"))
        st.session_state.scan_result = result
        st.session_state.ai_cache = {}
        st.rerun()
    except Exception as exc:
        st.error(f"Scan failed: {exc}")

# ------------------------------------------------------------------ #
# Main area — before scan: welcome / landing view
# ------------------------------------------------------------------ #
if st.session_state.scan_result is None:
    st.title("🔍 AI Infrastructure Auditor")
    st.markdown("##### DevSecOps security platform for Infrastructure-as-Code")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### ☸️ Kubernetes Security")
        st.markdown(
            "Detects privileged containers, root users, missing resource limits, "
            "hostNetwork access, and image tag issues across all Kubernetes manifests."
        )
    with col2:
        st.markdown("### 🐳 Docker Compose Audit")
        st.markdown(
            "Catches hardcoded secrets, privileged services, ports bound to 0.0.0.0, "
            "missing healthchecks, and unset resource limits."
        )
    with col3:
        st.markdown("### 🏗️ Terraform Compliance")
        st.markdown(
            "Finds open security groups, public S3 buckets, unencrypted RDS instances, "
            "missing deletion protection, and hardcoded regions."
        )

    st.markdown("---")
    st.info("Select a workspace in the sidebar and click **Run Audit** to begin.")
    st.stop()

# ------------------------------------------------------------------ #
# Main area — after scan: results
# ------------------------------------------------------------------ #
result = st.session_state.scan_result
findings: list[dict] = result.get("all_findings", [])
compliance: dict = result.get("compliance", {})
files_scanned: list[dict] = result.get("files_scanned", [])
files_by_type: dict = result.get("files_by_type", {})

st.title("🔍 AI Infrastructure Auditor")
st.caption(f"Workspace: `{result.get('workspace', '')}` · Scanned: {result.get('scanned_at', '')[:19].replace('T', ' ')}")
st.markdown("---")

# ------------------------------------------------------------------ #
# Section 1: Risk Dashboard
# ------------------------------------------------------------------ #
st.subheader("📊 Risk Dashboard")

total = compliance.get("total_findings", 0)
breakdown = compliance.get("breakdown", {})
score = compliance.get("score", 0)
grade = compliance.get("grade", "F")
crit_count = breakdown.get("CRITICAL", 0)
high_count = breakdown.get("HIGH", 0)
med_count = breakdown.get("MEDIUM", 0)
low_count = breakdown.get("LOW", 0)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Findings", total)
with m2:
    st.metric("🔴 Critical", crit_count)
with m3:
    st.metric("Security Score", f"{score}/100")
with m4:
    grade_color = _grade_color(grade)
    st.metric("Grade", grade)

r1, r2, r3 = st.columns(3)
with r1:
    st.metric("Files Scanned", len(files_scanned))
with r2:
    st.metric("🟠 High", high_count)
with r3:
    st.metric("🟡 Med + Low", med_count + low_count)

st.markdown("---")

# ------------------------------------------------------------------ #
# Section 2: Top 3 Urgent Fixes
# ------------------------------------------------------------------ #
top3 = compliance.get("top_3_urgent", [])
if top3:
    st.subheader("🚨 Top 3 Urgent Fixes")
    for idx, urgent in enumerate(top3, 1):
        sev = urgent.get("severity", "")
        emoji = SEVERITY_EMOJI.get(sev, "")
        color = SEVERITY_COLORS.get(sev, "#FFFFFF")
        fix_text = urgent.get("fix", "")
        title_text = urgent.get("title", "")
        st.markdown(
            f"**{idx}.** {emoji} "
            f"<span style='color:{color}; font-weight:bold;'>[{sev}]</span> "
            f"**{title_text}**  \n"
            f"_{fix_text}_",
            unsafe_allow_html=True,
        )
    st.markdown("---")

# ------------------------------------------------------------------ #
# Section 3: Findings Explorer
# ------------------------------------------------------------------ #
st.subheader("🔎 Findings Explorer")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    selected_severities = st.multiselect(
        "Severity",
        options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        key="filter_severity",
    )
with filter_col2:
    selected_types = st.multiselect(
        "Type",
        options=["Kubernetes", "Docker Compose", "Terraform"],
        default=["Kubernetes", "Docker Compose", "Terraform"],
        key="filter_type",
    )

# Map display label back to source_label values
label_map = {
    "Kubernetes": "Kubernetes",
    "Docker Compose": "Docker Compose",
    "Terraform": "Terraform",
}
selected_labels = [label_map[t] for t in selected_types]

filtered_findings = [
    f for f in findings
    if f.get("severity") in selected_severities
    and f.get("source_label", f.get("source_type", "")) in selected_labels
]

if not filtered_findings:
    st.success("No findings match the current filters.")
else:
    st.caption(f"Showing {len(filtered_findings)} of {total} findings")

    for i, finding in enumerate(filtered_findings):
        sev = finding.get("severity", "LOW")
        emoji = SEVERITY_EMOJI.get(sev, "")
        source_file = finding.get("source_file", "")
        source_label = finding.get("source_label", finding.get("source_type", ""))
        title_text = finding.get("title", "")

        expander_label = (
            f"{emoji} [{sev}] {title_text}  ·  {source_file}  ·  {source_label}"
        )

        with st.expander(expander_label, expanded=False):
            left_col, right_col = st.columns([3, 2])

            with left_col:
                st.markdown("**📋 Detail**")
                st.markdown(finding.get("detail", ""))

                fix_text = finding.get("fix", "")
                if fix_text:
                    st.info(f"🔧 **Recommended Fix:** {fix_text}")

                example_text = finding.get("example", "")
                if example_text:
                    lang = "hcl" if source_label == "Terraform" else "yaml"
                    st.code(example_text, language=lang)

            with right_col:
                st.markdown("**🤖 AI Explanation**")
                cache_key = f"{title_text}|{source_file}"

                if cache_key in st.session_state.ai_cache:
                    st.success(st.session_state.ai_cache[cache_key])
                elif not ollama_ok:
                    st.warning(
                        "⚠️ Ollama not available — start Ollama to enable AI explanations"
                    )
                else:
                    if st.button("🤖 Explain with AI", key=f"ai_{i}"):
                        with st.spinner("Asking AI..."):
                            try:
                                explanation = explain_finding(
                                    finding_title=title_text,
                                    finding_detail=finding.get("detail", ""),
                                    file_type=source_label,
                                    fix=fix_text,
                                )
                                if explanation:
                                    st.session_state.ai_cache[cache_key] = explanation
                                    st.success(explanation)
                                else:
                                    st.warning(
                                        "AI did not return an explanation. "
                                        "Check that Ollama is running and the model is available."
                                    )
                            except Exception as exc:
                                st.error(f"AI request failed: {exc}")

st.markdown("---")

# ------------------------------------------------------------------ #
# Section 4: Scan Details (collapsed)
# ------------------------------------------------------------------ #
with st.expander("📄 Scan Details", expanded=False):
    st.markdown("**Files Scanned**")
    if files_scanned:
        import pandas as pd
        df_data = [
            {
                "File": f["relative_path"],
                "Type": f["file_type"].replace("_", " ").title(),
                "Findings": f["findings_count"],
            }
            for f in files_scanned
        ]
        st.dataframe(df_data, use_container_width=True)
    else:
        st.caption("No files were scanned.")

    st.markdown("**Raw Findings (JSON)**")
    st.json(findings)
