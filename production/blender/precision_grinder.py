"""Production-detail augmentation for the internal raceway grinding cell."""

from __future__ import annotations

import math
from typing import Any

import bpy

import modeling


def _tag(obj: bpy.types.Object, role: str, detail: str) -> bpy.types.Object:
    obj["lookdev_role"] = role
    obj["sum_quality_level"] = "production"
    obj["sum_design_detail"] = detail
    return obj


def _exclude_old_doors() -> None:
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(
            ("SUM_GrindingCell_LeftDoor_", "SUM_GrindingCell_RightDoor_")
        ):
            obj.hide_render = True
            obj["sum_export_exclude"] = True
            obj["sum_replaced_by"] = "animated production sliding doors"


def _build_sliding_door(
    side: int,
    cell_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    label = "Left" if side < 0 else "Right"
    center_y = side * 1.15
    front_x = 1.605
    door = modeling._empty(
        f"SUM_GrindingCell_{label}ProductionSlidingDoor",
        collection,
        parent=cell_root,
        display_size=0.12,
    )
    door["sum_part_role"] = "animated_machine_sliding_door"
    door["door_side"] = label.lower()
    door["closed_offset_m"] = 0.0
    door["open_offset_m"] = side * 1.22

    lower = modeling._box(
        f"SUM_GrindingCell_{label}ProductionDoor_LowerPanel",
        (0.095, 2.12, 0.94),
        collection,
        location=(front_x, center_y, 0.84),
        parent=door,
        material=materials["enclosure_paint"],
        bevel=0.014,
        role="double_skin_machine_door_lower_panel",
    )
    _tag(lower, "powder_coat", "double_skin_machine_door_lower_panel")
    frame_boxes = [
        ((front_x, center_y - 1.02, 2.30), (0.095, 0.13, 2.92)),
        ((front_x, center_y + 1.02, 2.30), (0.095, 0.13, 2.92)),
        ((front_x, center_y, 1.31), (0.095, 2.08, 0.13)),
        ((front_x, center_y, 3.29), (0.095, 2.08, 0.13)),
    ]
    frame = modeling._box_array(
        f"SUM_GrindingCell_{label}ProductionDoor_Frame",
        frame_boxes,
        collection,
        parent=door,
        material=materials["paint_graphite"],
        bevel=0.012,
        role="machine_sliding_door_structural_frame",
    )
    _tag(frame, "dark_metal", "machine_sliding_door_structural_frame")
    glass = modeling._box(
        f"SUM_GrindingCell_{label}ProductionDoor_SafetyGlass",
        (0.028, 1.86, 1.78),
        collection,
        location=(front_x + 0.055, center_y, 2.30),
        parent=door,
        material=materials["safety_glass"],
        bevel=0.007,
        role="laminated_polycarbonate_machine_window",
    )
    _tag(glass, "safety_glass", "laminated_polycarbonate_machine_window")
    handle = modeling._cylinder(
        f"SUM_GrindingCell_{label}ProductionDoor_Handle",
        0.025,
        0.34,
        collection,
        location=(front_x + 0.12, center_y - side * 0.82, 1.72),
        parent=door,
        material=materials["black_oxide"],
        segments=24,
        bevel=0.004,
        role="machine_door_pull_handle",
    )
    _tag(handle, "dark_metal", "machine_door_pull_handle")
    rollers = []
    for y in (center_y - 0.78, center_y + 0.78):
        rollers.append(
            modeling._cylinder(
                f"SUM_GrindingCell_{label}DoorRoller_{'A' if y < center_y else 'B'}",
                0.055,
                0.045,
                collection,
                location=(front_x - 0.045, y, 3.73),
                rotation=(0.0, math.pi * 0.5, 0.0),
                parent=door,
                material=materials["black_oxide"],
                segments=24,
                bevel=0.003,
                role="enclosed_sliding_door_roller",
            )
        )
    for roller in rollers:
        _tag(roller, "dark_metal", "enclosed_sliding_door_roller")
    return door


def _build_b_axis_and_workhead(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    dark = materials["paint_graphite"]
    steel = materials["machined_steel"]
    brushed = materials["brushed_steel"]

    pedestal = modeling._box(
        "SUM_GrindingCell_BAxis_GranitePedestal",
        (0.92, 0.92, 0.48),
        collection,
        location=(-0.78, 0.0, 1.08),
        parent=root,
        material=materials["fixture"],
        bevel=0.035,
        role="polymer_concrete_workhead_pedestal",
    )
    _tag(pedestal, "powder_coat", "polymer_concrete_workhead_pedestal")
    rotary_base = modeling._cylinder(
        "SUM_GrindingCell_BAxis_RotaryTable",
        0.43,
        0.18,
        collection,
        location=(-0.78, 0.0, 1.36),
        parent=root,
        material=dark,
        segments=72,
        bevel=0.012,
        role="hydrostatic_b_axis_rotary_table",
    )
    _tag(rotary_base, "dark_metal", "hydrostatic_b_axis_rotary_table")
    scale_ring = modeling._torus(
        "SUM_GrindingCell_BAxis_EncoderScale",
        0.36,
        0.018,
        collection,
        location=(-0.78, 0.0, 1.46),
        parent=root,
        material=steel,
        major_segments=96,
        minor_segments=12,
        role="b_axis_optical_encoder_scale_ring",
    )
    _tag(scale_ring, "brushed_metal", "b_axis_optical_encoder_scale_ring")

    for index, x in enumerate((-1.10, -0.94, -0.78, -0.62), start=1):
        fin = modeling._torus(
            f"SUM_GrindingCell_Workhead_CoolingFin_{index:02d}",
            0.305,
            0.018,
            collection,
            location=(x, 0.0, 1.82),
            rotation=(0.0, math.pi * 0.5, 0.0),
            parent=root,
            material=dark,
            major_segments=64,
            minor_segments=10,
            role="workhead_motor_cooling_fin",
        )
        _tag(fin, "dark_metal", "workhead_motor_cooling_fin")

    bearing_cartridge = modeling._cylinder_between(
        "SUM_GrindingCell_Workhead_BearingCartridge",
        (-0.44, 0.0, 1.82),
        (-0.18, 0.0, 1.82),
        0.155,
        collection,
        parent=root,
        material=brushed,
        segments=64,
        bevel=0.008,
        role="precision_workhead_bearing_cartridge",
    )
    _tag(bearing_cartridge, "brushed_metal", "precision_workhead_bearing_cartridge")
    service_cap = modeling._cylinder_between(
        "SUM_GrindingCell_Workhead_ServiceCap",
        (-1.28, 0.0, 1.82),
        (-1.18, 0.0, 1.82),
        0.245,
        collection,
        parent=root,
        material=dark,
        segments=64,
        bevel=0.010,
        role="workhead_rear_service_cap",
    )
    _tag(service_cap, "dark_metal", "workhead_rear_service_cap")

    faceplate = modeling._annular_prism(
        "SUM_GrindingCell_ChuckPrecisionFaceplate",
        0.225,
        0.052,
        0.040,
        collection,
        location=(-0.005, 0.0, 1.82),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=root,
        material=dark,
        segments=96,
        bevel=0.004,
        role="precision_chuck_faceplate",
    )
    _tag(faceplate, "dark_metal", "precision_chuck_faceplate")
    bolts = modeling._add_bolt_circle(
        "SUM_GrindingCell_ChuckFaceplate",
        (-0.028, 0.0, 1.82),
        (1.0, 0.0, 0.0),
        0.172,
        0.010,
        0.030,
        12,
        collection,
        parent=root,
        material=steel,
    )
    for bolt in bolts:
        _tag(bolt, "brushed_metal", "chuck_faceplate_fastener")

    jaw_parts = []
    for index in range(3):
        angle = math.tau * index / 3.0
        radial_y = math.cos(angle)
        radial_z = math.sin(angle)
        jaw_parts.extend(
            (
                (
                    (0.075, radial_y * 0.155, 1.82 + radial_z * 0.155),
                    (0.13, 0.075, 0.075),
                ),
                (
                    (0.115, radial_y * 0.132, 1.82 + radial_z * 0.132),
                    (0.10, 0.050, 0.050),
                ),
            )
        )
    stepped_jaws = modeling._box_array(
        "SUM_GrindingCell_SteppedSoftJaws",
        jaw_parts,
        collection,
        parent=root,
        material=steel,
        bevel=0.006,
        role="stepped_soft_jaws_for_inner_ring",
    )
    _tag(stepped_jaws, "brushed_metal", "stepped_soft_jaws_for_inner_ring")

    raceway = modeling._torus(
        "SUM_GrindingCell_Workpiece_InternalRaceway",
        0.103,
        0.011,
        collection,
        location=(0.112, 0.0, 1.82),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=root,
        material=brushed,
        major_segments=96,
        minor_segments=16,
        role="inner_ring_raceway_contact_surface",
    )
    _tag(raceway, "brushed_metal", "inner_ring_raceway_contact_surface")


def _build_grinding_slide(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    steel = materials["machined_steel"]
    dark = materials["paint_graphite"]
    rails = []
    for y in (-0.43, 0.43):
        rails.append(((0.77, y, 1.04), (1.58, 0.075, 0.085)))
    rail_obj = modeling._box_array(
        "SUM_GrindingCell_XSlide_LinearRails",
        rails,
        collection,
        parent=root,
        material=steel,
        bevel=0.008,
        role="preloaded_linear_guide_rails",
    )
    _tag(rail_obj, "brushed_metal", "preloaded_linear_guide_rails")
    blocks = []
    for x in (0.28, 0.72):
        for y in (-0.43, 0.43):
            blocks.append(((x, y, 1.11), (0.22, 0.17, 0.13)))
    block_obj = modeling._box_array(
        "SUM_GrindingCell_XSlide_LinearBlocks",
        blocks,
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.014,
        role="preloaded_linear_guide_carriages",
    )
    _tag(block_obj, "dark_metal", "preloaded_linear_guide_carriages")

    bellows = []
    x = 0.96
    while x <= 1.46:
        bellows.append(((x, 0.0, 1.20), (0.035, 0.78, 0.24)))
        x += 0.055
    bellows_obj = modeling._box_array(
        "SUM_GrindingCell_XSlide_Bellows",
        bellows,
        collection,
        parent=root,
        material=materials["rubber"],
        bevel=0.004,
        role="telescopic_slide_bellows",
    )
    _tag(bellows_obj, "rubber", "telescopic_slide_bellows")

    spindle_mount = modeling._box(
        "SUM_GrindingCell_GrindingSpindleMount",
        (0.78, 0.68, 0.16),
        collection,
        location=(1.03, 0.037, 1.20),
        parent=root,
        material=dark,
        bevel=0.025,
        role="precision_spindle_saddle",
    )
    _tag(spindle_mount, "powder_coat", "precision_spindle_saddle")
    spindle_support = modeling._box(
        "SUM_GrindingCell_GrindingSpindleCastSupport",
        (0.42, 0.54, 0.48),
        collection,
        location=(1.16, 0.037, 1.46),
        parent=root,
        material=dark,
        bevel=0.055,
        role="ribbed_cast_spindle_support",
    )
    _tag(spindle_support, "powder_coat", "ribbed_cast_spindle_support")
    spindle_motor = modeling._cylinder_between(
        "SUM_GrindingCell_HighSpeedSpindleMotor",
        (0.76, 0.037, 1.82),
        (1.43, 0.037, 1.82),
        0.195,
        collection,
        parent=root,
        material=dark,
        segments=72,
        bevel=0.018,
        role="liquid_cooled_high_speed_spindle_motor",
    )
    _tag(spindle_motor, "dark_metal", "liquid_cooled_high_speed_spindle_motor")
    rear_cap = modeling._cylinder_between(
        "SUM_GrindingCell_SpindleMotorRearCap",
        (1.41, 0.037, 1.82),
        (1.55, 0.037, 1.82),
        0.162,
        collection,
        parent=root,
        material=steel,
        segments=64,
        bevel=0.010,
        role="spindle_motor_encoder_end_cap",
    )
    _tag(rear_cap, "brushed_metal", "spindle_motor_encoder_end_cap")
    for index, x in enumerate((1.05, 1.18, 1.31), start=1):
        cooling_ring = modeling._torus(
            f"SUM_GrindingCell_SpindleCoolingRing_{index:02d}",
            0.184,
            0.012,
            collection,
            location=(x, 0.037, 1.82),
            rotation=(0.0, math.pi * 0.5, 0.0),
            parent=root,
            material=steel,
            major_segments=64,
            minor_segments=10,
            role="spindle_motor_cooling_jacket_ring",
        )
        _tag(cooling_ring, "brushed_metal", "spindle_motor_cooling_jacket_ring")
    balance_collar = modeling._cylinder_between(
        "SUM_GrindingCell_SpindleBalanceCollar",
        (0.56, 0.037, 1.82),
        (0.70, 0.037, 1.82),
        0.128,
        collection,
        parent=root,
        material=steel,
        segments=64,
        bevel=0.008,
        role="grinding_spindle_balance_collar",
    )
    _tag(balance_collar, "brushed_metal", "grinding_spindle_balance_collar")
    wheel_guard = modeling._cylinder_between(
        "SUM_GrindingCell_WheelGuardCartridge",
        (0.205, 0.037, 1.82),
        (0.32, 0.037, 1.82),
        0.092,
        collection,
        parent=root,
        material=materials["black_oxide"],
        segments=48,
        bevel=0.006,
        role="internal_wheel_guard_and_splash_cartridge",
    )
    _tag(wheel_guard, "dark_metal", "internal_wheel_guard_and_splash_cartridge")

    servo = modeling._cylinder_between(
        "SUM_GrindingCell_XAxis_ServoMotor",
        (1.35, -0.60, 1.16),
        (1.62, -0.60, 1.16),
        0.15,
        collection,
        parent=root,
        material=dark,
        segments=48,
        bevel=0.012,
        role="x_axis_direct_drive_servo_motor",
    )
    _tag(servo, "powder_coat", "x_axis_direct_drive_servo_motor")
    encoder = modeling._cylinder_between(
        "SUM_GrindingCell_XAxis_ServoEncoder",
        (1.62, -0.60, 1.16),
        (1.72, -0.60, 1.16),
        0.11,
        collection,
        parent=root,
        material=materials["screen_frame"],
        segments=40,
        bevel=0.008,
        role="absolute_servo_encoder",
    )
    _tag(encoder, "screen_glass", "absolute_servo_encoder")


def _build_coolant_and_dressing(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    manifold = modeling._box(
        "SUM_GrindingCell_CoolantManifold",
        (0.22, 0.30, 0.18),
        collection,
        location=(0.58, -0.52, 2.20),
        parent=root,
        material=materials["brushed_steel"],
        bevel=0.018,
        role="high_pressure_coolant_manifold",
    )
    _tag(manifold, "brushed_metal", "high_pressure_coolant_manifold")
    for index, points in enumerate(
        (
            ((0.58, -0.52, 2.20), (0.42, -0.34, 2.08), (0.24, -0.12, 1.90)),
            ((0.58, -0.48, 2.16), (0.46, -0.20, 1.98), (0.20, 0.08, 1.88)),
        ),
        start=1,
    ):
        line = modeling._bezier_tube(
            f"SUM_GrindingCell_HighPressureCoolantLine_{index:02d}",
            list(points),
            0.014,
            collection,
            parent=root,
            material=materials["brushed_steel"],
            role="high_pressure_grinding_coolant_line",
            resolution=10,
        )
        _tag(line, "brushed_metal", "high_pressure_grinding_coolant_line")
        nozzle = modeling._cylinder_between(
            f"SUM_GrindingCell_CoolantJetNozzle_{index:02d}",
            points[-1],
            (0.13, -0.005 + index * 0.018, 1.835),
            0.018,
            collection,
            parent=root,
            material=materials["black_oxide"],
            segments=20,
            bevel=0.002,
            role="focused_coolant_jet_nozzle",
        )
        _tag(nozzle, "dark_metal", "focused_coolant_jet_nozzle")

    dresser_slide = modeling._box(
        "SUM_GrindingCell_Dresser_MicroSlide",
        (0.30, 0.24, 0.18),
        collection,
        location=(0.31, -0.34, 1.32),
        parent=root,
        material=materials["black_oxide"],
        bevel=0.016,
        role="diamond_dresser_micro_slide",
    )
    _tag(dresser_slide, "dark_metal", "diamond_dresser_micro_slide")
    dresser_scale = modeling._box(
        "SUM_GrindingCell_Dresser_LinearScale",
        (0.32, 0.055, 0.065),
        collection,
        location=(0.31, -0.48, 1.38),
        parent=root,
        material=materials["screen_frame"],
        bevel=0.008,
        role="dresser_linear_encoder",
    )
    _tag(dresser_scale, "screen_glass", "dresser_linear_encoder")

    inspection_camera = modeling._cylinder_between(
        "SUM_GrindingCell_ProcessInspectionCamera",
        (0.36, 0.42, 2.35),
        (0.28, 0.34, 2.22),
        0.052,
        collection,
        parent=root,
        material=materials["screen_frame"],
        segments=32,
        bevel=0.006,
        role="sealed_process_inspection_camera",
    )
    _tag(inspection_camera, "screen_glass", "sealed_process_inspection_camera")


def augment_grinder(assets: dict[str, Any]) -> dict[str, Any]:
    cell = assets.get("enclosed_grinding_cell")
    process_root = bpy.data.objects.get("SUM_GrindingCell_ProcessFrame_BAxis")
    materials = assets.get("placeholder_materials")
    root_collection = assets.get("root_collection")
    if not isinstance(cell, bpy.types.Object):
        raise TypeError("assets must provide enclosed_grinding_cell")
    if not isinstance(process_root, bpy.types.Object):
        raise RuntimeError("Grinding process frame is missing")
    if not isinstance(materials, dict):
        raise TypeError("assets must provide placeholder_materials")
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")

    collection = modeling._child_collection(
        root_collection, "SUM_MODEL_PrecisionGrinderDetail"
    )
    _exclude_old_doors()
    left_door = _build_sliding_door(-1, cell, collection, materials)
    right_door = _build_sliding_door(1, cell, collection, materials)

    detail_root = modeling._empty(
        "SUM_ASSET_InternalGrindingProcessDetail",
        collection,
        parent=process_root,
        display_size=0.18,
    )
    detail_root["sum_asset_type"] = "production_internal_raceway_grinding_process"
    detail_root["verified_process_axis"] = "horizontal X work and wheel spindle axes"
    detail_root["verified_contact"] = "small CBN wheel enters bore at radial offset"
    detail_root["detail_gate"] = (
        "B-axis, workhead, faceplate, stepped jaws, raceway, linear guides, "
        "bellows, servo, dresser, coolant, inspection camera"
    )
    _build_b_axis_and_workhead(detail_root, collection, materials)
    _build_grinding_slide(detail_root, collection, materials)
    _build_coolant_and_dressing(detail_root, collection, materials)

    cell["door_state"] = "animated open during process shot"
    cell["process_detail_level"] = "foreground production"
    assets["grinder_detail"] = detail_root
    assets["grinder_doors"] = (left_door, right_door)
    assets.setdefault("collections", {})["precision_grinder"] = collection
    bpy.context.view_layer.update()
    return assets
