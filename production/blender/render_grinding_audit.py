"""Render repeatable grinding-contact camera candidates from a built scene."""

from __future__ import annotations

from pathlib import Path
import sys

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import cinematography  # noqa: E402


def main() -> None:
    scene = bpy.context.scene
    camera = bpy.data.objects["CIN_Camera"]
    look_at = bpy.data.objects["CIN_LookAt"]
    ring = bpy.data.objects["RING_HERO_01"]
    follow = camera.constraints.get("CIN_FollowPath")
    base_location = camera.location.copy()
    base_rotation = camera.rotation_quaternion.copy()
    camera_action = camera.animation_data.action if camera.animation_data else None
    look_at_action = look_at.animation_data.action if look_at.animation_data else None
    black_handoff = bpy.data.objects.get("CIN_BlackHandoff")
    if follow is not None:
        follow.mute = True
    if camera.animation_data:
        camera.animation_data.action = None
    if look_at.animation_data:
        look_at.animation_data.action = None
    if black_handoff is not None:
        black_handoff.hide_render = True

    scene.frame_set(430)
    bpy.context.view_layer.update()
    target = ring.matrix_world.translation.copy()
    look_at.location = target
    scene.render.resolution_x = 768
    scene.render.resolution_y = 432
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 16

    candidates = {
        "process-left": (Vector((-0.45, 0.72, 1.80)), 48.0),
        "process-left-high": (Vector((-0.20, 1.02, 1.70)), 52.0),
        "process-center": (Vector((0.00, 0.68, 1.95)), 54.0),
        "process-right": (Vector((0.65, 0.82, 1.70)), 52.0),
        "process-wide": (Vector((-0.85, 1.15, 2.15)), 44.0),
        "process-low": (Vector((-0.25, 0.34, 1.55)), 58.0),
    }
    camera.data.clip_start = 0.005
    camera.data.dof.use_dof = False
    output = ROOT / "production" / "renders" / "lookdev"
    output.mkdir(parents=True, exist_ok=True)
    for slug, (offset, lens) in candidates.items():
        camera.location = target + offset
        direction = target - camera.location
        hit, _location, _normal, _index, hit_object, _matrix = scene.ray_cast(
            bpy.context.evaluated_depsgraph_get(),
            camera.location,
            direction.normalized(),
            distance=max(0.0, direction.length - 0.045),
        )
        print(
            "Grinding audit visibility:",
            slug,
            "first hit",
            hit_object.name if hit and hit_object is not None else "clear",
        )
        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = cinematography._film_look_quaternion(
            camera.location, target
        )
        camera.data.lens = lens
        bpy.context.view_layer.update()
        scene.render.filepath = str(output / f"grinding-camera-{slug}-0430.png")
        bpy.ops.render.render(write_still=True)

    if follow is not None:
        camera.location = base_location
        camera.rotation_quaternion = base_rotation
        follow.mute = False
    if camera.animation_data:
        camera.animation_data.action = camera_action
    if look_at.animation_data:
        look_at.animation_data.action = look_at_action
    if black_handoff is not None:
        black_handoff.hide_render = False
    camera.data.clip_start = 0.02
    camera.data.dof.use_dof = False
    scene.render.use_motion_blur = False


if __name__ == "__main__":
    main()
