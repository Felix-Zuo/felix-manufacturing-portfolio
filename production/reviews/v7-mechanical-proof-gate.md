# V8 Mechanical and Visual Release Gate

Review date: 2026-07-22

This gate records the two fixed-camera chapter loops that are approved for the
portfolio. Mechanical validity, loop continuity, material treatment, framing,
and website delivery media were reviewed separately. Low-resolution review
encodes remain diagnostic artifacts and are not release media.

## Robot Pick-Place

Decision: **PASS / website approved**

Approved scene: `production/scenes/robot-pick-place-proof-v25.blend`

Evidence:

- One 159-frame scene at 24 fps; the release encode uses frames 1-158 so the
  identical terminal seam frame is not duplicated.
- The same flat bearing ring remains supported by the conveyor, follows the
  tool center point during transfer, seats on the receiving nest, and is then
  released.
- A three-jaw internal expanding gripper enters the bore and uses 12-frame
  close and release windows.
- Conveyor indexing starts only after the robot retracts from the pickup area.
- No visibility swap is used and the collision validator reports zero
  intersections.
- Raw first/last SSIM is `0.995186`; PSNR is `37.3976 dB`.
- Independent visual review found no clipping, positional seam jump, or
  vertical workpiece transport.

Validation and release media:

- `production/renders/robot-pick-place-proof/report-v25.json`
- `production/renders/robot-pick-place-proof/validation-v25.json`
- `production/renders/robot-pick-place-proof/contact-sheet-v25.png`
- `production/renders/robot-pick-place-proof/robot-cycle-v25-master-1080p.mp4`
- `public/media/holds/robot-desktop.mp4`
- `public/media/holds/robot-mobile.mp4`

## Internal Raceway Grinding

Decision: **PASS / website approved**

Approved scene: `production/scenes/grinding-process-proof-v28.blend`

Evidence:

- Fixed camera across the 96-frame, 24 fps loop.
- Workpiece and wheel axes remain horizontal and parallel.
- Workpiece contact radius is `0.142 m`; the small grinding-wheel contact
  radius is `0.050 m`.
- The coolant treatment combines nozzle streams, a contact film, asynchronous
  micro-droplets, mist, gravity rivulets, and restrained wet-grinding sparks.
- Sparks occur as two short events rather than a continuous dry-grinding plume.
- Maximum visible particle movement is `0.012844 m` per frame; the whole-frame
  freeze test found no frozen interval.
- Raw first/last SSIM is `0.993507`; PSNR is `37.818 dB`.
- Independent visual review accepted the process logic, framing, and loop seam.

Validation and release media:

- `production/renders/grinding-process-proof/report-v28.json`
- `production/renders/grinding-process-proof/validation-v28.json`
- `production/renders/grinding-process-proof/grinding-cycle-v28-master-1080p.mp4`
- `public/media/holds/process-desktop.mp4`
- `public/media/holds/process-mobile.mp4`

## Website Integration

- The process chapter uses the v28 grinding loop.
- The impact chapter dissolves from the existing camera-arrival frame into the
  v25 robot loop; leaving that chapter dissolves back into the next camera move.
- Desktop delivery is 1600x900. Mobile delivery is a subject-safe 720x1280
  center crop. Both variants are H.264, yuv420p, muted, inline, and seamless.
- The active and adjacent chapter assets are warmed; distant videos are
  released and unused reverse transition files are not prefetched.

## Release Decision

Both loops pass mechanical, visual, continuity, and delivery checks. The 640x360
review encodes must not be published; only the approved master and web
derivatives listed above may be used.
