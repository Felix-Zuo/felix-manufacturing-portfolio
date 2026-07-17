# Control-room loop

This isolated pipeline turns `public/media/control-room-base.jpg` into a true
five-second idle loop. It does not load or modify the Blender journey scene.

Contract:

- 24 fps, 120 encoded frames, exactly 5.000 seconds.
- Generated frame 121 is pixel-identical to generated frame 1.
- The camera and source image remain fixed.
- Motion is confined to screen refresh, indicator lights, distant conveyor
  markers, and one distant fan.
- Outputs are silent VP9 WebM, H.264 MP4 fallback, and WebP poster.

Run the low-resolution proof first:

```powershell
.\production\render_control_room_loop.ps1 -Mode Proof
```

After the proof report passes, create the 1280 x 720 fallback and the 1920 x
1080 public master:

```powershell
.\production\render_control_room_loop.ps1 -Mode Fallback
.\production\render_control_room_loop.ps1 -Mode Public
```

Proof outputs and validation reports live under `production/renders/`, which is
intentionally ignored. Public mode writes only these media assets:

- `public/media/control-room-loop.webm`
- `public/media/control-room-loop.mp4`
- `public/media/control-room-loop-poster.webp`
- `public/media/control-room-loop-720p.webm`
- `public/media/control-room-loop-720p.mp4`
- `public/media/control-room-loop-720p-poster.webp`
