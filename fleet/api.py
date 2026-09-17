"""FastAPI orchestrator."""

import asyncio
import os
import secrets
import subprocess
import tempfile
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from fleet.identity import IdentityService
from fleet.keybox import KeyboxManager, KeyboxUnavailable
from fleet.vm import VMController, VMError


class Config:
    KEYBOX_POOL_URL = os.environ["KEYBOX_POOL_URL"]
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    LIBVIRT_URI = os.environ.get("LIBVIRT_URI", "qemu:///system")
    IMAGE_DIR = os.environ.get("IMAGE_DIR", "/var/lib/libvirt/images")
    TEMPLATE_DIR = os.environ.get("TEMPLATE_DIR", "/opt/fleet/fleet/templates")
    GOLD_IMAGE = os.environ.get(
        "GOLD_IMAGE", "/var/lib/libvirt/images/gold.qcow2"
    )
    TEE_DEVICE = os.environ.get("TEE_DEVICE", "/dev/tee0")


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = aioredis.from_url(Config.REDIS_URL)
    vmctl = VMController(
        conn_uri=Config.LIBVIRT_URI,
        image_dir=Config.IMAGE_DIR,
        template_dir=Config.TEMPLATE_DIR,
        gold_image=Config.GOLD_IMAGE,
        tee_device=Config.TEE_DEVICE,
    )
    keybox = KeyboxManager(Config.KEYBOX_POOL_URL, redis_client)
    try:
        await keybox.fetch_pool()
    except Exception as exc:
        print(f"[lifespan] keybox pool unavailable: {exc}")

    app.state.redis = redis_client
    app.state.vmctl = vmctl
    app.state.keybox = keybox
    app.state.identity = IdentityService()

    try:
        yield
    finally:
        await redis_client.aclose()


app = FastAPI(title="Fleet Orchestrator", lifespan=lifespan)


class CreateRequest(BaseModel):
    name: str = Field(..., pattern=r"^[a-z0-9][a-z0-9\-]{1,62}$")
    profile: str = "pixel4"
    cpu_cores: int = Field(4, ge=1, le=16)
    ram_gb: int = Field(8, ge=2, le=32)


async def _apply_identity(vmctl, name, identity, keybox_content):
    target = f"{name}.fleet.local:5555"
    for k, v in (
        ("ro.product.model", identity["model"]),
        ("ro.product.manufacturer", identity["manufacturer"]),
        ("ro.serialno", identity["serial"]),
    ):
        vmctl.shell(name, f"su -c \"setprop {k} '{v}'\"")

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(keybox_content)
        path = tmp.name
    try:
        subprocess.run(
            ["adb", "-s", target, "push", path,
             "/data/local/tmp/keybox.xml"],
            check=True, capture_output=True,
        )
        vmctl.shell(
            name,
            "su -c 'cp /data/local/tmp/keybox.xml "
            "/data/adb/tricky_store/keybox.xml && "
            "chmod 644 /data/adb/tricky_store/keybox.xml'",
        )
    finally:
        os.unlink(path)

    for pkg in (
        "com.google.android.gms",
        "com.google.android.gsf",
        "com.android.vending",
    ):
        vmctl.shell(name, f"pm clear {pkg}")

    vmctl.shell(name, "reboot")
    await asyncio.sleep(30)
    vmctl.wait_for_adb(name, timeout_s=120)


async def _verify_attestation(vmctl, name):
    return vmctl.shell(
        name,
        "am broadcast -a com.google.android.gms.INTEGRITY_CHECK",
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/instances")
async def create_instance(req: CreateRequest):
    vmctl = app.state.vmctl
    keybox = app.state.keybox
    identity = app.state.identity.generate(req.profile)
    mac = "52:54:00:" + ":".join(
        f"{secrets.randbelow(256):02x}" for _ in range(3)
    )

    try:
        vmctl.clone(req.name, req.cpu_cores, req.ram_gb, mac)
    except VMError as e:
        raise HTTPException(500, f"clone: {e}")

    try:
        kb = await keybox.assign(req.name, req.profile)
    except KeyboxUnavailable:
        vmctl.destroy(req.name)
        raise HTTPException(503, "no keybox")

    try:
        vmctl.start(req.name)
        vmctl.wait_for_adb(req.name)
        await _apply_identity(vmctl, req.name, identity, kb.content)
    except VMError as e:
        vmctl.destroy(req.name)
        raise HTTPException(500, f"provision: {e}")

    verdict = await _verify_attestation(vmctl, req.name)
    if "MEETS_DEVICE_INTEGRITY" not in verdict:
        vmctl.destroy(req.name)
        raise HTTPException(500, "attestation failed")

    return {"name": req.name, "profile": req.profile, "state": "running"}


@app.get("/instances/{name}")
async def get_instance(name: str):
    try:
        d = app.state.vmctl._domain(name)
    except VMError:
        raise HTTPException(404)
    return {
        "name": name,
        "state": "running" if d.isActive() else "stopped",
    }


@app.delete("/instances/{name}")
async def destroy_instance(name: str):
    app.state.vmctl.destroy(name)
    return {"name": name, "state": "destroyed"}


@app.post("/instances/{name}/start")
async def start_instance(name: str):
    app.state.vmctl.start(name)
    return {"name": name, "state": "running"}


@app.post("/instances/{name}/stop")
async def stop_instance(name: str):
    app.state.vmctl.stop(name)
    return {"name": name, "state": "stopped"}


@app.get("/instances/{name}/attestation")
async def attestation(name: str):
    verdict = await _verify_attestation(app.state.vmctl, name)
    return {
        "name": name,
        "verdict": verdict,
        "passed": "MEETS_DEVICE_INTEGRITY" in verdict,
    }


@app.post("/instances/{name}/keybox/rotate")
async def rotate_keybox(name: str):
    try:
        kb = await app.state.keybox.rotate(name)
    except KeyboxUnavailable:
        raise HTTPException(503, "no keybox")
    return {"name": name, "keybox_id": kb.keybox_id}


@app.get("/pool/keyboxes")
async def pool_status():
    pool = app.state.keybox.pool
    return {
        "total": len(pool),
        "available": sum(
            1 for kb in pool.values() if kb.uses < KeyboxManager.MAX_USES
        ),
    }
