# Positional and extended user-control map

Batch 7 adds 108 normalized controls and covers 120 previously unmatched
native entries. It expands beyond ordinary increment/decrement buttons into
direct positional selectors, simulator utilities, VR panels, and camera modes.

The structured source of truth is `sim_controls_manager.control_names`; this
document summarizes the repetitive families rather than reproducing 108 nearly
identical rows.

## Direct positional selectors

| Family | iRacing native form | AC EVO native form |
| --- | --- | --- |
| ABS | `ABSLevel` | `145: InputAction_Car_ABS_Direct_X_15` |
| Traction control | `TractionControlLevel` and `TractionControl2Level`–`4Level` | `141: InputAction_Car_TractionControl_Direct_X_15` |
| TC cut | — | `143: InputAction_Car_TractionControl_Cut_Direct_X_15` |
| Brake bias/settings | `BrakeBiasLevel`, `BrakeBiasFineLevel`, `PeakBrakeBiasLevel`, `BrakeMiscLevel` | EBB uses packed `235: ...Ebb_Cycle_X_2` |
| Anti-roll bars | `AntiRollFrontLevel`, `AntiRollRearLevel` | — |
| Turbo/engine/fuel | `BoostLevelLevel`, `EngineBrakingLevel`, `EnginePowerLevel`, `FuelMixtureLevel`, `FuelCutPositionLevel` | Direct engine map and performance-mode selectors |
| Differential | `DiffPreloadLevel`, `DiffEntryLevel`, `DiffMiddleLevel`, `DiffExitLevel` | — |
| Hybrid | MGU-K regeneration, deployment mode, and fixed-deployment level records | — |
| Shocks/weight jacker | Four shock level records and left/right weight-jacker levels | — |
| Wings and throttle | Front/rear wing levels and `ThrottleShapeLevel` | — |
| Dashboard/display | `DashPageLevel`, `DashPage2Level` | Direct display-device and page selectors |
| Lights and wipers | — | Direct 3-stage headlights and 5-stage wipers |
| Stability control | — | `150: InputAction_Car_ESC_Direct_X_10` |

## iRacing-specific utilities

- Direct black-box selections F1–F12, size, and visibility
- Custom-sector start/end, active-reset save/run, and splits-delta cycling
- Qualifying-tape adjustment and direct position
- Driver horizon, tilt recentering, driver marker, radar, and reference car
- Layout editing, interface/system meters, video capture/timer, telemetry
  logging, latency reporting, texture reload, and giant screenshot capture
- Spotter leader-line report and previous driving camera

## AC EVO and VR additions

- VR panel forward/backward and scale up/down
- Drivable, onboard, tracking, and helicopter/spectator camera identifiers
- Packed electronic brake-balance adjustment

## Camera and display additions

- Camera zoom in/out, including iRacing's inverse FOV relationship
- Previous camera and camera-view set in Automobilista 2
- CPU-time and framerate displays in Le Mans Ultimate
- Driving, onboard, spectator, swingman, tracking, and original-vehicle views
- Instant replay and all seven LMU swingman movement/reset/zoom actions

After this batch, every inventoried Assetto Corsa, ACC, AMS2, and LMU action is
either mapped or classified as non-action metadata. Remaining user-facing
native entries exist only in iRacing and AC EVO's deeper camera/replay sets.

