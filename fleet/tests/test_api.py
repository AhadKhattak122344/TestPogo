import os
os.environ.setdefault("KEYBOX_POOL_URL", "http://localhost:6379")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LIBVIRT_URI", "qemu:///system")
os.environ.setdefault("IMAGE_DIR", "/var/lib/libvirt/images")
os.environ.setdefault("TEMPLATE_DIR", "/opt/fleet/fleet/templates")
os.environ.setdefault("GOLD_IMAGE", "/var/lib/libvirt/images/gold.qcow2")
os.environ.setdefault("TEE_DEVICE", "/dev/tee0")

import subprocess as _subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from fleet.api import app


@pytest.fixture
def client():
    fake_vm = MagicMock()
    fake_vm.clone.return_value = "/tmp/disk.qcow2"
    fake_vm.shell.return_value = "MEETS_DEVICE_INTEGRITY"
    fake_vm.wait_for_adb.return_value = None
    fake_vm._domain.return_value.isActive.return_value = True

    fake_kb = AsyncMock()
    fake_kb.assign.return_value = MagicMock(
        keybox_id="kb1", content=b"<keybox/>", profile="pixel4", uses=1
    )
    fake_kb.pool = {}

    patcher = patch("fleet.api.subprocess.run", return_value=MagicMock(returncode=0))
    patcher.start()

    with TestClient(app) as c:
        app.state.vmctl = fake_vm
        app.state.keybox = fake_kb
        yield c

    patcher.stop()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_create(client):
    r = client.post("/instances", json={"name": "g1", "profile": "pixel4"})
    assert r.status_code == 200, r.text


def test_bad_name(client):
    r = client.post("/instances", json={"name": "BAD NAME"})
    assert r.status_code == 422


def test_attestation(client):
    r = client.get("/instances/g1/attestation")
    assert r.status_code == 200
    assert r.json()["passed"] is True


def test_destroy(client):
    r = client.delete("/instances/g1")
    assert r.status_code == 200
