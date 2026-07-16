"""Render lightweight continuity frames from an already-built FPV scene."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=480)
    parser.add_argument("--height", type=int, default=270)
    parser.add_argument("--samples", type=int, default=2)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(argv)


def main() -> None:
    args = _args()
    frames = [int(value.strip()) for value in args.frames.split(",") if value.strip()]
    if not frames:
        raise ValueError("--frames must contain at least one frame")

    scene = bpy.context.scene
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 45
    scene.render.use_motion_blur = False
    if hasattr(scene, "eevee"):
        if hasattr(scene.eevee, "taa_samples"):
            scene.eevee.taa_samples = args.samples
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = args.samples

    for frame in frames:
        if not scene.frame_start <= frame <= scene.frame_end:
            raise ValueError(f"frame {frame} is outside the scene range")
        scene.frame_set(frame)
        scene.render.filepath = str(output / f"frame-{frame:04d}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
