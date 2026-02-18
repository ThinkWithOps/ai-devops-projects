#!/usr/bin/env python3
"""
AI Kubernetes Pod Debugger
Analyzes pod failures and uses AI to explain root causes in plain English.
"""

import subprocess
import json
import sys
import argparse
from typing import Dict, List, Optional
import requests
from datetime import datetime


class K8sDebugger:
    """Main debugger class that orchestrates kubectl and AI analysis."""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """
        Initialize the debugger.
        
        Args:
            ollama_host: URL of Ollama API endpoint
        """
        self.ollama_host = ollama_host
        self.ollama_model = "llama3.2"
        
    def check_kubectl_installed(self) -> bool:
        """Check if kubectl is installed and accessible."""
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def check_cluster_accessible(self) -> bool:
        """Check if Kubernetes cluster is accessible."""
        try:
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_pods(self, namespace: str = "default") -> List[Dict]:
        """
        Get list of pods in the namespace.
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            List of pod information dictionaries
        """
        try:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            pods = []
            
            for item in data.get("items", []):
                pod_name = item["metadata"]["name"]
                status = item["status"]["phase"]
                
                # Get container statuses
                container_statuses = item["status"].get("containerStatuses", [])
                
                # Check for problems
                ready = all(cs.get("ready", False) for cs in container_statuses)
                restart_count = sum(cs.get("restartCount", 0) for cs in container_statuses)
                
                # Determine health
                is_healthy = status == "Running" and ready and restart_count == 0
                
                pods.append({
                    "name": pod_name,
                    "status": status,
                    "ready": ready,
                    "restarts": restart_count,
                    "healthy": is_healthy,
                    "namespace": namespace
                })
            
            return pods
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting pods: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing pod data: {e}")
            return []
    
    def get_pod_logs(self, pod_name: str, namespace: str = "default", 
                     tail: int = 50) -> str:
        """
        Get logs from a pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Kubernetes namespace
            tail: Number of lines to retrieve
            
        Returns:
            Pod logs as string
        """
        try:
            result = subprocess.run(
                ["kubectl", "logs", pod_name, "-n", namespace, f"--tail={tail}"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            return result.stdout
        except subprocess.CalledProcessError:
            # Try to get previous logs if container crashed
            try:
                result = subprocess.run(
                    ["kubectl", "logs", pod_name, "-n", namespace, 
                     "--previous", f"--tail={tail}"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10
                )
                return result.stdout
            except:
                return ""
        except subprocess.TimeoutExpired:
            return ""
    
    def get_pod_events(self, pod_name: str, namespace: str = "default") -> str:
        """
        Get events related to a pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Kubernetes namespace
            
        Returns:
            Events as string
        """
        try:
            result = subprocess.run(
                ["kubectl", "describe", "pod", pod_name, "-n", namespace],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            # Extract Events section
            output = result.stdout
            if "Events:" in output:
                events_section = output.split("Events:")[1]
                # Take first 20 lines of events
                events_lines = events_section.split('\n')[:20]
                return '\n'.join(events_lines)
            return ""
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return ""
    
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
                timeout=180
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: AI returned status code {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"Error communicating with AI: {e}"
    
    def analyze_pod_failure(self, pod: Dict, logs: str, events: str) -> str:
        """
        Use AI to analyze pod failure and suggest fixes.
        
        Args:
            pod: Pod information dictionary
            logs: Pod logs
            events: Pod events
            
        Returns:
            AI analysis as string
        """
        # Truncate logs/events if too long
        logs_sample = logs[:2000] if logs else "No logs available"
        events_sample = events[:1000] if events else "No events available"
        
        prompt = f"""You are a Kubernetes expert helping debug pod failures.

Pod Information:
- Name: {pod['name']}
- Status: {pod['status']}
- Ready: {pod['ready']}
- Restart Count: {pod['restarts']}

Recent Logs (last 50 lines):
{logs_sample}

Recent Events:
{events_sample}

Provide a diagnosis in this format:

**ROOT CAUSE:**
[Explain in 1-2 sentences what's causing the pod to fail, using simple terms]

**WHY THIS HAPPENS:**
[Explain why this error occurs, use an analogy if helpful]

**HOW TO FIX:**
[Provide specific kubectl commands or YAML changes to fix the issue]

Keep it concise and actionable. If logs show common errors like ImagePullBackOff, CrashLoopBackOff, or OOMKilled, explain those clearly."""

        response = self.ask_ollama(prompt)
        return self._remove_repeated_suffix(response)
    
    @staticmethod
    def _remove_repeated_suffix(text: str) -> str:
        """Remove duplicated trailing content that LLMs sometimes produce."""
        length = len(text)
        # Check if the second half repeats any suffix of the first half
        for split in range(length // 3, length // 2 + 1):
            first_part = text[:split].rstrip()
            second_part = text[split:].strip()
            if second_part and first_part.endswith(second_part):
                return first_part
        return text

    def generate_fix_command(self, pod: Dict, diagnosis: str) -> Optional[str]:
        """
        Generate kubectl command to help fix the issue.
        
        Args:
            pod: Pod information
            diagnosis: AI diagnosis
            
        Returns:
            Suggested kubectl command
        """
        # Simple heuristics for common issues
        if pod['status'] == 'ImagePullBackOff' or 'image' in diagnosis.lower():
            return f"kubectl describe pod {pod['name']} -n {pod['namespace']} | grep -A 5 'Events:'"
        elif pod['restarts'] > 0:
            return f"kubectl logs {pod['name']} -n {pod['namespace']} --previous"
        elif not pod['ready']:
            return f"kubectl get pod {pod['name']} -n {pod['namespace']} -o yaml"
        else:
            return f"kubectl describe pod {pod['name']} -n {pod['namespace']}"
    
    def print_pod_report(self, pod: Dict, diagnosis: str):
        """
        Print formatted debugging report.
        
        Args:
            pod: Pod information
            diagnosis: AI diagnosis
        """
        print("\n" + "="*80)
        print(f"🔍 KUBERNETES POD DEBUG REPORT")
        print("="*80)
        print(f"Pod: {pod['name']}")
        print(f"Namespace: {pod['namespace']}")
        print(f"Status: {pod['status']}")
        print(f"Ready: {'✅ Yes' if pod['ready'] else '❌ No'}")
        print(f"Restarts: {pod['restarts']}")
        print(f"Healthy: {'✅ Yes' if pod['healthy'] else '⚠️  No'}")
        print("="*80)
        
        print("\n🤖 AI DIAGNOSIS:")
        print("-" * 80)
        print(diagnosis)
        print("-" * 80)
        
        # Suggest next steps
        fix_cmd = self.generate_fix_command(pod, diagnosis)
        if fix_cmd:
            print("\n💡 SUGGESTED NEXT STEP:")
            print(f"   {fix_cmd}")
        
        print("\n" + "="*80)


def main():
    """Main entry point for the debugger."""
    parser = argparse.ArgumentParser(
        description="AI Kubernetes Pod Debugger - Analyze pod failures with AI"
    )
    parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace (default: default)"
    )
    parser.add_argument(
        "--pod",
        help="Specific pod name to analyze (optional)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all unhealthy pods"
    )
    parser.add_argument(
        "--ollama-host",
        default="http://localhost:11434",
        help="Ollama API host (default: http://localhost:11434)"
    )
    
    args = parser.parse_args()
    
    # Initialize debugger
    debugger = K8sDebugger(ollama_host=args.ollama_host)
    
    # Pre-flight checks
    print("🚀 AI Kubernetes Pod Debugger")
    print("-" * 80)
    
    if not debugger.check_kubectl_installed():
        print("❌ kubectl is not installed!")
        print("Install with: brew install kubectl  (macOS)")
        print("            or: choco install kubernetes-cli  (Windows)")
        print("            or: apt-get install kubectl  (Ubuntu)")
        sys.exit(1)
    
    print("✅ kubectl installed")
    
    if not debugger.check_cluster_accessible():
        print("❌ Kubernetes cluster is not accessible!")
        print("Make sure Minikube is running: minikube start")
        print("Or check your cluster connection: kubectl cluster-info")
        sys.exit(1)
    
    print("✅ Cluster accessible")
    
    if not debugger.check_ollama_running():
        print("❌ Ollama is not running!")
        print("Start Ollama and run: ollama pull llama3.2")
        sys.exit(1)
    
    print("✅ Ollama running")
    print("-" * 80)
    
    # Get pods
    print(f"\n🔍 Scanning pods in namespace '{args.namespace}'...")
    pods = debugger.get_pods(args.namespace)
    
    if not pods:
        print(f"❌ No pods found in namespace '{args.namespace}'")
        sys.exit(1)
    
    # Filter pods to analyze
    if args.pod:
        # Analyze specific pod
        pods_to_analyze = [p for p in pods if p['name'] == args.pod]
        if not pods_to_analyze:
            print(f"❌ Pod '{args.pod}' not found in namespace '{args.namespace}'")
            sys.exit(1)
    elif args.all:
        # Analyze all unhealthy pods
        pods_to_analyze = [p for p in pods if not p['healthy']]
        if not pods_to_analyze:
            print(f"✅ Great news! All {len(pods)} pods are healthy!")
            return
    else:
        # Analyze unhealthy pods, or show status if all healthy
        pods_to_analyze = [p for p in pods if not p['healthy']]
        if not pods_to_analyze:
            print(f"\n✅ Great news! All {len(pods)} pods are healthy!")
            print("\nPod Status:")
            for pod in pods:
                print(f"  • {pod['name']}: {pod['status']} (Restarts: {pod['restarts']})")
            return
    
    print(f"\n⚠️  Found {len(pods_to_analyze)} unhealthy pod(s)")
    print(f"📋 Analyzing with AI...\n")
    
    # Analyze each unhealthy pod
    for i, pod in enumerate(pods_to_analyze, 1):
        if i > 1:
            print("\n" + "="*80 + "\n")
        
        print(f"🔍 Analyzing pod {i}/{len(pods_to_analyze)}: {pod['name']}")
        
        # Get logs and events
        print("   Fetching logs...")
        logs = debugger.get_pod_logs(pod['name'], args.namespace)
        
        print("   Fetching events...")
        events = debugger.get_pod_events(pod['name'], args.namespace)
        
        print("   Generating AI diagnosis...")
        diagnosis = debugger.analyze_pod_failure(pod, logs, events)
        
        # Print report
        debugger.print_pod_report(pod, diagnosis)
    
    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
