# Quiet Precision

Sim Controls is a compact Windows productivity tool, not a dashboard. Its interface should recede until an action, warning, or selection needs attention. Hierarchy comes from typography, spacing, alignment, and small changes in neutral surface tone. Borders are reserved for focus, selection, and controls that genuinely need an edge.

## Foundation

- Use Segoe UI Variable Display for page and section headings and Segoe UI Variable Text for controls and body copy. Cascadia Mono is reserved for paths and machine-facing values.
- Use natural title and sentence case. Preserve capitalization only for real names and acronyms such as ACC, ABS, and SimHub.
- Keep a neutral near-black application background with graphite surfaces. Do not tint every surface blue.
- Use blue for intent and selection, mint for healthy state, amber for attention, and coral only for errors or destructive actions.
- Use the 4, 8, 12, 18, 24, and 32 pixel spacing scale. Density should feel deliberate rather than cramped.

## Components

- Primary buttons are reserved for the next meaningful action. Secondary buttons use a quiet raised surface. Ghost buttons expose low-priority actions without adding another rectangle. Destructive buttons remain subdued until hovered or focused.
- Inputs and selects sit on a single raised plane with no persistent keyline. Keyboard focus adds a clear blue keyline. Disabled controls lose contrast and accent color.
- Navigation uses one coherent Fluent icon set, a label, a narrow blue selection edge, and a subtle tonal change. The sidebar should not compete with the active workspace.
- Tables use calm headers, compact rows, sticky identity columns, synchronized selection, row hover, and horizontal scrolling where the data requires it.
- Status is communicated with a small semantic dot plus plain language. Avoid decorative badges and KPI cards.

## Page composition

- Overview uses a centered, moderate-width summary. Source locations remain collapsed until requested.
- Deck Studio uses the full workspace. The deck canvas is centered and paired with a contextual inspector; the command bar contains only page, grid, mode, automation, and save controls.
- Control Map uses the full width because its data benefits from it. Search and filters remain a light part of the table toolbar.
- Bindings is a focused editor with an explicit `simulator action → current binding → SimHub target` relationship and an intentional maximum width.
- Recovery is a narrow, task-focused flow with protection details presented as supporting information.

## Interaction

Every interactive component must account for default, hover, active, focus, selected, disabled, loading, and error states. Transitions should be fast and quiet. Selection and connection changes may use restrained color; the rest of the interface stays neutral.
