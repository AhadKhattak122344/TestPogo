"""
Frida Manager - Handles Frida server deployment and script execution for Pokemod analysis.
"""
import os
import subprocess
import time
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from .adb import Adb


@dataclass
class FridaStatus:
    """Status of Frida server on device"""
    server_running: bool
    server_pid: Optional[int]
    server_version: Optional[str]
    device_arch: Optional[str]
    listening_port: Optional[int]
    observations: List[str]


class FridaManager:
    """Manages Frida server lifecycle and script execution"""
    
    FRIDA_SERVER_VERSION = "17.18.0"
    DEFAULT_PORT = 27042
    REMOTE_PATH = "/data/local/tmp/frida-server"
    
    ARCH_MAP = {
        "arm64-v8a": "android-arm64",
        "armeabi-v7a": "android-arm",
        "x86_64": "android-x86_64",
        "x86": "android-x86",
    }
    
    def __init__(self, adb: Adb):
        self.adb = adb
        self.server_process = None
        
    def get_device_arch(self) -> Optional[str]:
        """Get device CPU architecture"""
        result = self.adb.shell("getprop ro.product.cpu.abi")
        if result:
            return result.strip()
        return None
    
    def get_frida_server_url(self, arch: str) -> str:
        """Construct Frida server download URL"""
        frida_arch = self.ARCH_MAP.get(arch, "android-arm64")
        return (
            f"https://github.com/frida/frida/releases/"
            f"download/{self.FRIDA_SERVER_VERSION}/"
            f"frida-server-{self.FRIDA_SERVER_VERSION}-{frida_arch}.xz"
        )
    
    def download_frida_server(self, arch: str, output_path: Path) -> bool:
        """Download Frida server binary for specified architecture"""
        url = self.get_frida_server_url(arch)
        print(f"Downloading Frida server from: {url}")
        
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Decompress if .xz
            if output_path.suffix == ".xz":
                import lzma
                decompressed_path = output_path.with_suffix("")
                with lzma.open(output_path, "rb") as f_in:
                    with open(decompressed_path, "wb") as f_out:
                        f_out.write(f_in.read())
                output_path.unlink()  # Remove compressed file
                output_path = decompressed_path
            
            # Make executable
            os.chmod(output_path, 0o755)
            print(f"Frida server downloaded to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Failed to download Frida server: {e}")
            return False
    
    def push_frida_server(self, local_path: Path) -> bool:
        """Push Frida server to device"""
        result = self.adb.run("push", str(local_path), self.REMOTE_PATH)
        if not result:
            print(f"Failed to push Frida server")
            return False
        
        # Set permissions
        self.adb.shell(f"chmod 755 {self.REMOTE_PATH}")
        return True
    
    def start_frida_server(self) -> bool:
        """Start Frida server on device"""
        # Check if already running
        status = self.get_status()
        if status.server_running:
            print("Frida server already running")
            return True
        
        # Start in background
        cmd = f"nohup {self.REMOTE_PATH} --port {self.DEFAULT_PORT} &"
        result = self.adb.shell(cmd)
        
        if not result and "starting" not in result.lower():
            print(f"Failed to start Frida server")
            return False
        
        # Wait for server to start
        time.sleep(2)
        return True
    
    def stop_frida_server(self) -> bool:
        """Stop Frida server on device"""
        result = self.adb.shell(f"pkill -f frida-server")
        return bool(result)
    
    def get_status(self) -> FridaStatus:
        """Get Frida server status on device"""
        observations = []
        
        # Check process
        ps_result = self.adb.shell("ps | grep frida-server || echo 'not running'")
        server_running = "frida-server" in (ps_result or "")
        server_pid = None
        
        if server_running and ps_result:
            # Extract PID
            parts = ps_result.split()
            if len(parts) > 1:
                try:
                    server_pid = int(parts[1])
                except ValueError:
                    pass
        
        # Get architecture
        device_arch = self.get_device_arch()
        
        # Check port
        netstat_result = self.adb.shell(f"netstat -tlnp | grep :{self.DEFAULT_PORT} || echo 'not listening'")
        listening = f":{self.DEFAULT_PORT}" in (netstat_result or "")
        
        if not server_running:
            observations.append("Frida server process not found")
        if not listening and server_running:
            observations.append("Frida server process exists but not listening on port")
        if not device_arch:
            observations.append("Could not determine device architecture")
        
        return FridaStatus(
            server_running=server_running,
            server_pid=server_pid,
            server_version=self.FRIDA_SERVER_VERSION,
            device_arch=device_arch,
            listening_port=self.DEFAULT_PORT if listening else None,
            observations=observations
        )
    
    def ensure_frida_server(self, bin_dir: Path) -> bool:
        """Ensure Frida server is downloaded, pushed, and running"""
        arch = self.get_device_arch()
        if not arch:
            print("Could not determine device architecture")
            return False
        
        frida_arch = self.ARCH_MAP.get(arch, "android-arm64")
        local_binary = bin_dir / f"frida-server-{self.FRIDA_SERVER_VERSION}-{frida_arch}"
        
        # Download if not exists
        if not local_binary.exists():
            print(f"Frida server binary not found, downloading...")
            if not self.download_frida_server(arch, local_binary):
                return False
        
        # Push to device
        if not self.push_frida_server(local_binary):
            return False
        
        # Start server
        if not self.start_frida_server():
            return False
        
        # Verify
        status = self.get_status()
        if not status.server_running:
            print("Failed to verify Frida server is running")
            return False
        
        print(f"Frida server running (PID: {status.server_pid})")
        return True
    
    def run_script(self, script_path: Path, target_package: str = "com.nianticlabs.pokemongo") -> Optional[subprocess.Popen]:
        """Run a Frida script against target package"""
        if not script_path.exists():
            print(f"Script not found: {script_path}")
            return None
        
        status = self.get_status()
        if not status.server_running:
            print("Frida server not running, starting...")
            if not self.start_frida_server():
                return None
        
        # Build Frida command
        cmd = [
            "frida",
            "-U",  # USB/Emulator
            "-f", target_package,
            "-l", str(script_path),
            "--no-pause"
        ]
        
        print(f"Running Frida: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            return process
        except Exception as e:
            print(f"Failed to start Frida: {e}")
            return None
    
    def attach_to_running(self, target_package: str, script_path: Path) -> Optional[subprocess.Popen]:
        """Attach Frida script to already running process"""
        cmd = [
            "frida",
            "-U",
            "-n", target_package,
            "-l", str(script_path)
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            return process
        except Exception as e:
            print(f"Failed to attach Frida: {e}")
            return None
