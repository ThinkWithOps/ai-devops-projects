"""Docker Compose security auditor."""
import yaml
import re


def audit_docker_compose(content: str) -> list[dict]:
    """
    Audit a Docker Compose YAML file for security issues and misconfigurations.

    Returns list of findings. Each finding:
    {
        "title": str,
        "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
        "detail": str,
        "fix": str,
        "example": str,
        "category": str,
        "line_hint": str,
    }
    """
    findings = []

    try:
        data = yaml.safe_load(content)
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

    if not data or "services" not in data:
        return findings

    services = data.get("services", {}) or {}

    secret_patterns = [
        (r"password", "PASSWORD"),
        (r"secret", "SECRET"),
        (r"api_key|apikey", "API KEY"),
        (r"token", "TOKEN"),
        (r"AKIA[0-9A-Z]{16}", "AWS ACCESS KEY"),
    ]

    for svc_name, svc in services.items():
        if not isinstance(svc, dict):
            continue

        # ------------------------------------------------------------------ #
        # CRITICAL: privileged mode
        # ------------------------------------------------------------------ #
        if svc.get("privileged") is True:
            findings.append(
                {
                    "title": f"Privileged container: '{svc_name}'",
                    "severity": "CRITICAL",
                    "detail": f"Service '{svc_name}' runs with privileged: true — full host access.",
                    "fix": "Remove 'privileged: true' from the service definition.",
                    "example": f"{svc_name}:\n  image: ...\n  # no privileged field",
                    "category": "Security",
                    "line_hint": f"services.{svc_name}.privileged",
                }
            )

        # ------------------------------------------------------------------ #
        # CRITICAL: hardcoded secrets in environment
        # ------------------------------------------------------------------ #
        env = svc.get("environment", {})
        if isinstance(env, dict):
            env_items = list(env.items())
        elif isinstance(env, list):
            env_items = []
            for e in env:
                if isinstance(e, str) and "=" in e:
                    k, v = e.split("=", 1)
                    env_items.append((k, v))
                elif isinstance(e, str):
                    env_items.append((e, ""))
        else:
            env_items = []

        for key, val in env_items:
            key_str = str(key).lower()
            val_str = str(val) if val is not None else ""
            for pattern, label in secret_patterns:
                if (
                    re.search(pattern, key_str, re.IGNORECASE)
                    and val_str
                    and not val_str.startswith("${")
                ):
                    findings.append(
                        {
                            "title": f"Hardcoded {label} ({key}): '{svc_name}'",
                            "severity": "CRITICAL",
                            "detail": (
                                f"Service '{svc_name}' has a hardcoded {label} in the "
                                "environment block. This will be committed to Git."
                            ),
                            "fix": "Use Docker secrets or environment variable references: ${MY_SECRET}",
                            "example": f"environment:\n  {key}: ${{MY_{label.replace(' ', '_')}}}",
                            "category": "Security",
                            "line_hint": f"services.{svc_name}.environment.{key}",
                        }
                    )
                    break

        # ------------------------------------------------------------------ #
        # HIGH: running as root (no user field)
        # ------------------------------------------------------------------ #
        if not svc.get("user"):
            findings.append(
                {
                    "title": f"No non-root user defined: '{svc_name}'",
                    "severity": "HIGH",
                    "detail": (
                        f"Service '{svc_name}' does not specify a non-root user. "
                        "Container likely runs as root by default."
                    ),
                    "fix": "Add 'user: \"1000:1000\"' to the service definition.",
                    "example": f"{svc_name}:\n  user: \"1000:1000\"",
                    "category": "Security",
                    "line_hint": f"services.{svc_name}.user",
                }
            )

        # ------------------------------------------------------------------ #
        # HIGH: ports bound to 0.0.0.0
        # ------------------------------------------------------------------ #
        ports = svc.get("ports", []) or []
        for port in ports:
            port_str = str(port)
            if port_str.startswith("0.0.0.0"):
                findings.append(
                    {
                        "title": f"Port bound to 0.0.0.0: '{svc_name}'",
                        "severity": "HIGH",
                        "detail": (
                            f"Service '{svc_name}' binds port {port_str} to all interfaces. "
                            "Exposed to entire network."
                        ),
                        "fix": "Bind to 127.0.0.1 for internal services: '127.0.0.1:8080:8080'",
                        "example": "ports:\n  - '127.0.0.1:8080:8080'",
                        "category": "Security",
                        "line_hint": f"services.{svc_name}.ports",
                    }
                )

        # ------------------------------------------------------------------ #
        # MEDIUM: no resource limits
        # ------------------------------------------------------------------ #
        deploy = svc.get("deploy", {}) or {}
        resources = deploy.get("resources", {}) or {}
        if not resources.get("limits"):
            findings.append(
                {
                    "title": f"No resource limits: '{svc_name}'",
                    "severity": "MEDIUM",
                    "detail": (
                        f"Service '{svc_name}' has no CPU/memory limits under "
                        "deploy.resources.limits."
                    ),
                    "fix": "Add deploy.resources.limits with cpus and memory.",
                    "example": (
                        "deploy:\n"
                        "  resources:\n"
                        "    limits:\n"
                        "      cpus: '0.5'\n"
                        "      memory: 256M"
                    ),
                    "category": "Resource Management",
                    "line_hint": f"services.{svc_name}.deploy.resources",
                }
            )

        # ------------------------------------------------------------------ #
        # LOW: no healthcheck
        # ------------------------------------------------------------------ #
        if not svc.get("healthcheck"):
            findings.append(
                {
                    "title": f"No healthcheck defined: '{svc_name}'",
                    "severity": "LOW",
                    "detail": (
                        f"Service '{svc_name}' has no healthcheck. "
                        "Docker cannot detect if the app inside is actually healthy."
                    ),
                    "fix": "Add a healthcheck with test, interval, timeout, and retries.",
                    "example": (
                        "healthcheck:\n"
                        "  test: ['CMD', 'curl', '-f', 'http://localhost:8080/health']\n"
                        "  interval: 30s\n"
                        "  timeout: 10s\n"
                        "  retries: 3"
                    ),
                    "category": "Compliance",
                    "line_hint": f"services.{svc_name}.healthcheck",
                }
            )

        # ------------------------------------------------------------------ #
        # LOW: image uses latest tag or no tag
        # ------------------------------------------------------------------ #
        image = svc.get("image", "")
        if image and (image.endswith(":latest") or ":" not in image):
            findings.append(
                {
                    "title": f"Image uses ':latest' tag: '{svc_name}'",
                    "severity": "LOW",
                    "detail": (
                        f"Service '{svc_name}' uses image '{image}'. "
                        "Unpinned images cause unpredictable deployments."
                    ),
                    "fix": "Pin to a specific version tag.",
                    "example": f"image: {image.split(':')[0]}:1.21",
                    "category": "Compliance",
                    "line_hint": f"services.{svc_name}.image",
                }
            )

    return findings
