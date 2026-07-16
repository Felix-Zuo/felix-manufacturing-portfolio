# Offline Cinematic Pipeline

The v8 home-page journey is a 38.000-second industrial portfolio film. Blender
owns the physical scene, process animation, lighting, and camera. The web layer
scrubs the rendered media and presents accessible HTML project overlays, magnetic
chapter stops, scene hotspots, and the final portfolio summary.

## Delivered Web Masters

- Timeline: `F001-F912`, 24 fps, 38.000 seconds.
- Desktop: 960 x 540 H.264, `yuv420p`, BT.709, fixed GOP 12, no audio.
- Mobile: 540 x 960 dedicated composition with the same timeline and stops.
- Posters: dedicated desktop and mobile WebP first frames.
- Current constrained render source: 456 Blender frames at 12 fps, published to
  exactly 912 frames with motion-compensated interpolation and an exact terminal
  trim. The final files are verified as 24 fps / 38.000 seconds.

The current web masters prioritize reliable playback and practical repository
size. For an archival master, render every frame at 1280 x 720 or higher with the
`render_final.ps1` commands below, then review the full sequence before replacing
the web assets.

## Industrial Logic

- The bearing outer ring enters the grinder with its axis horizontal.
- A guarded servo turner reorients it under camera occlusion after grinding.
- The ring travels flat, axis vertical, in a three-point tracked carrier on a
  continuous side-flex belt with a tangent curved transition. There are no exposed
  outfeed rollers.
- Inspection uses a vertical-axis air-bearing rotary table, three ceramic face
  supports, OD centering fingers, and an L-shaped internal-raceway stylus.
- A three-jaw internal-expanding collet transfers the flat ring to the outbound
  AGV nest.

These invariants are executable checks in `blender/validate_v8_factory.py`.

## Build And Review

Build the scene and render desktop or mobile focus frames:

```powershell
.\production\render_storyboard.ps1 -Duration 38.0
.\production\render_storyboard.ps1 -Mobile -Duration 38.0
```

Render a complete constrained preview and publish the exact web timeline:

```powershell
.\production\render_playblast.ps1 -Samples 8 -RenderStep 2 -Duration 38.0
.\production\publish_playblast.ps1 -Mode desktop -RenderStep 2 -Duration 38.0

.\production\render_playblast.ps1 -Mobile -Samples 8 -RenderStep 2 -Duration 38.0
.\production\publish_playblast.ps1 -Mode mobile -RenderStep 2 -Duration 38.0
```

For full-rate, higher-resolution masters:

```powershell
.\production\render_final.ps1 -Mode desktop -Samples 64 -Width 1280 -Height 720 -Duration 38.0
.\production\render_final.ps1 -Mode mobile -Samples 64 -Width 720 -Height 1280 -Duration 38.0
.\production\encode_media.ps1 -Mode desktop -Duration 38.0
.\production\encode_media.ps1 -Mode mobile -Duration 38.0
```

Long final renders can be resumed in frame chunks. Chunks write into the same
ignored frame directory, and the encoder refuses to publish until all 912 frames
exist.

## Validation

Validate the Blender scene in background mode:

```powershell
& '..\tools\blender-4.5.11-windows-x64\blender.exe' `
  --background production\scenes\felix-journey-blend.blend `
  --python production\blender\validate_v8_factory.py
```

With the web app running on port 3000, validate desktop wheel increments, magnetic
stops, finale handoff, mobile media selection, overflow, reduced motion, and
runtime errors:

```powershell
$base = "$HOME\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules"
$env:NODE_PATH = "$base;$base\.pnpm\playwright-core@1.61.1\node_modules"
& "$HOME\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" `
  production\qa\validate_journey.cjs
```

The physical finale is a split door opening into a non-emissive black threshold.
The HTML portfolio summary resolves only after that handoff.
