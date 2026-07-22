# Twinmotion Animation Import Diagnostic

Date: 2026-07-22

## Question

The full robot proof passes Blender GLB and FBX roundtrip validation, but the
Twinmotion viewport shows only a small subset of the animated robot geometry.
The first hypothesis was a metre/inch/centimetre scale conversion fault.

## Controlled Probe

`production/blender/build_twinmotion_scale_probe.py` exports five animated
cubes. Every cube has a final Blender world size of exactly 1 metre, but uses a
different mesh/node-scale encoding:

- applied 1 m geometry at node scale 1;
- 39.37007874 m geometry at node scale 0.0254;
- 0.0254 m geometry at node scale 39.37007874;
- 100 m geometry at node scale 0.01;
- 0.01 m geometry at node scale 100.

The GLB contains one six-second scene animation with ten translation/rotation
channels. A clean Blender roundtrip retained all five moving meshes and the
expected bounds. Twinmotion 2026.1 imported and played all five cubes at the
same visible 1 m size at both the start and moving states.

Evidence:

- `production/twinmotion/import/twinmotion-scale-probe-v1.glb`
- `production/twinmotion/import/twinmotion-scale-probe-v1.json`
- `production/twinmotion/import/twinmotion-scale-probe-v1-roundtrip.json`
- `production/scenes/twinmotion-scale-probe-v1.blend`
- `C:\Users\左雅轩\Documents\Twinmotion2026.1\FelixV7_VisualGate.tm`

## Finding

Twinmotion's general GLB animation and unit conversion path is working. The
missing full-size robot is therefore not a global scale multiplier error. It is
specific to the complex robot handoff: object hierarchy, duplicated geometry,
modifier/data ownership, or Twinmotion's interpretation of that asset.

Continuing to compensate with arbitrary scale multipliers would hide the defect
without making the production path reliable.

## Production Boundary

- **Blender:** authoritative mechanical geometry, robot kinematics, grinding
  process, coolant, sparks, conveyor motion, camera choreography, hold loops,
  and final offline-rendered footage.
- **Twinmotion:** factory-space reference, licensed environment dressing,
  static material and daylight look-development, and composition reference.
- **Website:** preloads encoded transition and hold-loop videos, then advances
  chapter-to-chapter on click/tap. It must not render the production factory in
  real time.

No mechanical asset is promoted from Twinmotion without a five-state visual
gate. For this project, Blender-rendered video is the approved delivery path.
