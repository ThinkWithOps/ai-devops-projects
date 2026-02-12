#!/usr/bin/env python3
"""
Docker Image Comparison Tool
Compare vulnerability counts across multiple Docker images
"""

import subprocess
import sys
from docker_scanner import DockerScanner


def quick_scan(scanner, image_name):
    """Quick scan to count vulnerabilities only."""
    scan_data = scanner.scan_image(image_name)
    if not scan_data:
        return None
    
    vulns = scanner.extract_vulnerabilities(scan_data)
    critical = sum(1 for v in vulns if v['severity'] == 'CRITICAL')
    high = sum(1 for v in vulns if v['severity'] == 'HIGH')
    
    return {
        'image': image_name,
        'total': len(vulns),
        'critical': critical,
        'high': high
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_images.py <image1> <image2> [image3] ...")
        print("\nExample:")
        print("  python compare_images.py nginx:latest nginx:alpine nginx:1.27-alpine")
        sys.exit(1)
    
    images = sys.argv[1:]
    scanner = DockerScanner()
    
    print("🔍 Comparing Docker Images")
    print("=" * 80)
    print()
    
    results = []
    for image in images:
        print(f"Scanning {image}...")
        result = quick_scan(scanner, image)
        if result:
            results.append(result)
            print(f"  ✅ Found {result['total']} vulnerabilities\n")
        else:
            print(f"  ❌ Scan failed\n")
    
    if not results:
        print("No results to compare")
        return
    
    # Sort by total vulnerabilities (lowest first)
    results.sort(key=lambda x: x['total'])
    
    print("\n" + "=" * 80)
    print("📊 COMPARISON RESULTS")
    print("=" * 80)
    print()
    print(f"{'Image':<40} {'Total':<10} {'Critical':<10} {'High':<10}")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        marker = "✅ BEST" if i == 1 else "⚠️" if i == len(results) else "  "
        print(f"{result['image']:<40} {result['total']:<10} {result['critical']:<10} {result['high']:<10} {marker}")
    
    print()
    print("=" * 80)
    print(f"🏆 RECOMMENDATION: Use {results[0]['image']}")
    print(f"   (Lowest vulnerability count: {results[0]['total']})")
    print("=" * 80)


if __name__ == "__main__":
    main()