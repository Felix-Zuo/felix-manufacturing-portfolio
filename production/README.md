# Offline Cinematic Pipeline

The v6 home-page journey is a 38.000-second, 24 fps, 912-frame continuous FPV
industrial portfolio film. Blender owns the scene and camera; the web experience
only scrubs the rendered video and presents accessible HTML overlays. The locked
director's contract is in [`FPV_DIRECTORS_CUT.md`](./FPV_DIRECTORS_CUT.md).

## Locked Contract

- Frame range: `F001-F912`, with no cuts or editorial retiming.
- Focus frames: `[91, 169, 301, 433, 553, 673, 793, 877]`.
- Desktop master: 1920 x 1080, 24 fps, 912 frames.
- Mobile master: 1080 x 1920, 24 fps, 912 frames, rendered as a dedicated composition.
- Web encodes: H.264, `yuv420p`, BT.709-tagged, fixed GOP 12, `faststart`, no audio.

Every wrapper accepts `-Duration`; its compatible default is `38.0`. The existing
commands therefore remain valid, while the explicit production form is:

```powershell
.\production\render_storyboard.ps1 -Duration 38.0
.\production\render_storyboard.ps1 -Mobile -Duration 38.0
```

## Playblast-First Pipeline

1. Render and review all eight desktop and mobile storyboard focus frames.
2. Render both complete playblasts and review the continuous 912-frame move.
3. Record a new v6 motion approval. The earlier 28-second approval does not clear
   this retimed director's cut.
4. Only after that approval, render both final masters and required finishing passes.
5. Encode the silent web assets and verify duration, frame rate, color tags, GOP,
   frame count, poster, and seeking behavior.

Render the low-resolution continuous previews before any final render:

```powershell
.\production\render_playblast.ps1 -Duration 38.0
.\production\render_playblast.ps1 -Mobile -Duration 38.0
```

For constrained local hardware, the mobile preview can render every second source
frame while preserving the 24 fps animation clock. Publish the resulting 12 fps
source through motion-compensated interpolation; the publisher pads the terminal
hold and rejects anything other than exactly 912 frames / 38.000 seconds:

```powershell
.\production\render_playblast.ps1 -Mobile -Samples 3 -RenderStep 2 -Duration 38.0
.\production\publish_playblast.ps1 -Mode mobile -RenderStep 2 -Duration 38.0
```

Use `publish_playblast.ps1 -RenderStep 1` for a full-rate desktop playblast. The
half-rate path is a review/web fallback, not a replacement for the 1080p final
master gate below.

After the playblast gate passes, render the desktop and mobile masters:

```powershell
.\production\render_final.ps1 -Mode desktop -Samples 64 -Duration 38.0
.\production\render_final.ps1 -Mode mobile -Samples 64 -Duration 38.0
```

The final handoff is not complete with Beauty PNGs alone. Both aspect ratios must
have frame-aligned OpenEXR, Beauty, Clean Plate, and Screen Matte deliverables as
specified in the director's contract. Generated scenes and frame sequences remain
build artifacts; only approved web media belongs in `public/media/`.

Encode the web-ready assets after final-master approval:

```powershell
.\production\encode_media.ps1 -Mode desktop -Duration 38.0
.\production\encode_media.ps1 -Mode mobile -Duration 38.0
```

The encoder requires a complete 912-frame sequence at the default duration, limits
the encode to that exact frame count, uses the first focus frame for the poster,
and intentionally strips audio. A separately delivered standalone film may carry
approved sound; the scroll-scrub web videos must remain silent.
