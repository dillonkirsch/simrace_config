# Sim Controls Manager UI

## Direction

The interface should feel like a focused motorsport utility: dark, precise, and
calm. It must communicate that every write is previewed and recoverable without
making the product feel like a developer tool.

## Principles

- Lead with system readiness: iRacing, SimHub, and the virtual device are visible
  before an apply action is offered.
- Preserve the safe sequence: scan, select, preview, apply, recover.
- Use color semantically. Teal means ready or verified, amber means attention,
  red means destructive or blocked, and blue is the primary action.
- Keep file paths and format details available as supporting information, not as
  the main interaction.
- Never apply from stale state. Any profile or device selection invalidates the
  existing preview.

## Tokens

| Token | Value | Use |
| --- | --- | --- |
| Canvas | `#0B0F14` | App background |
| Sidebar | `#0E141C` | Navigation |
| Surface | `#121A24` | Cards and panels |
| Raised | `#192432` | Inputs and secondary buttons |
| Border | `#263446` | Dividers and focus boundaries |
| Text | `#F4F7FA` | Primary text |
| Muted | `#8FA1B5` | Supporting text |
| Accent | `#55D6BE` | Verified and ready state |
| Primary | `#4F8CFF` | Primary action |
| Warning | `#F2B84B` | Active-profile caution |
| Danger | `#F06A6A` | Restore and error state |

Typography uses Segoe UI on Windows. Page titles are 24 px, card titles are
12–14 px, and supporting copy is 9–10 px. Spacing follows an 8 px base grid.

## Interaction rules

- Scanning and file operations run off the UI thread.
- Apply remains disabled until a successful preview exists.
- Changing a profile, device, or source path invalidates the preview.
- Writing an active profile requires a separate acknowledgement.
- Apply and restore always use the core backup, hash verification, process guard,
  format validation, and rollback behavior.
