# Cinematic Streaming Release

Release date: 2026-07-18

Production target: <https://felix-manufacturing-portfolio.vercel.app/>

## Release Intent

This release keeps the authored factory journey and replaces frame-by-frame browser seeking with a bounded streaming architecture. The experience now loads deterministically, moves through the main camera path with native video playback, and switches to lightweight animated holds when the camera settles on a chapter.

## Runtime Architecture

- The preloader selects one device profile and fetches only that profile's journey master, eight chapter holds, control-room loop, project evidence, and live takt footage.
- Exact byte totals drive the visible loading percentage and the loader does not release until every selected asset has a usable URL.
- Forward movement uses native video playback. Reverse movement uses rate-limited seeking because browser video cannot play backward natively.
- A settled chapter pauses the main journey and plays one matching ambient hold. Only one hold decoder is active at a time.
- The final control room starts its own loop only after it becomes active. The live takt video starts only when its in-scene hotspot is selected.
- Long-lived media receives immutable one-year cache headers.

## Delivery Media

| Asset group | Desktop | Mobile | Format |
| --- | --- | --- | --- |
| Main journey | 1600 x 900, 11.85 MB | 720 x 1280, 7.93 MB | H.264, 24 fps, no audio |
| Eight chapter holds | 3.45 MB total | 2.18 MB total | H.264, 24 fps, no audio |
| Control room | 1920 x 1080, 0.27 MB | 1280 x 720, 0.17 MB | VP9, 24 fps, no audio |
| Live takt evidence | 1.05 MB | shared | H.264 |

All chapter holds are forward-only. Their final frames crossfade back to their first frame, so rotating equipment, coolant, data screens, and factory movement never reverse direction.

## Authored Dynamic Holds

- Entry, impact, notice, visibility, systems, and close use forward motion extracted from their authored timeline ranges.
- The process hold is rerendered from the saved Blender scene at frame 301 with a fixed camera, rotating process geometry, restrained sparks, modulated coolant streams, and animated droplets.
- The takt hold is rerendered from frame 553 with a fixed camera while the embedded simulator values and screen state continue changing.
- Desktop and mobile process/takt holds use their own camera compositions rather than cropping one layout into the other.

## Final Control Room

The former panel-based deck is replaced by a full-scene control room. Release, takt, visibility, systems, and contact are spatial hotspots attached to monitors, consoles, and the center aisle. Selecting a hotspot changes the physical screen in the scene and reveals a lower-third project summary with real links. The closing factory door becomes a widening black center gap before the control room resolves.

## Acceptance Evidence

- `npm run lint`: pass.
- `npm run build`: pass; homepage and three case-study routes prerender successfully.
- All 16 hold files decode as H.264, 24 fps, `yuv420p`, with one video stream and no audio.
- Every hold contains a unique encoded frame at every timeline position.
- First/last hold-frame SSIM ranges from 0.948 to 0.994 after the endpoint blend.
- First load was captured with the Chinese progress gate visible before the journey released.
- Desktop and 390 x 844 mobile layouts were captured in Chrome; mobile horizontal overflow is 0 px.
- A physical wheel gesture advanced story progress from `0.16000` to `0.16570`, confirming small incremental motion.
- Entry, impact, process, control-room, and live takt videos were observed advancing while active and pausing when inactive.
- Reduced-motion emulation exposes a static-frame presentation without autoplay controls.
- The door transition was captured at three intermediate states and contains no white flash.

## Regeneration

```powershell
./production/build_stream_media.ps1
./production/render_hold_loops.ps1 -Mode desktop -Chapters process,takt -Samples 24
./production/render_hold_loops.ps1 -Mode mobile -Chapters process,takt -Samples 16
```

The hold renderer reuses the saved mature Blender scenes under `production/scenes/`; it does not reconstruct the factory from primitives.
