#!/usr/bin/env python3
"""
AI GitHub Actions Auto-Healer
Analyzes failed GitHub Actions workflows and uses AI to suggest fixes.
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Optional
from datetime import datetime


class GitHubActionsHealer:
    """Main class that analyzes failed workflows and suggests fixes with AI."""
    
    def __init__(self, 
                 github_token: str,
                 repo: str,
                 ollama_host: str = "http://localhost:11434"):
        """
        Initialize the healer.
        
        Args:
            github_token: GitHub personal access token
            repo: Repository in format "owner/repo"
            ollama_host: URL of Ollama API endpoint
        """
        self.github_token = github_token
        self.repo = repo
        self.ollama_host = ollama_host
        self.ollama_model = "llama3.2"
        self.github_api = "https://api.github.com"
        
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def check_github_token(self) -> bool:
        """Check if GitHub token is valid."""
        try:
            response = requests.get(
                f"{self.github_api}/user",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_workflow_runs(self, 
                         status: str = "failure", 
                         limit: int = 10) -> List[Dict]:
        """
        Get recent workflow runs with specified status.
        
        Args:
            status: Workflow status (failure, success, etc.)
            limit: Maximum number of runs to fetch
            
        Returns:
            List of workflow run dictionaries
        """
        try:
            url = f"{self.github_api}/repos/{self.repo}/actions/runs"
            params = {
                "status": status,
                "per_page": limit
            }
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("workflow_runs", [])
            else:
                print(f"❌ GitHub API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching workflows: {e}")
            return []
    
    def get_workflow_jobs(self, run_id: int) -> List[Dict]:
        """
        Get jobs for a specific workflow run.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            List of job dictionaries
        """
        try:
            url = f"{self.github_api}/repos/{self.repo}/actions/runs/{run_id}/jobs"
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("jobs", [])
            else:
                return []
                
        except Exception as e:
            print(f"❌ Error fetching jobs: {e}")
            return []
    
    def get_job_logs(self, job_id: int) -> str:
        """
        Get logs for a specific job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job logs as string
        """
        try:
            url = f"{self.github_api}/repos/{self.repo}/actions/jobs/{job_id}/logs"
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
            else:
                return ""
                
        except Exception as e:
            print(f"❌ Error fetching logs: {e}")
            return ""
    
    def extract_error_from_logs(self, logs: str) -> str:
        """
        Extract error messages from workflow logs - IMPROVED to catch all failures.
        
        Args:
            logs: Full log text
            
        Returns:
            Extracted error portion with all relevant failures
        """
        lines = logs.split('\n')
        
        # Comprehensive error keywords
        error_keywords = [
            'error:', 'error ', 'ERROR:', 'ERROR ',
            'failed', 'failure', 'fail:', 'FAILED',
            'not found', 'does not exist', 'no such file',
            'exception', 'traceback', 'Traceback',
            'fatal:', 'cannot', 'unable to',
            'exit code', 'returned non-zero',
            'command not found', 'permission denied'
        ]
        
        error_sections = []
        seen_lines = set()  # Avoid duplicates
        
        # Find all error occurrences
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if this line contains an error
            if any(keyword in line_lower for keyword in error_keywords):
                # Skip if we've already captured this area
                if i in seen_lines:
                    continue
                
                # Get context (8 lines before and 12 after for full picture)
                start = max(0, i - 8)
                end = min(len(lines), i + 12)
                
                # Mark these lines as seen
                for j in range(start, end):
                    seen_lines.add(j)
                
                # Extract section
                section_lines = lines[start:end]
                section = '\n'.join(section_lines)
                
                error_sections.append(f"--- Error Block {len(error_sections)+1} ---")
                error_sections.append(section)
                error_sections.append("")  # Blank line separator
        
        if error_sections:
            # Return all error sections (limit to 3 most relevant)
            result = '\n'.join(error_sections)
            # Keep it under ~1500 chars for AI processing
            if len(result) > 1500:
                result = result[:1500] + "\n... (truncated for brevity)"
            return result
        else:
            # Fallback: return last 40 lines (likely contains the failure)
            return '\n'.join(lines[-40:])
    
    def ask_ollama(self, prompt: str) -> str:
        """
        Send a prompt to Ollama and get AI response.
        
        Args:
            prompt: The prompt to send to the AI
            
        Returns:
            AI response as string
        """
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: AI returned status code {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"Error communicating with AI: {e}"
    
    def analyze_failure(self, 
                       workflow_name: str,
                       job_name: str,
                       error_logs: str,
                       workflow_file: str = "") -> str:
        """
        Use AI to analyze workflow failure and suggest fixes.
        
        Args:
            workflow_name: Name of the workflow
            job_name: Name of the failed job
            error_logs: Error logs from the job
            workflow_file: Content of workflow YAML (optional)
            
        Returns:
            AI analysis and recommendations
        """
        # Build context for AI
        workflow_context = f"Workflow YAML:\n```yaml\n{workflow_file[:1000]}\n```\n\n" if workflow_file else ""
        
        # Limit log size for faster AI processing
        limited_logs = error_logs[:1200]
        
        prompt = f"""You are a GitHub Actions expert analyzing a failed CI/CD workflow.

WORKFLOW INFO:
Workflow: {workflow_name}
Failed Job: {job_name}

{workflow_context}ERROR LOGS:
```
{limited_logs}
```

Analyze ALL failures present in the logs and provide recommendations in this format:

**ROOT CAUSE:**
[Identify EACH specific error causing the failure - list all if multiple]

**WHY THIS HAPPENED:**
[Explain why each error occurred - use simple language]

**HOW TO FIX:**
[Provide specific, actionable steps to fix ALL issues found - number them]

**YAML CHANGES:**
[Show exact YAML changes needed - if applicable]

**PREVENTION:**
[How to prevent these errors in the future]

IMPORTANT: If you see multiple errors (e.g., "file not found" AND "command failed"), address BOTH of them. Don't focus on just one issue."""

        return self.ask_ollama(prompt)
    
    def get_workflow_file_content(self, workflow_path: str) -> str:
        """
        Get the content of a workflow file from the repository.
        
        Args:
            workflow_path: Path to workflow file (e.g., ".github/workflows/ci.yml")
            
        Returns:
            File content as string
        """
        try:
            url = f"{self.github_api}/repos/{self.repo}/contents/{workflow_path}"
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                import base64
                content = response.json().get("content", "")
                return base64.b64decode(content).decode('utf-8')
            else:
                return ""
                
        except Exception as e:
            print(f"⚠️  Could not fetch workflow file: {e}")
            return ""
    
    def print_analysis_report(self, 
                            workflow: Dict,
                            job: Dict,
                            analysis: str):
        """
        Print formatted analysis report.
        
        Args:
            workflow: Workflow run dictionary
            job: Job dictionary
            analysis: AI analysis
        """
        print("\n" + "="*80)
        print(f"🔍 GITHUB ACTIONS FAILURE ANALYSIS")
        print("="*80)
        print(f"Repository: {self.repo}")
        print(f"Workflow: {workflow['name']}")
        print(f"Run ID: {workflow['id']}")
        print(f"Failed Job: {job['name']}")
        print(f"Run Date: {workflow['created_at']}")
        print(f"Conclusion: {job['conclusion']}")
        print("="*80)
        
        print("\n🤖 AI DIAGNOSIS:")
        print("-" * 80)
        print(analysis)
        print("-" * 80)
        
        print("\n💡 HELPFUL LINKS:")
        print(f"  • Workflow Run: {workflow['html_url']}")
        print(f"  • Job Details: {job['html_url']}")
        
        print("\n" + "="*80)
    
    def save_report(self, 
                   workflow: Dict,
                   job: Dict,
                   analysis: str,
                   filename: str):
        """
        Save analysis report to JSON file.
        
        Args:
            workflow: Workflow run dictionary
            job: Job dictionary
            analysis: AI analysis
            filename: Output filename
        """
        report = {
            "report_date": datetime.now().isoformat(),
            "repository": self.repo,
            "workflow": {
                "id": workflow["id"],
                "name": workflow["name"],
                "run_number": workflow["run_number"],
                "created_at": workflow["created_at"],
                "conclusion": workflow["conclusion"],
                "url": workflow["html_url"]
            },
            "job": {
                "id": job["id"],
                "name": job["name"],
                "conclusion": job["conclusion"],
                "started_at": job["started_at"],
                "completed_at": job["completed_at"],
                "url": job["html_url"]
            },
            "ai_analysis": analysis
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to: {filename}")


def main():
    """Main entry point for the GitHub Actions healer."""
    parser = argparse.ArgumentParser(
        description="AI GitHub Actions Auto-Healer - Analyze and fix workflow failures"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository in format 'owner/repo'"
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--run-id",
        type=int,
        help="Specific workflow run ID to analyze"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of recent failed runs to check (default: 5)"
    )
    parser.add_argument(
        "--output",
        help="Save report to JSON file"
    )
    parser.add_argument(
        "--ollama-host",
        default="http://localhost:11434",
        help="Ollama API host (default: http://localhost:11434)"
    )
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = args.token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("❌ GitHub token required!")
        print("\nProvide token via:")
        print("  --token YOUR_TOKEN")
        print("  or set GITHUB_TOKEN environment variable")
        print("\nCreate token at: https://github.com/settings/tokens")
        print("Required scopes: repo, workflow")
        sys.exit(1)
    
    # Initialize healer
    healer = GitHubActionsHealer(
        github_token=github_token,
        repo=args.repo,
        ollama_host=args.ollama_host
    )
    
    # Pre-flight checks
    print("🔧 AI GitHub Actions Auto-Healer")
    print("-" * 80)
    
    if not healer.check_github_token():
        print("❌ Invalid GitHub token!")
        sys.exit(1)
    print("✅ GitHub token valid")
    
    if not healer.check_ollama_running():
        print("❌ Ollama is not running!")
        print("Start Ollama and run: ollama pull llama3.2")
        sys.exit(1)
    print("✅ Ollama running")
    print("-" * 80)
    
    # Get failed workflows
    if args.run_id:
        print(f"\n🔍 Analyzing specific run: {args.run_id}...")
        # Fetch specific run (implementation would go here)
        print("Feature not implemented yet - analyzing recent failures instead")
    
    print(f"\n🔍 Fetching last {args.limit} failed workflow runs...")
    failed_runs = healer.get_workflow_runs(status="failure", limit=args.limit)
    
    if not failed_runs:
        print("\n✅ No failed workflows found! Everything is working! 🎉")
        return
    
    print(f"⚠️  Found {len(failed_runs)} failed workflow(s)")
    
    # Analyze the most recent failure
    workflow = failed_runs[0]
    print(f"\n📋 Analyzing most recent failure: {workflow['name']}")
    print(f"   Run #{workflow['run_number']} - {workflow['created_at']}")
    
    # Get jobs for this workflow
    print("🔍 Fetching job details...")
    jobs = healer.get_workflow_jobs(workflow["id"])
    
    # Find failed job
    failed_job = None
    for job in jobs:
        if job["conclusion"] == "failure":
            failed_job = job
            break
    
    if not failed_job:
        print("❌ Could not find failed job details")
        return
    
    print(f"   Failed job: {failed_job['name']}")
    
    # Get job logs
    print("📄 Fetching job logs...")
    logs = healer.get_job_logs(failed_job["id"])
    
    if not logs:
        print("❌ Could not fetch job logs")
        return
    
    # Extract error
    error_logs = healer.extract_error_from_logs(logs)
    
    # Get workflow file content
    workflow_path = workflow.get("path", "")
    workflow_content = ""
    if workflow_path:
        print(f"📝 Fetching workflow file: {workflow_path}...")
        workflow_content = healer.get_workflow_file_content(workflow_path)
    
    # AI analysis
    print("🤖 Generating AI diagnosis...\n")
    analysis = healer.analyze_failure(
        workflow_name=workflow["name"],
        job_name=failed_job["name"],
        error_logs=error_logs,
        workflow_file=workflow_content
    )
    
    # Print report
    healer.print_analysis_report(workflow, failed_job, analysis)
    
    # Save if requested
    if args.output:
        healer.save_report(workflow, failed_job, analysis, args.output)
    
    print("\n✅ Analysis complete!")
    print("\n💡 TIP: Run this after every failed workflow to quickly identify issues!")
    print("="*80)


if __name__ == "__main__":
    main()
