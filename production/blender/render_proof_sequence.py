"""Render a deterministic PNG sequence for proof-loop review and encoding."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--width", type=int, default=854)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--frame-start", type=int, required=True)
    parser.add_argument("--frame-end", type=int, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def main() -> None:
    args = _args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    scene.frame_start = args.frame_start
    scene.frame_end = args.frame_end
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.filepath = str(output_dir / "frame-")
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = args.samples

    bpy.ops.render.render(animation=True)
    report = {
        "scene": bpy.data.filepath,
        "output_dir": str(output_dir),
        "frames": [scene.frame_start, scene.frame_end],
        "fps": scene.render.fps,
        "resolution": [args.width, args.height],
        "samples": args.samples,
    }
    print("SUM_PROOF_SEQUENCE=" + json.dumps(report))


if __name__ == "__main__":
    main()
