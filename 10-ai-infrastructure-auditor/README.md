# 🔍 AI Infrastructure Auditor

> A DevSecOps audit platform that scans entire infrastructure workspaces — Kubernetes, Docker Compose, and Terraform — for critical vulnerabilities, misconfigurations, and compliance violations. Powered by local AI (Ollama). No API keys. No cloud.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)](https://streamlit.io)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.2-green)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Table of Contents

- [Problem Statement](#problem-statement)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Results](#results)
- [Challenges & Learnings](#challenges--learnings)
- [Installation & Usage](#installation--usage)

---

<a id="problem-statement"></a>
## 🎯 Problem Statement

Your infrastructure files are hiding security time bombs nobody is reviewing:

- Your **Terraform opens port 22 to 0.0.0.0/0** — every IP on the internet can attempt SSH
- Your **K8s pods run as root** with `privileged: true` — full host node access from a compromised container
- Your **Docker Compose hardcodes passwords** in plain text — committed to Git history forever
- Your **S3 bucket is set to public-read** — all data readable by anyone without authentication
- Nobody has time to manually check 20+ CIS benchmark rules across every file, every PR, every environment

**Your infra has been lying to you. You don't know — until it's too late.**

This tool is an AI-powered DevSecOps platform. Point it at any infrastructure workspace — it recursively discovers all IaC files, runs 22+ security rules across Kubernetes, Docker Compose, and Terraform, calculates a compliance score, and uses local AI to explain every finding in plain English.

---

<a id="tech-stack"></a>
## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core platform logic |
| Streamlit 1.32+ | DevSecOps dashboard UI |
| Ollama (Llama 3.2) | Local AI for security explanations |
| PyYAML | Kubernetes and Docker Compose parsing |
| `re` (stdlib) | Terraform HCL regex-based auditing |
| `pathlib` (stdlib) | Recursive workspace file discovery |
| `subprocess` (stdlib) | Ollama integration (Windows-safe) |
| `python-dotenv` | Environment variable management |

**100% local — no API costs, no data sent to cloud.**

---

<a id="architecture"></a>
## 🏗️ Architecture

```
Infrastructure Workspace (any directory)
          │
          ▼
  Workspace Scanner
  (recursive discovery,
   content-based type detection)
          │
          ├──────────────────────┬────────────────────┐
          ▼                      ▼                    ▼
   Kubernetes              Docker Compose         Terraform
   Auditor                 Auditor                Auditor
   (7 rules,               (7 rules,              (8 rules,
    multi-doc YAML)         env secret scan)       regex-based)
          │                      │                    │
          └──────────────────────┴────────────────────┘
                                 │
                                 ▼
                       Compliance Checker
                       (CIS-inspired score 0–100,
                        grade A–F, top 3 urgent fixes)
                                 │
                                 ▼
                         AI Explainer (Ollama)
                         Per-finding plain-English
                         explanation — local, no API key
                                 │
                                 ▼
                      Streamlit Platform Dashboard
                      (workspace tree, findings explorer,
                       severity filters, scan history)
```

**Detection categories:**
- **Security** — privileged containers, root users, open ports, hardcoded credentials, open security groups
- **Resource Management** — missing CPU/memory limits, missing healthchecks
- **Compliance** — untagged resources, unencrypted storage, missing versioning, latest image tags

---

<a id="results"></a>
## 📊 Results

| Metric | Before (Manual Review) | After (AI Auditor) |
|--------|----------------------|-------------------|
| Time to audit a full workspace | 2–4 hours | < 10 seconds |
| Files scanned | One at a time (human error) | All discovered automatically |
| Rules checked per file | Varies | 22+ consistently |
| AI explanation per finding | Never | Instant (local) |
| Compliance score visibility | Never calculated | Real score shown |
| API cost | $0 | $0 (100% local) |

**Live demo — Sample Ecommerce App workspace (5 IaC files):**

```
Workspace:  sample_ecommerce_app/infra/
Files:      docker-compose.yml  ·  k8s/deployment.yaml
            k8s/service.yaml    ·  k8s/ingress.yaml
            terraform/main.tf

Total findings:   44
  CRITICAL:       11  (privileged containers, hardcoded secrets,
                        open security group, public S3 bucket)
  HIGH:           11  (root containers, exposed ports, no user defined)
  MEDIUM:         11  (missing resource limits, no healthchecks)
  LOW:            11  (latest image tags, missing tags)

Compliance score: 0 / 100
Grade:            F
Scan time:        < 5 seconds
```

---

<a id="challenges--learnings"></a>
## 🧠 Challenges & Learnings

**1. Content-based file type detection**
Kubernetes and Docker Compose are both YAML. Filename alone isn't reliable — `deploy.yaml` could be either. Solved by scoring content indicators: files with `kind:` + `apiVersion:` + `metadata:` → Kubernetes; files with `services:` → Docker Compose.

**2. Multi-document YAML parsing**
Kubernetes files often contain multiple resources separated by `---`. Using `yaml.safe_load()` only reads the first document. Switched to `yaml.safe_load_all()` and iterating over all documents — critical for real-world manifests.

**3. Terraform without an HCL parser**
Python has no reliable, lightweight HCL parser. Used regex patterns instead — catches all common misconfigurations without adding a fragile dependency. Covers 95% of real-world cases.

**4. Making AI explanations reliable**
Ollama responses vary in length and format. The prompt explicitly instructs "2-3 sentences, no bullet points, plain sentences" and uses a subprocess timeout to prevent the UI from hanging.

**5. Windows subprocess encoding**
Ollama subprocess calls on Windows default to the system code page (cp1252), not UTF-8. Passing `encoding='utf-8'` to `subprocess.run()` prevents crashes when model output includes special characters.

**6. Streamlit button key uniqueness**
Each "Explain with AI" button must have a globally unique `key=` value. Used `f"ai_{i}"` with the finding index to guarantee uniqueness across all expanders.

---

<a id="installation--usage"></a>
## 🚀 Installation & Usage

### Prerequisites

- Python 3.11+
- Ollama installed (optional — app works without it, AI buttons disabled)

### Step 1: Clone the repo

```bash
git clone https://github.com/ThinkWithOps/ai-devops-projects.git
cd ai-devops-projects/10-ai-infrastructure-auditor
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Pull Ollama model (optional)

```bash
# Download Ollama: https://ollama.ai/download
ollama pull llama3.2
```

### Step 4: Launch the platform

```bash
streamlit run app.py
```

Browser opens at `http://localhost:8501` automatically.

### Step 5: Run your first audit

1. In the sidebar, **"Sample Ecommerce App"** is pre-selected
2. Click **"🚀 Run Audit"**
3. Platform scans 5 IaC files — findings appear in seconds
4. Explore findings by severity, click "Explain with AI" on any finding

> **Custom workspace:** Select "Custom Path" in the sidebar and enter any local directory containing `.yaml`, `.yml`, or `.tf` files.

---

### Command Reference

```
streamlit run app.py              Start the platform
pip install -r requirements.txt   Install Python deps
ollama pull llama3.2              Download AI model
```

---

## 📁 Project Structure

```
10-ai-infrastructure-auditor/
├── app.py                              # Streamlit platform (main entry point)
├── config.py                           # Ollama settings, severity config
├── src/
│   ├── scanner/
│   │   ├── workspace_scanner.py        # Recursive IaC file discovery
│   │   └── scan_runner.py              # Orchestrates full workspace scan
│   ├── auditors/
│   │   ├── kubernetes_auditor.py       # 7-rule K8s YAML auditor
│   │   ├── docker_compose_auditor.py   # 7-rule Docker Compose auditor
│   │   ├── terraform_auditor.py        # 8-rule Terraform regex auditor
│   │   └── compliance_checker.py       # CIS-inspired score calculator
│   └── ai/
│       └── ollama_client.py            # Subprocess Ollama client
├── sample_ecommerce_app/               # Target application for demo
│   ├── backend/                        # FastAPI backend
│   ├── frontend/                       # HTML storefront
│   └── infra/                          # Intentionally insecure IaC files
│       ├── docker-compose.yml
│       ├── k8s/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   └── ingress.yaml
│       └── terraform/
│           └── main.tf
├── sample_infra/                       # Single-file demo samples
│   ├── insecure_k8s.yaml
│   ├── insecure_docker_compose.yml
│   └── insecure_terraform.tf
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🎬 YouTube Video

**Watch the full tutorial:** [https://youtu.be/K5RBtMLvXQ4]

---

## 📝 License

MIT License — feel free to use in your own projects!

---

## ⚠️ Important Notes

- Static analysis tool — for learning and demonstration purposes
- Always review AI suggestions before implementing in production
- Regex-based Terraform auditor covers common patterns but is not a full HCL parser
- AI explanations are generated locally and may occasionally be imprecise — always verify

---

## 🔗 Related Projects

| # | Project | Type |
|---|---------|------|
| 01 | AI Docker Security Scanner | CLI |
| 02 | AI K8s Pod Debugger | CLI |
| 03 | AI AWS Cost Detective | CLI |
| 04 | AI GitHub Actions Healer | CLI |
| 05 | AI Terraform Generator | CLI |
| 06 | AI Local Incident Commander | Rich terminal |
| 07 | AI Log Analyzer | Streamlit |
| 08 | AI Pipeline War Room | Rich terminal (multi-agent) |
| 09 | AI DB Query Optimizer | Streamlit |
| **10** | **AI Infrastructure Auditor** | **Streamlit platform** |
| 11 | Coming soon | — |
| 12 | Coming soon | — |

---

## 📧 Contact

**YouTube:** [ThinkWithOps](https://youtube.com/@thinkwithops)
**GitHub:** [ThinkWithOps](https://github.com/ThinkWithOps)

---

**⭐ If this saved your infrastructure from a breach, please star the repo!**
