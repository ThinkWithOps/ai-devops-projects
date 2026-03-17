"""
Workspace scanner — recursively discovers and routes IaC files to correct auditor.
"""
import os
import pathlib
from typing import Generator

KUBERNETES_INDICATORS = ["kind:", "apiVersion:", "metadata:"]
DOCKER_COMPOSE_INDICATORS = ["services:", "version:"]


def detect_file_type(content: str, filename: str) -> str | None:
    """Detect IaC file type from content and filename."""
    filename_lower = filename.lower()

    # Terraform
    if filename_lower.endswith(".tf"):
        return "terraform"

    # Docker Compose by filename
    if "docker-compose" in filename_lower or "compose" in filename_lower:
        return "docker_compose"

    # YAML files — detect by content
    if filename_lower.endswith((".yaml", ".yml")):
        # Check for Kubernetes indicators
        k8s_score = sum(1 for ind in KUBERNETES_INDICATORS if ind in content)
        compose_score = sum(1 for ind in DOCKER_COMPOSE_INDICATORS if ind in content)

        if k8s_score >= 2:
            return "kubernetes"
        if compose_score >= 1:
            return "docker_compose"
        if k8s_score >= 1:
            return "kubernetes"

    return None


def scan_workspace(workspace_path: str) -> list[dict]:
    """
    Recursively scan a workspace directory for IaC files.
    Returns list of: {path, filename, relative_path, file_type, content}
    """
    results = []
    workspace = pathlib.Path(workspace_path)

    if not workspace.exists():
        return results

    # Walk all files
    for file_path in workspace.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip hidden dirs, node_modules, __pycache__, .git
        skip_dirs = {".git", "node_modules", "__pycache__", ".terraform", "venv", ".venv"}
        if any(part in skip_dirs for part in file_path.parts):
            continue

        suffix = file_path.suffix.lower()
        if suffix not in (".yaml", ".yml", ".tf"):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        file_type = detect_file_type(content, file_path.name)
        if not file_type:
            continue

        try:
            relative_path = str(file_path.relative_to(workspace))
        except ValueError:
            relative_path = str(file_path)

        results.append({
            "path": str(file_path),
            "filename": file_path.name,
            "relative_path": relative_path.replace("\\", "/"),
            "file_type": file_type,
            "content": content,
        })

    return results


def build_file_tree(files: list[dict]) -> dict:
    """Build nested dict representing file tree for sidebar display."""
    tree = {}
    for f in files:
        parts = f["relative_path"].split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = f["file_type"]
    return tree
