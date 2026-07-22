# V8 Cinematic Recovery Record

Status: **mechanical recovery and web integration complete**

The V6 interaction architecture is useful, but its visual source is not an
approved production asset. The current robot hold, grinding hold, chapter loop
builder, material pass, and Twinmotion lookdev all failed visual review. No new
case-study scene should be built on that foundation.

## What Failed

1. The robot motion is a hand-authored six-joint pose table. It has no inverse
   kinematics target, collision envelope, grasp constraint, or physical transfer
   of a workpiece. The hold renderer only swaps render visibility between two
   ring meshes. The result reads as an arm nodding through the conveyor.
2. Most hold clips are made by concatenating a forward camera move with its
   reverse. This creates the rejected camera rubbing and is not environmental
   motion.
3. The grinding scene uses a presentation transform and almost perfectly
   rotationally symmetric proxy parts. The real work axis is not visually
   legible, and no world-space spindle-axis check exists.
4. Coolant is animated by scaling curve and sheet proxies. Sparks are a small
   set of moving ico spheres. Neither passes a close industrial-process shot.
5. The factory is mostly project-authored primitive geometry with placeholder
   Principled materials. Only one local PBR texture set exists. The Twinmotion
   cloud library has not been populated, so previous claims of a Twinmotion
   material pass were inaccurate.
6. The existing Twinmotion project opens, but it contains an imported long hall
   at distant overview scale in the default environment. It is not the promised
   dressed, lit, camera-authored production scene.
7. Several review documents marked assets as production-ready from object
   counts and script metadata. Those checks did not prove silhouette, contact,
   clearance, material response, or motion quality.

## Durable Toolchain Decision

### Blender / CAD source

Owns dimensional geometry, pivots, robot hierarchy, inverse kinematics,
constraints, workholding, conveyor contact, collision checks, and all mechanical
animation. A renderer cannot repair invalid mechanism design.

### Twinmotion 2026.1

Provides scale calibration, library exploration, material and lighting lookdev,
and a visual reference gate. The validated 1:1 Blender-to-Twinmotion scale chain
is documented in `production/twinmotion/TWINMOTION_IMPORT_DIAGNOSTIC.md`.
Twinmotion does not own the final mechanical loops because its imported hierarchy
and automation surface cannot provide the deterministic collision, contact, and
loop-seam checks required here.

### Web application

Owns chapter input, one-way transition playback, accessible bilingual project
content, DOM overlays, hover/pointer effects, and final five-zone interaction.
It must not fake camera motion while a chapter is stopped.

### CLI-Anything

The official general and Blender skills are installed locally. The Blender
harness is useful for bounded scene creation, JSON inspection, and preview
automation. It does not replace Blender's own Python API, inverse kinematics,
simulation, or Twinmotion lookdev. The current harness also does not open the
binary `.blend` production scene as a native editable project, so it is an
automation aid rather than the core DCC pipeline.

## Recovery Sequence

1. **Complete:** freeze the public V6 media as a rollback asset.
2. **Complete:** enforce the source contracts in `production/tests/`.
3. **Complete:** build and validate the 6.58-second fixed-camera robot cycle.
4. **Complete:** build and validate the 4-second fixed-camera grinding cycle.
5. **Complete:** record AmbientCG CC0 PBR sources and replace proof materials.
6. **Complete:** validate Twinmotion scale import and retain it as a lookdev
   reference rather than an unchecked final-animation path.
7. **Complete:** preserve adjacent one-way camera transitions, publish only the
   independently validated robot and grinding fixed-camera loops, and keep all
   other chapter anchors on still frames.
8. **Complete locally:** integrate desktop/mobile media, click navigation,
   reverse playback, bilingual content, five-zone finale, and case-study routes.
   Production URL verification remains part of the deployment gate.

## Approval Gates

The next full cinematic render is forbidden until both mechanical proofs pass.
The website may not label a scene as approved based only on build success,
object counts, metadata, or a single still frame.

Every visual gate requires:

- a neutral-light turntable or mechanism view;
- first, midpoint, contact, placement, and final-frame captures;
- a contact sheet covering the complete loop;
- measured clearance and axis checks;
- first/last-frame equality for an environmental loop;
- visual review at native desktop and mobile crop sizes;
- a license record for every external model or texture.

## Definition of Done for the Reopened Goal

- Robot transfers one flat bearing ring from the conveyor pickup nest to a
  machine/load nest and returns home without penetrating the belt, fence,
  workpiece, or fixture.
- Grinding workpiece and wheel rotate around their actual spindle axes. The
  small profiled wheel contacts the inner raceway; coolant and sparse sparks
  remain subordinate to the machining evidence.
- Chapter holds contain no camera animation and no reverse-video construction.
- Twinmotion import is scale-validated and used only for lookdev decisions; the
  released Blender loops use recorded PBR materials and authored lighting.
- The eight-chapter journey and five-zone finale use only assets that passed the
  gates above. Final evidence is recorded in
  `production/reviews/v7-mechanical-proof-gate.md`.
