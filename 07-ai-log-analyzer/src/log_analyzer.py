#!/usr/bin/env python3
"""
AI Log Analyzer
Parses Docker/K8s/App logs, identifies errors with AI, suggests root causes and fixes
"""

import argparse
import json
import os
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
import subprocess

# Regex patterns
SEVERITY_PATTERN = re.compile(r'\b(CRITICAL|FATAL|ERROR|WARN|WARNING|INFO|DEBUG)\b', re.IGNORECASE)
TIMESTAMP_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}')
SYSLOG_PATTERN = re.compile(r'^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.*)')

K8S_ERROR_TERMS = re.compile(
    r'(CrashLoopBackOff|OOMKilled|ImagePullBackOff|ErrImagePull|'
    r'Evicted|Failed|Error|Unhealthy|BackOff|Pending)', re.IGNORECASE
)

SEVERITY_RANK = {
    'CRITICAL': 0, 'FATAL': 0,
    'ERROR': 1,
    'WARNING': 2, 'WARN': 2,
    'INFO': 3,
    'DEBUG': 4,
}


# ─── Format Detection ───────────────────────────────────────────────────────

def detect_format(filepath):
    """Auto-detect log format from first non-empty line"""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
                return 'json'
            except json.JSONDecodeError:
                pass
            if SYSLOG_PATTERN.match(line):
                return 'syslog'
            return 'text'
    return 'text'


# ─── Parsers ────────────────────────────────────────────────────────────────

def _make_entry(line_num, raw, severity='INFO', timestamp=None, message=None):
    return {
        'line': line_num,
        'raw': raw,
        'severity': severity,
        'timestamp': timestamp,
        'message': message or raw,
    }


def _normalize_severity(sev):
    sev = sev.upper()
    return 'WARNING' if sev == 'WARN' else sev


def parse_text_log(filepath):
    """Parse plain text / K8s style logs"""
    entries = []
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            entry = _make_entry(line_num, line)

            sev_match = SEVERITY_PATTERN.search(line)
            if sev_match:
                entry['severity'] = _normalize_severity(sev_match.group(1))
            elif K8S_ERROR_TERMS.search(line):
                entry['severity'] = 'ERROR'

            ts_match = TIMESTAMP_PATTERN.search(line)
            if ts_match:
                entry['timestamp'] = ts_match.group(0)

            entries.append(entry)
    return entries


def parse_json_log(filepath):
    """Parse JSON log format (one JSON object per line)"""
    entries = []
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)

                severity = 'INFO'
                for field in ['level', 'severity', 'log_level', 'lvl']:
                    if field in data:
                        severity = _normalize_severity(str(data[field]))
                        break

                message = line
                for field in ['message', 'msg', 'text', 'log']:
                    if field in data:
                        message = str(data[field])
                        break

                timestamp = None
                for field in ['timestamp', 'time', 'ts', '@timestamp']:
                    if field in data:
                        timestamp = str(data[field])
                        break

                entries.append(_make_entry(line_num, line, severity, timestamp, message))

            except json.JSONDecodeError:
                entries.append(_make_entry(line_num, line))

    return entries


def parse_syslog(filepath):
    """Parse syslog format"""
    entries = []
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            entry = _make_entry(line_num, line)

            match = SYSLOG_PATTERN.match(line)
            if match:
                entry['timestamp'] = match.group(1)
                entry['message'] = match.group(4)

            sev_match = SEVERITY_PATTERN.search(line)
            if sev_match:
                entry['severity'] = _normalize_severity(sev_match.group(1))
            elif K8S_ERROR_TERMS.search(line):
                entry['severity'] = 'ERROR'

            entries.append(entry)
    return entries


# ─── Analysis ───────────────────────────────────────────────────────────────

def categorize_entries(entries):
    """Group log entries by severity"""
    categories = {'CRITICAL': [], 'ERROR': [], 'WARNING': [], 'INFO': [], 'DEBUG': []}
    for entry in entries:
        sev = entry.get('severity', 'INFO')
        categories.setdefault(sev, []).append(entry)
    return categories


def identify_patterns(entries):
    """Find recurring error/warning messages"""
    error_entries = [e for e in entries if e['severity'] in ('CRITICAL', 'FATAL', 'ERROR', 'WARNING')]
    if not error_entries:
        return []

    normalized = []
    for e in error_entries:
        msg = e['message']
        msg = TIMESTAMP_PATTERN.sub('<timestamp>', msg)
        msg = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '<ip>', msg)
        msg = re.sub(r'[a-f0-9]{8,}', '<hash>', msg)
        # Normalize K8s pod/replicaset hashes (5+ alphanumeric after dash containing digits)
        msg = re.sub(r'-([a-z0-9]{5,})',
                     lambda m: '-<id>' if any(c.isdigit() for c in m.group(1)) else m.group(0),
                     msg)
        msg = re.sub(r'\b\d+\b', '<N>', msg)
        normalized.append(msg)

    patterns = []
    for msg, count in Counter(normalized).most_common(5):
        if count > 1:
            patterns.append({'message': msg, 'count': count})
    return patterns


# ─── Ollama ─────────────────────────────────────────────────────────────────

def check_ollama():
    """Verify Ollama is running and llama3.2 is available"""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            print("❌ Ollama is not running. Please start Ollama first.")
            print("   Windows: Start Ollama from Start Menu")
            print("   Mac/Linux: Run 'ollama serve' in another terminal")
            sys.exit(1)
        if 'llama3.2' not in result.stdout and 'llama3.3' not in result.stdout:
            print("⚠️  llama3.2 not found. Installing...")
            subprocess.run(['ollama', 'pull', 'llama3.2'], check=True)
        return True
    except FileNotFoundError:
        print("❌ Ollama not found. Visit: https://ollama.ai/download")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("❌ Ollama not responding. Please restart Ollama.")
        sys.exit(1)


def call_ollama(prompt, model="llama3.2"):
    """Send prompt to Ollama and return response"""
    try:
        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True, text=True,
            encoding='utf-8', timeout=180
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "AI analysis timed out. Please try again."
    except Exception as e:
        return f"AI analysis error: {str(e)}"


def analyze_with_ai(categories, patterns, filename):
    """Build prompt from log summary and call Ollama"""
    criticals = categories.get('CRITICAL', []) + categories.get('FATAL', [])
    errors = categories.get('ERROR', [])
    warnings = categories.get('WARNING', [])
    total = sum(len(v) for v in categories.values())

    sample_lines = []
    for entry in (criticals + errors)[:10]:
        sample_lines.append(f"  [{entry['severity']}] Line {entry['line']}: {entry['message'][:200]}")

    pattern_text = ""
    if patterns:
        pattern_text = "\nRecurring Patterns:\n"
        for p in patterns:
            pattern_text += f"  - Seen {p['count']}x: {p['message'][:150]}\n"

    prompt = f"""You are a DevOps expert analyzing log files. Analyze these log errors and provide:

1. Root Cause Analysis (what went wrong and why)
2. Immediate Fix Steps (specific commands or actions)
3. Prevention Measures (how to avoid this in future)

Log File: {filename}
Total Lines: {total}
Critical/Fatal: {len(criticals)} | Errors: {len(errors)} | Warnings: {len(warnings)}

Sample Error Messages:
{chr(10).join(sample_lines)}{pattern_text}

Provide a concise analysis with specific, actionable steps. Focus on the most impactful issues."""

    return call_ollama(prompt)


# ─── Report ──────────────────────────────────────────────────────────────────

def generate_report(filename, entries, categories, patterns, ai_analysis):
    """Generate markdown report"""
    criticals = categories.get('CRITICAL', []) + categories.get('FATAL', [])
    errors = categories.get('ERROR', [])
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines = [
        "# Log Analysis Report",
        f"\n**File:** `{filename}`",
        f"**Analyzed:** {timestamp}",
        f"**Total Lines:** {len(entries)}",
        "\n## Summary",
        "| Severity | Count |",
        "|----------|-------|",
        f"| 🔴 CRITICAL | {len(criticals)} |",
        f"| 🟠 ERROR | {len(errors)} |",
        f"| 🟡 WARNING | {len(categories.get('WARNING', []))} |",
        f"| 🔵 INFO | {len(categories.get('INFO', []))} |",
    ]

    if patterns:
        lines.append("\n## Recurring Patterns")
        for p in patterns:
            lines.append(f"- **{p['count']}x:** `{p['message'][:120]}`")

    lines.append("\n## AI Root Cause Analysis")
    lines.append(ai_analysis)

    if criticals or errors:
        lines.append("\n## Critical & Error Lines")
        for entry in (criticals + errors)[:25]:
            lines.append(f"- **Line {entry['line']}:** `{entry['message'][:150]}`")

    return "\n".join(lines)


def save_report(filename, entries, categories, patterns, ai_analysis):
    """Save report to log_reports/ directory"""
    report_dir = Path("log_reports")
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_dir / f"report_{timestamp}.md"
    content = generate_report(filename, entries, categories, patterns, ai_analysis)
    report_file.write_text(content, encoding='utf-8')
    return report_file


# ─── Simulate ────────────────────────────────────────────────────────────────

SIMULATED_LOGS = {
    'k8s': {
        'filename': 'k8s_failed_deployment.log',
        'format': 'text',
        'content': """\
2024-01-15T10:23:41Z INFO Starting deployment: api-server v2.1.0
2024-01-15T10:23:42Z INFO Pulling image: registry.company.com/api-server:v2.1.0
2024-01-15T10:23:55Z WARNING Slow image pull detected (>10s)
2024-01-15T10:24:10Z ERROR Failed to pull image "registry.company.com/api-server:v2.1.0": rpc error: code = Unknown desc = failed to pull and unpack image: unexpected status code 401 Unauthorized
2024-01-15T10:24:10Z ERROR Error: ErrImagePull - pod api-server-7d9f8b-xk2pq
2024-01-15T10:24:30Z WARNING Back-off pulling image "registry.company.com/api-server:v2.1.0" - ImagePullBackOff
2024-01-15T10:24:30Z ERROR pod/api-server-7d9f8b-xk2pq: ImagePullBackOff
2024-01-15T10:24:31Z ERROR pod/api-server-7d9f8b-xp9mn: ImagePullBackOff
2024-01-15T10:24:32Z ERROR pod/api-server-7d9f8b-rt4lx: ImagePullBackOff
2024-01-15T10:24:45Z CRITICAL Deployment api-server: 0/3 pods ready (timeout: 60s)
2024-01-15T10:24:46Z ERROR Liveness probe failed: connection refused - pod api-server-7d9f8b-xk2pq
2024-01-15T10:24:50Z CRITICAL Service api-server unhealthy: no endpoints available
2024-01-15T10:25:00Z CRITICAL Deployment api-server failed: pods not ready after 60s
2024-01-15T10:25:01Z ERROR Initiating rollback: deployment api-server to revision 5
2024-01-15T10:25:02Z WARNING Rolling back to: registry.company.com/api-server:v2.0.9
2024-01-15T10:25:10Z ERROR Rollback failed: insufficient replica history
2024-01-15T10:25:11Z CRITICAL Service api-server: 0 healthy endpoints - ALL PODS FAILING
""",
    },
    'app': {
        'filename': 'app_errors.log',
        'format': 'json',
        'content': """\
{"timestamp":"2024-01-15T14:00:01Z","level":"INFO","service":"payment-api","message":"Server started on port 8080"}
{"timestamp":"2024-01-15T14:01:23Z","level":"INFO","service":"payment-api","message":"Processing payment request","user_id":"u_12345"}
{"timestamp":"2024-01-15T14:01:24Z","level":"ERROR","service":"payment-api","message":"Database connection failed: timeout after 30s","db_host":"postgres-primary:5432"}
{"timestamp":"2024-01-15T14:01:24Z","level":"ERROR","service":"payment-api","message":"Database connection failed: timeout after 30s","db_host":"postgres-replica:5432"}
{"timestamp":"2024-01-15T14:01:25Z","level":"WARNING","service":"payment-api","message":"Falling back to read replica","attempt":1}
{"timestamp":"2024-01-15T14:01:30Z","level":"ERROR","service":"payment-api","message":"Payment processing failed: database unavailable","user_id":"u_12345","amount":99.99}
{"timestamp":"2024-01-15T14:01:31Z","level":"ERROR","service":"payment-api","message":"Database connection failed: timeout after 30s","db_host":"postgres-primary:5432"}
{"timestamp":"2024-01-15T14:01:32Z","level":"CRITICAL","service":"payment-api","message":"Circuit breaker OPEN: database connection pool exhausted (100/100 connections)"}
{"timestamp":"2024-01-15T14:01:33Z","level":"ERROR","service":"payment-api","message":"Payment processing failed: circuit breaker open","user_id":"u_67890","amount":249.99}
{"timestamp":"2024-01-15T14:01:34Z","level":"ERROR","service":"payment-api","message":"Payment processing failed: circuit breaker open","user_id":"u_11111","amount":15.00}
{"timestamp":"2024-01-15T14:01:35Z","level":"CRITICAL","service":"payment-api","message":"Health check FAILED: /health returning 503"}
{"timestamp":"2024-01-15T14:01:40Z","level":"INFO","service":"payment-api","message":"Attempting database reconnection","attempt":1}
{"timestamp":"2024-01-15T14:01:45Z","level":"ERROR","service":"payment-api","message":"Reconnection failed: max retries exceeded"}
""",
    },
    'docker': {
        'filename': 'docker_crash.log',
        'format': 'text',
        'content': """\
2024-01-15 16:45:01 INFO Starting container: web-app-1
2024-01-15 16:45:02 INFO Container web-app-1 started (PID: 12847)
2024-01-15 16:45:03 INFO Binding to port 80
2024-01-15 16:45:10 WARNING Memory usage high: 87% (3.5GB/4GB)
2024-01-15 16:45:15 WARNING Memory usage critical: 94% (3.76GB/4GB)
2024-01-15 16:45:20 ERROR Out of memory: Kill process 12847 (node) score 980 or sacrifice child
2024-01-15 16:45:20 CRITICAL Container web-app-1 killed - OOMKilled
2024-01-15 16:45:21 ERROR Exit code: 137 (SIGKILL)
2024-01-15 16:45:22 INFO Restarting container: web-app-1 (restart policy: always)
2024-01-15 16:45:25 INFO Container web-app-1 started (PID: 12901)
2024-01-15 16:45:30 WARNING Memory usage high: 89% (3.56GB/4GB)
2024-01-15 16:45:35 CRITICAL Container web-app-1 killed - OOMKilled
2024-01-15 16:45:36 ERROR Exit code: 137 (SIGKILL)
2024-01-15 16:45:37 INFO Restarting container: web-app-1 (restart policy: always) - attempt 2
2024-01-15 16:45:40 WARNING Memory usage high: 91% (3.64GB/4GB)
2024-01-15 16:45:45 CRITICAL Container web-app-1 killed - OOMKilled
2024-01-15 16:45:46 ERROR Exit code: 137 (SIGKILL)
2024-01-15 16:45:47 ERROR Max restart attempts (3) reached - container in CrashLoopBackOff
2024-01-15 16:45:48 CRITICAL Service web-app UNAVAILABLE - all containers failed
""",
    },
}


def run_simulate(sim_type, save_report_flag, no_ai):
    """Run simulation using embedded log content"""
    sim = SIMULATED_LOGS.get(sim_type)
    if not sim:
        print(f"❌ Unknown simulation type: {sim_type}")
        return

    print(f"🎭 Simulating {sim_type} log analysis...\n")

    # Write to temp file, parse, then clean up
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.log', delete=False, encoding='utf-8'
    ) as f:
        f.write(sim['content'])
        temp_path = f.name

    try:
        run_analysis(
            filepath=Path(temp_path),
            filename=sim['filename'],
            fmt=sim['format'],
            save_report_flag=save_report_flag,
            no_ai=no_ai,
        )
    finally:
        os.unlink(temp_path)


# ─── Core Analysis Runner ────────────────────────────────────────────────────

def run_analysis(filepath, filename, fmt, save_report_flag, no_ai):
    """Parse, categorize, detect patterns, AI analyze, optionally save report"""

    print(f"📂 Analyzing: {filename}")
    print(f"📋 Format: {fmt}")
    print("🔄 Parsing log entries...")

    if fmt == 'json':
        entries = parse_json_log(filepath)
    elif fmt == 'syslog':
        entries = parse_syslog(filepath)
    else:
        entries = parse_text_log(filepath)

    if not entries:
        print("⚠️  No log entries found.")
        return

    print(f"📊 Parsed {len(entries)} log entries\n")

    categories = categorize_entries(entries)
    criticals = categories.get('CRITICAL', []) + categories.get('FATAL', [])
    errors = categories.get('ERROR', [])
    warnings = categories.get('WARNING', [])

    print("📊 Log Summary:")
    print(f"   🔴 CRITICAL: {len(criticals)}")
    print(f"   🟠 ERROR:    {len(errors)}")
    print(f"   🟡 WARNING:  {len(warnings)}")
    print(f"   🔵 INFO:     {len(categories.get('INFO', []))}")
    print()

    patterns = identify_patterns(entries)
    if patterns:
        print("🔄 Recurring Patterns:")
        for p in patterns:
            print(f"   {p['count']}x: {p['message'][:80]}")
        print()

    if criticals or errors:
        print("🚨 Critical & Error Lines:")
        for entry in (criticals + errors)[:10]:
            print(f"   Line {entry['line']:>4}: {entry['message'][:100]}")
        if len(criticals) + len(errors) > 10:
            print(f"   ... and {len(criticals) + len(errors) - 10} more")
        print()
    else:
        print("✅ No critical errors or errors found. System appears healthy!\n")

    if not no_ai:
        print("🤖 Analyzing with AI (this may take 30-60 seconds)...")
        ai_analysis = analyze_with_ai(categories, patterns, filename)
        print("\n" + "=" * 60)
        print("📋 AI ROOT CAUSE ANALYSIS")
        print("=" * 60)
        print(ai_analysis)
    else:
        ai_analysis = "AI analysis skipped (--no-ai flag)"

    if save_report_flag:
        report_file = save_report(filename, entries, categories, patterns, ai_analysis)
        print(f"\n💾 Report saved to: {report_file}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='AI Log Analyzer - Analyze Docker/K8s/App logs with AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a log file (auto-detect format)
  python src/log_analyzer.py --file demo/sample_logs/k8s_failed_deployment.log

  # Analyze and save report
  python src/log_analyzer.py --file demo/sample_logs/app_errors.log --save-report

  # Specify format explicitly
  python src/log_analyzer.py --file app.log --format json

  # Simulate K8s failure for demo
  python src/log_analyzer.py --simulate k8s

  # Skip AI (just parse and categorize)
  python src/log_analyzer.py --file app.log --no-ai
        """
    )

    parser.add_argument('--file', type=str, help='Log file to analyze')
    parser.add_argument(
        '--format', choices=['auto', 'json', 'text', 'syslog'],
        default='auto', help='Log format (default: auto-detect)'
    )
    parser.add_argument(
        '--simulate', choices=['k8s', 'app', 'docker'],
        help='Simulate log scenario for demo (k8s, app, docker)'
    )
    parser.add_argument('--save-report', action='store_true',
                        help='Save analysis report to log_reports/')
    parser.add_argument('--no-ai', action='store_true',
                        help='Skip AI analysis (parse and categorize only)')

    args = parser.parse_args()

    if not args.no_ai:
        print("🔍 Checking Ollama installation...")
        check_ollama()
        print("✅ Ollama is ready!\n")

    print("=" * 60)
    print("       🔍 AI LOG ANALYZER 🔍")
    print("=" * 60)
    print()

    if args.simulate:
        run_simulate(args.simulate, args.save_report, args.no_ai)
        return

    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)

        fmt = args.format
        if fmt == 'auto':
            fmt = detect_format(filepath)

        run_analysis(
            filepath=filepath,
            filename=filepath.name,
            fmt=fmt,
            save_report_flag=args.save_report,
            no_ai=args.no_ai,
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()
