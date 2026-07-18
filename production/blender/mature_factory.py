"""Production-detail factory augmentation for the V5 cinematic scene.

The original scene remains the mechanical and camera contract. This module
replaces its whitebox envelope with a clean, structurally coherent precision
factory that can be imported into Twinmotion as authored geometry.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

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


def _profile_prism_y(
    name: str,
    profile_depth_z: Sequence[tuple[float, float]],
    side: int,
    inner_face: float,
    y_min: float,
    y_max: float,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    role: str,
    detail: str,
    open_front: bool = False,
    bevel: float = 0.025,
) -> bpy.types.Object:
    """Extrude an aisle-to-back X/Z machine profile along local travel Y."""

    profile = [(inner_face + side * depth, z) for depth, z in profile_depth_z]
    count = len(profile)
    vertices = [
        (x, y, z)
        for y in (y_min, y_max)
        for x, z in profile
    ]
    faces: list[tuple[int, ...]] = [
        tuple(reversed(range(count))),
        tuple(range(count, count * 2)),
    ]
    for index in range(count):
        next_index = (index + 1) % count
        if open_front and next_index == 0:
            continue
        faces.append(
            (
                index,
                next_index,
                next_index + count,
                index + count,
            )
        )
    return _tag(
        modeling._mesh_object(
            name,
            vertices,
            faces,
            collection,
            parent=parent,
            material=material,
            bevel=bevel,
            smooth=False,
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
    resolution: int = 8,
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
            resolution=resolution,
        ),
        role,
        detail,
    )


def _area_light(
    name: str,
    collection: bpy.types.Collection,
    *,
    location: Vec3,
    parent: bpy.types.Object,
    energy: float,
    size: float,
) -> bpy.types.Object:
    light_data = bpy.data.lights.new(f"{name}_Data", type="AREA")
    light_data.energy = energy
    light_data.color = (0.70, 0.82, 0.92)
    light_data.shape = "RECTANGLE"
    light_data.size = size
    light_data.size_y = 0.24
    light_data.use_shadow = True
    light = bpy.data.objects.new(name, light_data)
    collection.objects.link(light)
    light.parent = parent
    light.location = location
    light["sum_quality_level"] = "production"
    light["sum_design_detail"] = "shielded_machine_process_task_light"
    return light


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


def _build_machine_utility_drops(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    machine_positions: Sequence[tuple[int, float]],
) -> bpy.types.Object:
    """Connect the hall headers to machines with rigid, bracketed drops."""

    utilities = modeling._empty(
        "SUM_MatureFactory_MachineUtilityDrops",
        collection,
        parent=root,
        display_size=0.30,
    )
    utilities["sum_asset_type"] = "rigid_machine_air_coolant_and_power_distribution"

    for side in (-1, 1):
        side_name = "L" if side < 0 else "R"
        header_x = side * 6.92
        for label, z, radius, material, role, detail in (
            (
                "Air",
                5.42,
                0.034,
                materials["factory_structure"],
                "steel_blue",
                "painted_rigid_compressed_air_header",
            ),
            (
                "Coolant",
                5.20,
                0.042,
                materials["brushed_steel"],
                "brushed_metal",
                "stainless_central_coolant_supply_header",
            ),
        ):
            _tube(
                f"SUM_Utility_{side_name}_{label}Header",
                ((header_x, 24.0, z), (header_x, 148.0, z)),
                radius,
                collection,
                parent=utilities,
                material=material,
                role=role,
                detail=detail,
                resolution=4,
            )

        _box(
            f"SUM_Utility_{side_name}_CoveredCableTray",
            (0.34, 124.0, 0.16),
            collection,
            location=(side * 7.38, 86.0, 5.54),
            parent=utilities,
            material=materials["black_oxide"],
            role="dark_metal",
            detail="covered_overhead_machine_power_and_network_cable_tray",
            bevel=0.018,
        )

        _boxes(
            f"SUM_Utility_{side_name}_HeaderSupportBrackets",
            (
                ((side * 7.15, y, 5.38), (0.64, 0.075, 0.075))
                for y in range(26, 149, 8)
            ),
            collection,
            parent=utilities,
            material=materials["factory_structure"],
            role="steel_blue",
            detail="regular_overhead_utility_header_support_brackets",
            bevel=0.006,
        )

    for side, travel_y in machine_positions:
        side_name = "L" if side < 0 else "R"
        header_x = side * 6.92
        machine_x = side * 6.20
        coolant_y = travel_y - 0.11
        air_y = travel_y + 0.11
        drop = _tube(
            f"SUM_Utility_{side_name}_{travel_y:05.1f}_CoolantDrop",
            (
                (header_x, coolant_y, 5.20),
                (header_x, coolant_y, 4.30),
                (machine_x, coolant_y, 4.13),
                (machine_x, coolant_y, 4.04),
            ),
            0.020,
            collection,
            parent=utilities,
            material=materials["brushed_steel"],
            role="brushed_metal",
            detail="rigid_stainless_machine_coolant_service_drop",
            resolution=6,
        )
        drop["service_connection"] = "coolant header to enclosed machine roof manifold"
        air_drop = _tube(
            f"SUM_Utility_{side_name}_{travel_y:05.1f}_AirDrop",
            (
                (header_x, air_y, 5.42),
                (header_x, air_y, 4.48),
                (machine_x, air_y, 4.25),
                (machine_x, air_y, 4.04),
            ),
            0.015,
            collection,
            parent=utilities,
            material=materials["factory_structure"],
            role="steel_blue",
            detail="painted_rigid_machine_compressed_air_drop",
            resolution=6,
        )
        air_drop["service_connection"] = "air header to lockable roof manifold"

        _box(
            f"SUM_Utility_{side_name}_{travel_y:05.1f}_RoofManifoldBase",
            (0.42, 0.50, 0.12),
            collection,
            location=(machine_x, travel_y, 3.84),
            parent=utilities,
            material=materials["paint_graphite"],
            role="dark_metal",
            detail="machine_roof_service_manifold_mounting_plinth",
            bevel=0.018,
        )
        _box(
            f"SUM_Utility_{side_name}_{travel_y:05.1f}_RoofManifold",
            (0.30, 0.38, 0.16),
            collection,
            location=(machine_x, travel_y, 3.97),
            parent=utilities,
            material=materials["factory_structure"],
            role="steel_blue",
            detail="enclosed_machine_roof_air_and_coolant_manifold",
            bevel=0.020,
        )
        for label, branch_y, material, role in (
            ("Coolant", coolant_y, materials["brushed_steel"], "brushed_metal"),
            ("Air", air_y, materials["factory_structure"], "steel_blue"),
        ):
            _cylinder(
                f"SUM_Utility_{side_name}_{travel_y:05.1f}_{label}IsolationCollar",
                0.042,
                0.090,
                collection,
                location=(machine_x, branch_y, 4.035),
                parent=utilities,
                material=material,
                role=role,
                detail=f"lockable_{label.lower()}_isolation_connection",
                segments=20,
            )

        raceway_x = side * 7.18
        roof_entry_x = side * 6.18
        _box(
            f"SUM_Utility_{side_name}_{travel_y:05.1f}_CoveredCableDrop",
            (0.18, 0.22, 1.40),
            collection,
            location=(raceway_x, travel_y, 4.82),
            parent=utilities,
            material=materials["black_oxide"],
            role="dark_metal",
            detail="covered_vertical_machine_power_and_network_drop",
            bevel=0.014,
        )
        _box(
            f"SUM_Utility_{side_name}_{travel_y:05.1f}_RoofCableBridge",
            (abs(raceway_x - roof_entry_x), 0.22, 0.12),
            collection,
            location=((raceway_x + roof_entry_x) * 0.5, travel_y, 4.12),
            parent=utilities,
            material=materials["black_oxide"],
            role="dark_metal",
            detail="covered_rigid_machine_roof_cable_bridge",
            bevel=0.012,
        )
        _box(
            f"SUM_Utility_{side_name}_{travel_y:05.1f}_RoofCableBridgeSupport",
            (0.20, 0.24, 0.28),
            collection,
            location=(roof_entry_x, travel_y, 3.92),
            parent=utilities,
            material=materials["factory_structure"],
            role="steel_blue",
            detail="machine_roof_cable_bridge_support_and_gland_box",
            bevel=0.014,
        )
    return utilities


def _build_machine_process(
    prefix: str,
    family: str,
    service_sign: int,
    front_x: float,
    toward_aisle: int,
    window_y: float,
    window_width: float,
    bay: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    work_y = window_y - service_sign * 0.12
    work_z = 2.12

    _box(
        f"{prefix}_CoolantSwarfTray",
        (0.46, window_width - 0.18, 0.12),
        collection,
        location=(front_x - toward_aisle * 0.37, window_y, 1.45),
        parent=bay,
        material=materials["black_oxide"],
        role="wet_steel",
        detail="sloped_internal_coolant_and_swarf_collection_tray",
        bevel=0.016,
    )

    workhead = modeling._cylinder_between(
        f"{prefix}_WorkheadHousing",
        (front_x - toward_aisle * 0.62, work_y, work_z),
        (front_x - toward_aisle * 0.38, work_y, work_z),
        0.245,
        collection,
        parent=bay,
        material=materials["paint_graphite"],
        segments=40,
        bevel=0.012,
        role="horizontal_machine_workhead_housing",
    )
    _tag(workhead, "dark_metal", "horizontal_machine_workhead_housing")

    spindle = modeling._cylinder_between(
        f"{prefix}_WorkSpindleNose",
        (front_x - toward_aisle * 0.43, work_y, work_z),
        (front_x - toward_aisle * 0.25, work_y, work_z),
        0.095,
        collection,
        parent=bay,
        material=materials["machined_steel"],
        segments=40,
        bevel=0.005,
        role="precision_horizontal_work_spindle_nose",
    )
    _tag(spindle, "machined_steel", "precision_horizontal_work_spindle_nose")

    chuck = modeling._cylinder_between(
        f"{prefix}_ThreeJawChuck",
        (front_x - toward_aisle * 0.29, work_y, work_z),
        (front_x - toward_aisle * 0.20, work_y, work_z),
        0.185,
        collection,
        parent=bay,
        material=materials["black_oxide"],
        segments=48,
        bevel=0.007,
        role="compact_three_jaw_workholding_chuck",
    )
    _tag(chuck, "dark_metal", "compact_three_jaw_workholding_chuck")

    jaw_boxes = []
    for jaw_index in range(3):
        angle = math.tau * jaw_index / 3.0
        jaw_boxes.append(
            (
                (
                    front_x - toward_aisle * 0.175,
                    work_y + math.cos(angle) * 0.12,
                    work_z + math.sin(angle) * 0.12,
                ),
                (0.055, 0.070, 0.105),
            )
        )
    _boxes(
        f"{prefix}_ChuckJaws",
        jaw_boxes,
        collection,
        parent=bay,
        material=materials["machined_steel"],
        role="machined_steel",
        detail="three_jaw_chuck_gripping_blocks",
        bevel=0.005,
    )

    backup = modeling._annular_prism(
        f"{prefix}_WorkholdingBackupFlange",
        0.29,
        0.19,
        0.050,
        collection,
        location=(front_x - toward_aisle * 0.205, work_y, work_z),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["black_oxide"],
        segments=64,
        bevel=0.004,
        role="workholding_backup_flange",
    )
    _tag(backup, "dark_metal", "workholding_backup_flange")

    workpiece = modeling._annular_prism(
        f"{prefix}_ProcessRingFixture",
        0.255,
        0.155,
        0.070,
        collection,
        location=(front_x - toward_aisle * 0.155, work_y, work_z),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["machined_steel"],
        segments=72,
        bevel=0.004,
        role="horizontal_clamped_bearing_ring_workpiece",
    )
    _tag(workpiece, "workpiece_steel", "horizontal_clamped_bearing_ring_workpiece")

    if family == "raceway_grinder":
        wheel_y = work_y + service_sign * 0.065
        wheel_z = work_z + 0.015
        grinding_housing = modeling._cylinder_between(
            f"{prefix}_GrindingSpindleHousing",
            (front_x - toward_aisle * 0.48, wheel_y, wheel_z),
            (front_x - toward_aisle * 0.28, wheel_y, wheel_z),
            0.095,
            collection,
            parent=bay,
            material=materials["paint_graphite"],
            segments=36,
            bevel=0.009,
            role="compact_internal_grinding_spindle_housing",
        )
        _tag(
            grinding_housing,
            "dark_metal",
            "compact_internal_grinding_spindle_housing",
        )
        grinding_shaft = modeling._cylinder_between(
            f"{prefix}_GrindingSpindleShaft",
            (front_x - toward_aisle * 0.30, wheel_y, wheel_z),
            (front_x - toward_aisle * 0.13, wheel_y, wheel_z),
            0.020,
            collection,
            parent=bay,
            material=materials["machined_steel"],
            segments=28,
            bevel=0.002,
            role="internal_grinding_spindle_shaft",
        )
        _tag(
            grinding_shaft,
            "machined_steel",
            "internal_grinding_spindle_shaft",
        )
        grinding_wheel = modeling._cylinder_between(
            f"{prefix}_CBNGrindingWheel",
            (front_x - toward_aisle * 0.165, wheel_y, wheel_z),
            (front_x - toward_aisle * 0.125, wheel_y, wheel_z),
            0.072,
            collection,
            parent=bay,
            material=materials["machined_steel"],
            segments=48,
            bevel=0.002,
            role="profiled_internal_grinding_wheel",
        )
        _tag(grinding_wheel, "abrasive", "profiled_internal_grinding_wheel")
        _tube(
            f"{prefix}_InternalCoolantLine",
            (
                (front_x - toward_aisle * 0.50, window_y + service_sign * 0.46, 2.69),
                (front_x - toward_aisle * 0.37, window_y + service_sign * 0.34, 2.54),
                (front_x - toward_aisle * 0.24, wheel_y + service_sign * 0.10, 2.31),
                (front_x - toward_aisle * 0.15, wheel_y, wheel_z + 0.09),
            ),
            0.012,
            collection,
            parent=bay,
            material=materials["brushed_steel"],
            role="wet_steel",
            detail="shielded_grinding_coolant_supply_line",
        )
    else:
        turret_y = work_y + service_sign * 0.39
        turret_z = 1.91
        turret = modeling._cylinder_between(
            f"{prefix}_TurningToolTurret",
            (front_x - toward_aisle * 0.24, turret_y, turret_z),
            (front_x - toward_aisle * 0.13, turret_y, turret_z),
            0.19,
            collection,
            parent=bay,
            material=materials["black_oxide"],
            segments=40,
            bevel=0.008,
            role="compact_indexing_turning_tool_turret",
        )
        _tag(turret, "dark_metal", "compact_indexing_turning_tool_turret")
        tool_x = front_x - toward_aisle * 0.105
        _boxes(
            f"{prefix}_TurningToolBlocks",
            (
                ((tool_x, turret_y - 0.17, turret_z), (0.055, 0.22, 0.070)),
                ((tool_x, turret_y + 0.17, turret_z), (0.055, 0.22, 0.070)),
                ((tool_x, turret_y, turret_z - 0.17), (0.055, 0.070, 0.22)),
                ((tool_x, turret_y, turret_z + 0.17), (0.055, 0.070, 0.22)),
            ),
            collection,
            parent=bay,
            material=materials["machined_steel"],
            role="machined_steel",
            detail="indexed_turning_toolholders",
            bevel=0.004,
        )
        _beam(
            f"{prefix}_ActiveTurningTool",
            (tool_x, turret_y - service_sign * 0.08, turret_z + 0.08),
            (tool_x, work_y + service_sign * 0.19, work_z - 0.02),
            collection,
            parent=bay,
            material=materials["machined_steel"],
            role="machined_steel",
            detail="active_turning_toolholder_and_insert",
            width=0.065,
            depth=0.050,
        )


def _build_machine_controls_and_services(
    prefix: str,
    service_sign: int,
    front_x: float,
    center_x: float,
    toward_aisle: int,
    bay: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    *,
    family: str,
    variant: int,
) -> None:
    service_y = service_sign * 1.67
    panel_y = service_y - service_sign * 0.10
    panel_x = front_x + toward_aisle * 0.12
    mount = (front_x - toward_aisle * 0.035, service_y, 2.48)
    elbow = (front_x + toward_aisle * 0.055, panel_y, 2.48)
    console_width = 0.76 if family == "raceway_grinder" else 0.70
    console_height = 1.10 if variant != 3 else 1.02
    screen_width = console_width - 0.18
    screen_height = 0.39 if family == "raceway_grinder" else 0.36

    _box(
        f"{prefix}_HMIWallPivot",
        (0.14, 0.24, 0.30),
        collection,
        location=mount,
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="sealed_hmi_wall_pivot_base",
        bevel=0.025,
    )
    _beam(
        f"{prefix}_HMIMountingArm",
        mount,
        elbow,
        collection,
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="short_articulated_hmi_support_arm",
        width=0.12,
        depth=0.10,
    )
    _cylinder(
        f"{prefix}_HMIArticulationJoint",
        0.085,
        0.13,
        collection,
        location=elbow,
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="hmi_articulation_joint",
        segments=24,
    )
    _box(
        f"{prefix}_HMIHousing",
        (0.20, console_width, console_height),
        collection,
        location=(panel_x, panel_y, 2.28),
        parent=bay,
        material=materials["paint_graphite"],
        role="powder_coat",
        detail="articulated_sealed_machine_control_console",
        bevel=0.035,
    )
    screen_x = panel_x + toward_aisle * 0.112
    _box(
        f"{prefix}_HMIScreen",
        (0.030, screen_width, screen_height),
        collection,
        location=(screen_x, panel_y, 2.48),
        parent=bay,
        material=materials["screen_content"],
        role="screen_glass",
        detail="machine_hmi_display_glass",
        bevel=0.008,
    )
    bezel_x = screen_x + toward_aisle * 0.020
    bezel_y = screen_width * 0.5 + 0.026
    bezel_z = screen_height * 0.5 + 0.026
    _boxes(
        f"{prefix}_HMIScreenRetainingBezel",
        (
            ((bezel_x, panel_y - bezel_y, 2.48), (0.020, 0.036, screen_height + 0.09)),
            ((bezel_x, panel_y + bezel_y, 2.48), (0.020, 0.036, screen_height + 0.09)),
            ((bezel_x, panel_y, 2.48 - bezel_z), (0.020, screen_width + 0.09, 0.036)),
            ((bezel_x, panel_y, 2.48 + bezel_z), (0.020, screen_width + 0.09, 0.036)),
        ),
        collection,
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="replaceable_hmi_screen_retaining_bezel",
        bevel=0.004,
    )
    _box(
        f"{prefix}_HMIHardkeyPanel",
        (0.018, console_width - 0.13, 0.24),
        collection,
        location=(bezel_x, panel_y, 2.06),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="sealed_hmi_hardkey_panel",
        bevel=0.012,
    )
    keypad = []
    row_count = 2 if family == "raceway_grinder" else 3
    column_count = 4 if family == "raceway_grinder" else 3
    for row in range(row_count):
        for column in range(column_count):
            keypad.append(
                (
                    (
                        bezel_x + toward_aisle * 0.012,
                        panel_y + (column - (column_count - 1) * 0.5) * 0.13,
                        2.105 - row * 0.080,
                    ),
                    (0.020, 0.052, 0.040),
                )
            )
    _boxes(
        f"{prefix}_HMIKeypadButtons",
        keypad,
        collection,
        parent=bay,
        material=materials["machined_steel"],
        role="machined_steel",
        detail="sealed_industrial_hmi_keypad_buttons",
        bevel=0.005,
    )
    _cylinder(
        f"{prefix}_EmergencyStopGuardCollar",
        0.074,
        0.035,
        collection,
        location=(screen_x + toward_aisle * 0.010, panel_y + service_sign * 0.20, 1.83),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="emergency_stop_protective_guard_collar",
        segments=24,
    )
    _cylinder(
        f"{prefix}_EmergencyStop",
        0.052,
        0.055,
        collection,
        location=(screen_x + toward_aisle * 0.045, panel_y + service_sign * 0.20, 1.83),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["indicator_red"],
        role="amber_signal",
        detail="machine_emergency_stop",
        segments=20,
    )
    _cylinder(
        f"{prefix}_CycleStartCollar",
        0.052,
        0.035,
        collection,
        location=(screen_x + toward_aisle * 0.010, panel_y - service_sign * 0.20, 1.83),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="cycle_start_pushbutton_collar",
        segments=20,
    )
    _cylinder(
        f"{prefix}_CycleStartButton",
        0.036,
        0.048,
        collection,
        location=(screen_x + toward_aisle * 0.040, panel_y - service_sign * 0.20, 1.83),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["indicator_green"],
        role="luminaire",
        detail="illuminated_machine_cycle_start_button",
        segments=20,
    )
    _cylinder(
        f"{prefix}_ModeSelector",
        0.038,
        0.045,
        collection,
        location=(screen_x + toward_aisle * 0.035, panel_y, 1.83),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["machined_steel"],
        role="machined_steel",
        detail="keyed_machine_mode_selector_switch",
        segments=20,
    )
    _box(
        f"{prefix}_HMIModelAccent",
        (0.020, console_width - 0.10, 0.040),
        collection,
        location=(bezel_x, panel_y, 2.28 + console_height * 0.5 - 0.025),
        parent=bay,
        material=(
            materials["factory_structure"]
            if family == "raceway_grinder"
            else materials["brushed_steel"]
        ),
        role="steel_blue" if family == "raceway_grinder" else "brushed_metal",
        detail="machine_family_hmi_identification_accent",
        bevel=0.006,
    )

    filter_x = front_x + toward_aisle * 0.035
    _box(
        f"{prefix}_FilteredVentBacking",
        (0.070, 0.94, 0.64),
        collection,
        location=(filter_x, service_y, 0.78),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="electrical_cabinet_filter_housing",
        bevel=0.018,
    )
    _boxes(
        f"{prefix}_FilteredVentSlats",
        (
            (
                (filter_x + toward_aisle * 0.045, service_y, 0.55 + slot * 0.085),
                (0.025, 0.72, 0.030),
            )
            for slot in range(6 + variant % 2)
        ),
        collection,
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="replaceable_filtered_vent_louvers",
        bevel=0.003,
    )

    disconnect_x = front_x + toward_aisle * 0.055
    _box(
        f"{prefix}_MainDisconnectBacking",
        (0.060, 0.32, 0.24),
        collection,
        location=(disconnect_x, service_y, 1.29),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="lockable_machine_main_disconnect_backplate",
        bevel=0.012,
    )
    _box(
        f"{prefix}_MainDisconnectHandle",
        (0.070, 0.055, 0.15),
        collection,
        location=(disconnect_x + toward_aisle * 0.050, service_y, 1.29),
        parent=bay,
        material=materials["safety_yellow"],
        role="safety_yellow",
        detail="lockable_machine_main_disconnect_handle",
        bevel=0.012,
    )

    utility_y = service_sign * 2.665
    raceway_x = front_x - toward_aisle * 2.78
    _box(
        f"{prefix}_ElectricalCableRaceway",
        (0.18, 0.075, 2.30),
        collection,
        location=(raceway_x, utility_y, 1.70),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="covered_vertical_machine_electrical_raceway",
        bevel=0.012,
    )
    service_air_line = _tube(
        f"{prefix}_ServiceAirLine",
        (
            (raceway_x + toward_aisle * 0.14, utility_y, 3.28),
            (front_x - toward_aisle * 1.76, utility_y, 3.10),
            (front_x - toward_aisle * 1.15, utility_y, 2.20),
            (front_x - toward_aisle * 0.72, utility_y, 1.52),
        ),
        0.014,
        collection,
        parent=bay,
        material=materials["rubber"],
        role="rubber",
        detail="secured_machine_service_air_line",
    )
    service_air_line.hide_render = True
    service_air_line["sum_visibility_policy"] = (
        "service-corridor routing; excluded from aisle camera"
    )
    coolant_return = _tube(
        f"{prefix}_CoolantReturnLoop",
        (
            (front_x - toward_aisle * 0.48, utility_y, 1.30),
            (front_x - toward_aisle * 0.70, utility_y, 0.82),
            (front_x - toward_aisle * 1.55, utility_y, 0.43),
            (center_x, utility_y, 0.38),
        ),
        0.022,
        collection,
        parent=bay,
        material=materials["brushed_steel"],
        role="wet_steel",
        detail="rigid_machine_coolant_return_loop",
    )
    coolant_return.hide_render = True
    coolant_return["sum_visibility_policy"] = (
        "under-cabinet routing; excluded from aisle camera"
    )


def _build_machine_door_and_sheetmetal_details(
    prefix: str,
    variant: int,
    service_sign: int,
    front_x: float,
    toward_aisle: int,
    window_y: float,
    window_width: float,
    window_z: float,
    window_height: float,
    fixed_end_y: float,
    bay: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    """Add manufacturable door tracks, seals, seams, and service hardware."""

    visible_x = front_x + toward_aisle * 0.072
    gasket_x = front_x + toward_aisle * 0.044
    track_top_z = window_z + window_height * 0.5 + 0.135
    track_bottom_z = window_z - window_height * 0.5 - 0.105
    _boxes(
        f"{prefix}_SlidingDoorTracks",
        (
            ((visible_x, window_y, track_top_z), (0.064, window_width + 0.34, 0.055)),
            ((visible_x, window_y, track_bottom_z), (0.064, window_width + 0.34, 0.050)),
        ),
        collection,
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="enclosed_linear_sliding_door_tracks",
        bevel=0.006,
    )
    _boxes(
        f"{prefix}_SlidingDoorTrackCovers",
        (
            (
                (visible_x + toward_aisle * 0.026, window_y, track_top_z + 0.046),
                (0.034, window_width + 0.24, 0.040),
            ),
            (
                (visible_x + toward_aisle * 0.022, window_y, track_bottom_z - 0.040),
                (0.030, window_width + 0.20, 0.032),
            ),
        ),
        collection,
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="stainless_sliding_door_track_wear_covers",
        bevel=0.004,
    )
    _boxes(
        f"{prefix}_WindowPerimeterSeals",
        (
            (
                (gasket_x, window_y - window_width * 0.5 + 0.035, window_z),
                (0.028, 0.032, window_height - 0.13),
            ),
            (
                (gasket_x, window_y + window_width * 0.5 - 0.035, window_z),
                (0.028, 0.032, window_height - 0.13),
            ),
            (
                (gasket_x, window_y, window_z - window_height * 0.5 + 0.035),
                (0.028, window_width - 0.10, 0.032),
            ),
            (
                (gasket_x, window_y, window_z + window_height * 0.5 - 0.035),
                (0.028, window_width - 0.10, 0.032),
            ),
        ),
        collection,
        parent=bay,
        material=materials["rubber"],
        role="rubber",
        detail="continuous_laminated_window_coolant_seals",
        bevel=0.004,
    )
    end_stop_y = window_width * 0.5 + 0.145
    _boxes(
        f"{prefix}_SlidingDoorEndStops",
        (
            ((visible_x, window_y - end_stop_y, track_top_z), (0.080, 0.090, 0.115)),
            ((visible_x, window_y + end_stop_y, track_top_z), (0.080, 0.090, 0.115)),
            ((visible_x, window_y - end_stop_y, track_bottom_z), (0.075, 0.085, 0.095)),
            ((visible_x, window_y + end_stop_y, track_bottom_z), (0.075, 0.085, 0.095)),
        ),
        collection,
        parent=bay,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="adjustable_sliding_door_end_stops",
        bevel=0.010,
    )
    _boxes(
        f"{prefix}_FrontSheetMetalFoldSeams",
        (
            ((gasket_x, window_y, 0.335), (0.026, window_width + 0.18, 0.024)),
            ((gasket_x, window_y, 1.350), (0.026, window_width + 0.18, 0.024)),
            ((gasket_x, fixed_end_y, 0.335), (0.026, 0.62, 0.024)),
            ((gasket_x, fixed_end_y, 1.365), (0.026, 0.62, 0.024)),
        ),
        collection,
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="formed_sheet_metal_door_fold_and_panel_seams",
        bevel=0.002,
    )

    inspection_x = front_x + toward_aisle * 0.066
    inspection_width = 0.49 if variant in (0, 2) else 0.45
    _box(
        f"{prefix}_FrontInspectionDoorGasket",
        (0.028, inspection_width + 0.05, 0.74),
        collection,
        location=(inspection_x, fixed_end_y, 0.79),
        parent=bay,
        material=materials["rubber"],
        role="rubber",
        detail="sealed_front_service_inspection_door_gasket",
        bevel=0.010,
    )
    _box(
        f"{prefix}_FrontInspectionDoor",
        (0.028, inspection_width, 0.68),
        collection,
        location=(inspection_x + toward_aisle * 0.020, fixed_end_y, 0.79),
        parent=bay,
        material=materials["enclosure_paint"],
        role="powder_coat",
        detail="flush_hinged_front_service_inspection_door",
        bevel=0.008,
    )
    hinge_y = fixed_end_y - service_sign * (inspection_width * 0.42)
    for hinge_index, hinge_z in enumerate((0.60, 0.98), start=1):
        _cylinder(
            f"{prefix}_InspectionDoorHinge_{hinge_index:02d}",
            0.020,
            0.115,
            collection,
            location=(inspection_x + toward_aisle * 0.042, hinge_y, hinge_z),
            parent=bay,
            material=materials["black_oxide"],
            role="dark_metal",
            detail="sealed_service_door_hinge_barrel",
            segments=16,
        )
    latch_y = fixed_end_y + service_sign * (inspection_width * 0.35)
    _cylinder(
        f"{prefix}_InspectionDoorQuarterTurnLatch",
        0.030,
        0.030,
        collection,
        location=(inspection_x + toward_aisle * 0.050, latch_y, 0.79),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["machined_steel"],
        role="machined_steel",
        detail="quarter_turn_service_door_compression_latch",
        segments=20,
    )

    fastener_x = front_x + toward_aisle * 0.072
    fastener_positions = (
        (window_y - window_width * 0.42, 0.48),
        (window_y + window_width * 0.42, 0.48),
        (window_y - window_width * 0.42, 1.20),
        (window_y + window_width * 0.42, 1.20),
    )
    for fastener_index, (fastener_y, fastener_z) in enumerate(
        fastener_positions, start=1
    ):
        _cylinder(
            f"{prefix}_LowerDoorFastener_{fastener_index:02d}",
            0.016,
            0.020,
            collection,
            location=(fastener_x, fastener_y, fastener_z),
            rotation=(0.0, math.pi * 0.5, 0.0),
            parent=bay,
            material=materials["machined_steel"],
            role="machined_steel",
            detail="flush_sheet_metal_panel_fastener",
            segments=16,
        )

    interlock_y = window_y + service_sign * (window_width * 0.5 + 0.105)
    _box(
        f"{prefix}_DoorSafetyInterlock",
        (0.060, 0.12, 0.18),
        collection,
        location=(visible_x, interlock_y, 1.56),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="coded_sliding_door_safety_interlock",
        bevel=0.010,
    )
    _box(
        f"{prefix}_DoorSafetyNotice",
        (0.026, 0.18, 0.080),
        collection,
        location=(visible_x + toward_aisle * 0.040, interlock_y, 2.76),
        parent=bay,
        material=materials["safety_yellow"],
        role="safety_yellow",
        detail="restrained_machine_door_interlock_warning_marker",
        bevel=0.005,
    )


def _build_machine_fixture_and_service_details(
    prefix: str,
    variant: int,
    service_sign: int,
    front_x: float,
    toward_aisle: int,
    fixed_end_y: float,
    bay: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    """Add capped service points and a restrained changeover fixture tray."""

    interface_x = front_x + toward_aisle * 0.105
    interface_z = 0.58
    _box(
        f"{prefix}_ServiceInterfacePlate",
        (0.034, 0.44, 0.22),
        collection,
        location=(interface_x, fixed_end_y, interface_z),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="sealed_machine_pneumatic_and_coolant_service_interface_plate",
        bevel=0.010,
    )
    for port_index, (port_y, material, role, detail) in enumerate(
        (
            (
                fixed_end_y - service_sign * 0.11,
                materials["factory_structure"],
                "steel_blue",
                "capped_compressed_air_service_coupling",
            ),
            (
                fixed_end_y + service_sign * 0.11,
                materials["brushed_steel"],
                "brushed_metal",
                "capped_coolant_service_coupling",
            ),
        ),
        start=1,
    ):
        _cylinder(
            f"{prefix}_ServicePortCollar_{port_index:02d}",
            0.052,
            0.026,
            collection,
            location=(interface_x + toward_aisle * 0.026, port_y, interface_z),
            rotation=(0.0, math.pi * 0.5, 0.0),
            parent=bay,
            material=materials["rubber"],
            role="rubber",
            detail="sealed_service_port_mounting_collar",
            segments=20,
        )
        _cylinder(
            f"{prefix}_ServicePortCap_{port_index:02d}",
            0.038,
            0.048,
            collection,
            location=(interface_x + toward_aisle * 0.060, port_y, interface_z),
            rotation=(0.0, math.pi * 0.5, 0.0),
            parent=bay,
            material=material,
            role=role,
            detail=detail,
            segments=20,
        )

    if variant not in (0, 2):
        return

    tray_y = fixed_end_y - service_sign * 0.015
    tray_x = front_x + toward_aisle * 0.115
    tray_front_x = front_x + toward_aisle * 0.195
    tray_z = 1.17
    _box(
        f"{prefix}_ChangeoverFixtureTray",
        (0.18, 0.58, 0.045),
        collection,
        location=(tray_x, tray_y, tray_z),
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="fold_down_stainless_changeover_fixture_tray",
        bevel=0.008,
    )
    _boxes(
        f"{prefix}_FixtureTrayRaisedLips",
        (
            ((tray_front_x, tray_y, tray_z + 0.035), (0.028, 0.60, 0.070)),
            ((tray_x, tray_y - 0.29, tray_z + 0.026), (0.18, 0.025, 0.052)),
            ((tray_x, tray_y + 0.29, tray_z + 0.026), (0.18, 0.025, 0.052)),
        ),
        collection,
        parent=bay,
        material=materials["machined_steel"],
        role="machined_steel",
        detail="fixture_tray_formed_retention_lips",
        bevel=0.004,
    )
    for support_index, support_y in enumerate((tray_y - 0.22, tray_y + 0.22), start=1):
        _beam(
            f"{prefix}_FixtureTraySupport_{support_index:02d}",
            (front_x + toward_aisle * 0.055, support_y, 0.98),
            (tray_front_x, support_y, tray_z - 0.015),
            collection,
            parent=bay,
            material=materials["black_oxide"],
            role="dark_metal",
            detail="fold_down_fixture_tray_support_link",
            width=0.020,
            depth=0.020,
        )
    for locator_index, locator_y in enumerate((tray_y - 0.13, tray_y + 0.13), start=1):
        _cylinder(
            f"{prefix}_FixtureTrayLocator_{locator_index:02d}",
            0.034,
            0.018,
            collection,
            location=(tray_x, locator_y, tray_z + 0.032),
            parent=bay,
            material=materials["black_oxide"],
            role="dark_metal",
            detail="fixture_tray_hardened_locating_pocket",
            segments=20,
        )


def _build_machine_identity_details(
    prefix: str,
    side_name: str,
    index: int,
    service_sign: int,
    front_x: float,
    toward_aisle: int,
    bay: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    asset_id = modeling._text_label(
        f"{prefix}_AssetIdentificationText",
        f"{side_name}-{index:02d}",
        0.055,
        collection,
        location=(
            front_x + toward_aisle * 0.086,
            service_sign * 2.18,
            2.915,
        ),
        rotation=(0.0, toward_aisle * math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["black_oxide"],
        role="machine_asset_identification_text",
    )
    _tag(asset_id, "dark_metal", "restrained_machine_asset_identification_text")


def _build_machine_bay(
    index: int,
    side: int,
    travel_y: float,
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    side_name = "L" if side < 0 else "R"
    prefix = f"SUM_Machine_{side_name}{index:02d}"
    bay = modeling._empty(
        f"SUM_MatureFactory_MachineBay_{side_name}{index:02d}",
        collection,
        location=(0.0, travel_y, 0.0),
        parent=root,
        display_size=0.20,
    )

    variant = (index + (1 if side > 0 else 0)) % 4
    family = "compact_turning_center" if variant == 2 else "raceway_grinder"
    model_codes = (
        "RG 320",
        "RG 420",
        "TC 500",
        "RG 460",
    )
    service_sign = 1 if variant in (0, 3) else -1
    window_width = 1.94 if family == "compact_turning_center" else 2.14

    bay["sum_asset_type"] = "enclosed_precision_machine_bay"
    bay["service_clearance_m"] = 0.85
    bay["lookdev_role"] = "powder_coat"
    bay["machine_family"] = family
    bay["machine_model"] = model_codes[variant]
    bay["process_axis"] = "horizontal X axis facing central service aisle"
    bay["service_side_local_y"] = service_sign
    bay["machine_corridor_revision"] = "F228-production-machine-family-v3"

    center_x = side * 4.35
    inner_face = side * 2.43
    toward_aisle = -side
    front_x = inner_face + toward_aisle * 0.025
    shell = (
        materials["factory_wall"]
        if variant in (0, 3)
        else materials["enclosure_paint"]
    )
    dark = materials["paint_graphite"]
    frame = (
        materials["factory_structure"]
        if family == "raceway_grinder"
        else materials["black_oxide"]
    )

    shoulder_z = 3.29 + (0.05 if variant in (1, 3) else 0.0)
    _profile_prism_y(
        f"{prefix}_MainEnclosure",
        (
            (0.16, 0.29),
            (3.82, 0.29),
            (3.82, 3.55),
            (3.52, 3.78),
            (0.58, 3.78),
            (0.16, shoulder_z),
        ),
        side,
        inner_face,
        -2.62,
        2.62,
        collection,
        parent=bay,
        material=shell,
        role="powder_coat",
        detail="open_front_sloped_shoulder_precision_machine_shell",
        open_front=True,
        bevel=0.040,
    )
    _box(
        f"{prefix}_ModelFamilyFascia",
        (0.055, 4.76 - variant * 0.08, 0.105),
        collection,
        location=(front_x + toward_aisle * 0.050, 0.0, 3.20),
        parent=bay,
        material=(
            materials["black_oxide"]
            if family == "compact_turning_center"
            else materials["factory_structure"]
        ),
        role="dark_metal" if family == "compact_turning_center" else "steel_blue",
        detail="machine_family_material_identity_fascia",
        bevel=0.012,
    )
    _box(
        f"{prefix}_ServiceIdentificationPlate",
        (0.040, 0.42, 0.135),
        collection,
        location=(front_x + toward_aisle * 0.060, service_sign * 2.18, 2.92),
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="etched_machine_family_and_asset_identification_plate",
        bevel=0.008,
    )
    _box(
        f"{prefix}_BasePlinth",
        (3.98, 5.58, 0.24),
        collection,
        location=(center_x, 0.0, 0.19),
        parent=bay,
        material=dark,
        role="dark_metal",
        detail="machine_vibration_isolation_plinth_and_coolant_sump",
        bevel=0.024,
    )
    _boxes(
        f"{prefix}_LevelingFeet",
        (
            ((center_x + x_offset, y_offset, 0.085), (0.34, 0.42, 0.17))
            for x_offset in (-1.43, 1.43)
            for y_offset in (-2.18, 2.18)
        ),
        collection,
        parent=bay,
        material=materials["rubber"],
        role="rubber",
        detail="four_independent_machine_leveling_and_vibration_feet",
        bevel=0.025,
    )

    window_y = -service_sign * 0.53
    window_z = 2.18
    window_height = 1.36
    service_y = service_sign * 1.67
    fixed_end_y = -service_sign * 2.19

    _boxes(
        f"{prefix}_SegmentedFrontDoors",
        (
            ((front_x, window_y, 0.84), (0.11, window_width + 0.20, 1.02)),
            ((front_x, window_y, 3.11), (0.11, window_width + 0.20, 0.31)),
            ((front_x, service_y, 1.74), (0.11, 1.38, 2.80)),
            ((front_x, fixed_end_y, 1.74), (0.11, 0.68, 2.80)),
        ),
        collection,
        parent=bay,
        material=shell,
        role="powder_coat",
        detail="segmented_machine_sliding_door_and_service_cabinet_faces",
        bevel=0.018,
    )
    _boxes(
        f"{prefix}_FrontDoorShadowReveals",
        (
            ((front_x + toward_aisle * 0.018, -2.52, 1.78), (0.035, 0.040, 2.90)),
            ((front_x + toward_aisle * 0.018, 2.52, 1.78), (0.035, 0.040, 2.90)),
            (
                (front_x + toward_aisle * 0.018, service_y - service_sign * 0.75, 1.78),
                (0.035, 0.035, 2.88),
            ),
            (
                (front_x + toward_aisle * 0.018, fixed_end_y + service_sign * 0.43, 1.78),
                (0.035, 0.035, 2.88),
            ),
            ((front_x + toward_aisle * 0.018, 0.0, 3.31), (0.035, 4.95, 0.040)),
        ),
        collection,
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="intentional_segmented_door_and_shoulder_shadow_reveals",
        bevel=0.002,
    )

    cavity_back_x = front_x - toward_aisle * 0.63
    cavity_mid_x = (front_x + cavity_back_x) * 0.5
    _box(
        f"{prefix}_DarkProcessCavity",
        (0.075, window_width - 0.12, window_height - 0.10),
        collection,
        location=(cavity_back_x, window_y, window_z),
        parent=bay,
        material=dark,
        role="dark_metal",
        detail="deep_recessed_machine_process_cavity_backwall",
        bevel=0.010,
    )
    _boxes(
        f"{prefix}_DeepWindowReveals",
        (
            (
                (cavity_mid_x, window_y - window_width * 0.5, window_z),
                (0.56, 0.085, window_height + 0.08),
            ),
            (
                (cavity_mid_x, window_y + window_width * 0.5, window_z),
                (0.56, 0.085, window_height + 0.08),
            ),
            (
                (cavity_mid_x, window_y, window_z - window_height * 0.5),
                (0.56, window_width, 0.085),
            ),
            (
                (cavity_mid_x, window_y, window_z + window_height * 0.5),
                (0.56, window_width, 0.085),
            ),
        ),
        collection,
        parent=bay,
        material=materials["brushed_steel"],
        role="wet_steel",
        detail="deep_stainless_window_reveal_and_coolant_liner",
        bevel=0.008,
    )

    _build_machine_process(
        prefix,
        family,
        service_sign,
        front_x,
        toward_aisle,
        window_y,
        window_width,
        bay,
        collection,
        materials,
    )
    _box(
        f"{prefix}_ProcessTaskLightDiffuser",
        (0.060, window_width - 0.26, 0.045),
        collection,
        location=(front_x - toward_aisle * 0.26, window_y, 2.78),
        parent=bay,
        material=materials["luminaire_diffuser"],
        role="luminaire",
        detail="shielded_process_cavity_task_light_diffuser",
        bevel=0.008,
    )
    _area_light(
        f"{prefix}_ProcessTaskLight",
        collection,
        location=(front_x - toward_aisle * 0.26, window_y, 2.74),
        parent=bay,
        energy=62.0 if family == "raceway_grinder" else 52.0,
        size=window_width - 0.38,
    )

    glass_x = front_x + toward_aisle * 0.025
    _box(
        f"{prefix}_SafetyWindow",
        (0.025, window_width - 0.10, window_height - 0.08),
        collection,
        location=(glass_x, window_y, window_z),
        parent=bay,
        material=materials["safety_glass"],
        role="safety_glass",
        detail="recessed_laminated_machine_safety_window",
        bevel=0.006,
    )
    trim_x = front_x + toward_aisle * 0.055
    _boxes(
        f"{prefix}_WindowTrim",
        (
            (
                (trim_x, window_y - window_width * 0.5 - 0.045, window_z),
                (0.060, 0.085, window_height + 0.17),
            ),
            (
                (trim_x, window_y + window_width * 0.5 + 0.045, window_z),
                (0.060, 0.085, window_height + 0.17),
            ),
            (
                (trim_x, window_y, window_z - window_height * 0.5 - 0.045),
                (0.060, window_width + 0.17, 0.085),
            ),
            (
                (trim_x, window_y, window_z + window_height * 0.5 + 0.045),
                (0.060, window_width + 0.17, 0.085),
            ),
        ),
        collection,
        parent=bay,
        material=frame,
        role="steel_blue",
        detail="structural_safety_window_retaining_frame",
        bevel=0.007,
    )
    _box(
        f"{prefix}_WindowDripSill",
        (0.080, window_width + 0.26, 0.080),
        collection,
        location=(trim_x + toward_aisle * 0.010, window_y, 1.40),
        parent=bay,
        material=materials["brushed_steel"],
        role="wet_steel",
        detail="stainless_machine_window_coolant_drip_sill",
        bevel=0.008,
    )
    handle_y = window_y + service_sign * (window_width * 0.5 + 0.17)
    handle = modeling._cylinder_between(
        f"{prefix}_SlidingDoorHandle",
        (trim_x + toward_aisle * 0.030, handle_y, 1.72),
        (trim_x + toward_aisle * 0.030, handle_y, 2.44),
        0.025,
        collection,
        parent=bay,
        material=materials["brushed_steel"],
        segments=20,
        bevel=0.004,
        role="full_height_machine_sliding_door_handle",
    )
    _tag(handle, "brushed_metal", "full_height_machine_sliding_door_handle")

    _build_machine_door_and_sheetmetal_details(
        prefix,
        variant,
        service_sign,
        front_x,
        toward_aisle,
        window_y,
        window_width,
        window_z,
        window_height,
        fixed_end_y,
        bay,
        collection,
        materials,
    )
    _build_machine_fixture_and_service_details(
        prefix,
        variant,
        service_sign,
        front_x,
        toward_aisle,
        fixed_end_y,
        bay,
        collection,
        materials,
    )

    side_panel_x = inner_face + side * 2.02
    end_panels = []
    end_reveals = []
    for end_y in (-2.655, 2.655):
        end_panels.append(((side_panel_x, end_y, 1.60), (2.58, 0.055, 2.16)))
        for x_depth in (0.73, 3.31):
            end_reveals.append(
                (
                    (inner_face + side * x_depth, end_y - math.copysign(0.035, end_y), 1.60),
                    (0.030, 0.025, 2.17),
                )
            )
        for z in (0.52, 2.68):
            end_reveals.append(
                (
                    (side_panel_x, end_y - math.copysign(0.035, end_y), z),
                    (2.60, 0.025, 0.030),
                )
            )
    _boxes(
        f"{prefix}_EndServicePanels",
        end_panels,
        collection,
        parent=bay,
        material=shell,
        role="powder_coat",
        detail="flush_side_service_access_panels",
        bevel=0.012,
    )
    _boxes(
        f"{prefix}_EndServicePanelReveals",
        end_reveals,
        collection,
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="side_service_access_panel_shadow_reveals",
        bevel=0.002,
    )
    end_panel_fasteners = []
    for end_y in (-2.655, 2.655):
        visible_end_y = end_y + math.copysign(0.038, end_y)
        for x_depth in (1.02, 3.02):
            for fastener_z in (0.64, 2.54):
                end_panel_fasteners.append(
                    (
                        (inner_face + side * x_depth, visible_end_y, fastener_z),
                        (0.060, 0.026, 0.060),
                    )
                )
    _boxes(
        f"{prefix}_EndServicePanelCompressionLatches",
        end_panel_fasteners,
        collection,
        parent=bay,
        material=materials["machined_steel"],
        role="machined_steel",
        detail="flush_end_panel_quarter_turn_compression_latches",
        bevel=0.008,
    )
    vent_center_x = inner_face + side * (1.30 if variant % 2 else 2.65)
    _box(
        f"{prefix}_SideFilterHousing",
        (0.96, 0.045, 0.78),
        collection,
        location=(vent_center_x, -2.705, 1.14),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="side_mount_mist_filter_intake_housing",
        bevel=0.016,
    )
    _boxes(
        f"{prefix}_SideFilterLouvers",
        (
            ((vent_center_x, -2.735, 0.88 + slot * 0.09), (0.76, 0.025, 0.032))
            for slot in range(7)
        ),
        collection,
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="side_mount_mist_filter_intake_louvers",
        bevel=0.003,
    )

    _build_machine_controls_and_services(
        prefix,
        service_sign,
        front_x,
        center_x,
        toward_aisle,
        bay,
        collection,
        materials,
        family=family,
        variant=variant,
    )

    _build_machine_identity_details(
        prefix,
        side_name,
        index,
        service_sign,
        front_x,
        toward_aisle,
        bay,
        collection,
        materials,
    )

    roof_filter_x = inner_face + side * 2.70
    roof_filter_y = service_sign * (1.54 + 0.06 * (variant % 2))
    roof_filter_dimensions = (
        (0.86, 1.04, 0.26),
        (0.94, 0.92, 0.28),
        (0.78, 1.10, 0.24),
        (0.90, 0.98, 0.28),
    )[variant]
    _box(
        f"{prefix}_MistFilterModule",
        roof_filter_dimensions,
        collection,
        location=(roof_filter_x, roof_filter_y, 3.87),
        parent=bay,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="roof_mounted_coolant_mist_filter_module",
        bevel=0.025,
    )
    filter_top_z = 3.87 + roof_filter_dimensions[2] * 0.5
    _box(
        f"{prefix}_MistFilterServiceLid",
        (
            roof_filter_dimensions[0] - 0.10,
            roof_filter_dimensions[1] - 0.10,
            0.035,
        ),
        collection,
        location=(roof_filter_x, roof_filter_y, filter_top_z + 0.018),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="gasketed_mist_filter_service_lid",
        bevel=0.008,
    )
    _cylinder(
        f"{prefix}_MistFilterDuctCollar",
        0.115 if family == "raceway_grinder" else 0.100,
        0.11,
        collection,
        location=(
            roof_filter_x,
            roof_filter_y - service_sign * 0.20,
            filter_top_z + 0.075,
        ),
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="sealed_mist_filter_exhaust_duct_collar",
        segments=28,
    )
    _boxes(
        f"{prefix}_MistFilterLidLatches",
        (
            (
                (
                    roof_filter_x - side * (roof_filter_dimensions[0] * 0.34),
                    roof_filter_y,
                    filter_top_z + 0.045,
                ),
                (0.055, 0.095, 0.045),
            ),
            (
                (
                    roof_filter_x + side * (roof_filter_dimensions[0] * 0.34),
                    roof_filter_y,
                    filter_top_z + 0.045,
                ),
                (0.055, 0.095, 0.045),
            ),
        ),
        collection,
        parent=bay,
        material=materials["machined_steel"],
        role="machined_steel",
        detail="mist_filter_service_lid_over_center_latches",
        bevel=0.006,
    )

    nameplate_y = fixed_end_y
    _box(
        f"{prefix}_Nameplate",
        (0.035, 0.66, 0.19),
        collection,
        location=(front_x + toward_aisle * 0.070, nameplate_y, 3.12),
        parent=bay,
        material=materials["black_oxide"],
        role="dark_metal",
        detail="low_contrast_machine_model_nameplate",
        bevel=0.008,
    )
    nameplate_text = modeling._text_label(
        f"{prefix}_NameplateText",
        model_codes[variant],
        0.105,
        collection,
        location=(front_x + toward_aisle * 0.092, nameplate_y, 3.12),
        rotation=(0.0, toward_aisle * math.pi * 0.5, 0.0),
        parent=bay,
        material=materials["brushed_steel"],
        role="small_machine_model_identification_text",
    )
    _tag(
        nameplate_text,
        "brushed_metal",
        "small_machine_model_identification_text",
    )

    tower_x = inner_face + side * 0.34
    tower_y = -service_sign * 2.10
    _cylinder(
        f"{prefix}_TowerMast",
        0.026,
        0.34,
        collection,
        location=(tower_x, tower_y, 3.91),
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="machine_status_tower_mast",
        segments=16,
    )
    status_keys = {
        0: ((4.10, "indicator_green"), (4.21, "safety_glass")),
        1: ((4.10, "safety_amber"), (4.21, "safety_glass")),
        2: ((4.10, "indicator_green"), (4.21, "safety_glass")),
        3: ((4.10, "indicator_green"), (4.21, "safety_amber")),
    }[variant]
    for segment, (z, key) in enumerate(status_keys, start=1):
        _cylinder(
            f"{prefix}_Tower_{segment:02d}",
            0.057,
            0.095,
            collection,
            location=(tower_x, tower_y, z),
            parent=bay,
            material=materials[key],
            role=(
                "amber_signal"
                if key == "safety_amber"
                else "luminaire" if key == "indicator_green" else "safety_glass"
            ),
            detail="machine_stack_status_light",
            segments=20,
        )
    for collar_index, collar_z in enumerate((4.045, 4.155, 4.265), start=1):
        _cylinder(
            f"{prefix}_TowerDividerCollar_{collar_index:02d}",
            0.061,
            0.018,
            collection,
            location=(tower_x, tower_y, collar_z),
            parent=bay,
            material=materials["black_oxide"],
            role="dark_metal",
            detail="machine_stack_light_segment_divider_collar",
            segments=20,
        )

    _boxes(
        f"{prefix}_SafetyBoundary",
        (
            ((center_x, -2.92, 0.044), (4.35, 0.055, 0.009)),
            ((center_x, 2.92, 0.044), (4.35, 0.055, 0.009)),
            ((side * 2.16, 0.0, 0.044), (0.055, 5.88, 0.009)),
        ),
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

    machine_utilities = _build_machine_utility_drops(
        root,
        collection,
        materials,
        tuple((-1, y) for y in left_positions) + tuple((1, y) for y in right_positions),
    )

    _recolor_staging_robot(assets)
    assets["mature_factory"] = root
    assets["mature_factory_collection"] = collection
    assets["mature_machine_bays"] = machine_bays
    assets["mature_machine_utilities"] = machine_utilities
    assets["command_screen_bay"] = command_bay
    assets["hero_screen"] = hero_screen
    assets["robot_cell_fence"] = robot_fence
    assets["agv"] = agv
    assets["agv_07"] = agv
    assets.setdefault("collections", {})["mature_factory"] = collection
    bpy.context.view_layer.update()
    return assets
