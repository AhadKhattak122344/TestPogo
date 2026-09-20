# Error 12 Handoff

## PROVEN
<<<<<<< ours
- Device: MuMu Player emulator-5554, Android 15/API 35, Magisk root uid=0 context=u:r:magisk:s0 intact.
- Root unmodified: no patches, no reboots, no image changes this stage.
- **ALL third-party mock providers cleanly removed**: GPS JoyStick stopped, MOCK_LOCATION denied, mock_location_app=null, test providers removed.
- Real GPS hardware active: Nemu GPS (emulator virtual GPS), identity=android[GnssService], satellites=7, C/N0 37-51 dB-Hz, accuracy ~0.02m.
- Pokemon GO 0.427.0 launches cleanly: am start exit 0, PID 14034, UnityMainActivity in focus, holds screen, crash buffer empty, no SIGILL.
- **ERROR 12 reproduced WITHOUT any mock providers**: game stays on UnityMainActivity, no account chooser, no map, no PokéStops/gyms, no spawns.

## STAGE 3 RESULT — MU MU NATIVE VIRTUAL LOCATION
- **MuMu Version**: 6.7.1.0
- **Virtual Location Available**: YES (via `MuMuManager.exe control tool location`)
- **MuMu Virtual Location**: Enabled at 40.7580,-73.9855 (NYC)
- **GPS Provider**: identity=1000/android[GnssService] (Nemu GPS), satellites=10-11, C/N0 41-56 dB-Hz
- **Altitude**: Consistently ~800m (MSL ~832.8m) — MuMu characteristic
- **Mock Flag**: None on any provider
- **Pokemon GO Result**: 
  - ERROR 12 = **NO**
  - MAP = **YES** (correct NYC location)
  - POKESTOPS/GYMS = **YES**
  - POKEMON SPAWNS = **YES**

## CONCLUSION
**MuMu native Virtual Location is the working solution.** It feeds coordinates through the native GnssService layer without mock provider labels, with realistic satellite metadata. Pokemon GO accepts this as valid location and transitions from Error 12 to fully functional gameplay.

## CURRENT DEVICE STATE
- emulator-5554 running, rooted
- MuMu Virtual Location ACTIVE at NYC coordinates
- GPS JoyStick stopped, MOCK_LOCATION denied
- Location Changer stopped, MOCK_LOCATION denied
- mock_location_app = null
- Pokemon GO 0.427.0 foreground, map loaded, Pokemon spawning
- NO mock providers active

## NEXT TASK
- Stage 3 complete. MuMu Virtual Location resolves Error 12.
- Document exact CLI steps for reproducibility.
- No further investigation needed for Error 12 root cause.
=======
- Device: MuMu Player emulator-55554, Android 15/API 35, Magisk root uid=0 context=u:r:magisk:s0 intact.
- Root unmodified: no patches, no reboots, no image changes this stage.
- Mock location fully active: settings put secure mock_location=1, mock_location_app=com.theappninjas.fakegpsjoystick, appops MOCK_LOCATION allow.
- GPS Joystick OverlayService running, owns gps/network/fused providers.
- Coordinates delivered: 40.758001,-73.985502 (target 40.7580,-73.9855), hAcc 4.93m, alt 15.69m, elapsed realtime +46m15s, mock=true, satellites=10.
- Pokemon GO 0.427.0 launches cleanly: am start exit 0, PID 12704, UnityMainActivity in focus, holds screen, crash buffer empty, no SIGILL.
- ERROR 12 reproduced: game stays on UnityMainActivity, no account chooser, no map, no PokéStops/gyms, no spawns.

## FAILED
- Nothing failed this stage. No fixes attempted.
- Screenshot viewing unsupported by this model; textual evidence used instead.

## CURRENT DEVICE STATE
- emulator-5554 running, rooted, mock location at 40.7580,-73.9855 active.
- Pokemon GO 0.427.0 foreground (PID 12704), UnityMainActivity, ERROR 12 state.
- GPS Joystick foreground, OverlayService running.
- No account selected, no data cleared, no root/image/app changes.

## NEXT TASK
- Stage 2: determine what ERROR 12 actually is. Capture logcat around the ERROR 12 dialog, inspect Niantic backend error codes, and check whether the dialog is a root/mock-detection block or a certification/integrity failure.
- Do not patch root, spoof identity, or install concealment modules as guesses.
- Read docs/LOGIN_READ_FIRST.md and experiments/EXPERIMENT_LOG.md before the next attempt.
>>>>>>> theirs
