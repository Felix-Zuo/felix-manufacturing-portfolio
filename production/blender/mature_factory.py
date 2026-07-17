"""Production-detail factory augmentation for the V5 cinematic scene.

The original scene remains the mechanical and camera contract. This module
replaces its whitebox envelope with a clean, structurally coherent precision
factory that can be imported into Twinmotion as authored geometry.
"""

from __future__ import annotations

import math
from typing import Any, Iterable

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
    rotation: Vec3 = (0.0, 0.0, 0.0),
    bevel: float = 0.012,
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
    bevel: float = 0.008,
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
    segments: int = 24,
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


def _beam(
    name: str,
    start: Vec3,
    end: Vec3,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    role: str,
    detail: str,
    width: float,
    depth: float,
) -> bpy.types.Object:
    return _tag(
        modeling._tapered_link(
            name,
            start,
            end,
            width,
            width,
            depth,
            depth,
            collection,
            parent=parent,
            material=material,
            bevel=min(width, depth) * 0.08,
            role=detail,
        ),
        role,
        detail,
    )


def _hide_object_tree(root: object) -> None:
    if not isinstance(root, bpy.types.Object):
        return
    for obj in bpy.context.scene.objects:
        cursor = obj
        while cursor is not None:
            if cursor is root:
                obj.hide_render = True
                obj["sum_export_exclude"] = True
                break
            cursor = cursor.parent


def _hide_whitebox_conflicts(assets: dict[str, Any]) -> None:
    _hide_object_tree(assets.get("dual_rail_guide"))
    for name in (
        "SUM_Factory_Repeated_StructuralPortalFrames",
        "SUM_Factory_Portal_BasePlates",
        "SUM_Factory_Portal_AnchorBolts",
        "SUM_Factory_Entrance_ClearanceScaleMarkers",
        "SUM_Factory_Left_UpperWall_Panels",
        "SUM_Factory_Right_UpperWall_Panels",
        "SUM_Factory_White_RoofPanels",
        "SUM_Factory_Longitudinal_LuminaireCarrierChannels",
        "SUM_Factory_Longitudinal_LuminaireDiffusers",
        "SUM_Factory_RobotCell_GuardFence_Frame",
        "SUM_Factory_RobotCell_GuardFence_Panels",
    ):
        obj = bpy.data.objects.get(name)
        if isinstance(obj, bpy.types.Object):
            obj.hide_render = True
            obj["sum_export_exclude"] = True


def _build_floor_and_routes(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    *,
    floor_start: float,
    floor_end: float,
) -> None:
    length = floor_end - floor_start
    center_y = (floor_start + floor_end) * 0.5
    _box(
        "SUM_MatureFactory_SealedEpoxyFloor",
        (18.0, length, 0.12),
        collection,
        location=(0.0, center_y, -0.03),
        parent=root,
        material=materials["factory_floor"],
        role="floor",
        detail="sealed_light_gray_epoxy_floor",
        bevel=0.006,
    )

    joints = []
    joint_y = floor_start + 6.0
    while joint_y < floor_end:
        joints.append(((0.0, joint_y, 0.035), (17.7, 0.022, 0.006)))
        joint_y += 12.0
    _boxes(
        "SUM_MatureFactory_InlaidExpansionJoints",
        joints,
        collection,
        parent=root,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="flush_inlaid_floor_expansion_joints",
        bevel=0.001,
    )

    route = [
        ((-1.92, center_y, 0.041), (0.075, length - 1.0, 0.008)),
        ((1.92, center_y, 0.041), (0.075, length - 1.0, 0.008)),
    ]
    for y in (2.0, 10.5, 23.0, 34.5):
        route.append(((0.0, y, 0.042), (3.84, 0.07, 0.008)))
    for y in range(4, 142, 8):
        route.extend(
            (
                ((-1.62, float(y), 0.043), (0.42, 0.075, 0.009)),
                ((1.62, float(y), 0.043), (0.42, 0.075, 0.009)),
            )
        )
    _boxes(
        "SUM_MatureFactory_PaintedAGVRoute",
        route,
        collection,
        parent=root,
        material=materials["safety_yellow"],
        role="safety_yellow",
        detail="flush_safety_yellow_agv_route_markings",
        bevel=0.001,
    )


def _roof_height(x: float) -> float:
    return 8.35 - abs(x) * 0.105


def _build_structural_hall(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    *,
    floor_start: float,
    floor_end: float,
) -> None:
    length = floor_end - floor_start
    center_y = (floor_start + floor_end) * 0.5
    structure = materials["factory_structure"]
    wall = materials["factory_wall"]
    glass = materials["safety_glass"]

    portal_positions: list[float] = []
    y = -8.0
    while y <= floor_end - 1.0:
        portal_positions.append(y)
        y += 8.0

    columns = []
    bases = []
    for y in portal_positions:
        for x in (-8.45, 8.45):
            columns.append(((x, y, 3.65), (0.30, 0.38, 7.30)))
            bases.append(((x, y, 0.045), (0.64, 0.72, 0.09)))
    _boxes(
        "SUM_MatureFactory_PortalColumns",
        columns,
        collection,
        parent=root,
        material=structure,
        role="steel_blue",
        detail="galvanized_load_bearing_portal_columns",
        bevel=0.016,
    )
    _boxes(
        "SUM_MatureFactory_ColumnBasePlates",
        bases,
        collection,
        parent=root,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="anchored_column_base_plates",
        bevel=0.010,
    )

    for index, y in enumerate(portal_positions, start=1):
        _beam(
            f"SUM_MatureFactory_Truss_{index:02d}_LeftRafter",
            (-8.45, y, 7.30),
            (0.0, y, 8.35),
            collection,
            parent=root,
            material=structure,
            role="steel_blue",
            detail="pitched_portal_rafter",
            width=0.24,
            depth=0.30,
        )
        _beam(
            f"SUM_MatureFactory_Truss_{index:02d}_RightRafter",
            (0.0, y, 8.35),
            (8.45, y, 7.30),
            collection,
            parent=root,
            material=structure,
            role="steel_blue",
            detail="pitched_portal_rafter",
            width=0.24,
            depth=0.30,
        )
        _beam(
            f"SUM_MatureFactory_Truss_{index:02d}_BottomChord",
            (-8.10, y, 7.03),
            (8.10, y, 7.03),
            collection,
            parent=root,
            material=structure,
            role="steel_blue",
            detail="roof_truss_bottom_chord",
            width=0.15,
            depth=0.20,
        )
        for x0, x1 in ((-8.0, -4.0), (-4.0, 0.0), (0.0, 4.0), (4.0, 8.0)):
            _beam(
                f"SUM_MatureFactory_Truss_{index:02d}_Web_{x0:+.0f}",
                (x0, y, 7.04),
                (x1, y, _roof_height(x1) - 0.10),
                collection,
                parent=root,
                material=structure,
                role="steel_blue",
                detail="roof_truss_diagonal_web",
                width=0.10,
                depth=0.13,
            )

    roof_angle = math.atan2(1.05, 8.45)
    _box(
        "SUM_MatureFactory_LeftInsulatedRoof",
        (7.25, length, 0.12),
        collection,
        location=(-4.75, center_y, 7.78),
        rotation=(0.0, -roof_angle, 0.0),
        parent=root,
        material=wall,
        role="architecture",
        detail="bright_insulated_roof_panel_system",
        bevel=0.008,
    )
    _box(
        "SUM_MatureFactory_RightInsulatedRoof",
        (7.25, length, 0.12),
        collection,
        location=(4.75, center_y, 7.78),
        rotation=(0.0, roof_angle, 0.0),
        parent=root,
        material=wall,
        role="architecture",
        detail="bright_insulated_roof_panel_system",
        bevel=0.008,
    )
    _box(
        "SUM_MatureFactory_CentralSkylight",
        (2.40, length - 0.8, 0.055),
        collection,
        location=(0.0, center_y, 8.31),
        parent=root,
        material=glass,
        role="safety_glass",
        detail="continuous_daylight_skylight",
        bevel=0.004,
    )

    purlins = []
    for x in (-7.2, -4.8, -2.4, 2.4, 4.8, 7.2):
        purlins.append(((x, center_y, _roof_height(x) - 0.16), (0.16, length - 0.5, 0.14)))
    _boxes(
        "SUM_MatureFactory_LongitudinalRoofPurlins",
        purlins,
        collection,
        parent=root,
        material=structure,
        role="steel_blue",
        detail="longitudinal_roof_purlins",
        bevel=0.010,
    )

    for side, x in (("Left", -8.87), ("Right", 8.87)):
        _box(
            f"SUM_MatureFactory_{side}LowerWall",
            (0.12, length, 3.95),
            collection,
            location=(x, center_y, 1.98),
            parent=root,
            material=wall,
            role="architecture",
            detail="clean_insulated_lower_wall_panels",
            bevel=0.008,
        )
        _box(
            f"SUM_MatureFactory_{side}ClerestoryGlass",
            (0.07, length - 0.8, 2.35),
            collection,
            location=(x - math.copysign(0.02, x), center_y, 5.18),
            parent=root,
            material=glass,
            role="safety_glass",
            detail="continuous_clerestory_daylight_glazing",
            bevel=0.004,
        )
    mullions = []
    for y in portal_positions:
        for x in (-8.82, 8.82):
            mullions.extend(
                (
                    ((x, y, 5.18), (0.10, 0.11, 2.36)),
                    ((x, y, 4.02), (0.13, 0.18, 0.13)),
                    ((x, y, 6.34), (0.13, 0.18, 0.13)),
                )
            )
    _boxes(
        "SUM_MatureFactory_ClerestoryMullions",
        mullions,
        collection,
        parent=root,
        material=structure,
        role="steel_blue",
        detail="clerestory_structural_mullions",
        bevel=0.006,
    )

    luminaires = []
    diffusers = []
    for y in portal_positions:
        for x in (-2.85, 2.85):
            luminaires.append(((x, y + 3.7, 6.82), (0.22, 5.55, 0.14)))
            diffusers.append(((x, y + 3.7, 6.73), (0.13, 5.30, 0.035)))
    _boxes(
        "SUM_MatureFactory_SegmentedLuminaireHousings",
        luminaires,
        collection,
        parent=root,
        material=structure,
        role="steel_blue",
        detail="segmented_linear_luminaire_housings",
        bevel=0.012,
    )
    _boxes(
        "SUM_MatureFactory_SegmentedLuminaireDiffusers",
        diffusers,
        collection,
        parent=root,
        material=materials["luminaire_diffuser"],
        role="luminaire",
        detail="neutral_white_segmented_luminaires",
        bevel=0.006,
    )

    for index, (x, z, radius) in enumerate(
        ((-7.55, 6.48, 0.085), (-7.18, 6.28, 0.070), (-6.84, 6.50, 0.055)),
        start=1,
    ):
        _tag(
            modeling._cylinder_between(
                f"SUM_MatureFactory_UtilityPipe_{index:02d}",
                (x, floor_start + 1.0, z),
                (x, floor_end - 1.0, z),
                radius,
                collection,
                parent=root,
                material=materials["brushed_steel"],
                segments=20,
                bevel=0.004,
                role="organized_overhead_utility_pipe",
            ),
            "brushed_metal",
            "organized_overhead_utility_pipe",
        )

    tray_boxes = [
        ((-6.20, center_y, 6.52), (0.055, length - 1.8, 0.24)),
        ((-5.66, center_y, 6.52), (0.055, length - 1.8, 0.24)),
    ]
    rung_y = floor_start + 1.5
    while rung_y < floor_end - 1.0:
        tray_boxes.append(((-5.93, rung_y, 6.40), (0.58, 0.05, 0.055)))
        rung_y += 1.25
    _boxes(
        "SUM_MatureFactory_OverheadCableTray",
        tray_boxes,
        collection,
        parent=root,
        material=materials["factory_structure"],
        role="steel_blue",
        detail="organized_overhead_cable_tray",
        bevel=0.005,
    )


def _build_machine_bay(
    index: int,
    side: int,
    travel_y: float,
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    side_name = "L" if side < 0 else "R"
    bay = modeling._empty(
        f"SUM_MatureFactory_MachineBay_{side_name}{index:02d}",
        collection,
        location=(0.0, travel_y, 0.0),
        parent=root,
        display_size=0.20,
    )
    bay["sum_asset_type"] = "enclosed_precision_machine_bay"
    bay["service_clearance_m"] = 0.85
    bay["lookdev_role"] = "powder_coat"

    center_x = side * 4.35
    inner_face = side * 2.43
    toward_aisle = -side
    shell = materials["factory_wall"]
    dark = materials["paint_graphite"]
    frame = materials["factory_structure"]

    _box(
        f"SUM_Machine_{side_name}{index:02d}_MainEnclosure",
        (3.75, 5.45, 3.55),
        collection,
        location=(center_x, 0.0, 1.79),
        parent=bay,
        material=shell,
        role="architecture",
        detail="clean_enclosed_precision_machine_shell",
        bevel=0.055,
    )
    _box(
        f"SUM_Machine_{side_name}{index:02d}_TopServiceCrown",
        (3.45, 4.95, 0.26),
        collection,
        location=(center_x, 0.0, 3.64),
        parent=bay,
        material=dark,
        role="powder_coat",
        detail="machine_service_crown",
        bevel=0.025,
    )
    _box(
        f"SUM_Machine_{side_name}{index:02d}_BasePlinth",
        (3.95, 5.60, 0.24),
        collection,
        location=(center_x, 0.0, 0.12),
        parent=bay,
        material=dark,
        role="dark_metal",
        detail="machine_vibration_isolation_plinth",
        bevel=0.024,
    )

    face_x = inner_face + toward_aisle * 0.025
    _box(
        f"SUM_Machine_{side_name}{index:02d}_DarkProcessCavity",
        (0.055, 2.25, 1.45),
        collection,
        location=(face_x, -0.50, 2.13),
        parent=bay,
        material=dark,
        role="dark_metal",
        detail="recessed_machine_process_cavity",
        bevel=0.010,
    )
    glass_x = face_x + toward_aisle * 0.035
    _box(
        f"SUM_Machine_{side_name}{index:02d}_SafetyWindow",
        (0.035, 2.12, 1.32),
        collection,
        location=(glass_x, -0.50, 2.13),
        parent=bay,
        material=materials["safety_glass"],
        role="safety_glass",
        detail="laminated_machine_safety_window",
        bevel=0.008,
    )
    trim_x = glass_x + toward_aisle * 0.025
    trim = [
        ((trim_x, -1.59, 2.13), (0.055, 0.065, 1.48)),
        ((trim_x, 0.59, 2.13), (0.055, 0.065, 1.48)),
        ((trim_x, -0.50, 2.84), (0.055, 2.25, 0.065)),
        ((trim_x, -0.50, 1.42), (0.055, 2.25, 0.065)),
    ]
    _boxes(
        f"SUM_Machine_{side_name}{index:02d}_WindowTrim",
        trim,
        collection,
        parent=bay,
        material=frame,
        role="steel_blue",
        detail="machine_window_structural_trim",
        bevel=0.006,
    )
    _box(
        f"SUM_Machine_{side_name}{index:02d}_WindowDripSill",
        (0.070, 2.32, 0.075),
        collection,
        location=(trim_x + toward_aisle * 0.008, -0.50, 1.34),
        parent=bay,
        material=materials["brushed_steel"],
        role="wet_steel",
        detail="stainless_machine_window_coolant_drip_sill",
        bevel=0.008,
    )

    service_reveals = [
        ((trim_x, -1.72, 0.84), (0.045, 0.020, 1.00)),
        ((trim_x, 0.72, 0.84), (0.045, 0.020, 1.00)),
        ((trim_x, -0.50, 0.34), (0.045, 2.42, 0.020)),
        ((trim_x, -0.50, 1.34), (0.045, 2.42, 0.020)),
    ]
    _boxes(
        f"SUM_Machine_{side_name}{index:02d}_LowerServicePanelReveals",
        service_reveals,
        collection,
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="machine_lower_service_panel_shadow_reveals",
        bevel=0.002,
    )

    _boxes(
        f"SUM_Machine_{side_name}{index:02d}_ServicePanelFasteners",
        [
            (
                (trim_x + toward_aisle * 0.014, y, z),
                (0.024, 0.035, 0.035),
            )
            for y in (-1.61, 0.61)
            for z in (0.47, 1.21)
        ],
        collection,
        parent=bay,
        material=materials["machined_steel"],
        role="machined_steel",
        detail="quarter_turn_machine_service_panel_fasteners",
        bevel=0.004,
    )

    hmi_x = inner_face + toward_aisle * 0.14
    _box(
        f"SUM_Machine_{side_name}{index:02d}_HMIHousing",
        (0.26, 0.78, 1.26),
        collection,
        location=(hmi_x, 1.65, 2.06),
        parent=bay,
        material=dark,
        role="powder_coat",
        detail="integrated_machine_hmi_housing",
        bevel=0.035,
    )
    _box(
        f"SUM_Machine_{side_name}{index:02d}_HMIScreen",
        (0.035, 0.60, 0.43),
        collection,
        location=(hmi_x + toward_aisle * 0.145, 1.65, 2.26),
        parent=bay,
        material=materials["screen_content"],
        role="screen_glass",
        detail="machine_hmi_display_glass",
        bevel=0.008,
    )
    _box(
        f"SUM_Machine_{side_name}{index:02d}_HMIMountingArm",
        (0.18, 0.16, 0.16),
        collection,
        location=(inner_face - toward_aisle * 0.01, 1.65, 2.04),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="short_rigid_machine_hmi_mounting_arm",
        bevel=0.025,
    )
    _cylinder(
        f"SUM_Machine_{side_name}{index:02d}_EmergencyStop",
        0.065,
        0.065,
        collection,
        location=(hmi_x + toward_aisle * 0.17, 1.65, 1.72),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["indicator_red"],
        role="amber_signal",
        detail="machine_emergency_stop",
        segments=20,
    )

    tower_x = side * 2.68
    tower_y = -2.08
    _cylinder(
        f"SUM_Machine_{side_name}{index:02d}_TowerMast",
        0.028,
        0.35,
        collection,
        location=(tower_x, tower_y, 3.86),
        parent=bay,
        material=frame,
        role="brushed_metal",
        detail="machine_status_tower_mast",
        segments=16,
    )
    for segment, (z, key) in enumerate(
        ((4.08, "indicator_green"), (4.20, "safety_amber")), start=1
    ):
        _cylinder(
            f"SUM_Machine_{side_name}{index:02d}_Tower_{segment:02d}",
            0.060,
            0.10,
            collection,
            location=(tower_x, tower_y, z),
            parent=bay,
            material=materials[key],
            role="amber_signal" if key == "safety_amber" else "luminaire",
            detail="machine_stack_status_light",
            segments=20,
        )

    boundary = [
        ((center_x, -2.92, 0.044), (4.35, 0.055, 0.009)),
        ((center_x, 2.92, 0.044), (4.35, 0.055, 0.009)),
        ((side * 2.16, 0.0, 0.044), (0.055, 5.88, 0.009)),
    ]
    _boxes(
        f"SUM_Machine_{side_name}{index:02d}_SafetyBoundary",
        boundary,
        collection,
        parent=bay,
        material=materials["safety_yellow"],
        role="safety_yellow",
        detail="machine_floor_safety_clearance_boundary",
        bevel=0.001,
    )
    return bay


def _build_command_screen_bay(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> tuple[bpy.types.Object, bpy.types.Object]:
    bay = modeling._empty(
        "SUM_MatureFactory_CommandScreenBay",
        collection,
        location=(0.0, 4.0, 0.0),
        parent=root,
        display_size=0.22,
    )
    bay["sum_asset_type"] = "aisle_integrated_project_display_machine"
    _box(
        "SUM_CommandBay_MainShell",
        (5.50, 6.50, 4.55),
        collection,
        location=(5.80, 0.0, 2.28),
        parent=bay,
        material=materials["factory_wall"],
        role="architecture",
        detail="integrated_command_machine_architecture",
        bevel=0.045,
    )
    _box(
        "SUM_CommandBay_GraphiteReveal",
        (0.18, 4.20, 2.75),
        collection,
        location=(3.00, 0.0, 2.65),
        parent=bay,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="deep_recessed_display_reveal",
        bevel=0.025,
    )
    display = modeling._display_surface(
        "SUM_CommandBay_ProjectDisplay",
        3.62,
        2.14,
        collection,
        location=(2.895, 0.0, 2.65),
        parent=bay,
        material=materials["screen_content"],
    )
    display.rotation_euler.z = math.pi
    _tag(display, "screen_glass", "recessed_large_project_display")
    trim = [
        ((2.86, -1.91, 2.65), (0.10, 0.10, 2.36)),
        ((2.86, 1.91, 2.65), (0.10, 0.10, 2.36)),
        ((2.86, 0.0, 3.78), (0.10, 3.92, 0.10)),
        ((2.86, 0.0, 1.52), (0.10, 3.92, 0.10)),
    ]
    _boxes(
        "SUM_CommandBay_DisplayFrame",
        trim,
        collection,
        parent=bay,
        material=materials["screen_frame"],
        role="dark_metal",
        detail="anodized_recessed_display_frame",
        bevel=0.008,
    )
    _box(
        "SUM_CommandBay_TopInspectionLight",
        (0.11, 4.20, 0.08),
        collection,
        location=(2.80, 0.0, 4.18),
        parent=bay,
        material=materials["luminaire_diffuser"],
        role="luminaire",
        detail="display_bay_integrated_inspection_light",
        bevel=0.006,
    )
    rail_boxes = [
        ((2.45, -2.63, 0.62), (0.10, 0.10, 1.02)),
        ((2.45, 2.63, 0.62), (0.10, 0.10, 1.02)),
        ((2.45, 0.0, 0.67), (0.10, 5.30, 0.10)),
        ((2.45, -2.63, 0.12), (0.62, 0.10, 0.10)),
        ((2.45, 2.63, 0.12), (0.62, 0.10, 0.10)),
    ]
    _boxes(
        "SUM_CommandBay_SafetyRail",
        rail_boxes,
        collection,
        parent=bay,
        material=materials["safety_yellow"],
        role="safety_yellow",
        detail="display_bay_machine_protection_rail",
        bevel=0.020,
    )
    return bay, display


def _mesh_panel_boxes(
    *,
    axis: str,
    fixed: float,
    start: float,
    end: float,
    height: float,
) -> list[tuple[Vec3, Vec3]]:
    boxes: list[tuple[Vec3, Vec3]] = []
    cursor = start + 0.18
    while cursor < end - 0.12:
        if axis == "y":
            boxes.append(((fixed, cursor, height * 0.5), (0.022, 0.022, height)))
        else:
            boxes.append(((cursor, fixed, height * 0.5), (0.022, 0.022, height)))
        cursor += 0.18
    z = 0.18
    while z < height - 0.10:
        if axis == "y":
            boxes.append(((fixed, (start + end) * 0.5, z), (0.024, end - start, 0.022)))
        else:
            boxes.append((((start + end) * 0.5, fixed, z), (end - start, 0.024, 0.022)))
        z += 0.18
    return boxes


def _build_robot_cell_fence(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    fence = modeling._empty(
        "SUM_MatureFactory_RobotCellFence",
        collection,
        parent=root,
        display_size=0.18,
    )
    fence["sum_asset_type"] = "robot_cell_machine_guarding"
    x_front = -1.95
    x_back = -7.10
    y_start = 4.5
    y_end = 16.5
    height = 2.25

    posts = []
    for y in (4.5, 6.7, 8.9, 9.8, 13.2, 14.3, 16.5):
        posts.append(((x_front, y, height * 0.5), (0.095, 0.095, height)))
    for x in (x_back, -5.35, -3.65):
        posts.extend(
            (
                ((x, y_start, height * 0.5), (0.095, 0.095, height)),
                ((x, y_end, height * 0.5), (0.095, 0.095, height)),
            )
        )
    _boxes(
        "SUM_RobotCell_SafetyYellowPosts",
        posts,
        collection,
        parent=fence,
        material=materials["safety_yellow"],
        role="safety_yellow",
        detail="safety_yellow_robot_guard_posts",
        bevel=0.010,
    )

    rails = [
        ((x_front, (y_start + y_end) * 0.5, z), (0.075, y_end - y_start, 0.075))
        for z in (0.10, height - 0.08)
    ]
    for y in (y_start, y_end):
        for z in (0.10, height - 0.08):
            rails.append((((x_front + x_back) * 0.5, y, z), (x_front - x_back, 0.075, 0.075)))
    _boxes(
        "SUM_RobotCell_BlackGuardRails",
        rails,
        collection,
        parent=fence,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="black_robot_guard_perimeter_rails",
        bevel=0.008,
    )

    mesh = _mesh_panel_boxes(
        axis="y", fixed=x_front, start=y_start, end=9.8, height=height
    )
    mesh.extend(
        _mesh_panel_boxes(axis="y", fixed=x_front, start=13.2, end=y_end, height=height)
    )
    mesh.extend(
        _mesh_panel_boxes(axis="x", fixed=y_start, start=x_back, end=x_front, height=height)
    )
    mesh.extend(
        _mesh_panel_boxes(axis="x", fixed=y_end, start=x_back, end=x_front, height=height)
    )
    _boxes(
        "SUM_RobotCell_WeldedWireMesh",
        mesh,
        collection,
        parent=fence,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="welded_wire_robot_safety_mesh",
        bevel=0.002,
    )

    _box(
        "SUM_RobotCell_DarkIsolationPad",
        (4.90, 10.55, 0.025),
        collection,
        location=(-4.53, 10.50, 0.030),
        parent=fence,
        material=materials["fixture"],
        role="floor",
        detail="robot_cell_isolation_floor_pad",
        bevel=0.004,
    )
    return fence


def _build_agv(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    agv = modeling._empty(
        "SUM_MatureFactory_AGV07",
        collection,
        location=(0.0, 7.2, 0.0),
        parent=root,
        display_size=0.16,
    )
    agv["sum_asset_type"] = "low_profile_autonomous_mobile_robot"
    agv["vehicle_number"] = "07"
    agv["route"] = "painted_floor_route_no_raised_rail"
    agv["footprint_m"] = "1.32 x 1.74"
    agv["deck_height_m"] = 0.63
    agv["wheel_diameter_m"] = 0.34

    _box(
        "SUM_AGV07_LowerChassis",
        (1.32, 1.74, 0.27),
        collection,
        location=(0.0, 0.0, 0.20),
        parent=agv,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="agv_impact_resistant_lower_chassis",
        bevel=0.10,
    )
    _box(
        "SUM_AGV07_UpperDeck",
        (1.12, 1.38, 0.20),
        collection,
        location=(0.0, 0.02, 0.40),
        parent=agv,
        material=materials["enclosure_paint"],
        role="powder_coat",
        detail="agv_removable_upper_service_deck",
        bevel=0.08,
    )
    _box(
        "SUM_AGV07_PayloadCassette",
        (0.82, 0.92, 0.12),
        collection,
        location=(0.0, 0.02, 0.56),
        parent=agv,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="agv_precision_payload_cassette",
        bevel=0.035,
    )
    _box(
        "SUM_AGV07_CassetteRecess",
        (0.58, 0.68, 0.035),
        collection,
        location=(0.0, 0.02, 0.63),
        parent=agv,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="agv_payload_location_recess",
        bevel=0.015,
    )

    deck_reveals = [
        ((-0.565, 0.02, 0.505), (0.018, 1.28, 0.018)),
        ((0.565, 0.02, 0.505), (0.018, 1.28, 0.018)),
        ((0.0, -0.63, 0.505), (1.12, 0.018, 0.018)),
        ((0.0, 0.67, 0.505), (1.12, 0.018, 0.018)),
    ]
    _boxes(
        "SUM_AGV07_UpperDeckServiceReveals",
        deck_reveals,
        collection,
        parent=agv,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="agv_removable_deck_service_panel_reveals",
        bevel=0.002,
    )

    bumper_sections = [
        ((-0.39, -0.885, 0.25), (0.43, 0.055, 0.11)),
        ((0.39, -0.885, 0.25), (0.43, 0.055, 0.11)),
        ((-0.39, 0.885, 0.25), (0.43, 0.055, 0.11)),
        ((0.39, 0.885, 0.25), (0.43, 0.055, 0.11)),
    ]
    for x in (-0.675, 0.675):
        bumper_sections.extend(
            (
                ((x, -0.74, 0.25), (0.055, 0.16, 0.11)),
                ((x, 0.0, 0.25), (0.055, 0.24, 0.11)),
                ((x, 0.74, 0.25), (0.055, 0.16, 0.11)),
            )
        )
    _boxes(
        "SUM_AGV07_CompliantBumperBand",
        bumper_sections,
        collection,
        parent=agv,
        material=materials["rubber"],
        role="rubber",
        detail="segmented_compliant_agv_safety_bumper_band",
        bevel=0.018,
    )

    _boxes(
        "SUM_AGV07_WheelGuardHoods",
        [
            ((x, y, 0.355), (0.15, 0.42, 0.075))
            for x in (-0.61, 0.61)
            for y in (-0.48, 0.48)
        ],
        collection,
        parent=agv,
        material=materials["paint_graphite"],
        role="powder_coat",
        detail="agv_recessed_wheel_guard_hoods",
        bevel=0.025,
    )

    for wheel_index, (x, y) in enumerate(
        ((-0.61, -0.48), (0.61, -0.48), (-0.61, 0.48), (0.61, 0.48)),
        start=1,
    ):
        _cylinder(
            f"SUM_AGV07_ProtectedWheel_{wheel_index:02d}",
            0.17,
            0.13,
            collection,
            location=(x, y, 0.18),
            rotation=(0.0, math.pi * 0.5, 0.0),
            parent=agv,
            material=materials["rubber"],
            role="rubber",
            detail="agv_recessed_protected_drive_wheel",
            segments=28,
        )
        _cylinder(
            f"SUM_AGV07_WheelHub_{wheel_index:02d}",
            0.060,
            0.020,
            collection,
            location=(x + math.copysign(0.075, x), y, 0.18),
            rotation=(0.0, math.pi * 0.5, 0.0),
            parent=agv,
            material=materials["machined_steel"],
            role="machined_steel",
            detail="agv_sealed_drive_wheel_hub",
            segments=24,
        )

    locating_pins = modeling._prism_array(
        "SUM_AGV07_PayloadCassetteLocatingPins",
        [(x, y, 0.67) for x in (-0.31, 0.31) for y in (-0.35, 0.39)],
        0.018,
        0.045,
        12,
        collection,
        parent=agv,
        material=materials["machined_steel"],
        bevel=0.002,
        role="agv_payload_cassette_hardened_locating_pins",
    )
    _tag(
        locating_pins,
        "machined_steel",
        "agv_payload_cassette_hardened_locating_pins",
    )

    for end_index, y in enumerate((-0.88, 0.88), start=1):
        _cylinder(
            f"SUM_AGV07_SafetyScanner_{end_index:02d}",
            0.115,
            0.07,
            collection,
            location=(0.0, y, 0.22),
            rotation=(math.pi * 0.5, 0.0, 0.0),
            parent=agv,
            material=materials["screen_frame"],
            role="screen_glass",
            detail="agv_bidirectional_lidar_safety_scanner",
            segments=28,
        )
        _box(
            f"SUM_AGV07_LightStrip_{end_index:02d}",
            (0.70, 0.035, 0.045),
            collection,
            location=(0.0, y + math.copysign(0.02, y), 0.34),
            parent=agv,
            material=materials["indicator_green"],
            role="luminaire",
            detail="agv_directional_status_light_strip",
            bevel=0.012,
        )

    for corner_index, (x, y) in enumerate(
        ((-0.53, -0.76), (0.53, -0.76), (-0.53, 0.76), (0.53, 0.76)),
        start=1,
    ):
        _cylinder(
            f"SUM_AGV07_CornerSensor_{corner_index:02d}",
            0.040,
            0.045,
            collection,
            location=(x, y, 0.31),
            parent=agv,
            material=materials["safety_glass"],
            role="screen_glass",
            detail="agv_corner_proximity_sensor",
            segments=18,
        )

    label = modeling._text_label(
        "SUM_AGV07_NumberPlate",
        "07",
        0.18,
        collection,
        location=(0.0, -0.892, 0.25),
        rotation=(math.pi * 0.5, 0.0, 0.0),
        parent=agv,
        material=materials["factory_wall"],
        role="agv_fleet_number_plate",
    )
    _tag(label, "architecture", "agv_fleet_number_plate")
    return agv


def _recolor_staging_robot(assets: dict[str, Any]) -> None:
    robot = assets.get("robot_arm_6axis")
    if not isinstance(robot, bpy.types.Object):
        return
    white = assets["placeholder_materials"]["factory_wall"]
    dark = assets["placeholder_materials"]["black_oxide"]
    for obj in bpy.context.scene.objects:
        cursor = obj
        descendant = False
        while cursor is not None:
            if cursor is robot:
                descendant = True
                break
            cursor = cursor.parent
        if not descendant or obj.type != "MESH":
            continue
        lowered = obj.name.lower()
        if any(token in lowered for token in ("cable", "hose", "bolt", "fastener", "joint_axis")):
            obj.data.materials.clear()
            obj.data.materials.append(dark)
            obj["lookdev_role"] = "dark_metal"
        elif any(token in lowered for token in ("housing", "arm", "link", "shoulder", "wrist", "base")):
            obj.data.materials.clear()
            obj.data.materials.append(white)
            obj["lookdev_role"] = "architecture"


def augment_factory(assets: dict[str, Any]) -> dict[str, Any]:
    """Replace whitebox environment cues with the mature production factory."""

    root_collection = assets.get("root_collection")
    layout_root = assets.get("layout_root")
    materials = assets.get("placeholder_materials")
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")
    if not isinstance(layout_root, bpy.types.Object):
        raise TypeError("assets must provide layout_root")
    if not isinstance(materials, dict):
        raise TypeError("assets must provide placeholder_materials")

    _hide_whitebox_conflicts(assets)
    collection = modeling._child_collection(root_collection, "SUM_MODEL_MatureFactory")
    root = modeling._empty(
        "SUM_ASSET_MatureFactory",
        collection,
        parent=layout_root,
        display_size=0.70,
    )
    root["sum_asset_type"] = "production_ready_bright_precision_factory"
    root["design_reference"] = "production/v5/source-frames/s01-entry-clean.png"
    root["visual_hierarchy"] = "central aisle -> AGV -> robot cell -> machine row -> project display"
    root["structural_grid_m"] = 8.0
    root["hall_bounds_m"] = "18.0 x 163.0 x 8.35"

    floor_start = -14.0
    floor_end = 149.0
    _build_floor_and_routes(
        root, collection, materials, floor_start=floor_start, floor_end=floor_end
    )
    _build_structural_hall(
        root, collection, materials, floor_start=floor_start, floor_end=floor_end
    )
    command_bay, hero_screen = _build_command_screen_bay(root, collection, materials)
    robot_fence = _build_robot_cell_fence(root, collection, materials)
    agv = _build_agv(root, collection, materials)

    machine_bays: list[bpy.types.Object] = []
    left_positions = (30.0, 39.0, 48.0, 61.0, 70.0, 79.0, 88.0, 108.0, 117.0, 126.0, 135.0, 144.0)
    right_positions = (35.0, 44.0, 53.0, 62.0, 84.0, 93.0, 102.0, 111.0, 130.0, 139.0)
    for index, travel_y in enumerate(left_positions, start=1):
        machine_bays.append(
            _build_machine_bay(index, -1, travel_y, root, collection, materials)
        )
    for index, travel_y in enumerate(right_positions, start=1):
        machine_bays.append(
            _build_machine_bay(index, 1, travel_y, root, collection, materials)
        )

    _recolor_staging_robot(assets)
    assets["mature_factory"] = root
    assets["mature_factory_collection"] = collection
    assets["mature_machine_bays"] = machine_bays
    assets["command_screen_bay"] = command_bay
    assets["hero_screen"] = hero_screen
    assets["robot_cell_fence"] = robot_fence
    assets["agv"] = agv
    assets["agv_07"] = agv
    assets.setdefault("collections", {})["mature_factory"] = collection
    bpy.context.view_layer.update()
    return assets
