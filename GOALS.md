# Goals and scope

## Product goal

Set a button action once, see how each supported simulator will interpret it, and apply the verified bindings safely. A single physical-control change in SimHub should not require rebinding every game if the virtual controller's button assignments remain stable.

## Initial audience

Windows sim racers who use multiple games and already use, or are willing to configure, SimHub Control Mapper with a stable virtual output.

## Success criteria for the first usable release

- Detect a chosen virtual controller and display its identity and button range.
- Maintain a local, exportable catalog of action IDs and virtual button assignments.
- Support at least two **validated** game adapters for common button actions; do not count discovery-only adapters as full support.
- Show a per-game diff before writing, including unsupported actions, conflicts, and affected profile paths.
- Preserve unrelated settings, reject unknown formats, make a backup before each write, and offer restore.
- Verify on a real Windows installation that the game loads the edited binding after restart.
- Reapplying the same mapping produces no further changes.

## In scope initially

- Button and encoder-as-button actions, including pit limiter, traction control increase/decrease, and brake bias increase/decrease **where a game's tested action vocabulary supports them**.
- Per-game and per-profile discovery, import, dry run, apply, backup, and restore.
- Explicit user selection when multiple game profiles or devices could match.
- Read-only or manually entered SimHub role/button mapping until an integration is validated.

## Deferred

- Creating or editing SimHub Control Mapper roles automatically.
- Keyboard macros and multi-step menu navigation.
- Live edits while a sim is running.
- Axes, calibration, wheel force feedback, car-specific setup values, and cloud sync.
- Promising production-ready write support for AC EVO or any write support for AMS2 before their formats and reload behavior are verified.

## Design principles

1. **Truthful coverage:** distinguish supported, unsupported, unknown, and game-version-incompatible actions.
2. **User control:** show which files and profiles will change and permit per-game opt out.
3. **No silent loss:** preserve unknown fields, take a backup, validate the output, and make restore simple.
4. **Stable identity:** never assume virtual button numbers, device IDs, or installed paths are universal.
5. **Evidence before support:** a parser round trip is necessary but insufficient; validate binding behavior in the game.

## Open product decisions

- Windows desktop stack and packaging format.
- Whether the first shipped adapter should be Assetto Corsa or iRacing, based on available fixtures and in-game verification.
- Whether SimHub remains a required dependency or becomes an optional input provider later.
- How to represent two logically similar actions that have different semantics across games.
