# =============================================================================
# Sample Ecommerce App — Terraform AWS Infrastructure
# INTENTIONALLY INSECURE — for audit demo purposes only
# DO NOT use in production
# =============================================================================

# ISSUE: LOW — region is hardcoded, not a variable; makes module non-reusable
provider "aws" {
  region = "us-east-1"
}

# =============================================================================
# Security Group
# ISSUE: CRITICAL — SSH (22) and HTTP (80) open to 0.0.0.0/0 (entire internet)
# =============================================================================
resource "aws_security_group" "shopai_sg" {
  name        = "shopai-security-group"
  description = "Security group for ShopAI ecommerce app"
  # ISSUE: no tags on this resource

  # ISSUE: CRITICAL — SSH open to the entire internet
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # ISSUE: should be restricted to known IPs
  }

  # ISSUE: CRITICAL — HTTP open to the entire internet (acceptable for public web,
  # but combined with no WAF and other issues, this is flagged)
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
}

# =============================================================================
# S3 Bucket — Static Assets
# ISSUE: CRITICAL — acl = "public-read" exposes all objects to the internet
# ISSUE: HIGH — no versioning enabled
# ISSUE: MEDIUM — no MFA delete
# =============================================================================
resource "aws_s3_bucket" "assets" {
  bucket = "shopify-clone-assets"
  acl    = "public-read"   # ISSUE: CRITICAL — all files in this bucket are publicly readable

  # ISSUE: HIGH — no versioning block; accidental deletes are permanent
  # versioning {
  #   enabled = true
  # }

  # ISSUE: no tags on this resource
}

# =============================================================================
# RDS PostgreSQL Database
# ISSUE: HIGH — storage_encrypted = false; data at rest is unencrypted
# ISSUE: HIGH — deletion_protection = false; one terraform destroy loses everything
# =============================================================================
resource "aws_db_instance" "shopdb" {
  identifier           = "shopai-postgres"
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  db_name              = "shopdb"
  username             = "shopuser"
  password             = "ShopAdmin2024!"     # ISSUE: CRITICAL — hardcoded password
  storage_encrypted    = false                 # ISSUE: HIGH — encryption disabled
  deletion_protection  = false                 # ISSUE: HIGH — no deletion protection
  skip_final_snapshot  = true
  publicly_accessible  = true                  # ISSUE: HIGH — DB directly internet-accessible

  # ISSUE: no tags on this resource
}

# =============================================================================
# EC2 Instance — Application Server
# ISSUE: no tags; no IAM role; default VPC
# =============================================================================
resource "aws_instance" "app_server" {
  ami                    = "ami-0c02fb55956c7d316"   # Amazon Linux 2
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.shopai_sg.id]

  # ISSUE: LOW — no tags; impossible to identify cost/owner/environment
  # tags = {
  #   Name        = "shopai-app-server"
  #   Environment = "production"
  #   Owner       = "platform-team"
  # }
}
