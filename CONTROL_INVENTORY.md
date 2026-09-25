# Installed simulator control-file inventory

Snapshot taken from this PC on 2026-09-24. This is a read-only inventory of files that actually exist locally. No simulator or configuration file was changed.

“Controls” below means action names/IDs stored in the discovered file, not graphics, force-feedback tuning, assists, or calibration-only values.

## Summary

| Game | Local state | Control source | Format | Recoverable controls |
| --- | --- | --- | --- | ---: |
| iRacing | Installed and configured | `Documents\iRacing\...\controls.cfg` | GFCC binary | 369 |
| Assetto Corsa | Installed and configured | `Documents\Assetto Corsa\cfg\controls.ini` | INI | 44 sections |
| Assetto Corsa Competizione | Installed and configured | `Documents\Assetto Corsa Competizione\Config\controls.json` | JSON | 31 current action codes |
| Assetto Corsa EVO | Installed and configured | `Saved Games\ACE\input_*` | Protobuf-style binary | 253 action enum values in executable |
| Automobilista 2 | Installed and configured | `Documents\Automobilista 2\...\default.controllersettings.v1.03.sav` | Binary SAV + executable labels | 108 installed control labels |
| Le Mans Ultimate | Installed and configured | `UserData\Controller\Presets\*.json` | JSON | 110 unique actions |

## iRacing

### Files and types

- Active profile: `C:\Users\Dillon\Documents\iRacing\profiles\controls\Baseline\controls.cfg` — GFCC binary v20, controls table v8, 369 records.
- Test profile: `C:\Users\Dillon\Documents\iRacing\profiles\controls\Test\controls.cfg` — GFCC binary v20, controls table v8, 367 records.
- Legacy/stale file: `C:\Users\Dillon\Documents\iRacing\controls.cfg` — GFCC binary v20, controls table v8, 367 records.
- Calibration files: `C:\Users\Dillon\Documents\iRacing\profiles\controls\<profile>\joyCalib.yaml` — YAML calibration/device data; no action catalog.

Baseline binding record types: axis=4, unbound=178, button=2, key=185.
Baseline contains two records absent from Test and the legacy file: `PitSummaryToggle` and `ToggleUIVisibleDrive`.

### Complete action-name union (369)

```text
Throttle
Throttle2
Brake
Brake2
Clutch
Clutch2
SteerLeft
SteerRight
ShiftDown
ShiftDown2
ShiftUp
ShiftUp2
GearReverse
GearNeutral
Gear1
Gear2
Gear3
Gear4
Gear5
Gear6
Gear7
Gear8
Gear9
Gear10
Gear11
Gear12
Gear13
Gear14
Gear15
Gear16
Ignition
Starter
TellTaleReset
PitSpeedLimiter
RevLimiter
PushToPass
DRS
TractionControlArm
Handbrake
Reset
LookLeft
LookRight
LookUp
LookDown
HandUpWarning
TearOffVisor
ToggleWindshieldWipers
TriggerWindshieldWipers
ClutchLaunchAssist
BrakeBiasInc
BrakeBiasDec
BrakeBiasLevel
BrakeBiasFineInc
BrakeBiasFineDec
BrakeBiasFineLevel
PeakBrakeBiasInc
PeakBrakeBiasDec
PeakBrakeBiasLevel
BrakeMiscInc
BrakeMiscDec
BrakeMiscLevel
AntiRollFrontInc
AntiRollFrontDec
AntiRollFrontLevel
AntiRollRearInc
AntiRollRearDec
AntiRollRearLevel
FuelMixtureInc
FuelMixtureDec
FuelMixtureLevel
BoostLevelInc
BoostLevelDec
BoostLevelLevel
LaunchRPMInc
LaunchRPMDec
LaunchRPMLevel
WeightJackerLeftInc
WeightJackerLeftDec
WeightJackerLeftLevel
WeightJackerRightInc
WeightJackerRightDec
WeightJackerRightLevel
ShockLeftFrontInc
ShockLeftFrontDec
ShockLeftFrontLevel
ShockRightFrontInc
ShockRightFrontDec
ShockRightFrontLevel
ShockLeftRearInc
ShockLeftRearDec
ShockLeftRearLevel
ShockRightRearInc
ShockRightRearDec
ShockRightRearLevel
QTapeInc
QTapeDec
QTapeLevel
ABSInc
ABSDec
ABSLevel
TractionControlInc
TractionControlDec
TractionControlLevel
TractionControl2Inc
TractionControl2Dec
TractionControl2Level
TractionControl3Inc
TractionControl3Dec
TractionControl3Level
TractionControl4Inc
TractionControl4Dec
TractionControl4Level
PowerSteeringInc
PowerSteeringDec
PowerSteeringLevel
DashPageInc
DashPageDec
DashPageLevel
DashPage2Inc
DashPage2Dec
DashPage2Level
WingFrontInc
WingFrontDec
WingFrontLevel
WingRearInc
WingRearDec
WingRearLevel
DiffPreloadInc
DiffPreloadDec
DiffPreloadLevel
DiffEntryInc
DiffEntryDec
DiffEntryLevel
DiffMiddleInc
DiffMiddleDec
DiffMiddleLevel
DiffExitInc
DiffExitDec
DiffExitLevel
EngineBrakingInc
EngineBrakingDec
EngineBrakingLevel
EnginePowerInc
EnginePowerDec
EnginePowerLevel
ThrottleShapeInc
ThrottleShapeDec
ThrottleShapeLevel
MGUKRegenGainInc
MGUKRegenGainDec
MGUKRegenGainLevel
MGUKDeployModeInc
MGUKDeployModeDec
MGUKDeployModeLevel
MGUKDeployFixedInc
MGUKDeployFixedDec
MGUKDeployFixedLevel
FuelCutPositionInc
FuelCutPositionDec
FuelCutPositionLevel
TractionControlToggle
ABSToggle
HeadlightFlash
RFBrakeAttachedToggle
FuelNoCutToggle
LowFuelAccept
HysBoostHold
HysRegenHold
HysNoBoostToggle
InLapToggle
FCYToggle
DCamFOVInc
DCamFOVDec
DCamVanishYInc
DCamVanishYDec
DCamDrvHeightInc
DCamDrvHeightDec
ToggleVirtualMirror
ToggleDrivingLine
ToggleEditLayoutMode
ToggleSpeedGearDisplay
ToggleRadioDisplay
ToggleirsdkDiskLogging
ToggleSystemMeterDisplay
ToggleVideoTimerDisplay
ToggleVideoCapture
TriggerScreenshotCapture
TriggerGiantScreenshotCapture
ReportLatency
IrsdkDriverMarker
AutoFFB
IncFFB
DecFFB
TChatInitiate
TChatReply
TChatToggle
NextDrivingCam
PrevDrivingCam
SplitsDeltaNext
SplitsDeltaPrev
ToggleRefCar
RecenterTiltAxis
ReloadCarTexture
AutoChat1
AutoChat2
AutoChat3
AutoChat4
AutoChat5
AutoChat6
AutoChat7
AutoChat8
AutoChat9
AutoChat10
AutoChat11
AutoChat12
AutoChat13
AutoChat14
AutoChat15
BlackBoxShowNext
BlackBoxShowPrev
BlackBoxF1
BlackBoxF2
BlackBoxF3
BlackBoxF4
BlackBoxF5
BlackBoxF6
BlackBoxF7
BlackBoxF8
BlackBoxF9
BlackBoxF10
BlackBoxF11
BlackBoxF12
BlackBoxInc
BlackBoxDec
BlackBoxNext
BlackBoxPrev
BlackBoxToggle
BlackBoxSize
DashBoxToggle
PitSummaryToggle
NextRpyCamCam
PrevRpyCamCam
NextRpyCamGroup
PrevRpyCamGroup
RpyToStart
RpySessionRew
RpyRew
RpyFrameRew
RpyPausePlay
RpyStop
RpyIncreaseRate
RpyFrameAdv
RpyFF
RpySessionFF
RpyLapFF
RpyLapRew
RpyIncidentFF
RpyIncidentRew
RpyToEnd
FocusNextCar
FocusPrevCar
FocusPlayerCar
RecenterHeadMountedDisplay
ToggleRadar
ScaleUIUp
ScaleUIDown
ToggleUIVisible
ToggleUIVisibleDrive
VChatPushToTalk
VChatChannelNext
VChatChannelPrev
VChatVolumeUp
VChatVolumeDown
VChatMute
VChatDriverMute
SPCCVolumeUp
SPCCVolumeDown
SPCCShutUp
SPCCToggleLapTimes
SPCCAnounceLeaderLine
SPCCDamageReport
SPCCWeatherReport
LFEVolumeUp
LFEVolumeDown
TrueForceVolumeUp
TrueForceVolumeDown
MasterVolumeUp
MasterVolumeDown
CamFOVInc
CamFOVDec
CamExposureInc
CamExposureDec
CamShakePctInc
CamShakePctDec
CamVanishXInc
CamVanishXDec
CamVanishYInc
CamVanishYDec
CamLongInc
CamLongDec
CamLatInc
CamLatDec
CamAltInc
CamAltDec
CamYawInc
CamYawDec
CamPitchInc
CamPitchDec
CamRollInc
CamRollDec
CamNearPlaneBiasInc
CamNearPlaneBiasDec
CamListenerGainBiasInc
CamListenerGainBiasDec
CamListenerGainBiasAuto
CamAcquireStart
CamAcquireEnd
CamToggleAimType
CamToggleSensorType
CamTogglePosType
CamToggleZoom
CamMoveMultInc
CamMoveMultDec
CamToggleMoveMultAccel
CamToggleMoveMultScale
CamToggleParabolicMic
CamTogglePitchGyro
CamToggleRollGyro
CamToggleAcquire
CamRadInc
CamRadDec
CamVelInc
CamVelDec
CamInsert
CamRemove
CamCopy
CamPaste
GroupCopy
GroupPaste
CamLoadTrack
CamSaveTrack
CamLoadCar
CamSaveCar
CamToggleDisplay
CamToggleBeyondFence
CamToggleInCockpit
CamToggleCamCtrlActive
CamToggleHasWeight
CamToggleUseShotQ
CamToggleCamLocalCopy
CamToggleCamTool
CamToggleFocus
CamFocusDepthInc
CamFocusDepthDec
CamFNumberInc
CamFNumberDec
CamToggleIsIR
CamIRMinTempInc
CamIRMinTempDec
CamIRMaxTempInc
CamIRMaxTempDec
SaveActiveReset
RunActiveReset
CustSectSetStart
CustSectSetEnd
FuelToEndToggle
FuelToEndMarginInc
FuelToEndMarginDec
Pause
```

## Assetto Corsa

### Files and types

- Live controls: `C:\Users\Dillon\Documents\Assetto Corsa\cfg\controls.ini` — text INI.
- Shipped default: `C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\cfg\controls.ini` — text INI with the same section set.
- Saved presets: `C:\Users\Dillon\Documents\Assetto Corsa\cfg\controllers\presets\*.ini` — text INI.
- Shipped presets: `C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\cfg\controllers\presets\*.ini` — text INI.
- Device identity: `C:\Users\Dillon\Documents\Assetto Corsa\cfg\controllers\d94e3400-6276-11f1-8003-444553540000.ini` — text INI containing only a `[CONTROLLER]` identity section.

### Sections in the live controls file (44)

The action-bearing sections are the axes and button actions. `HEADER`, `ADVANCED`, `X360`, `KEYBOARD`, `CONTROLLERS`, and the `FF_*` sections are mode/tuning sections rather than bindable actions. `SHIFTER` contains gear 1–7 and reverse fields.

```text
HEADER
ADVANCED
X360
KEYBOARD
CONTROLLERS
STEER
FF_TWEAKS
FF_ENHANCEMENT
FF_ENHANCEMENT_2
FF_SKIP_STEPS
THROTTLE
BRAKES
CLUTCH
BALANCEUP
BALANCEDN
KERS
DRS
GEARUP
GEARDN
STARTER
HANDBRAKE
SHIFTER
ACTION_HEADLIGHTS
ACTION_HORN
GLANCELEFT
GLANCERIGHT
GLANCEBACK
ACTION_CHANGE_CAMERA
ACTION_CELEBRATE
ACTION_CLAIM
TURBODN
TURBOUP
ABSUP
ABSDN
TCUP
TCDN
ACTION_HEADLIGHTS_FLASH
ENGINE_BRAKE_UP
ENGINE_BRAKE_DN
MGUK_DELIVERY_UP
MGUK_DELIVERY_DN
MGUK_RECOVERY_UP
MGUK_RECOVERY_DN
MGUH_MODE
```

## Assetto Corsa Competizione

### Files and types

- Live controls: `C:\Users\Dillon\Documents\Assetto Corsa Competizione\Config\controls.json` — 12,996-byte JSON document.
- The root `commandDevices` array contains three detected devices: `P2000 Haptic`, `Logitech G29 Driving Force Racing Wheel USB`, and `MOZA SRP2 pedals`.
- Each device can contain `uICommandButtonList`, `raceCommandButtonList`, and `raceCommandAxisList` arrays. Button records store instant/extended action codes; axis records store `axisCode`.
- Only the Logitech G29 record currently contains mappings: 8 UI button records, 21 race button records, and 4 race-axis records.
- Force-feedback settings are stored separately in `C:\Users\Dillon\Documents\Assetto Corsa Competizione\Config\ffbUserSettings.json`; they are not action mappings.

### Complete action-code union currently stored (31)

#### UI buttons (8)

```text
Backward
CycleLeft
CycleRight
Down
Forward
Left
Right
Up
```

#### Race buttons (19)

```text
CycleCamera
CycleCarLightStages
CycleHudMfd
CycleWiper
DecreaseBrakeBias
DecreaseTC
DisplayPageDown
DisplayPageUp
GearDown
GearUp
IgnitionOff
IgnitionSequenceOn
IncreaseBrakeBias
IncreaseTC
LookLeft
LookRight
Pause
PitLimiter
Starter
```

#### Race axes (4)

```text
Brake
Clutch
Gas
Steer
```

## Assetto Corsa EVO

### Files and types

- `C:\Users\Dillon\Saved Games\ACE\input_keyboard.keyboardinputconfiguration` — 926-byte protobuf-style binary keyboard mapping.
- `C:\Users\Dillon\Saved Games\ACE\input_devices.inputdeviceconfiguration` — 479-byte protobuf-style binary device mapping.
- `C:\Users\Dillon\Saved Games\ACE\input_settings.inputsettings` — 63-byte protobuf-style binary input settings; no plain-text action names.
- `C:\Program Files (x86)\Steam\steamapps\common\Assetto Corsa EVO\AssettoCorsaEVO.exe` — PE executable containing the current protobuf `InputAction` enum used to resolve saved numeric IDs.

The save files store numeric action IDs, not names. Some keyboard IDs are legacy values no longer named by the current executable enum; they are preserved below as IDs rather than guessed.

### IDs currently present in the keyboard mapping (43)

```text
1: name not present in current executable enum
2: name not present in current executable enum
3: name not present in current executable enum
55: name not present in current executable enum
97: name not present in current executable enum
98: name not present in current executable enum
159: InputAction_UI_CycleNameplateVisibility
167: InputAction_UI_Toggle_Virtual_Mirror
299: InputAction_Car_H_Shifter_Toggle
301: InputAction_Dev_Toggle_Debug_Ui
302: InputAction_Dev_Game_Quit
400: InputAction_Camera_Drivable
401: InputAction_Camera_OnBoardFree
402: InputAction_Camera_Free
403: InputAction_Camera_Track
404: InputAction_Camera_Helicopter
406: InputAction_Camera_Onboard
412: InputAction_Camera_PanLeft
413: InputAction_Camera_PanRight
414: InputAction_Camera_Forward
415: InputAction_Camera_Backward
418: InputAction_Camera_ResetView
505: name not present in current executable enum
506: name not present in current executable enum
507: name not present in current executable enum
508: name not present in current executable enum
510: InputAction_UI_Up
511: InputAction_UI_Down
512: InputAction_UI_Left
513: InputAction_UI_Right
514: InputAction_UI_PageUp
515: InputAction_UI_PageDown
516: InputAction_UI_Confirm
517: InputAction_UI_Cancel
518: InputAction_UI_Menu
520: InputAction_UI_ToggleHud
523: InputAction_UI_ShowPoi
531: InputAction_UI_Vr_Panel_Forward
532: InputAction_UI_Vr_Panel_Backward
533: InputAction_UI_Vr_Panel_ScaleUp
534: InputAction_UI_Vr_Panel_ScaleDown
535: InputAction_UI_Vr_Settings_Reset
552: InputAction_AIDev_LoadSnapshot
```

### IDs currently present in the device mapping (13)

```text
104: InputAction_Car_Handbrake
110: InputAction_Car_Paddle_Gear_X_2
139: InputAction_Car_Horn
400: InputAction_Camera_Drivable
510: InputAction_UI_Up
511: InputAction_UI_Down
512: InputAction_UI_Left
513: InputAction_UI_Right
516: InputAction_UI_Confirm
517: InputAction_UI_Cancel
518: InputAction_UI_Menu
524: InputAction_UI_OpenMap
525: InputAction_UI_FreeRoamCarReset
```

### Complete embedded InputAction enum (253)

#### Driving (60)

```text
100: InputAction_Car_Steer_Left
101: InputAction_Car_Steer_Right
102: InputAction_Car_Gas
103: InputAction_Car_Brake
104: InputAction_Car_Handbrake
105: InputAction_Car_Clutch
110: InputAction_Car_Paddle_Gear_X_2
111: InputAction_Car_Shifter_Gear_X_9
113: InputAction_Car_Shifter_Gear_Reverse
120: InputAction_Car_Light_Cycle_X_2
121: InputAction_Car_Flashing_Lights
122: InputAction_Car_Light_Direct_X_3
123: InputAction_Car_Display_Device_Cycle_X_2
124: InputAction_Car_Display_Device_Direct_X_5
125: InputAction_Car_Display_Page_Cycle_X_2
126: InputAction_Car_Display_Page_Direct_X_5
131: InputAction_Car_Rain_Lights
132: InputAction_Car_Direction_Light_Left
133: InputAction_Car_Direction_Light_Right
134: InputAction_Car_Warning_Lights
135: InputAction_Car_Retractable_HeadLights_Toggle
136: InputAction_Car_Ignition_Toggle
137: InputAction_Car_Starter
138: InputAction_Car_Pit_Limiter_Toggle
139: InputAction_Car_Horn
140: InputAction_Car_TractionControl_Cycle_X_2
141: InputAction_Car_TractionControl_Direct_X_15
142: InputAction_Car_TractionControl_Cut_Cycle_X_2
143: InputAction_Car_TractionControl_Cut_Direct_X_15
144: InputAction_Car_ABS_Cycle_X_2
145: InputAction_Car_ABS_Direct_X_15
146: InputAction_Car_Engine_Map_Cycle_X_2
147: InputAction_Car_Engine_Map_Direct_X_10
148: InputAction_Car_Brake_Bias_Cycle_X_2
149: InputAction_Car_ESC_Cycle_X_2
150: InputAction_Car_ESC_Direct_X_10
155: InputAction_Car_Wipers_Cycle_X_2
156: InputAction_Car_Wipers_Direct_X_5
161: InputAction_Car_Mirrors_Cycle_X_2
162: InputAction_Car_Mirrors_Pitch_X_2
163: InputAction_Car_Mirrors_Yaw_X_2
164: InputAction_Car_Mirrors_Fov_X_2
165: InputAction_Car_PerformanceMode_Cycle_X_2
166: InputAction_Car_PerformanceMode_Direct_X_10
168: InputAction_Car_FFB_Gain_X_2
169: InputAction_Car_Turbo_Level_Cycle_X_2
231: InputAction_Car_Front_Bump_Damper_Cycle_X_2
232: InputAction_Car_Front_Rebound_Damper_Cycle_X_2
233: InputAction_Car_Rear_Bump_Damper_Cycle_X_2
234: InputAction_Car_Rear_Rebound_Damper_Cycle_X_2
235: InputAction_Car_Ebb_Cycle_X_2
236: InputAction_Car_Diff_Power_Level_Cycle_X_2
237: InputAction_Car_Diff_Coast_Level_Cycle_X_2
299: InputAction_Car_H_Shifter_Toggle
913: InputAction_Car_Optional_Animation_X_5
1700: InputAction_Car_Ers_Recharge_Cycle_X_2
1701: InputAction_Car_Ers_Deployment_Cycle_X_2
1702: InputAction_Car_Ers_Heat_Charging_Toggle
1703: InputAction_Car_Ers_Overtake
1704: InputAction_Car_DRS_Toggle
```

#### Camera (56)

```text
0: InputAction_Camera_Drone_Toggle
400: InputAction_Camera_Drivable
401: InputAction_Camera_OnBoardFree
402: InputAction_Camera_Free
403: InputAction_Camera_Track
404: InputAction_Camera_Helicopter
405: InputAction_Camera_Sequence
406: InputAction_Camera_Onboard
410: InputAction_Camera_PanUp
411: InputAction_Camera_PanDown
412: InputAction_Camera_PanLeft
413: InputAction_Camera_PanRight
414: InputAction_Camera_Forward
415: InputAction_Camera_Backward
416: InputAction_Camera_YawLeft
417: InputAction_Camera_YawRight
418: InputAction_Camera_ResetView
419: InputAction_Camera_CancelResetView
420: InputAction_Camera_PitchUp
421: InputAction_Camera_PitchDown
422: InputAction_Camera_RollRight
423: InputAction_Camera_RollLeft
424: InputAction_Camera_Zoom_Toggle
425: InputAction_Camera_LookLeft
426: InputAction_Camera_LookRight
427: InputAction_Camera_LookBehind
430: InputAction_Camera_Showroom_RotateCar
431: InputAction_Camera_Showroom_InternalView
435: InputAction_Camera_FovModifier
501: InputAction_Camera_Select_Next_Car
502: InputAction_Camera_Select_Prev_Car
503: InputAction_Camera_Select_Player_Car
1410: InputAction_Camera_PanUp_Slow
1411: InputAction_Camera_PanDown_Slow
1412: InputAction_Camera_PanLeft_Slow
1413: InputAction_Camera_PanRight_Slow
1414: InputAction_Camera_Forward_Slow
1415: InputAction_Camera_Backward_Slow
1416: InputAction_Camera_YawLeft_Slow
1417: InputAction_Camera_YawRight_Slow
1420: InputAction_Camera_PitchUp_Slow
1421: InputAction_Camera_PitchDown_Slow
1422: InputAction_Camera_RollRight_Slow
1423: InputAction_Camera_RollLeft_Slow
2410: InputAction_Camera_PanUp_Fast
2411: InputAction_Camera_PanDown_Fast
2412: InputAction_Camera_PanLeft_Fast
2413: InputAction_Camera_PanRight_Fast
2414: InputAction_Camera_Forward_Fast
2415: InputAction_Camera_Backward_Fast
2416: InputAction_Camera_YawLeft_Fast
2417: InputAction_Camera_YawRight_Fast
2420: InputAction_Camera_PitchUp_Fast
2421: InputAction_Camera_PitchDown_Fast
2422: InputAction_Camera_RollRight_Fast
2423: InputAction_Camera_RollLeft_Fast
```

#### UI (22)

```text
159: InputAction_UI_CycleNameplateVisibility
167: InputAction_UI_Toggle_Virtual_Mirror
510: InputAction_UI_Up
511: InputAction_UI_Down
512: InputAction_UI_Left
513: InputAction_UI_Right
514: InputAction_UI_PageUp
515: InputAction_UI_PageDown
516: InputAction_UI_Confirm
517: InputAction_UI_Cancel
518: InputAction_UI_Menu
520: InputAction_UI_ToggleHud
521: InputAction_UI_Cycle_Mfd_Up
522: InputAction_UI_Cycle_Mfd_Down
523: InputAction_UI_ShowPoi
524: InputAction_UI_OpenMap
525: InputAction_UI_FreeRoamCarReset
531: InputAction_UI_Vr_Panel_Forward
532: InputAction_UI_Vr_Panel_Backward
533: InputAction_UI_Vr_Panel_ScaleUp
534: InputAction_UI_Vr_Panel_ScaleDown
535: InputAction_UI_Vr_Settings_Reset
```

#### Showroom (12)

```text
900: InputAction_Showroom_Hood
901: InputAction_Showroom_Tailgate
903: InputAction_Showroom_Door_FL
904: InputAction_Showroom_Door_FR
905: InputAction_Showroom_Door_RL
906: InputAction_Showroom_Door_RR
907: InputAction_Showroom_Pedal_Accelerator
908: InputAction_Showroom_Pedal_Brake
909: InputAction_Showroom_Pedal_Clutch
910: InputAction_Showroom_Gear_Shift_Up
911: InputAction_Showroom_Gear_Shift_Down
912: InputAction_Showroom_Hand_Brake
```

#### Internal/editor/developer (103)

```text
5: InputAction_Editor_Quit
6: InputAction_Editor_Undo
7: InputAction_Editor_Redo
8: InputAction_Editor_Save_Active
9: InputAction_Editor_Save_All
10: InputAction_Editor_Close_Active
11: InputAction_Editor_Close_All
12: InputAction_Editor_Gizmo_Translate
13: InputAction_Editor_Gizmo_Rotate
14: InputAction_Editor_Gizmo_Scale
15: InputAction_Editor_Copy
16: InputAction_Editor_Paste
17: InputAction_Editor_Gizmo_Mode
20: InputAction_Editor_VSyncToggle
21: InputAction_Editor_CapFPSToggle
22: InputAction_Editor_ViewPerspective
23: InputAction_Editor_ViewOrthographic
24: InputAction_Editor_Spline_Move_Backward
25: InputAction_Editor_Spline_Move_Forward
26: InputAction_Editor_Spline_Delete
27: InputAction_Editor_Spline_Insert_After
28: InputAction_Editor_Spline_Insert_Before
29: InputAction_Editor_Spline_Insert_At_Middle
30: InputAction_Editor_Spline_Append_On_Click
31: InputAction_Editor_Spline_Select_Next
32: InputAction_Editor_Spline_Select_Previous
33: InputAction_Editor_Spline_Cycle_Anchors
34: InputAction_Editor_Spline_Add_Marker
35: InputAction_Editor_Spline_Insert_Marker_After
36: InputAction_Editor_Spline_Insert_Marker_Before
37: InputAction_Editor_Spline_Toggle_Big_Nodes
38: InputAction_Editor_Spline_Toggle_Lock_Anchor_Direction
40: InputAction_Editor_Cut
41: InputAction_Editor_Delete
50: InputAction_Editor_Select_Closest_Pivot
51: InputAction_Editor_ViewPhysics
52: InputAction_Editor_Move_Selected_Here
53: InputAction_Editor_TeleportCamera
60: InputAction_Editor_Favorite_X_10
61: InputAction_Editor_Show_Symbols
70: InputAction_Editor_FastOpen
99: InputAction_Editor_Focus_On_Selected
151: InputAction_CarDev_WindshieldDirt_Inc
152: InputAction_CarDev_WindshieldDirt_Dec
153: InputAction_CarDev_WindshieldScratch_Inc
154: InputAction_CarDev_WindshieldScratch_Dec
171: InputAction_CarDev_Dirt_Inc
172: InputAction_CarDev_Dirt_Dec
173: InputAction_CarDev_Dust_Inc
174: InputAction_CarDev_Dust_Dec
175: InputAction_CarDev_Pickup_Inc
176: InputAction_CarDev_Pickup_Dec
200: InputAction_Terrain_Recreate_Renderer
201: InputAction_Terrain_Refresh_Vegetation
202: InputAction_Terrain_Cycle_Debug_Visualization
203: InputAction_Terrain_Pin_On_Terrain
204: InputAction_Terrain_Toggle_Vegetation
205: InputAction_Terrain_Build_Current_Quadrant
250: InputAction_Editor_Road_Generate_Meshes_And_Linked_Intersections
251: InputAction_Editor_Road_Generate_Meshes
252: InputAction_Editor_Road_Compute_Camber
300: InputAction_Dev_Toggle_Log_Bar
301: InputAction_Dev_Toggle_Debug_Ui
302: InputAction_Dev_Game_Quit
453: InputAction_Dev_Replay_Save
550: InputAction_AIDev_Possess_Focused_Car
551: InputAction_AIDev_SaveSnapshot
552: InputAction_AIDev_LoadSnapshot
553: InputAction_AIDev_StartRecording
554: InputAction_AIDev_SaveIdealLine
555: InputAction_AIDev_SaveReferences
556: InputAction_AIDev_Replay_Start
557: InputAction_AIDev_Replay_Stop
558: InputAction_AIDev_Replay_ResumeFromSnapshot
559: InputAction_AIDev_Replay_ToggleReverse
560: InputAction_AIDev_SaveGame
561: InputAction_AIDev_RestoreGame
600: InputAction_Editor_Renderer_Settings
601: InputAction_Editor_Renderer_Debug
602: InputAction_Editor_Renderer_Visualization
603: InputAction_Editor_Switch_Preview_Source
604: InputAction_Editor_Add_Coordinates_To_Procedural_Skip_List
605: InputAction_Editor_Renderer_Inspector
606: InputAction_Editor_Renderer_HotReloadShaders
700: InputAction_Editor_ShowIrradianceVolume
701: InputAction_Editor_ShowReflectionProbe
702: InputAction_Editor_ShowGizmoSphere
704: InputAction_Editor_RotationSpeedModifier
800: InputAction_Weather_ForwardOneHour
801: InputAction_Weather_BackOneHour
1900: InputAction_Editor_Picking_Toggle
6666: InputAction_Reload_SelectedDevUiCar
6897: InputAction_Editor_Toggle_InstancePainting
7600: InputAction_Editor_InstancePainting_BrushRadius_Plus
7601: InputAction_Editor_InstancePainting_BrushRadius_Minus
7602: InputAction_Editor_InstancePainting_BrushDensity_Plus
7603: InputAction_Editor_InstancePainting_BrushDensity_Minus
7604: InputAction_Editor_InstancePainting_MinDistance_Plus
7605: InputAction_Editor_InstancePainting_MinDistance_Minus
7606: InputAction_Editor_InstancePainting_MaxDistance_Plus
7607: InputAction_Editor_InstancePainting_MaxDistance_Minus
7608: InputAction_Editor_InstancePainting_ForceVertical
7609: InputAction_Editor_InstancePainting_SingleInstance
```

## Automobilista 2

### Files and types

- Live controller profile: `C:\Users\Dillon\Documents\Automobilista 2\savegame\1150528881\automobilista 2\profiles\default.controllersettings.v1.03.sav` — 171,848-byte binary `.sav` container.
- General profile: `C:\Users\Dillon\Documents\Automobilista 2\savegame\1150528881\automobilista 2\profiles\default.sav` — binary `.sav`.
- Local settings: `C:\Users\Dillon\Documents\Automobilista 2\savegame\1150528881\automobilista 2\profiles\default.localsettings.v1.03.sav` — binary `.sav`.
- Installed action-label source: `C:\Program Files (x86)\Steam\steamapps\common\Automobilista 2\AMS2AVX.exe` — PE executable containing the control-menu labels corresponding to the binary profile.

The controller `.sav` is a high-entropy serialized/protected container: it has no readable action names or self-describing header. The available control names below are the exact `Control ...` labels embedded in the installed executable, normalized by removing the duplicate `Secondary` suffix. This records the locally installed action catalog without claiming the `.sav` layout is decoded.

### Installed control-label union (108)

```text
Accelerate
ActiveSusp Damping Decrease
ActiveSusp Damping Increase
ActiveSusp Reaction Speed Decrease
ActiveSusp Reaction Speed Increase
Brake
Change View
Change View Set
Clutch
Cycle Cam Back
Cycle Cam Forward
Cycle HUD Mode
Cycle Lap Info
Decrease Abs Strength
Decrease Brake Bias
Decrease Force Feedback Tone
Decrease Force Feedback Volume
Decrease Front Anti Roll Bars
Decrease Fuel Mapping
Decrease Rear Anti Roll Bars
Decrease Turbo Boost
Decrease Weight Jacker
Driver List
Driving Aids
DRS
ERS Mode Decrease
ERS Mode Increase
ERS Mode Overtake
Gear 1
Gear 2
Gear 3
Gear 4
Gear 5
Gear 6
Gear 7
Gear 8
Gear 9
Gear R
Handbrake
HeadLights
High Beam
HUD Mode
ICM
ICM Cycle
ICM Down
ICM Left
ICM Right
ICM Up
Increase Abs Strength
Increase Brake Bias
Increase Force Feedback Tone
Increase Force Feedback Volume
Increase FOV
Increase Front Anti Roll Bars
Increase Fuel Mapping
Increase Rear Anti Roll Bars
Increase Turbo Boost
Increase Weight Jacker
Launch Control
Look Back
Look Down
Look Left
Look Right
Look Up
Next Radio Station
Nitrous
Onboard Auto Shift Mode Decrease
Onboard Auto Shift Mode Increase
Onboard Diff Coast Decrease
Onboard Diff Coast Increase
Onboard Diff Power Decrease
Onboard Diff Power Increase
Onboard Diff Preload Decrease
Onboard Diff Preload Increase
Onboard Traction Control Decrease
Onboard Traction Control Increase
Opponent Names Toggle
Pause Game
Realtime Chat
Reduce FOV
Request Pit Stop
Reset Car
Reset Seat Position
Reset VR
Seat Aft
Seat Angle Down
Seat Angle Up
Seat Down
Seat Fore
Seat Up
Shift Down
Shift Up
Start Your Engine
Steer Left
Steer Right
Toggle ABS
Toggle Auto Brake
Toggle Auto Clutch
Toggle Auto Gears
Toggle Auto Steer
Toggle HUD Dials
Toggle Ignition
Toggle Pit Speed Limiter
Toggle Stability Control
Toggle Traction Control
Traction Control Off
Traction Control On
Wipers
```

## Le Mans Ultimate

### Files and types

- Current settings: `C:\Program Files (x86)\Steam\steamapps\common\Le Mans Ultimate\UserData\player\current controls.json` — JSON input options/settings; it contains no `Input` action map.
- Controller presets: `C:\Program Files (x86)\Steam\steamapps\common\Le Mans Ultimate\UserData\Controller\Presets\*.json` — 71 JSON preset files. Each file has an `Input` object whose keys are action names.
- Important shipped presets include `keyboard.json` and `gamepad.json`; wheel/pedal presets use the same structure.

### Complete union of preset Input keys (110)

```text
Adjust Seat Aft
Adjust Seat Down
Adjust Seat Fore
Adjust Seat Up
Alternate Esc
Antilock Brake System Down
Antilock Brake System Up
Bias Forward
Bias Rearward
Brake
Brake Migration Forward
Brake Migration Rearward
Camera Zoom In
Camera Zoom Out
Clutch In
CPU Time
Dec Front ARB
Dec Rear ARB
Decrease Vertical FOV
Decrement Mixture
Decrement Motor Map
Decrement Regeneration
Display Mode
Display Vehicle Labels
Driver Overlay Cycle Track Map
Driver Overlay Next MFD
Driver Overlay Previous MFD
Driver Overlay Toggle HUD
Driving Cameras
Fifth Gear
First Gear
Fourth Gear
Framerate
Front Flap
Headlights
Headlights Pulse
Horn
Ignition
Inc Front ARB
Inc Rear ARB
Increase Vertical FOV
Increment Mixture
Increment Motor Map
Increment Regeneration
Instant Replay
Launch Control
Look Left
Look Right
Lower Track Bar
Neutral
Onboard Cameras
Pit Menu Dec
Pit Menu Down
Pit Menu Inc
Pit Menu Up
Pit Request
Push To change camera view
Quick Chat #1
Quick Chat #12
Quick Chat #2
Quick Chat #3
Quick Chat #4
Quick Chat #5
Quick Chat #6
Quick Chat #7
Quick Chat #8
Quick Chat #9
Raise Track Bar
Realtime Chat
Rear Flap
Rear Look
Reset Force Feedback
Restart Race
Reverse Gear
Screenshot
Second Gear
Shift Down
Shift Up
Sixth Gear
Skip Formation
Spectator Cameras
Speed Limiter
Starter
Steer Left
Steer Right
Swingman Camera
Swingman Down
Swingman Left
Swingman Reset
Swingman Right
Swingman Up
Swingman Zoom In
Swingman Zoom Out
TCOverride
Third Gear
Throttle
Toggle AI Control
Toggle Cursor
Toggle Mirror
Tracking Cameras
Traction Control 2 Down
Traction Control 2 Up
Traction Control Down
Traction Control Slip Angle Down
Traction Control Slip Angle Up
Traction Control Up
Triples
Vehicle Status
View Original Vehicle
Wipers
```

## Refresh notes

- Re-scan ACC when devices or bindings change; `controls.json` contains only the action codes currently written for detected devices.
- AMS2's action labels are recoverable, but its binary `.sav` profile still needs a verified decoder before individual assignments can be inspected safely.
- Re-scan after major game updates because action tables and profile schemas can change.
- This file records names and formats only; it does not select mappings or imply write support.
