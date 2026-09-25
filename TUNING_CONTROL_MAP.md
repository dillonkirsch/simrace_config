# Advanced tuning and race-operation control map

Batch 4 adds 50 normalized controls. Native names come from the installed-file
inventory in [CONTROL_INVENTORY.md](CONTROL_INVENTORY.md).

Legend: `—` = not exposed in a complete inspected vocabulary; `?` = not
observed in ACC's binding-dependent file; `*` = packed/compound action; `†` =
related but not semantically identical.

## Advanced brake and traction-control settings

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Move brake bias slightly forward | `BrakeBiasFineInc` | — | ? | — | — | — |
| Move brake bias slightly rearward | `BrakeBiasFineDec` | — | ? | — | — | — |
| Increase peak brake bias | `PeakBrakeBiasInc` | — | ? | — | — | — |
| Decrease peak brake bias | `PeakBrakeBiasDec` | — | ? | — | — | — |
| Move brake migration forward | — | — | ? | — | — | `Brake Migration Forward` |
| Move brake migration rearward | — | — | ? | — | — | `Brake Migration Rearward` |
| Increase traction control 2 | `TractionControl2Inc` | — | ? | — | — | `Traction Control 2 Up` |
| Decrease traction control 2 | `TractionControl2Dec` | — | ? | — | — | `Traction Control 2 Down` |
| Increase TC slip-angle target | — | — | ? | — | — | `Traction Control Slip Angle Up` |
| Decrease TC slip-angle target | — | — | ? | — | — | `Traction Control Slip Angle Down` |
| Increase traction-control cut | — | — | ? | `142: InputAction_Car_TractionControl_Cut_Cycle_X_2` * | — | — |
| Decrease traction-control cut | — | — | ? | `142: InputAction_Car_TractionControl_Cut_Cycle_X_2` * | — | — |
| Traction-control override | `TractionControlArm` † | — | ? | — | — | `TCOverride` |

## Differential and aero

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Increase differential preload | `DiffPreloadInc` | — | ? | — | `Onboard Diff Preload Increase` | — |
| Decrease differential preload | `DiffPreloadDec` | — | ? | — | `Onboard Diff Preload Decrease` | — |
| Increase differential entry | `DiffEntryInc` | — | ? | — | — | — |
| Decrease differential entry | `DiffEntryDec` | — | ? | — | — | — |
| Increase differential mid-corner | `DiffMiddleInc` | — | ? | — | — | — |
| Decrease differential mid-corner | `DiffMiddleDec` | — | ? | — | — | — |
| Increase differential exit | `DiffExitInc` | — | ? | — | — | — |
| Decrease differential exit | `DiffExitDec` | — | ? | — | — | — |
| Increase differential power | — | — | ? | `236: InputAction_Car_Diff_Power_Level_Cycle_X_2` * | `Onboard Diff Power Increase` | — |
| Decrease differential power | — | — | ? | `236: InputAction_Car_Diff_Power_Level_Cycle_X_2` * | `Onboard Diff Power Decrease` | — |
| Increase differential coast | — | — | ? | `237: InputAction_Car_Diff_Coast_Level_Cycle_X_2` * | `Onboard Diff Coast Increase` | — |
| Decrease differential coast | — | — | ? | `237: InputAction_Car_Diff_Coast_Level_Cycle_X_2` * | `Onboard Diff Coast Decrease` | — |
| Increase front wing/flap | `WingFrontInc` | — | ? | — | — | `Front Flap` † |
| Decrease front wing/flap | `WingFrontDec` | — | ? | — | — | `Front Flap` † |
| Increase rear wing/flap | `WingRearInc` | — | ? | — | — | `Rear Flap` † |
| Decrease rear wing/flap | `WingRearDec` | — | ? | — | — | `Rear Flap` † |

## Engine and chassis adjustments

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Increase power steering | `PowerSteeringInc` | — | ? | — | — | — |
| Decrease power steering | `PowerSteeringDec` | — | ? | — | — | — |
| Increase throttle shaping | `ThrottleShapeInc` | — | ? | — | — | — |
| Decrease throttle shaping | `ThrottleShapeDec` | — | ? | — | — | — |
| Increase engine power | `EnginePowerInc` | — | ? | `165: InputAction_Car_PerformanceMode_Cycle_X_2` † | — | — |
| Decrease engine power | `EnginePowerDec` | — | ? | `165: InputAction_Car_PerformanceMode_Cycle_X_2` † | — | — |
| Increase fuel-cut position | `FuelCutPositionInc` | — | ? | — | — | — |
| Decrease fuel-cut position | `FuelCutPositionDec` | — | ? | — | — | — |
| Increase launch RPM | `LaunchRPMInc` | — | ? | — | — | — |
| Decrease launch RPM | `LaunchRPMDec` | — | ? | — | — | — |
| Raise track bar | — | — | ? | — | — | `Raise Track Bar` |
| Lower track bar | — | — | ? | — | — | `Lower Track Bar` |

## Race-operation actions

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Single windshield wipe | `TriggerWindshieldWipers` | — | `CycleWiper` † | `155: InputAction_Car_Wipers_Cycle_X_2` † | `Wipers` † | `Wipers` † |
| Acknowledge low-fuel warning | `LowFuelAccept` | — | ? | — | — | — |
| Toggle in-lap mode | `InLapToggle` | — | ? | — | — | — |
| Toggle full-course yellow mode | `FCYToggle` | — | ? | — | — | — |
| Toggle fuel-to-end display | `FuelToEndToggle` | — | ? | — | — | — |
| Increase fuel-to-end margin | `FuelToEndMarginInc` | — | ? | — | — | — |
| Decrease fuel-to-end margin | `FuelToEndMarginDec` | — | ? | — | — | — |
| Skip formation sequence | — | — | ? | — | — | `Skip Formation` |
| Toggle AI control | — | — | ? | — | — | `Toggle AI Control` |

The structured crosswalk in `sim_controls_manager.control_names` contains the
full notes explaining each compound or related mapping.

