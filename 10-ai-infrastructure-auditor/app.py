"""
AI Infrastructure Auditor — Streamlit Web App
Project 10 of 12 — AI + DevOps Portfolio Series

Audits Kubernetes YAML, Docker Compose, and Terraform files for security
issues, misconfigurations, and best-practice violations.
Uses Ollama (Llama 3.2) locally for AI explanations — no API costs.
"""
import json
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from src.auditors.compliance_checker import calculate_compliance_score
from src.auditors.docker_compose_auditor import audit_docker_compose
from src.auditors.kubernetes_auditor import audit_kubernetes
from src.auditors.terraform_auditor import audit_terraform
from src.ai.ollama_client import check_ollama_available, explain_finding

# ------------------------------------------------------------------ #
# Page configuration
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="AI Infrastructure Auditor",
    page_icon="🔍",
    layout="wide",
)

# ------------------------------------------------------------------ #
# Severity colours used throughout the UI
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

# ------------------------------------------------------------------ #
# Sample file paths
# ------------------------------------------------------------------ #
_BASE = os.path.dirname(__file__)
SAMPLE_FILES = {
    "Kubernetes YAML": os.path.join(_BASE, "sample_infra", "insecure_k8s.yaml"),
    "Docker Compose": os.path.join(_BASE, "sample_infra", "insecure_docker_compose.yml"),
    "Terraform": os.path.join(_BASE, "sample_infra", "insecure_terraform.tf"),
}

SAMPLE_BUTTON_LABELS = {
    "Kubernetes YAML": "Load Insecure K8s Sample",
    "Docker Compose": "Load Insecure Docker Compose Sample",
    "Terraform": "Load Insecure Terraform Sample",
}

FILE_LANGUAGE = {
    "Kubernetes YAML": "yaml",
    "Docker Compose": "yaml",
    "Terraform": "hcl",
}

# ------------------------------------------------------------------ #
# Session state initialisation
# ------------------------------------------------------------------ #
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
if "compliance" not in st.session_state:
    st.session_state.compliance = None
if "file_content" not in st.session_state:
    st.session_state.file_content = ""
if "file_type" not in st.session_state:
    st.session_state.file_type = "Kubernetes YAML"
if "ai_explanations" not in st.session_state:
    st.session_state.ai_explanations = {}


# ------------------------------------------------------------------ #
# Helper: load a sample file safely
# ------------------------------------------------------------------ #
def _load_sample(file_type: str) -> str:
    path = SAMPLE_FILES.get(file_type, "")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except Exception as exc:
        st.error(f"Could not load sample file: {exc}")
        return ""


# ------------------------------------------------------------------ #
# Helper: run the correct auditor
# ------------------------------------------------------------------ #
def _run_audit(content: str, file_type: str) -> list[dict]:
    try:
        if file_type == "Kubernetes YAML":
            return audit_kubernetes(content)
        elif file_type == "Docker Compose":
            return audit_docker_compose(content)
        elif file_type == "Terraform":
            return audit_terraform(content)
    except Exception as exc:
        return [
            {
                "title": "Audit error",
                "severity": "HIGH",
                "detail": str(exc),
                "fix": "Check that the file is valid.",
                "example": "",
                "category": "Error",
                "line_hint": "",
            }
        ]
    return []


# ------------------------------------------------------------------ #
# Sidebar
# ------------------------------------------------------------------ #
with st.sidebar:
    st.title("⚙️ Settings")

    ollama_ok = check_ollama_available()
    if ollama_ok:
        st.success("✅ Ollama connected")
    else:
        st.warning("⚠️ Ollama not running — AI explanations disabled")

    ollama_model = st.text_input("Ollama model", value="llama3.2")

    st.divider()

    st.markdown("**About**")
    st.markdown(
        "Project 10 · AI + DevOps Series  \n"
        "100% Local · No API Costs  \n"
        "Audits K8s · Docker Compose · Terraform"
    )

    st.divider()

    st.markdown(
        "**Severity guide**\n"
        "- 🔴 CRITICAL — Fix immediately\n"
        "- 🟠 HIGH — Fix before next release\n"
        "- 🟡 MEDIUM — Schedule for this sprint\n"
        "- 🟢 LOW — Backlog item"
    )

# ------------------------------------------------------------------ #
# Main header
# ------------------------------------------------------------------ #
st.title("🔍 AI Infrastructure Auditor")
st.markdown(
    "Scan Kubernetes, Docker Compose, and Terraform files for security issues "
    "— powered by local AI"
)

st.divider()

# ------------------------------------------------------------------ #
# File type selector
# ------------------------------------------------------------------ #
file_type = st.radio(
    "Select file type to audit",
    options=["Kubernetes YAML", "Docker Compose", "Terraform"],
    horizontal=True,
    key="file_type_radio",
)
st.session_state.file_type = file_type

# ------------------------------------------------------------------ #
# Input section — two columns
# ------------------------------------------------------------------ #
col_upload, col_sample = st.columns([3, 2])

with col_upload:
    st.markdown("**Upload a file**")
    accepted_types = (
        ["yaml", "yml"] if file_type in ("Kubernetes YAML", "Docker Compose") else ["tf"]
    )
    uploaded = st.file_uploader(
        f"Upload {file_type} file",
        type=accepted_types,
        key=f"uploader_{file_type}",
    )
    if uploaded is not None:
        try:
            st.session_state.file_content = uploaded.read().decode("utf-8", errors="replace")
            # Clear previous audit when a new file is uploaded
            st.session_state.audit_results = None
            st.session_state.compliance = None
            st.session_state.ai_explanations = {}
        except Exception as exc:
            st.error(f"Error reading uploaded file: {exc}")

with col_sample:
    st.markdown("**Or load a sample file**")
    sample_label = SAMPLE_BUTTON_LABELS[file_type]
    if st.button(sample_label, use_container_width=True):
        content = _load_sample(file_type)
        if content:
            st.session_state.file_content = content
            st.session_state.audit_results = None
            st.session_state.compliance = None
            st.session_state.ai_explanations = {}

# ------------------------------------------------------------------ #
# Code preview
# ------------------------------------------------------------------ #
if st.session_state.file_content:
    with st.expander("📄 File preview", expanded=False):
        st.code(
            st.session_state.file_content,
            language=FILE_LANGUAGE.get(file_type, "yaml"),
        )

# ------------------------------------------------------------------ #
# Run Audit button
# ------------------------------------------------------------------ #
st.divider()

if st.button("🚀 Run Audit", use_container_width=True, type="primary"):
    content = st.session_state.file_content

    # Demo mode: auto-load K8s sample if nothing is loaded
    if not content:
        st.info("No file loaded — running Demo Mode with the insecure K8s sample.")
        content = _load_sample("Kubernetes YAML")
        file_type = "Kubernetes YAML"
        st.session_state.file_type = file_type
        st.session_state.file_content = content

    if content:
        with st.spinner("Analysing infrastructure..."):
            findings = _run_audit(content, file_type)
            compliance = calculate_compliance_score(findings)

        st.session_state.audit_results = findings
        st.session_state.compliance = compliance
        st.session_state.ai_explanations = {}

# ------------------------------------------------------------------ #
# Results section
# ------------------------------------------------------------------ #
if st.session_state.audit_results is not None:
    findings: list[dict] = st.session_state.audit_results
    compliance: dict = st.session_state.compliance

    st.divider()
    st.subheader("📊 Audit Results")

    # ---- Summary metrics ------------------------------------------ #
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Total Findings", compliance["total_findings"])

    with m2:
        crit_count = compliance["breakdown"].get("CRITICAL", 0)
        st.metric("Critical", crit_count, delta=None)

    with m3:
        score = compliance["score"]
        score_delta = None
        score_color = "normal"
        if score >= 70:
            score_color = "normal"
        elif score >= 50:
            score_color = "off"
        else:
            score_color = "inverse"
        st.metric("Compliance Score", f"{score}/100")

    with m4:
        grade = compliance["grade"]
        st.metric("Grade", grade)

    # Compliance progress bar
    st.progress(
        compliance["score"] / 100,
        text=f"Compliance: {compliance['score']}/100 — Grade {compliance['grade']}",
    )

    if compliance["passed"]:
        st.success("✅ Compliance check PASSED (score ≥ 70)")
    else:
        st.error("❌ Compliance check FAILED (score < 70)")

    st.divider()

    # ---- Findings by severity ------------------------------------- #
    if not findings:
        st.success("🎉 No issues found! Your infrastructure looks clean.")
    else:
        st.subheader("🔎 Findings by Severity")

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            sev_findings = [f for f in findings if f.get("severity") == severity]
            if not sev_findings:
                continue

            count = len(sev_findings)
            emoji = SEVERITY_EMOJI[severity]
            color = SEVERITY_COLORS[severity]

            with st.expander(
                f"{emoji} {severity} — {count} finding{'s' if count != 1 else ''}",
                expanded=(severity == "CRITICAL"),
            ):
                for i, finding in enumerate(sev_findings):
                    with st.container():
                        st.markdown(
                            f"<span style='color:{color}; font-weight:bold;'>"
                            f"{emoji} {finding['title']}"
                            f"</span>",
                            unsafe_allow_html=True,
                        )

                        # Category badge + line hint
                        badge_cols = st.columns([1, 3])
                        with badge_cols[0]:
                            st.markdown(
                                f"`{finding.get('category', 'General')}`"
                            )
                        with badge_cols[1]:
                            if finding.get("line_hint"):
                                st.caption(f"Location: `{finding['line_hint']}`")

                        # Detail
                        st.markdown(finding.get("detail", ""))

                        # Fix
                        if finding.get("fix"):
                            st.info(f"**Fix:** {finding['fix']}")

                        # Example code
                        if finding.get("example"):
                            st.code(finding["example"], language="yaml")

                        # AI Explanation button
                        btn_key = f"explain_{severity}_{i}_{finding['title'][:20].replace(' ', '_')}"
                        finding_key = finding["title"]

                        if finding_key in st.session_state.ai_explanations:
                            st.success(
                                f"🤖 **AI Explanation:** "
                                f"{st.session_state.ai_explanations[finding_key]}"
                            )
                        else:
                            if st.button("🤖 Explain with AI", key=btn_key):
                                if not ollama_ok:
                                    st.warning(
                                        "Ollama is not available. "
                                        "Start Ollama and reload the page to enable AI explanations."
                                    )
                                else:
                                    with st.spinner("Asking AI..."):
                                        explanation = explain_finding(
                                            finding_title=finding.get("title", ""),
                                            finding_detail=finding.get("detail", ""),
                                            file_type=st.session_state.file_type,
                                            fix=finding.get("fix", ""),
                                            model=ollama_model,
                                        )
                                    if explanation:
                                        st.session_state.ai_explanations[finding_key] = (
                                            explanation
                                        )
                                        st.success(
                                            f"🤖 **AI Explanation:** {explanation}"
                                        )
                                    else:
                                        st.warning(
                                            "AI did not return an explanation. "
                                            "Check that Ollama is running and the model is available."
                                        )

                        st.divider()

    # ---- Top 3 Urgent Fixes --------------------------------------- #
    if compliance["top_3_urgent"]:
        st.subheader("🚨 Top 3 Urgent Fixes")
        for idx, urgent in enumerate(compliance["top_3_urgent"], 1):
            sev = urgent["severity"]
            emoji = SEVERITY_EMOJI.get(sev, "")
            color = SEVERITY_COLORS.get(sev, "#FFFFFF")
            st.markdown(
                f"**{idx}.** {emoji} "
                f"<span style='color:{color};'>[{sev}]</span> "
                f"**{urgent['title']}**  \n"
                f"Fix: _{urgent['fix']}_",
                unsafe_allow_html=True,
            )

    # ---- Raw JSON ------------------------------------------------- #
    st.divider()
    with st.expander("📄 Raw findings (JSON)"):
        st.json(findings)
