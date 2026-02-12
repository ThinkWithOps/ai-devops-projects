# AI Docker Security Scanner 🐳🤖

> Scan Docker images for vulnerabilities and get AI-powered explanations in plain English

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**YouTube Tutorial:** [Watch the full walkthrough](#) *(link coming soon)*

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Results](#-results)
- [Challenges & Learnings](#-challenges--learnings)
- [Installation & Usage](#-installation--usage)

---

## 🎯 Problem Statement

**The Problem:**
Developers regularly use Docker images from Docker Hub, but most don't understand the security vulnerabilities hiding inside them. Traditional security scanners like Trivy output technical CVE IDs and cryptic descriptions that are hard to understand for beginners.

**What This Solves:**
- ✅ Scans any Docker image for HIGH and CRITICAL vulnerabilities
- ✅ Uses AI (Ollama + Llama 3.2) to explain each vulnerability in simple terms
- ✅ Provides actionable fix suggestions
- ✅ Generates executive-level security summaries
- ✅ Works 100% offline and FREE (no cloud API costs)

**Real-World Use Case:**
Before deploying a new Docker image to production, run this scanner to understand security risks and get plain-English explanations that you can share with your team.

---

## 🛠️ Tech Stack

| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **Docker** | Container runtime | Industry standard for containerization |
| **Trivy** | Vulnerability scanner | Free, fast, comprehensive CVE database |
| **Ollama** | Local LLM runtime | Run AI models locally without API costs |
| **Llama 3.2** | AI model | Excellent at technical explanations, runs on 8GB RAM |
| **Python 3.8+** | Programming language | Easy to read, great libraries for API calls |
| **requests** | HTTP library | Simple API calls to Ollama |

**Why 100% Local?**
- ❌ No OpenAI API costs ($0.002 per 1K tokens adds up fast)
- ✅ Privacy: Your code/images never leave your machine
- ✅ Speed: No network latency for AI calls
- ✅ Learning: Understand how LLMs work locally

---

## 🏗️ Architecture

### High-Level Flow

```
┌─────────────┐
│ Docker Image│
│  (nginx)    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Trivy Scanner     │  ◄── Scans for CVEs
│  (CLI Tool)         │
└──────┬──────────────┘
       │
       │ JSON output (vulnerabilities)
       ▼
┌─────────────────────┐
│  Python Script      │
│  (docker_scanner.py)│
└──────┬──────────────┘
       │
       │ For each vulnerability:
       │ "Explain CVE-2024-1234 in simple terms"
       ▼
┌─────────────────────┐
│   Ollama API        │
│  (localhost:11434)  │
└──────┬──────────────┘
       │
       │ AI generates plain English explanation
       ▼
┌─────────────────────┐
│  Terminal Report    │  ◄── Human-readable output
│  + JSON file        │
└─────────────────────┘
```

### Component Details

**1. Trivy (Security Scanner)**
- Scans Docker image layers
- Checks against CVE database
- Outputs JSON with vulnerability details
- Free and open-source

**2. Python Orchestrator**
- Parses Trivy JSON output
- Sends each vulnerability to Ollama
- Formats AI responses
- Generates final report

**3. Ollama (Local AI)**
- Runs Llama 3.2 model locally
- Responds via REST API (port 11434)
- No internet required after model download
- Free unlimited usage

### Data Flow

1. **Scan**: `trivy image nginx:latest --format json`
2. **Extract**: Parse JSON → get CVE IDs, packages, severities
3. **Analyze**: For each CVE → send to Ollama with context
4. **Explain**: Ollama returns plain English explanation
5. **Report**: Format and display all explanations

---

## 📊 Results

### Before (Traditional Trivy Output)
```
CVE-2024-1234 (CRITICAL)
Package: openssl 1.1.1k
Description: Use-after-free in X509_verify_cert function
```
😕 *"What does this mean? How do I fix it?"*

### After (AI-Enhanced Output)
```
🤖 AI Explanation:
This vulnerability is like leaving your house key under the doormat. 
The OpenSSL library (which handles secure connections) has a bug 
where attackers could potentially decrypt your HTTPS traffic. 

Fix: Update to openssl 1.1.1w or later in your Dockerfile.
```
✅ *"Now I understand! I'll update the base image."*

### Metrics

| Metric | Value |
|--------|-------|
| **Images Scanned** | 50+ (nginx, node, python, ubuntu) |
| **Avg Scan Time** | 15-30 seconds per image |
| **AI Explanation Time** | ~3 seconds per vulnerability |
| **Cost** | $0 (100% local) |
| **Accuracy** | AI explanations match official CVE descriptions |

### Example Scan Output

**Image:** `nginx:1.19` (intentionally vulnerable for demo)

```
🛡️  AI DOCKER SECURITY REPORT
================================================================================
Image: nginx:1.19
Scan Date: 2024-02-09 14:30:00
Total Vulnerabilities: 47

📊 AI SECURITY SUMMARY:
--------------------------------------------------------------------------------
This image has critical security concerns that need immediate attention. 
The main risks come from outdated SSL/TLS libraries and compression tools 
that could allow attackers to intercept encrypted traffic or execute 
malicious code. Priority action: Upgrade to nginx:1.25 or rebuild with 
updated base image.
--------------------------------------------------------------------------------

🔍 VULNERABILITY DETAILS (5 shown):
================================================================================

[1] CRITICAL - CVE-2022-37434
    Package: zlib (1.2.11)
    Fixed in: 1.2.12

    🤖 AI Explanation:
    Think of zlib like a zip file handler. This vulnerability is similar to
    a malicious zip bomb - an attacker could craft a special compressed file
    that, when your server tries to decompress it, crashes the system or
    allows code execution. Fix: Update your Dockerfile to use Ubuntu 22.04
    base image which includes zlib 1.2.12.

[2] HIGH - CVE-2021-23017
    Package: nginx (1.19.0)
    Fixed in: 1.21.0

    🤖 AI Explanation:
    This is a DNS resolver bug. If your nginx config uses DNS hostnames
    (like proxy_pass http://backend.example.com), attackers could poison
    the DNS response and redirect traffic to malicious servers. It's like
    someone changing road signs to send you to the wrong destination.
    Fix: Upgrade to nginx:1.25-alpine for the latest security patches.

...
```

---

## 🧠 Challenges & Learnings

### Challenges Faced

**1. Challenge: Trivy Output Format Changes**
- **Problem**: Trivy JSON structure varies between versions
- **Solution**: Wrote defensive parsing code with `.get()` fallbacks
- **Learning**: Always validate external tool outputs

**2. Challenge: Ollama Response Time**
- **Problem**: First AI call took 30+ seconds (model loading)
- **Solution**: Keep Ollama running; use `ollama run llama3.2` to preload
- **Learning**: Local LLMs have cold-start overhead

**3. Challenge: AI Explanations Too Technical**
- **Problem**: Initial prompts produced jargon-filled responses
- **Solution**: Refined prompts to explicitly ask for analogies and simple terms
- **Learning**: Prompt engineering is critical for good AI outputs

**4. Challenge: Handling 100+ Vulnerabilities**
- **Problem**: Some images have 200+ CVEs (analyzing all takes 10+ minutes)
- **Solution**: Added `--limit` flag to analyze top N vulnerabilities
- **Learning**: Always consider performance in real-world usage

### Key Learnings

✅ **DevOps Skills Learned:**
- Docker image layers and security best practices
- Using Trivy for CVE scanning
- JSON parsing and data transformation
- Command-line tool design (argparse)

✅ **AI/ML Skills Learned:**
- Running local LLMs with Ollama
- Prompt engineering for technical explanations
- API integration (REST calls to Ollama)
- Balancing AI quality vs. speed

✅ **How This Prepares Me for AI Engineering:**
- **Practical LLM usage**: Not just theory, real API integration
- **Prompt optimization**: Critical skill for AI engineering
- **Local AI deployment**: Understanding on-premise AI systems
- **Tool integration**: Combining traditional DevOps tools with AI

---

## 🚀 Installation & Usage

### Prerequisites

- Docker Desktop installed
- Python 3.8 or higher
- 8GB RAM minimum (for Ollama)

### Step 1: Install Trivy

**macOS:**
```bash
brew install trivy
```

**Ubuntu/Debian:**
```bash
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy
```

**Windows:**
```powershell
choco install trivy
```

Verify installation:
```bash
trivy --version
```

### Step 2: Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [ollama.com](https://ollama.com)

### Step 3: Download AI Model

```bash
ollama pull llama3.2
```

This downloads ~2GB. Wait for completion.

Verify Ollama is running:
```bash
ollama run llama3.2
>>> Hello!  (Type /bye to exit)
```

### Step 4: Clone This Repository

```bash
git clone https://github.com/yourusername/thinkwithops-portfolio.git
cd thinkwithops-portfolio/01-ai-docker-scanner
```

### Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Run the Scanner!

**Basic scan:**
```bash
python src/docker_scanner.py nginx:latest
```

**Scan with options:**
```bash
# Limit to top 3 vulnerabilities
python src/docker_scanner.py nginx:latest --limit 3

# Save report to JSON
python src/docker_scanner.py nginx:latest --output report.json

# Use custom Ollama host
python src/docker_scanner.py nginx:latest --ollama-host http://192.168.1.100:11434
```

### Example Commands

**Scan a vulnerable image (for demo):**
```bash
python src/docker_scanner.py nginx:1.19
```

**Scan a secure image:**
```bash
python src/docker_scanner.py nginx:alpine
```

**Scan your own image:**
```bash
docker build -t myapp:latest .
python src/docker_scanner.py myapp:latest
```

---

## 📁 Project Structure

```
01-ai-docker-scanner/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── src/
│   └── docker_scanner.py    # Main scanner script
├── demo/
│   ├── screenshot1.png      # Terminal output example
│   ├── screenshot2.png      # AI explanation example
│   └── sample_report.json   # Example JSON output
└── .gitignore               # Ignore venv, cache, etc.
```

---

## 🎬 YouTube Video

**Watch the full tutorial:** [Coming Soon]

In the video, I cover:
- Installing all tools from scratch
- Running the scanner on real images
- Explaining the code architecture
- Live demo of AI explanations
- Tips for extending this project

---

## 📝 License

MIT License - feel free to use this in your own projects!

---

## 🙏 Acknowledgments

- **Trivy** by Aqua Security - Amazing free security scanner
- **Ollama** - Making local LLMs accessible to everyone
- **Meta AI** - Llama 3.2 model

---

## 🔗 Related Projects

**Next in series:**
- **Project 2**: AI Kubernetes Pod Debugger (uses similar AI explanation pattern)
- **Project 3**: AI AWS Cost Detective (extends scanning to cloud resources)

---

## 📧 Contact

**YouTube:** [ThinkWithOps](https://youtube.com/@thinkwithops)  
**GitHub:** [Your GitHub](https://github.com/yourusername)

---

**⭐ If this helped you, please star the repo and subscribe to the YouTube channel!**