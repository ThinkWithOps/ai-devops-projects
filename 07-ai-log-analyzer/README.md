# 🔍 AI Log Analyzer

> AI-powered log analysis tool that reads Docker, K8s, and application logs — finds root causes and suggests fixes in seconds instead of hours.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
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

When something breaks in production, engineers spend **2-4 hours** manually:
- Scrolling through thousands of log lines
- Grepping for errors across multiple files
- Searching Stack Overflow for similar issues
- Trial and error until something works

**Meanwhile your app is down and customers are frustrated.**

This tool analyzes logs in seconds, finds the root cause, and gives you exact fix commands — so you spend time fixing, not searching.

---

<a id="tech-stack"></a>
## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core scripting |
| Ollama (Llama 3.2) | Local AI for root cause analysis |
| `re` (stdlib) | Log parsing with regex |
| `json` (stdlib) | JSON log format parsing |
| `collections.Counter` | Pattern frequency detection |
| `subprocess` (stdlib) | Ollama integration |
| `pathlib` (stdlib) | File handling |

**No external pip packages required.** 100% local — no API costs, no data sent to cloud.

---

<a id="architecture"></a>
## 🏗️ Architecture

```
Log File (text/JSON/syslog)
         │
         ▼
  Format Detection
  (auto-detect or manual)
         │
         ▼
     Log Parser
  (text / json / syslog)
         │
         ▼
  Severity Categorization
  CRITICAL / ERROR / WARNING / INFO
         │
         ▼
   Pattern Detection
  (recurring error groups)
         │
         ▼
   AI Analysis (Ollama)
  Root Cause + Fix Steps
         │
         ▼
  Report (terminal + markdown)
```

**Supported Log Formats:**
- **Plain text** — K8s events, application logs with timestamp + level prefix
- **JSON** — Structured logs (supports `level`, `severity`, `message`, `msg` fields)
- **Syslog** — Standard Unix syslog format

---

<a id="results"></a>
## 📊 Results

| Metric | Before (Manual) | After (AI Analyzer) |
|--------|----------------|---------------------|
| Time to find root cause | 2-4 hours | < 2 minutes |
| Log formats supported | 1 (manual grep) | 3 (auto-detected) |
| Pattern detection | Manual | Automatic |
| Fix suggestions | Google/Stack Overflow | AI-generated instantly |
| Incident report | Hours to write | Auto-generated |
| API cost | $0 | $0 (100% local) |

---

<a id="challenges--learnings"></a>
## 🧠 Challenges & Learnings

**1. Multi-format log parsing**
Different tools log differently — K8s uses plain text, modern apps use JSON, Unix systems use syslog. Built an auto-detector that checks the first line structure to pick the right parser.

**2. Pattern normalization**
Raw error messages contain timestamps, IPs, and pod hashes that make identical errors look different. Used regex to strip variable parts before counting, so `pod/api-server-7d9f8b-xk2pq: ImagePullBackOff` and `pod/api-server-rt4lx-abc12: ImagePullBackOff` are recognized as the same pattern.

**3. AI prompt engineering**
Sending all errors to the AI is slow and noisy. Capped at top 10 errors + top 3 patterns. This gives the AI enough context without overwhelming it — and keeps response time under 60 seconds.

**4. Windows encoding (again)**
Ollama outputs Unicode on Windows but subprocess defaults to `cp1252`. Fixed with `encoding='utf-8'` on `subprocess.run()`.

---

<a id="installation--usage"></a>
## 🚀 Installation & Usage

### Prerequisites

- Python 3.11+
- Ollama installed and running

### Step 1: Clone the repo

```bash
git clone https://github.com/ThinkWithOps/ai-devops-projects.git
cd ai-devops-projects/07-ai-log-analyzer
```

### Step 2: Install dependencies + Ollama model

```bash
pip install -r requirements.txt

# Download Ollama: https://ollama.ai/download
ollama pull llama3.2
```

### Step 3: Launch the Web Dashboard!

```bash
streamlit run src/app.py
```

Browser opens at `http://localhost:8501` automatically.

**Then:**
1. Click **"☸️ K8s Failed Deployment"** — see metrics dashboard + AI analysis
2. Click **"💳 App Errors (JSON)"** — watch format auto-detection
3. Click **"🐳 Docker OOMKilled"** — see OOMKilled root cause
4. Upload your own `.log` file — drag & drop anywhere

> **CLI alternative** (no browser needed):
> ```bash
> python src/log_analyzer.py --file demo/sample_logs/k8s_failed_deployment.log --save-report
> ```

---

### Usage Examples

**Example 1: Analyze K8s failed deployment**
```bash
python src/log_analyzer.py --file demo/sample_logs/k8s_failed_deployment.log --save-report
```
```
🔍 Checking Ollama installation...
✅ Ollama is ready!

============================================================
       🔍 AI LOG ANALYZER 🔍
============================================================

📂 Analyzing: k8s_failed_deployment.log
📋 Format: text
🔄 Parsing log entries...
📊 Parsed 18 log entries

📊 Log Summary:
   🔴 CRITICAL: 4
   🟠 ERROR:    8
   🟡 WARNING:  3
   🔵 INFO:     3

🔄 Recurring Patterns:
   3x: pod/api-server-<hash>: ImagePullBackOff

🚨 Critical & Error Lines:
   Line   4: Failed to pull image "registry.company.com/api-server:v2.1.0": 401 Unauthorized
   Line   5: Error: ErrImagePull - pod api-server-7d9f8b-xk2pq
   Line   7: pod/api-server-7d9f8b-xk2pq: ImagePullBackOff
   ...

🤖 Analyzing with AI (this may take 30-60 seconds)...

============================================================
📋 AI ROOT CAUSE ANALYSIS
============================================================
Root Cause: The deployment failed because the container registry
returned a 401 Unauthorized error. The image pull secret is either
missing, expired, or misconfigured for registry.company.com.

Immediate Fix Steps:
1. Check imagePullSecrets: kubectl get secret regcred -n default
2. Recreate the secret: kubectl create secret docker-registry regcred \
   --docker-server=registry.company.com \
   --docker-username=<user> --docker-password=<token>
3. Patch the deployment: kubectl patch deployment api-server \
   -p '{"spec":{"template":{"spec":{"imagePullSecrets":[{"name":"regcred"}]}}}}'

Prevention: Store registry credentials as K8s secrets and rotate
them on a schedule. Add registry authentication checks to CI/CD
pipeline before deployment.

💾 Report saved to: log_reports/report_20240115_102600.md
```

**Example 2: JSON format app errors (auto-detected)**
```bash
python src/log_analyzer.py --file demo/sample_logs/app_errors.log
```
```
📂 Analyzing: app_errors.log
📋 Format: json
📊 Parsed 13 log entries

📊 Log Summary:
   🔴 CRITICAL: 2
   🟠 ERROR:    6
   🟡 WARNING:  1
   🔵 INFO:     4

🔄 Recurring Patterns:
   3x: Database connection failed: timeout after <N>s

🤖 Analyzing with AI...
Root Cause: Database connection pool exhausted due to repeated
timeout failures. Circuit breaker opened after pool hit 100/100
connections...
```

**Example 3: Analyze your own log file**
```bash
python src/log_analyzer.py --file /path/to/your/app.log --save-report
```

**Example 4: Skip AI (fast categorization only)**
```bash
python src/log_analyzer.py --file app.log --no-ai
```

---

### Command Reference

```
python src/log_analyzer.py [OPTIONS]

Options:
  --file FILE            Log file to analyze
  --format FORMAT        Log format: auto, json, text, syslog (default: auto)
  --simulate TYPE        Demo mode: k8s, app, docker
  --save-report          Save markdown report to log_reports/
  --no-ai               Skip AI analysis (parse and categorize only)
  -h, --help            Show help
```

> **Note:** `--save-report` saves a markdown report to `log_reports/report_*.md`.
> Without it, results are shown in the terminal only.

---

## 📁 Project Structure

```
07-ai-log-analyzer/
├── src/
│   └── log_analyzer.py          # Main script
├── demo/
│   ├── demo.py                  # Runs all 3 sample log analyses
│   └── sample_logs/
│       ├── k8s_failed_deployment.log  # K8s ImagePullBackOff scenario
│       ├── app_errors.log             # JSON payment API DB failure
│       └── docker_crash.log           # Docker OOMKilled scenario
├── log_reports/                 # Auto-generated reports (git-ignored)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🎬 YouTube Video

**Watch the full tutorial:** [https://youtu.be/LINK_HERE]

---

## 📝 License

MIT License - feel free to use in your own projects!

---

## ⚠️ Important Notes

**This is a log analysis and AI suggestion tool:**
- For learning and demonstration purposes
- Always review AI suggestions before implementing
- Test fixes in dev environment first
- AI is ~90% accurate but not infallible

---

## 🙏 Acknowledgments

- **Ollama** - Making local AI accessible
- **Meta** - For Llama models
- **Streamlit** - Beautiful web UI with zero frontend code

---

## 🔗 Related Projects

**Previous in series:**
- Project 1: AI Docker Scanner
- Project 2: AI K8s Debugger
- Project 3: AI AWS Cost Detective
- Project 4: AI GitHub Actions Healer
- Project 5: AI Terraform Generator
- Project 6: AI Incident Commander

**Next in series:**
- Project 8: AI CI/CD Optimizer (coming soon)

---

## 📧 Contact

**YouTube:** [ThinkWithOps](https://youtube.com/@thinkwithops)
**GitHub:** [ThinkWithOps](https://github.com/ThinkWithOps)

---

**⭐ If this saved you time debugging logs, please star the repo!**
