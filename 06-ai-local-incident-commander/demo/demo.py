#!/usr/bin/env python3
"""
Demo scenarios for AI Incident Commander
Run different incident simulations to showcase the tool
"""

import subprocess
import sys
import time

def run_demo(scenario):
    """Run a demo scenario"""
    print("=" * 70)
    print(f"  DEMO: {scenario['title']}")
    print("=" * 70)
    print(f"\n📝 Scenario: {scenario['description']}\n")
    
    input("Press Enter to start simulation...")
    
    # Run the incident commander
    cmd = ['python', 'src/incident_commander.py'] + scenario['args']
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("\n❌ Demo failed. Make sure Ollama is running!")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print()

def main():
    scenarios = [
        {
            'title': 'High CPU Alert',
            'description': 'Memory leak causing 92% CPU usage',
            'args': ['--simulate', 'cpu', '--save-report']
        },
        {
            'title': 'Memory Leak Critical',
            'description': 'Application consuming 95% of available memory',
            'args': ['--simulate', 'memory', '--save-report']
        },
        {
            'title': 'Disk Space Critical',
            'description': 'Disk at 96% capacity, only 12GB free',
            'args': ['--simulate', 'disk', '--save-report']
        }
    ]
    
    print("\n🎬 AI Incident Commander - Demo Suite\n")
    print("This will run 3 incident simulations:\n")
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['title']}: {scenario['description']}")
    print()
    
    choice = input("Run all demos? (y/n): ").lower()
    
    if choice != 'y':
        print("\nAvailable demos:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. {scenario['title']}")
        
        try:
            num = int(input("\nSelect demo number (1-3): "))
            if 1 <= num <= 3:
                run_demo(scenarios[num-1])
            else:
                print("Invalid selection!")
        except (ValueError, IndexError):
            print("Invalid input!")
        return
    
    # Run all demos
    for scenario in scenarios:
        run_demo(scenario)
        time.sleep(2)
    
    print("✅ All demos completed!")
    print("\n📁 Check the 'incident_logs' folder for generated reports\n")

if __name__ == "__main__":
    main()
