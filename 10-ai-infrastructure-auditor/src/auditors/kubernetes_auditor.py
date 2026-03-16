"""Kubernetes manifest security auditor."""
import yaml


def audit_kubernetes(content: str) -> list[dict]:
    """
    Audit a Kubernetes YAML manifest for security issues and misconfigurations.

    Returns list of findings. Each finding:
    {
        "title": str,
        "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
        "detail": str,
        "fix": str,
        "example": str,   # secure version snippet
        "category": str,  # "Security" | "Resource Management" | "Compliance"
        "line_hint": str, # where to look in the file
    }
    """
    findings = []

    try:
        docs = list(yaml.safe_load_all(content))
    except yaml.YAMLError as e:
        return [
            {
                "title": "Invalid YAML",
                "severity": "HIGH",
                "detail": str(e),
                "fix": "Fix YAML syntax",
                "example": "",
                "category": "Parsing",
                "line_hint": "",
            }
        ]

    for doc in docs:
        if not doc or not isinstance(doc, dict):
            continue
        kind = doc.get("kind", "")

        # ------------------------------------------------------------------ #
        # Collect containers from supported workload types
        # ------------------------------------------------------------------ #
        containers = []
        spec = doc.get("spec", {}) or {}

        if kind == "Pod":
            containers = spec.get("containers", []) or []
        elif kind in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"):
            template_spec = (spec.get("template", {}) or {}).get("spec", {}) or {}
            containers = (template_spec.get("containers", []) or []) + (
                template_spec.get("initContainers", []) or []
            )

        for c in containers:
            if not isinstance(c, dict):
                continue
            name = c.get("name", "unknown")
            sc = c.get("securityContext", {}) or {}

            # CRITICAL: privileged container
            if sc.get("privileged") is True:
                findings.append(
                    {
                        "title": f"Privileged container: '{name}'",
                        "severity": "CRITICAL",
                        "detail": (
                            f"Container '{name}' runs with privileged: true — "
                            "full host access, equivalent to root on the node."
                        ),
                        "fix": "Set privileged: false or remove the securityContext.privileged field entirely.",
                        "example": "securityContext:\n  privileged: false\n  runAsNonRoot: true",
                        "category": "Security",
                        "line_hint": f"containers[name={name}].securityContext.privileged",
                    }
                )

            # CRITICAL: running as root (UID 0)
            if sc.get("runAsUser") == 0:
                findings.append(
                    {
                        "title": f"Container runs as root (UID 0): '{name}'",
                        "severity": "CRITICAL",
                        "detail": (
                            f"Container '{name}' explicitly sets runAsUser: 0. "
                            "Root in container = root on host if container escapes."
                        ),
                        "fix": "Set runAsUser to a non-zero UID (e.g. 1000) and runAsNonRoot: true.",
                        "example": "securityContext:\n  runAsUser: 1000\n  runAsNonRoot: true",
                        "category": "Security",
                        "line_hint": f"containers[name={name}].securityContext.runAsUser",
                    }
                )

            # HIGH: no runAsNonRoot
            if not sc.get("runAsNonRoot") and sc.get("runAsUser", 1) != 0:
                findings.append(
                    {
                        "title": f"runAsNonRoot not enforced: '{name}'",
                        "severity": "HIGH",
                        "detail": (
                            f"Container '{name}' does not set runAsNonRoot: true. "
                            "Container may start as root if image default is root."
                        ),
                        "fix": "Add runAsNonRoot: true to securityContext.",
                        "example": "securityContext:\n  runAsNonRoot: true\n  runAsUser: 1000",
                        "category": "Security",
                        "line_hint": f"containers[name={name}].securityContext",
                    }
                )

            # HIGH: allowPrivilegeEscalation not disabled
            if sc.get("allowPrivilegeEscalation", True) is True:
                findings.append(
                    {
                        "title": f"Privilege escalation allowed: '{name}'",
                        "severity": "HIGH",
                        "detail": (
                            f"Container '{name}' allows privilege escalation (default). "
                            "Attackers can use setuid binaries to gain root."
                        ),
                        "fix": "Set allowPrivilegeEscalation: false.",
                        "example": "securityContext:\n  allowPrivilegeEscalation: false",
                        "category": "Security",
                        "line_hint": f"containers[name={name}].securityContext.allowPrivilegeEscalation",
                    }
                )

            # MEDIUM: no resource limits
            resources = c.get("resources", {}) or {}
            if not resources.get("limits"):
                findings.append(
                    {
                        "title": f"No resource limits: '{name}'",
                        "severity": "MEDIUM",
                        "detail": (
                            f"Container '{name}' has no CPU/memory limits. "
                            "A runaway process can consume all node resources."
                        ),
                        "fix": "Add resources.limits with cpu and memory values.",
                        "example": (
                            "resources:\n"
                            "  limits:\n"
                            "    cpu: '500m'\n"
                            "    memory: '256Mi'\n"
                            "  requests:\n"
                            "    cpu: '100m'\n"
                            "    memory: '128Mi'"
                        ),
                        "category": "Resource Management",
                        "line_hint": f"containers[name={name}].resources",
                    }
                )

            # MEDIUM: no readOnlyRootFilesystem
            if not sc.get("readOnlyRootFilesystem"):
                findings.append(
                    {
                        "title": f"Writable root filesystem: '{name}'",
                        "severity": "MEDIUM",
                        "detail": (
                            f"Container '{name}' has a writable root filesystem. "
                            "Attackers can modify binaries or write malicious scripts."
                        ),
                        "fix": "Set readOnlyRootFilesystem: true and use emptyDir volumes for writable paths.",
                        "example": "securityContext:\n  readOnlyRootFilesystem: true",
                        "category": "Security",
                        "line_hint": f"containers[name={name}].securityContext.readOnlyRootFilesystem",
                    }
                )

            # LOW: image uses latest tag or no tag
            image = c.get("image", "")
            if image and (image.endswith(":latest") or ":" not in image):
                findings.append(
                    {
                        "title": f"Image uses ':latest' tag: '{name}'",
                        "severity": "LOW",
                        "detail": (
                            f"Container '{name}' uses image '{image}'. "
                            "'latest' tag is mutable — you may deploy unexpected versions."
                        ),
                        "fix": "Pin to a specific immutable image digest or version tag.",
                        "example": f"image: {image.split(':')[0]}:1.21.6",
                        "category": "Compliance",
                        "line_hint": f"containers[name={name}].image",
                    }
                )

        # ------------------------------------------------------------------ #
        # Namespace-level: missing NetworkPolicy hint
        # ------------------------------------------------------------------ #
        if kind == "Namespace":
            findings.append(
                {
                    "title": "Namespace has no NetworkPolicy",
                    "severity": "MEDIUM",
                    "detail": (
                        "No NetworkPolicy detected for this namespace. "
                        "All pods can communicate with each other by default."
                    ),
                    "fix": "Add a default-deny NetworkPolicy and allowlist required traffic.",
                    "example": (
                        "kind: NetworkPolicy\n"
                        "spec:\n"
                        "  podSelector: {}\n"
                        "  policyTypes: [Ingress, Egress]"
                    ),
                    "category": "Security",
                    "line_hint": "namespace definition",
                }
            )

        # ------------------------------------------------------------------ #
        # CRITICAL: hostNetwork
        # ------------------------------------------------------------------ #
        pod_spec: dict = {}
        if kind == "Pod":
            pod_spec = spec
        elif kind in ("Deployment", "StatefulSet", "DaemonSet"):
            pod_spec = (spec.get("template", {}) or {}).get("spec", {}) or {}

        if pod_spec.get("hostNetwork") is True:
            findings.append(
                {
                    "title": "hostNetwork: true — pod shares host network namespace",
                    "severity": "CRITICAL",
                    "detail": "Pod uses the host's network stack directly. Can sniff all host network traffic.",
                    "fix": "Remove hostNetwork: true unless absolutely required (e.g., CNI plugins).",
                    "example": "# Remove hostNetwork from spec entirely",
                    "category": "Security",
                    "line_hint": "spec.hostNetwork",
                }
            )

    return findings
