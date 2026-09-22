"""
Pokemod Automation - Orchestrates Frida, service management, and binary discovery.
"""
import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from .adb import Adb
from .frida_manager import FridaManager


@dataclass
class AutomationResult:
    """Result of automation run"""
    component: str
    operation: str
    success: bool
    details: Dict[str, Any]
    errors: List[str]


class PokemodAutomation:
    """Main automation orchestrator for Pokemod workflow"""
    
    POGO_PACKAGE = "com.nianticlabs.pokemongo"
    ATLAS_PACKAGE = "com.pokemod.atlas"
    
    def __init__(self, adb: Adb, frida: FridaManager, bin_dir: Path, scripts_dir: Path):
        self.adb = adb
        self.frida = frida
        self.bin_dir = bin_dir
        self.scripts_dir = scripts_dir
        self.results: List[AutomationResult] = []
    
    def _add_result(self, component: str, operation: str, success: bool, details: Dict[str, Any], errors: List[str] = None):
        """Record automation result"""
        self.results.append(AutomationResult(
            component=component,
            operation=operation,
            success=success,
            details=details,
            errors=errors or []
        ))
    
    def check_binaries(self) -> Dict[str, Any]:
        """Check for required binaries (Atlas APK, Zygisk module, etc.)"""
        print("\n=== Checking for Binaries ===")
        
        binaries = {
            "atlas_apk": self.bin_dir / "Atlas.apk",
            "pogomod_zygisk": self.bin_dir / "Pokemod-Zygisk.zip",
            "frida_server": None,  # Will be downloaded
        }
        
        status = {}
        for name, path in binaries.items():
            if path and path.exists():
                status[name] = {
                    "found": True,
                    "path": str(path),
                    "size_bytes": path.stat().st_size
                }
            else:
                status[name] = {"found": False, "path": str(path) if path else "auto-download"}
        
        # Check Frida separately
        frida_status = self.frida.get_status()
        status["frida_server"] = {
            "found": frida_status.server_running,
            "pid": frida_status.server_pid,
            "arch": frida_status.device_arch
        }
        
        self._add_result(
            "binaries",
            "check",
            all(s.get("found", False) for s in status.values() if s.get("found") is not None),
            status
        )
        
        return status
    
    def deploy_atlas(self, apk_path: Optional[Path] = None) -> bool:
        """Deploy Atlas APK to device"""
        print("\n=== Deploying Atlas ===")
        
        if apk_path is None:
            apk_path = self.bin_dir / "Atlas.apk"
        
        if not apk_path.exists():
            self._add_result("atlas", "deploy", False, {}, ["Atlas.apk not found"])
            print("Atlas.apk not found in bin directory")
            return False
        
        # Install APK - using shell command since Adb class doesn't have install method
        result = self.adb.shell(f"pm install -r {apk_path}")
        success = "Success" in (result or "")
        
        self._add_result("atlas", "deploy", success, {"apk": str(apk_path)}, [] if success else [result or "Unknown error"])
        
        if success:
            print("Atlas deployed successfully")
        else:
            print(f"Failed to deploy Atlas: {result or 'Unknown error'}")
        
        return success
    
    def start_atlas_service(self, service_name: str = "MappingService") -> bool:
        """Start Atlas service via am command"""
        print(f"\n=== Starting Atlas Service: {service_name} ===")
        
        cmd = f"am startservice {self.ATLAS_PACKAGE}/com.pokemod.atlas.services.{service_name}"
        result = self.adb.shell(cmd)
        
        success = bool(result) and ("start" in result.lower() or "starting" in result.lower())
        
        self._add_result(
            "atlas_service",
            "start",
            success,
            {"service": service_name, "cmd": cmd},
            [] if success else [result or "Failed to start service"]
        )
        
        if success:
            print(f"Service {service_name} started")
        else:
            print(f"Failed to start service: {result or 'Unknown error'}")
        
        return success
    
    def check_pogo_installed(self) -> bool:
        """Check if Pokémon GO is installed"""
        result = self.adb.shell(f"pm list packages | grep {self.POGO_PACKAGE}")
        installed = self.POGO_PACKAGE in (result or "")
        
        self._add_result("pogo", "check_installed", installed, {"installed": installed})
        return installed
    
    def launch_pogo_with_frida(self, script_path: Optional[Path] = None) -> bool:
        """Launch Pokémon GO with Frida script attached"""
        print("\n=== Launching Pokémon GO with Frida ===")
        
        if script_path and not script_path.exists():
            self._add_result("pogo_frida", "launch", False, {}, [f"Script not found: {script_path}"])
            print(f"Frida script not found: {script_path}")
            return False
        
        # Use Frida to launch
        process = self.frida.run_script(
            script_path=script_path or (self.scripts_dir / "default_hook.js"),
            target_package=self.POGO_PACKAGE
        )
        
        success = process is not None
        
        self._add_result(
            "pogo_frida",
            "launch",
            success,
            {"script": str(script_path) if script_path else "none", "pid": process.pid if process else None},
            [] if success else ["Failed to start Frida process"]
        )
        
        if success:
            print(f"Launched Pokémon GO with Frida (PID: {process.pid})")
        else:
            print("Failed to launch with Frida")
        
        return success
    
    def run_analysis_script(self, script_name: str) -> AutomationResult:
        """Run a specific analysis script"""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            result = AutomationResult(
                component="analysis",
                operation=f"run_{script_name}",
                success=False,
                details={"script": str(script_path)},
                errors=[f"Script not found: {script_path}"]
            )
            self.results.append(result)
            return result
        
        print(f"\n=== Running Analysis Script: {script_name} ===")
        
        process = self.frida.attach_to_running(self.POGO_PACKAGE, script_path)
        
        if process:
            # Collect output for a few seconds
            time.sleep(5)
            if process.poll() is None:
                process.terminate()
            
            result = AutomationResult(
                component="analysis",
                operation=f"run_{script_name}",
                success=True,
                details={"script": str(script_path), "output_collected": True},
                errors=[]
            )
        else:
            result = AutomationResult(
                component="analysis",
                operation=f"run_{script_name}",
                success=False,
                details={"script": str(script_path)},
                errors=["Failed to attach Frida"]
            )
        
        self.results.append(result)
        return result
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return {
            "timestamp": time.time(),
            "device_serial": self.adb.serial,
            "results": [
                {
                    "component": r.component,
                    "operation": r.operation,
                    "success": r.success,
                    "details": r.details,
                    "errors": r.errors
                }
                for r in self.results
            ],
            "summary": {
                "total_operations": len(self.results),
                "successful": sum(1 for r in self.results if r.success),
                "failed": sum(1 for r in self.results if not r.success)
            }
        }
    
    def save_report(self, output_path: Path):
        """Save automation report to file"""
        report = self.get_status_report()
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {output_path}")
    
    def full_workflow(self, script_path: Optional[Path] = None) -> Dict[str, Any]:
        """Run complete automation workflow"""
        print("\n" + "="*60)
        print("POKEMOD AUTOMATION WORKFLOW")
        print("="*60)
        
        # Step 1: Check binaries
        self.check_binaries()
        
        # Step 2: Ensure Frida server
        print("\n=== Ensuring Frida Server ===")
        frida_ok = self.frida.ensure_frida_server(self.bin_dir)
        self._add_result("frida", "ensure", frida_ok, {"running": frida_ok})
        
        # Step 3: Deploy Atlas (if available)
        atlas_deployed = self.deploy_atlas()
        
        # Step 4: Start Atlas service (if deployed)
        if atlas_deployed:
            self.start_atlas_service()
        
        # Step 5: Check Pogo
        pogo_installed = self.check_pogo_installed()
        
        # Step 6: Launch Pogo with Frida (if script available)
        if pogo_installed:
            self.launch_pogo_with_frida(script_path)
        
        # Generate report
        report = self.get_status_report()
        
        print("\n" + "="*60)
        print("WORKFLOW SUMMARY")
        print("="*60)
        print(f"Total Operations: {report['summary']['total_operations']}")
        print(f"Successful: {report['summary']['successful']}")
        print(f"Failed: {report['summary']['failed']}")
        
        return report
