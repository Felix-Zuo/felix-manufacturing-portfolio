# Storyboard Round 4 Motion Review

- Review date: 2026-07-13
- Reviewer role: independent visual quality reviewer
- Gate: `production/QUALITY_GATE.md`
- Scope: motion and visual continuity only; no code, scene, or render changes

## Verdict

**FAIL - do not start the final high-resolution render.**

Both 28-second playblasts are technically complete and share the expected timing:

| Version | Resolution | Rate | Frames | Duration |
| --- | ---: | ---: | ---: | ---: |
| Desktop | 640 x 360 | 24 fps | 672 | 28.000 s |
| Mobile | 360 x 640 | 24 fps | 672 | 28.000 s |

The route is recognizably one continuous move, and Round 3's mobile framing fixes are present. However, two motion findings remain blocking because they would be baked into the expensive final render.

## P0 Blocking Findings

### P0-1: Grinding-cell exit loses all continuity cues

- **Desktop:** `00:09.67-00:10.33`
- **Mobile:** `00:09.67-00:10.33`

After the grinding contact, the camera sweeps past the enclosure and the image becomes almost entirely an uninformative grey/white wall before it reacquires the corridor. Frame-by-frame inspection shows no hard edit, but the visual result reads like a wall clip or an empty whip: the subject, twin rail, enclosure edge, and forward destination all disappear together.

This violates the requirements for an uninterrupted spatially legible move and for transitions without wall clips. The transition must retain at least one stable spatial cue and must not spend this long on a nearly empty wall.

### P0-2: The ending cuts off while the camera is still advancing

- **Desktop:** `00:27.20-00:28.00`
- **Mobile:** `00:27.20-00:28.00`

The physical door is a valid endpoint, but its scale continues increasing through the final available frame. There is no perceptible terminal ease or stable landing beat before the file ends, so the shot stops mid-push rather than arriving. This is especially obvious in the mobile crop, where the door continues expanding beyond the frame edges during the last second.

The final move needs a visible deceleration and a short stable endpoint before frame 672, or sufficient additional duration for the landing to complete.

## Motion Findings That Pass

- No hard cut was found. The large visual change around `00:03.13-00:03.33` is a continuous bearing-to-robot reveal, not an edit.
- No sustained camera roll is visible; vertical frames and the horizon remain controlled in both versions.
- No black frame or sustained frozen frame was observed.
- The bearing, six-axis arm, mounted grinding cell, screen stands, and terminal door retain consistent factory placement.
- Bearing races and rolling elements read credibly at the intended distance.
- The robot reads as a mounted six-axis industrial arm; base, joints, fasteners, cable route, wrist, and tooling remain recognizable through the pass.
- Grinding contact and sparks are visible. The operation is understandable at first glance, although the abrasive/contact separation remains a polish risk.
- The twin rail establishes the opening direction, reappears through the corridor transits, and resolves at the terminal door.
- Screen approaches are spatially differentiated rather than repeated locked shots.
- Updated mobile keyframes `02` and `04` preserve the complete robot silhouette, twin rails, display frame, and evidence content inside the 9:16 crop.
- The Felix Zuo endpoint signature remains restrained and environmental.

## Remaining Non-Blocking Risks

- Project titles are readable near approximately `00:12.00-00:12.75`, `00:15.50-00:16.50`, `00:19.25-00:20.00`, and `00:22.50-00:23.50`; smaller evidence copy is not reliably readable in the playblast. Final motion blur must not shorten these windows further.
- The repeated screen exits around `00:13.00`, `00:16.75`, `00:20.00`, and `00:23.75` use similar whip-away rhythms. They are continuous, but may feel formulaic in the final grade.
- White shells, walls, and floors are close in value. The final render must retain edge definition and avoid clipping the lower white regions of the project screens.
- The grinding sparks are restrained, but the small abrasive tool and workpiece should remain materially distinct at final resolution.
- The orange robot cable is visually prominent; its attachment and deformation must remain mechanically plausible during the final animation.

## Re-Review Requirement

Submit revised desktop and mobile playblasts covering the same 672-frame route. Re-review can be limited to the two blocking windows plus confirmation that their timing changes do not create new jumps at adjacent chapter boundaries. Final high-resolution rendering remains blocked until both P0 findings are cleared.
