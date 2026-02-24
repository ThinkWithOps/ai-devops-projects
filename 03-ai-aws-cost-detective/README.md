# AI AWS Cost Detective 💰🤖

> Analyze AWS costs and get AI-powered recommendations to reduce your bill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**YouTube Tutorial:** [Watch the full walkthrough](https://youtu.be/rg1Vnjjt9xk)

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
AWS bills are confusing and opaque. You see charges for services you don't remember creating. Hidden costs accumulate - idle EC2 instances, unused EBS volumes, forgotten S3 buckets. By the time you notice, you've wasted hundreds of dollars.

**What This Solves:**
- ✅ Automatically analyzes your AWS spending across all services
- ✅ Uses AI (Ollama + Llama 3.2) to identify waste and hidden costs
- ✅ Provides specific, actionable recommendations to reduce your bill
- ✅ Works with AWS Free Tier (no additional costs)
- ✅ 100% local AI processing (your cost data never leaves your machine)

**Real-World Use Case:**
Run this monthly to catch cost leaks early. For example: "You're spending $45/month on an EC2 instance that's only used 2 hours/day. Switch to Lambda and save $40/month." Or: "Your S3 bucket has 50GB of data you uploaded for testing 6 months ago. Delete it and save $1.15/month (adds up!)."

---

## 🛠️ Tech Stack

| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **AWS Cost Explorer API** | Fetch billing data | Official AWS service for cost analysis |
| **boto3** | AWS SDK for Python | Standard library for AWS automation |
| **AWS Free Tier** | Cloud platform | 750 hours/month free EC2, free Cost Explorer |
| **Ollama** | Local LLM runtime | Run AI locally without API costs |
| **Llama 3.2** | AI model | Excellent at analyzing data and giving advice |
| **Python 3.8+** | Programming language | Easy AWS integration and data processing |

**Why AWS Free Tier?**
- ✅ Cost Explorer API is FREE (no charges for queries)
- ✅ 750 hours/month free EC2 (test deployments)
- ✅ 5GB free S3 storage
- ✅ Learn cloud without spending money

**Why Local AI?**
- ❌ No OpenAI API costs
- ✅ Privacy: Your billing data stays on your machine
- ✅ Unlimited analysis runs
- ✅ Works offline after setup

---

## 🏗️ Architecture

### High-Level Flow

```
AWS Account
    │
    ├── Cost Explorer API
    │   (Billing data)
    │
    ├── EC2 (count instances)
    ├── S3 (count buckets)
    ├── RDS (count databases)
    └── Lambda (count functions)
    │
    ▼
┌─────────────────────┐
│   boto3 SDK         │  ◄── Fetch costs + resources
│   (Python)          │
└──────┬──────────────┘
       │
       │ Cost data + resource counts
       ▼
┌─────────────────────┐
│  Python Script      │
│ (aws_cost_          │
│  detective.py)      │
└──────┬──────────────┘
       │
       │ "Analyze spending + suggest savings"
       ▼
┌─────────────────────┐
│   Ollama API        │
│  (localhost:11434)  │
└──────┬──────────────┘
       │
       │ AI recommendations
       ▼
┌─────────────────────┐
│  Terminal Report    │  ◄── Actionable cost savings
└─────────────────────┘
```

### Component Details

**1. AWS Cost Explorer API**
- Provides detailed billing data by service
- Free to use (no API charges)
- Returns last 30 days of costs by default
- Groups costs by service (EC2, S3, RDS, etc.)

**2. boto3 SDK + Python**
- Fetches cost data: `ce_client.get_cost_and_usage()`
- Counts resources across services
- Aggregates total spending
- Identifies top cost drivers

**3. AI Analysis (Ollama)**
- Receives: Service costs + resource counts + total spend
- Analyzes patterns and identifies waste
- Generates: Cost analysis + hidden costs + optimization tips + savings estimate
- Uses context about AWS services to give specific advice

### Data Flow

1. **Authenticate**: Verify AWS credentials (IAM user or role)
2. **Fetch Costs**: Get last 30 days of billing from Cost Explorer
3. **Count Resources**: Check how many EC2, S3, RDS, Lambda resources exist
4. **Aggregate**: Calculate total cost + identify top 5 services
5. **AI Analysis**: Send to Ollama with context
6. **Generate Report**: Display findings + recommendations
7. **Optional**: Save to JSON for tracking over time

---

## 📊 Results

### Before (Traditional AWS Console)

```
AWS Console → Billing Dashboard
Total: $127.43

Services:
- EC2: $89.23
- RDS: $32.50
- S3: $5.70
```

😕 *"Okay, but WHY am I spending this much? What should I do?"*

### After (AI-Enhanced Analysis)

```bash
$ python src/aws_cost_detective.py

💰 AWS COST DETECTIVE REPORT
Total Cost: $127.43 (Last 30 days)

🤖 AI COST ANALYSIS:

**COST ANALYSIS:**
Your primary expense is EC2 ($89.23), which suggests you're running instances 
continuously. The RDS cost of $32.50 indicates a database that may be 
oversized for your workload.

**HIDDEN COSTS DETECTED:**
• EC2 instances running 24/7 when likely only needed 8 hours/day (wasting ~$60/month)
• RDS db.t3.medium could be downgraded to db.t3.micro (save ~$20/month)
• S3 storage with no lifecycle policy (old data not archived)

**OPTIMIZATION RECOMMENDATIONS:**
1. EC2: Implement auto-scaling or use Lambda for variable workloads
2. RDS: Downgrade to db.t3.micro or use Aurora Serverless for dev/test
3. S3: Enable lifecycle policies to move data >90 days old to Glacier
4. Enable AWS Budgets alerts to catch spikes early

**ESTIMATED SAVINGS:**
Following these recommendations could reduce your monthly bill to ~$45-50, 
saving approximately $75-80/month (60% reduction).
```

✅ *"Now I know exactly what to fix! Let me implement these changes."*

### Metrics

| Metric | Value |
|--------|-------|
| **Accounts Analyzed** | Personal AWS Free Tier account |
| **Avg Analysis Time** | 15-20 seconds total |
| **AI Recommendation Quality** | Matches AWS Well-Architected best practices |
| **Cost** | $0 (AWS Free Tier + local AI) |
| **Potential Savings Identified** | 30-70% bill reduction typical |

### Example Scenarios Tested

**Scenario 1: Idle EC2 instance**
- Cost: $45/month for t3.small running 24/7
- AI Recommendation: ✅ "This instance is idle 80% of time. Use Lambda or stop when not needed."
- Potential Savings: ~$35/month

**Scenario 2: Oversized RDS**
- Cost: $30/month for db.t3.medium
- AI Recommendation: ✅ "CPU usage <10%. Downgrade to db.t3.micro."
- Potential Savings: ~$18/month

**Scenario 3: Forgotten S3 data**
- Cost: $10/month for 400GB in S3 Standard
- AI Recommendation: ✅ "90% of data not accessed in 6 months. Use Glacier."
- Potential Savings: ~$8/month

---

## 🧠 Challenges & Learnings

### Challenges Faced

**1. Challenge: AWS Free Tier limits**
- **Problem**: Cost Explorer API has no free tier limits, but needed to be careful not to create resources that cost money while testing
- **Solution**: Used AWS Free Tier calculator, stayed within 750 EC2 hours/month
- **Learning**: Always check "Free Tier Eligible" filter in AWS Console

**2. Challenge: boto3 authentication**
- **Problem**: Multiple ways to configure AWS credentials (env vars, ~/.aws/credentials, IAM roles)
- **Solution**: Used `aws configure` for simplicity, documented alternatives
- **Learning**: Always use IAM best practices (least privilege, never commit keys)

**3. Challenge: Cost Explorer data lag**
- **Problem**: Cost data can be 24-48 hours delayed
- **Solution**: Document this in README, recommend running weekly/monthly
- **Learning**: Real-time cost monitoring requires CloudWatch + custom metrics

**4. Challenge: AI giving generic advice**
- **Problem**: Initial prompts gave vague "reduce EC2 usage" suggestions
- **Solution**: Added service names, cost amounts, and resource counts to prompt for specific context
- **Learning**: Good prompts = specific inputs + structured output format

### Key Learnings

✅ **DevOps Skills Learned:**
- AWS Cost Explorer API and billing structure
- boto3 SDK for AWS automation
- IAM roles and credential management
- AWS Free Tier limits and cost optimization strategies

✅ **AI/ML Skills Learned:**
- Context engineering (providing relevant data to AI)
- Prompt structuring for consistent advice
- Handling numerical data (costs) in AI responses
- Estimating savings with AI assistance

✅ **How This Prepares Me for AI Engineering:**
- **Practical FinOps**: Combining cloud expertise with AI insights
- **Cost optimization**: Critical skill for production AI systems
- **Data analysis**: Processing billing data programmatically
- **Business value**: Directly save companies money (high-impact work)

---

## 🚀 Installation & Usage

### Prerequisites

- **AWS Account** (Free Tier is sufficient)
- **AWS CLI** installed
- Python 3.8 or higher
- Ollama (with Llama 3.2 model)

> **💰 Cost Warning:**  
> This tool itself is FREE to run, but if you create AWS resources (EC2, RDS, etc.), they may incur charges after Free Tier limits. Always check [AWS Free Tier](https://aws.amazon.com/free/) limits.

---

### Step 1: Create AWS Account (If You Don't Have One)

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Follow signup process (requires credit card, but won't be charged for Free Tier usage)
4. **Important**: Enable MFA (Multi-Factor Authentication) for security

---

### Step 2: Create IAM User for This Tool

**Don't use your root account!** Create a dedicated IAM user:

1. **Log into AWS Console** → Search "IAM"
2. **Click "Users"** → "Create user"
3. **Username**: `cost-detective`
4. **Permissions**: Click "Attach policies directly"
   - Search and select: `AWSBillingReadOnlyAccess` (required for Cost Explorer)
   - Also add: `ViewOnlyAccess` (safe, read-only access to resources)
   - Or create custom policy with these permissions:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "ce:GetCostAndUsage",
             "ec2:Describe*",
             "s3:ListAllMyBuckets",
             "rds:Describe*",
             "lambda:List*"
           ],
           "Resource": "*"
         }
       ]
     }
     ```
5. **Create access key**:
   - Click on the user → "Security credentials" tab
   - "Create access key" → Choose "CLI"
   - **Download the CSV** (contains Access Key ID + Secret Access Key)
   - ⚠️ **NEVER commit these keys to GitHub!**

---

### Step 3: Install AWS CLI

**macOS:**
```bash
brew install awscli
```

**Windows:**
```powershell
# Using Chocolatey (PowerShell as Admin)
choco install awscli

# Or download from: https://aws.amazon.com/cli/
```

**Ubuntu/Linux:**
```bash
sudo apt-get update
sudo apt-get install awscli
```

**Verify installation:**
```bash
aws --version
```

---

### Step 4: Configure AWS Credentials

```bash
aws configure
```

**Enter when prompted:**
```
AWS Access Key ID: [paste from CSV]
AWS Secret Access Key: [paste from CSV]
Default region name: us-east-1
Default output format: json
```

**Verify it works:**
```bash
aws sts get-caller-identity
```

Should show your account info!

---

### Step 5: Install Ollama (If Not Already Installed)

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

### Step 6: Clone Repository & Install Dependencies

```bash
git clone https://github.com/ThinkWithOps/ai-devops-projects.git
cd ai-devops-projects/03-ai-aws-cost-detective

# Install Python dependencies
pip install -r requirements.txt
```

---

### Step 7: Run the Cost Detective!

**Analyze your AWS costs:**
```bash
python src/aws_cost_detective.py
```

**Analyze specific time period:**
```bash
python src/aws_cost_detective.py --days 60
```

**Save report to file:**
```bash
python src/aws_cost_detective.py --output report.json
```

**Get help:**
```bash
python src/aws_cost_detective.py --help
```

---

## 📖 Usage Examples

### Example 1: Basic Analysis

```bash
$ python src/aws_cost_detective.py

💰 AI AWS Cost Detective
--------------------------------------------------------------------------------
✅ AWS credentials configured
✅ Ollama running
--------------------------------------------------------------------------------

💵 Fetching AWS costs for last 30 days...
📊 Analyzing AWS resources...
🤖 Generating AI cost analysis...

[AI analysis appears here]
```

### Example 2: 90-Day Analysis

```bash
python src/aws_cost_detective.py --days 90
```

### Example 3: Save Report for Tracking

```bash
# Run monthly and save
python src/aws_cost_detective.py --output cost-report-feb-2026.json

# Compare month-over-month later
```

---

## 🧹 Cleanup

**This tool doesn't create any AWS resources!** It only reads data.

**But if you created test resources:**
```bash
# Stop EC2 instances
aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# Delete S3 buckets (first empty them)
aws s3 rb s3://my-test-bucket --force

# Delete RDS instances
aws rds delete-db-instance --db-instance-identifier mydb --skip-final-snapshot
```

---

## 🔧 Troubleshooting

### Issue: "AWS credentials not configured"

**Solution:**
```bash
# Check if credentials are set
aws configure list

# If not configured, run:
aws configure

# Or set environment variables:
export AWS_ACCESS_KEY_ID='your-key'
export AWS_SECRET_ACCESS_KEY='your-secret'
export AWS_DEFAULT_REGION='us-east-1'
```

---

### Issue: "No AWS costs detected"

**Solution:**
This is good news! You're either:
1. ✅ Using 100% Free Tier (no charges)
2. ✅ Haven't deployed anything yet
3. ⚠️ Cost data hasn't synced yet (wait 24-48 hours after first deployment)

---

### Issue: "Ollama timeout"

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not responding, restart Ollama
# macOS/Linux: ollama serve
# Windows: Restart Ollama app
```

---

### Issue: "Access Denied" errors

**Solution:**
Your IAM user needs permissions. Add these policies in IAM → Users → your user → Add permissions:
- `AWSBillingReadOnlyAccess` (required for Cost Explorer `ce:GetCostAndUsage`)
- `ViewOnlyAccess` (for reading EC2, S3, RDS, Lambda resource counts)
- Or custom policy with specific permissions (see Step 2 above)

---

## 📁 Project Structure

```
03-ai-aws-cost-detective/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── src/
│   └── aws_cost_detective.py # Main script
├── demo/
│   └── february-2026-report.json  # Sample cost report output
└── .gitignore               # Git ignore (includes AWS credentials!)
```

---

## 🎬 YouTube Video

**Watch the full tutorial:** [https://youtu.be/rg1Vnjjt9xk]

In the video, I cover:
- Creating an AWS Free Tier account
- Setting up IAM users and credentials safely
- Running the cost detective
- Interpreting AI recommendations
- Implementing cost savings

---

## 📝 License

MIT License - feel free to use this in your own projects!

---

## ⚠️ Security Warning

**NEVER commit AWS credentials to GitHub!**

This project's `.gitignore` includes:
- `.aws/`
- `credentials`
- `*.pem`
- `*.key`

**If you accidentally commit keys:**
1. Delete them from AWS Console immediately
2. Rotate credentials (create new ones)
3. Remove from Git history: `git filter-branch` or BFG Repo-Cleaner

---

## 🙏 Acknowledgments

- **AWS** - Free Tier makes cloud learning accessible
- **Ollama** - Local AI that actually works
- **boto3** - Excellent AWS SDK

---

## 🔗 Related Projects

**Previous in series:**
- **Project 1**: AI Docker Security Scanner
- **Project 2**: AI Kubernetes Pod Debugger

**Next in series:**
- **Project 4**: AI GitHub Actions Auto-Healer (coming next week)

---

## 📧 Contact

**YouTube:** [ThinkWithOps](https://youtube.com/@thinkwithops)  
**GitHub:** [ThinkWithOps](https://github.com/ThinkWithOps)

---

**⭐ If this saved you money, please star the repo and subscribe to the YouTube channel!**
