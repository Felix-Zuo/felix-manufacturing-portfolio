"""Validate AGV staging and camera motion in a built SUM Blender scene.

Run after opening a generated blend file::

    blender scene.blend --background --python validate_motion.py -- \
        --preview-dir production/renders/motion-validation
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


DISTANCE_MIN_METERS = 2.5
DISTANCE_MAX_METERS = 5.25
AGV_NAME = "SUM_MatureFactory_AGV07"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-dir", type=Path)
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(values)


def _descendants(root: bpy.types.Object) -> list[bpy.types.Object]:
    descendants: list[bpy.types.Object] = []
    pending = list(root.children)
    while pending:
        obj = pending.pop()
        descendants.append(obj)
        pending.extend(obj.children)
    return descendants


def _assembly_corners(root: bpy.types.Object) -> list[Vector]:
    corners: list[Vector] = []
    for obj in (root, *_descendants(root)):
        if obj.type not in {"MESH", "CURVE", "FONT"}:
            continue
        corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not corners:
        raise RuntimeError(f"{root.name} has no renderable assembly bounds")
    return corners


def _bounds_center(corners: list[Vector]) -> Vector:
    minimum = Vector(tuple(min(point[axis] for point in corners) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in corners) for axis in range(3)))
    return (minimum + maximum) * 0.5


def _is_visible(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    corners: list[Vector],
) -> bool:
    projected = [world_to_camera_view(scene, camera, point) for point in corners]
    in_front = [point for point in projected if point.z > 0.0]
    if not in_front:
        return False
    min_x = min(point.x for point in in_front)
    max_x = max(point.x for point in in_front)
    min_y = min(point.y for point in in_front)
    max_y = max(point.y for point in in_front)
    return max_x >= 0.0 and min_x <= 1.0 and max_y >= 0.0 and min_y <= 1.0


def _has_unoccluded_surface_sample(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    objects: list[bpy.types.Object],
) -> bool:
    """Reject projected-only fragments hidden behind factory geometry."""

    depsgraph = bpy.context.evaluated_depsgraph_get()
    assembly_names = {obj.name for obj in objects}
    origin = camera.matrix_world.translation.copy()
    for obj in objects:
        if obj.type not in {"MESH", "CURVE", "FONT"}:
            continue
        samples = [obj.matrix_world.translation.copy()]
        samples.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
        for sample in samples:
            projected = world_to_camera_view(scene, camera, sample)
            if projected.z <= 0.0 or not (0.0 <= projected.x <= 1.0 and 0.0 <= projected.y <= 1.0):
                continue
            direction = sample - origin
            distance = direction.length
            if distance <= 1.0e-4:
                continue
            hit, _location, _normal, _index, hit_object, _matrix = scene.ray_cast(
                depsgraph,
                origin,
                direction.normalized(),
                distance=max(0.0, distance - 0.002),
            )
            if not hit or hit_object is None or hit_object.name in assembly_names:
                return True
    return False


def _visibility_runs(frames: list[int]) -> list[list[int]]:
    if not frames:
        return []
    runs = [[frames[0]]]
    for frame in frames[1:]:
        if frame == runs[-1][-1] + 1:
            runs[-1].append(frame)
        else:
            runs.append([frame])
    return runs


def _quaternion_step_vector(start: Any, end: Any) -> Vector:
    aligned = end.copy()
    if start.dot(aligned) < 0.0:
        aligned.negate()
    delta = start.rotation_difference(aligned)
    if delta.w < 0.0:
        delta.negate()
    angle = min(math.pi, max(0.0, float(delta.angle)))
    if angle <= 1.0e-10:
        return Vector((0.0, 0.0, 0.0))
    return delta.axis.normalized() * angle


def _validate_agv(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    agv: bpy.types.Object,
) -> dict[str, Any]:
    opening_end = int(agv.get("sum_animation_opening_end_frame", 0))
    escort_end = int(agv.get("sum_animation_escort_end_frame", 0))
    if not 1 < opening_end < escort_end <= scene.frame_end:
        raise RuntimeError("AGV route metadata is missing or invalid")

    descendants = _descendants(agv)
    independently_animated = [
        obj.name
        for obj in descendants
        if obj.animation_data is not None and obj.animation_data.action is not None
    ]
    if independently_animated:
        raise RuntimeError(
            "AGV children must inherit the assembly-root route: "
            + ", ".join(independently_animated)
        )

    renderable = [
        obj for obj in descendants if obj.type in {"MESH", "CURVE", "FONT"}
    ]
    body_objects = [
        obj
        for obj in renderable
        if any(
            token in obj.name
            for token in (
                "LowerChassis",
                "UpperDeck",
                "PayloadCassette",
                "CompliantBumperBand",
            )
        )
    ]
    if len(body_objects) < 3:
        raise RuntimeError("AGV validation cannot identify all principal body objects")

    distances: list[float] = []
    forward_depths: list[float] = []
    invisible_frames: list[int] = []
    child_only_frames: list[int] = []
    visible_frames: list[int] = []
    opening_bounds: list[tuple[float, float, float, float]] = []
    aisle_x: list[float] = []
    aisle_y: list[float] = []
    for frame in range(1, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        corners = _assembly_corners(agv)
        center = _bounds_center(corners)
        assembly_visible = _is_visible(scene, camera, corners)
        body_visible = any(
            _is_visible(
                scene,
                camera,
                [obj.matrix_world @ Vector(corner) for corner in obj.bound_box],
            )
            for obj in body_objects
        )
        if assembly_visible and not body_visible:
            assembly_visible = _has_unoccluded_surface_sample(
                scene,
                camera,
                [agv, *renderable],
            )
        if assembly_visible:
            visible_frames.append(frame)
            if not body_visible:
                child_only_frames.append(frame)
        if frame <= escort_end:
            camera_space = camera.matrix_world.inverted() @ center
            distances.append((center - camera.matrix_world.translation).length)
            forward_depths.append(-float(camera_space.z))
        if frame <= opening_end and not assembly_visible:
            invisible_frames.append(frame)
        if frame <= opening_end:
            projected = [
                world_to_camera_view(scene, camera, point)
                for point in corners
            ]
            in_front = [point for point in projected if point.z > 0.0]
            if in_front:
                opening_bounds.append(
                    (
                        min(point.x for point in in_front),
                        max(point.x for point in in_front),
                        min(point.y for point in in_front),
                        max(point.y for point in in_front),
                    )
                )
        aisle_x.append(float(agv.location.x))
        aisle_y.append(float(agv.location.y))

    runs = _visibility_runs(visible_frames)
    failures = []
    if min(distances) < DISTANCE_MIN_METERS - 1.0e-4:
        failures.append(f"minimum distance {min(distances):.3f}m")
    if max(distances) > DISTANCE_MAX_METERS + 1.0e-4:
        failures.append(f"maximum distance {max(distances):.3f}m")
    if min(forward_depths) <= 0.0:
        failures.append(f"minimum forward depth {min(forward_depths):.3f}m")
    if invisible_frames:
        failures.append(f"not visible at frames {invisible_frames[:12]}")
    composition_bounds = {
        "min_x": min(value[0] for value in opening_bounds),
        "max_x": max(value[1] for value in opening_bounds),
        "min_y": min(value[2] for value in opening_bounds),
        "max_y": max(value[3] for value in opening_bounds),
    }
    if (
        composition_bounds["min_x"] < -0.05
        or composition_bounds["max_x"] > 1.05
        or composition_bounds["min_y"] < -0.05
        or composition_bounds["max_y"] > 1.05
    ):
        failures.append(
            "opening composition leaves the frame: "
            + ", ".join(
                f"{name}={value:.3f}"
                for name, value in composition_bounds.items()
            )
        )
    if child_only_frames:
        failures.append(
            "child-only visibility at frames "
            f"{child_only_frames[:12]} with visibility runs "
            f"{[(run[0], run[-1]) for run in runs]}"
        )
    if max(abs(value) for value in aisle_x) > 0.73:
        failures.append(f"aisle lateral excursion {max(abs(value) for value in aisle_x):.3f}m")
    if any(following <= current for current, following in zip(aisle_y, aisle_y[1:])):
        failures.append("center-aisle travel reverses or stalls")
    if failures:
        raise RuntimeError("AGV opening validation failed: " + "; ".join(failures))

    short_reappearances = [run for run in runs[1:] if len(run) < 6]
    if short_reappearances:
        raise RuntimeError(
            "AGV has short frustum reappearances: "
            + ", ".join(f"{run[0]}-{run[-1]}" for run in short_reappearances)
        )

    return {
        "opening_frames": [1, opening_end],
        "escort_frames": [1, escort_end],
        "assembly_descendants": len(descendants),
        "independently_animated_children": 0,
        "distance_m": {
            "minimum": round(min(distances), 4),
            "maximum": round(max(distances), 4),
        },
        "forward_depth_m": {
            "minimum": round(min(forward_depths), 4),
            "maximum": round(max(forward_depths), 4),
        },
        "opening_composition_bounds": {
            name: round(value, 4)
            for name, value in composition_bounds.items()
        },
        "visible_frame_ratio": round(len(visible_frames) / scene.frame_end, 4),
        "child_only_visible_frames": 0,
        "visibility_runs": [[run[0], run[-1]] for run in runs],
        "max_abs_aisle_x_m": round(max(abs(value) for value in aisle_x), 4),
        "final_aisle_y_m": round(aisle_y[-1], 4),
        "travel_monotone": True,
    }


def _validate_camera(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
) -> dict[str, Any]:
    max_step = float(camera.get("cin_max_angular_step_degrees", 2.0))
    max_acceleration = float(camera.get("cin_max_angular_acceleration_degrees", 0.55))
    quaternions = []
    positions = []
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        quaternions.append(camera.matrix_world.to_quaternion().normalized())
        positions.append(camera.matrix_world.translation.copy())

    step_vectors = [
        _quaternion_step_vector(start, end)
        for start, end in zip(quaternions, quaternions[1:])
    ]
    step_degrees = [math.degrees(value.length) for value in step_vectors]
    acceleration_degrees = [
        math.degrees((following - current).length)
        for current, following in zip(step_vectors, step_vectors[1:])
    ]
    observed_step = max(step_degrees, default=0.0)
    observed_acceleration = max(acceleration_degrees, default=0.0)
    if observed_step > max_step + 0.02:
        raise RuntimeError(
            f"Camera angular jump {observed_step:.3f} exceeds {max_step:.3f} deg/frame"
        )
    if observed_acceleration > max_acceleration + 0.03:
        raise RuntimeError(
            "Camera angular acceleration jump "
            f"{observed_acceleration:.3f} exceeds {max_acceleration:.3f} deg/frame2"
        )

    hold_frame = int(scene.get("cin_terminal_settle_frame", scene.frame_end))
    hold_position = positions[hold_frame - scene.frame_start]
    hold_quaternion = quaternions[hold_frame - scene.frame_start]
    position_drift = max(
        (value - hold_position).length
        for value in positions[hold_frame - scene.frame_start :]
    )
    orientation_drift = max(
        math.degrees(_quaternion_step_vector(hold_quaternion, value).length)
        for value in quaternions[hold_frame - scene.frame_start :]
    )
    if position_drift > 1.0e-5 or orientation_drift > 1.0e-4:
        raise RuntimeError(
            "Terminal camera hold drifted: "
            f"position={position_drift:.6f}m orientation={orientation_drift:.6f}deg"
        )

    return {
        "frames": [scene.frame_start, scene.frame_end],
        "max_angular_step_degrees_per_frame": round(observed_step, 4),
        "max_angular_acceleration_degrees_per_frame2": round(
            observed_acceleration, 4
        ),
        "limits": {
            "step": max_step,
            "acceleration": max_acceleration,
        },
        "terminal_hold_frame": hold_frame,
        "terminal_position_drift_m": round(position_drift, 8),
        "terminal_orientation_drift_degrees": round(orientation_drift, 8),
    }


def _render_previews(
    scene: bpy.types.Scene,
    agv: bpy.types.Object,
    output: Path,
) -> list[str]:
    if not output.is_absolute():
        output = Path(__file__).resolve().parents[2] / output
    output.mkdir(parents=True, exist_ok=True)
    scene.render.resolution_x = 320
    scene.render.resolution_y = 180
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 1
    frames = sorted(
        {
            1,
            int(agv["sum_animation_opening_end_frame"]) // 2,
            int(agv["sum_animation_opening_end_frame"]),
            int(agv["sum_animation_escort_end_frame"]),
        }
    )
    rendered = []
    for frame in frames:
        scene.frame_set(frame)
        path = output / f"motion-{frame:04d}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path))
    return rendered


def main() -> None:
    args = _args()
    scene = bpy.context.scene
    camera = scene.camera
    agv = bpy.data.objects.get(AGV_NAME)
    if camera is None or camera.type != "CAMERA":
        raise RuntimeError("Built scene has no active camera")
    if agv is None:
        raise RuntimeError(f"Built scene has no {AGV_NAME} assembly root")

    original_frame = scene.frame_current
    try:
        report = {
            "agv": _validate_agv(scene, camera, agv),
            "camera": _validate_camera(scene, camera),
        }
        if args.preview_dir is not None:
            report["preview_frames"] = _render_previews(scene, agv, args.preview_dir)
    finally:
        scene.frame_set(original_frame)
    print("MOTION_VALIDATION=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
