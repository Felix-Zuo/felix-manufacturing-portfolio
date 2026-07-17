# Cinematic Portfolio Release

Release date: 2026-07-17

Live site: <https://felix-manufacturing-portfolio.vercel.app/>

## Experience Contract

The homepage is a scroll-directed cinematic journey rather than a conventional long page.

- Each wheel gesture advances the rendered timeline by a small amount.
- Chapter navigation accelerates toward the selected project, then settles on its presentation beat.
- Project overlays appear only at authored stops and remain readable while the background holds.
- The final factory door resolves into a dark transition before the interactive control deck.
- Reduced-motion visitors receive a stable, usable presentation without forced motion.

## Media Masters

| Asset | Specification | Purpose |
| --- | --- | --- |
| `felix-journey-desktop.mp4` | 1920 x 1080, 24 fps, 38 s, H.264 | Large desktop master |
| `felix-journey-desktop-720.mp4` | 1280 x 720, 24 fps, 38 s, H.264 | Medium desktop delivery |
| `felix-journey-mobile.mp4` | 720 x 1280, 24 fps, 38 s, H.264 | Portrait mobile master |
| `control-room-loop.webm` | 1920 x 1080, 24 fps, 5 s | Seamless interactive deck background |

All journey masters use closed GOPs and a keyframe interval of six frames (0.25 seconds). MP4 metadata is placed before media data for progressive loading and reliable scroll seeking.

## Story Beats

1. AGV-led aisle introduction establishes the full production environment.
2. Robot cell and material-handling details introduce automated flow.
3. Grinding close-up shows the spindle, workholding, coolant, and restrained sparks.
4. Production notice project appears on an integrated machine display.
5. The takt simulator display uses a real running public-safe capture rather than a static mock.
6. Operations visibility and supporting tools complete the project system.
7. The closing door leads into the interactive portfolio control deck and contact surface.

## Public Data Boundary

- Project media, metrics, and screenshots are public-safe or synthetic unless explicitly identified as a live public tool.
- The takt simulator footage is a sanitized public run with no private production records.
- Factory imagery and 3D scenes communicate process logic without exposing customer names, internal documents, or raw plant data.
- Private traces, source spreadsheets, customer payloads, and internal evidence remain outside this repository.

## Acceptance Evidence

- Desktop frame sequence: 912 of 912 frames rendered at 1920 x 1080.
- Mobile frame sequence: 912 of 912 PNG frames validated at 720 x 1280 with no missing or invalid frames.
- Mobile encode: 912 decoded frames, 38.0 seconds, BT.709, H.264 High profile, no audio.
- Mobile seeking: 152 keyframes with an exact 0.25-second interval.
- Control-room loop: 120 frames over 5.0 seconds with an exact first/last endpoint match.
- Local delivery: homepage returns HTTP 200; byte-range video request returns HTTP 206 with the correct `video/mp4` type.
- External project links were checked; the unavailable HulunGuard Pages URL now resolves to its public GitHub repository.

## Reproduction

The production scripts under `production/` build the Blender scene, render resumable frame batches, encode browser media, and verify the control-room loop. Long render batches hold the Windows execution state to prevent Modern Standby from interrupting a render.

See the root `README.md` for exact commands and prerequisites.
