# Common race-control name map

This second crosswalk batch covers controls commonly placed on a wheel or
button box. Native names come from the local files and executable action tables
recorded in [CONTROL_INVENTORY.md](CONTROL_INVENTORY.md). The structured source
of truth, including per-cell status and notes, is
`sim_controls_manager.control_names`.

## Visibility and driver view

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Cycle headlights | Not exposed | `[ACTION_HEADLIGHTS]` | `CycleCarLightStages` | `120: InputAction_Car_Light_Cycle_X_2` * | `HeadLights` | `Headlights` |
| Flash headlights | `HeadlightFlash` | `[ACTION_HEADLIGHTS_FLASH]` | Not observed | `121: InputAction_Car_Flashing_Lights` | `High Beam` † | `Headlights Pulse` |
| Cycle wipers | `ToggleWindshieldWipers` | Not exposed | `CycleWiper` | `155: InputAction_Car_Wipers_Cycle_X_2` * | `Wipers` | `Wipers` |
| Horn | Not exposed | `[ACTION_HORN]` | Not observed | `139: InputAction_Car_Horn` | Not exposed | `Horn` |
| Look left | `LookLeft` | `[GLANCELEFT]` | `LookLeft` | `425: InputAction_Camera_LookLeft` | `Look Left` | `Look Left` |
| Look right | `LookRight` | `[GLANCERIGHT]` | `LookRight` | `426: InputAction_Camera_LookRight` | `Look Right` | `Look Right` |
| Look behind | Not exposed | `[GLANCEBACK]` | Not observed | `427: InputAction_Camera_LookBehind` | `Look Back` | `Rear Look` |
| Next driving camera | `NextDrivingCam` | `[ACTION_CHANGE_CAMERA]` | `CycleCamera` | `405: InputAction_Camera_Sequence` † | `Change View` | `Push To change camera view` |

## Car systems and race actions

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Move brake bias forward | `BrakeBiasInc` | `[BALANCEUP]` | `IncreaseBrakeBias` | `148: InputAction_Car_Brake_Bias_Cycle_X_2` * | `Increase Brake Bias` | `Bias Forward` |
| Move brake bias rearward | `BrakeBiasDec` | `[BALANCEDN]` | `DecreaseBrakeBias` | `148: InputAction_Car_Brake_Bias_Cycle_X_2` * | `Decrease Brake Bias` | `Bias Rearward` |
| Increase traction control | `TractionControlInc` | `[TCUP]` | `IncreaseTC` | `140: InputAction_Car_TractionControl_Cycle_X_2` * | `Onboard Traction Control Increase` | `Traction Control Up` |
| Decrease traction control | `TractionControlDec` | `[TCDN]` | `DecreaseTC` | `140: InputAction_Car_TractionControl_Cycle_X_2` * | `Onboard Traction Control Decrease` | `Traction Control Down` |
| Toggle traction control | `TractionControlToggle` | Not exposed | Not observed | Not exposed | `Toggle Traction Control` | Not exposed |
| Increase ABS | `ABSInc` | `[ABSUP]` | Not observed | `144: InputAction_Car_ABS_Cycle_X_2` * | `Increase Abs Strength` | `Antilock Brake System Up` |
| Decrease ABS | `ABSDec` | `[ABSDN]` | Not observed | `144: InputAction_Car_ABS_Cycle_X_2` * | `Decrease Abs Strength` | `Antilock Brake System Down` |
| Toggle ABS | `ABSToggle` | Not exposed | Not observed | Not exposed | `Toggle ABS` | Not exposed |
| DRS | `DRS` | `[DRS]` | Not observed | `1704: InputAction_Car_DRS_Toggle` | `DRS` | `Rear Flap` |
| Overtake / push-to-pass | `PushToPass` | `[KERS]` † | Not observed | `1703: InputAction_Car_Ers_Overtake` | `ERS Mode Overtake` | Not exposed |
| Reset car | `Reset` | Not exposed | Not observed | `525: InputAction_UI_FreeRoamCarReset` † | `Reset Car` | Not exposed |
| Pause | `Pause` | Not exposed | `Pause` | Not exposed | `Pause Game` | Not exposed |

`*` **Compound:** the native identifier packs two directions or actions. The
sub-action encoding still needs to be decoded before writing it.

`†` **Related, not equivalent:** the native command has narrower or different
semantics. In particular, high beam may not be momentary flash, KERS is not a
universal overtake-mode equivalent, camera sequence behavior is unverified,
and AC EVO's reset is specifically for free roam.

As in the basic map, **Not exposed** means a complete relevant vocabulary was
inspected, while **Not observed** means the inspected file is binding-dependent
and absence is not proof that the game lacks the control.
