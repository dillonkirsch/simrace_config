# Suspension, hybrid, and communication control map

Batch 5 adds 50 normalized controls. Native names come from the installed-file
inventory in [CONTROL_INVENTORY.md](CONTROL_INVENTORY.md).

Legend: `—` = not exposed in a complete inspected vocabulary; `?` = not
observed in ACC's binding-dependent file; `*` = packed/compound action; `†` =
related but not semantically identical.

## Additional brake, TC, and per-corner shock controls

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Increase miscellaneous brake setting | `BrakeMiscInc` | — | ? | — | — | — |
| Decrease miscellaneous brake setting | `BrakeMiscDec` | — | ? | — | — | — |
| Increase traction control 3 | `TractionControl3Inc` | — | ? | — | — | — |
| Decrease traction control 3 | `TractionControl3Dec` | — | ? | — | — | — |
| Increase traction control 4 | `TractionControl4Inc` | — | ? | — | — | — |
| Decrease traction control 4 | `TractionControl4Dec` | — | ? | — | — | — |
| Increase left-front shock | `ShockLeftFrontInc` | — | ? | — | — | — |
| Decrease left-front shock | `ShockLeftFrontDec` | — | ? | — | — | — |
| Increase right-front shock | `ShockRightFrontInc` | — | ? | — | — | — |
| Decrease right-front shock | `ShockRightFrontDec` | — | ? | — | — | — |
| Increase left-rear shock | `ShockLeftRearInc` | — | ? | — | — | — |
| Decrease left-rear shock | `ShockLeftRearDec` | — | ? | — | — | — |
| Increase right-rear shock | `ShockRightRearInc` | — | ? | — | — | — |
| Decrease right-rear shock | `ShockRightRearDec` | — | ? | — | — | — |

## Dampers and active suspension

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Increase front bump damping | — | — | ? | `231: InputAction_Car_Front_Bump_Damper_Cycle_X_2` * | — | — |
| Decrease front bump damping | — | — | ? | `231: InputAction_Car_Front_Bump_Damper_Cycle_X_2` * | — | — |
| Increase front rebound damping | — | — | ? | `232: InputAction_Car_Front_Rebound_Damper_Cycle_X_2` * | — | — |
| Decrease front rebound damping | — | — | ? | `232: InputAction_Car_Front_Rebound_Damper_Cycle_X_2` * | — | — |
| Increase rear bump damping | — | — | ? | `233: InputAction_Car_Rear_Bump_Damper_Cycle_X_2` * | — | — |
| Decrease rear bump damping | — | — | ? | `233: InputAction_Car_Rear_Bump_Damper_Cycle_X_2` * | — | — |
| Increase rear rebound damping | — | — | ? | `234: InputAction_Car_Rear_Rebound_Damper_Cycle_X_2` * | — | — |
| Decrease rear rebound damping | — | — | ? | `234: InputAction_Car_Rear_Rebound_Damper_Cycle_X_2` * | — | — |
| Increase active-suspension damping | — | — | ? | — | `ActiveSusp Damping Increase` | — |
| Decrease active-suspension damping | — | — | ? | — | `ActiveSusp Damping Decrease` | — |
| Increase suspension reaction speed | — | — | ? | — | `ActiveSusp Reaction Speed Increase` | — |
| Decrease suspension reaction speed | — | — | ? | — | `ActiveSusp Reaction Speed Decrease` | — |

## Hybrid and special brake-system actions

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Increase fixed MGU-K deployment | `MGUKDeployFixedInc` | — | ? | — | — | — |
| Decrease fixed MGU-K deployment | `MGUKDeployFixedDec` | — | ? | — | — | — |
| Toggle ERS heat charging | — | — | ? | `1702: InputAction_Car_Ers_Heat_Charging_Toggle` | — | — |
| Toggle right-front brake attachment | `RFBrakeAttachedToggle` | — | ? | — | — | — |
| Toggle fuel no-cut mode | `FuelNoCutToggle` | — | ? | — | — | — |
| Hold hybrid boost | `HysBoostHold` | — | ? | — | — | — |
| Hold hybrid regeneration | `HysRegenHold` | — | ? | — | — | — |
| Toggle hybrid no-boost mode | `HysNoBoostToggle` | — | ? | — | — | — |

## Cockpit information, communication, and FFB

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Tilt seat up | — | — | ? | — | `Seat Angle Up` | — |
| Tilt seat down | — | — | ? | — | `Seat Angle Down` | — |
| Reset seat position | — | — | ? | — | `Reset Seat Position` | — |
| Cycle track map | — | — | ? | — | — | `Driver Overlay Cycle Track Map` |
| Open map | — | — | ? | `524: InputAction_UI_OpenMap` | — | — |
| Show vehicle status | — | — | ? | — | — | `Vehicle Status` |
| Show driver list | — | — | ? | — | `Driver List` | — |
| Cycle lap information | — | — | ? | — | `Cycle Lap Info` | — |
| Next radio station | — | — | ? | — | `Next Radio Station` | — |
| Open text chat | `TChatInitiate` | — | ? | — | `Realtime Chat` | `Realtime Chat` |
| Next voice-chat channel | `VChatChannelNext` | — | ? | — | — | — |
| Previous voice-chat channel | `VChatChannelPrev` | — | ? | — | — | — |
| Mute voice chat | `VChatMute` | — | ? | — | — | — |
| Mute spotter | `SPCCShutUp` † | — | ? | — | — | — |
| Reset force feedback | — | — | ? | — | — | `Reset Force Feedback` |
| Automatically adjust force feedback | `AutoFFB` | — | ? | — | — | — |

The structured crosswalk in `sim_controls_manager.control_names` contains the
full notes explaining each compound or related mapping.

