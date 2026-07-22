"""Render a lightweight MP4 for timing and compression review of proof scenes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=854)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--frame-start", type=int)
    parser.add_argument("--frame-end", type=int)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def main() -> None:
    args = _args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    if args.frame_start is not None:
        scene.frame_start = args.frame_start
    if args.frame_end is not None:
        scene.frame_end = args.frame_end
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.filepath = str(output)
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = args.samples
    bpy.ops.render.render(animation=True)
    report = {
        "scene": bpy.data.filepath,
        "output": str(output),
        "frames": [scene.frame_start, scene.frame_end],
        "fps": scene.render.fps,
        "resolution": [args.width, args.height],
        "samples": args.samples,
    }
    print("SUM_PROOF_PREVIEW=" + json.dumps(report))


if __name__ == "__main__":
    main()
