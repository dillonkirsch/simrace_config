# Basic driving-control name map

This is the central, human-readable vocabulary for basic vehicle operation.
The native names come from the locally installed files and executable action
tables inventoried on 2026-09-24 in [CONTROL_INVENTORY.md](CONTROL_INVENTORY.md).
They are names only: inclusion here does not imply that an adapter can safely
write the corresponding binding yet.

## Core controls

| Central name | iRacing | Assetto Corsa | ACC | AC EVO | Automobilista 2 | Le Mans Ultimate |
| --- | --- | --- | --- | --- | --- | --- |
| Steering | `SteerLeft` + `SteerRight` | `[STEER]` | `Steer` | `100: InputAction_Car_Steer_Left` + `101: InputAction_Car_Steer_Right` | `Steer Left` + `Steer Right` | `Steer Left` + `Steer Right` |
| Accelerator (throttle) | `Throttle` / `Throttle2` | `[THROTTLE]` | `Gas` | `102: InputAction_Car_Gas` | `Accelerate` | `Throttle` |
| Brake pedal | `Brake` / `Brake2` | `[BRAKES]` | `Brake` | `103: InputAction_Car_Brake` | `Brake` | `Brake` |
| Clutch pedal | `Clutch` / `Clutch2` | `[CLUTCH]` | `Clutch` | `105: InputAction_Car_Clutch` | `Clutch` | `Clutch In` |
| Shift up | `ShiftUp` / `ShiftUp2` | `[GEARUP]` | `GearUp` | `110: InputAction_Car_Paddle_Gear_X_2` * | `Shift Up` | `Shift Up` |
| Shift down | `ShiftDown` / `ShiftDown2` | `[GEARDN]` | `GearDown` | `110: InputAction_Car_Paddle_Gear_X_2` * | `Shift Down` | `Shift Down` |
| Reverse gear | `GearReverse` | `[SHIFTER] GEAR_R` | Not observed | `113: InputAction_Car_Shifter_Gear_Reverse` | `Gear R` | `Reverse Gear` |
| Neutral gear | `GearNeutral` | Not exposed | Not observed | Not observed | Not observed | `Neutral` |
| Handbrake | `Handbrake` | `[HANDBRAKE]` | Not observed | `104: InputAction_Car_Handbrake` | `Handbrake` | Not exposed |
| Ignition | `Ignition` | Not exposed | `IgnitionOff` + `IgnitionSequenceOn` * | `136: InputAction_Car_Ignition_Toggle` | `Toggle Ignition` | `Ignition` |
| Engine starter | `Starter` | `[STARTER]` | `Starter` | `137: InputAction_Car_Starter` | `Start Your Engine` | `Starter` |
| Pit speed limiter | `PitSpeedLimiter` | Not exposed | `PitLimiter` | `138: InputAction_Car_Pit_Limiter_Toggle` | `Toggle Pit Speed Limiter` | `Speed Limiter` |

`*` A packed or compound native action. Its presence proves the vocabulary,
but its direction/sub-action encoding must be decoded before an adapter writes
it. ACC's ignition commands also do not form a simple toggle equivalent.

## Direct forward gears

| Simulator | Native names represented by central `Gear 1` through `Gear 9` |
| --- | --- |
| iRacing | `Gear1` through `Gear9` (the installed table continues through `Gear16`) |
| Assetto Corsa | `[SHIFTER] GEAR_1` through `GEAR_7`; gears 8–9 are not exposed |
| ACC | No direct-gear action was observed in the inspected `controls.json` |
| AC EVO | `111: InputAction_Car_Shifter_Gear_X_9` is a packed nine-way action; sub-action indices are not decoded |
| Automobilista 2 | `Gear 1` through `Gear 9` |
| Le Mans Ultimate | `First Gear` through `Sixth Gear`; gears 7–9 are not exposed |

## Meaning of absence

- **Not exposed**: the complete installed action vocabulary or relevant config
  section was inspected and did not contain a distinct control.
- **Not observed**: the inspected data was incomplete or binding-dependent, so
  the missing name is not evidence that the simulator cannot support it.
- Multiple names in one cell can mean paired directions, primary/secondary
  slots, or separate commands. See the structured notes in
  `sim_controls_manager.control_names` before using them in an adapter.
