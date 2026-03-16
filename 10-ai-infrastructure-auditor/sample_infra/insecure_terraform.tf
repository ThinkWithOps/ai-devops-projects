# ============================================================
# INTENTIONALLY INSECURE Terraform Configuration
# FOR DEMO / EDUCATION PURPOSES ONLY
# Each issue is commented to explain why it is dangerous.
# ============================================================

# ISSUE: Hardcoded region — not using var.region
# Hardcoding the region makes this module impossible to reuse across
# environments (dev/staging/prod) without editing the source.
# Use variable "region" { default = "us-east-1" } instead.
provider "aws" {
  region = "us-east-1"

  # ISSUE: (if credentials were here) Never hardcode access keys.
  # The AKIA pattern below is a fake key for demo — the auditor
  # detects it regardless of whether it is real.
  # access_key = "AKIAIOSFODNN7EXAMPLE"
  # secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

# ============================================================
# VPC Security Group
# ============================================================

resource "aws_security_group" "web_sg" {
  name        = "web-security-group"
  description = "Security group for web servers"
  vpc_id      = "vpc-12345678"

  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"

    # ISSUE: 0.0.0.0/0 ingress on SSH
    # This opens SSH (port 22) to the ENTIRE internet.
    # Automated bots scan for open port 22 within minutes of an
    # instance launching. Brute-force attacks begin immediately.
    # Restrict to your office IP or use a bastion host / VPN.
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ISSUE: No tags
  # Untagged resources make cost attribution and compliance auditing
  # impossible. You cannot tell who owns this, what project it is for,
  # or which environment it belongs to.
}

# ============================================================
# S3 Bucket
# ============================================================

resource "aws_s3_bucket" "data_bucket" {
  bucket = "my-company-data-bucket"

  # ISSUE: Public read ACL
  # Setting acl = "public-read" makes EVERY OBJECT in this bucket
  # readable by anyone on the internet without authentication.
  # Data breaches from misconfigured S3 buckets are the #1 cloud
  # security incident type. Always use "private" and bucket policies.
  acl = "public-read"

  # ISSUE: No versioning block
  # Without versioning, there is no recovery from accidental deletes
  # or ransomware that overwrites objects. One s3 rm command and
  # your data is gone permanently.
  #
  # versioning {         <-- intentionally omitted
  #   enabled = true
  # }

  # ISSUE: No tags
  # (same problem as security group above)
}

# ============================================================
# RDS Database Instance
# ============================================================

resource "aws_db_instance" "app_db" {
  identifier        = "app-database"
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  db_name  = "appdb"
  username = "admin"
  password = "insecure-password-123"

  # ISSUE: storage_encrypted = false
  # Database data at rest is stored in plaintext on the EBS volume.
  # Violates SOC2, PCI-DSS, HIPAA, and most enterprise security policies.
  # Enabling encryption requires recreating the instance — there is no
  # in-place upgrade. Fix this before creating the instance, not after.
  storage_encrypted = false

  # ISSUE: deletion_protection = false (default)
  # Without deletion protection, a single `terraform destroy` or
  # a misconfigured pipeline can permanently destroy the production
  # database with all its data. Always enable this in production.
  deletion_protection = false

  skip_final_snapshot = true

  # ISSUE: No tags
  # (same problem as above — impossible to identify this instance
  # in the AWS console or billing reports without tags)
}
