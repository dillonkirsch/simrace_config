# Sim Controls Manager — desktop design system

The interface is a native Windows workspace for managing simulator controls.
It uses graphite surfaces, a restrained blue accent, readable compact controls,
and layouts built around each tool. The window keeps its standard Windows
caption, drag region, system menu, and minimize/maximize/close behavior. DWM
dark-caption support is requested where the operating system supports it.

## Foundation

Shared tokens live in `ui_theme.py`. Workspace composition lives in
`ui_workspaces.py`; simulator operations remain in `gui.py` and the existing
adapters. `ui_dialogs.py` supplies modal confirmations, messages, and text prompts.
No third-party runtime dependency is required.

| Surface | Color | Purpose |
| --- | --- | --- |
| Canvas | `#191B20` | Deck working canvas |
| Shell | `#202229` | Navigation, command strip, status bar |
| Workspace | `#262930` | Page background |
| Supporting surface | `#292D35` | Toolbars and secondary groups |
| Section | `#2E323B` | Main sections and inspectors |
| Raised control | `#393E49` | Inputs and secondary buttons |
| Primary action | `#4779DC` | Main action buttons |
| Accent text | `#86AEFF` | Selection and pending changes |
| Success / warning / error | `#75D6AD` / `#EAC17D` / `#F38F99` | Semantic status |

Typography uses Segoe UI and Segoe UI Variable Display, with Cascadia Mono for
machine values. Sizes are specified in pixels: 25 for page titles, 15 for section
headings, 13 for body text, 12 for controls and secondary text, and 11 for metadata.
The spacing scale is 4, 8, 12, 16, 24, and 32 pixels. Sections use quiet single
keylines. Tiles use a small 5-pixel corner radius; ordinary Tk controls preserve
their native rectangular geometry. Elevation comes from surface contrast.

## Components and behavior

- Buttons have primary, secondary, ghost, and destructive variants with hover,
  pressed, focus, and disabled states. Re-enabling restores text and surface.
- Inputs, dropdown lists, checkboxes, menus, tooltips, inspector tabs, and modal
  dialogs share the palette and typography. Checkboxes use explicit marks.
- Navigation has a selection edge, matching icons, hover feedback, keyboard focus,
  and Ctrl+1 through Ctrl+5 shortcuts.
- Dialogs wrap long text, support scrolling and copying, return focus to the
  invoking control, and cancel on Escape. Destructive confirmations focus Cancel.
- Control Map fixes the header and identity column while native-name columns
  scroll. Selection, hover, filter counts, column visibility, and explicit empty
  states remain available. Ctrl+F focuses search.
- Smaller windows scroll the relevant content while keeping apply/restore
  actions visible. The minimum window size remains 1080×680.

## Page composition

- **Overview:** readiness strip, six-simulator library, input connections,
  pending binding review, deck summary, recovery summary, and session activity.
  Source locations expand in place. Every status comes from application state.
- **Deck Studio:** large canvas, compact toolbar, tile inspector with Appearance
  and Shortcut tabs, visible save state, and keyboard tile selection. Ctrl+S saves.
- **Control Map:** full-width reference grid with a frozen action column, search,
  filters, column menu, mapping notes, and a resettable no-results state.
- **Bindings:** full-width selectors, explicit action → current → target rows,
  native action names, per-action change status, contextual review panel,
  cross-game actions, and a persistent apply bar.
- **Recovery:** dated, filterable receipt history and a scrollable inspector.
  Verification runs off the UI thread. Malformed receipts and damaged, missing,
  changed, or already-restored targets remain visible with their status.
  Imported receipts remain available during the session.

Existing receipts record paths and before/after hashes, not action-level diffs.
The inspector states this explicitly. Inspection never modifies game files.
Restore is enabled only after verification and still revalidates the receipt,
target, and process guard at execution time.

## Verification

`python -m unittest discover -s tests -q` runs domain and presentation-model tests.
On Windows, `python tools/capture_visual_qa.py` renders all five pages at 1440×880
and 1100×700 using temporary, synthetic files. It verifies preview gating, search
and columns, deck editing/saving, recovery integrity states, and modal cancellation.
PNG captures are written to `build/visual-qa-captures`. The harness does not modify
real simulator files or the user's saved deck.
