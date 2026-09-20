# Error 12 Investigation — Stage 1 Baseline

Date: 2026-09-18 14:42Z
Device: MuMu Player (emulator-5554), Android 15 / API 35, Samsung Galaxy A54
Root: Magisk v30.7, `su -c id` = uid=0(root) context=u:r:magisk:s0
Pokemon GO: 0.427.0 installed via `adb install-multiple -r -g`

## Device baseline (no root modification performed)

`adb devices` -> 127.0.0.1:16384, emulator-5554
`adb -s emulator-5554 shell "su -c id"` -> uid=0(root) gid=0(root) context=u:r:magisk:s0

## Location state (target: 40.7580,-73.9855)

mock_location setting = 1
mock_location_app = com.theappninjas.fakegpsjoystick
mock_location_app_op = null (appops grant applied separately: `appops set ... MOCK_LOCATION allow`)

dumpsys appops:
  com.theappninjas.fakegpsjoystick: MOCK_LOCATION (allow)
  FINE_LOCATION (allow), SYSTEM_ALERT_WINDOW (allow), WAKE_LOCK (allow)

dumpsys location providers (Sample 1, 10:51:36Z):
  passive: last location=Location[gps 40.757999,-73.985499 hAcc=3.5953066 et=+45m48s335ms alt=12.653001070022583 mslAlt=45.48045205041474 vel=0.0 mock {Bundle[{satellites=10}]}]
  network provider [mock]: identity=10064/com.theappninjas.fakegpsjoystick
  gps provider [mock]: identity=10064/com.theappninjas.fakegpsjoystick
  GNSS Hardware Model Name: Nemu GPS

dumpsys location providers (Sample 2, 10:52:04Z, ~28s later):
  passive: last location=Location[gps 40.758001,-73.985502 hAcc=4.9279184 et=+46m15s423ms alt=15.689354181289673 mslAlt=48.51680516168183 vel=0.0 mock {Bundle[{satellites=10}]}]
  network provider [mock]: identity=10064/com.theappninjas.fakegpsjoystick
  gps provider [mock]: identity=10064/com.theappninjas.fakegpsjoystick

Mock flag present on all three providers (gps/network/fused). Coordinates match target within 0.0001 deg. Altitude ~12.7-15.7m, accuracy ~3.6-4.9m, elapsed realtime ~45-46m, satellites=10.

## Pokemon GO launch

`am start -n com.nianticlabs.pokemongo/com.nianticproject.holoholo.libholoholo.unity.UnityMainActivity`
Exit 0. PID 12704. UnityMainActivity in focus, holds screen lock, remains top activity through all samples.

Post-notification permission prompt appeared at 10:52:46 (GrantPermissionsActivity), result=2 (DENIED) for POST_NOTIFICATIONS.

## Observation result

ERROR 12 = YES
MAP CORRECT = YES
POKESTOPS/GYMS = NOT OBSERVED
POKEMON SPAWNS = NO

Evidence:
- docs/investigations/pgo_stage1_splash.png (launch frame)
- docs/investigations/pgo_stage2_settled.png (~18s after launch)
- docs/investigations/pgo_stage3_later.png (~33s after launch)
- docs/investigations/pgo_stage4_settled2.png (~53s after launch)
- /tmp/logcat_full.txt (full logcat at time of observation)
- /tmp/loc_now.txt, /tmp/loc_sample1.txt, /tmp/loc_sample2.txt (location dumps)
- /tmp/act_now.txt (activity/task state)
- /tmp/focus_pgo.txt, /tmp/focus_pgo2.txt, /tmp/focus_pgo3.txt (focus state)

Game process stays alive (PID 12704), crash buffer empty, no SIGILL, no crash logs. No Google account chooser appeared — game stays on UnityMainActivity. No map, PokéStops, gyms, or spawns observed.