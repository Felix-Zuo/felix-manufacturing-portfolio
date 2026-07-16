"""V8 story motion for the hero ring, AGV, inspection and final handoff."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from typing import Any

import bpy

import animation


BASE_DURATION = 38.0


def _frame(authored_frame: int, fps: int, duration: float) -> int:
    seconds = (authored_frame - 1) / 24.0
    return max(1, min(round(duration * fps), 1 + int(round(seconds * duration / BASE_DURATION * fps))))


def _zero_keys(frames: Sequence[int], values: Sequence[float]) -> list[tuple[int, float, float]]:
    return [(int(frame), float(value), 0.0) for frame, value in zip(frames, values)]


def _location_channels(
    points: Sequence[tuple[int, tuple[float, float, float]]],
    fps: int,
    duration: float,
) -> list[tuple[str, int, list[tuple[int, float, float]]]]:
    frames = [_frame(frame, fps, duration) for frame, _ in points]
    return [
        ("location", axis, _zero_keys(frames, [location[axis] for _, location in points]))
        for axis in range(3)
    ]


def _descendants(root: bpy.types.Object) -> list[bpy.types.Object]:
    return list(root.children_recursive)


def _animate_hero_ring(
    ring: bpy.types.Object,
    fps: int,
    duration: float,
) -> bpy.types.Action:
    points = (
        (1, (0.0, -0.75, 0.58)),
        (84, (0.0, 4.30, 0.58)),
        (132, (0.0, 6.20, 0.58)),
        (150, (0.0, 6.80, 0.58)),
        (166, (0.0, 9.15, 0.58)),
        (184, (-0.07, 10.68, 0.97)),
        (205, (-0.29, 10.72, 0.95)),
        (228, (-0.23, 10.02, 1.08)),
        (244, (0.25, 10.20, 1.10)),
        (252, (0.25, 10.75, 1.10)),
        (287, (0.25, 13.00, 1.18)),
        (300, (0.25, 14.25, 1.82)),
        (318, (1.65, 14.55, 1.82)),
        (342, (2.93, 15.00, 1.82)),
        (498, (2.93, 15.00, 1.82)),
        (506, (2.93, 15.00, 1.82)),
        (510, (2.55, 17.20, 1.13)),
        (518, (2.55, 17.20, 1.13)),
        (522, (2.55, 17.20, 1.13)),
        (531, (2.34, 17.95, 1.13)),
        (540, (1.875, 18.60, 1.13)),
        (550, (1.41, 19.25, 1.13)),
        (559, (1.20, 20.00, 1.13)),
        (588, (1.20, 20.00, 1.13)),
        (620, (-1.00, 23.50, 1.15)),
        (660, (-2.20, 25.00, 1.11)),
        (702, (-2.20, 25.00, 1.11)),
        (735, (-0.80, 27.50, 0.93)),
        (760, (0.0, 29.00, 0.518)),
        (798, (0.0, 29.00, 0.518)),
        (882, (0.0, 34.20, 0.518)),
        (912, (0.0, 35.80, 0.518)),
    )
    spin_points = (
        (1, 0.0),
        (343, 0.0),
        (386, math.pi * 0.25),
        (420, math.pi * 2.0),
        (465, math.pi * 17.0),
        (498, math.pi * 18.0),
        (588, math.pi * 18.0),
        (660, math.pi * 20.0),
        (702, math.pi * 26.0),
        (912, math.pi * 26.0),
    )
    spin_frames = [_frame(frame, fps, duration) for frame, _ in spin_points]
    spin_values = [value for _, value in spin_points]
    channels = _location_channels(points, fps, duration)
    orientation_frames = [_frame(value, fps, duration) for value in (1, 506, 510, 912)]
    orientation_y = (math.pi * 0.5, math.pi * 0.5, 0.0, 0.0)
    channels.append(("rotation_euler", 1, _zero_keys(orientation_frames, orientation_y)))
    channels.append(("delta_rotation_euler", 2, animation._sampled_keys(spin_frames, spin_values)))
    ring["sum_story_parent_sequence"] = (
        "AGV pallet -> robot gripper -> grinder locator -> outfeed -> inspection -> AGV output"
    )
    ring["sum_animation_contact_frames"] = [
        _frame(420, fps, duration),
        _frame(465, fps, duration),
    ]
    ring["post_process_reorientation"] = (
        "enclosed servo turner lays the ring flat before the side-flex belt carrier"
    )
    return animation._create_action(
        ring,
        "SUM_ANIM_V8HeroRingJourney",
        "single_outer_ring_process_journey",
        channels,
        fps,
        duration,
    )


def _animate_agv(
    agv: bpy.types.Object,
    fps: int,
    duration: float,
) -> tuple[bpy.types.Action, list[bpy.types.Action]]:
    points = (
        (1, (0.0, -0.75, 0.0)),
        (84, (0.0, 4.30, 0.0)),
        (132, (0.0, 6.20, 0.0)),
        (150, (0.0, 6.80, 0.0)),
        (166, (0.0, 9.15, 0.0)),
        (190, (-2.40, 10.50, 0.0)),
        (588, (-2.40, 24.00, 0.0)),
        (660, (-2.40, 26.00, 0.0)),
        (735, (0.0, 29.00, 0.0)),
        (798, (0.0, 29.00, 0.0)),
        (882, (0.0, 34.20, 0.0)),
        (912, (0.0, 35.80, 0.0)),
    )
    agv_action = animation._create_action(
        agv,
        "SUM_ANIM_V8AGV07Journey",
        "agv_story_route_with_parallel_return_loop",
        _location_channels(points, fps, duration),
        fps,
        duration,
    )

    frames = [_frame(frame, fps, duration) for frame, _ in points]
    distance = 0.0
    distances = [0.0]
    for (_, previous), (_, current) in zip(points, points[1:]):
        distance += math.sqrt(sum((current[index] - previous[index]) ** 2 for index in range(3)))
        distances.append(distance)
    radius = float(agv.get("agv_drive_wheel_radius_m", 0.0625))
    angles = [value / radius for value in distances]
    wheel_actions: list[bpy.types.Action] = []
    for index, wheel in enumerate(
        sorted(
            (
                obj
                for obj in _descendants(agv)
                if obj.get("sum_part_role") == "agv_recessed_protected_drive_wheel"
            ),
            key=lambda obj: obj.name,
        ),
        start=1,
    ):
        wheel_actions.append(
            animation._create_action(
                wheel,
                f"SUM_ANIM_V8AGV07Wheel_{index:02d}",
                "agv_no_slip_driven_wheel_rotation",
                (("delta_rotation_euler", 1, animation._sampled_keys(frames, angles)),),
                fps,
                duration,
            )
        )
    agv["sum_animation_route"] = "inbound center aisle -> left return loop -> outbound center aisle"
    agv["sum_animation_distance_m"] = distance
    return agv_action, wheel_actions


def _animate_scan_line(scan_line: bpy.types.Object, fps: int, duration: float) -> bpy.types.Action:
    base = tuple(float(value) for value in scan_line.location)
    frames = [_frame(value, fps, duration) for value in (1, 100, 110, 132, 148, 160, 912)]
    values = (0.44, 0.44, 0.48, 0.60, 0.78, 0.78, 0.78)
    visibility = (0.001, 0.001, 1.0, 1.0, 1.0, 0.001, 0.001)
    return animation._create_action(
        scan_line,
        "SUM_ANIM_V8ScanLine",
        "single_direction_machine_vision_scan",
        (
            ("location", 0, _zero_keys(frames, [base[0]] * len(frames))),
            ("location", 1, _zero_keys(frames, [base[1]] * len(frames))),
            ("location", 2, _zero_keys(frames, values)),
            ("scale", 0, _zero_keys(frames, visibility)),
            ("scale", 1, _zero_keys(frames, visibility)),
            ("scale", 2, _zero_keys(frames, visibility)),
        ),
        fps,
        duration,
    )


def _animate_transfer(
    carriage: bpy.types.Object,
    loader: bpy.types.Object,
    fps: int,
    duration: float,
) -> list[bpy.types.Action]:
    carriage_points = (
        (1, (0.25, 10.15, 0.0)),
        (228, (0.25, 10.15, 0.0)),
        (244, (0.25, 10.20, 0.0)),
        (252, (0.25, 10.75, 0.0)),
        (287, (0.25, 13.00, 0.08)),
        (300, (0.25, 14.25, 0.72)),
        (342, (0.25, 14.25, 0.72)),
        (522, (0.25, 14.25, 0.72)),
        (588, (0.25, 10.15, 0.0)),
        (912, (0.25, 10.15, 0.0)),
    )
    loader_points = (
        (1, (0.25, 14.25, 1.82)),
        (300, (0.25, 14.25, 1.82)),
        (318, (1.65, 14.55, 1.82)),
        (342, (2.10, 15.00, 1.82)),
        (360, (2.10, 15.00, 1.82)),
        (386, (0.25, 14.25, 1.82)),
        (912, (0.25, 14.25, 1.82)),
    )
    return [
        animation._create_action(
            carriage,
            "SUM_ANIM_V8TransferCarriage",
            "servo_transfer_index_and_elevator",
            _location_channels(carriage_points, fps, duration),
            fps,
            duration,
        ),
        animation._create_action(
            loader,
            "SUM_ANIM_V8MachineLoaderSlide",
            "machine_loader_extend_dwell_retract",
            _location_channels(loader_points, fps, duration),
            fps,
            duration,
        ),
    ]


def _animate_roller_group(
    rollers: Sequence[bpy.types.Object],
    frame_values: Sequence[int],
    angle_values: Sequence[float],
    label: str,
    fps: int,
    duration: float,
) -> list[bpy.types.Action]:
    frames = [_frame(value, fps, duration) for value in frame_values]
    actions: list[bpy.types.Action] = []
    for index, roller in enumerate(rollers, start=1):
        actions.append(
            animation._create_action(
                roller,
                f"SUM_ANIM_V8{label}_{index:02d}",
                f"{label.lower()}_physically_driven_rotation",
                (("delta_rotation_euler", 2, animation._sampled_keys(frames, angle_values)),),
                fps,
                duration,
            )
        )
    return actions


def _animate_belt_group(
    belts: Sequence[bpy.types.Object],
    fps: int,
    duration: float,
) -> list[bpy.types.Action]:
    frames = [_frame(value, fps, duration) for value in (1, 500, 518, 559, 588, 620, 912)]
    phases = (0.0, 0.0, 0.0, 3.2, 5.0, 5.4, 5.4)
    actions: list[bpy.types.Action] = []
    for index, belt in enumerate(belts, start=1):
        belt["belt_phase"] = 0.0
        belt["belt_speed_mps"] = 0.35
        actions.append(
            animation._create_action(
                belt,
                f"SUM_ANIM_V8OutfeedBelt_{index:02d}",
                "continuous_conveyor_belt_phase",
                (("[\"belt_phase\"]", 0, _zero_keys(frames, phases)),),
                fps,
                duration,
            )
        )
    return actions


def _animate_outfeed_carrier(
    carrier: bpy.types.Object,
    fps: int,
    duration: float,
) -> bpy.types.Action:
    points = (
        (1, (2.55, 17.20, 0.0)),
        (518, (2.55, 17.20, 0.0)),
        (522, (2.55, 17.20, 0.0)),
        (531, (2.34, 17.95, 0.0)),
        (540, (1.875, 18.60, 0.0)),
        (550, (1.41, 19.25, 0.0)),
        (559, (1.20, 20.00, 0.0)),
        (912, (1.20, 20.00, 0.0)),
    )
    return animation._create_action(
        carrier,
        "SUM_ANIM_V8OutfeedNestCarrier",
        "side_flex_belt_workpiece_carrier_transfer",
        _location_channels(points, fps, duration),
        fps,
        duration,
    )


def _animate_inspection_head(
    probe: bpy.types.Object,
    laser_line: bpy.types.Object,
    fps: int,
    duration: float,
) -> list[bpy.types.Action]:
    probe_base = tuple(float(value) for value in probe.location)
    frames = [_frame(value, fps, duration) for value in (1, 620, 642, 660, 690, 702, 730, 912)]
    offsets = (0.22, 0.22, 0.05, 0.0, 0.0, 0.05, 0.22, 0.22)
    probe_action = animation._create_action(
        probe,
        "SUM_ANIM_V8InspectionProbe",
        "servo_probe_approach_measure_retract",
        (
            ("location", 0, _zero_keys(frames, [probe_base[0]] * len(frames))),
            ("location", 1, _zero_keys(frames, [probe_base[1]] * len(frames))),
            ("location", 2, _zero_keys(frames, [probe_base[2] + value for value in offsets])),
        ),
        fps,
        duration,
    )
    laser_frames = [_frame(value, fps, duration) for value in (1, 638, 648, 696, 708, 912)]
    visibility = (0.001, 0.001, 1.0, 1.0, 0.001, 0.001)
    laser_action = animation._create_action(
        laser_line,
        "SUM_ANIM_V8InspectionLaser",
        "inspection_laser_measurement_window",
        tuple(("scale", axis, _zero_keys(laser_frames, visibility)) for axis in range(3)),
        fps,
        duration,
    )
    return [probe_action, laser_action]


def _animate_wet_film(
    wet_film: bpy.types.Object,
    fps: int,
    duration: float,
) -> bpy.types.Action:
    frames = [_frame(value, fps, duration) for value in (1, 382, 404, 498, 522, 588, 620, 650, 912)]
    visibility = (0.001, 0.001, 1.0, 1.0, 0.88, 0.58, 0.24, 0.001, 0.001)
    rotation = (0.0, 0.0, math.pi, math.pi * 22.0, math.pi * 23.0, math.pi * 24.0, math.pi * 24.5, math.pi * 24.5, math.pi * 24.5)
    channels = [("scale", axis, _zero_keys(frames, visibility)) for axis in range(3)]
    channels.append(("delta_rotation_euler", 2, animation._sampled_keys(frames, rotation)))
    return animation._create_action(
        wet_film,
        "SUM_ANIM_V8RacewayWetFilm",
        "coolant_wet_film_build_and_spin_off",
        channels,
        fps,
        duration,
    )


def _animate_grinding_effects(fps: int, duration: float) -> list[bpy.types.Action]:
    actions: list[bpy.types.Action] = []
    jet_frames = [_frame(value, fps, duration) for value in (1, 374, 390, 498, 514, 912)]
    jet_values = (0.001, 0.001, 1.0, 1.0, 0.001, 0.001)
    for index in range(1, 3):
        jet = bpy.data.objects.get(f"SUM_GrindingCell_CoolantJet_Stream_{index:02d}")
        if not isinstance(jet, bpy.types.Object):
            continue
        actions.append(
            animation._create_action(
                jet,
                f"SUM_ANIM_V8CoolantJet_{index:02d}",
                "coherent_coolant_jet_process_window",
                tuple(("scale", axis, _zero_keys(jet_frames, jet_values)) for axis in range(3)),
                fps,
                duration,
            )
        )

    sparks = bpy.data.objects.get("LD_Grinding_Sparks")
    if isinstance(sparks, bpy.types.Object):
        spark_frames = [
            _frame(value, fps, duration)
            for value in (1, 404, 414, 430, 446, 462, 478, 490, 912)
        ]
        envelope = (0.001, 0.001, 0.65, 2.65, 0.82, 2.10, 0.55, 0.001, 0.001)
        channels = [
            ("scale", axis, _zero_keys(spark_frames, envelope))
            for axis in range(3)
        ]
        channels.append(
            (
                "delta_rotation_euler",
                0,
                _zero_keys(spark_frames, (0.0, 0.0, -0.08, 0.06, -0.04, 0.05, -0.03, 0.0, 0.0)),
            )
        )
        actions.append(
            animation._create_action(
                sparks,
                "SUM_ANIM_V8GrindingSparks",
                "restrained_wet_grinding_spark_bursts",
                channels,
                fps,
                duration,
            )
        )
    spark_light = bpy.data.objects.get("LD_Spark_Bounce")
    if isinstance(spark_light, bpy.types.Object) and isinstance(spark_light.data, bpy.types.Light):
        light_frames = [
            _frame(value, fps, duration)
            for value in (1, 404, 414, 430, 446, 462, 478, 490, 912)
        ]
        light_energy = (0.0, 0.0, 5.0, 26.0, 9.0, 21.0, 6.0, 0.0, 0.0)
        actions.append(
            animation._create_action(
                spark_light.data,
                "SUM_ANIM_V8GrindingSparkBounce",
                "restrained_wet_grinding_spark_bounce",
                (("energy", 0, _zero_keys(light_frames, light_energy)),),
                fps,
                duration,
            )
        )
    return actions


def _animate_overhead_trolley(
    trolley: bpy.types.Object,
    fps: int,
    duration: float,
) -> bpy.types.Action:
    points = (
        (1, (-2.70, 9.0, 3.30)),
        (166, (-2.70, 9.0, 3.30)),
        (228, (-2.70, 10.5, 3.24)),
        (342, (-2.70, 13.5, 3.18)),
        (474, (-2.70, 16.5, 3.26)),
        (588, (-2.70, 20.0, 3.20)),
        (702, (-2.70, 24.5, 3.16)),
        (798, (-2.70, 28.0, 3.24)),
        (882, (-2.70, 29.5, 3.30)),
        (912, (-2.70, 29.5, 3.30)),
    )
    return animation._create_action(
        trolley,
        "SUM_ANIM_V8OverheadLogistics",
        "overhead_tooling_pallet_transfer",
        _location_channels(points, fps, duration),
        fps,
        duration,
    )


def _animate_quality_gantry(
    bridge: bpy.types.Object,
    trolley: bpy.types.Object,
    jaws: Sequence[bpy.types.Object],
    fps: int,
    duration: float,
) -> list[bpy.types.Action]:
    bridge_points = (
        (1, (0.0, 20.0, 0.0)),
        (522, (0.0, 20.0, 0.0)),
        (588, (0.0, 20.0, 0.0)),
        (620, (0.0, 23.5, 0.0)),
        (642, (0.0, 25.0, 0.0)),
        (650, (0.0, 25.0, 0.0)),
        (702, (0.0, 25.0, 0.0)),
        (710, (0.0, 25.0, 0.0)),
        (735, (0.0, 27.5, 0.0)),
        (760, (0.0, 29.0, 0.0)),
        (770, (0.0, 29.0, 0.0)),
        (912, (0.0, 29.0, 0.0)),
    )
    trolley_points = (
        (1, (1.20, 0.0, 0.0)),
        (548, (1.20, 0.0, 0.0)),
        (559, (1.20, 0.0, -0.13)),
        (588, (1.20, 0.0, -0.13)),
        (620, (-1.00, 0.0, -0.10)),
        (642, (-2.20, 0.0, -0.17)),
        (650, (0.50, 0.0, 0.62)),
        (702, (0.50, 0.0, 0.62)),
        (710, (-2.20, 0.0, -0.17)),
        (735, (-0.80, 0.0, -0.32)),
        (760, (0.0, 0.0, -0.72)),
        (770, (0.0, 0.0, 0.62)),
        (798, (0.0, 0.0, 0.62)),
        (912, (0.0, 0.0, 0.0)),
    )
    actions = [
        animation._create_action(
            bridge,
            "SUM_ANIM_V8QualityGantryBridge",
            "quality_gantry_longitudinal_transfer",
            _location_channels(bridge_points, fps, duration),
            fps,
            duration,
        ),
        animation._create_action(
            trolley,
            "SUM_ANIM_V8QualityGantryTrolley",
            "quality_gantry_cross_travel",
            _location_channels(trolley_points, fps, duration),
            fps,
            duration,
        ),
    ]
    frames = [
        _frame(value, fps, duration)
        for value in (1, 548, 559, 642, 650, 702, 710, 735, 760, 770, 912)
    ]
    radii = (0.035, 0.035, 0.058, 0.058, 0.035, 0.035, 0.058, 0.058, 0.058, 0.035, 0.035)
    for index, jaw in enumerate(jaws, start=1):
        angle = float(jaw.get("grip_angle_rad", 0.0))
        x_values = [math.cos(angle) * radius for radius in radii]
        y_values = [math.sin(angle) * radius for radius in radii]
        actions.append(
            animation._create_action(
                jaw,
                f"SUM_ANIM_V8QualityGantryJaw_{index:02d}",
                "quality_gantry_three_jaw_internal_expand_hold_release",
                (
                    ("location", 0, _zero_keys(frames, x_values)),
                    ("location", 1, _zero_keys(frames, y_values)),
                ),
                fps,
                duration,
            )
        )
    return actions


def _animate_gripper_jaws(
    gripper: bpy.types.Object,
    fps: int,
    duration: float,
) -> list[bpy.types.Action]:
    movable_roles = {
        "servo_parallel_gripper_jaw_carrier",
        "servo_parallel_gripper_replaceable_finger",
        "replaceable_nonmarking_bearing_grip_pad",
        "replaceable_gripper_pad_fastener",
    }
    frames = [_frame(value, fps, duration) for value in (1, 150, 166, 184, 212, 228, 912)]
    actions: list[bpy.types.Action] = []
    for obj in gripper.children_recursive:
        if obj.get("sum_part_role") not in movable_roles:
            continue
        if "_L" in obj.name:
            sign = -1.0
        elif "_R" in obj.name:
            sign = 1.0
        else:
            continue
        base = float(obj.location.y)
        values = (
            base + sign * 0.035,
            base + sign * 0.035,
            base + sign * 0.035,
            base,
            base,
            base + sign * 0.035,
            base + sign * 0.035,
        )
        actions.append(
            animation._create_action(
                obj,
                f"SUM_ANIM_V8GripperJaw_{len(actions) + 1:02d}",
                "robot_gripper_open_clamp_release",
                (("location", 1, _zero_keys(frames, values)),),
                fps,
                duration,
            )
        )
    return actions


def _animate_inspection(
    rotary_assets: Sequence[bpy.types.Object],
    fps: int,
    duration: float,
) -> list[bpy.types.Action]:
    frames = [_frame(value, fps, duration) for value in (589, 620, 660, 702, 730)]
    angles = (0.0, math.pi * 2.0, math.pi * 10.0, math.pi * 18.0, math.pi * 18.0)
    actions = []
    for index, rotary in enumerate(rotary_assets, start=1):
        actions.append(
            animation._create_action(
                rotary,
                f"SUM_ANIM_V8InspectionRotaryTable_{index:02d}",
                "inspection_vertical_axis_air_bearing_rotation",
                (("delta_rotation_euler", 2, animation._sampled_keys(frames, angles)),),
                fps,
                duration,
            )
        )
    return actions


def _animate_final_doors(
    doors: Sequence[bpy.types.Object],
    fps: int,
    duration: float,
) -> list[bpy.types.Action]:
    frames = [_frame(value, fps, duration) for value in (799, 828, 864, 882, 912)]
    actions = []
    for index, door in enumerate(doors, start=1):
        base = float(door.location.x)
        sign = -1.0 if base < 0.0 else 1.0
        values = (base, base, sign * 1.45, sign * 1.45, sign * 1.45)
        actions.append(
            animation._create_action(
                door,
                f"SUM_ANIM_V8FinalDoor_{index:02d}",
                "final_door_open_to_black_handoff",
                (("location", 0, _zero_keys(frames, values)),),
                fps,
                duration,
            )
        )
    return actions


def animate_story(assets: dict[str, Any], fps: int = 24, duration: float = 38.0) -> dict[str, Any]:
    ring = assets.get("hero_ring")
    agv = assets.get("agv")
    scan_line = assets.get("scan_line")
    transfer_carriage = assets.get("transfer_carriage")
    loader_slide = assets.get("machine_loader_slide")
    outfeed_belts = assets.get("outfeed_belts")
    outfeed_carrier = assets.get("outfeed_carrier")
    grinding_drive_roller = assets.get("grinding_drive_roller")
    inspection_rotary_assets = assets.get("inspection_rotary_assets")
    inspection_probe = assets.get("inspection_probe")
    inspection_laser = assets.get("inspection_laser_line")
    overhead_trolley = assets.get("overhead_trolley")
    quality_bridge = assets.get("quality_gantry_bridge")
    quality_trolley = assets.get("quality_gantry_trolley")
    quality_jaws = assets.get("quality_gantry_jaws")
    gripper = assets.get("kuka_gripper")
    wet_film = assets.get("hero_wet_film")
    final_doors = assets.get("final_story_door_leaves")
    if not isinstance(ring, bpy.types.Object):
        raise TypeError("assets must provide hero_ring")
    if not isinstance(agv, bpy.types.Object):
        raise TypeError("assets must provide agv")
    if not isinstance(scan_line, bpy.types.Object):
        raise TypeError("assets must provide scan_line")
    if not isinstance(transfer_carriage, bpy.types.Object) or not isinstance(loader_slide, bpy.types.Object):
        raise TypeError("assets must provide transfer carriage and loader slide")
    if not isinstance(outfeed_belts, Sequence) or not all(isinstance(item, bpy.types.Object) for item in outfeed_belts):
        raise TypeError("assets must provide outfeed_belts")
    if not isinstance(outfeed_carrier, bpy.types.Object):
        raise TypeError("assets must provide outfeed_carrier")
    if not isinstance(grinding_drive_roller, bpy.types.Object):
        raise TypeError("assets must provide grinding_drive_roller")
    if not isinstance(inspection_rotary_assets, Sequence) or not all(
        isinstance(item, bpy.types.Object) for item in inspection_rotary_assets
    ):
        raise TypeError("assets must provide inspection_rotary_assets")
    if not isinstance(inspection_probe, bpy.types.Object) or not isinstance(inspection_laser, bpy.types.Object):
        raise TypeError("assets must provide inspection probe and laser")
    if not isinstance(overhead_trolley, bpy.types.Object):
        raise TypeError("assets must provide overhead_trolley")
    if not isinstance(quality_bridge, bpy.types.Object) or not isinstance(quality_trolley, bpy.types.Object):
        raise TypeError("assets must provide quality gantry bridge and trolley")
    if not isinstance(quality_jaws, Sequence) or not all(isinstance(item, bpy.types.Object) for item in quality_jaws):
        raise TypeError("assets must provide quality_gantry_jaws")
    if not isinstance(gripper, bpy.types.Object):
        raise TypeError("assets must provide kuka_gripper")
    if not isinstance(wet_film, bpy.types.Object):
        raise TypeError("assets must provide hero_wet_film")
    if not isinstance(final_doors, Sequence) or not all(isinstance(item, bpy.types.Object) for item in final_doors):
        raise TypeError("assets must provide final_story_door_leaves")

    hero_action = _animate_hero_ring(ring, fps, duration)
    agv_action, wheel_actions = _animate_agv(agv, fps, duration)
    scan_action = _animate_scan_line(scan_line, fps, duration)
    transfer_actions = _animate_transfer(transfer_carriage, loader_slide, fps, duration)
    outfeed_actions = _animate_belt_group(outfeed_belts, fps, duration)
    outfeed_carrier_action = _animate_outfeed_carrier(outfeed_carrier, fps, duration)
    drive_roller_actions = _animate_roller_group(
        (grinding_drive_roller,),
        (1, 386, 420, 474, 498, 912),
        (0.0, 0.0, -math.pi * 2.0, -math.pi * 36.0, -math.pi * 40.0, -math.pi * 40.0),
        "GrindingDriveRoller",
        fps,
        duration,
    )
    inspection_actions = _animate_inspection(inspection_rotary_assets, fps, duration)
    inspection_head_actions = _animate_inspection_head(inspection_probe, inspection_laser, fps, duration)
    wet_film_action = _animate_wet_film(wet_film, fps, duration)
    grinding_effect_actions = _animate_grinding_effects(fps, duration)
    overhead_action = _animate_overhead_trolley(overhead_trolley, fps, duration)
    quality_gantry_actions = _animate_quality_gantry(
        quality_bridge,
        quality_trolley,
        quality_jaws,
        fps,
        duration,
    )
    gripper_actions = _animate_gripper_jaws(gripper, fps, duration)
    door_actions = _animate_final_doors(final_doors, fps, duration)
    manifest = {
        "version": 8,
        "hero_ring": ring.name,
        "hero_action": hero_action.name,
        "agv_action": agv_action.name,
        "wheel_actions": [action.name for action in wheel_actions],
        "scan_action": scan_action.name,
        "transfer_actions": [action.name for action in transfer_actions],
        "outfeed_belt_actions": [action.name for action in outfeed_actions],
        "outfeed_carrier_action": outfeed_carrier_action.name,
        "drive_roller_actions": [action.name for action in drive_roller_actions],
        "inspection_actions": [action.name for action in inspection_actions],
        "inspection_head_actions": [action.name for action in inspection_head_actions],
        "wet_film_action": wet_film_action.name,
        "grinding_effect_actions": [action.name for action in grinding_effect_actions],
        "overhead_action": overhead_action.name,
        "quality_gantry_actions": [action.name for action in quality_gantry_actions],
        "gripper_actions": [action.name for action in gripper_actions],
        "final_door_actions": [action.name for action in door_actions],
        "handoff_order": ["AGV", "robot", "grinder", "outfeed", "inspection", "AGV"],
        "wet_grinding_contact_frames": [_frame(420, fps, duration), _frame(465, fps, duration)],
        "black_handoff_frame": _frame(904, fps, duration),
    }
    bpy.context.scene["v8_story_animation_manifest"] = json.dumps(
        manifest, separators=(",", ":"), ensure_ascii=True
    )
    bpy.context.scene.frame_set(1)
    return manifest
