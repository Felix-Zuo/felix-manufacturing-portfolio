# Twinmotion Production Pipeline

## Chosen Workflow

1. Use the existing Blender scene as the dimensional and mechanical source.
2. Use Twinmotion for static factory-space, material, daylight, and composition
   references only.
3. Reproduce the approved static look in Blender and keep the mechanically
   validated robot, grinder, coolant, sparks, conveyor, and camera there.
4. Render one short transition proof and one fixed-camera hold loop before the
   complete journey.
5. Encode the approved transition and hold masters as preloaded web video.
6. Advance the website by click/tap between chapter nodes; do not run the
   production factory as real-time browser 3D.

Blender is the final animation and rendering tool. Twinmotion remains a useful
look-development reference, but its complex robot import failed the visual gate
even though the same GLB and FBX files passed clean Blender roundtrips. See
`TWINMOTION_IMPORT_DIAGNOSTIC.md` for the controlled scale-probe result.

## Local Export

```powershell
$blender = 'D:\0A OpenClaw\projects\展示项目\tools\blender-4.5.11-windows-x64\blender.exe'
& $blender `
  --background 'production\source-scenes\felix-journey-v4-desktop.blend' `
  --python 'production\twinmotion\export_for_twinmotion.py'
```

Generated import packages:

- `production/twinmotion/import/felix-v5-environment-static.glb`
- `production/twinmotion/import/felix-v5-mechanical-animation.glb`
- `production/twinmotion/import/felix-v5-mechanical-core.glb`
- `production/twinmotion/import/scene-inventory.json`

Validate the complete GLB in a clean scene:

```powershell
& $blender `
  --background `
  --factory-startup `
  --python 'production\twinmotion\validate_export.py'
```

Import `environment-static.glb` through Twinmotion Geometry import. Import `mechanical-animation.glb` through the Animation tab so its tracks are available in Sequence mode.

## Mechanical Proof Handoff Gate

Do not refresh an older Twinmotion animation card when comparing exporter
formats. A refresh can preserve stale hierarchy visibility and cached import
state. Import each candidate as a new Animation card, keep all older candidates
hidden, and visually check the first, midpoint, contact, placement, and final
states.

The robot proof is exported with inherited world motion baked onto independent
visible objects. Twinmotion receives a shallow static root rather than the deep
robotics hierarchy used for mechanism authoring.

```powershell
& $blender `
  --background 'production\scenes\robot-pick-place-proof.blend' `
  --python 'production\blender\export_twinmotion_proof.py' -- `
  --output 'production\twinmotion\import\robot-pick-place-v9.fbx' `
  --report 'production\twinmotion\import\robot-pick-place-v9.json' `
  --asset-id robot-pick-place-v9 `
  --family robot `
  --format fbx
```

Roundtrip the exact handoff file through a clean Blender scene before opening
Twinmotion. This proves that mesh count, animation actions, sampled world motion,
and the loop envelope survive interchange.

```powershell
& $blender `
  --background `
  --python 'production\blender\validate_twinmotion_roundtrip.py' -- `
  --input 'production\twinmotion\import\robot-pick-place-v9.fbx' `
  --report 'production\twinmotion\import\robot-pick-place-v9-roundtrip.json'
```

Passing the roundtrip gate is necessary but not sufficient. Twinmotion playback
must still show the complete robot and workpiece movement in the viewport before
material dressing or camera work begins.

## First Lookdev Gate

Before authoring the full sequence, produce one 1920x1080 five-second render matching `production/v5/source-frames/s01-entry-clean.png`:

- central aisle and vanishing point match;
- robot, fence, grinder, AGV and recessed screen have correct scale and clearance;
- daylight and materials are within the approved palette;
- no incorrect process action, clutter, floating UI, rail conflict, or baked text;
- no visible geometry or animation defect in the first and final frames.

Only after this proof passes should the full camera and project checkpoints be authored.
