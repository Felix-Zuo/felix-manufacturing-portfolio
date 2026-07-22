"""Render deterministic review frames from an already-built proof scene."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=32)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def main() -> None:
    args = _args()
    frames = tuple(int(value.strip()) for value in args.frames.split(",") if value.strip())
    if not frames:
        raise ValueError("At least one review frame is required")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.use_file_extension = True
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = args.samples

    for index, frame in enumerate(frames, 1):
        scene.frame_set(frame)
        scene.render.filepath = str(output / f"review-{index:02d}-frame-{frame:03d}.png")
        bpy.ops.render.render(write_still=True)

    manifest = {
        "scene": bpy.data.filepath,
        "frames": frames,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "samples": args.samples,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("SUM_PROOF_KEYFRAMES=" + json.dumps(manifest))


if __name__ == "__main__":
    main()
