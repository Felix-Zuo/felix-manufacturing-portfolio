"""Fail-fast geometric validation for the 38-second FPV camera master."""

from __future__ import annotations

import json
import math

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


FOCUS = (
    (433, "SUM_FPV_EvidenceBay_01_DisplaySurface"),
    (553, "SUM_FPV_EvidenceBay_02_DisplaySurface"),
    (673, "SUM_FPV_EvidenceBay_03_DisplaySurface"),
    (793, "SUM_FPV_EvidenceBay_04_DisplaySurface"),
)
TERMINAL_SETTLE_FRAME = 895


def _camera_position(scene: bpy.types.Scene, camera: bpy.types.Object, frame: int) -> Vector:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return camera.matrix_world.translation.copy()


def _screen_bounds(scene: bpy.types.Scene, camera: bpy.types.Object, obj: bpy.types.Object) -> list[tuple[float, float]]:
    return [
        tuple(world_to_camera_view(scene, camera, obj.matrix_world @ vertex.co)[:2])
        for vertex in obj.data.vertices
    ]


def main() -> None:
    scene = bpy.context.scene
    camera = scene.camera
    errors: list[str] = []
    if camera is None or camera.name != "CIN_Camera":
        raise RuntimeError("CIN_Camera is not the active scene camera")
    if (scene.frame_start, scene.frame_end, scene.render.fps) != (1, 912, 24):
        errors.append(
            f"expected frames 1-912 at 24 fps, got {scene.frame_start}-{scene.frame_end} at {scene.render.fps}"
        )

    positions = [_camera_position(scene, camera, frame) for frame in range(1, 913)]
    reversals = [
        frame
        for frame, (current, following) in enumerate(zip(positions, positions[1:]), start=1)
        if following.z > current.z + 1.0e-5
    ]
    if reversals:
        errors.append(f"camera reverses along the factory rail near frames {reversals[:8]}")

    terminal_drift = max(
        (position - positions[TERMINAL_SETTLE_FRAME - 1]).length
        for position in positions[TERMINAL_SETTLE_FRAME - 1 :]
    )
    if terminal_drift > 1.0e-4:
        errors.append(f"terminal hold drifts by {terminal_drift:.6f} m")

    focus_report = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for frame, name in FOCUS:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            errors.append(f"missing focus display {name}")
            continue
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        camera_position = camera.matrix_world.translation.copy()
        target = obj.matrix_world.translation.copy()
        ray = target - camera_position
        distance = ray.length
        hit, _location, _normal, _index, hit_obj, _matrix = scene.ray_cast(
            depsgraph, camera_position, ray.normalized(), distance=distance + 0.02
        )
        if not hit or hit_obj is None or hit_obj.name != name:
            blocker = hit_obj.name if hit_obj is not None else "none"
            errors.append(f"frame {frame} center ray reaches {blocker}, expected {name}")

        bounds = _screen_bounds(scene, camera, obj)
        xs = [value[0] for value in bounds]
        ys = [value[1] for value in bounds]
        if min(xs) < -0.08 or max(xs) > 1.08 or min(ys) < -0.08 or max(ys) > 1.08:
            errors.append(f"frame {frame} active screen exceeds the composition guard")
        coverage = max(0.0, min(1.0, max(xs)) - max(0.0, min(xs))) * max(
            0.0, min(1.0, max(ys)) - max(0.0, min(ys))
        )
        if not 0.28 <= coverage <= 0.82:
            errors.append(f"frame {frame} screen coverage {coverage:.3f} is outside 0.28-0.82")
        focus_report.append(
            {
                "frame": frame,
                "screen": name,
                "coverage": round(coverage, 4),
                "lens_mm": round(float(camera.data.lens), 2),
                "distance_m": round(distance, 3),
            }
        )

    report = {
        "ok": not errors,
        "frame_range": [scene.frame_start, scene.frame_end],
        "fps": scene.render.fps,
        "rail_reversal_count": len(reversals),
        "terminal_drift_m": round(terminal_drift, 7),
        "focus": focus_report,
        "errors": errors,
    }
    print("FPV_CAMERA_VALIDATION=" + json.dumps(report, ensure_ascii=True, separators=(",", ":")))
    if errors:
        raise RuntimeError("FPV camera validation failed")


if __name__ == "__main__":
    main()
