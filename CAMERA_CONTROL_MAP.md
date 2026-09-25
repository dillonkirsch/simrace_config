# Camera movement and selection control map

Batch 8 adds 47 normalized camera controls and covers 63 previously unmatched
native entries: all 47 remaining AC EVO user-facing camera actions plus 16
overlapping iRacing actions.

## Shared camera movement

| Central direction | iRacing | AC EVO |
| --- | --- | --- |
| Up/down | `CamAltInc` / `CamAltDec` | `InputAction_Camera_PanUp` / `PanDown` |
| Left/right | `CamLatDec` / `CamLatInc` | `InputAction_Camera_PanLeft` / `PanRight` |
| Forward/backward | `CamLongInc` / `CamLongDec` | `InputAction_Camera_Forward` / `Backward` |
| Yaw left/right | `CamYawDec` / `CamYawInc` | `InputAction_Camera_YawLeft` / `YawRight` |
| Pitch up/down | `CamPitchInc` / `CamPitchDec` | `InputAction_Camera_PitchUp` / `PitchDown` |
| Roll left/right | `CamRollDec` / `CamRollInc` | `InputAction_Camera_RollLeft` / `RollRight` |

iRacing's positive/negative coordinate directions are marked `related` until
their on-screen direction is validated. AC EVO's identifiers name the visual
direction explicitly.

## AC EVO speed-specific movement

AC EVO additionally exposes 24 distinct controls: slow and fast variants of
pan up/down/left/right, forward/backward movement, yaw left/right, pitch
up/down, and roll left/right. They map to IDs 1410–1423 and 2410–2423.

## Camera modes and focus

- Drone-camera toggle, free camera, and free onboard camera
- Camera-view reset and cancel-reset
- Camera zoom toggle
- Showroom rotation and showroom internal view
- Focus next car, previous car, and player car; these align with iRacing's
  `FocusNextCar`, `FocusPrevCar`, and `FocusPlayerCar`

After this batch AC EVO has no uncovered user-facing native actions. The 77
iRacing advanced camera-editor and replay commands that followed are documented
in [MEDIA_CONTROL_MAP.md](MEDIA_CONTROL_MAP.md).
