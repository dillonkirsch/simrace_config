# Remaining core and utility control map

Batch 6 completes the chosen core/useful button-action scope with 90 controls.
Native names come from [CONTROL_INVENTORY.md](CONTROL_INVENTORY.md).

Legend: `—` = not exposed in a complete inspected vocabulary; `?` = not
observed in ACC's binding-dependent file; `*` = packed/compound action; `†` =
related but not semantically identical.

## Higher direct gears

| Central controls | iRacing | Other five games |
| --- | --- | --- |
| Gear 10 through Gear 16 | `Gear10` through `Gear16` | — |

## Menu navigation

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Menu up | — | — | `Up` | `510: InputAction_UI_Up` | — | — |
| Menu down | — | — | `Down` | `511: InputAction_UI_Down` | — | — |
| Menu left | — | — | `Left` | `512: InputAction_UI_Left` | — | — |
| Menu right | — | — | `Right` | `513: InputAction_UI_Right` | — | — |
| Menu confirm | — | — | `Forward` † | `516: InputAction_UI_Confirm` | — | — |
| Menu cancel | — | — | `Backward` † | `517: InputAction_UI_Cancel` | — | — |
| Open menu | — | — | ? | `518: InputAction_UI_Menu` | — | — |
| Menu page up | — | — | `CycleLeft` † | `514: InputAction_UI_PageUp` | — | — |
| Menu page down | — | — | `CycleRight` † | `515: InputAction_UI_PageDown` | — | — |

## Mirror adjustment

| Central name | AC EVO native name | Other games |
| --- | --- | --- |
| Cycle mirrors | `161: InputAction_Car_Mirrors_Cycle_X_2` * | — or ACC not observed |
| Tilt mirror up/down | `162: InputAction_Car_Mirrors_Pitch_X_2` * | — or ACC not observed |
| Turn mirror left/right | `163: InputAction_Car_Mirrors_Yaw_X_2` * | — or ACC not observed |
| Increase/decrease mirror FOV | `164: InputAction_Car_Mirrors_Fov_X_2` * | — or ACC not observed |

## Vehicle modes and remaining race utilities

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Toggle H-pattern shifter | — | — | ? | `299: InputAction_Car_H_Shifter_Toggle` | — | — |
| Toggle stability control | — | — | ? | — | `Toggle Stability Control` | — |
| Toggle automatic clutch | — | — | ? | — | `Toggle Auto Clutch` | — |
| Toggle automatic gears | — | — | ? | — | `Toggle Auto Gears` | — |
| Toggle automatic braking | — | — | ? | — | `Toggle Auto Brake` | — |
| Toggle automatic steering | — | — | ? | — | `Toggle Auto Steer` | — |
| Force traction control on | — | — | ? | — | `Traction Control On` | — |
| Force traction control off | — | — | ? | — | `Traction Control Off` | — |
| Toggle retractable headlights | — | — | ? | `135: InputAction_Car_Retractable_HeadLights_Toggle` | — | — |
| Increase/decrease stability-control level | — | — | ? | `149: InputAction_Car_ESC_Cycle_X_2` * | — | — |
| Cycle MGU-H mode | — | `[MGUH_MODE]` | ? | — | — | — |
| Nitrous | — | — | ? | — | `Nitrous` | — |
| Reset dashboard telltales | `TellTaleReset` | — | ? | — | — | — |
| Raise driver hand warning | `HandUpWarning` | — | ? | — | — | — |
| Increase/decrease automatic-shift mode | — | — | ? | — | `Onboard Auto Shift Mode Increase/Decrease` | — |
| Toggle in-car menu | — | — | ? | — | `ICM` | — |
| Restart race | — | — | ? | — | — | `Restart Race` |
| Toggle triple-screen mode | — | — | ? | — | — | `Triples` |
| Optional vehicle animation | — | `[ACTION_CELEBRATE]` + `[ACTION_CLAIM]` † | ? | `913: InputAction_Car_Optional_Animation_X_5` * | — | — |
| Alternate escape | — | — | ? | — | — | `Alternate Esc` |

## Dashboard and view utilities

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Next/previous secondary dashboard page | `DashPage2Inc` / `DashPage2Dec` | — | ? | — | — | — |
| Toggle pit summary | `PitSummaryToggle` | — | ? | — | — | — |
| Toggle driving line | `ToggleDrivingLine` | — | ? | — | — | — |
| Toggle speed and gear display | `ToggleSpeedGearDisplay` | — | ? | — | — | — |
| Toggle radio display | `ToggleRadioDisplay` | — | ? | — | — | — |
| Increase/decrease interface scale | `ScaleUIUp` / `ScaleUIDown` | — | ? | — | — | — |
| Show points of interest | — | — | ? | `523: InputAction_UI_ShowPoi` | — | — |
| Toggle cursor | — | — | ? | — | — | `Toggle Cursor` |
| Look up/down | `LookUp` / `LookDown` | — | ? | — | `Look Up` / `Look Down` | — |

## Quick chat

| Slots | iRacing | Le Mans Ultimate | Other games |
| --- | --- | --- | --- |
| 1–9 | `AutoChat1`–`AutoChat9` | `Quick Chat #1`–`Quick Chat #9` | — or ACC not observed |
| 10–11 | `AutoChat10`–`AutoChat11` | — | — or ACC not observed |
| 12 | `AutoChat12` | `Quick Chat #12` | — or ACC not observed |
| 13–15 | `AutoChat13`–`AutoChat15` | — | — or ACC not observed |

## Audio, voice, and chat

| Central name | iRacing | Automobilista 2 | Other games |
| --- | --- | --- | --- |
| Mute selected driver | `VChatDriverMute` | — | — or ACC not observed |
| Voice-chat volume up/down | `VChatVolumeUp` / `VChatVolumeDown` | — | — or ACC not observed |
| Spotter volume up/down | `SPCCVolumeUp` / `SPCCVolumeDown` | — | — or ACC not observed |
| Toggle spotter lap times | `SPCCToggleLapTimes` | — | — or ACC not observed |
| Request damage report | `SPCCDamageReport` | — | — or ACC not observed |
| Request weather report | `SPCCWeatherReport` | — | — or ACC not observed |
| Master volume up/down | `MasterVolumeUp` / `MasterVolumeDown` | — | — or ACC not observed |
| LFE volume up/down | `LFEVolumeUp` / `LFEVolumeDown` | — | — or ACC not observed |
| TrueForce volume up/down | `TrueForceVolumeUp` / `TrueForceVolumeDown` | — | — or ACC not observed |
| Force-feedback tone up/down | — | `Increase Force Feedback Tone` / `Decrease Force Feedback Tone` | — or ACC not observed |
| Reply in text chat | `TChatReply` | — | — or ACC not observed |
| Toggle text-chat display | `TChatToggle` | — | — or ACC not observed |

The structured crosswalk in `sim_controls_manager.control_names` contains all
90 individual controls and the full notes for compound and related mappings.

