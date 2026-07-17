# V6 Cinematic Pacing Contract

This pass keeps the approved V6 rendered film unchanged. The browser applies a
non-linear story clock, restrained input, magnetic project stops, and accessible
HTML narration over the existing desktop and mobile media.

## Story Anchors

| Story | Source frame | Source time | Browser role |
| --- | ---: | ---: | --- |
| Entry / AGV establishing view | F001 | 0.0 s | Minimal identity caption |
| Measured impact | F169 | 7.0 s | Interlude |
| Process observation | F301 | 12.5 s | Interlude |
| Production notice | F433 | 18.0 s | Magnetic project stop |
| Takt simulation | F553 | 23.0 s | Magnetic project stop |
| Operations visibility | F673 | 28.0 s | Magnetic project stop |
| Connected public systems | F793 | 33.0 s | Magnetic project stop |
| Contact | F877 | 36.5 s | Finale |
| Physical handoff | F912 | 38.0 s | End of story clock |

Each interval uses a blended linear/smoothstep curve. The non-zero linear share
prevents the camera from sticking when it leaves a chapter, while smoothstep
provides visible deceleration into and acceleration out of each anchor.

## Input Contract

- A standard 100-pixel wheel notch advances about 0.085 seconds at the opening.
- Wheel magnitude is normalized and clamped across mouse and trackpad hardware.
- The timeline follows its target with exponential damping and a hard velocity cap.
- Crossing a project anchor clamps the target to that anchor.
- Trackpad momentum cannot release a stop. Input must become idle for 260 ms, then
  a new wheel gesture releases the chapter.
- Touch movement uses the same story clock with viewport-relative sensitivity.

## Narration Contract

- Entry begins on the full AGV establishing frame, not the bearing close-up.
- Interludes remain compact and do not cover the camera subject.
- Project chapters reframe the media slightly toward the available side and open
  an unframed editorial rail opposite the embedded project screen.
- Each project explains the operating problem, three evidence points, one outcome
  metric, and the available case-study/project links.
- Desktop project rails alternate sides according to shot composition. Mobile
  uses a bounded bottom editorial layer with internal overflow protection.
- Reduced-motion mode keeps the F001 poster and removes timeline animation.

## Final Handoff

- The accepted V6 film still owns the factory journey. No source MP4 is re-encoded.
- The media layer uses slight overscan during project reframing so motion never
  exposes the page background at the lower or side edges.
- After the final door movement, story progress 0.978-1.000 drives a scroll-bound
  black gate into the interactive operations control deck.
- The control deck exposes four real project channels: Release, Flow, Inventory,
  and System. Each channel uses existing public screenshots, case-study routes,
  live demos, repositories, outcomes, and public-data boundaries.
- Two matched generated control-room frames crossfade on a five-second
  0-1-0 loop. The geometry remains fixed; only restrained status lighting changes.
- The final deck keeps direct contact, GitHub, supporting systems, and a return
  control back to the final factory frame.

## Verified Browser States

- Desktop project times: 18.0 s, 23.0 s, 28.0 s, and 33.0 s.
- One-notch opening advance: about 0.085 s.
- Magnetic stop release: the next post-idle wheel gesture advances the film.
- Desktop and 390 x 844 mobile layouts: zero document horizontal overflow.
- Mobile source: dedicated 360 x 640 MP4.
- Reduced motion: video hidden, poster retained, zero runtime errors.

Design behavior follows the same principles exposed by GSAP ScrollTrigger's
numeric scrub and label snapping: one timeline owns the experience, smoothing is
applied to playhead catch-up, and narrative anchors are explicit rather than
inferred from whichever card happens to be nearest.
