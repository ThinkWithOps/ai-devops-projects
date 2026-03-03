#!/usr/bin/env python3
"""
AI Local Incident Commander
Monitors system alerts, analyzes incidents with AI, and suggests fixes
"""

import argparse
import json
import psutil
import time
from datetime import datetime
from pathlib import Path
import subprocess
import sys

def check_ollama():
    """Check if Ollama is installed and running"""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("❌ Ollama is not running. Please start Ollama first.")
            print("   Windows: Start Ollama from Start Menu")
            print("   Mac/Linux: Run 'ollama serve' in another terminal")
            sys.exit(1)
        
        # Check if llama3.2 is available
        if 'llama3.2' not in result.stdout and 'llama3.3' not in result.stdout:
            print("⚠️  llama3.2 or llama3.3 not found. Installing llama3.2...")
            subprocess.run(['ollama', 'pull', 'llama3.2'], check=True)
        
        return True
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first:")
        print("   Visit: https://ollama.ai/download")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("❌ Ollama is not responding. Please restart Ollama.")
        sys.exit(1)

def call_ollama(prompt, model="llama3.2"):
    """Call Ollama API for AI analysis"""
    try:
        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "AI analysis timed out. Please try again."
    except Exception as e:
        return f"AI analysis error: {str(e)}"

def get_system_metrics():
    """Get current system metrics"""
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
        'disk_percent': psutil.disk_usage('/').percent,
        'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
    }
    
    # Add network stats if available
    try:
        net_io = psutil.net_io_counters()
        metrics['network_bytes_sent'] = net_io.bytes_sent
        metrics['network_bytes_recv'] = net_io.bytes_recv
    except:
        pass
    
    return metrics

def detect_incidents(metrics, thresholds):
    """Detect incidents based on thresholds"""
    incidents = []
    
    # CPU check
    if metrics['cpu_percent'] > thresholds['cpu_critical']:
        incidents.append({
            'type': 'CPU',
            'severity': 'CRITICAL',
            'message': f"CPU usage at {metrics['cpu_percent']}% (threshold: {thresholds['cpu_critical']}%)",
            'value': metrics['cpu_percent']
        })
    elif metrics['cpu_percent'] > thresholds['cpu_warning']:
        incidents.append({
            'type': 'CPU',
            'severity': 'WARNING',
            'message': f"CPU usage at {metrics['cpu_percent']}% (threshold: {thresholds['cpu_warning']}%)",
            'value': metrics['cpu_percent']
        })
    
    # Memory check
    if metrics['memory_percent'] > thresholds['memory_critical']:
        incidents.append({
            'type': 'Memory',
            'severity': 'CRITICAL',
            'message': f"Memory usage at {metrics['memory_percent']}% ({metrics['memory_available_gb']}GB available)",
            'value': metrics['memory_percent']
        })
    elif metrics['memory_percent'] > thresholds['memory_warning']:
        incidents.append({
            'type': 'Memory',
            'severity': 'WARNING',
            'message': f"Memory usage at {metrics['memory_percent']}% ({metrics['memory_available_gb']}GB available)",
            'value': metrics['memory_percent']
        })
    
    # Disk check
    if metrics['disk_percent'] > thresholds['disk_critical']:
        incidents.append({
            'type': 'Disk',
            'severity': 'CRITICAL',
            'message': f"Disk usage at {metrics['disk_percent']}% ({metrics['disk_free_gb']}GB free)",
            'value': metrics['disk_percent']
        })
    elif metrics['disk_percent'] > thresholds['disk_warning']:
        incidents.append({
            'type': 'Disk',
            'severity': 'WARNING',
            'message': f"Disk usage at {metrics['disk_percent']}% ({metrics['disk_free_gb']}GB free)",
            'value': metrics['disk_percent']
        })
    
    return incidents

def analyze_incident_with_ai(incident, metrics):
    """Analyze incident with AI and get recommendations"""
    prompt = f"""You are a DevOps incident commander. Analyze this system incident and provide:

1. Root cause analysis
2. Immediate action steps
3. Long-term prevention measures

Incident Details:
- Type: {incident['type']}
- Severity: {incident['severity']}
- Issue: {incident['message']}

Current System State:
- CPU: {metrics['cpu_percent']}%
- Memory: {metrics['memory_percent']}% ({metrics['memory_available_gb']}GB available)
- Disk: {metrics['disk_percent']}% ({metrics['disk_free_gb']}GB free)

Provide a concise analysis (3-4 sentences) and 2-3 specific action items.
"""
    
    print(f"\n🤖 Analyzing {incident['type']} incident with AI...")
    analysis = call_ollama(prompt)
    
    return analysis

def generate_incident_report(incidents, metrics, analyses):
    """Generate incident report in markdown format"""
    report_lines = [
        "# Incident Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n## Summary",
        f"- **Incidents Detected:** {len(incidents)}",
        f"- **Critical:** {sum(1 for i in incidents if i['severity'] == 'CRITICAL')}",
        f"- **Warning:** {sum(1 for i in incidents if i['severity'] == 'WARNING')}",
        "\n## System Metrics",
        f"- CPU Usage: {metrics['cpu_percent']}%",
        f"- Memory Usage: {metrics['memory_percent']}% ({metrics['memory_available_gb']}GB available)",
        f"- Disk Usage: {metrics['disk_percent']}% ({metrics['disk_free_gb']}GB free)",
    ]
    
    # Add each incident
    for i, (incident, analysis) in enumerate(zip(incidents, analyses), 1):
        report_lines.extend([
            f"\n## Incident {i}: {incident['type']} - {incident['severity']}",
            f"\n**Alert:** {incident['message']}",
            f"\n### AI Analysis",
            analysis,
        ])
    
    return "\n".join(report_lines)

def save_incident_log(incidents, metrics, analyses):
    """Save incident data to JSON log"""
    log_dir = Path("incident_logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"incident_{timestamp}.json"
    
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics,
        'incidents': incidents,
        'analyses': analyses
    }
    
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    return log_file

def simulate_incident(incident_type):
    """Simulate different incident types for demo"""
    print(f"\n🎭 Simulating {incident_type} incident...\n")
    
    if incident_type == 'cpu':
        # Simulate high CPU
        print("⚠️  HIGH CPU ALERT")
        print("Current CPU: 92%")
        print("Threshold: 80%")
        
        return {
            'type': 'CPU',
            'severity': 'CRITICAL',
            'message': 'CPU usage at 92% (threshold: 80%)',
            'value': 92
        }, {
            'cpu_percent': 92,
            'memory_percent': 45,
            'memory_available_gb': 8.5,
            'disk_percent': 60,
            'disk_free_gb': 120.0,
            'timestamp': datetime.now().isoformat()
        }
    
    elif incident_type == 'memory':
        # Simulate memory leak
        print("⚠️  MEMORY LEAK DETECTED")
        print("Current Memory: 95%")
        print("Threshold: 85%")
        
        return {
            'type': 'Memory',
            'severity': 'CRITICAL',
            'message': 'Memory usage at 95% (0.8GB available)',
            'value': 95
        }, {
            'cpu_percent': 65,
            'memory_percent': 95,
            'memory_available_gb': 0.8,
            'disk_percent': 55,
            'disk_free_gb': 135.0,
            'timestamp': datetime.now().isoformat()
        }
    
    elif incident_type == 'disk':
        # Simulate disk full
        print("⚠️  DISK SPACE CRITICAL")
        print("Current Disk: 96%")
        print("Threshold: 90%")
        
        return {
            'type': 'Disk',
            'severity': 'CRITICAL',
            'message': 'Disk usage at 96% (12GB free)',
            'value': 96
        }, {
            'cpu_percent': 45,
            'memory_percent': 55,
            'memory_available_gb': 7.2,
            'disk_percent': 96,
            'disk_free_gb': 12.0,
            'timestamp': datetime.now().isoformat()
        }
    
    else:
        return None, None

def main():
    parser = argparse.ArgumentParser(
        description='AI Local Incident Commander - Monitor and analyze system incidents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor system in real-time
  python incident_commander.py --monitor

  # Run one-time check
  python incident_commander.py --check

  # Simulate incidents for demo
  python incident_commander.py --simulate cpu
  python incident_commander.py --simulate memory
  python incident_commander.py --simulate disk

  # Custom thresholds
  python incident_commander.py --check --cpu-critical 90 --memory-critical 90
        """
    )
    
    parser.add_argument('--monitor', action='store_true',
                       help='Monitor system continuously (Ctrl+C to stop)')
    parser.add_argument('--check', action='store_true',
                       help='Run one-time system check')
    parser.add_argument('--simulate', choices=['cpu', 'memory', 'disk'],
                       help='Simulate incident for demo (cpu, memory, or disk)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Monitoring interval in seconds (default: 30)')
    
    # Threshold arguments
    parser.add_argument('--cpu-warning', type=int, default=70,
                       help='CPU warning threshold (default: 70%%)')
    parser.add_argument('--cpu-critical', type=int, default=85,
                       help='CPU critical threshold (default: 85%%)')
    parser.add_argument('--memory-warning', type=int, default=75,
                       help='Memory warning threshold (default: 75%%)')
    parser.add_argument('--memory-critical', type=int, default=90,
                       help='Memory critical threshold (default: 90%%)')
    parser.add_argument('--disk-warning', type=int, default=80,
                       help='Disk warning threshold (default: 80%%)')
    parser.add_argument('--disk-critical', type=int, default=90,
                       help='Disk critical threshold (default: 90%%)')
    
    parser.add_argument('--no-ai', action='store_true',
                       help='Skip AI analysis (just show alerts)')
    parser.add_argument('--save-report', action='store_true',
                       help='Save incident report to file')
    
    args = parser.parse_args()
    
    # Check if Ollama is available (unless --no-ai)
    if not args.no_ai:
        print("🔍 Checking Ollama installation...")
        check_ollama()
        print("✅ Ollama is ready!\n")
    
    # Set up thresholds
    thresholds = {
        'cpu_warning': args.cpu_warning,
        'cpu_critical': args.cpu_critical,
        'memory_warning': args.memory_warning,
        'memory_critical': args.memory_critical,
        'disk_warning': args.disk_warning,
        'disk_critical': args.disk_critical,
    }
    
    print("=" * 60)
    print("       🚨 AI LOCAL INCIDENT COMMANDER 🚨")
    print("=" * 60)
    print(f"\n📊 Monitoring Thresholds:")
    print(f"   CPU: Warning {thresholds['cpu_warning']}% | Critical {thresholds['cpu_critical']}%")
    print(f"   Memory: Warning {thresholds['memory_warning']}% | Critical {thresholds['memory_critical']}%")
    print(f"   Disk: Warning {thresholds['disk_warning']}% | Critical {thresholds['disk_critical']}%")
    print()
    
    # Handle simulate mode
    if args.simulate:
        incident, metrics = simulate_incident(args.simulate)
        if incident:
            incidents = [incident]
            
            if not args.no_ai:
                analysis = analyze_incident_with_ai(incident, metrics)
                analyses = [analysis]
                
                print("\n" + "=" * 60)
                print("📋 AI ANALYSIS")
                print("=" * 60)
                print(analysis)
            else:
                analyses = ["AI analysis skipped (--no-ai flag)"]
            
            # Generate and save report
            if args.save_report:
                report = generate_incident_report(incidents, metrics, analyses)
                report_file = Path("incident_logs") / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                report_file.parent.mkdir(exist_ok=True)
                report_file.write_text(report)
                print(f"\n💾 Report saved to: {report_file}")
                
                log_file = save_incident_log(incidents, metrics, analyses)
                print(f"💾 Log saved to: {log_file}")
        
        return
    
    # Handle check mode
    if args.check:
        print("🔍 Running system check...\n")
        metrics = get_system_metrics()
        incidents = detect_incidents(metrics, thresholds)
        
        if not incidents:
            print("✅ No incidents detected. System is healthy!")
            print(f"\n📊 Current Metrics:")
            print(f"   CPU: {metrics['cpu_percent']}%")
            print(f"   Memory: {metrics['memory_percent']}%")
            print(f"   Disk: {metrics['disk_percent']}%")
            return
        
        print(f"⚠️  Found {len(incidents)} incident(s)!\n")
        
        analyses = []
        for incident in incidents:
            print(f"🚨 {incident['severity']}: {incident['message']}")
            
            if not args.no_ai:
                analysis = analyze_incident_with_ai(incident, metrics)
                analyses.append(analysis)
                print(f"\n📋 AI Analysis:\n{analysis}\n")
            else:
                analyses.append("AI analysis skipped (--no-ai flag)")
        
        # Save report if requested
        if args.save_report:
            report = generate_incident_report(incidents, metrics, analyses)
            report_file = Path("incident_logs") / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_file.parent.mkdir(exist_ok=True)
            report_file.write_text(report)
            print(f"\n💾 Report saved to: {report_file}")
            
            log_file = save_incident_log(incidents, metrics, analyses)
            print(f"💾 Log saved to: {log_file}")
        
        return
    
    # Handle monitor mode
    if args.monitor:
        print(f"👀 Monitoring system every {args.interval} seconds...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                metrics = get_system_metrics()
                incidents = detect_incidents(metrics, thresholds)
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                if incidents:
                    print(f"\n⚠️  [{timestamp}] {len(incidents)} incident(s) detected!")
                    
                    analyses = []
                    for incident in incidents:
                        print(f"   {incident['severity']}: {incident['message']}")
                        
                        if not args.no_ai:
                            analysis = analyze_incident_with_ai(incident, metrics)
                            analyses.append(analysis)
                            print(f"\n   AI Analysis:\n   {analysis}\n")
                        else:
                            analyses.append("AI analysis skipped")
                    
                    # Auto-save incidents
                    if incidents:
                        log_file = save_incident_log(incidents, metrics, analyses)
                        print(f"   💾 Logged to: {log_file}")
                else:
                    print(f"✅ [{timestamp}] System healthy - "
                          f"CPU: {metrics['cpu_percent']}% | "
                          f"Mem: {metrics['memory_percent']}% | "
                          f"Disk: {metrics['disk_percent']}%")
                
                time.sleep(args.interval)
        
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped.")
            return
    
    # If no mode specified, show help
    if not (args.monitor or args.check or args.simulate):
        parser.print_help()

if __name__ == "__main__":
    main()
