# Goal 2 Factory Project Hub Specification

Date: 2026-07-22

## Scope

Goal 2 changes only the post-door control room. It does not build the five full
case-study pages and does not introduce the bilingual content framework reserved
for later goals.

## Design Target

Preserve the accepted control-room film, top navigation, industrial typography,
black metal surfaces, amber signal color, and low-positioned evidence panel. The
factory remains the primary visual; interface elements identify real spatial zones
instead of covering the scene with a dashboard or card grid.

## Five Factory Zones

1. Planning control: pull-based rolling production scheduling.
2. WIP and inventory: WIP governance and account-card-material integrity.
3. Procurement control: BOM expansion, net demand, and supply-risk warning.
4. Supplier resilience: overseas supplier performance and logistics risk.
5. Skills and standards: frontline skills, standard work, maintenance, 5S, and EHS.

## Interaction Contract

- The room opens in an overview state with all five signals visible.
- Clicking a signal or its rail entry selects the same project state.
- Selection applies a restrained camera push, strengthens the spatial marker, and
  reveals a project briefing without pausing the background film.
- The briefing shows an evidence-based outcome, a concise operating description,
  and three project signals.
- Escape first returns to the five-zone overview; a second Escape returns to the
  cinematic journey.
- Arrow, Home, and End keys move focus spatially between the five zones.
- Mobile keeps the full room visible, uses a five-position rail, and moves the
  project briefing below the scene instead of covering it.

## Acceptance Criteria

- Exactly five project zones are visible and individually selectable.
- No zone link produces a dead route before the project-page goals are complete.
- Guidance is readable without competing with the factory scene.
- Selection transitions do not reset or interrupt the background loop.
- Desktop and 390 px mobile layouts have no horizontal overflow.
- Pointer, keyboard, reduced-motion, and focus states are complete.
- Browser visual comparison, console inspection, lint, and production build pass.

## Implementation Notes

- Project content lives in a typed five-entry atlas so future bilingual and case
  page goals can extend one stable contract.
- The accepted control-room film remains the visual source of truth. Selection
  changes only camera framing and interface emphasis; it does not replace or
  restart the scene.
- Goal 2 intentionally opens an in-scene briefing rather than linking to empty
  project routes. Full project navigation is activated when Goals 4 and 5 deliver
  the corresponding pages.
- The desktop experience uses both spatial hotspots and a persistent project rail.
  Mobile retains the full scene, then places the same overview or briefing below
  the five-position rail.

## Verification

- Same-state visual comparison completed at 1280 x 720.
- Responsive inspection completed at 390 x 844 with zero horizontal overflow.
- Scene hotspots, rail selection, keyboard focus, Enter, Escape, and the journey
  return path were exercised in the browser.
- Direct `/#control` loading, continuous video playback, and reduced-motion pause
  behavior were verified.
- Browser console inspection returned no warnings or errors.
