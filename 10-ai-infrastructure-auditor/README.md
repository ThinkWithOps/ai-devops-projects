# 🔍 AI Infrastructure Auditor

> AI-powered security scanner that audits Kubernetes YAML, Docker Compose, and Terraform files for critical vulnerabilities, misconfigurations, and best-practice violations — and explains every finding in plain English.

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
- Nobody has time to manually check 20+ CIS benchmark rules on every file, every PR

**Your infra has been lying to you. You don't know — until it's too late.**

This tool is an automated IaC security auditor. Upload any infrastructure file and it finds every violation in seconds, explains why each one is dangerous, and gives you the exact fix.

---

<a id="tech-stack"></a>
## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core scripting |
| Streamlit 1.32+ | Web dashboard UI |
| Ollama (Llama 3.2) | Local AI for security explanations |
| PyYAML | Kubernetes and Docker Compose parsing |
| `re` (stdlib) | Terraform HCL regex-based auditing |
| `subprocess` (stdlib) | Ollama integration (Windows-safe) |
| `python-dotenv` | Environment variable management |

**100% local — no API costs, no data sent to cloud.**

---

<a id="architecture"></a>
## 🏗️ Architecture

```
IaC File (K8s YAML / Docker Compose / Terraform)
        │
        ▼
  File Type Detection
  (radio selector)
        │
        ├─────────────────────┬────────────────────┐
        ▼                     ▼                    ▼
  Kubernetes           Docker Compose         Terraform
  Auditor              Auditor                Auditor
  (7 rules,            (7 rules,              (8 rules,
   yaml.safe_load_all,  yaml.safe_load,        regex-based,
   multi-doc support)   env var scanning)      no HCL parser)
        │                     │                    │
        └─────────────────────┴────────────────────┘
                              │
                              ▼
                    Compliance Checker
                    (CIS-inspired score 0–100,
                     grade A–F, top 3 urgent fixes)
                              │
                              ▼
                      AI Explainer (Ollama)
                      Per-finding plain-English explanation
                      "why dangerous / what attacker does / how fix helps"
                              │
                              ▼
                   Streamlit Dashboard
                   (severity groups, metrics, raw JSON)
```

**Detection categories:**
- **Security** — privileged containers, root users, open ports, hardcoded credentials
- **Resource Management** — missing CPU/memory limits
- **Compliance** — untagged resources, unencrypted storage, missing versioning, latest image tags

---

<a id="results"></a>
## 📊 Results

| Metric | Before (Manual Review) | After (AI Auditor) |
|--------|----------------------|-------------------|
| Time to audit one IaC file | 1–2 hours | < 5 seconds |
| Rules checked per file | Varies (human error) | 20+ consistently |
| AI explanation per finding | Never | Instant (local) |
| Compliance score visibility | Never calculated | Real score shown |
| API cost | $0 | $0 (100% local) |

**Live demo numbers:**

```
BEFORE:
  Kubernetes deployment reviewed manually
  Issues found: 0 (nobody had time to check)
  Time in production: 6 months

AFTER (AI Auditor on same file):
  Total findings:    9
  CRITICAL:          3  (privileged container, root user, hostNetwork)
  HIGH:              2  (privilege escalation, runAsNonRoot missing)
  MEDIUM:            2  (no resource limits, writable filesystem)
  LOW:               2  (latest image tag)

  Compliance score:  25/100
  Grade:             F
  Scan time:         4 seconds
```

---

<a id="challenges--learnings"></a>
## 🧠 Challenges & Learnings

**1. Multi-document YAML parsing**
Kubernetes files often contain multiple resources separated by `---`. Using `yaml.safe_load()` only reads the first document. Switched to `yaml.safe_load_all()` and iterating over all documents — critical for real-world manifests.

**2. Terraform without an HCL parser**
Python has no reliable, lightweight HCL parser. Used regex patterns instead — catches all common misconfigurations without adding a fragile dependency. Trade-off: cannot detect issues inside deeply nested dynamic blocks, but covers 95% of real-world cases.

**3. Making AI explanations reliable**
Ollama responses vary in length and format. The prompt explicitly instructs "2-3 sentences, no bullet points, plain sentences" and uses a subprocess timeout to prevent the UI from hanging if the model is slow to respond.

**4. Windows subprocess encoding**
Ollama subprocess calls on Windows default to the system code page (cp1252), not UTF-8. Passing `encoding='utf-8'` and `errors='replace'` to `subprocess.run()` prevents crashes when model output includes special characters.

**5. Streamlit button key uniqueness**
Each "Explain with AI" button must have a globally unique `key=` value. Used the pattern `f"explain_{severity}_{i}_{title[:20]}"` to guarantee uniqueness even when two findings have similar titles.

---

<a id="installation--usage"></a>
## 🚀 Installation & Usage

### Prerequisites

- Python 3.11+
- Ollama installed (optional — app works without it)

### Step 1: Clone the repo

```bash
git clone https://github.com/ThinkWithOps/ai-devops-projects.git
cd ai-devops-projects/10-ai-infrastructure-auditor
```

### Step 2: Install dependencies + Ollama model

```bash
pip install -r requirements.txt

# Download Ollama: https://ollama.ai/download
ollama pull llama3.2
```

### Step 3: Configure environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work out of the box)
```

### Step 4: Launch the dashboard

```bash
streamlit run app.py
```

Browser opens at `http://localhost:8501` automatically.

> **No files to test with?** Click **"Load Insecure K8s Sample"** in the app. Demo Mode auto-loads the sample file with intentional security violations — 9 findings, score 25/100, Grade F.

---

### Command Reference

```
streamlit run app.py                    Start the dashboard
pip install -r requirements.txt         Install Python deps
ollama pull llama3.2                    Download AI model
cp .env.example .env                    Create config file
```

---

## 📁 Project Structure

```
10-ai-infrastructure-auditor/
├── app.py                              # Streamlit dashboard (main entry point)
├── config.py                           # Ollama settings, severity config
├── src/
│   ├── auditors/
│   │   ├── kubernetes_auditor.py       # 7-rule K8s YAML auditor
│   │   ├── docker_compose_auditor.py   # 7-rule Docker Compose auditor
│   │   ├── terraform_auditor.py        # 8-rule Terraform regex auditor
│   │   └── compliance_checker.py       # CIS-inspired score calculator
│   └── ai/
│       └── ollama_client.py            # Subprocess call to ollama CLI
├── sample_infra/
│   ├── insecure_k8s.yaml               # Demo K8s manifest (9 findings)
│   ├── insecure_docker_compose.yml     # Demo Docker Compose (8+ findings)
│   └── insecure_terraform.tf           # Demo Terraform (7+ findings)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🎬 YouTube Video

**Watch the full tutorial:** [https://youtu.be/PLACEHOLDER]

---

## 📝 License

MIT License — feel free to use in your own projects!

---

## ⚠️ Important Notes

**This is a static analysis and AI suggestion tool:**
- For learning and demonstration purposes
- Always review AI suggestions before implementing in production
- The regex-based Terraform auditor covers common patterns but is not a full HCL parser
- AI explanations are generated locally and may occasionally be imprecise — always verify

---

## 🙏 Acknowledgments

- **Ollama** — Making local AI accessible
- **Meta** — For Llama models
- **Streamlit** — Beautiful web UI with zero frontend code
- **CIS Benchmarks** — For the security rule inspiration

---

## 🔗 Related Projects

**Previous in series:**
- Project 01: AI Docker Scanner
- Project 02: AI K8s Debugger
- Project 03: AI AWS Cost Detective
- Project 04: AI GitHub Actions Healer
- Project 05: AI Terraform Generator
- Project 06: AI Local Incident Commander
- Project 07: AI Log Analyzer
- Project 08: AI Pipeline War Room
- Project 09: AI DB Query Optimizer

**Next in series:**
- Project 11: Coming soon
- Project 12: Coming soon

---

## 📧 Contact

**YouTube:** [ThinkWithOps](https://youtube.com/@thinkwithops)
**GitHub:** [ThinkWithOps](https://github.com/ThinkWithOps)

---

**⭐ If this saved your infrastructure from a breach, please star the repo!**
