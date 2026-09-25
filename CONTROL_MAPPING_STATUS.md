# Control mapping status

This file tracks which simulator control concepts have been normalized and
which discovered concepts still need semantic cross-game mapping. Update it
with every mapping batch.

## Completed

| Batch | Scope | Controls | Crosswalk cells | Reference |
| --- | --- | ---: | ---: | --- |
| 1 | Basic driving, pedals, shifting, ignition | 21 | 126 | [BASIC_CONTROL_MAP.md](BASIC_CONTROL_MAP.md) |
| 2 | Common race and wheel/button-box actions | 20 | 120 | [COMMON_CONTROL_MAP.md](COMMON_CONTROL_MAP.md) |
| 3 | Car setup, displays, pit interaction, and cockpit actions | 50 | 300 | [ADVANCED_CONTROL_MAP.md](ADVANCED_CONTROL_MAP.md) |
| 4 | Advanced tuning and race operations | 50 | 300 | [TUNING_CONTROL_MAP.md](TUNING_CONTROL_MAP.md) |
| 5 | Suspension, hybrid systems, cockpit information, and communication | 50 | 300 | [SYSTEM_CONTROL_MAP.md](SYSTEM_CONTROL_MAP.md) |
| 6 | Remaining core and utility button actions | 90 | 540 | [CORE_UTILITY_CONTROL_MAP.md](CORE_UTILITY_CONTROL_MAP.md) |
| 7 | Positional selectors and extended user controls | 108 | 648 | [EXTENDED_CONTROL_MAP.md](EXTENDED_CONTROL_MAP.md) |
| 8 | Camera movement and selection | 47 | 282 | [CAMERA_CONTROL_MAP.md](CAMERA_CONTROL_MAP.md) |
| 9 | Advanced camera editor and replay | 77 | 462 | [MEDIA_CONTROL_MAP.md](MEDIA_CONTROL_MAP.md) |
| **Total** |  | **513** | **3,078** | `sim_controls_manager.control_names` |

A completed crosswalk cell can still be `not_exposed`, `not_observed`,
`compound`, or `related`. “Completed” means the concept was evaluated for all
six games and the evidence status was recorded; it does not mean every game
supports the action or that adapters can write it.

## Core/useful scope status

**Complete.** Every user-facing button action selected for the core/useful
scope has a stable central ID and an evidence status for all six games.

## Excluded non-user-facing scope

The user-facing inventory is complete. The following remain deliberately
outside the normalized control vocabulary:

- Developer/editor, terrain, AI-development, and internal debug actions.
- Showroom-only doors, hood, tailgate, and presentation controls.
- Non-action configuration metadata.

## Complete-coverage audit

The reproducible audit in `tools/audit_control_coverage.py` compares every
native name in the 2026-09-24 installed inventory with every native name already
referenced by the crosswalk.

| Game | User-facing native entries still uncovered | Separately excluded |
| --- | ---: | --- |
| iRacing | 0 | — |
| Assetto Corsa | 0 | 9 non-action configuration sections |
| Assetto Corsa Competizione | 0 | — |
| Assetto Corsa EVO | 0 | 103 developer/internal and 12 showroom-only entries |
| Automobilista 2 | 0 | — |
| Le Mans Ultimate | 0 | — |
| **Total** | **0** | **124** |

Therefore, complete user-facing coverage requires evaluating **0 more per-game
native entries**. The raw unmatched count is 124: 103 AC EVO
developer/internal actions, 12 AC EVO showroom-only presentation actions, and
9 Assetto Corsa non-action metadata sections. None belong in a user control
crosswalk.
