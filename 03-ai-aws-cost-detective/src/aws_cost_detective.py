#!/usr/bin/env python3
"""
AI AWS Cost Detective
Analyzes AWS costs and uses AI to identify waste and suggest optimizations.
"""

import boto3
import json
import sys
import argparse
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types from AWS."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class AWSCostDetective:
    """Main class that analyzes AWS costs and uses AI for recommendations."""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """
        Initialize the cost detective.
        
        Args:
            ollama_host: URL of Ollama API endpoint
        """
        self.ollama_host = ollama_host
        self.ollama_model = "llama3.2"
        self.ce_client = None
        
    def check_aws_credentials(self) -> bool:
        """Check if AWS credentials are configured."""
        try:
            sts = boto3.client('sts')
            sts.get_caller_identity()
            return True
        except Exception as e:
            print(f"❌ AWS credentials not configured: {e}")
            return False
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_cost_and_usage(self, days: int = 30) -> Dict:
        """
        Get AWS cost and usage data for the specified period.
        
        Args:
            days: Number of days to analyze (default 30)
            
        Returns:
            Dictionary containing cost data
        """
        try:
            self.ce_client = boto3.client('ce', region_name='us-east-1')
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get cost by service
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            return response
            
        except Exception as e:
            print(f"❌ Error fetching AWS cost data: {e}")
            return {}
    
    def parse_cost_data(self, cost_data: Dict) -> List[Dict]:
        """
        Parse AWS cost data into a simpler format.
        
        Args:
            cost_data: Raw cost data from AWS
            
        Returns:
            List of service costs
        """
        services = []
        
        try:
            for result in cost_data.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service_name = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    # Only include services with non-zero costs
                    if cost > 0.01:
                        services.append({
                            'service': service_name,
                            'cost': cost,
                            'period': result['TimePeriod']
                        })
            
            # Sort by cost (highest first)
            services.sort(key=lambda x: x['cost'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error parsing cost data: {e}")
        
        return services
    
    def get_resource_counts(self) -> Dict:
        """
        Get counts of various AWS resources across services.
        
        Returns:
            Dictionary with resource counts
        """
        resources = {
            'ec2_instances': 0,
            'ebs_volumes': 0,
            's3_buckets': 0,
            'rds_instances': 0,
            'lambda_functions': 0
        }
        
        try:
            # EC2 instances
            ec2 = boto3.client('ec2', region_name='us-east-1')
            instances = ec2.describe_instances()
            resources['ec2_instances'] = sum(
                len(r['Instances']) 
                for r in instances['Reservations']
            )
            
            # EBS volumes
            volumes = ec2.describe_volumes()
            resources['ebs_volumes'] = len(volumes['Volumes'])
            
            # S3 buckets
            s3 = boto3.client('s3')
            buckets = s3.list_buckets()
            resources['s3_buckets'] = len(buckets['Buckets'])
            
            # RDS instances
            try:
                rds = boto3.client('rds', region_name='us-east-1')
                databases = rds.describe_db_instances()
                resources['rds_instances'] = len(databases['DBInstances'])
            except:
                pass  # RDS might not be available in free tier
            
            # Lambda functions
            try:
                lambda_client = boto3.client('lambda', region_name='us-east-1')
                functions = lambda_client.list_functions()
                resources['lambda_functions'] = len(functions['Functions'])
            except:
                pass
                
        except Exception as e:
            print(f"⚠️  Warning: Could not fetch all resources: {e}")
        
        return resources
    
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
    
    def analyze_costs(self, services: List[Dict], resources: Dict) -> str:
        """
        Use AI to analyze costs and provide recommendations.
        
        Args:
            services: List of service costs
            resources: Resource counts
            
        Returns:
            AI analysis and recommendations
        """
        # Prepare cost summary
        total_cost = sum(s['cost'] for s in services)
        top_services = services[:5]  # Top 5 most expensive
        
        # Build context for AI
        services_text = "\n".join([
            f"- {s['service']}: ${s['cost']:.2f}"
            for s in top_services
        ])
        
        resources_text = "\n".join([
            f"- {k.replace('_', ' ').title()}: {v}"
            for k, v in resources.items()
        ])
        
        prompt = f"""You are an AWS cost optimization expert analyzing a user's AWS bill.

COST SUMMARY (Last 30 Days):
Total Cost: ${total_cost:.2f}

Top 5 Services by Cost:
{services_text}

Resources Currently Running:
{resources_text}

Provide cost optimization recommendations in this format:

**COST ANALYSIS:**
[Summarize the spending pattern in 1-2 sentences - what's expensive and why]

**HIDDEN COSTS DETECTED:**
[List 2-3 specific areas where money is being wasted, use bullet points]

**OPTIMIZATION RECOMMENDATIONS:**
[Provide 3-4 actionable steps to reduce costs, be specific with AWS service names and features]

**ESTIMATED SAVINGS:**
[Estimate potential monthly savings if recommendations are followed]

Keep it practical and specific. If costs are low (under $10), acknowledge they're doing well but still suggest optimizations for when they scale."""

        return self.ask_ollama(prompt)
    
    def generate_savings_tips(self, service_name: str, cost: float) -> str:
        """
        Generate specific savings tips for a service.
        
        Args:
            service_name: AWS service name
            cost: Monthly cost
            
        Returns:
            Specific tips for that service
        """
        prompt = f"""You are an AWS cost expert. A user is spending ${cost:.2f}/month on {service_name}.

Provide 2-3 specific, actionable tips to reduce costs for this service. Be brief (max 3 sentences total).

Examples:
- For EC2: "Use t3.micro instead of t3.small, enable auto-scaling, use spot instances"
- For S3: "Enable lifecycle policies to move old data to Glacier, delete incomplete multipart uploads"
- For RDS: "Use Aurora Serverless for variable workloads, enable automated backups retention reduction"

Your tips:"""

        return self.ask_ollama(prompt)
    
    def print_cost_report(self, services: List[Dict], resources: Dict, analysis: str):
        """
        Print formatted cost analysis report.
        
        Args:
            services: Service costs
            resources: Resource counts
            analysis: AI analysis
        """
        total_cost = sum(s['cost'] for s in services)
        
        print("\n" + "="*80)
        print(f"💰 AWS COST DETECTIVE REPORT")
        print("="*80)
        print(f"Analysis Period: Last 30 days")
        print(f"Total Cost: ${total_cost:.2f}")
        print(f"Number of Services: {len(services)}")
        print("="*80)
        
        # Resources summary
        print("\n📊 RESOURCES IN USE:")
        print("-" * 80)
        for key, value in resources.items():
            resource_name = key.replace('_', ' ').title()
            print(f"  • {resource_name}: {value}")
        
        # Cost breakdown
        print("\n💵 TOP 5 SERVICES BY COST:")
        print("-" * 80)
        for i, service in enumerate(services[:5], 1):
            percentage = (service['cost'] / total_cost * 100) if total_cost > 0 else 0
            print(f"  {i}. {service['service']}: ${service['cost']:.2f} ({percentage:.1f}%)")
        
        # AI Analysis
        print("\n🤖 AI COST ANALYSIS:")
        print("-" * 80)
        print(analysis)
        print("-" * 80)
        
        print("\n" + "="*80)
    
    def save_report(self, services: List[Dict], resources: Dict, 
                   analysis: str, filename: str):
        """
        Save cost report to JSON file.
        
        Args:
            services: Service costs
            resources: Resource counts
            analysis: AI analysis
            filename: Output filename
        """
        total_cost = sum(s['cost'] for s in services)
        
        report = {
            "report_date": datetime.now().isoformat(),
            "total_cost": total_cost,
            "analysis_period_days": 30,
            "resources": resources,
            "services": services,
            "ai_analysis": analysis
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, cls=DecimalEncoder)
        
        print(f"\n💾 Report saved to: {filename}")


def main():
    """Main entry point for the cost detective."""
    parser = argparse.ArgumentParser(
        description="AI AWS Cost Detective - Analyze and optimize AWS costs"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)"
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
    
    # Initialize detective
    detective = AWSCostDetective(ollama_host=args.ollama_host)
    
    # Pre-flight checks
    print("💰 AI AWS Cost Detective")
    print("-" * 80)
    
    if not detective.check_aws_credentials():
        print("❌ AWS credentials not configured!")
        print("\nSetup AWS credentials:")
        print("1. Install AWS CLI: pip install awscli")
        print("2. Configure: aws configure")
        print("3. Enter your Access Key ID and Secret Access Key")
        print("\nOr set environment variables:")
        print("  export AWS_ACCESS_KEY_ID='your-key'")
        print("  export AWS_SECRET_ACCESS_KEY='your-secret'")
        sys.exit(1)
    
    print("✅ AWS credentials configured")
    
    if not detective.check_ollama_running():
        print("❌ Ollama is not running!")
        print("Start Ollama and run: ollama pull llama3.2")
        sys.exit(1)
    
    print("✅ Ollama running")
    print("-" * 80)
    
    # Fetch cost data
    print(f"\n💵 Fetching AWS costs for last {args.days} days...")
    cost_data = detective.get_cost_and_usage(args.days)
    
    if not cost_data:
        print("❌ Could not fetch cost data!")
        sys.exit(1)
    
    # Parse costs
    services = detective.parse_cost_data(cost_data)
    
    if not services:
        print("\n✅ Great news! No AWS costs detected in the last 30 days!")
        print("🎉 You're either using free tier perfectly or haven't deployed anything yet.")
        return
    
    # Get resource counts
    print("📊 Analyzing AWS resources...")
    resources = detective.get_resource_counts()
    
    # AI analysis
    print("🤖 Generating AI cost analysis...\n")
    analysis = detective.analyze_costs(services, resources)
    
    # Print report
    detective.print_cost_report(services, resources, analysis)
    
    # Save if requested
    if args.output:
        detective.save_report(services, resources, analysis, args.output)
    
    print("\n✅ Analysis complete!")
    print("\n💡 TIP: Run this monthly to track cost trends and catch waste early!")
    print("="*80)


if __name__ == "__main__":
    main()
