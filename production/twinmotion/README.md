# Twinmotion Production Pipeline

## Chosen Workflow

1. Use the existing Blender scene as the dimensional and mechanical source.
2. Export static factory geometry and animated robot/grinding assemblies as GLB.
3. Assemble licensed environment modules and PBR assets in Twinmotion.
4. Replace V4 lookdev with clean daylight, path-traced materials, and an exact camera sequence.
5. Render a short 5-second lookdev proof before building the complete 30-second journey.
6. Encode the approved master for scroll-controlled playback on the website.

Twinmotion is the final visual tool. Blender remains in the pipeline because Unreal/Twinmotion are not mechanical modeling applications and cannot replace precise raceway, spindle, robot pivot, or bearing geometry authoring.

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

## First Lookdev Gate

Before authoring the full sequence, produce one 1920x1080 five-second render matching `production/v5/source-frames/s01-entry-clean.png`:

- central aisle and vanishing point match;
- robot, fence, grinder, AGV and recessed screen have correct scale and clearance;
- daylight and materials are within the approved palette;
- no incorrect process action, clutter, floating UI, rail conflict, or baked text;
- no visible geometry or animation defect in the first and final frames.

Only after this proof passes should the full camera and project checkpoints be authored.
