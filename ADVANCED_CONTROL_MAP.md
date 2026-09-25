# Car setup and cockpit control-name map

Batch 3 adds 50 normalized controls. Native names come from the installed-file
inventory in [CONTROL_INVENTORY.md](CONTROL_INVENTORY.md). This is a vocabulary
crosswalk, not a claim that every native format is writable.

Legend: `—` = not exposed in a complete inspected vocabulary; `?` = not
observed in ACC's binding-dependent file; `*` = packed/compound action; `†` =
related but not semantically identical.

## Powertrain and setup

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Increase fuel mixture | `FuelMixtureInc` | — | ? | — | — | `Increment Mixture` |
| Decrease fuel mixture | `FuelMixtureDec` | — | ? | — | — | `Decrement Mixture` |
| Increase engine map | `EnginePowerInc` † | — | ? | `146: InputAction_Car_Engine_Map_Cycle_X_2` * | `Increase Fuel Mapping` † | `Increment Motor Map` |
| Decrease engine map | `EnginePowerDec` † | — | ? | `146: InputAction_Car_Engine_Map_Cycle_X_2` * | `Decrease Fuel Mapping` † | `Decrement Motor Map` |
| Increase engine braking | `EngineBrakingInc` | `[ENGINE_BRAKE_UP]` | ? | — | — | — |
| Decrease engine braking | `EngineBrakingDec` | `[ENGINE_BRAKE_DN]` | ? | — | — | — |
| Increase turbo boost | `BoostLevelInc` | `[TURBOUP]` | ? | `169: InputAction_Car_Turbo_Level_Cycle_X_2` * | `Increase Turbo Boost` | — |
| Decrease turbo boost | `BoostLevelDec` | `[TURBODN]` | ? | `169: InputAction_Car_Turbo_Level_Cycle_X_2` * | `Decrease Turbo Boost` | — |
| Stiffen front anti-roll bar | `AntiRollFrontInc` | — | ? | — | `Increase Front Anti Roll Bars` | `Inc Front ARB` |
| Soften front anti-roll bar | `AntiRollFrontDec` | — | ? | — | `Decrease Front Anti Roll Bars` | `Dec Front ARB` |
| Stiffen rear anti-roll bar | `AntiRollRearInc` | — | ? | — | `Increase Rear Anti Roll Bars` | `Inc Rear ARB` |
| Soften rear anti-roll bar | `AntiRollRearDec` | — | ? | — | `Decrease Rear Anti Roll Bars` | `Dec Rear ARB` |
| Increase weight jacker | `WeightJackerLeftInc` + `WeightJackerRightInc` * | — | ? | — | `Increase Weight Jacker` | — |
| Decrease weight jacker | `WeightJackerLeftDec` + `WeightJackerRightDec` * | — | ? | — | `Decrease Weight Jacker` | — |
| Increase ERS deployment | `MGUKDeployModeInc` | `[MGUK_DELIVERY_UP]` | ? | `1701: InputAction_Car_Ers_Deployment_Cycle_X_2` * | `ERS Mode Increase` | — |
| Decrease ERS deployment | `MGUKDeployModeDec` | `[MGUK_DELIVERY_DN]` | ? | `1701: InputAction_Car_Ers_Deployment_Cycle_X_2` * | `ERS Mode Decrease` | — |
| Increase ERS regeneration | `MGUKRegenGainInc` | `[MGUK_RECOVERY_UP]` | ? | `1700: InputAction_Car_Ers_Recharge_Cycle_X_2` * | — | `Increment Regeneration` |
| Decrease ERS regeneration | `MGUKRegenGainDec` | `[MGUK_RECOVERY_DN]` | ? | `1700: InputAction_Car_Ers_Recharge_Cycle_X_2` * | — | `Decrement Regeneration` |
| Launch control | `ClutchLaunchAssist` † | — | ? | — | `Launch Control` | `Launch Control` |

## Signals and visibility

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Rain light | — | — | ? | `131: InputAction_Car_Rain_Lights` | — | — |
| Left turn signal | — | — | ? | `132: InputAction_Car_Direction_Light_Left` | — | — |
| Right turn signal | — | — | ? | `133: InputAction_Car_Direction_Light_Right` | — | — |
| Hazard lights | — | — | ? | `134: InputAction_Car_Warning_Lights` | — | — |

## Displays and pit interaction

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Next MFD | `BlackBoxShowNext` † | — | `CycleHudMfd` | `521: InputAction_UI_Cycle_Mfd_Up` | `ICM Cycle` | `Driver Overlay Next MFD` |
| Previous MFD | `BlackBoxShowPrev` † | — | ? | `522: InputAction_UI_Cycle_Mfd_Down` | — | `Driver Overlay Previous MFD` |
| Toggle HUD | `ToggleUIVisibleDrive` † | — | ? | `520: InputAction_UI_ToggleHud` | `Toggle HUD Dials` | `Driver Overlay Toggle HUD` |
| Next dashboard page | `DashPageInc` | — | `DisplayPageUp` | `125: InputAction_Car_Display_Page_Cycle_X_2` * | `Cycle Lap Info` † | — |
| Previous dashboard page | `DashPageDec` | — | `DisplayPageDown` | `125: InputAction_Car_Display_Page_Cycle_X_2` * | — | — |
| Request pit stop | — | — | ? | — | `Request Pit Stop` | `Pit Request` |
| Pit menu up | `BlackBoxPrev` † | — | ? | — | `ICM Up` | `Pit Menu Up` |
| Pit menu down | `BlackBoxNext` † | — | ? | — | `ICM Down` | `Pit Menu Down` |
| Increase pit-menu value | `BlackBoxInc` † | — | ? | — | `ICM Right` | `Pit Menu Inc` |
| Decrease pit-menu value | `BlackBoxDec` † | — | ? | — | `ICM Left` | `Pit Menu Dec` |
| Cycle driving aids | `ToggleDrivingLine` † | — | ? | — | `Driving Aids` | — |
| Cycle HUD mode | — | — | ? | `123: InputAction_Car_Display_Device_Cycle_X_2` * | `Cycle HUD Mode` | `Display Mode` † |

## Cockpit, communication, and system actions

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Increase force-feedback gain | `IncFFB` | — | ? | `168: InputAction_Car_FFB_Gain_X_2` * | `Increase Force Feedback Volume` † | — |
| Decrease force-feedback gain | `DecFFB` | — | ? | `168: InputAction_Car_FFB_Gain_X_2` * | `Decrease Force Feedback Volume` † | — |
| Move seat up | `DCamDrvHeightInc` † | — | ? | — | `Seat Up` | `Adjust Seat Up` |
| Move seat down | `DCamDrvHeightDec` † | — | ? | — | `Seat Down` | `Adjust Seat Down` |
| Move seat forward | — | — | ? | — | `Seat Fore` | `Adjust Seat Fore` |
| Move seat backward | — | — | ? | — | `Seat Aft` | `Adjust Seat Aft` |
| Increase field of view | `DCamFOVInc` | — | ? | `435: InputAction_Camera_FovModifier` † | `Increase FOV` | `Increase Vertical FOV` |
| Decrease field of view | `DCamFOVDec` | — | ? | `435: InputAction_Camera_FovModifier` † | `Reduce FOV` | `Decrease Vertical FOV` |
| Toggle virtual mirror | `ToggleVirtualMirror` | — | ? | `167: InputAction_UI_Toggle_Virtual_Mirror` | — | `Toggle Mirror` |
| Toggle driver labels | — | — | ? | `159: InputAction_UI_CycleNameplateVisibility` | `Opponent Names Toggle` | `Display Vehicle Labels` |
| Push to talk | `VChatPushToTalk` | — | ? | — | — | — |
| Take screenshot | `TriggerScreenshotCapture` | — | ? | — | — | `Screenshot` |
| Recenter VR view | `RecenterHeadMountedDisplay` | — | ? | `535: InputAction_UI_Vr_Settings_Reset` † | `Reset VR` | — |
| Tear off visor | `TearOffVisor` | — | ? | — | — | — |
| Rev limiter | `RevLimiter` | — | ? | — | — | — |

The full notes behind `*` and `†`, including why a candidate is not an exact
equivalent, are stored in `sim_controls_manager.control_names`.
