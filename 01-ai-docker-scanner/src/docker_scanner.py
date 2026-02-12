#!/usr/bin/env python3
"""
AI Docker Security Scanner
Scans Docker images for vulnerabilities and uses AI to explain them in plain English.
"""

import subprocess
import json
import sys
import argparse
from typing import Dict, List, Optional
import requests
from datetime import datetime


class DockerScanner:
    """Main scanner class that orchestrates Trivy scanning and AI analysis."""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """
        Initialize the scanner.
        
        Args:
            ollama_host: URL of Ollama API endpoint
        """
        self.ollama_host = ollama_host
        self.ollama_model = "llama3.2"
        
    def check_trivy_installed(self) -> bool:
        """Check if Trivy is installed and accessible."""
        try:
            result = subprocess.run(
                ["trivy", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def scan_image(self, image_name: str) -> Optional[Dict]:
        """
        Scan Docker image using Trivy.
        
        Args:
            image_name: Name of the Docker image to scan
            
        Returns:
            Dictionary containing scan results or None if scan failed
        """
        # Check if image exists locally
        check_local = subprocess.run(
            ["docker", "images", "-q", image_name],
            capture_output=True,
            text=True,
            check=False
        )
        
        if check_local.stdout.strip():
            print(f"✅ Using local image")
        else:
            print(f"⚠️  Image not found locally - Trivy will download from registry")
            print(f"💡 Tip: Run 'docker pull {image_name}' first for faster scans")
        
        print(f"🔍 Scanning image: {image_name}...")
        
        try:
            # Run Trivy scan with JSON output
            result = subprocess.run(
                [
                    "trivy",
                    "image",
                    "--format", "json",
                    "--severity", "HIGH,CRITICAL",
                    image_name
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            scan_data = json.loads(result.stdout)
            return scan_data
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error scanning image: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing scan results: {e}")
            return None
    
    def extract_vulnerabilities(self, scan_data: Dict) -> List[Dict]:
        """
        Extract vulnerability information from Trivy scan results.

        Args:
            scan_data: Raw scan data from Trivy

        Returns:
            List of vulnerability dictionaries (deduplicated by vulnerability ID)
        """
        vulnerabilities = []
        seen_vulns = set()  # Track unique vulnerability IDs

        # Trivy results are in "Results" array
        for result in scan_data.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                vuln_id = vuln.get("VulnerabilityID", "N/A")

                # Skip if we've already seen this vulnerability ID
                if vuln_id in seen_vulns:
                    continue

                seen_vulns.add(vuln_id)
                vulnerabilities.append({
                    "id": vuln_id,
                    "package": vuln.get("PkgName", "N/A"),
                    "version": vuln.get("InstalledVersion", "N/A"),
                    "severity": vuln.get("Severity", "N/A"),
                    "title": vuln.get("Title", "N/A"),
                    "description": vuln.get("Description", "N/A"),
                    "fixed_version": vuln.get("FixedVersion", "Not available")
                })

        return vulnerabilities
    
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
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: AI returned status code {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"Error communicating with AI: {e}"
    
    def explain_vulnerability(self, vuln: Dict) -> str:
        """
        Use AI to explain a vulnerability in plain English.
        
        Args:
            vuln: Vulnerability dictionary
            
        Returns:
            AI explanation as string
        """
        prompt = f"""You are a security expert explaining vulnerabilities to developers.

Vulnerability Details:
- ID: {vuln['id']}
- Package: {vuln['package']} (version {vuln['version']})
- Severity: {vuln['severity']}
- Title: {vuln['title']}

Explain in 2-3 sentences:
1. What this vulnerability means in simple terms
2. Why it's dangerous
3. How to fix it (fixed version: {vuln['fixed_version']})

Keep it concise and actionable. Use analogies if helpful."""

        return self.ask_ollama(prompt)
    
    def generate_summary(self, image_name: str, vulnerabilities: List[Dict]) -> str:
        """
        Generate an overall security summary using AI.
        
        Args:
            image_name: Name of the scanned image
            vulnerabilities: List of found vulnerabilities
            
        Returns:
            AI summary as string
        """
        critical_count = sum(1 for v in vulnerabilities if v['severity'] == 'CRITICAL')
        high_count = sum(1 for v in vulnerabilities if v['severity'] == 'HIGH')
        
        # Extract common packages with issues
        vulnerable_packages = list(set(v['package'] for v in vulnerabilities[:3]))
        
        prompt = f"""You are a security consultant reviewing a Docker image scan.

Image: {image_name}
Total vulnerabilities: {len(vulnerabilities)}
- Critical: {critical_count}
- High: {high_count}

Main vulnerable packages: {', '.join(vulnerable_packages)}

Provide your response in this EXACT format:

SECURITY_POSTURE: [one of: "good", "concerning", "critical"]
VULNERABLE_PACKAGES: [list the top 2-3 problem packages]
REMEDIATION: [general strategy - one sentence]
VARIANTS_TO_TEST: [comma-separated list of 2-3 image variants to compare, e.g., "alpine,slim,distroless" or "ubuntu,bookworm-slim" - choose based on what would likely help]

Important:
- For VARIANTS_TO_TEST, suggest realistic Docker image variants (alpine, slim, distroless, ubuntu, bookworm-slim, etc.)
- Don't suggest specific version numbers
- Choose variants appropriate for the base image type"""

        ai_response = self.ask_ollama(prompt)
        
        # Parse the structured response
        lines = ai_response.strip().split('\n')
        parsed = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                parsed[key.strip()] = value.strip()
        
        # Extract base image name (e.g., "nginx" from "nginx:latest")
        base_image = image_name.split(':')[0]
        
        # Build human-readable summary
        summary_parts = []
        if 'SECURITY_POSTURE' in parsed:
            summary_parts.append(f"Security posture: {parsed['SECURITY_POSTURE']}")
        if 'VULNERABLE_PACKAGES' in parsed:
            summary_parts.append(f"Main issues in: {parsed['VULNERABLE_PACKAGES']}")
        if 'REMEDIATION' in parsed:
            summary_parts.append(f"Recommendation: {parsed['REMEDIATION']}")
        
        summary = ". ".join(summary_parts) + "."
        
        # Add comparison command with AI-suggested variants
        if 'VARIANTS_TO_TEST' in parsed:
            variants = parsed['VARIANTS_TO_TEST'].strip('[]').split(',')
            variants = [v.strip() for v in variants if v.strip()]
            
            # Build comparison command
            variant_args = ' '.join([f"{base_image}:{v}" for v in variants])
            comparison_cmd = f"\n\nTo compare variants, run:\n    python src/compare_images.py {image_name} {variant_args}"
        else:
            # Fallback if parsing fails
            comparison_cmd = f"\n\nTo compare variants, run:\n    python src/compare_images.py {image_name} {base_image}:alpine {base_image}:slim"
        
        return summary + comparison_cmd
    
    def print_report(self, image_name: str, vulnerabilities: List[Dict], summary: str):
        """
        Print formatted security report to console.
        
        Args:
            image_name: Name of the scanned image
            vulnerabilities: List of vulnerabilities
            summary: AI-generated summary
        """
        print("\n" + "="*80)
        print(f"🛡️  AI DOCKER SECURITY REPORT")
        print("="*80)
        print(f"Image: {image_name}")
        print(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Vulnerabilities: {len(vulnerabilities)}")
        print("="*80)
        
        # AI Summary
        print("\n📊 AI SECURITY SUMMARY:")
        print("-" * 80)
        print(summary)
        print("-" * 80)
        
        # Vulnerability details
        print(f"\n🔍 VULNERABILITY DETAILS ({len(vulnerabilities)} found):")
        print("="*80)
        
        for i, vuln in enumerate(vulnerabilities, 1):
            print(f"\n[{i}] {vuln['severity']} - {vuln['id']}")
            print(f"    Package: {vuln['package']} ({vuln['version']})")
            print(f"    Fixed in: {vuln['fixed_version']}")
            print(f"\n    🤖 AI Explanation:")
            print()  # Add blank line after heading

            # Get AI explanation
            explanation = self.explain_vulnerability(vuln)
            for line in explanation.split('\n'):
                if line.strip():
                    # Add spacing before numbered points
                    if line.strip().startswith(('**1.', '**2.', '**3.')):
                        print()  # Blank line before each numbered point
                    print(f"    {line.strip()}")

            print()  # Add blank line before divider
            print("-" * 80)
    
    def save_report(self, image_name: str, vulnerabilities: List[Dict], 
                   summary: str, filename: str):
        """
        Save report to a JSON file.
        
        Args:
            image_name: Name of the scanned image
            vulnerabilities: List of vulnerabilities
            summary: AI-generated summary
            filename: Output filename
        """
        report = {
            "image": image_name,
            "scan_date": datetime.now().isoformat(),
            "summary": summary,
            "total_vulnerabilities": len(vulnerabilities),
            "vulnerabilities": vulnerabilities
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to: {filename}")


def main():
    """Main entry point for the scanner."""
    parser = argparse.ArgumentParser(
        description="AI Docker Security Scanner - Scan images and get AI explanations"
    )
    parser.add_argument(
        "image",
        help="Docker image to scan (e.g., nginx:latest)"
    )
    parser.add_argument(
        "--ollama-host",
        default="http://localhost:11434",
        help="Ollama API host (default: http://localhost:11434)"
    )
    parser.add_argument(
        "--output",
        help="Save report to JSON file"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Limit number of vulnerabilities to analyze (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Initialize scanner
    scanner = DockerScanner(ollama_host=args.ollama_host)
    
    # Pre-flight checks
    print("🚀 AI Docker Security Scanner")
    print("-" * 80)
    
    if not scanner.check_trivy_installed():
        print("❌ Trivy is not installed!")
        print("Install with: brew install trivy  (macOS)")
        print("            or: apt-get install trivy  (Ubuntu)")
        sys.exit(1)
    
    print("✅ Trivy installed")
    
    if not scanner.check_ollama_running():
        print("❌ Ollama is not running!")
        print("Start Ollama and run: ollama pull llama3.2")
        sys.exit(1)
    
    print("✅ Ollama running")
    print("-" * 80)
    
    # Scan image
    scan_data = scanner.scan_image(args.image)
    if not scan_data:
        print("❌ Scan failed!")
        sys.exit(1)
    
    # Extract vulnerabilities
    all_vulnerabilities = scanner.extract_vulnerabilities(scan_data)
    
    if not all_vulnerabilities:
        print("\n✅ Great news! No HIGH or CRITICAL vulnerabilities found!")
        print(f"🎉 {args.image} appears to be secure!")
        return
    
    # Limit vulnerabilities for AI analysis
    vulnerabilities = all_vulnerabilities[:args.limit]
    
    print(f"\n⚠️  Found {len(all_vulnerabilities)} vulnerabilities")
    print(f"📋 Analyzing top {len(vulnerabilities)} with AI...\n")
    
    # Generate AI summary
    print("🤖 Generating AI security summary...")
    summary = scanner.generate_summary(args.image, all_vulnerabilities)
    
    # Print report
    scanner.print_report(args.image, vulnerabilities, summary)
    
    # Save report if requested
    if args.output:
        scanner.save_report(args.image, vulnerabilities, summary, args.output)
    
    print("\n" + "="*80)
    print("✅ Scan complete!")
    print("="*80)


if __name__ == "__main__":
    main()