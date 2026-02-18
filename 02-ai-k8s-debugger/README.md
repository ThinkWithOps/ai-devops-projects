# AI Kubernetes Pod Debugger 🚢🤖

> Debug Kubernetes pod failures with AI-powered explanations in plain English

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
When Kubernetes pods crash, developers get cryptic error messages like "CrashLoopBackOff", "ImagePullBackOff", or "OOMKilled". You have to dig through logs, events, and StackOverflow to figure out what's actually wrong.

**What This Solves:**
- ✅ Automatically detects unhealthy pods in your cluster
- ✅ Fetches logs and events for failing pods
- ✅ Uses AI (Ollama + Llama 3.2) to explain WHY the pod is failing
- ✅ Suggests specific kubectl commands to fix the issue
- ✅ Works 100% locally (no cloud API costs)

**Real-World Use Case:**
When a pod crashes at 2 AM, instead of digging through kubectl logs for 30 minutes, run this tool and get an AI explanation in 10 seconds: "Your pod is crashing because the container image doesn't exist in the registry. Fix: Check your deployment YAML for typos in the image name."

---

## 🛠️ Tech Stack

| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **Kubernetes** | Container orchestration | Industry standard for production deployments |
| **Minikube** | Local K8s cluster | Free, runs on your laptop, perfect for learning |
| **kubectl** | K8s CLI tool | Official tool for interacting with clusters |
| **Ollama** | Local LLM runtime | Run AI models locally without API costs |
| **Llama 3.2** | AI model | Excellent at technical explanations |
| **Python 3.8+** | Programming language | Easy to integrate with kubectl and APIs |

**Why 100% Local?**
- ❌ No OpenAI API costs
- ✅ Privacy: Your cluster data never leaves your machine
- ✅ Speed: No network latency for AI calls
- ✅ Learning: Understand how K8s + AI work together

---

## 🏗️ Architecture

### High-Level Flow

```
Kubernetes Cluster (Minikube)
        │
        ├── Pod 1 (Healthy)
        ├── Pod 2 (CrashLoopBackOff) ⚠️
        └── Pod 3 (ImagePullBackOff) ⚠️
        │
        ▼
┌─────────────────────┐
│   kubectl CLI       │  ◄── Get pod status, logs, events
│   (Python wrapper)  │
└──────┬──────────────┘
       │
       │ Pod info + logs + events
       ▼
┌─────────────────────┐
│  Python Script      │
│  (k8s_debugger.py)  │
└──────┬──────────────┘
       │
       │ "Why is this pod failing?"
       ▼
┌─────────────────────┐
│   Ollama API        │
│  (localhost:11434)  │
└──────┬──────────────┘
       │
       │ AI diagnosis with fixes
       ▼
┌─────────────────────┐
│  Terminal Report    │  ◄── Human-readable explanation
└─────────────────────┘
```

### Component Details

**1. Kubernetes Cluster (Minikube)**
- Local single-node cluster running on your laptop
- Runs inside Docker Desktop
- Free and isolated from production

**2. kubectl + Python**
- Fetches pod status: `kubectl get pods`
- Gets logs: `kubectl logs pod-name`
- Gets events: `kubectl describe pod pod-name`
- All wrapped in Python for easy parsing

**3. AI Analysis (Ollama)**
- Receives pod info, logs, and events
- Analyzes common error patterns
- Generates plain English explanations
- Suggests specific fix commands

### Data Flow

1. **Scan**: `kubectl get pods -o json`
2. **Filter**: Find unhealthy pods (not Running, restarts > 0)
3. **Collect**: Get logs + events for each unhealthy pod
4. **Analyze**: Send to Ollama with context
5. **Explain**: AI returns diagnosis in structured format
6. **Display**: Show report with suggested fixes

---

## 📊 Results

### Before (Traditional kubectl)

```bash
$ kubectl get pods
NAME          READY   STATUS             RESTARTS   AGE
broken-pod    0/1     ImagePullBackOff   0          2m
```

😕 *"ImagePullBackOff? What does that mean? How do I fix it?"*

### After (AI-Enhanced)

```bash
$ python src/k8s_debugger.py

🔍 KUBERNETES POD DEBUG REPORT
Pod: broken-pod
Status: ImagePullBackOff

🤖 AI DIAGNOSIS:

**ROOT CAUSE:**
The pod cannot start because Kubernetes cannot pull the container image 
'nonexistent-image:latest' from the registry. This image doesn't exist.

**WHY THIS HAPPENS:**
Think of it like trying to download an app from the app store, but you 
typed the wrong app name. The app store says "not found" and your phone 
can't install it. Similarly, Kubernetes can't pull an image that doesn't 
exist in Docker Hub or your registry.

**HOW TO FIX:**
1. Check your pod YAML for typos in the image name
2. Verify the image exists: docker pull nonexistent-image:latest
3. If it's a private registry, check your imagePullSecrets
4. Fix the image name and reapply: kubectl apply -f your-pod.yaml

💡 SUGGESTED NEXT STEP:
   kubectl describe pod broken-pod -n default | grep -A 5 'Events:'
```

✅ *"Now I understand! I'll fix the image name in my YAML."*

### Metrics

| Metric | Value |
|--------|-------|
| **Pods Analyzed** | 20+ (various failure types) |
| **Avg Diagnosis Time** | 10-15 seconds per pod |
| **AI Explanation Quality** | Matches K8s docs accuracy |
| **Cost** | $0 (100% local) |
| **Common Errors Detected** | ImagePullBackOff, CrashLoopBackOff, OOMKilled, ErrImagePull |

### Example Scenarios Tested

**Scenario 1: Image doesn't exist**
- Error: ImagePullBackOff
- AI Diagnosis: ✅ Correctly identified typo in image name
- Fix suggested: ✅ Check YAML, verify image exists

**Scenario 2: Container keeps crashing**
- Error: CrashLoopBackOff
- AI Diagnosis: ✅ Found "panic: runtime error" in logs
- Fix suggested: ✅ Check application code, add error handling

**Scenario 3: Out of memory**
- Error: OOMKilled
- AI Diagnosis: ✅ Identified memory limit too low
- Fix suggested: ✅ Increase memory limit in deployment YAML

---

## 🧠 Challenges & Learnings

### Challenges Faced

**1. Challenge: Getting logs from crashed containers**
- **Problem**: `kubectl logs` fails if container already exited
- **Solution**: Use `--previous` flag to get logs from last run
- **Learning**: Always have a fallback for crashed containers

**2. Challenge: Parsing kubectl JSON output**
- **Problem**: Nested JSON structure with containerStatuses
- **Solution**: Careful parsing with `.get()` for safe access
- **Learning**: kubectl JSON can have missing fields, handle gracefully

**3. Challenge: AI responses too generic**
- **Problem**: Initial prompts gave vague "check your YAML" responses
- **Solution**: Structured prompt with specific format requirements
- **Learning**: Good prompts make huge difference in AI output quality

**4. Challenge: Minikube not starting on Windows**
- **Problem**: WSL2 and Docker Desktop conflicts
- **Solution**: Use Minikube with Docker driver explicitly
- **Learning**: Always specify driver on Windows: `minikube start --driver=docker`

### Key Learnings

✅ **DevOps Skills Learned:**
- Kubernetes pod lifecycle and status phases
- kubectl commands for debugging (logs, describe, events)
- Understanding common K8s error patterns
- YAML configuration and pod specs

✅ **AI/ML Skills Learned:**
- Prompt engineering for technical diagnostics
- Structuring AI responses for consistency
- Context window management (truncating logs)
- Local AI deployment with Ollama

✅ **How This Prepares Me for AI Engineering:**
- **Practical AI integration**: Real-world debugging use case
- **Production thinking**: Error handling, timeouts, fallbacks
- **Local-first AI**: Understanding on-premise AI systems
- **Tool integration**: Combining CLI tools with AI APIs

---

## 🚀 Installation & Usage

### Prerequisites

- **Docker Desktop** installed **and running** (very important!)
- Python 3.8 or higher
- 8GB RAM minimum (16GB recommended for Minikube)

> **⚠️ Windows Users:**  
> Docker Desktop MUST be running before you start Minikube!  
> Look for the whale icon in your system tray - it should be solid, not blinking.

---

### Step 1: Install Minikube

**macOS:**
```bash
brew install minikube
```

**Windows:**
```powershell
# Using Chocolatey (in PowerShell as Admin)
choco install minikube

# Or download from: https://minikube.sigs.k8s.io/docs/start/
```

> **⚠️ Important for GitBash users:**  
> After installing with Chocolatey, add to GitBash PATH:
> ```bash
> echo 'export PATH="$PATH:/c/ProgramData/chocolatey/bin"' >> ~/.bashrc
> source ~/.bashrc
> ```
> Then restart GitBash.

**Ubuntu/Linux:**
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

**Verify installation:**
```bash
minikube version
```

---

### Step 2: Install kubectl

**macOS:**
```bash
brew install kubectl
```

**Windows:**
```powershell
choco install kubernetes-cli
```

**Ubuntu/Linux:**
```bash
sudo apt-get update
sudo apt-get install -y kubectl
```

**Verify installation:**
```bash
kubectl version --client
```

---

### Step 3: Start Minikube

```bash
# Start a local Kubernetes cluster
minikube start

# Verify it's running
kubectl cluster-info
kubectl get nodes
```

**Expected output:**
```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   1m    v1.28.3
```

**Troubleshooting:**
- **Windows**: If it fails, try: `minikube start --driver=docker`
- **Low memory**: Try: `minikube start --memory=4096 --cpus=2`
- **Already running**: Try: `minikube delete` then `minikube start`

---

### Step 4: Install Ollama (if not already installed)

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from https://ollama.com

**Download AI model:**
```bash
ollama pull llama3.2
```

**Verify Ollama is running:**
```bash
ollama list
```

---

### Step 5: Clone Repository & Install Dependencies

```bash
git clone https://github.com/ThinkWithOps/ai-devops-projects.git
cd ai-devops-projects/02-ai-k8s-debugger

# Install Python dependencies
pip install -r requirements.txt
```

---

### Step 6: Test with a Broken Pod

**Create a broken pod for testing:**
```bash
kubectl apply -f demo/broken-pod.yaml
```

**Wait a few seconds, then check status:**
```bash
kubectl get pods
```

**Expected output:**
```
NAME         READY   STATUS             RESTARTS   AGE
broken-pod   0/1     ImagePullBackOff   0          30s
```

---

### Step 7: Run the Debugger!

**Analyze all unhealthy pods:**
```bash
python src/k8s_debugger.py
```

**Analyze a specific pod:**
```bash
python src/k8s_debugger.py --pod broken-pod
```

**Analyze pods in a specific namespace:**
```bash
python src/k8s_debugger.py --namespace kube-system
```

**Get help:**
```bash
python src/k8s_debugger.py --help
```

---

## 📖 Usage Examples

### Example 1: Scan All Pods

```bash
$ python src/k8s_debugger.py

🚀 AI Kubernetes Pod Debugger
--------------------------------------------------------------------------------
✅ kubectl installed
✅ Cluster accessible
✅ Ollama running
--------------------------------------------------------------------------------

🔍 Scanning pods in namespace 'default'...

⚠️  Found 1 unhealthy pod(s)
📋 Analyzing with AI...

[AI analysis appears here]
```

### Example 2: Specific Pod

```bash
python src/k8s_debugger.py --pod my-app-pod
```

### Example 3: Different Namespace

```bash
python src/k8s_debugger.py --namespace production
```

### Example 4: All Pods (Even Healthy)

```bash
python src/k8s_debugger.py --all
```

---

## 🧹 Cleanup

**Delete test pod:**
```bash
kubectl delete pod broken-pod
```

**Stop Minikube:**
```bash
minikube stop
```

**Delete Minikube cluster:**
```bash
minikube delete
```

---

## 🔧 Troubleshooting

### Windows-Specific Issues

**Issue: "Unable to pick a default driver" or "docker: Not healthy"**

**Solution:**
Docker Desktop is not running!

1. Open Docker Desktop from Start menu
2. Wait for it to fully start (whale icon in system tray should be solid)
3. Verify Docker is running:
   ```bash
   docker version
   ```
4. Then try again:
   ```bash
   minikube start
   ```

---

**Issue: "kubectl: command not found" or "minikube: command not found" in GitBash (Windows)

**Solution (Windows GitBash users):**

If you installed via Chocolatey in PowerShell but GitBash doesn't recognize the commands:

```bash
# Add Chocolatey bin to GitBash PATH
echo 'export PATH="$PATH:/c/ProgramData/chocolatey/bin"' >> ~/.bashrc
source ~/.bashrc

# Verify
minikube version
kubectl version --client
```

**Solution (macOS/Linux):**
```bash
# Verify installation
which kubectl
which minikube

# If not found, reinstall (see installation steps above)
```

---

### Issue: "Cluster is not accessible"

**Solution:**
```bash
# Check if Minikube is running
minikube status

# If not running, start it
minikube start

# Verify
kubectl get nodes
```

---

### Issue: "No unhealthy pods found but pod is clearly broken"

**Solution:**
```bash
# Check pod status manually
kubectl get pods

# Force analyze specific pod
python src/k8s_debugger.py --pod <pod-name>
```

---

### Issue: Ollama timeout

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not responding, restart Ollama
# macOS/Linux: ollama serve
# Windows: Restart Ollama app
```

---

## 📁 Project Structure

```
02-ai-k8s-debugger/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── src/
│   └── k8s_debugger.py      # Main debugger script
├── demo/
│   └── broken-pod.yaml      # Sample broken pod for testing
└── .gitignore               # Git ignore rules
```

---

## 🎬 YouTube Video

**Watch the full tutorial:** [Coming Soon]

In the video, I cover:
- Installing Minikube and kubectl from scratch
- Starting a local Kubernetes cluster
- Running the debugger on broken pods
- Explaining the code architecture
- Live demo of AI diagnosing pod failures

---

## 📝 License

MIT License - feel free to use this in your own projects!

---

## 🙏 Acknowledgments

- **Kubernetes** - Amazing container orchestration
- **Minikube** - Making K8s accessible locally
- **Ollama** - Free local AI that actually works
- **Meta AI** - Llama 3.2 model

---

## 🔗 Related Projects

**Previous in series:**
- **Project 1**: AI Docker Security Scanner

**Next in series:**
- **Project 3**: AI AWS Cost Detective (coming next week)

---

## 📧 Contact

**YouTube:** [ThinkWithOps](https://youtube.com/@thinkwithops)  
**GitHub:** [ThinkWithOps](https://github.com/ThinkWithOps)

---

**⭐ If this helped you, please star the repo and subscribe to the YouTube channel!**
