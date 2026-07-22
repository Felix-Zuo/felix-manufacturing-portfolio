"""Validate the fixed-camera KR210 pick-place proof inside Blender."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROBOT_ROOT = "SUM_ASSET_KUKA_KR210_L150"
TCP_NAME = "SUM_KUKA_KR210_Tool0"
TRANSFER_RING = "SUM_RobotCell_InfeedBearingRing_02"
NEXT_RING = "SUM_RobotCell_InfeedBearingRing_03"
PREVIOUS_RING = "SUM_RobotCell_HandoffNest_BearingRing"
UPSTREAM_RING = "SUM_RobotCell_InfeedBearingRing_04"
NEW_RING = "SUM_RobotCell_InfeedBearingRing_05"
BELT_SURFACE = "SUM_RobotCell_InfeedBeltSurface"
PRECISION_NEST = "SUM_RobotCell_HandoffPrecisionNest"
OUTFEED_BELT = "SUM_RobotCell_HandoffOutfeedBelt"
ALLOWED_SUPPORTS = {PRECISION_NEST, OUTFEED_BELT}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--frame-step", type=int, default=1)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _required(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Missing required object: {name}")
    return obj


def _is_descendant(obj: bpy.types.Object, ancestor: bpy.types.Object) -> bool:
    cursor = obj.parent
    while cursor is not None:
        if cursor is ancestor:
            return True
        cursor = cursor.parent
    return False


def _world_mesh(obj: bpy.types.Object, depsgraph: bpy.types.Depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    matrix = evaluated.matrix_world
    vertices = [matrix @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return vertices, polygons


def _bvh(obj: bpy.types.Object, depsgraph: bpy.types.Depsgraph) -> BVHTree:
    vertices, polygons = _world_mesh(obj, depsgraph)
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False, epsilon=0.0002)


def _bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (
        Vector(tuple(min(point[axis] for point in points) for axis in range(3))),
        Vector(tuple(max(point[axis] for point in points) for axis in range(3))),
    )


def _bounds_overlap(
    a: tuple[Vector, Vector], b: tuple[Vector, Vector], margin: float = 0.0
) -> bool:
    return all(
        a[0][axis] <= b[1][axis] + margin
        and a[1][axis] + margin >= b[0][axis]
        for axis in range(3)
    )


def _matrix_delta(a, b) -> float:
    return max(abs(float(x) - float(y)) for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b))


def _rotation_delta_degrees(a, b) -> float:
    delta = a.to_quaternion().rotation_difference(b.to_quaternion())
    _, angle = delta.to_axis_angle()
    if angle > math.pi:
        angle = math.tau - angle
    return math.degrees(abs(angle))


def _scale_deviation(matrix) -> float:
    scale = matrix.to_scale()
    return max(abs(float(value) - 1.0) for value in scale)


def _radial_extents(
    obj: bpy.types.Object,
    center: Vector,
    axis: Vector,
    depsgraph: bpy.types.Depsgraph,
) -> tuple[float, float]:
    vertices, _ = _world_mesh(obj, depsgraph)
    radii = []
    for point in vertices:
        offset = point - center
        radial = offset - axis * offset.dot(axis)
        radii.append(radial.length)
    return min(radii), max(radii)


def _action_paths(obj: bpy.types.Object) -> set[str]:
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return set()
    return {curve.data_path for curve in action.fcurves}


def _pair_key(a: bpy.types.Object, b: bpy.types.Object) -> str:
    return f"{a.name} :: {b.name}"


def _main() -> dict[str, object]:
    args = _args()
    args.report = args.report.resolve()
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    robot_root = _required(ROBOT_ROOT)
    tcp = _required(TCP_NAME)
    transfer_ring = _required(TRANSFER_RING)
    next_ring = _required(NEXT_RING)
    previous_ring = _required(PREVIOUS_RING)
    upstream_ring = _required(UPSTREAM_RING)
    new_ring = _required(NEW_RING)
    belt = _required(BELT_SURFACE)
    nest = _required(PRECISION_NEST)
    grasp_begin_frame = int(scene.get("proof_grasp_begin_frame", 31))
    grasp_frame = int(scene.get("proof_grasp_frame", 42))
    place_frame = int(scene.get("proof_place_frame", scene.get("proof_release_frame", 107) - 9))
    release_frame = int(scene.get("proof_release_frame", 107))

    robot_meshes = [
        obj
        for obj in scene.objects
        if obj.type == "MESH"
        and not obj.hide_render
        and _is_descendant(obj, robot_root)
        and obj.name not in {TRANSFER_RING, NEXT_RING, PREVIOUS_RING}
    ]
    fixed_meshes = [
        obj
        for obj in scene.objects
        if obj.type == "MESH"
        and not obj.hide_render
        and obj.name.startswith(("SUM_RobotCell_Infeed", "SUM_RobotCell_Handoff"))
        and obj.name not in {TRANSFER_RING, NEXT_RING, PREVIOUS_RING}
    ]

    sampled_frames = sorted(
        set(range(scene.frame_start, scene.frame_end + 1, max(1, args.frame_step)))
        | {
            scene.frame_start,
            scene.frame_end,
            grasp_frame - 1,
            grasp_frame,
            grasp_frame + 1,
            release_frame - 1,
            release_frame,
            release_frame + 1,
        }
    )
    collisions: list[dict[str, object]] = []
    support_contacts: list[dict[str, object]] = []
    tcp_positions: list[tuple[int, Vector]] = []
    ring_positions: list[tuple[int, Vector]] = []
    ring_matrices: dict[int, object] = {}
    maximum_ring_scale_deviation = 0.0
    camera_reference = None
    camera_lens_reference = None
    camera_fstop_reference = None
    max_camera_delta = 0.0
    max_camera_lens_delta = 0.0
    max_camera_fstop_delta = 0.0

    for frame in sampled_frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        if camera_reference is None:
            camera_reference = scene.camera.matrix_world.copy()
            camera_lens_reference = float(scene.camera.data.lens)
            camera_fstop_reference = float(scene.camera.data.dof.aperture_fstop)
        max_camera_delta = max(
            max_camera_delta,
            _matrix_delta(camera_reference, scene.camera.matrix_world),
        )
        max_camera_lens_delta = max(
            max_camera_lens_delta,
            abs(float(scene.camera.data.lens) - camera_lens_reference),
        )
        max_camera_fstop_delta = max(
            max_camera_fstop_delta,
            abs(float(scene.camera.data.dof.aperture_fstop) - camera_fstop_reference),
        )
        tcp_positions.append((frame, tcp.matrix_world.translation.copy()))
        ring_positions.append((frame, transfer_ring.matrix_world.translation.copy()))
        ring_matrices[frame] = transfer_ring.matrix_world.copy()
        for ring in (transfer_ring, next_ring, previous_ring, upstream_ring, new_ring):
            maximum_ring_scale_deviation = max(
                maximum_ring_scale_deviation,
                _scale_deviation(ring.matrix_world),
            )

        static_cache = {
            obj.name: (_bounds(obj), _bvh(obj, depsgraph)) for obj in fixed_meshes
        }
        for moving in robot_meshes:
            moving_bounds = _bounds(moving)
            candidate_fixed = [
                fixed
                for fixed in fixed_meshes
                if _bounds_overlap(moving_bounds, static_cache[fixed.name][0], margin=0.001)
            ]
            if not candidate_fixed:
                continue
            moving_bvh = _bvh(moving, depsgraph)
            for fixed in candidate_fixed:
                overlaps = moving_bvh.overlap(static_cache[fixed.name][1])
                if overlaps:
                    collisions.append(
                        {
                            "frame": frame,
                            "pair": _pair_key(moving, fixed),
                            "triangle_pairs": len(overlaps),
                        }
                    )

        if grasp_frame < frame <= release_frame:
            ring_bounds = _bounds(transfer_ring)
            ring_bvh = _bvh(transfer_ring, depsgraph)
            for fixed in fixed_meshes:
                if not _bounds_overlap(ring_bounds, static_cache[fixed.name][0], margin=0.001):
                    continue
                overlaps = ring_bvh.overlap(static_cache[fixed.name][1])
                if overlaps:
                    item = {
                        "frame": frame,
                        "pair": _pair_key(transfer_ring, fixed),
                        "triangle_pairs": len(overlaps),
                    }
                    support_gap = ring_bounds[0].y - static_cache[fixed.name][0][1].y
                    if (
                        fixed.name in ALLOWED_SUPPORTS
                        and place_frame <= frame <= release_frame
                        and -0.0005 <= support_gap <= 0.001
                    ):
                        item["support_gap_m"] = support_gap
                        support_contacts.append(item)
                    else:
                        collisions.append(item)

    scene.frame_set(grasp_frame - 1)
    belt_top = _bounds(belt)[1].y
    pickup_bottom = _bounds(transfer_ring)[0].y
    scene.frame_set(release_frame)
    nest_top = _bounds(nest)[1].y
    release_bottom = _bounds(transfer_ring)[0].y
    scene.frame_set(release_frame + 1)
    post_release_bottom = _bounds(transfer_ring)[0].y

    scene.frame_set(grasp_frame)
    ring_center = transfer_ring.matrix_world.translation.copy()
    ring_axis = (
        transfer_ring.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
    ).normalized()
    inner_radius, _ = _radial_extents(
        transfer_ring, ring_center, ring_axis, depsgraph
    )
    jaw_contact_gaps = []
    jaw_roots = []
    for index in range(1, 4):
        jaw_roots.append(_required(f"SUM_PROOF_InternalGripper_JawRoot_{index:02d}"))
        pin = _required(f"SUM_PROOF_InternalGripper_Pin_{index:02d}")
        _, pin_outer_radius = _radial_extents(pin, ring_center, ring_axis, depsgraph)
        jaw_contact_gaps.append(inner_radius - pin_outer_radius)

    scene.frame_set(grasp_begin_frame)
    jaw_retracted_locations = [jaw.location.copy() for jaw in jaw_roots]
    scene.frame_set(grasp_frame)
    jaw_grasp_locations = [jaw.location.copy() for jaw in jaw_roots]
    jaw_grasp_travel = [
        (expanded - retracted).length
        for retracted, expanded in zip(jaw_retracted_locations, jaw_grasp_locations)
    ]
    scene.frame_set(place_frame)
    jaw_place_locations = [jaw.location.copy() for jaw in jaw_roots]
    scene.frame_set(release_frame)
    jaw_release_locations = [jaw.location.copy() for jaw in jaw_roots]
    jaw_release_travel = [
        (released - expanded).length
        for expanded, released in zip(jaw_place_locations, jaw_release_locations)
    ]
    hub_max_dimension = max(float(value) for value in _required("SUM_PROOF_InternalGripper_Hub").dimensions)

    grasp_position_jump = (
        ring_matrices[grasp_frame - 1].translation
        - ring_matrices[grasp_frame].translation
    ).length
    grasp_rotation_jump = _rotation_delta_degrees(
        ring_matrices[grasp_frame - 1], ring_matrices[grasp_frame]
    )
    release_position_jump = (
        ring_matrices[release_frame].translation
        - ring_matrices[release_frame + 1].translation
    ).length
    release_rotation_jump = _rotation_delta_degrees(
        ring_matrices[release_frame], ring_matrices[release_frame + 1]
    )

    scene.frame_set(1)
    first_camera = scene.camera.matrix_world.copy()
    first_camera_lens = float(scene.camera.data.lens)
    first_camera_fstop = float(scene.camera.data.dof.aperture_fstop)
    first_ring_matrix = transfer_ring.matrix_world.copy()
    first_nest_matrix = previous_ring.matrix_world.copy()
    first_conveyor = [
        _required("SUM_RobotCell_InfeedBearingRing_01").matrix_world.copy(),
        transfer_ring.matrix_world.copy(),
        next_ring.matrix_world.copy(),
        upstream_ring.matrix_world.copy(),
    ]
    scene.frame_set(scene.frame_end)
    last_camera = scene.camera.matrix_world.copy()
    last_camera_lens = float(scene.camera.data.lens)
    last_camera_fstop = float(scene.camera.data.dof.aperture_fstop)
    last_pick_matrix = next_ring.matrix_world.copy()
    last_nest_matrix = transfer_ring.matrix_world.copy()
    last_conveyor = [
        _required("SUM_RobotCell_InfeedBearingRing_01").matrix_world.copy(),
        next_ring.matrix_world.copy(),
        upstream_ring.matrix_world.copy(),
        new_ring.matrix_world.copy(),
    ]

    tcp_steps = [
        (
            frame_a,
            frame_b,
            (b - a).length / max(frame_b - frame_a, 1),
        )
        for (frame_a, a), (frame_b, b) in zip(tcp_positions, tcp_positions[1:])
    ]
    ring_steps = [
        (
            frame_a,
            frame_b,
            (b - a).length / max(frame_b - frame_a, 1),
        )
        for (frame_a, a), (frame_b, b) in zip(ring_positions, ring_positions[1:])
    ]
    max_tcp_step = max(tcp_steps, key=lambda item: item[2], default=(0, 0, 0.0))
    max_ring_step = max(ring_steps, key=lambda item: item[2], default=(0, 0, 0.0))
    maximum_support_penetration = max(
        (-float(item["support_gap_m"]) for item in support_contacts),
        default=0.0,
    )
    visibility_paths = sorted(
        path
        for obj in (transfer_ring, next_ring, previous_ring)
        for path in _action_paths(obj)
        if "hide_" in path
    )
    unique_collision_pairs = sorted({item["pair"] for item in collisions})
    scale_animation_paths = sorted(
        f"{obj.name}:{path}"
        for obj in (transfer_ring, next_ring, previous_ring, upstream_ring, new_ring)
        for path in _action_paths(obj)
        if path == "scale"
    )
    checks = {
        "camera_fixed": max_camera_delta <= 1.0e-7
        and _matrix_delta(first_camera, last_camera) <= 1.0e-7
        and max_camera_lens_delta <= 1.0e-7
        and max_camera_fstop_delta <= 1.0e-7
        and abs(first_camera_lens - last_camera_lens) <= 1.0e-7
        and abs(first_camera_fstop - last_camera_fstop) <= 1.0e-7
        and scene.camera.data.animation_data is None,
        "no_mesh_penetration": not collisions,
        "support_contact_within_tolerance": maximum_support_penetration <= 0.0005,
        "pickup_supported": abs(pickup_bottom - belt_top) <= 0.001,
        "destination_supported_before_release": abs(release_bottom - nest_top) <= 0.001,
        "destination_supported_after_release": abs(post_release_bottom - nest_top) <= 0.001,
        "three_jaw_contact": max(abs(gap) for gap in jaw_contact_gaps) <= 0.002,
        "jaw_motion_is_visually_readable": min(jaw_grasp_travel) >= 0.045
        and min(jaw_release_travel) >= 0.045,
        "jaw_timing_is_visually_readable": grasp_frame - grasp_begin_frame >= 10
        and release_frame - place_frame >= 10,
        "gripper_hub_preserves_bore_aperture": hub_max_dimension <= inner_radius,
        "rigid_workpiece_scale": maximum_ring_scale_deviation <= 1.0e-4
        and not scale_animation_paths,
        "grasp_boundary_continuous": grasp_position_jump <= 0.00025
        and grasp_rotation_jump <= 0.1,
        "release_boundary_continuous": release_position_jump <= 0.00025
        and release_rotation_jump <= 0.1,
        "pickup_visual_closure": (first_ring_matrix.translation - last_pick_matrix.translation).length <= 0.001,
        "destination_visual_closure": (first_nest_matrix.translation - last_nest_matrix.translation).length <= 0.001,
        "conveyor_visual_closure": max(
            (first.translation - last.translation).length
            for first, last in zip(first_conveyor, last_conveyor)
        ) <= 0.001,
        "no_visibility_swap": not visibility_paths,
        "tcp_step_continuous": max_tcp_step[2] <= 0.085,
        "workpiece_step_continuous": max_ring_step[2] <= 0.085,
    }
    report: dict[str, object] = {
        "status": "pass" if all(checks.values()) else "fail",
        "scene": bpy.data.filepath,
        "sampled_frames": sampled_frames,
        "checks": checks,
        "collision_count": len(collisions),
        "collision_pairs": unique_collision_pairs,
        "collision_examples": collisions[:50],
        "support_contact_count": len(support_contacts),
        "support_contact_examples": support_contacts[:50],
        "maximum_support_penetration_m": maximum_support_penetration,
        "pickup_support_gap_m": pickup_bottom - belt_top,
        "destination_support_gap_m": release_bottom - nest_top,
        "post_release_support_gap_m": post_release_bottom - nest_top,
        "inner_ring_radius_m": inner_radius,
        "jaw_contact_gaps_m": jaw_contact_gaps,
        "jaw_grasp_travel_m": jaw_grasp_travel,
        "jaw_release_travel_m": jaw_release_travel,
        "grasp_duration_frames": grasp_frame - grasp_begin_frame,
        "release_duration_frames": release_frame - place_frame,
        "gripper_hub_max_dimension_m": hub_max_dimension,
        "maximum_ring_scale_deviation": maximum_ring_scale_deviation,
        "camera_lens_mm": first_camera_lens,
        "camera_aperture_fstop": first_camera_fstop,
        "maximum_camera_lens_delta": max_camera_lens_delta,
        "maximum_camera_fstop_delta": max_camera_fstop_delta,
        "scale_animation_paths": scale_animation_paths,
        "grasp_position_jump_m": grasp_position_jump,
        "grasp_rotation_jump_deg": grasp_rotation_jump,
        "release_position_jump_m": release_position_jump,
        "release_rotation_jump_deg": release_rotation_jump,
        "max_camera_matrix_delta": max_camera_delta,
        "max_tcp_step_m_per_frame": max_tcp_step[2],
        "max_tcp_step_frames": [max_tcp_step[0], max_tcp_step[1]],
        "largest_tcp_steps": [
            {"frames": [start, end], "step_m": step}
            for start, end, step in sorted(
                tcp_steps, key=lambda item: item[2], reverse=True
            )[:12]
        ],
        "max_workpiece_step_m_per_frame": max_ring_step[2],
        "max_workpiece_step_frames": [max_ring_step[0], max_ring_step[1]],
        "visibility_animation_paths": visibility_paths,
        "robot_mesh_count": len(robot_meshes),
        "fixed_mesh_count": len(fixed_meshes),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SUM_ROBOT_VALIDATION=" + json.dumps(report))
    if report["status"] != "pass":
        raise RuntimeError("Robot proof failed validation; inspect the JSON report")
    return report


if __name__ == "__main__":
    _main()
