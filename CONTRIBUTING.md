# Contributing research and code

The best early contributions are **reproducible game-created control samples** and verification of which profile the game actually loads.

## Before opening a change

1. Read [goals](docs/GOALS.md), [architecture](docs/ARCHITECTURE.md), and [research procedure](docs/RESEARCH.md).
2. Record the game build, selected profile, device output (vJoy/Arduino/other), and exact in-game change.
3. Keep raw personal configuration files private. Redact paths, account IDs, controller serials, GUIDs that identify your device, and unrelated settings before adding fixtures.
4. State clearly whether the change was verified by parsing alone or also by reloading it in the game.

## Adapter acceptance checklist

- A game-created fixture before and after one binding change, with provenance.
- Round-trip coverage showing no unrelated fields lost.
- A preview that identifies exact changed settings and files.
- A backup and tested restore path.
- Explicit handling of unknown versions, unsupported actions, and ambiguous profiles.
- An in-game check showing the game responds to the new binding after restart.

Keep copyright and licensing of third-party codecs in mind. Link to an external implementation when documenting it; copying code requires a separate license review. A repository license is still to be selected.
