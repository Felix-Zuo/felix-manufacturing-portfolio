"""Credible robot-cell production context for the cinematic handoff beat.

The licensed six-axis robot remains the hero asset.  This module supplies the
missing manufacturing logic around it: a flat-belt infeed, horizontal bearing
rings, a located handoff nest, an enclosed downstream machine, and an overhead
service gantry.  All geometry is camera-safe and stays inside the guarded cell.
"""

from __future__ import annotations

import math
from typing import Any

import bpy

import modeling


Vec3 = tuple[float, float, float]


def _tag(obj: bpy.types.Object, role: str, detail: str) -> bpy.types.Object:
    obj["lookdev_role"] = role
    obj["sum_quality_level"] = "production"
    obj["sum_design_detail"] = detail
    return obj


def _box(
    name: str,
    dimensions: Vec3,
    collection: bpy.types.Collection,
    *,
    location: Vec3,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    role: str,
    detail: str,
    bevel: float = 0.018,
) -> bpy.types.Object:
    return _tag(
        modeling._box(
            name,
            dimensions,
            collection,
            location=location,
            parent=parent,
            material=material,
            bevel=bevel,
            role=detail,
        ),
        role,
        detail,
    )


def _cylinder(
    name: str,
    radius: float,
    depth: float,
    collection: bpy.types.Collection,
    *,
    location: Vec3,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    role: str,
    detail: str,
    rotation: Vec3 = (0.0, 0.0, 0.0),
    segments: int = 48,
) -> bpy.types.Object:
    return _tag(
        modeling._cylinder(
            name,
            radius,
            depth,
            collection,
            location=location,
            rotation=rotation,
            parent=parent,
            material=material,
            segments=segments,
            bevel=0.006,
            role=detail,
        ),
        role,
        detail,
    )


def _build_flat_belt(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> tuple[bpy.types.Object, list[bpy.types.Object]]:
    belt_root = modeling._empty(
        "SUM_RobotCell_FlatBeltInfeed",
        collection,
        location=(-2.78, 9.42, 0.0),
        parent=root,
        display_size=0.18,
    )
    belt_root["sum_asset_type"] = "horizontal_flat_belt_bearing_infeed"
    belt_root["transfer_logic"] = "rings lie flat on a continuous belt"

    belt = _box(
        "SUM_RobotCell_InfeedBeltSurface",
        (1.02, 4.55, 0.10),
        collection,
        location=(0.0, 0.0, 0.88),
        parent=belt_root,
        material=materials["rubber"],
        role="rubber",
        detail="continuous_antistatic_flat_conveyor_belt",
        bevel=0.10,
    )
    _box(
        "SUM_RobotCell_InfeedBeltBed",
        (1.18, 4.72, 0.19),
        collection,
        location=(0.0, 0.0, 0.76),
        parent=belt_root,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="guarded_flat_belt_conveyor_bed",
        bevel=0.065,
    )
    # The camera approaches from +X. Keep the far guide tall enough to locate
    # the rings while dropping the near guide below their sight line; two tall
    # rails read as an opaque barrier in the robot handoff composition.
    for x, rail_height, rail_z, detail in (
        (-0.59, 0.16, 0.98, "far_adjustable_stainless_conveyor_side_guide"),
        (0.59, 0.055, 0.925, "camera_side_low_profile_conveyor_edge_guide"),
    ):
        _box(
            f"SUM_RobotCell_InfeedSideRail_{'L' if x < 0 else 'R'}",
            (0.045, 4.65, rail_height),
            collection,
            location=(x, 0.0, rail_z),
            parent=belt_root,
            material=materials["brushed_steel"],
            role="brushed_metal",
            detail=detail,
            bevel=0.010,
        )
    supports = [
        ((x, y, 0.39), (0.10, 0.10, 0.70))
        for x in (-0.46, 0.46)
        for y in (-1.82, 1.82)
    ]
    support_obj = modeling._box_array(
        "SUM_RobotCell_InfeedSupportLegs",
        supports,
        collection,
        parent=belt_root,
        material=materials["factory_structure"],
        bevel=0.010,
        role="levelled_conveyor_support_frame",
    )
    _tag(support_obj, "steel_blue", "levelled_conveyor_support_frame")
    _box(
        "SUM_RobotCell_InfeedDriveGuard",
        (0.74, 0.34, 0.48),
        collection,
        location=(0.0, 2.35, 0.61),
        parent=belt_root,
        material=materials["paint_graphite"],
        role="powder_coat",
        detail="enclosed_conveyor_drive_and_tension_guard",
        bevel=0.055,
    )

    rings: list[bpy.types.Object] = []
    for index, y in enumerate((-1.44, -0.35, 0.78, 1.72), start=1):
        ring = modeling._annular_prism(
            f"SUM_RobotCell_InfeedBearingRing_{index:02d}",
            0.235,
            0.158,
            0.070,
            collection,
            location=(0.0, y, 0.985),
            parent=belt_root,
            material=materials["machined_steel"],
            segments=96,
            bevel=0.005,
            role="heat_treated_bearing_outer_ring_flat_on_belt",
        )
        _tag(ring, "workpiece_steel", "heat_treated_bearing_outer_ring_flat_on_belt")
        rings.append(ring)

    sensor = _box(
        "SUM_RobotCell_InfeedPhotoeye",
        (0.16, 0.10, 0.16),
        collection,
        location=(0.70, -1.83, 1.16),
        parent=belt_root,
        material=materials["screen_frame"],
        role="screen_glass",
        detail="conveyor_part_present_photoelectric_sensor",
        bevel=0.025,
    )
    sensor["process_signal"] = "part_present_before_robot_pick"
    return belt, rings


def _build_handoff_nest(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    nest_root = modeling._empty(
        "SUM_RobotCell_HandoffNest",
        collection,
        location=(-3.12, 12.45, 0.0),
        parent=root,
        display_size=0.16,
    )
    _box(
        "SUM_RobotCell_HandoffNestBase",
        (1.20, 1.24, 0.62),
        collection,
        location=(0.0, 0.0, 0.34),
        parent=nest_root,
        material=materials["paint_graphite"],
        role="powder_coat",
        detail="stiff_welded_robot_handoff_pedestal",
        bevel=0.055,
    )
    _cylinder(
        "SUM_RobotCell_HandoffRotaryTable",
        0.46,
        0.12,
        collection,
        location=(0.0, 0.0, 0.72),
        parent=nest_root,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="indexing_robot_handoff_rotary_table",
        segments=72,
    )
    _cylinder(
        "SUM_RobotCell_HandoffPrecisionNest",
        0.34,
        0.07,
        collection,
        location=(0.0, 0.0, 0.82),
        parent=nest_root,
        material=materials["brushed_steel"],
        role="machined_steel",
        detail="ground_three_point_bearing_location_nest",
        segments=72,
    )
    for index, angle in enumerate((0.0, math.tau / 3.0, 2.0 * math.tau / 3.0), start=1):
        _cylinder(
            f"SUM_RobotCell_HandoffNest_Locator_{index:02d}",
            0.024,
            0.10,
            collection,
            location=(math.cos(angle) * 0.245, math.sin(angle) * 0.245, 0.91),
            parent=nest_root,
            material=materials["machined_steel"],
            role="machined_steel",
            detail="hardened_bearing_nest_location_pin",
            segments=24,
        )
    ring = modeling._annular_prism(
        "SUM_RobotCell_HandoffNest_BearingRing",
        0.255,
        0.170,
        0.082,
        collection,
        location=(0.0, 0.0, 0.955),
        parent=nest_root,
        material=materials["machined_steel"],
        segments=96,
        bevel=0.005,
        role="bearing_ring_horizontal_in_robot_handoff_nest",
    )
    _tag(ring, "workpiece_steel", "bearing_ring_horizontal_in_robot_handoff_nest")
    return nest_root


def _build_downstream_machine(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    machine = modeling._empty(
        "SUM_RobotCell_DownstreamMachine",
        collection,
        location=(-7.15, 11.80, 0.0),
        parent=root,
        display_size=0.22,
    )
    machine["sum_asset_type"] = "robot_loaded_enclosed_precision_machine"
    _box(
        "SUM_RobotCell_DownstreamMachineShell",
        (1.45, 5.05, 3.38),
        collection,
        location=(0.0, 0.0, 1.72),
        parent=machine,
        material=materials["factory_wall"],
        role="powder_coat",
        detail="double_skin_robot_loaded_machine_enclosure",
        bevel=0.075,
    )
    _box(
        "SUM_RobotCell_DownstreamMachineDarkSpine",
        (0.18, 4.76, 3.12),
        collection,
        location=(0.79, 0.0, 1.78),
        parent=machine,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="recessed_machine_front_structural_spine",
        bevel=0.025,
    )
    _box(
        "SUM_RobotCell_DownstreamMachineLoadDoor",
        (0.08, 2.18, 1.74),
        collection,
        location=(0.90, 0.20, 2.00),
        parent=machine,
        material=materials["safety_glass"],
        role="safety_glass",
        detail="robot_loading_safety_window_and_sliding_door",
        bevel=0.018,
    )
    _box(
        "SUM_RobotCell_DownstreamMachineProcessCavity",
        (0.07, 2.02, 1.58),
        collection,
        location=(0.84, 0.20, 2.00),
        parent=machine,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="deep_robot_loading_process_cavity",
        bevel=0.012,
    )
    process_trim = modeling._box_array(
        "SUM_RobotCell_DownstreamMachineWindowTrim",
        [
            ((1.125, -0.91, 2.00), (0.065, 0.080, 1.82)),
            ((1.125, 1.31, 2.00), (0.065, 0.080, 1.82)),
            ((1.125, 0.20, 2.87), (0.065, 2.30, 0.080)),
            ((1.125, 0.20, 1.13), (0.065, 2.30, 0.080)),
        ],
        collection,
        parent=machine,
        material=materials["factory_structure"],
        bevel=0.008,
        role="deep_machine_loading_window_structural_trim",
    )
    _tag(process_trim, "steel_blue", "deep_machine_loading_window_structural_trim")
    spindle = modeling._cylinder_between(
        "SUM_RobotCell_DownstreamMachineWorkSpindle",
        (0.62, 0.20, 1.96),
        (0.96, 0.20, 1.96),
        0.105,
        collection,
        parent=machine,
        material=materials["machined_steel"],
        segments=64,
        bevel=0.006,
        role="horizontal_robot_loaded_work_spindle",
    )
    _tag(spindle, "machined_steel", "horizontal_robot_loaded_work_spindle")
    workpiece = modeling._annular_prism(
        "SUM_RobotCell_DownstreamMachineBearingRing",
        0.315,
        0.190,
        0.090,
        collection,
        location=(1.035, 0.20, 1.96),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=machine,
        material=materials["machined_steel"],
        segments=96,
        bevel=0.005,
        role="horizontal_bearing_ring_loaded_in_machine",
    )
    _tag(workpiece, "workpiece_steel", "horizontal_bearing_ring_loaded_in_machine")
    _box(
        "SUM_RobotCell_DownstreamMachineTaskLight",
        (0.045, 0.92, 0.075),
        collection,
        location=(1.10, 0.20, 2.75),
        parent=machine,
        material=materials["luminaire_diffuser"],
        role="luminaire",
        detail="sealed_machine_loading_task_light",
        bevel=0.012,
    )
    _box(
        "SUM_RobotCell_DownstreamMachineControlPod",
        (0.27, 0.70, 1.08),
        collection,
        location=(0.96, -1.66, 2.08),
        parent=machine,
        material=materials["paint_graphite"],
        role="powder_coat",
        detail="sealed_robot_cell_machine_control_pod",
        bevel=0.040,
    )
    _box(
        "SUM_RobotCell_DownstreamMachineHMI",
        (0.04, 0.53, 0.38),
        collection,
        location=(1.115, -1.66, 2.30),
        parent=machine,
        material=materials["screen_content"],
        role="screen_glass",
        detail="machine_cycle_status_hmi_glass",
        bevel=0.010,
    )
    vents = [
        ((0.86, 1.78 + index * 0.13, 0.72), (0.04, 0.090, 0.025))
        for index in range(7)
    ]
    vent_obj = modeling._box_array(
        "SUM_RobotCell_DownstreamMachineFilterVents",
        vents,
        collection,
        parent=machine,
        material=materials["black_oxide"],
        bevel=0.003,
        role="filtered_machine_electrical_cabinet_vents",
    )
    _tag(vent_obj, "dark_metal", "filtered_machine_electrical_cabinet_vents")
    return machine


def _build_overhead_service_gantry(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    gantry = modeling._empty(
        "SUM_RobotCell_OverheadServiceGantry",
        collection,
        parent=root,
        display_size=0.25,
    )
    columns = [
        ((x, y, 2.45), (0.16, 0.18, 4.90))
        for x in (-7.55, -2.35)
        for y in (5.20, 15.95)
    ]
    column_obj = modeling._box_array(
        "SUM_RobotCell_GantryColumns",
        columns,
        collection,
        parent=gantry,
        material=materials["factory_structure"],
        bevel=0.015,
        role="robot_cell_overhead_service_gantry_columns",
    )
    _tag(column_obj, "steel_blue", "robot_cell_overhead_service_gantry_columns")
    rails = [
        ((-4.95, y, 4.84), (5.36, 0.18, 0.22)) for y in (5.20, 15.95)
    ]
    rails.extend(
        [
            ((x, 10.58, 4.84), (0.18, 10.80, 0.22))
            for x in (-7.55, -2.35)
        ]
    )
    rail_obj = modeling._box_array(
        "SUM_RobotCell_GantryRails",
        rails,
        collection,
        parent=gantry,
        material=materials["factory_structure"],
        bevel=0.015,
        role="robot_cell_overhead_service_gantry_rails",
    )
    _tag(rail_obj, "steel_blue", "robot_cell_overhead_service_gantry_rails")
    _box(
        "SUM_RobotCell_GantryCableTrolley",
        (0.58, 0.72, 0.28),
        collection,
        location=(-4.95, 12.70, 4.66),
        parent=gantry,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="overhead_energy_chain_service_trolley",
        bevel=0.045,
    )
    service_drop = modeling._bezier_tube(
        "SUM_RobotCell_GantryUtilityDrop",
        [
            (-4.95, 12.70, 4.55),
            (-4.86, 12.66, 4.03),
            (-4.72, 12.58, 3.43),
            (-4.58, 12.48, 3.04),
        ],
        0.026,
        collection,
        parent=gantry,
        material=materials["rubber"],
        role="robot_cell_dressed_power_air_and_io_service_drop",
        resolution=16,
    )
    _tag(service_drop, "rubber", "robot_cell_dressed_power_air_and_io_service_drop")
    return gantry


def augment_robot_cell(assets: dict[str, Any]) -> dict[str, Any]:
    root_collection = assets.get("root_collection")
    layout_root = assets.get("layout_root")
    materials = assets.get("placeholder_materials")
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")
    if not isinstance(layout_root, bpy.types.Object):
        raise TypeError("assets must provide layout_root")
    if not isinstance(materials, dict):
        raise TypeError("assets must provide placeholder_materials")

    collection = modeling._child_collection(root_collection, "SUM_MODEL_RobotCellStory")
    root = modeling._empty(
        "SUM_ASSET_RobotCellStory",
        collection,
        parent=layout_root,
        display_size=0.32,
    )
    root["sum_asset_type"] = "robot_cell_manufacturing_story_context"
    root["visual_logic"] = (
        "flat infeed -> robot pick -> located handoff nest -> enclosed machine"
    )

    belt, rings = _build_flat_belt(root, collection, materials)
    nest = _build_handoff_nest(root, collection, materials)
    machine = _build_downstream_machine(root, collection, materials)
    gantry = _build_overhead_service_gantry(root, collection, materials)

    assets["robot_cell_story"] = root
    assets["robot_cell_infeed_belt"] = belt
    assets["robot_cell_infeed_rings"] = rings
    assets["robot_cell_handoff_nest"] = nest
    assets["robot_cell_downstream_machine"] = machine
    assets["robot_cell_overhead_gantry"] = gantry
    assets.setdefault("collections", {})["robot_cell_story"] = collection
    bpy.context.view_layer.update()
    return assets


__all__ = ["augment_robot_cell"]
