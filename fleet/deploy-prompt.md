# ARM64 Host Deployment

You are on an ARM64 Ubuntu host. I am deploying a fleet control plane
that manages Android guests through KVM + libvirt + OP-TEE. All the
Python code already exists at /opt/fleet. Do not rewrite it. Do not
summarize it. Do not explain it.

Your job is to bring this host from a fresh Ubuntu install to a state
where `fleet/scripts/provision_instance.sh guest-001 pixel4` returns
PASS.

Work through the phases below in order. After each phase, run the
verification command shown. If verification fails, stop and print:

  PHASE <n> FAILED: <reason>

Do not proceed to the next phase until the current one passes.

------------------------------------------------------------
PHASE 1 — Hardware and kernel verification
------------------------------------------------------------

Run and report the exact output of each:

  uname -m
  kvm-ok
  ls -la /dev/kvm
  ls -la /dev/tee0
  ls -la /dev/teepriv0
  dmesg | grep -iE "optee|smmu|trusted firmware" | head -30

Verification: uname -m must be aarch64, /dev/kvm must exist, and
/dev/tee0 must exist. If /dev/tee0 is missing, print PHASE 1 FAILED:
TEE_NOT_EXPOSED and stop.

------------------------------------------------------------
PHASE 2 — Install system packages
------------------------------------------------------------

  sudo apt update
  sudo apt install -y qemu-system-arm qemu-efi-aarch64 \
      libvirt-daemon-system libvirt-clients virtinst \
      bridge-utils zfsutils-linux optee-client optee-test \
      python3-pip python3-venv adb ansible redis-server

Verification:
  virsh version | head -2
  systemctl is-active libvirtd
  systemctl is-active tee-supplicant
  redis-cli ping

All must report active or version output. Otherwise PHASE 2 FAILED.

------------------------------------------------------------
PHASE 3 — Configure networking and storage
------------------------------------------------------------

Read /opt/fleet/inventory.ini to find the host IP. Detect the primary
network interface. Create /etc/netplan/01-br0.yaml that bridges that
interface into br0 with a static IP, gateway, and DNS. Apply netplan.

  sudo netplan apply

Verify:
  ip addr show br0
  virsh pool-list --all

If the libvirt pool "guests" is not defined, run:

  virsh pool-define-as guests dir --target /var/lib/libvirt/images
  virsh pool-start guests
  virsh pool-autostart guests

Verification: br0 has an IP and the guests pool is active.

------------------------------------------------------------
PHASE 4 — Deploy the Python control plane
------------------------------------------------------------

  cd /opt/fleet
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

Edit /opt/fleet/env.sh and set KEYBOX_POOL_URL to a URL that returns
JSON in this shape:

  {"keyboxes":[{"id":"kb-001","content":"<xml>...</xml>","profile":"pixel4"}]}

If you do not have a keybox URL yet, print PHASE 4 BLOCKED:
KEYBOX_POOL_URL_REQUIRED and stop. Nothing else can pass attestation
without real keyboxes.

Verification:
  source /opt/fleet/env.sh
  python -c "from fleet.identity import IdentityService; print(IdentityService().generate('pixel4'))"

Must print a dict with android_id, imei, mac_address, serial, model,
manufacturer.

------------------------------------------------------------
PHASE 5 — Run unit tests
------------------------------------------------------------

  cd /opt/fleet
  source .venv/bin/activate
  PYTHONPATH=/opt/fleet pytest fleet/tests/ -v

Verification: all tests must pass. If any fail, print PHASE 5 FAILED
and the failing test name.

------------------------------------------------------------
PHASE 6 — Verify gold image exists
------------------------------------------------------------

  ls -lh /var/lib/libvirt/images/gold.qcow2

If it does not exist, print PHASE 6 BLOCKED: GOLD_IMAGE_MISSING and
stop. The gold image must be built separately and must already pass
attestation on its own before the API can use it.

Verification: the file exists and is larger than 10 GB.

------------------------------------------------------------
PHASE 7 — Start the API as a systemd service
------------------------------------------------------------

Write /etc/systemd/system/fleet-api.service with:

  [Unit]
  Description=Fleet Orchestrator API
  After=network.target libvirtd.service redis-server.service

  [Service]
  Type=simple
  User=root
  WorkingDirectory=/opt/fleet
  EnvironmentFile=/opt/fleet/env.sh
  ExecStart=/opt/fleet/.venv/bin/uvicorn fleet.api:app --host 0.0.0.0 --port 8000
  Restart=on-failure

  [Install]
  WantedBy=multi-user.target

Then:

  sudo systemctl daemon-reload
  sudo systemctl enable --now fleet-api

Verification:
  sleep 5
  curl -s http://localhost:8000/health

Must return {"status":"ok"}. Otherwise:

  journalctl -u fleet-api --no-pager | tail -50

and print PHASE 7 FAILED with the last error line.

------------------------------------------------------------
PHASE 8 — Provision one instance
------------------------------------------------------------

  chmod +x /opt/fleet/fleet/scripts/provision_instance.sh
  /opt/fleet/fleet/scripts/provision_instance.sh guest-001 pixel4

This will take 3 to 10 minutes. Watch the output. Do not interrupt it.

Verification: the script must print PASS guest-001.

If it prints FAIL, immediately capture:

  curl -s http://localhost:8000/instances/guest-001/attestation
  journalctl -u fleet-api --no-pager | tail -100
  virsh list --all
  ls -lh /var/lib/libvirt/images/

Print PHASE 8 FAILED with those outputs and stop.

------------------------------------------------------------
PHASE 9 — Report
------------------------------------------------------------

Print exactly this block and nothing else:

  HOST: <uname -n>
  KERNEL: <uname -r>
  TEE: <ls /dev/tee0 result>
  LIBVIRT: <virsh version first line>
  POOL: <virsh pool-list result>
  API: <curl health result>
  KEYBOXES_TOTAL: <curl /pool/keyboxes result>
  INSTANCE_001: <curl /instances/guest-001/attestation result>
  RESULT: PASS or FAIL

If RESULT is PASS, print:

  NEXT: scale by running provision_instance.sh with guest-002 through
  guest-N. Do not scale past the number of keyboxes available in the
  pool.

------------------------------------------------------------
RULES
------------------------------------------------------------

- Do not modify any file under /opt/fleet unless a phase explicitly
  tells you to.
- Do not install packages outside phase 2.
- Do not skip verification steps.
- Do not continue past a failed verification.
- If any command asks for input, do not guess. Print PHASE <n>
  BLOCKED: <what you need> and stop.
- Use only the shell. Do not write Python scripts to wrap shell
  commands.
