#!/usr/bin/env python3
"""
Demo script for AI Log Analyzer
Runs analysis on all 3 sample log files to demonstrate multi-format support
"""

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
SRC = BASE.parent / 'src' / 'log_analyzer.py'
LOGS = BASE / 'sample_logs'


def run(cmd, description):
    print(f"\n{'=' * 60}")
    print(f"  {description}")
    print(f"{'=' * 60}")
    print(f"$ {' '.join(str(c) for c in cmd)}\n")
    subprocess.run([sys.executable] + [str(c) for c in cmd])


def main():
    print("\n" + "=" * 60)
    print("  AI LOG ANALYZER - FULL DEMO")
    print("=" * 60)
    print("\nDemonstrating analysis of 3 different log formats:\n")
    print("  1. K8s failed deployment  (plain text)")
    print("  2. App payment errors     (JSON format)")
    print("  3. Docker OOMKilled crash (plain text)")
    print()

    # Demo 1: K8s failed deployment - save report
    run(
        [SRC, '--file', LOGS / 'k8s_failed_deployment.log', '--save-report'],
        "Demo 1: K8s Failed Deployment (saves report)"
    )

    # Demo 2: JSON format app errors
    run(
        [SRC, '--file', LOGS / 'app_errors.log'],
        "Demo 2: App Errors - JSON Format (auto-detected)"
    )

    # Demo 3: Docker OOMKilled crash
    run(
        [SRC, '--file', LOGS / 'docker_crash.log'],
        "Demo 3: Docker Container OOMKilled"
    )

    print("\n" + "=" * 60)
    print("  ✅ Demo complete!")
    print("  📁 Check log_reports/ for the saved K8s report")
    print("=" * 60)


if __name__ == "__main__":
    main()
