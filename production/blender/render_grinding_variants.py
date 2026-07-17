"""Render quick camera candidates for the grinding hero frame.

Run after opening the built master blend. The script temporarily removes the
camera path constraints, renders four physically continuous viewpoints, and
does not save those exploratory camera changes back into the blend.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def _aim(camera: bpy.types.Object, target: Vector) -> None:
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = (target - camera.location).to_track_quat("-Z", "Y")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(argv)

    scene = bpy.context.scene
    scene.frame_set(301)
    camera = scene.camera
    if camera is None:
        raise RuntimeError("The master scene has no active camera")
    for constraint in camera.constraints:
        constraint.mute = True
    # Detach baked cinematography while auditioning fixed viewpoints.  Merely
    # muting Follow Path is insufficient because the per-frame quaternion
    # action would otherwise overwrite `_aim()` during render evaluation.
    if camera.animation_data is not None:
        camera.animation_data.action = None
    if camera.data.animation_data is not None:
        camera.data.animation_data.action = None

    target_obj = bpy.data.objects.get("SUM_ANCHOR_GrindingContact")
    target = (
        target_obj.matrix_world.translation.copy()
        if target_obj is not None
        else Vector((5.52, 1.82, -25.96))
    )
    variants = (
        ("a-aisle-tele", (2.80, 2.15, -23.20), 72.0),
        ("b-front-oblique", (3.20, 2.10, -23.80), 70.0),
        ("c-raised-oblique", (2.80, 2.60, -24.20), 75.0),
        ("d-close-oblique", (3.40, 2.20, -24.40), 80.0),
        ("e-wheel-side", (2.50, 2.35, -26.50), 68.0),
        ("f-wheel-raised", (2.10, 2.75, -26.80), 72.0),
    )
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene.render.resolution_x = 640
    scene.render.resolution_y = 360
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if hasattr(scene, "cycles"):
        scene.cycles.samples = 6
        scene.cycles.use_denoising = True

    for slug, position, lens in variants:
        camera.location = Vector(position)
        camera.data.lens = lens
        _aim(camera, target)
        scene.render.filepath = str(output_dir / f"{slug}.png")
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {slug}: camera={position}, lens={lens}, target={tuple(target)}")


if __name__ == "__main__":
    main()
