# To-do and milestones

Status key: `[ ]` pending, `[x]` complete. Mark work done only after verification on a game-created fixture and, where specified, in-game testing.

## Milestone 0 — establish facts

- [ ] Create a repository, choose a license, and add issue templates after the initial scope is agreed.
- [ ] Record installed game versions, Windows version, selected virtual output, and SimHub version for each test rig.
- [ ] Collect sanitized before/after control files for one changed button per target game; document exact reproduction steps.
- [ ] Check whether iRacing's active Control Profile changes which file must be edited.
- [ ] Check AMS2's six-profile behavior and identify actual files for each selected profile.
- [ ] Write a compatibility matrix of actions based on game menus and generated config, not name guesses.
- [ ] Decide the first adapter after validating file discovery and a lossless round trip.

## Milestone 1 — safe single-game proof of concept

- [x] Implement game/profile discovery and read-only binding inspection.
- [x] Model three actions: `pit_limiter`, `tc_increase`, `tc_decrease` (only where supported).
- [x] Accept a manually configured, stable SimHub virtual-button assignment.
- [x] Preview an exact diff; reject ambiguous profiles, unknown formats, and duplicate assignments.
- [x] Implement backup, guarded write, post-write validation, and restore.
- [ ] Prove that the game reads each changed binding and that a second apply makes no changes.

## Milestone 2 — more game adapters

- [ ] Add a second adapter with its own fixtures and in-game verification.
- [ ] Investigate iRacing profile variants, Assetto Corsa saved presets, ACC custom presets, and LMU's GameInput/DirectInput paths.
- [ ] Keep AC EVO and AMS2 read-only until format/version/device evidence supports writes.
- [ ] Verify real device names and button index conventions (0-based versus 1-based) for each game.

## Milestone 3 — usable Windows app

- [x] Add action-oriented mapping screen, game/profile selection, and per-game status.
- [ ] Add an input-listening wizard; distinguish physical input from SimHub virtual output.
- [ ] Add export/import and a full local backup browser. (Receipt selection and restore preview are implemented.)
- [ ] Test unplug/replug, game update, profile switch, interrupted write, and cloud-synced folders.
- [ ] Package and document install, recovery, and supported game versions.

## Definition of done for each adapter

- [ ] Knows active profile path and game/version it was tested against.
- [ ] Parses and round trips representative game-created samples while preserving unknown data.
- [ ] Handles unsupported actions and duplicate device/button conflicts explicitly.
- [ ] Backs up and restores all files it changes.
- [ ] Passes a real in-game binding test after the game is restarted.
