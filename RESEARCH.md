# Format research and evidence log

**Reviewed:** 2026-09-25. This file separates published evidence from hypotheses. Paths and schemas should be rechecked against the installed game version before any adapter writes.

| Game | Evidence available | What still needs proof | Current write gate |
| --- | --- | --- | --- |
| iRacing | A local 2026.09.10.02 install resolves `Baseline` through `app.ini`, also exposes a `Test` profile, and its GFCC 20/LRTC 8 files pass byte-exact round trips. The three native action records are present. | Select the SimHub DirectInput instance/product GUID, apply only to `Test`, then verify reload and on-track behavior. | Closed pending device and in-game test |
| Assetto Corsa | Content Manager source manages INI controls and saved presets. | Which live/preset files the game actually loads, action key mapping, formatting preservation. | Closed |
| Assetto Corsa Competizione | Control JSON files have been observed, but no official schema is established in this research. | Path and profile selection, action IDs, device metadata, unknown field preservation, in-game effect. | Closed |
| Assetto Corsa EVO | Publisher confirms the move from Documents to `Saved Games/ACE`. | Exact current binding file(s), serialization and versioning, safe read/write, in-game effect. | Closed |
| Le Mans Ultimate | Studio 397 documents `current controls.json` and a shift toward GameInput with DirectInput fallback. | Action entries, input mode and device identifiers, files actually updated by the game. | Closed |
| Automobilista 2 | Reiza community identifies `.sav` controller settings and notes six built-in profiles since v1.2.2.0. | Current profile filenames, binary structure, safe per-binding edits, in-game effect. | Closed |

"Closed" means no file writes enabled yet; it does not mean the project is blocked. Discovery and backups can precede full adapters.

## Controlled sample procedure

For **each** game and build:

1. Shut down the game and copy the entire relevant control/profile directory to a private test folder.
2. Start the game; save an untouched baseline, then exit fully.
3. Change **one** button binding in-game, save, exit, and capture a second copy.
4. Repeat with the same action on a different button, then a different action on the original button.
5. Capture device plug/unplug and a second profile separately if the game supports profiles.
6. Compare paths, hashes, decoded fields, binary offsets, timestamps, and game logs.
7. Redact personal data, check the game's terms, then add only minimal synthetic or sanitized fixtures to the repo.
8. Round trip a fixture unchanged. Patch a copy, reload it in the game, verify the actual action, and test restore.

For opaque files, compare multiple controlled saves before attributing byte changes to bindings. Compression, checksums, generated IDs, and incidental settings can make a simple binary diff misleading.

## Research questions

- Does SimHub expose a supported way to read or change role assignments outside its UI? If not, use manual entry and verification first.
- Does a game use 0-based or 1-based button numbers in its file, UI, and Windows input APIs?
- What happens if the virtual controller is absent, changes GUID, or switches from vJoy to an Arduino bridge?
- What is the active profile when multiple presets, cars, input modes, or Windows accounts exist?
- Does the game overwrite external edits at startup, shutdown, via launcher, or via cloud sync?
- Are paired increase/decrease commands separate bindings, hold actions, or menu macros?

## Primary sources and useful code

- [SimHub Control Mapper documentation](https://github.com/SHWotever/SimHub/wiki/Control-Mapper-plugin): stable role/button assignments, output choices, and FFB limitation.
- [iRacing May 2026 development update](https://www.iracing.com/iracing-development-update-may-2026/): native Control Profiles feature.
- [iRacing Controls Editor](https://github.com/jackhumbert/iracing-controls-editor-app): independently developed `controls.cfg` editing example; verify current profile locations separately.
- [Assetto Corsa Content Manager controls code](https://github.com/gro-ove/actools/blob/master/AcManager.Tools/Helpers/AcSettings/ControlsSettings.cs): existing INI/preset implementation.
- [Le Mans Ultimate input hotfix](https://guide.lemansultimate.com/hc/en-gb/articles/13755123150991-V1-0-2-2-Patch-2-Hotfix-2): GameInput and DirectInput behavior.
- [505 Games AC EVO 0.5.2 patch notes](https://support.505games.com/support/solutions/articles/150000221632-assetto-corsa-evo-0-5-2-patch-notes): `Saved Games/ACE` migration.
- [Reiza Studios forum: controller profiles](https://forum.reizastudios.com/threads/custom-files-for-controllers-profile-exists.9794/): historical `.sav` path, with a later edit stating six profiles are supported. Community evidence; confirm on a current build.

## Sample record template

```text
Game/build:
Windows/SimHub version:
Input device (redacted stable identifier):
Input backend (if known):
Selected in-game profile:
Action and before/after input:
Changed file paths and hashes:
Observed action in-game after restart:
Unknown byte/field changes:
Restore result:
Researcher/date:
```
