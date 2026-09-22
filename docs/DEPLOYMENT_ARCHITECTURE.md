# Deployment Architecture

This document describes how PogoMod components flow from source to runtime execution.

## Artifact Flow

```
SOURCE → BUILD → PACKAGE → DEPLOY → RUNTIME
```

---

## 1. Source Layer

### Host Tooling
- **Location**: `android_lab/`, `scripts/`, `tools/`
- **Type**: Python, PowerShell, Bash
- **Build**: None required (interpreted)
- **Output**: Executable scripts and modules

### Backend Infrastructure  
- **Location**: `external/atlas/`, `external/rotom/`
- **Type**: Docker Compose, Node.js
- **Build**: `docker-compose up -d`, `npm run build`
- **Output**: Running containers

### Proprietary Components (External)
- **Atlas APK**: Download from Pokemod distribution
- **Zygisk Module**: Download from Pokemod distribution  
- **Placement**: Store in `artifacts/proprietary/`

---

## 2. Build Layer

### Python Package
```bash
uv sync
python -m compileall android_lab
uv run pytest
```

**Artifacts**:
- `.venv/` - Virtual environment
- `android_lab/__pycache__/` - Compiled bytecode

### Backend Services
```bash
cd external/atlas
docker-compose build
```

**Artifacts**:
- Docker images (local registry)

### Magisk Module (Future)
```bash
tools/windows/build-pogomod-module.ps1
```

**Expected Artifacts**:
- `pogomod-vX.X.X.zip` - Flashable Magisk module

---

## 3. Package Layer

### Component Inventory

| Component | Format | Target Location |
|-----------|--------|-----------------|
| Atlas APK | `.apk` | `/sdcard/Download/Atlas.apk` |
| Pokémon GO | `.apk` | Play Store or sideload |
| eMagisk | `.zip` | Magisk Manager flash |
| PogoMod Module | `.zip` | Magisk Manager flash |
| Config Files | `.json` | `/data/local/tmp/` |

### Configuration Templates

**Atlas Configuration** (`/data/local/tmp/atlas_config.json`):
```json
{
  "rdm_url": "http://192.168.1.100:9001",
  "auth_bearer": "your-secret-token",
  "device_name": "ATV-Bedroom-01",
  "email": "user@example.com",
  "device_token": "atlas-device-token-here"
}
```

**eMagisk Configuration** (`/data/local/tmp/emagisk.config`):
```bash
rdm_check=1
rdm_user=admin
rdm_password=secure-password
rdm_backendURL=http://192.168.1.100:9001
```

---

## 4. Deploy Layer

### Deployment Sequence

```
1. Flash Magisk (if not already rooted)
   └─→ Patch boot image via Magisk Manager

2. Flash eMagisk Module
   └─→ Install via Magisk Manager
   └─→ Reboot device

3. Flash PogoMod Module (when available)
   └─→ Install via Magisk Manager
   └─→ Reboot device

4. Deploy Atlas APK
   └─→ adb install artifacts/proprietary/Atlas.apk

5. Deploy Pokémon GO
   └─→ Install from Play Store or sideload

6. Configure Atlas
   └─→ Push atlas_config.json
   └─→ Grant permissions via ADB

7. Start Services
   └─→ am startservice MappingService
   └─→ Verify via health check
```

### Deployment Scripts (Planned)

```powershell
# tools/windows/deploy-to-device.ps1
.\deploy-to-device.ps1 `
  --serial emulator-5554 `
  --atlas-apk ../artifacts/proprietary/Atlas.apk `
  --config config/atlas-config.json `
  --install-magisk-modules
```

```python
# android_lab/deploy.py
from android_lab.deploy import DeviceDeployer

deployer = DeviceDeployer(serial="emulator-5554")
deployer.install_apk("Atlas.apk")
deployer.push_config("atlas_config.json")
deployer.start_service("MappingService")
```

---

## 5. Runtime Layer

### Service Architecture

```
┌─────────────────────────────────────────────┐
│              Android Device                  │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │         Atlas Application             │   │
│  │  ┌────────────┐  ┌─────────────────┐ │   │
│  │  │  Mapping   │  │    Overlay      │ │   │
│  │  │  Service   │  │    Service      │ │   │
│  │  │  (FG)      │  │    (FG)         │ │   │
│  │  └────────────┘  └─────────────────┘ │   │
│  │  ┌────────────┐  ┌─────────────────┐ │   │
│  │  │  Joystick  │  │     RPC         │ │   │
│  │  │  Service   │  │     Client      │ │   │
│  │  │  (FG)      │  │                 │ │   │
│  │  └────────────┘  └─────────────────┘ │   │
│  └──────────────────────────────────────┘   │
│                    │                         │
│  ┌─────────────────▼──────────────────────┐ │
│  │      Zygisk Injection Module           │ │
│  │  - Process injection into PoGo         │ │
│  │  - Native hooks                        │ │
│  │  - Memory manipulation                 │ │
│  └────────────────────────────────────────┘ │
│                    │                         │
│  ┌─────────────────▼──────────────────────┐ │
│  │         Pokémon GO                      │ │
│  │  - Unity/IL2CPP runtime                │ │
│  │  - Network communication               │ │
│  │  - Game logic                          │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
          │ HTTP/Webhook
          ▼
┌─────────────────────────────────────────────┐
│         RealDeviceMap Backend               │
│  - Device management                        │
│  - Account rotation                         │
│  - Webhook processing                       │
└─────────────────────────────────────────────┘
```

### Service Commands

**Start Mapping Service**:
```bash
adb shell am startservice \
  com.pokemod.atlas/com.pokemod.atlas.services.MappingService
```

**Stop Mapping Service**:
```bash
adb shell am stopservice \
  com.pokemod.atlas/com.pokemod.atlas.services.MappingService
```

**Check Service Status**:
```bash
adb shell dumpsys activity services com.pokemod.atlas
```

**Grant Permissions**:
```bash
# Mock location
adb shell appops set com.pokemod.atlas android:mock_location ignore

# Overlay
adb shell appops set com.pokemod.atlas SYSTEM_ALERT_WINDOW allow

# Foreground service
adb shell appops set com.pokemod.atlas FOREGROUND_SERVICE allow
```

---

## 6. Health Monitoring

### State Machine

```
OFFLINE → BOOTING → ROOT_READY → MODULES_LOADED → SERVICES_RUNNING → READY
   ↑         ↑          ↑              ↑                 ↑
   │         │          │              │                 │
   └─────────┴──────────┴──────────────┴─────────────────┘
                    (Failure Recovery)
```

### Health Checks

| Check | Method | Expected Result |
|-------|--------|-----------------|
| Device Online | `adb devices` | Listed as `device` |
| Root Access | `adb shell id` | `uid=0(root)` |
| Magisk Installed | `adb shell ls /sbin/magisk` | File exists |
| Atlas Installed | `adb shell pm list packages com.pokemod.atlas` | Package listed |
| Mapping Service | `adb shell pidof com.pokemod.atlas:mapping` | PID returned |
| RDM Connection | HTTP GET to RDM API | 200 OK |
| Last Seen | RDM device status | < 5 minutes ago |

### Automated Recovery

eMagisk's `ATVServices.sh` implements:
- Service restart after 6 minutes downtime
- Device reboot after 20 minutes downtime
- RDM connection validation every 4 minutes
- Network interface reset on connection failure

---

## 7. Directory Structure

### Device Layout

```
/
├── data/
│   ├── adb/
│   │   └── magisk.db              # Magisk policy database
│   ├── local/
│   │   └── tmp/
│   │       ├── atlas_config.json  # Atlas configuration
│   │       ├── emagisk.config     # eMagisk settings
│   │       └── emagisk.log        # eMagisk logs
│   └── pokemod/
│       └── modules/               # Future module storage
│
├── sdcard/
│   └── Download/
│       ├── Atlas.apk              # Installer
│       └── EmagiskBackups/        # Configuration backups
│
└── system/
    └── bin/
        ├── bash                   # From eMagisk
        ├── curl                   # From eMagisk
        └── tcpdump                # From eMagisk
```

### Repository Layout

```
/workspace/
├── android_lab/                   # Python tooling
├── artifacts/
│   └── proprietary/               # Downloaded binaries
│       ├── Atlas.apk
│       └── pogomod-module.zip
├── config/
│   ├── atlas-default.yaml
│   └── device-profiles/
├── docs/                          # Documentation
├── external/                      # Upstream repos
│   ├── atlas/
│   ├── emagisk/
│   ├── aegis/
│   └── rotom/
├── scripts/mumu/                  # MuMu automation
└── tools/
    ├── windows/
    └── linux/
```

---

## 8. Security Considerations

### Root Hiding

1. **MagiskHide/DenyList**: Hide root from Pokémon GO
2. **Shamiko**: Enhanced hiding for advanced detection
3. **Play Integrity Fix**: Pass Google's attestation

### Configuration Security

- **Do NOT commit** `atlas_config.json` with real tokens
- **Do NOT commit** RDM credentials
- **Use environment variables** for sensitive values
- **Encrypt** configuration files at rest

### Network Security

- **Use HTTPS** for RDM connections when possible
- **Firewall** RDM ports (9000-9300) from public access
- **Change default passwords** in all services
- **Isolate** backend services in separate network segment

---

## 9. Troubleshooting

### Common Issues

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Atlas crashes on start | Missing permissions | Grant mock location, overlay |
| Service won't start | Not rooted | Verify Magisk installation |
| RDM shows offline | Wrong webhook URL | Check atlas_config.json |
| Injection fails | Android 15 incompatibility | Try KernelSU + NeoZygisk |
| Ban wave | Detection | Review root hiding setup |

### Log Locations

- **eMagisk**: `/data/local/tmp/emagisk.log`
- **Atlas**: `logcat -s Atlas`
- **Magisk**: `/data/adb/magisk.log`
- **RDM**: Docker logs `docker logs atlas-rdm`

---

## 10. Version Compatibility Matrix

| Component | Android 11 | Android 12 | Android 13 | Android 14 | Android 15 |
|-----------|------------|------------|------------|------------|------------|
| Magisk 25.x | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| KernelSU | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| eMagisk 9.6 | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Atlas (latest) | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Standard Zygisk | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| NeoZygisk | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ Tested Working | ⚠️ Known Issues | ❌ Not Compatible

