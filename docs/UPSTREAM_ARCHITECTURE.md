# Upstream Architecture Analysis

## Cloned Repositories Status

### ✅ Successfully Cloned

1. **Atlas-All-In-One** - RealDeviceMap Docker stack for mapping backend
2. **Aegis-All-In-One** - Alternative mapping stack with Unown# tools (Golbat, Dragonite, Rotom)
3. **eMagisk** - Magisk module providing system binaries and ATV services
4. **Rotom** - MITM connector service (Node.js/TypeScript)

### ❌ Failed to Clone

1. **pogo_assets** - Repository clone timed out (may be private or large)

## Key Findings

### NO Android Controller Source Code Found

**Critical Discovery**: None of the cloned repositories contain:
- Android APK source code (no `.gradle`, `.kt`, `.java` files)
- Zygisk injection module source (no `.cpp`, `.cc`, CMakeLists.txt)
- Native hooking libraries
- Overlay service implementation
- Joystick controller code

### What These Repositories Actually Provide

#### 1. Atlas-All-In-One & Aegis-All-In-One
- **Purpose**: Server-side mapping infrastructure (RealDeviceMap/Golbat/Dragonite)
- **Technology**: Docker Compose stacks with MariaDB, ReactMap, monitoring tools
- **Role in Pokemod**: Backend mapping servers that devices connect to
- **NOT**: Android application code or injection modules

#### 2. eMagisk
- **Purpose**: Magisk module providing system utilities
- **Contents**: 
  - Bash, curl, nano, strace, tcpdump binaries
  - Optional ATV service health monitors
  - System properties tweaks
- **Files**: `module.prop`, `service.sh`, `install.sh`
- **Role**: System enhancement module, NOT Pokemod injection

#### 3. Rotom
- **Purpose**: MITM (Man-in-the-Middle) connector service
- **Technology**: Node.js/TypeScript server
- **Function**: Connects MITM traffic to raw processors/scanners
- **Ports**: 7070 (device connections), 7071 (raw processors)
- **Role**: Network traffic routing, NOT Android injection

## Missing Critical Components

The following Pokemod components are **NOT** present in upstream repositories:

| Component | Status | Notes |
|-----------|--------|-------|
| Android Controller APK | ❌ MISSING | No Gradle/Kotlin/Java source |
| Zygisk Injection Module | ❌ MISSING | No C++/NDK source |
| Native Hooking Library | ❌ MISSING | No IL2CPP resolver code |
| Overlay Service | ❌ MISSING | No Android overlay implementation |
| Joystick Service | ❌ MISSING | No touch input manipulation code |
| Frida Scripts | ❌ MISSING | No JavaScript injection scripts |
| LSPosed Module | ❌ MISSING | No Xposed hook definitions |

## Implications

The actual Pokemod Android implementation (Controller + Injection) appears to be:
1. **Proprietary/Closed-source** - Distributed as pre-built APK/modules only
2. **Separate from these infrastructure repos** - These repos only provide server-side tooling
3. **Not available for modification** - Cannot rebuild or customize the core modding functionality

## Available Integration Points

What CAN be implemented locally:

1. **Service Management** - Start/stop Atlas services via ADB commands
2. **Device Configuration** - Configure device connection to RDM/Aegis backends  
3. **Health Monitoring** - Check device status, root availability, module installation
4. **Deployment Automation** - Push pre-built APKs/modules to devices
5. **Network Setup** - Configure MITM routing through Rotom

## Recommended Path Forward

Since the core Pokemod Android source is unavailable:

1. **Treat Pokemod as a black-box dependency** - Use pre-built releases
2. **Focus on host-side tooling** - Build robust deployment and management infrastructure
3. **Implement compatibility layer** - Create adapters between our tools and Pokemod's expected configuration
4. **Document integration points** - Map how our controller communicates with Pokemod services

## Next Steps

1. Download latest Pokemod releases (Atlas APK, modules) from official sources
2. Reverse engineer configuration requirements from Atlas APK
3. Build host-side tooling around known interfaces
4. Create mock/test implementations where interfaces are unknown
