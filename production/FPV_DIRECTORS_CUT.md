# FPV Director's Cut Production Contract

## Picture Lock

This is one uninterrupted industrial FPV shot: `38.000 s`, `24 fps`, and exactly
`912` frames numbered `F001-F912`. There are no cuts, duplicated frames, editorial
speed ramps, or alternate-duration web versions. The camera begins in motion,
threads the factory evidence in one forward route, and only settles after the final
focus beat. Scene-action bullet time may slow local motion, but it must not retime
or stop the camera path.

For one-indexed frame numbers, the presentation time of a frame is
`(frame - 1) / 24`. The sequence endpoint is 38.000 seconds after 912 displayed
frames. The canonical focus list is:

`[91, 169, 301, 433, 553, 673, 793, 877]`

## Eight-Beat Shot

Focus frames are review anchors, not edit points. Motion, aim, focal length, roll,
exposure, and scene action must remain continuous between them.

| Beat | Span | Focus | Required picture and movement |
| --- | --- | --- | --- |
| 01 - Bearing datum | 00:00.000-00:04.500 / F001-F108 | 00:03.750 / F091 | Enter low over the twin rails and skim the bearing closely enough to read the races, cage, and rolling elements. No static hero opening. |
| 02 - Mechanical handoff | 00:04.500-00:09.000 / F109-F216 | 00:07.000 / F169 | Carry the same forward move across the six-axis arm, preserving the full joint chain and TCP handoff as the route bends toward grinding. |
| 03 - Grinding evidence | 00:09.000-00:15.000 / F217-F360 | 00:12.500 / F301 | Pass into the guarded wet-grinding cell and resolve the small CBN wheel, raceway contact, coolant, and restrained micro-sparks without a wall or spindle collision. |
| 04 - Notice control | 00:15.000-00:20.000 / F361-F480 | 00:18.000 / F433 | Reacquire the corridor and present the production-notice screen square enough to read its primary state while the FPV move continues. |
| 05 - Takt control | 00:20.000-00:25.000 / F481-F600 | 00:23.000 / F553 | Cross to the takt screen with its main value and curve inside both desktop and mobile safe composition. |
| 06 - Operations visibility | 00:25.000-00:30.000 / F601-F720 | 00:28.000 / F673 | Advance to the operations view, keeping the abnormal state and closed-loop evidence legible without losing the rail direction. |
| 07 - Connected systems | 00:30.000-00:35.000 / F721-F840 | 00:33.000 / F793 | Skim the connected-systems screen with its principal nodes and data path centered, then return the look direction to the physical endpoint. |
| 08 - Improvement loop | 00:35.000-00:38.000 / F841-F912 | 00:36.500 / F877 | Land on the final precision-inspection portal and improvement-loop endpoint; decelerate into a stable finish through F912 without a cut, reverse, or abrupt stop. |

The persistent hierarchy is twin rails first, one evidence subject per beat second,
and factory architecture third. `Felix Zuo` remains a restrained environmental
nameplate, never an extra focus beat. The desktop frame must preserve full spatial
context; the mobile master must independently keep every beat's critical evidence
inside its 9:16 safe composition.

## Master Deliverables

Both masters use the same camera clock, beat order, focus frames, and 912-frame
range. Mobile is a dedicated render, not a center-cropped desktop encode.

| Master | Raster | Rate / duration | Render sequence | Web output |
| --- | ---: | --- | --- | --- |
| Desktop | 1920 x 1080 | 24 fps / 38.000 s | `production/renders/desktop-frames/frame-%04d.png` | `public/media/felix-journey-desktop.mp4` |
| Mobile | 1080 x 1920 | 24 fps / 38.000 s | `production/renders/mobile-frames/frame-%04d.png` | `public/media/felix-journey-mobile.mp4` |

The PNG paths above are the display-referred Beauty sources consumed by the web
encoder. The finishing handoff must also contain, for every frame and both aspect
ratios, aligned linear OpenEXR material with matching resolution and numbering:

- **Beauty:** the complete final image used for grading and the approved web source.
- **Clean Plate:** identical camera, geometry, lighting, exposure, and motion with
  replaceable screen content and portfolio overlays removed.
- **Screen Matte:** a lossless screen-surface isolation pass, black outside the
  intended display areas, with stable IDs when more than one display is visible.
- **EXR:** half-float linear scene-referred files with no lossy intermediate; Beauty,
  Clean Plate, and Screen Matte must stay pixel- and frame-aligned.

Missing frames, stale frames from another duration, mismatched cameras, baked web
HTML, or a matte that does not track the display surface blocks mastering approval.

## Render Gates

1. **Contract preflight:** Blender receives `--duration 38.0`; scene metadata reports
   24 fps, `F001-F912`, one shot, and the canonical eight focus frames.
2. **Storyboard gate:** review all eight focus frames in desktop and mobile. Confirm
   subject evidence, rail direction, horizon, screen framing, and mobile safety.
3. **Playblast gate:** render complete 912-frame desktop and mobile playblasts first.
   Review continuous speed, look direction, collisions, occlusion, screen dwell,
   grinding entry/exit, final deceleration, and the stable endpoint. Written v6
   approval is required; the legacy 28-second review cannot be reused.
4. **Final-render gate:** only an approved playblast may start final Beauty and pass
   rendering. Camera curves, duration, focus frames, and aspect-specific framing are
   locked after approval.
5. **Mastering gate:** confirm 912 aligned frames for Beauty, Clean Plate, Screen
   Matte, and EXR in both aspect ratios, with no missing or duplicated frame.
6. **Web gate:** verify each MP4 is 38.000 seconds, 24 fps, 912 frames, H.264
   `yuv420p`, BT.709-tagged, fixed closed 12-frame GOP behavior, `faststart`, and has
   no audio stream. Scrub tests must pass on desktop and mobile before release.

## Web Encoding And Audio Boundary

`encode_media.ps1` encodes the approved Beauty PNG sequence with libx264, CRF 19,
BT.709 container metadata and x264 VUI, `yuv420p`, closed GOP 12, keyframe minimum
12, scene-cut keyframes disabled, and `faststart`. It validates a whole-frame
duration, requires every expected source frame, and caps output at the exact frame
count. The poster comes from F091, the first approved focus frame.

A standalone 38-second film may include approved music, sound design, or narration
in a separate audiovisual master. The desktop and mobile MP4 files used for
scroll-scrubbing are picture-only delivery assets: they remain silent (`-an`) and
must never acquire an embedded audio stream during later transcoding.
