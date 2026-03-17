# ShopAI — Sample Ecommerce App

This is a sample ecommerce application used as the audit target for the
**AI Infrastructure Auditor** (Project 10 of the AI + DevOps Portfolio Series).

**Do not use in production — intentionally insecure for demo purposes.**

## Structure

- `backend/` — FastAPI application with two endpoints (`/products`, `/health`)
- `frontend/` — Static HTML page that fetches and displays products
- `infra/docker-compose.yml` — Docker Compose with hardcoded secrets, privileged containers, and unpinned images
- `infra/k8s/` — Kubernetes manifests with root containers, hostNetwork, and no resource limits
- `infra/terraform/` — AWS Terraform with public S3 bucket, open security groups, and unencrypted RDS

## Known Issues (Intentional)

- Hardcoded passwords and API keys in Docker Compose and Kubernetes manifests
- Privileged containers in both Docker Compose and Kubernetes
- `nginx:latest`, `python:latest`, `postgres:latest`, `redis:latest` — all unpinned
- No resource limits on any container
- No healthchecks defined
- S3 bucket set to `public-read`
- RDS with `storage_encrypted = false` and `deletion_protection = false`
- SSH port 22 open to `0.0.0.0/0` in the security group
