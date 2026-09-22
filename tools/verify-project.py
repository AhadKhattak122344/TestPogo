#!/usr/bin/env python3
"""
Project Verification Script - Validates all code components compile and tests pass.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a command and report result"""
    print(f"\n{'='*60}")
    print(f"CHECKING: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ PASS: {description}")
        return True
    else:
        print(f"✗ FAIL: {description}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        return False


def main():
    workspace = Path(__file__).parent.parent
    results = {}
    
    # 1. Python compilation
    results['python_compile'] = run_command(
        [sys.executable, "-m", "compileall", "android_lab", "scripts"],
        "Python source compilation"
    )
    
    # 2. Import validation
    results['imports'] = run_command(
        [sys.executable, "-c", 
         "from android_lab.frida_manager import FridaManager; "
         "from android_lab.automation import PokemodAutomation; "
         "print('All imports OK')"],
        "Module imports"
    )
    
    # 3. Unit tests
    results['unit_tests'] = run_command(
        ["uv", "run", "pytest", "-p", "no:cacheprovider", "-q"],
        "Unit tests"
    )
    
    # 4. CLI help
    results['cli_help'] = run_command(
        [sys.executable, "scripts/frida/run_automation.py", "--help"],
        "CLI --help"
    )
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("ALL CHECKS PASSED ✓")
        print("\nReady for manual testing with:")
        print("  python scripts/frida/run_automation.py --workflow --bin-dir ./bin")
        return 0
    else:
        print("SOME CHECKS FAILED ✗")
        print("\nFix the above errors before proceeding to manual testing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
