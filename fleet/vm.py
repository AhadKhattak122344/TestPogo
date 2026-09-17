"""libvirt wrapper for ARM64 Android guests."""

import subprocess
import time
from pathlib import Path


class VMError(Exception):
    pass


class VMController:
    def __init__(
        self,
        conn_uri: str = "qemu:///system",
        image_dir: str = "/var/lib/libvirt/images",
        template_dir: str = "/opt/fleet/fleet/templates",
        gold_image: str = "/var/lib/libvirt/images/gold.qcow2",
        tee_device: str = "/dev/tee0",
    ):
        import libvirt
        from jinja2 import Environment, FileSystemLoader

        self.conn = libvirt.open(conn_uri)
        if self.conn is None:
            raise VMError(f"cannot connect to {conn_uri}")
        self.image_dir = Path(image_dir)
        self.gold_image = Path(gold_image)
        self.tee_device = tee_device
        self._jinja = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def clone(self, name: str, cpu_cores: int, ram_gb: int, mac: str) -> str:
        disk = self.image_dir / f"{name}.qcow2"
        if disk.exists():
            raise VMError(f"disk exists: {disk}")
        subprocess.run(
            ["cp", "--reflink=auto", str(self.gold_image), str(disk)],
            check=True,
        )
        xml = self._jinja.get_template("guest.xml.j2").render(
            name=name,
            memory_mb=ram_gb * 1024,
            vcpus=cpu_cores,
            mac=mac,
            disk_path=str(disk),
            tee_device=self.tee_device,
        )
        try:
            self.conn.defineXML(xml)
        except libvirt.libvirtError as e:
            disk.unlink(missing_ok=True)
            raise VMError(f"defineXML: {e}") from e
        return str(disk)

    def start(self, name: str) -> None:
        d = self._domain(name)
        if not d.isActive():
            d.create()

    def stop(self, name: str) -> None:
        d = self._domain(name)
        if d.isActive():
            d.destroy()

    def destroy(self, name: str) -> None:
        try:
            d = self._domain(name)
        except VMError:
            return
        if d.isActive():
            d.destroy()
        d.undefineFlags(
            libvirt.VIR_DOMAIN_UNDEFINE_NVRAM
            | libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE
        )
        (self.image_dir / f"{name}.qcow2").unlink(missing_ok=True)

    def shell(self, name: str, cmd: str, timeout: int = 30) -> str:
        target = f"{name}.fleet.local:5555"
        r = subprocess.run(
            ["adb", "-s", target, "shell", cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode != 0:
            raise VMError(f"adb shell: {r.stderr.strip()}")
        return r.stdout.strip()

    def wait_for_adb(self, name: str, timeout_s: int = 180) -> None:
        target = f"{name}.fleet.local:5555"
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            subprocess.run(["adb", "connect", target],
                           capture_output=True, text=True)
            r = subprocess.run(
                ["adb", "-s", target, "shell", "getprop", "sys.boot_completed"],
                capture_output=True, text=True,
            )
            if r.stdout.strip() == "1":
                return
            time.sleep(3)
        raise VMError(f"{name}: ADB not ready")

    def _domain(self, name: str):
        try:
            return self.conn.lookupByName(name)
        except libvirt.libvirtError as e:
            raise VMError(f"domain not found: {name}") from e
