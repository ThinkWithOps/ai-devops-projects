#!/usr/bin/env python3
"""
AI Terraform Code Generator
Generates Terraform/OpenTofu infrastructure code using AI based on natural language descriptions.
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Optional
from datetime import datetime


class TerraformGenerator:
    """Main class that generates Terraform code using AI."""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """
        Initialize the Terraform generator.
        
        Args:
            ollama_host: URL of Ollama API endpoint
        """
        self.ollama_host = ollama_host
        self.ollama_model = "llama3.2"
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
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
                timeout=300
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: AI returned status code {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"Error communicating with AI: {e}"
    
    def generate_terraform(self, 
                          description: str,
                          provider: str = "aws",
                          include_variables: bool = True) -> Dict[str, str]:
        """
        Generate Terraform code based on natural language description.
        
        Args:
            description: Natural language description of infrastructure
            provider: Cloud provider (aws, azure, gcp)
            include_variables: Whether to generate variables.tf
            
        Returns:
            Dictionary with filenames as keys and Terraform code as values
        """
        
        # Build comprehensive prompt
        prompt = f"""You are a Terraform/OpenTofu expert. Generate production-ready infrastructure code.

USER REQUEST:
{description}

PROVIDER: {provider}

Generate complete, working Terraform code with these files:

1. main.tf - Main infrastructure resources
2. variables.tf - Input variables with descriptions
3. outputs.tf - Output values
4. terraform.tfvars.example - Example variable values

REQUIREMENTS:
- Use Terraform 1.0+ syntax
- Include proper resource dependencies
- Add comments explaining each resource
- Use variables for configurable values
- Follow best practices (tagging, naming conventions)
- Include data sources where appropriate
- Add validation for variables
- Use locals for computed values

CRITICAL: 
- Generate ONLY valid Terraform/HCL code
- NO markdown formatting or code blocks
- Start each file with a comment showing the filename
- Separate files with: ### FILENAME ###

Format your response like this:

### main.tf ###
# Main infrastructure configuration
# Description of what this file does

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    {provider} = {{
      source  = "hashicorp/{provider}"
      version = "~> 5.0"
    }}
  }}
}}

[rest of main.tf code]

### variables.tf ###
# Input variables
# Configurable parameters

[variables code]

### outputs.tf ###
# Output values
# Exported information

[outputs code]

### terraform.tfvars.example ###
# Example variable values
# Copy to terraform.tfvars and customize

[example values]

Generate production-ready code now:"""

        print("🤖 Generating Terraform code with AI...")
        ai_response = self.ask_ollama(prompt)
        
        # Parse AI response into separate files
        files = self.parse_terraform_files(ai_response)
        
        return files
    
    def parse_terraform_files(self, ai_response: str) -> Dict[str, str]:
        """
        Parse AI response into separate Terraform files.
        
        Args:
            ai_response: Full AI response
            
        Returns:
            Dictionary mapping filenames to code content
        """
        files = {}
        
        # Split by file markers
        sections = ai_response.split("###")
        
        current_filename = None
        current_content = []
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if this is a filename marker
            if any(ext in section.lower() for ext in ['.tf', '.tfvars', '.hcl']):
                # Save previous file
                if current_filename and current_content:
                    files[current_filename] = '\n'.join(current_content).strip()
                
                # Extract new filename
                lines = section.split('\n')
                current_filename = lines[0].strip()
                current_content = lines[1:] if len(lines) > 1 else []
            else:
                # Add to current file content
                current_content.append(section)
        
        # Save last file
        if current_filename and current_content:
            files[current_filename] = '\n'.join(current_content).strip()
        
        # If parsing failed, try simple approach
        if not files:
            # Look for common filenames
            for filename in ['main.tf', 'variables.tf', 'outputs.tf', 'terraform.tfvars.example']:
                if filename in ai_response.lower():
                    # Extract content after filename until next file or end
                    start = ai_response.lower().find(filename)
                    end = len(ai_response)
                    
                    # Find next filename
                    for next_file in ['main.tf', 'variables.tf', 'outputs.tf', 'terraform.tfvars.example']:
                        if next_file != filename:
                            next_pos = ai_response.lower().find(next_file, start + len(filename))
                            if next_pos > start and next_pos < end:
                                end = next_pos
                    
                    content = ai_response[start:end]
                    # Remove filename from content
                    content = content.replace(filename, '', 1).strip()
                    # Remove markdown code blocks if present
                    content = content.replace('```hcl', '').replace('```terraform', '').replace('```', '')
                    files[filename] = content.strip()
        
        # If still no files, put everything in main.tf
        if not files:
            files['main.tf'] = ai_response.strip()
        
        return files
    
    def save_files(self, files: Dict[str, str], output_dir: str = "generated"):
        """
        Save generated Terraform files to disk.
        
        Args:
            files: Dictionary of filename -> content
            output_dir: Directory to save files in
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        
        for filename, content in files.items():
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            saved_files.append(filepath)
            print(f"  ✅ {filepath}")
        
        return saved_files
    
    def validate_terraform(self, directory: str) -> bool:
        """
        Validate generated Terraform code (if terraform is installed).
        
        Args:
            directory: Directory containing Terraform files
            
        Returns:
            True if validation passed, False otherwise
        """
        try:
            import subprocess
            
            # Check if terraform is installed
            result = subprocess.run(
                ['terraform', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False
            
            # Run terraform init
            print(f"\n🔍 Initializing Terraform in {directory}...")
            result = subprocess.run(
                ['terraform', 'init'],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"❌ Terraform init failed:\n{result.stderr}")
                return False
            
            # Run terraform validate
            print("✅ Running terraform validate...")
            result = subprocess.run(
                ['terraform', 'validate'],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Terraform validation passed!")
                return True
            else:
                print(f"❌ Terraform validation failed:\n{result.stderr}")
                return False
                
        except FileNotFoundError:
            print("⚠️  Terraform not installed - skipping validation")
            print("   Install from: https://www.terraform.io/downloads")
            return False
        except Exception as e:
            print(f"⚠️  Validation error: {e}")
            return False
    
    def print_summary(self, files: Dict[str, str], output_dir: str):
        """
        Print summary of generated files.
        
        Args:
            files: Generated files
            output_dir: Output directory
        """
        print("\n" + "="*80)
        print("🎉 TERRAFORM CODE GENERATED")
        print("="*80)
        print(f"Output Directory: {output_dir}/")
        print(f"Files Created: {len(files)}")
        print("="*80)
        
        for filename in sorted(files.keys()):
            line_count = len(files[filename].split('\n'))
            print(f"  📄 {filename:<30} ({line_count} lines)")
        
        print("="*80)
        print("\n💡 NEXT STEPS:")
        print(f"  1. Review the generated code in {output_dir}/")
        print("  2. Update terraform.tfvars with your values")
        print("  3. Run: terraform init")
        print("  4. Run: terraform plan")
        print("  5. Run: terraform apply")
        print("\n⚠️  IMPORTANT:")
        print("  - Review ALL generated code before applying")
        print("  - Understand costs of resources being created")
        print("  - Test in a dev environment first")
        print("="*80)


def main():
    """Main entry point for the Terraform generator."""
    parser = argparse.ArgumentParser(
        description="AI Terraform Code Generator - Generate IaC from natural language"
    )
    parser.add_argument(
        "--description",
        "-d",
        required=True,
        help="Natural language description of infrastructure (e.g., 'Create an EC2 instance with S3 bucket')"
    )
    parser.add_argument(
        "--provider",
        "-p",
        default="aws",
        choices=["aws", "azure", "gcp"],
        help="Cloud provider (default: aws)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="generated",
        help="Output directory for generated files (default: generated)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated code with terraform validate (requires terraform installed)"
    )
    parser.add_argument(
        "--ollama-host",
        default="http://localhost:11434",
        help="Ollama API host (default: http://localhost:11434)"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = TerraformGenerator(ollama_host=args.ollama_host)
    
    # Pre-flight checks
    print("🔧 AI Terraform Code Generator")
    print("-" * 80)
    
    if not generator.check_ollama_running():
        print("❌ Ollama is not running!")
        print("Start Ollama and run: ollama pull llama3.2")
        sys.exit(1)
    
    print("✅ Ollama running")
    print("-" * 80)
    
    print(f"\n📝 Request: {args.description}")
    print(f"☁️  Provider: {args.provider}")
    print(f"📂 Output: {args.output}/")
    print()
    
    # Generate Terraform code
    files = generator.generate_terraform(
        description=args.description,
        provider=args.provider
    )
    
    if not files:
        print("❌ Failed to generate Terraform code!")
        sys.exit(1)
    
    # Save files
    print("\n💾 Saving files:")
    generator.save_files(files, args.output)
    
    # Validate if requested
    if args.validate:
        generator.validate_terraform(args.output)
    
    # Print summary
    generator.print_summary(files, args.output)
    
    print("\n✅ Generation complete!")


if __name__ == "__main__":
    main()
