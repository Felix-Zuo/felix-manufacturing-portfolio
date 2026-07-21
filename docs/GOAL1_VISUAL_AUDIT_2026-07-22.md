# Goal 1 Visual Audit

Date: 2026-07-22

## Evidence

- User process reference: `codex-clipboard-46084529-3976-4413-813a-a1c356e9f6df.png`
- User impact reference: `codex-clipboard-280bd127-c836-436e-93d0-42296e850bde.png`
- Fresh local baseline: `production/renders/browser-qa/v16-goal1-before/`
- Process comparison: `compare-process.png`
- Impact comparison: `compare-impact.png`
- Existing hold-loop contact sheet: `holds/all-holds.png`

## Findings

1. The process hold creates 72 UV spheres as coolant droplets. At the current camera
   scale they read as white balls, while elongated splash geometry reads as rigid
   white rods. The result is visually disconnected from the nozzle and contact patch.
2. Existing one-second holds for impact, notice, visibility, system, and close are
   excerpts from a moving-camera master. They fade back to the first frame, creating
   a visible reset and the reported camera twitch.
3. The impact hold contains the robot scene, but its camera is not fixed and the
   held workpiece remains attached through the whole move. This makes the loading
   action ambiguous and exposes intersections near the conveyor.
4. Only process and takt ambient media are currently mounted in the React chapter
   data, leaving other arrived chapters static.
5. The route rail is visual-only. Previous navigation changes the chapter with a CSS
   fade instead of playing the adjacent transition in reverse.
6. The final chapter id is `contact`, while its still and hold media are named
   `close`, causing avoidable preload and fallback failures.
7. The lower-right next control exists but the full-canvas click affordance is not
   continuously explained after the start gate, especially on touch screens.

## Design Decision

Keep the accepted transition films unchanged. Repair the experience around them with
fixed-camera chapter loops, a direction-aware transition player, clickable route
nodes, and a single consistent interaction cue. Avoid extra floating HUD elements;
motion must support the story rather than add visual noise.

## Implemented Repair

1. The process chapter now uses a fixed camera and an integer-turn loop for the
   wheel and workpiece. Procedural translucent coolant sheets stay connected to
   the nozzles, while a small set of orange contact sparks replaces the former
   white sphere and rod particles.
2. The impact chapter now runs a three-second robot loading loop. The workpiece is
   visible only during the pickup and placement window, and the conflicting
   foreground guard rail is removed from this camera so the cycle reads cleanly.
3. All eight chapter arrivals now mount an ambient MP4 loop. The six non-custom
   holds use seamless ping-pong excerpts; impact and process use purpose-rendered
   fixed-camera loops.
4. Fourteen reverse desktop/mobile clips were generated for adjacent backward
   navigation. Route nodes use these clips for one-step travel and a black fade for
   longer jumps.
5. The scene now exposes a continuous click/tap cue, clickable route nodes, pointer
   feedback, layered panel motion, keyboard controls, input locking, and mobile and
   reduced-motion behavior.
6. The final chapter maps `contact` to the existing `close` media and continues into
   the interactive control deck instead of failing over to a static image.

## Verification Evidence

- Blender source scripts compile successfully.
- `npm run lint -- --quiet` passes.
- `npm run build` passes and statically generates all portfolio and case routes.
- Desktop browser QA verified forward travel, reverse travel, long route jumps,
  every hold loop, the door handoff, and the interactive takt display.
- Mobile browser QA at 390 x 844 verified dedicated portrait media, tap navigation,
  readable controls, and `scrollWidth === innerWidth`.
- Impact first/last-frame SSIM measured approximately `0.999874`; the process loop
  was also inspected at its seam and in a side-by-side reference comparison.
- Visual comparison sheets are stored under
  `production/renders/browser-qa/v16-goal1-after/` for local review.

## Release Evidence

- Implementation commit: `ee8b9b7` on `codex/v8-streamed-cinematic`.
- Production alias: `https://felix-manufacturing-portfolio.vercel.app/`.
- Vercel production build completed with Next.js 16.2.10 and generated all seven
  static/SSG routes.
- Production checks returned HTTP 200 for the home page, the impact desktop hold,
  the process mobile hold, and the process-to-impact reverse transition. Versioned
  media responses use `public, max-age=31536000, immutable`.
- A fresh production-browser run completed the Impact-to-Process transition and
  reported no errors or warnings.
