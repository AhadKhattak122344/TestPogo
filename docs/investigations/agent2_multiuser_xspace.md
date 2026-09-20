# Agent 2 — MuMu Multiuser / XSpace Investigation

Date: 2026-09-18
Device: MuMu Player 6.7.1.0, Android 15 (API 35), Samsung Galaxy A54 (a54x)
ADB: 127.0.0.1:16384

## Summary

**This MuMu instance does NOT have an XSpace-equivalent Android user.** The
screenshot's "Install to user XSpace" step must NOT be copied here.

## Phase 1 — Android Users

Commands run (read-only):

```
adb devices
adb shell pm list users
adb shell cmd user list
adb shell dumpsys user
```

Result:

```
Users:
  UserInfo{0:Owner:4c13} running
```

`dumpsys user` details:

- Current user: 0
- Only user: `UserInfo{0:null:4c13} serialNo=0 isPrimary=true`
- Type: `android.os.usertype.full.SYSTEM`
- State: RUNNING_UNLOCKED
- Has profile owner: false
- Guest restrictions: none
- Device managed: false
- Started users state: [0=RUNNING_UNLOCKED]
- Cached user IDs: [0]
- Max users: 200 (limit reached: false)
- Supports switchable users: false

**Exactly one Android user exists: user 0, the Owner.** No guest users,
no managed profiles, no clone profiles, no work profiles, no secondary users.

## Phase 2 — Pokemon GO User

```
pm path com.nianticlabs.pokemongo
dumpsys package com.nianticlabs.pokemongo
```

- Package: `com.nianticlabs.pokemongo` 0.427.0, uid=10057, arm64-v8a
- `dataDir=/data/user/0/com.nianticlabs.pokemongo`
- Installed via `com.android.shell` (sideloaded base.apk + split_config.arm64_v8a.apk)

**Pokemon GO runs under user 0 only.** There is no other user for it to run
under.

## Phase 3 — MuMu Multi-Instance vs Android Multiuser

MuMu's "multi-instance" feature is **not** the same as Android's built-in
multiple-user mechanism.

Evidence:

- Only one VM directory exists: `C:\...\MuMuPlayer\vms\MuMuPlayerGlobal-15.0-0`
- The `.nemu` file describes a single VirtualBox VM (`data.vdi`, `ota.vdi`)
- Each MuMu instance is a **separate VirtualBox virtual machine** with its own
  Android OS image, its own ADB port (16384), its own `/data` partition
- Android's multi-user mechanism (`pm list users`) operates **inside** one VM
  instance. MuMu does not create secondary Android users inside its VM.

So a second MuMu instance would be a whole separate Android VM — not an
Android "user" or "profile" inside the current VM. This is fundamentally
different from Xiaomi's Dual Apps / XSpace, which creates a secondary Android
user inside one device.

## Phase 4 — LSPosed Multiuser Behavior

LSPosed is **not installed** on this MuMu instance (verified: no lsposed
package, no lsposed .so in `/system_ext/lib64`). Only Magisk
(`com.topjohnwu.magisk`) is present.

However, the general LSPosed multiuser behavior is well documented:

- LSPosed modules are installed per-Android-user, not per-instance
- LSPosed Manager runs on the owner (user 0)
- A module must be installed into a secondary user for that user to be
  affected
- "Install to user XSpace" in the screenshot is **Xiaomi/MIUI-specific**
  terminology for Android's secondary user mechanism

Since this MuMu has only user 0, there is no secondary user to install into.

## Phase 5 — Conclusion

| Question | Answer |
|---|---|
| Does this MuMu have an XSpace-equivalent user? | **NO** |
| Android users present | 1 (user 0, Owner, full SYSTEM user) |
| Pokemon GO user | user 0 |
| Secondary profile | none |
| Screenshot XSpace step applies | **NO** |

The screenshot's XSpace step is a Xiaomi/MIUI feature that leverages Android's
secondary-user API. This MuMu instance exposes only user 0, so the step has
no target and must not be copied.

## Architecture for Agent 3

- Device: MuMu Player VM, Android 15/API 35, Samsung Galaxy A54
- ADB: 127.0.0.1:16384
- Single Android user: 0 (Owner)
- Pokemon GO: user 0, uid 10057, `/data/user/0/com.nianticlabs.pokemongo`
- Magisk present (`com.topjohnwu.magisk`), LSPosed NOT installed
- If multi-instance cloning is needed, it requires a separate MuMu VM
  instance (separate Android OS), not an Android user

## Commands Used

All read-only. No root was required for this investigation.

```
adb devices
adb connect 127.0.0.1:16384
adb shell pm list users
adb shell cmd user list
adb shell dumpsys user
adb shell dumpsys package com.nianticlabs.pokemongo
adb shell pm path com.nianticlabs.pokemongo
adb shell pm list packages
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
```