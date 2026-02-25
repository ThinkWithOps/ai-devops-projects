# AI Terraform Code Generator 🔧☁️

> Generate production-ready Terraform/OpenTofu infrastructure code from natural language using AI

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
Writing Terraform code is time-consuming and requires knowing exact syntax, resource names, and dependencies. You spend hours reading documentation just to create basic infrastructure. Beginners struggle with HCL syntax, while experts waste time on boilerplate.

**What This Solves:**
- ✅ Generate Terraform code from plain English descriptions
- ✅ Creates main.tf, variables.tf, outputs.tf automatically
- ✅ Follows Terraform best practices
- ✅ Includes proper dependencies and configurations
- ✅ 100% local AI (your infrastructure descriptions stay private)
- ✅ Works with AWS, Azure, GCP

**Real-World Use Case:**
Instead of reading 20 pages of Terraform docs to create an EC2 instance with S3, just say: "Create an EC2 instance with Ubuntu, attach an S3 bucket for storage, and output the instance IP." The AI generates complete, working Terraform code in seconds.

---

## 🛠️ Tech Stack

| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **Terraform/OpenTofu** | Infrastructure as Code | Industry standard for IaC |
| **Ollama** | Local LLM runtime | Free, private AI processing |
| **Llama 3.2** | AI model | Excellent at code generation |
| **Python 3.8+** | Programming language | Easy integration |
| **HCL** | HashiCorp Config Language | Terraform's native language |

**Why Local AI?**
- ❌ No OpenAI API costs
- ✅ Privacy: Infrastructure plans stay on your machine
- ✅ Unlimited generations
- ✅ Works offline after setup

---

## 🏗️ Architecture

### High-Level Flow

```
Natural Language Input
    |
    ▼
┌─────────────────────┐
│  Python Script      │
│  (terraform_        │
│   generator.py)     │
└──────┬──────────────┘
       │
       │ Structured prompt with IaC context
       ▼
┌─────────────────────┐
│   Ollama API        │
│  (localhost:11434)  │
│  Llama 3.2          │
└──────┬──────────────┘
       │
       │ Generated Terraform code
       ▼
┌─────────────────────┐
│  Parse & Save       │
│  - main.tf          │
│  - variables.tf     │
│  - outputs.tf       │
│  - tfvars.example   │
└─────────────────────┘
```

### How It Works

**1. User Input**
```bash
python src/terraform_generator.py \
  --description "Create EC2 with S3 bucket" \
  --provider aws
```

**2. AI Prompt Construction**
- Adds Terraform best practices
- Specifies required file structure
- Requests production-ready code
- Includes provider-specific context

**3. Code Generation**
- AI generates complete HCL code
- Multiple files (main, variables, outputs)
- Proper resource dependencies
- Comments and documentation

**4. File Parsing**
- Extracts individual files from response
- Separates main.tf, variables.tf, etc.
- Cleans formatting

**5. Output**
- Saves to `generated/` directory
- Ready to use with `terraform init`

---

## 📊 Results

### Before (Manual Terraform)

**Time to create EC2 + S3 setup:**
- Read AWS provider docs: 20 min
- Write main.tf: 15 min
- Create variables.tf: 10 min
- Write outputs.tf: 5 min
- Debug syntax errors: 10 min
- **Total: 60+ minutes** 😫

### After (AI Generated + Deployed to AWS)

```bash
$ python src/terraform_generator.py \
    --description "EC2 instance with S3 bucket for logs"

🤖 Generating Terraform code...
💾 Saving files:
  ✅ generated/main.tf
  ✅ generated/variables.tf
  ✅ generated/outputs.tf
  ✅ generated/terraform.tfvars.example

🎉 TERRAFORM CODE GENERATED
Files Created: 4
```

**Time: 30 seconds** ✅

**Then deploy to AWS:**
```bash
cd generated/
terraform init
terraform plan
terraform apply --auto-approve

# Resources created in AWS!
# ✅ EC2 instance running
# ✅ S3 bucket created
```

**Deployment time: 2 minutes** ✅

**Verify in AWS Console:**
- EC2 Dashboard shows instance running
- S3 Dashboard shows bucket exists
- **IT ACTUALLY WORKS!** 🎉

**Total time: ~4 minutes** (generation + deployment + verification)

**Generated code quality:**
- ✅ Proper resource blocks
- ✅ Variable definitions with validation
- ✅ Output values
- ✅ Best practices (tags, naming)
- ✅ Dependencies handled correctly
- ✅ **Production-ready** (proven by successful AWS deployment!)

**Cleanup:**
```bash
terraform destroy --auto-approve
# Resources destroyed, no charges
```

---

## 🧠 Challenges & Learnings

### Challenges Faced

**1. Challenge: AI generating invalid HCL syntax**
- **Problem**: Initial attempts produced pseudo-code or generic examples
- **Solution**: Highly structured prompts specifying exact Terraform syntax requirements
- **Learning**: AI needs clear output format specifications

**2. Challenge: Parsing multi-file responses**
- **Problem**: AI returns all files in one response, hard to separate
- **Solution**: Use file markers (### filename ###) and parse systematically
- **Learning**: Structured output is easier to parse than free-form

**3. Challenge: Provider-specific resources**
- **Problem**: AWS, Azure, GCP have different resource names
- **Solution**: Include provider context in prompts, use correct resource types
- **Learning**: Provider documentation knowledge is crucial

**4. Challenge: Variable best practices**
- **Problem**: AI sometimes hardcodes values instead of using variables
- **Solution**: Explicitly request variables for configurable parameters
- **Learning**: Good prompting = good output quality

### Key Learnings

✅ **DevOps Skills Learned:**
- Terraform/OpenTofu syntax and structure
- Infrastructure as Code best practices
- Multi-cloud resource provisioning
- Terraform file organization

✅ **AI/ML Skills Learned:**
- Code generation with LLMs
- Prompt engineering for structured output
- Parsing AI-generated code
- Validation of generated content

✅ **How This Prepares Me for AI Engineering:**
- **AI-powered tooling**: Building developer productivity tools
- **Code generation**: Understanding LLM capabilities for code
- **IaC automation**: Modern DevOps workflow optimization
- **Multi-cloud skills**: AWS, Azure, GCP knowledge

---

## 🚀 Installation & Usage

### Prerequisites

- Python 3.8 or higher
- Ollama (with Llama 3.2 model)
- **(Optional) Terraform** - for validation and deployment
- **(Optional) AWS Free Tier account** - to deploy generated infrastructure

**Note:** You can generate Terraform code without AWS or Terraform installed. To deploy the generated code (like shown in the demo), you'll need Terraform and a cloud account.

---

### Step 1: Install Ollama

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

**Verify:**
```bash
ollama list
```

---

### Step 2: Install Terraform

**Windows:**
1. Download from https://developer.hashicorp.com/terraform/downloads
2. Extract the zip and add `terraform.exe` to your PATH
3. Or use Chocolatey: `choco install terraform`

**macOS:**
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

**Linux:**
```bash
sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt-get install terraform
```

**Verify:**
```bash
terraform version
```

---

### Step 3: Set Up AWS (To Deploy Generated Code)

> **Skip this step** if you only want to generate Terraform code without deploying to AWS.

**3a. Create IAM User**

1. Go to: **AWS Console → IAM → Users → Create user**
2. **Username:** `terraform-generator`
3. **Permissions → Attach policies directly:**
   - ✅ `AmazonEC2FullAccess`
   - ✅ `AmazonS3FullAccess`
4. **Create access key:**
   - Go to the user → **Security credentials** tab
   - Click **Create access key**
   - Select **Command Line Interface (CLI)**
   - Copy the **Access Key ID** and **Secret Access Key**

**3b. Install AWS CLI**

Download from: https://aws.amazon.com/cli/

**Verify:**
```bash
aws --version
```

**3c. Configure AWS credentials**

```bash
aws configure
```

Enter when prompted:
```
AWS Access Key ID:     [your access key]
AWS Secret Access Key: [your secret key]
Default region name:   us-east-1
Default output format: json
```

**Verify it works:**
```bash
aws sts get-caller-identity
```

You should see your account ID and `terraform-generator` user in the output.

---

### Step 4: Clone Repository & Install

```bash
git clone https://github.com/ThinkWithOps/ai-devops-projects.git
cd ai-devops-projects/05-ai-terraform-generator

pip install -r requirements.txt
```

---

### Step 5: Generate Terraform Code!

**Basic usage:**
```bash
python src/terraform_generator.py \
  --description "Create an EC2 instance with Ubuntu"
```

**With specific provider:**
```bash
python src/terraform_generator.py \
  --description "Create a VM with storage" \
  --provider azure
```

**Custom output directory:**
```bash
python src/terraform_generator.py \
  --description "Kubernetes cluster with 3 nodes" \
  --provider gcp \
  --output my-k8s-cluster
```

**With validation (requires terraform installed):**
```bash
python src/terraform_generator.py \
  --description "S3 bucket with versioning" \
  --validate
```

---

## 📖 Usage Examples

### Example 1: Simple EC2 Instance

```bash
python src/terraform_generator.py \
  --description "EC2 t3.micro instance with Amazon Linux 2"
```

**Generates:**
- main.tf with EC2 resource
- variables.tf with instance type, AMI
- outputs.tf with instance IP
- terraform.tfvars.example

---

### Example 2: Complete Web Application Stack

```bash
python src/terraform_generator.py \
  --description "EC2 web server, RDS MySQL database, S3 for static files, and ALB for load balancing"
```

**Generates:**
- VPC with subnets
- Security groups
- EC2 instance
- RDS database
- S3 bucket
- Application Load Balancer
- All interconnections

---

### Example 3: Azure Resources

```bash
python src/terraform_generator.py \
  --description "Azure VM with managed disk and public IP" \
  --provider azure
```

---

## 🔧 Advanced Usage

### With Terraform Validation

**If you have Terraform installed:**
```bash
python src/terraform_generator.py \
  --description "EKS cluster" \
  --validate
```

**This will:**
1. Generate code
2. Run `terraform init`
3. Run `terraform validate`
4. Report any syntax errors

---

### Applying Generated Code

```bash
# 1. Generate code
python src/terraform_generator.py \
  --description "Your infrastructure" \
  --output my-infra

# 2. Review generated files
cd my-infra
cat main.tf

# 3. Create terraform.tfvars
cp terraform.tfvars.example terraform.tfvars
# Edit with your values

# 4. Initialize Terraform
terraform init

# 5. Plan (see what will be created)
terraform plan

# 6. Apply (create resources)
terraform apply
```

---

## 🧹 Cleanup

**Destroy created infrastructure:**
```bash
cd generated/
terraform destroy
```

**Remove generated files:**
```bash
rm -rf generated/
```

---

## 🔧 Troubleshooting

### Issue: "Ollama timeout"

**Solution:**
```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Restart if needed
# Windows: Restart Ollama app
# Mac/Linux: ollama serve
```

---

### Issue: "Generated code has syntax errors"

**Solution:**
- Review the AI-generated code manually
- The AI is ~85% accurate, may need small fixes
- Common issues: missing variables, incorrect resource names
- Install Terraform and run `terraform validate` to find errors

---

### Issue: "No files generated"

**Solution:**
- Check Ollama is running
- Ensure description is clear and specific
- Try simplifying the request
- Check terminal for error messages

---

## 📁 Project Structure

```
05-ai-terraform-generator/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   └── terraform_generator.py    # Main script
├── generated/                     # Output directory (created on first run)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
└── demo/
    └── example_output/            # Example generated code
```

---

## 🎬 YouTube Video

**Watch the full tutorial:** [Coming Soon]

---

## 📝 License

MIT License - feel free to use in your own projects!

---

## ⚠️ Important Notes

**AI-Generated Code:**
- Always review generated code before applying
- AI is ~85% accurate - may need minor fixes
- Test in dev environment first
- Understand what resources will be created

**Costs:**
- Cloud resources created by Terraform will incur costs
- Review pricing for your cloud provider
- Use free tier resources when testing
- Always run `terraform destroy` when done testing

---

## 🙏 Acknowledgments

- **Terraform** - Amazing IaC tool
- **Ollama** - Making local AI accessible
- **HashiCorp** - For HCL and Terraform

---

## 🔗 Related Projects

**Previous in series:**
- Project 1: AI Docker Scanner
- Project 2: AI K8s Debugger
- Project 3: AI AWS Cost Detective
- Project 4: AI GitHub Actions Healer

**Next in series:**
- Project 6: AI Local Incident Commander (coming soon)

---

**⭐ If this saved you time writing Terraform, please star the repo!**