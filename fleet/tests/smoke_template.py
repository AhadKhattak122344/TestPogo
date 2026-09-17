"""Smoke test for guest.xml.j2 rendering."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jinja2 import Environment, FileSystemLoader


def main() -> int:
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    xml = env.get_template("guest.xml.j2").render(
        name="guest-001",
        memory_mb=8192,
        vcpus=4,
        mac="52:54:00:aa:bb:cc",
        disk_path="/var/lib/libvirt/images/guest-001.qcow2",
        tee_device="/dev/tee0",
    )

    checks = [
        ("<name>guest-001</name>", xml),
        ("<memory unit='MiB'>8192</memory>", xml),
        ("<vcpu>4</vcpu>", xml),
        ("aarch64", xml),
        ("AAVMF_CODE.fd", xml),
        ("guest-001_VARS.fd", xml),
        ("/dev/tee0", xml),
        ("52:54:00:aa:bb:cc", xml),
        ("host-passthrough", xml),
    ]

    for needle, haystack in checks:
        assert needle in haystack, f"missing: {needle}"

    print("Template renders OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
