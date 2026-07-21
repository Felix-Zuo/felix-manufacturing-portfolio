# Cinematic Portfolio V16 Roadmap

Date: 2026-07-22

Status: Goal 1 completed locally and ready for release verification. Goals 2-6
remain pending until the user explicitly says to continue.

This roadmap is the durable scope contract for the next portfolio release. Work is
delivered one goal at a time. Goal 1 is the only implementation scope for the
current task; Goals 2-6 remain explicitly pending until the user says to continue.

## Product Direction

Preserve the accepted cinematic factory journey and its industrial control-room
visual language. The journey uses two coordinated media layers:

- Transition films move the camera between chapters.
- Fixed-camera ambient loops keep each arrived chapter alive without replaying or
  twitching the camera.

The click, keyboard, and progress controls operate the same chapter state machine.
Adjacent navigation plays the matching film. Non-adjacent navigation uses a short
black fade so the visitor can move directly without scrubbing through several clips.

## Goal 1 - Repair the Cinematic Journey

**Completion:** Implemented on `codex/v8-streamed-cinematic`.

### Steps

1. Preserve the accepted forward transition films and remove visual defects from
   chapter holds.
2. Replace the process hold's rigid white spheres and rod-like fluid geometry with
   restrained coolant sheets, mist, wheel rotation, and sparse contact sparks.
3. Replace the impact hold with a fixed-camera robot loading cycle that keeps the
   tool, horizontal bearing ring, conveyor, and machine envelope spatially valid.
4. Give every arrived chapter a seamless ambient loop; no camera reset or visible
   first-frame cut is allowed.
5. Play the adjacent transition in reverse when returning one chapter.
6. Make all desktop route nodes actionable. Use a black fade for multi-chapter
   jumps and keep the mobile transport compact.
7. Add an explicit next-scene prompt, a restrained cursor state, layered panel
   depth, keyboard parity, reduced-motion behavior, and input locking during films.
8. Verify desktop, mobile, direct hashes, console output, media loading, and the
   final door/control-room handoff.

### Acceptance Criteria

- No bright white coolant balls, rods, or unexplained moving objects remain in the
  process hold.
- The impact hold shows a readable loading action without robot/conveyor clipping.
- A chapter hold never moves the camera and never visibly jumps at its loop seam.
- Click/next plays forward; previous plays the adjacent film backward.
- Clicking any route node works; long jumps fade through black.
- Navigation is disabled only while a transition is actually playing.
- The final chapter resolves the `contact`/`close` media naming mismatch.
- `npm run lint` and `npm run build` pass, and browser QA covers desktop and mobile.

### Delivered

- Rebuilt the impact hold as a fixed-camera, three-second robot loading loop with
  a correctly timed horizontal workpiece and without the foreground rail collision.
- Rebuilt the process hold as a two-second machining loop with rotating tooling,
  restrained translucent coolant, and compact orange contact sparks. The former
  white spheres, rods, and moving splash artifacts are removed.
- Added seamless ambient holds for every chapter and separate desktop/mobile media.
- Added direction-aware adjacent navigation, including dedicated reverse clips;
  multi-chapter route-node navigation now uses a short black fade.
- Added persistent click/tap guidance, actionable progress nodes, keyboard parity,
  layered information-panel depth, a restrained pointer treatment, and mobile and
  reduced-motion fallbacks.
- Resolved the final `contact`/`close` asset mapping and preserved the animated
  control-room handoff after the door chapter.
- Browser QA covered the complete desktop journey, reverse playback, long jumps,
  the final interactive control deck, and 390 px mobile layouts with no horizontal
  overflow.

## Goal 2 - Build the Five-Zone Factory Project Hub

### Steps

1. Rebuild the post-door destination as one premium, continuously alive factory
   command environment rather than a stack of cards.
2. Define five physically legible interactive factory zones: planning control,
   WIP/inventory, procurement, supplier resilience, and skills/standard work.
3. Add strong spatial labels, hover/focus responses, zoom transitions, and a clear
   return path into the cinematic journey.
4. Use a seamless, subtle control-room/factory background loop that remains visible
   beneath the interface.

## Goal 3 - Add the Bilingual Foundation

### Steps

1. Move all journey, hub, navigation, metadata, and case-study copy into typed
   Chinese/English content dictionaries.
2. Add a compact navigation language switch and persist the visitor's choice.
3. Provide bilingual metadata, accessibility labels, chart labels, and route copy.
4. Verify typography, line wrapping, and mobile layout in both languages.

## Goal 4 - Create Project Pages 1 and 2

### Steps

1. Build the pull-based rolling production scheduling case study.
2. Build the WIP governance and account-card-physical consistency case study.
3. Create project-specific diagrams, timelines, Gantt views, KPI evidence, and
   restrained animated backgrounds.
4. Add chapter navigation, bilingual copy, and premium pointer/focus behavior.

## Goal 5 - Create Project Pages 3, 4, and 5

### Steps

1. Build the BOM expansion and procurement risk warning case study.
2. Build the overseas supply-chain resilience and supplier management case study.
3. Build the frontline skills and standard-work management case study.
4. Create project-specific charts, process maps, visual evidence, bilingual copy,
   and matching cinematic transitions.

## Goal 6 - Final QA and Release

### Steps

1. Run motion, responsive, keyboard, reduced-motion, and browser-console QA.
2. Measure media payloads, preload behavior, dropped frames, and interaction latency.
3. Validate every route, language state, project-zone hotspot, and external link.
4. Commit, push, deploy to Vercel, and record production URL and release evidence.

## Source Material for Goals 2-5

- Project 1: pull-based rolling production scheduling, supplied in the user brief on
  2026-07-22.
- Project 2: `C:\Users\左雅轩\.codex\attachments\0d580dd3-8848-4a9f-9092-a0ce53ee6e63\pasted-text.txt`
- Project 3: `C:\Users\左雅轩\.codex\attachments\efcfbdc5-5818-4d90-bad9-ce075fca79e1\pasted-text.txt`
- Project 4: `C:\Users\左雅轩\.codex\attachments\5737d591-5266-4ceb-87e3-a4a751045122\pasted-text.txt`
- Project 5: `C:\Users\左雅轩\.codex\attachments\933191db-7626-4afe-bedc-439b1d98161b\pasted-text.txt`

Private source material stays local. Only rewritten, public-safe portfolio content
and generated visual assets may be committed.
