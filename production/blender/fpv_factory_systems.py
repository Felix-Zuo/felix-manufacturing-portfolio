"""Production utility and overhead handling systems for the FPV factory.

The module adds only authored factory detail: machine service faces, grouped
utilities, and a visible linear gantry transfer.  The central service aisle is
kept clear below 2.80 m so the existing camera path remains unobstructed.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

import bpy

import modeling


COLLECTION_NAME = "SUM_MODEL_FPVFactorySystems"
ACTION_PREFIX = "SUM_FPV_FACTORY_"
REFERENCE_DURATION = 38.0

Vec3 = tuple[float, float, float]


def _tag(obj: bpy.types.Object, role: str, detail: str) -> bpy.types.Object:
    obj["lookdev_role"] = role
    obj["sum_quality_level"] = "production"
    obj["sum_design_detail"] = detail
    return obj


def _remove_orphaned_data(data: object) -> None:
    if getattr(data, "users", 1) != 0:
        return
    if isinstance(data, bpy.types.Mesh):
        bpy.data.meshes.remove(data)
    elif isinstance(data, bpy.types.Curve):
        bpy.data.curves.remove(data)


def _reset_collection(parent: bpy.types.Collection) -> bpy.types.Collection:
    existing = bpy.data.collections.get(COLLECTION_NAME)
    if existing is not None:
        owned_data = [
            obj.data
            for obj in existing.all_objects
            if getattr(obj, "data", None) is not None
        ]
        modeling._remove_collection_tree(existing)
        for datablock in owned_data:
            _remove_orphaned_data(datablock)
    for action in list(bpy.data.actions):
        if action.name.startswith(ACTION_PREFIX) and action.users == 0:
            bpy.data.actions.remove(action)
    return modeling._child_collection(parent, COLLECTION_NAME)


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
    rotation: Vec3 = (0.0, 0.0, 0.0),
    bevel: float = 0.008,
) -> bpy.types.Object:
    return _tag(
        modeling._box(
            name,
            dimensions,
            collection,
            location=location,
            rotation=rotation,
            parent=parent,
            material=material,
            bevel=bevel,
            role=detail,
        ),
        role,
        detail,
    )


def _boxes(
    name: str,
    boxes: Iterable[tuple[Vec3, Vec3]],
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    role: str,
    detail: str,
    bevel: float = 0.004,
) -> bpy.types.Object:
    return _tag(
        modeling._box_array(
            name,
            tuple(boxes),
            collection,
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
    segments: int = 28,
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
            bevel=min(radius * 0.16, 0.006),
            role=detail,
        ),
        role,
        detail,
    )


def _tube(
    name: str,
    points: Sequence[Vec3],
    radius: float,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    role: str,
    detail: str,
) -> bpy.types.Object:
    return _tag(
        modeling._bezier_tube(
            name,
            points,
            radius,
            collection,
            parent=parent,
            material=material,
            role=detail,
            resolution=10,
        ),
        role,
        detail,
    )


def _build_machine_service_face(
    bay: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    is_left = "MachineBay_L" in bay.name
    side = -1.0 if is_left else 1.0
    label = bay.name.rsplit("_", 1)[-1]
    toward_aisle = -side
    inner_face = side * 2.43
    face_x = inner_face + toward_aisle * 0.075
    panel_y = 1.54
    panel_z = 0.77

    _box(
        f"SUM_V7_Machine_{label}_LowerServiceDoor",
        (0.045, 1.02, 1.12),
        collection,
        location=(face_x, panel_y, panel_z),
        parent=bay,
        material=materials["enclosure_paint"],
        role="powder_coat",
        detail="flush_machine_lower_service_access_door",
        bevel=0.012,
    )
    gasket = (
        ((face_x + toward_aisle * 0.026, panel_y - 0.51, panel_z), (0.018, 0.025, 1.15)),
        ((face_x + toward_aisle * 0.026, panel_y + 0.51, panel_z), (0.018, 0.025, 1.15)),
        ((face_x + toward_aisle * 0.026, panel_y, panel_z - 0.56), (0.018, 1.04, 0.025)),
        ((face_x + toward_aisle * 0.026, panel_y, panel_z + 0.56), (0.018, 1.04, 0.025)),
    )
    _boxes(
        f"SUM_V7_Machine_{label}_ServiceDoorGasket",
        gasket,
        collection,
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="service_door_compression_gasket_and_reveal",
    )
    hardware_x = face_x + toward_aisle * 0.055
    fasteners = []
    for y in (panel_y - 0.45, panel_y + 0.45):
        for z in (panel_z - 0.48, panel_z, panel_z + 0.48):
            fasteners.append(((hardware_x, y, z), (0.025, 0.030, 0.030)))
    _boxes(
        f"SUM_V7_Machine_{label}_ServiceDoorFasteners",
        fasteners,
        collection,
        parent=bay,
        material=materials["machined_steel"],
        role="brushed_metal",
        detail="captive_service_panel_fasteners",
        bevel=0.002,
    )
    _cylinder(
        f"SUM_V7_Machine_{label}_QuarterTurnLatch",
        0.035,
        0.050,
        collection,
        location=(hardware_x, panel_y + 0.34, panel_z),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="quarter_turn_service_door_latch",
        segments=20,
    )

    wiper_x = inner_face + toward_aisle * 0.095
    _box(
        f"SUM_V7_Machine_{label}_WindowWiper",
        (0.030, 0.045, 0.92),
        collection,
        location=(wiper_x, -0.50, 2.13),
        rotation=(math.radians(18.0 * side), 0.0, 0.0),
        parent=bay,
        material=materials["black_oxide"],
        role="rubber",
        detail="machine_window_coolant_wiper",
        bevel=0.005,
    )
    _cylinder(
        f"SUM_V7_Machine_{label}_WiperPivot",
        0.045,
        0.050,
        collection,
        location=(wiper_x + toward_aisle * 0.020, -0.50, 1.70),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["machined_steel"],
        role="brushed_metal",
        detail="sealed_machine_window_wiper_pivot",
        segments=24,
    )

    # Stay within the projection of the existing HMI glass instead of making
    # the machine row intrude farther into the service aisle.
    hmi_x = inner_face + toward_aisle * 0.285
    keys = []
    for row in range(3):
        for column in range(4):
            keys.append(
                (
                    (hmi_x, 1.44 + column * 0.085, 1.76 + row * 0.075),
                    (0.025, 0.052, 0.038),
                )
            )
    _boxes(
        f"SUM_V7_Machine_{label}_HMIKeypad",
        keys,
        collection,
        parent=bay,
        material=materials["screen_frame"],
        role="screen_glass",
        detail="sealed_machine_hmi_membrane_keypad",
        bevel=0.006,
    )

    warning_x = inner_face + toward_aisle * 0.110
    _box(
        f"SUM_V7_Machine_{label}_HazardPlate",
        (0.026, 0.30, 0.24),
        collection,
        location=(warning_x, 0.62, 1.02),
        parent=bay,
        material=materials["safety_yellow"],
        role="safety_yellow",
        detail="machine_motion_hazard_identification_plate",
        bevel=0.008,
    )
    _boxes(
        f"SUM_V7_Machine_{label}_HazardChevron",
        (
            ((warning_x + toward_aisle * 0.018, 0.56, 1.02), (0.018, 0.030, 0.18)),
            ((warning_x + toward_aisle * 0.018, 0.68, 1.02), (0.018, 0.030, 0.18)),
        ),
        collection,
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="machine_hazard_chevron_symbol",
        bevel=0.002,
    )
    bay["v7_machine_detail"] = (
        "service door, captive fasteners, window wiper, sealed keypad, hazard plate"
    )


def _build_grouped_utilities(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    machine_bays: Sequence[bpy.types.Object],
) -> dict[str, list[bpy.types.Object]]:
    trays: list[bpy.types.Object] = []
    mains: list[bpy.types.Object] = []
    drops: list[bpy.types.Object] = []
    y_start = 18.0
    y_end = 147.0
    tray_center = (y_start + y_end) * 0.5
    tray_length = y_end - y_start

    for side in (-1.0, 1.0):
        label = "L" if side < 0 else "R"
        tray_x = side * 7.02
        trays.append(
            _boxes(
                f"SUM_V7_UtilityTray_{label}_LongitudinalFrame",
                (
                    ((tray_x - 0.22, tray_center, 4.72), (0.055, tray_length, 0.28)),
                    ((tray_x + 0.22, tray_center, 4.72), (0.055, tray_length, 0.28)),
                    ((tray_x, tray_center, 4.58), (0.50, tray_length, 0.045)),
                ),
                collection,
                parent=root,
                material=materials["factory_structure"],
                role="steel_blue",
                detail="machine_row_ladder_cable_tray",
                bevel=0.004,
            )
        )
        rung_boxes = []
        y = y_start + 0.60
        while y < y_end:
            rung_boxes.append(((tray_x, y, 4.61), (0.46, 0.045, 0.045)))
            y += 2.40
        trays.append(
            _boxes(
                f"SUM_V7_UtilityTray_{label}_Rungs",
                rung_boxes,
                collection,
                parent=root,
                material=materials["brushed_steel"],
                role="brushed_metal",
                detail="machine_row_cable_tray_rungs",
                bevel=0.003,
            )
        )
        for utility_name, x_offset, z, radius, material_key, role in (
            ("CoolantSupply", 0.38, 4.36, 0.055, "brushed_steel", "brushed_metal"),
            ("CoolantReturn", 0.56, 4.16, 0.072, "black_oxide", "dark_metal"),
            ("CompressedAir", 0.20, 4.49, 0.034, "machined_steel", "brushed_metal"),
        ):
            x = tray_x + side * x_offset
            main = modeling._cylinder_between(
                f"SUM_V7_UtilityMain_{label}_{utility_name}",
                (x, y_start, z),
                (x, y_end, z),
                radius,
                collection,
                parent=root,
                material=materials[material_key],
                segments=32,
                bevel=0.004,
                role=f"factory_{utility_name.lower()}_main",
            )
            mains.append(_tag(main, role, f"grouped_factory_{utility_name.lower()}_main"))

    for bay in machine_bays:
        if not isinstance(bay, bpy.types.Object):
            continue
        side = -1.0 if "MachineBay_L" in bay.name else 1.0
        label = bay.name.rsplit("_", 1)[-1]
        travel_y = float(bay.location.y)
        source_x = side * 7.22
        interface_x = side * 6.42
        drops.append(
            _box(
                f"SUM_V7_Machine_{label}_FloorUtilityInterface",
                (0.44, 0.54, 0.24),
                collection,
                location=(interface_x, travel_y, 0.16),
                parent=root,
                material=materials["paint_graphite"],
                role="dark_metal",
                detail="sealed_floor_utility_interface_box",
                bevel=0.028,
            )
        )
        for index, (offset, radius, material_key, role, detail) in enumerate(
            (
                (-0.10, 0.020, "rubber", "rubber", "machine_power_and_control_drop"),
                (0.00, 0.016, "brushed_steel", "brushed_metal", "machine_coolant_supply_drop"),
                (0.10, 0.012, "machined_steel", "brushed_metal", "machine_compressed_air_drop"),
            ),
            start=1,
        ):
            points = (
                (source_x + side * offset, travel_y, 4.45),
                (source_x + side * offset, travel_y, 3.25),
                (interface_x + side * 0.12, travel_y, 0.82),
                (interface_x, travel_y, 0.34),
            )
            drops.append(
                _tube(
                    f"SUM_V7_Machine_{label}_UtilityDrop_{index:02d}",
                    points,
                    radius,
                    collection,
                    parent=root,
                    material=materials[material_key],
                    role=role,
                    detail=detail,
                )
            )
    return {"trays": trays, "mains": mains, "drops": drops}


def _scaled_frame(seconds: float, fps: int, duration: float) -> int:
    frame_end = max(1, int(round(fps * duration)))
    scaled_seconds = seconds * duration / REFERENCE_DURATION
    return min(frame_end, max(1, 1 + int(round(scaled_seconds * fps))))


def _key_axis(
    obj: bpy.types.Object,
    axis: int,
    action_suffix: str,
    samples: Sequence[tuple[float, float]],
    fps: int,
    duration: float,
) -> bpy.types.Action:
    obj.animation_data_clear()
    for seconds, value in samples:
        obj.location[axis] = value
        obj.keyframe_insert(
            data_path="location",
            index=axis,
            frame=_scaled_frame(seconds, fps, duration),
            group="Factory motion",
        )
    action = obj.animation_data.action
    if action is None:
        raise RuntimeError(f"Unable to create factory motion action for {obj.name}")
    action.name = f"{ACTION_PREFIX}{action_suffix}"
    action["sum_generated_action"] = True
    action["sum_animation_fps"] = fps
    action["sum_animation_duration_s"] = duration
    try:
        for curve in action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "BEZIER"
                point.handle_left_type = "AUTO_CLAMPED"
                point.handle_right_type = "AUTO_CLAMPED"
    except AttributeError:
        pass
    return action


def _build_overhead_gantry(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    fps: int,
    duration: float,
) -> dict[str, Any]:
    rail_x = 4.25
    rail_start = 4.0
    rail_end = 43.0
    rail_center = (rail_start + rail_end) * 0.5
    rail_length = rail_end - rail_start

    rails = _boxes(
        "SUM_V7_Gantry_TwinLongitudinalRails",
        (
            ((-rail_x, rail_center, 5.54), (0.24, rail_length, 0.32)),
            ((rail_x, rail_center, 5.54), (0.24, rail_length, 0.32)),
            ((-rail_x, rail_center, 5.35), (0.12, rail_length, 0.075)),
            ((rail_x, rail_center, 5.35), (0.12, rail_length, 0.075)),
        ),
        collection,
        parent=root,
        material=materials["factory_structure"],
        role="steel_blue",
        detail="twin_linear_transfer_gantry_rails",
        bevel=0.010,
    )
    supports = []
    y = rail_start + 1.0
    while y <= rail_end:
        for x in (-rail_x, rail_x):
            supports.append(((x, y, 6.70), (0.10, 0.10, 2.12)))
            supports.append(((x, y, 7.74), (0.66, 0.10, 0.10)))
        y += 7.5
    _boxes(
        "SUM_V7_Gantry_RoofHangers",
        supports,
        collection,
        parent=root,
        material=materials["factory_structure"],
        role="steel_blue",
        detail="roof_suspended_gantry_hangers",
        bevel=0.008,
    )

    bridge = modeling._empty(
        "SUM_V7_Gantry_MovingBridge",
        collection,
        location=(0.0, 8.8, 0.0),
        parent=root,
        display_size=0.22,
    )
    bridge["sum_asset_type"] = "servo_linear_gantry_moving_bridge"
    _box(
        "SUM_V7_Gantry_BridgeBeam",
        (8.92, 0.30, 0.40),
        collection,
        location=(0.0, 0.0, 5.40),
        parent=bridge,
        material=materials["factory_structure"],
        role="steel_blue",
        detail="boxed_gantry_cross_bridge",
        bevel=0.018,
    )
    _box(
        "SUM_V7_Gantry_BridgeLinearEncoder",
        (8.10, 0.045, 0.055),
        collection,
        location=(0.0, -0.18, 5.22),
        parent=bridge,
        material=materials["machined_steel"],
        role="brushed_metal",
        detail="gantry_cross_axis_absolute_linear_encoder",
        bevel=0.004,
    )
    end_trucks = []
    for side in (-1.0, 1.0):
        end_trucks.append(((side * rail_x, 0.0, 5.48), (0.58, 0.82, 0.34)))
    _boxes(
        "SUM_V7_Gantry_EndTrucks",
        end_trucks,
        collection,
        parent=bridge,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="gantry_servo_end_trucks",
        bevel=0.035,
    )
    for side in (-1.0, 1.0):
        for y_offset in (-0.24, 0.24):
            _cylinder(
                f"SUM_V7_Gantry_TravelWheel_{'L' if side < 0 else 'R'}_{'A' if y_offset < 0 else 'B'}",
                0.115,
                0.090,
                collection,
                location=(side * rail_x, y_offset, 5.30),
                rotation=(0.0, math.pi * 0.5, 0.0),
                parent=bridge,
                material=materials["black_oxide"],
                role="dark_metal",
                detail="flanged_gantry_rail_wheel",
                segments=32,
            )

    trolley = modeling._empty(
        "SUM_V7_Gantry_CrossTrolley",
        collection,
        location=(-3.45, 0.0, 0.0),
        parent=bridge,
        display_size=0.16,
    )
    trolley["sum_asset_type"] = "servo_cross_axis_transfer_trolley"
    _box(
        "SUM_V7_Gantry_CrossTrolleyHousing",
        (0.82, 0.72, 0.48),
        collection,
        location=(0.0, 0.0, 5.38),
        parent=trolley,
        material=materials["paint_graphite"],
        role="powder_coat",
        detail="sealed_cross_trolley_servo_housing",
        bevel=0.055,
    )
    _cylinder(
        "SUM_V7_Gantry_CrossTrolleyServo",
        0.16,
        0.34,
        collection,
        location=(0.0, -0.46, 5.42),
        rotation=(math.pi * 0.5, 0.0, 0.0),
        parent=trolley,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="cross_trolley_brake_servo_motor",
        segments=40,
    )

    lift = modeling._empty(
        "SUM_V7_Gantry_ZAxisCarriage",
        collection,
        parent=trolley,
        display_size=0.15,
    )
    lift["sum_asset_type"] = "telescopic_servo_z_axis"
    _box(
        "SUM_V7_Gantry_ZAxisOuterGuide",
        (0.34, 0.34, 1.74),
        collection,
        location=(0.0, 0.0, 4.50),
        parent=lift,
        material=materials["factory_structure"],
        role="steel_blue",
        detail="gantry_z_axis_outer_guide_column",
        bevel=0.025,
    )
    _box(
        "SUM_V7_Gantry_ZAxisInnerRam",
        (0.22, 0.22, 1.34),
        collection,
        location=(0.0, 0.0, 3.57),
        parent=lift,
        material=materials["machined_steel"],
        role="brushed_metal",
        detail="ground_gantry_z_axis_inner_ram",
        bevel=0.018,
    )
    _tube(
        "SUM_V7_Gantry_ZAxisDressPack",
        ((0.20, 0.0, 5.30), (0.42, 0.0, 4.72), (0.34, 0.0, 4.08), (0.18, 0.0, 3.48)),
        0.028,
        collection,
        parent=lift,
        material=materials["rubber"],
        role="rubber",
        detail="gantry_z_axis_power_air_and_sensor_dress_pack",
    )

    tilt_wrist = modeling._empty(
        "SUM_V7_Gantry_BrakedTiltWrist",
        collection,
        location=(0.0, 0.0, 3.42),
        parent=lift,
        display_size=0.10,
    )
    tilt_wrist["sum_asset_type"] = "braked_gantry_payload_orientation_axis"
    _cylinder(
        "SUM_V7_Gantry_TiltWristServo",
        0.16,
        0.30,
        collection,
        location=(0.0, 0.0, 0.0),
        rotation=(math.pi * 0.5, 0.0, 0.0),
        parent=tilt_wrist,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="braked_gantry_payload_tilt_servo",
        segments=40,
    )
    _boxes(
        "SUM_V7_Gantry_TiltWristYoke",
        (
            ((-0.20, 0.0, -0.05), (0.10, 0.34, 0.32)),
            ((0.20, 0.0, -0.05), (0.10, 0.34, 0.32)),
        ),
        collection,
        parent=tilt_wrist,
        material=materials["factory_structure"],
        role="steel_blue",
        detail="gantry_tilt_wrist_structural_yoke",
        bevel=0.018,
    )
    gripper = modeling._empty(
        "SUM_V7_Gantry_ThreeJawBearingGripper",
        collection,
        rotation=(0.0, math.radians(-72.0), 0.0),
        parent=tilt_wrist,
        display_size=0.10,
    )
    gripper["sum_asset_type"] = "three_jaw_centric_overhead_bearing_gripper"
    gripper["payload_tilt_degrees"] = -72.0
    gripper["payload_orientation"] = "near-vertical for horizontal machine spindle loading"
    _cylinder(
        "SUM_V7_Gantry_GripperRotaryFlange",
        0.18,
        0.16,
        collection,
        location=(0.0, 0.0, 0.0),
        parent=gripper,
        material=materials["machined_steel"],
        role="brushed_metal",
        detail="gantry_gripper_iso_rotary_flange",
        segments=48,
    )
    for index in range(3):
        angle = math.tau * index / 3.0
        radial = 0.20
        center = (math.cos(angle) * radial, math.sin(angle) * radial, -0.10)
        _box(
            f"SUM_V7_Gantry_GripperJawSlide_{index + 1:02d}",
            (0.20, 0.075, 0.085),
            collection,
            location=center,
            rotation=(0.0, 0.0, angle),
            parent=gripper,
            material=materials["brushed_steel"],
            role="brushed_metal",
            detail="three_jaw_gripper_radial_slide",
            bevel=0.012,
        )
        finger_center = (
            math.cos(angle) * 0.190,
            math.sin(angle) * 0.190,
            -0.24,
        )
        _box(
            f"SUM_V7_Gantry_GripperFinger_{index + 1:02d}",
            (0.065, 0.085, 0.30),
            collection,
            location=finger_center,
            rotation=(0.0, 0.0, angle),
            parent=gripper,
            material=materials["black_oxide"],
            role="dark_metal",
            detail="replaceable_three_jaw_gripper_finger",
            bevel=0.018,
        )
        pad_center = (
            math.cos(angle) * 0.162,
            math.sin(angle) * 0.162,
            -0.31,
        )
        _box(
            f"SUM_V7_Gantry_GripperCompliantPad_{index + 1:02d}",
            (0.032, 0.070, 0.105),
            collection,
            location=pad_center,
            rotation=(0.0, 0.0, angle),
            parent=gripper,
            material=materials["rubber"],
            role="rubber",
            detail="replaceable_nonmarking_three_jaw_grip_pad",
            bevel=0.010,
        )
    payload = modeling._annular_prism(
        "SUM_V7_Gantry_CarriedBearingOuterRing",
        0.145,
        0.085,
        0.060,
        collection,
        location=(0.0, 0.0, -0.36),
        parent=gripper,
        material=materials["machined_steel"],
        segments=112,
        bevel=0.004,
        role="gantry_carried_bearing_outer_ring",
    )
    _tag(payload, "brushed_metal", "gantry_carried_pregrind_bearing_outer_ring")
    payload["manufacturing_state"] = "heat-treated outer ring awaiting internal raceway grind"
    payload["nominal_outer_diameter_mm"] = 290
    payload["nominal_bore_diameter_mm"] = 170
    payload["nominal_width_mm"] = 60

    actions = {
        "bridge": _key_axis(
            bridge,
            1,
            "GantryBridgeTravel",
            ((0.0, 8.8), (3.75, 9.4), (7.0, 12.0), (9.0, 16.0), (12.5, 25.3), (15.0, 30.0), (20.0, 36.0), (38.0, 36.0)),
            fps,
            duration,
        ),
        "cross_trolley": _key_axis(
            trolley,
            0,
            "GantryCrossTrolley",
            ((0.0, -3.45), (3.75, -3.55), (7.0, -3.55), (8.6, -2.8), (10.2, 0.0), (12.5, 3.55), (15.0, 3.45), (38.0, 3.45)),
            fps,
            duration,
        ),
        "z_axis": _key_axis(
            lift,
            2,
            "GantryZAxis",
            ((0.0, 0.0), (3.2, -0.95), (7.8, -0.95), (9.4, 0.0), (11.6, 0.0), (12.2, -0.30), (13.2, -0.30), (14.2, 0.0), (38.0, 0.0)),
            fps,
            duration,
        ),
    }
    bridge["motion_story"] = "bearing pickup, cross-aisle retract, grinder delivery, park"
    bridge["central_crossing_payload_clearance_m"] = 3.02
    return {
        "rails": rails,
        "bridge": bridge,
        "trolley": trolley,
        "z_axis": lift,
        "tilt_wrist": tilt_wrist,
        "gripper": gripper,
        "payload": payload,
        "actions": actions,
    }


def augment_factory_systems(
    assets: dict[str, Any],
    *,
    fps: int = 24,
    duration: float = REFERENCE_DURATION,
) -> dict[str, Any]:
    """Add production machine, utility, and overhead-transfer detail."""

    if not isinstance(assets, dict):
        raise TypeError("assets must be a dictionary")
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        raise ValueError("fps must be a positive integer")
    if duration <= 0.0:
        raise ValueError("duration must be positive")
    root_collection = assets.get("root_collection")
    layout_root = assets.get("layout_root")
    materials = assets.get("placeholder_materials")
    machine_bays = assets.get("mature_machine_bays", ())
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")
    if not isinstance(layout_root, bpy.types.Object):
        raise TypeError("assets must provide layout_root")
    if not isinstance(materials, dict):
        raise TypeError("assets must provide placeholder_materials")
    if not isinstance(machine_bays, (list, tuple)):
        raise TypeError("assets must provide mature_machine_bays")

    collection = _reset_collection(root_collection)
    root = modeling._empty(
        "SUM_ASSET_V7_FactorySystems",
        collection,
        parent=layout_root,
        display_size=0.55,
    )
    root["sum_asset_type"] = "integrated_factory_utilities_and_overhead_material_handling"
    root["central_service_aisle_policy"] = "no fixed geometry within x +/- 2.35 below 2.80 m"
    root["material_policy"] = "powder coat, galvanized structure, steel, rubber; safety yellow only at hazards"

    valid_bays = [bay for bay in machine_bays if isinstance(bay, bpy.types.Object)]
    for bay in valid_bays:
        _build_machine_service_face(bay, collection, materials)
    utilities = _build_grouped_utilities(root, collection, materials, valid_bays)
    gantry = _build_overhead_gantry(root, collection, materials, fps, float(duration))

    assets["factory_systems"] = root
    assets["factory_utilities"] = utilities
    assets["overhead_gantry"] = gantry
    assets["overhead_gantry_bridge"] = gantry["bridge"]
    assets["overhead_gantry_gripper"] = gantry["gripper"]
    assets["overhead_bearing_payload"] = gantry["payload"]
    assets.setdefault("collections", {})["factory_systems"] = collection
    bpy.context.scene["v7_factory_systems"] = (
        "detailed machine service faces, grouped utilities, animated bearing gantry"
    )
    bpy.context.view_layer.update()
    return assets


__all__ = ["augment_factory_systems"]
