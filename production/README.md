# Offline Cinematic Pipeline

The home-page journey is authored and rendered in Blender 4.5 LTS. The web
experience only scrubs the resulting video and renders accessible HTML overlays.

## Stages

1. Build the parametric hard-surface scene.
2. Render the eight storyboard frames.
3. Run visual review and revise before a full render.
4. Render desktop and mobile playblasts and review continuous motion.
5. Render desktop and mobile frame sequences.
6. Encode final H.264 video assets into `public/media/`.
7. Switch the home page to the rendered-video component and verify playback.

Run the storyboard from PowerShell:

```powershell
.\production\render_storyboard.ps1
.\production\render_storyboard.ps1 -Mobile
```

After static approval, render low-resolution continuous previews:

```powershell
.\production\render_playblast.ps1
.\production\render_playblast.ps1 -Mobile
```

Full renders are intentionally separate:

```powershell
.\production\render_final.ps1 -Mode desktop -Samples 64
.\production\render_final.ps1 -Mode mobile -Samples 64
```

The final masters render at 1600 x 900 and 900 x 1600. Eevee uses the maximum
1024 MB shadow pool with a 0.75 shadow-resolution scale so the full camera route
fits the shadow atlas without missing pages.

Then encode the web-ready assets with a short keyframe interval for smooth
scroll seeking:

```powershell
.\production\encode_media.ps1 -Mode desktop
.\production\encode_media.ps1 -Mode mobile
```

Generated Blender scenes and render frames are build artifacts. Only the final
web-ready poster and videos belong in `public/media/`.

Review evidence is recorded in `production/reviews/`. Round 5 is the motion
approval that clears the final-render gate.
