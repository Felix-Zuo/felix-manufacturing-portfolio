"""Validate the fixed-camera internal-raceway grinding proof inside Blender."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


WORKPIECE = "SUM_GrindingCell_OuterRing_Workpiece"
WHEEL = "SUM_GrindingCell_CBN_InternalGrindingWheel"
CONTACT = "SUM_ANCHOR_GrindingContact"
WORK_DRIVER = "SUM_PROOF_GRIND_WorkpieceSpinDriver"
WHEEL_DRIVER = "SUM_PROOF_GRIND_WheelSpinDriver"
ENCODED_END_FRAME = 96
VISIBLE_PARTICLE_SIZE_M = 0.00075
MAX_VISIBLE_PARTICLE_STEP_M = 0.04


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _required(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Missing required grinding proof object: {name}")
    return obj


def _matrix_delta(a: Matrix, b: Matrix) -> float:
    return max(
        abs(float(x) - float(y))
        for row_a, row_b in zip(a, b)
        for x, y in zip(row_a, row_b)
    )


def _axis(obj: bpy.types.Object) -> Vector:
    return (obj.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()


def _radial_distance(center: Vector, point: Vector, axis: Vector) -> float:
    offset = point - center
    offset -= axis * offset.dot(axis)
    return offset.length


def _particle_size(obj: bpy.types.Object) -> float:
    return max(abs(float(value)) for value in obj.dimensions)


def main() -> dict[str, object]:
    args = _args()
    args.report = args.report.resolve()
    scene = bpy.context.scene
    workpiece = _required(WORKPIECE)
    wheel = _required(WHEEL)
    contact = _required(CONTACT)
    work_driver = _required(WORK_DRIVER)
    wheel_driver = _required(WHEEL_DRIVER)
    particles = [obj for obj in scene.objects if bool(obj.get("proof_particle", False))]
    sparks = [
        obj
        for obj in particles
        if obj.get("proof_particle_role") == "sparse_wet_grinding_spark"
    ]
    droplets = [
        obj
        for obj in particles
        if obj.get("proof_particle_role") == "ballistic_coolant_droplet"
    ]
    mist = [
        obj
        for obj in particles
        if obj.get("proof_particle_role") == "fine_coolant_mist"
    ]
    fluid_sheets = [obj for obj in scene.objects if bool(obj.get("proof_fluid_sheet", False))]
    fluid_sprites = [obj for obj in fluid_sheets if bool(obj.get("proof_fluid_sprite", False))]
    animated_fluid_sheets = [
        obj
        for obj in fluid_sheets
        if any(
            bool(slot.material.get("proof_flow_loop", False))
            for slot in obj.material_slots
            if slot.material is not None
        )
    ]

    camera_reference = None
    max_camera_delta = 0.0
    minimum_parallel_dot = 1.0
    maximum_axis_up_dot = 0.0
    particle_samples: dict[str, list[tuple[int, Vector, float]]] = {
        obj.name: [] for obj in particles
    }
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        if camera_reference is None:
            camera_reference = scene.camera.matrix_world.copy()
        max_camera_delta = max(
            max_camera_delta,
            _matrix_delta(camera_reference, scene.camera.matrix_world),
        )
        work_axis = _axis(workpiece)
        wheel_axis = _axis(wheel)
        minimum_parallel_dot = min(
            minimum_parallel_dot, abs(float(work_axis.dot(wheel_axis)))
        )
        maximum_axis_up_dot = max(
            maximum_axis_up_dot,
            abs(float(work_axis.dot(Vector((0.0, 1.0, 0.0))))),
            abs(float(wheel_axis.dot(Vector((0.0, 1.0, 0.0))))),
        )
        if frame <= ENCODED_END_FRAME:
            for particle in particles:
                particle_samples[particle.name].append(
                    (
                        frame,
                        particle.matrix_world.translation.copy(),
                        _particle_size(particle),
                    )
                )

    scene.frame_set(scene.frame_start)
    first_work = workpiece.matrix_world.copy()
    first_wheel = wheel.matrix_world.copy()
    first_particles = {obj.name: obj.matrix_world.copy() for obj in particles}
    work_axis = _axis(workpiece)
    wheel_axis = _axis(wheel)
    contact_point = contact.matrix_world.translation.copy()
    work_radius = _radial_distance(
        workpiece.matrix_world.translation, contact_point, work_axis
    )
    wheel_radius = _radial_distance(
        wheel.matrix_world.translation, contact_point, wheel_axis
    )

    scene.frame_set(7)
    witness_motion_delta = _matrix_delta(first_work, workpiece.matrix_world)
    wheel_motion_delta = _matrix_delta(first_wheel, wheel.matrix_world)

    scene.frame_set(scene.frame_end)
    particle_seam_delta = max(
        (_matrix_delta(first_particles[obj.name], obj.matrix_world) for obj in particles),
        default=0.0,
    )
    work_seam_delta = _matrix_delta(first_work, workpiece.matrix_world)
    wheel_seam_delta = _matrix_delta(first_wheel, wheel.matrix_world)
    visible_particle_jumps: list[dict[str, object]] = []
    hidden_particle_jumps: list[dict[str, object]] = []
    maximum_visible_particle_step = 0.0
    maximum_particle_step = 0.0
    for name, samples in particle_samples.items():
        pairs = list(zip(samples, samples[1:]))
        if samples:
            pairs.append((samples[-1], samples[0]))
        for (frame_a, point_a, size_a), (frame_b, point_b, size_b) in pairs:
            step = (point_b - point_a).length
            maximum_particle_step = max(maximum_particle_step, step)
            item = {
                "particle": name,
                "frames": [frame_a, frame_b],
                "step_m": step,
                "sizes_m": [size_a, size_b],
            }
            if max(size_a, size_b) > VISIBLE_PARTICLE_SIZE_M:
                maximum_visible_particle_step = max(maximum_visible_particle_step, step)
                if step > MAX_VISIBLE_PARTICLE_STEP_M:
                    visible_particle_jumps.append(item)
            elif step > MAX_VISIBLE_PARTICLE_STEP_M:
                hidden_particle_jumps.append(item)

    soft_part_tokens = ("cable", "hose", "rubber", "bellows", "conduit")
    soft_parts = [
        obj
        for obj in scene.objects
        if obj.type in {"MESH", "CURVE"}
        and not obj.hide_render
        and any(token in obj.name.lower() for token in soft_part_tokens)
    ]
    incorrect_soft_materials = [
        {
            "object": obj.name,
            "materials": [slot.material.name for slot in obj.material_slots if slot.material],
        }
        for obj in soft_parts
        if not any(
            "rubberhose" in slot.material.name.lower()
            for slot in obj.material_slots
            if slot.material
        )
    ]
    checks = {
        "camera_fixed": max_camera_delta <= 1.0e-7,
        "horizontal_work_and_wheel_axes": maximum_axis_up_dot <= 1.0e-4,
        "parallel_spindle_directions": minimum_parallel_dot >= 0.9999,
        "workpiece_raceway_contact_radius": abs(work_radius - 0.142) <= 0.001,
        "small_wheel_contact_radius": abs(wheel_radius - 0.050) <= 0.001,
        "workpiece_visibly_rotates": witness_motion_delta >= 0.05,
        "wheel_visibly_rotates": wheel_motion_delta >= 0.05,
        "workpiece_loop_closes": work_seam_delta <= 1.0e-5,
        "wheel_loop_closes": wheel_seam_delta <= 1.0e-5,
        "particle_loop_closes": particle_seam_delta <= 1.0e-7,
        "particle_motion_has_no_visible_teleports": not visible_particle_jumps,
        "coolant_droplet_population_present": len(droplets) >= 50,
        "coolant_mist_population_present": len(mist) >= 10,
        "continuous_contact_sprite_present": len(fluid_sprites) == 1,
        "contact_sheets_have_looping_flow": len(animated_fluid_sheets) == len(fluid_sheets),
        "sparks_are_sparse": 1 <= len(sparks) <= 12,
        "soft_parts_use_rubber_material": bool(soft_parts) and not incorrect_soft_materials,
        "no_camera_action": scene.camera.animation_data is None,
    }
    report: dict[str, object] = {
        "status": "pass" if all(checks.values()) else "fail",
        "scene": bpy.data.filepath,
        "checks": checks,
        "max_camera_matrix_delta": max_camera_delta,
        "minimum_axis_parallel_dot": minimum_parallel_dot,
        "maximum_axis_up_dot": maximum_axis_up_dot,
        "workpiece_contact_radius_m": work_radius,
        "wheel_contact_radius_m": wheel_radius,
        "workpiece_motion_matrix_delta": witness_motion_delta,
        "wheel_motion_matrix_delta": wheel_motion_delta,
        "workpiece_seam_matrix_delta": work_seam_delta,
        "wheel_seam_matrix_delta": wheel_seam_delta,
        "particle_seam_matrix_delta": particle_seam_delta,
        "maximum_particle_step_m": maximum_particle_step,
        "maximum_visible_particle_step_m": maximum_visible_particle_step,
        "visible_particle_jump_examples": visible_particle_jumps[:30],
        "hidden_particle_jump_examples": hidden_particle_jumps[:30],
        "soft_part_count": len(soft_parts),
        "incorrect_soft_materials": incorrect_soft_materials,
        "particle_count": len(particles),
        "coolant_droplet_count": len(droplets),
        "coolant_mist_count": len(mist),
        "fluid_sheet_count": len(fluid_sheets),
        "fluid_sprite_count": len(fluid_sprites),
        "animated_fluid_sheet_count": len(animated_fluid_sheets),
        "spark_count": len(sparks),
        "workpiece_turns": int(work_driver.get("proof_spin_turns", 0)),
        "wheel_turns": int(wheel_driver.get("proof_spin_turns", 0)),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SUM_GRINDING_VALIDATION=" + json.dumps(report))
    if report["status"] != "pass":
        raise RuntimeError("Grinding proof failed validation; inspect the JSON report")
    return report


if __name__ == "__main__":
    main()
