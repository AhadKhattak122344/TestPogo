#!/usr/bin/env python3
"""
Pokemod Automation Runner - Main entry point for automation workflow.
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from android_lab.adb import Adb
from android_lab.frida_manager import FridaManager
from android_lab.automation import PokemodAutomation


def main():
    parser = argparse.ArgumentParser(description="Pokemod Automation Runner")
    parser.add_argument("--serial", default=None, help="ADB device serial")
    parser.add_argument("--script", type=Path, default=None, help="Frida script to run")
    parser.add_argument("--output", type=Path, default=None, help="Output report path")
    parser.add_argument("--bin-dir", type=Path, default=Path("bin"), help="Binaries directory")
    parser.add_argument("--scripts-dir", type=Path, default=Path("scripts/frida"), help="Scripts directory")
    parser.add_argument("--workflow", action="store_true", help="Run full workflow")
    parser.add_argument("--check-only", action="store_true", help="Only check binaries and status")
    
    args = parser.parse_args()
    
    # Resolve paths
    bin_dir = args.bin_dir.resolve()
    scripts_dir = args.scripts_dir.resolve()
    
    print(f"Bin directory: {bin_dir}")
    print(f"Scripts directory: {scripts_dir}")
    
    # Initialize ADB
    try:
        adb = Adb(serial=args.serial)
        devices_result = adb.shell("adb devices")
        
        if not devices_result or "device" not in devices_result:
            print("ERROR: No ADB devices found. Please connect a device or start an emulator.")
            sys.exit(1)
        
        # Parse devices - if no serial specified, use first
        if not args.serial:
            lines = devices_result.strip().split('\n')
            for line in lines[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    adb.serial = parts[0]
                    print(f"Using device: {adb.serial}")
                    break
        
    except Exception as e:
        print(f"ERROR: Failed to initialize ADB: {e}")
        sys.exit(1)
    
    # Initialize Frida Manager
    frida = FridaManager(adb)
    
    # Initialize Automation
    automation = PokemodAutomation(
        adb=adb,
        frida=frida,
        bin_dir=bin_dir,
        scripts_dir=scripts_dir
    )
    
    if args.check_only:
        print("\n=== Check Mode ===")
        status = automation.check_binaries()
        print("\nBinary Status:")
        for name, info in status.items():
            found = info.get("found", False)
            status_str = "✓ FOUND" if found else "✗ MISSING"
            print(f"  {name}: {status_str}")
            if "path" in info:
                print(f"    Path: {info['path']}")
        sys.exit(0)
    
    if args.workflow:
        # Run full workflow
        report = automation.full_workflow(script_path=args.script)
        
        # Save report if requested
        if args.output:
            automation.save_report(args.output)
        
        # Exit with error if any failures
        if report["summary"]["failed"] > 0:
            print(f"\nWARNING: {report['summary']['failed']} operations failed")
            sys.exit(1)
        
        sys.exit(0)
    
    # Default: Just ensure Frida server
    print("\n=== Ensuring Frida Server ===")
    if frida.ensure_frida_server(bin_dir):
        print("Frida server is ready")
        sys.exit(0)
    else:
        print("Failed to setup Frida server")
        sys.exit(1)


if __name__ == "__main__":
    main()
