"""
Orchestrates a full workspace scan — discovers files, runs all auditors, returns combined results.
"""
import json
import os
import pathlib
from datetime import datetime

from .workspace_scanner import scan_workspace, build_file_tree
from ..auditors.kubernetes_auditor import audit_kubernetes
from ..auditors.docker_compose_auditor import audit_docker_compose
from ..auditors.terraform_auditor import audit_terraform
from ..auditors.compliance_checker import calculate_compliance_score

AUDITOR_MAP = {
    "kubernetes": audit_kubernetes,
    "docker_compose": audit_docker_compose,
    "terraform": audit_terraform,
}

FILE_TYPE_LABELS = {
    "kubernetes": "Kubernetes",
    "docker_compose": "Docker Compose",
    "terraform": "Terraform",
}


def run_workspace_scan(workspace_path: str) -> dict:
    """
    Full workspace scan. Returns:
    {
        workspace: str,
        scanned_at: str,
        files_scanned: list[{filename, relative_path, file_type}],
        all_findings: list[{...finding, source_file, source_type, source_label}],
        compliance: dict,
        file_tree: dict,
        files_by_type: {kubernetes: int, docker_compose: int, terraform: int},
    }
    """
    discovered = scan_workspace(workspace_path)

    all_findings = []
    files_scanned = []

    for file_info in discovered:
        auditor = AUDITOR_MAP.get(file_info["file_type"])
        if not auditor:
            continue

        findings = auditor(file_info["content"])

        # Tag each finding with source info
        for f in findings:
            f["source_file"] = file_info["relative_path"]
            f["source_filename"] = file_info["filename"]
            f["source_type"] = file_info["file_type"]
            f["source_label"] = FILE_TYPE_LABELS.get(file_info["file_type"], file_info["file_type"])

        all_findings.extend(findings)
        files_scanned.append({
            "filename": file_info["filename"],
            "relative_path": file_info["relative_path"],
            "file_type": file_info["file_type"],
            "findings_count": len(findings),
        })

    compliance = calculate_compliance_score(all_findings)

    files_by_type = {}
    for f in discovered:
        files_by_type[f["file_type"]] = files_by_type.get(f["file_type"], 0) + 1

    return {
        "workspace": workspace_path,
        "scanned_at": datetime.now().isoformat(),
        "files_scanned": files_scanned,
        "all_findings": all_findings,
        "compliance": compliance,
        "file_tree": build_file_tree(discovered),
        "files_by_type": files_by_type,
    }


def save_scan_history(result: dict, history_file: str = "scan_history.json") -> None:
    """Append scan summary to local JSON history file."""
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    summary = {
        "scanned_at": result["scanned_at"],
        "workspace": result["workspace"],
        "total_findings": result["compliance"]["total_findings"],
        "critical": result["compliance"]["breakdown"].get("CRITICAL", 0),
        "high": result["compliance"]["breakdown"].get("HIGH", 0),
        "score": result["compliance"]["score"],
        "grade": result["compliance"]["grade"],
        "files_scanned": len(result["files_scanned"]),
    }
    history.insert(0, summary)
    history = history[:10]  # keep last 10

    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass


def load_scan_history(history_file: str = "scan_history.json") -> list:
    if not os.path.exists(history_file):
        return []
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
