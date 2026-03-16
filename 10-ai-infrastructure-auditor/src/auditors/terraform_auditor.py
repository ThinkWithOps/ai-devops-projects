"""Terraform security auditor — regex-based, no HCL parser required."""
import re


def audit_terraform(content: str) -> list[dict]:
    """
    Audit a Terraform HCL file for security issues and misconfigurations.
    Uses regex matching — no HCL parser dependency needed.

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

    # ------------------------------------------------------------------ #
    # CRITICAL: open security group — 0.0.0.0/0 ingress
    # ------------------------------------------------------------------ #
    if re.search(r'cidr_blocks\s*=\s*\[?\s*"0\.0\.0\.0/0"', content):
        findings.append(
            {
                "title": "Open security group — 0.0.0.0/0 ingress allowed",
                "severity": "CRITICAL",
                "detail": (
                    "Security group allows inbound traffic from ANY IP (0.0.0.0/0). "
                    "Your instances are exposed to the entire internet."
                ),
                "fix": "Restrict cidr_blocks to known IP ranges. Never use 0.0.0.0/0 for sensitive ports.",
                "example": 'cidr_blocks = ["10.0.0.0/8"]  # internal only',
                "category": "Security",
                "line_hint": "aws_security_group ingress cidr_blocks",
            }
        )

    # ------------------------------------------------------------------ #
    # CRITICAL: public S3 bucket (ACL public-read or public-read-write)
    # ------------------------------------------------------------------ #
    if re.search(r'acl\s*=\s*"public-read', content):
        findings.append(
            {
                "title": "S3 bucket publicly readable",
                "severity": "CRITICAL",
                "detail": (
                    "S3 bucket ACL is set to public-read or public-read-write. "
                    "All data in this bucket is readable by anyone on the internet."
                ),
                "fix": 'Set acl = "private" and use bucket policies for controlled access.',
                "example": 'acl = "private"',
                "category": "Security",
                "line_hint": "aws_s3_bucket acl",
            }
        )

    # ------------------------------------------------------------------ #
    # CRITICAL: hardcoded AWS credentials
    # ------------------------------------------------------------------ #
    if re.search(r"AKIA[0-9A-Z]{16}", content):
        findings.append(
            {
                "title": "Hardcoded AWS Access Key ID detected",
                "severity": "CRITICAL",
                "detail": (
                    "An AWS Access Key ID (AKIA...) is hardcoded in the Terraform file. "
                    "This will be committed to version control and can lead to account compromise."
                ),
                "fix": (
                    "Use environment variables (AWS_ACCESS_KEY_ID) or IAM roles. "
                    "Never hardcode credentials."
                ),
                "example": (
                    '# Use AWS provider without credentials — rely on IAM role or env vars\n'
                    'provider "aws" {\n'
                    "  region = var.region\n"
                    "}"
                ),
                "category": "Security",
                "line_hint": "provider or resource block with access_key",
            }
        )

    # ------------------------------------------------------------------ #
    # HIGH: encryption disabled on RDS
    # ------------------------------------------------------------------ #
    if re.search(r"aws_db_instance", content) and re.search(
        r"storage_encrypted\s*=\s*false", content
    ):
        findings.append(
            {
                "title": "RDS storage encryption disabled",
                "severity": "HIGH",
                "detail": (
                    "RDS instance has storage_encrypted = false. "
                    "Database data at rest is unencrypted. "
                    "Violates most compliance frameworks (SOC2, PCI, HIPAA)."
                ),
                "fix": "Set storage_encrypted = true. Note: requires re-creating existing instances.",
                "example": "storage_encrypted = true",
                "category": "Compliance",
                "line_hint": "aws_db_instance.storage_encrypted",
            }
        )

    # ------------------------------------------------------------------ #
    # HIGH: S3 versioning disabled / not present
    # ------------------------------------------------------------------ #
    if re.search(r"aws_s3_bucket", content) and not re.search(
        r"versioning\s*\{[^}]*enabled\s*=\s*true", content, re.DOTALL
    ):
        findings.append(
            {
                "title": "S3 bucket versioning not enabled",
                "severity": "HIGH",
                "detail": (
                    "S3 bucket does not have versioning enabled. "
                    "Accidental deletions or overwrites cannot be recovered."
                ),
                "fix": "Add a versioning block with enabled = true.",
                "example": "versioning {\n  enabled = true\n}",
                "category": "Compliance",
                "line_hint": "aws_s3_bucket versioning block",
            }
        )

    # ------------------------------------------------------------------ #
    # HIGH: no deletion protection on RDS
    # ------------------------------------------------------------------ #
    if re.search(r"aws_db_instance", content) and not re.search(
        r"deletion_protection\s*=\s*true", content
    ):
        findings.append(
            {
                "title": "RDS deletion protection disabled",
                "severity": "HIGH",
                "detail": (
                    "RDS instance has no deletion protection. "
                    "A terraform destroy or accidental delete will permanently remove the database."
                ),
                "fix": "Set deletion_protection = true.",
                "example": "deletion_protection = true",
                "category": "Compliance",
                "line_hint": "aws_db_instance.deletion_protection",
            }
        )

    # ------------------------------------------------------------------ #
    # MEDIUM: no MFA delete on S3
    # ------------------------------------------------------------------ #
    if re.search(r"aws_s3_bucket", content) and not re.search(
        r'mfa_delete\s*=\s*"Enabled"', content
    ):
        findings.append(
            {
                "title": "S3 MFA delete not enabled",
                "severity": "MEDIUM",
                "detail": (
                    "MFA delete is not enabled on S3 bucket. "
                    "Objects can be permanently deleted without MFA confirmation."
                ),
                "fix": "Enable MFA delete on the versioning block (requires root account and MFA device).",
                "example": 'versioning {\n  enabled    = true\n  mfa_delete = "Enabled"\n}',
                "category": "Compliance",
                "line_hint": "aws_s3_bucket versioning.mfa_delete",
            }
        )

    # ------------------------------------------------------------------ #
    # LOW: hardcoded AWS region (not using var.region)
    # ------------------------------------------------------------------ #
    if re.search(r'region\s*=\s*"[a-z]+-[a-z]+-[0-9]"', content) and not re.search(
        r"var\.region", content
    ):
        findings.append(
            {
                "title": "Hardcoded AWS region",
                "severity": "LOW",
                "detail": (
                    "AWS region is hardcoded instead of using a variable. "
                    "Makes the Terraform module non-reusable across environments."
                ),
                "fix": "Use var.region and define it as a variable.",
                "example": (
                    'variable "region" {\n'
                    '  default = "us-east-1"\n'
                    "}\n"
                    'provider "aws" {\n'
                    "  region = var.region\n"
                    "}"
                ),
                "category": "Compliance",
                "line_hint": "provider.aws.region",
            }
        )

    # ------------------------------------------------------------------ #
    # LOW: no tags on resources
    # ------------------------------------------------------------------ #
    if not re.search(r"tags\s*=\s*\{", content):
        findings.append(
            {
                "title": "Resources have no tags",
                "severity": "LOW",
                "detail": (
                    "No resource tags found. Untagged resources make cost allocation, "
                    "ownership, and compliance reporting impossible."
                ),
                "fix": "Add standard tags: Name, Environment, Owner, Project to all resources.",
                "example": (
                    'tags = {\n'
                    '  Name        = "my-resource"\n'
                    '  Environment = "production"\n'
                    '  Owner       = "team-name"\n'
                    "}"
                ),
                "category": "Compliance",
                "line_hint": "all resource blocks",
            }
        )

    return findings
