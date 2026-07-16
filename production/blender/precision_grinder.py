"""Production-detail augmentation for the internal raceway grinding cell."""

from __future__ import annotations

import math
import random
from typing import Any

import bpy
from mathutils import Vector

import modeling


MODEL_COLLECTION = "SUM_MODEL_PrecisionGrinderDetail"
_RACEWAY_CONTACT_RADIUS = 0.096
_WHEEL_CENTER_RADIUS = 0.041
_WHEEL_RADIAL_OFFSET = _RACEWAY_CONTACT_RADIUS - _WHEEL_CENTER_RADIUS
_WHEEL_CENTER = Vector((0.08, _WHEEL_RADIAL_OFFSET, 1.82))
_CONTACT_POINT = Vector((0.08, 0.096, 1.82))
_WHEEL_HALF_WIDTH = 0.010
_WHEEL_EDGE_RADIUS = 0.0385
_WHEEL_BOND_RADIUS = 0.034


def _tag(obj: bpy.types.Object, role: str, detail: str) -> bpy.types.Object:
    obj["lookdev_role"] = role
    obj["sum_quality_level"] = "production"
    obj["sum_design_detail"] = detail
    return obj


def _reset_detail_collection(
    parent: bpy.types.Collection,
) -> bpy.types.Collection:
    """Replace only the generated grinder-detail collection."""

    existing = bpy.data.collections.get(MODEL_COLLECTION)
    if existing is not None:
        owned_data = [
            obj.data
            for obj in existing.all_objects
            if getattr(obj, "data", None) is not None
        ]
        modeling._remove_collection_tree(existing)
        for datablock in owned_data:
            if datablock.users != 0:
                continue
            if isinstance(datablock, bpy.types.Mesh):
                bpy.data.meshes.remove(datablock)
            elif isinstance(datablock, bpy.types.Curve):
                bpy.data.curves.remove(datablock)
    return modeling._child_collection(parent, MODEL_COLLECTION)


def _raceway_ring_geometry(
    profile: list[tuple[float, float]],
    outer_radius: float,
    segments: int,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    stride = segments * 2
    for axial, inner_radius in profile:
        for radius in (outer_radius, inner_radius):
            for segment in range(segments):
                angle = math.tau * segment / segments
                vertices.append(
                    (math.cos(angle) * radius, math.sin(angle) * radius, axial)
                )

    for station in range(len(profile) - 1):
        current = station * stride
        following = current + stride
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append(
                (
                    current + segment,
                    current + next_segment,
                    following + next_segment,
                    following + segment,
                )
            )
            faces.append(
                (
                    current + segments + next_segment,
                    current + segments + segment,
                    following + segments + segment,
                    following + segments + next_segment,
                )
            )

    for station in (0, len(profile) - 1):
        offset = station * stride
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append(
                (
                    offset + segment,
                    offset + segments + segment,
                    offset + segments + next_segment,
                    offset + next_segment,
                )
            )
    return vertices, faces


def _raceway_surface_geometry(
    profile: list[tuple[float, float]],
    segments: int,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for axial, radius in profile:
        for segment in range(segments):
            angle = math.tau * segment / segments
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, axial))
    for station in range(len(profile) - 1):
        current = station * segments
        following = current + segments
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append(
                (
                    current + next_segment,
                    current + segment,
                    following + segment,
                    following + next_segment,
                )
            )
    return vertices, faces


def _rebuild_raceway_workpiece(
    workpiece: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    profile = [
        (-0.030, 0.0880),
        (-0.027, 0.0855),
        (-0.023, 0.0850),
        (-0.020, 0.0868),
        (-0.014, 0.0902),
        (-0.008, 0.0940),
        (0.000, 0.0960),
        (0.008, 0.0940),
        (0.014, 0.0902),
        (0.020, 0.0868),
        (0.023, 0.0850),
        (0.027, 0.0855),
        (0.030, 0.0880),
    ]
    vertices, faces = _raceway_ring_geometry(profile, 0.145, 144)
    replacement = bpy.data.meshes.new("SUM_GrindingCell_OuterRing_ProfiledRaceway_Mesh")
    replacement.from_pydata(vertices, [], faces)
    replacement.materials.append(materials["machined_steel"])
    replacement.update()
    previous = workpiece.data
    workpiece.data = replacement
    if previous is not None and previous.users == 0:
        bpy.data.meshes.remove(previous)
    for polygon in replacement.polygons:
        polygon.use_smooth = True
    for modifier in list(workpiece.modifiers):
        if modifier.name.startswith(("SUM_Bevel", "SUM_WeightedNormals")):
            workpiece.modifiers.remove(modifier)
    modeling._hard_surface(workpiece, 0.0012, segments=3, smooth=True)
    _tag(
        workpiece,
        "workpiece_steel",
        "bearing_outer_ring_with_concave_internal_raceway_profile",
    )
    workpiece["raceway_minor_depth_m"] = 0.011
    workpiece["raceway_contact_radius_m"] = 0.096
    workpiece["workpiece_type"] = "bearing_outer_ring"

    highlight_profile = [
        (-0.018, 0.0877),
        (-0.012, 0.0917),
        (-0.006, 0.0951),
        (0.000, 0.0957),
        (0.006, 0.0951),
        (0.012, 0.0917),
        (0.018, 0.0877),
    ]
    highlight_vertices, highlight_faces = _raceway_surface_geometry(
        highlight_profile, 160
    )
    highlight = modeling._mesh_object(
        "SUM_GrindingCell_FreshGround_RacewayBand",
        highlight_vertices,
        highlight_faces,
        collection,
        parent=workpiece,
        material=materials["machined_steel"],
        smooth=True,
    )
    _tag(
        highlight,
        "fresh_ground_steel",
        "freshly_ground_concave_internal_raceway_contact_band",
    )
    return highlight


def _wheel_profile_radius(axial: float) -> float:
    normalized = min(1.0, abs(axial) / _WHEEL_HALF_WIDTH)
    crown = math.cos(normalized * math.pi * 0.5) ** 1.65
    return _WHEEL_EDGE_RADIUS + (
        _WHEEL_CENTER_RADIUS - _WHEEL_EDGE_RADIUS
    ) * crown


def _profiled_abrasive_shell_geometry(
    segments: int = 128,
    axial_segments: int = 16,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    stride = segments * 2
    for station in range(axial_segments + 1):
        axial = -_WHEEL_HALF_WIDTH + 2.0 * _WHEEL_HALF_WIDTH * station / axial_segments
        for radius in (_wheel_profile_radius(axial), _WHEEL_BOND_RADIUS):
            for segment in range(segments):
                angle = math.tau * segment / segments
                vertices.append(
                    (math.cos(angle) * radius, math.sin(angle) * radius, axial)
                )

    for station in range(axial_segments):
        current = station * stride
        following = current + stride
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append(
                (
                    current + segment,
                    current + next_segment,
                    following + next_segment,
                    following + segment,
                )
            )
            faces.append(
                (
                    current + segments + next_segment,
                    current + segments + segment,
                    following + segments + segment,
                    following + segments + next_segment,
                )
            )

    for station in (0, axial_segments):
        offset = station * stride
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append(
                (
                    offset + segment,
                    offset + segments + segment,
                    offset + segments + next_segment,
                    offset + next_segment,
                )
            )
    return vertices, faces


def _append_crystal(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    center: Vector,
    tangent_a: Vector,
    tangent_b: Vector,
    normal: Vector,
    size: float,
    height: float,
) -> None:
    start = len(vertices)
    base = center - normal * size * 0.12
    vertices.extend(
        tuple(point)
        for point in (
            base + tangent_a * size,
            base + tangent_b * size * 0.82,
            base - tangent_a * size * 0.76,
            base - tangent_b * size,
            center + normal * height,
        )
    )
    faces.extend(
        (
            (start, start + 1, start + 4),
            (start + 1, start + 2, start + 4),
            (start + 2, start + 3, start + 4),
            (start + 3, start, start + 4),
            (start + 3, start + 2, start + 1, start),
        )
    )


def _cbn_grain_geometry() -> tuple[
    list[tuple[float, float, float]], list[tuple[int, ...]]
]:
    rng = random.Random(82173)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    for _ in range(240):
        angle = rng.uniform(0.0, math.tau)
        axial = rng.uniform(-_WHEEL_HALF_WIDTH * 0.92, _WHEEL_HALF_WIDTH * 0.92)
        normal = Vector((math.cos(angle), math.sin(angle), 0.0))
        tangent = Vector((-math.sin(angle), math.cos(angle), 0.0))
        axis = Vector((0.0, 0.0, 1.0))
        center = normal * (_wheel_profile_radius(axial) - rng.uniform(0.00002, 0.00007))
        center.z = axial
        size = rng.uniform(0.00006, 0.00013)
        _append_crystal(
            vertices,
            faces,
            center,
            tangent,
            axis,
            normal,
            size,
            rng.uniform(0.00004, 0.00011),
        )

    for side in (-1.0, 1.0):
        normal = Vector((0.0, 0.0, side))
        for _ in range(48):
            angle = rng.uniform(0.0, math.tau)
            radius = rng.uniform(_WHEEL_BOND_RADIUS + 0.0005, _WHEEL_EDGE_RADIUS - 0.0004)
            radial = Vector((math.cos(angle), math.sin(angle), 0.0))
            tangent = Vector((-math.sin(angle), math.cos(angle), 0.0))
            center = radial * radius
            center.z = side * _WHEEL_HALF_WIDTH
            size = rng.uniform(0.00005, 0.00011)
            _append_crystal(
                vertices,
                faces,
                center,
                radial,
                tangent,
                normal,
                size,
                rng.uniform(0.000035, 0.00010),
            )
    return vertices, faces


def _build_cbn_wheel_detail(
    wheel_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, bpy.types.Object]:
    _tag(wheel_root, "brushed_metal", "balanced_steel_quill_and_wheel_rotation_core")

    bond = modeling._cylinder(
        "SUM_GrindingCell_CBN_VitrifiedBondBody",
        _WHEEL_BOND_RADIUS,
        0.028,
        collection,
        parent=wheel_root,
        material=materials["grinding_wheel"],
        segments=128,
        bevel=0.0008,
        role="vitrified_cbn_bond_body",
    )
    _tag(bond, "abrasive_bond", "porous_vitrified_cbn_bond_body")

    shell_vertices, shell_faces = _profiled_abrasive_shell_geometry()
    shell = modeling._mesh_object(
        "SUM_GrindingCell_CBN_ProfiledAbrasiveLayer",
        shell_vertices,
        shell_faces,
        collection,
        parent=wheel_root,
        material=materials["grinding_wheel"],
        smooth=True,
    )
    _tag(
        shell,
        "abrasive",
        "convex_profiled_cbn_working_layer_for_internal_raceway",
    )

    grain_vertices, grain_faces = _cbn_grain_geometry()
    grains = modeling._mesh_object(
        "SUM_GrindingCell_CBN_ExposedAbrasiveCrystals",
        grain_vertices,
        grain_faces,
        collection,
        parent=wheel_root,
        material=materials["grinding_wheel"],
        smooth=False,
    )
    _tag(grains, "abrasive_grain", "partially_exposed_faceted_cbn_grains")
    grains["modeled_grain_count"] = 336
    grains["visual_scale_note"] = "B76-B126 scale silhouette grains; dense body texture is shader-driven"

    hub = modeling._cylinder(
        "SUM_GrindingCell_CBN_PrecisionArborHub",
        0.021,
        0.038,
        collection,
        parent=wheel_root,
        material=materials["machined_steel"],
        segments=72,
        bevel=0.0012,
        role="balanced_cbn_wheel_arbor_hub",
    )
    _tag(hub, "brushed_metal", "balanced_cbn_wheel_arbor_hub")
    flanges = []
    for side in (-1.0, 1.0):
        flange = modeling._cylinder(
            f"SUM_GrindingCell_CBN_SideFlange_{'A' if side < 0 else 'B'}",
            0.032,
            0.0028,
            collection,
            location=(0.0, 0.0, side * 0.0154),
            parent=wheel_root,
            material=materials["black_oxide"],
            segments=72,
            bevel=0.0005,
            role="cbn_wheel_side_retention_flange",
        )
        flanges.append(_tag(flange, "dark_metal", "cbn_wheel_side_retention_flange"))

    wheel_root["abrasive_layer_thickness_center_m"] = (
        _WHEEL_CENTER_RADIUS - _WHEEL_BOND_RADIUS
    )
    wheel_root["abrasive_layer_thickness_edge_m"] = (
        _WHEEL_EDGE_RADIUS - _WHEEL_BOND_RADIUS
    )
    wheel_root["abrasive_profile"] = "convex dressed raceway profile"
    return {
        "bond": bond,
        "shell": shell,
        "grains": grains,
        "hub": hub,
        "flanges": flanges,
    }


def _exclude_old_doors() -> None:
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(
            ("SUM_GrindingCell_LeftDoor_", "SUM_GrindingCell_RightDoor_")
        ):
            obj.hide_render = True
            obj["sum_export_exclude"] = True
            obj["sum_replaced_by"] = "animated production sliding doors"


def _exclude_replaced_process_proxies() -> None:
    replaced_names = {
        "SUM_GrindingCell_Workhead_Housing": "compact production workhead behind the shoe-supported ring",
        "SUM_GrindingCell_WorkSpindle_Nose": "low-profile magnetic drive plate and axial locators",
        "SUM_GrindingCell_ThreeJawChuck": "shoe support and regulating drive roller",
        "SUM_GrindingCell_Workholding_BackupFlange": "low-profile magnetic drive plate",
        "SUM_GrindingCell_GrindingSpindle_Housing": "liquid-cooled spindle motor assembly",
        "SUM_GrindingCell_GrindingSpindle_Shaft": "short taper arbor and wheel hub",
    }
    for obj in bpy.context.scene.objects:
        replacement = replaced_names.get(obj.name)
        if replacement is None and obj.name.startswith("SUM_GrindingCell_ChuckJaw_"):
            replacement = "rotated stepped soft jaws"
        if replacement is None:
            continue
        obj.hide_render = True
        obj["sum_export_exclude"] = True
        obj["sum_replaced_by"] = replacement


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


def _build_enclosure_service_detail(
    cell_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, bpy.types.Object]:
    """Add restrained production hardware around the grinding enclosure."""

    rear_panels = []
    for side in (-1.0, 1.0):
        rear_panels.append(((-1.625, side * 0.88, 2.03), (0.040, 1.55, 3.32)))
    service_doors = modeling._box_array(
        "SUM_GrindingCell_RearServiceAccessDoors",
        rear_panels,
        collection,
        parent=cell_root,
        material=materials["enclosure_paint"],
        bevel=0.012,
        role="flush_rear_machine_service_access_doors",
    )
    _tag(service_doors, "powder_coat", "flush_rear_machine_service_access_doors")

    seams = modeling._box_array(
        "SUM_GrindingCell_RearServiceDoorReveals",
        [
            ((-1.652, 0.0, 2.03), (0.022, 0.030, 3.18)),
            ((-1.652, -1.68, 2.03), (0.022, 0.030, 3.18)),
            ((-1.652, 1.68, 2.03), (0.022, 0.030, 3.18)),
            ((-1.652, 0.0, 0.42), (0.022, 3.38, 0.030)),
            ((-1.652, 0.0, 3.64), (0.022, 3.38, 0.030)),
        ],
        collection,
        parent=cell_root,
        material=materials["black_oxide"],
        bevel=0.003,
        role="rear_service_door_compression_reveals",
    )
    _tag(seams, "dark_metal", "rear_service_door_compression_reveals")

    fastener_boxes = []
    for y in (-1.56, -0.88, -0.20, 0.20, 0.88, 1.56):
        for z in (0.52, 1.50, 2.52, 3.52):
            fastener_boxes.append(((-1.680, y, z), (0.022, 0.034, 0.034)))
    fasteners = modeling._box_array(
        "SUM_GrindingCell_RearServiceDoorFasteners",
        fastener_boxes,
        collection,
        parent=cell_root,
        material=materials["machined_steel"],
        bevel=0.002,
        role="captive_rear_service_door_fasteners",
    )
    _tag(fasteners, "brushed_metal", "captive_rear_service_door_fasteners")

    console = modeling._empty(
        "SUM_GrindingCell_IntegratedOperatorConsole",
        collection,
        parent=cell_root,
        display_size=0.10,
    )
    console["sum_asset_type"] = "integrated_cnc_grinder_operator_panel"
    housing = modeling._box(
        "SUM_GrindingCell_OperatorConsoleHousing",
        (0.34, 0.84, 1.22),
        collection,
        location=(1.78, -2.67, 2.18),
        parent=console,
        material=materials["paint_graphite"],
        bevel=0.045,
        role="sealed_cnc_operator_console_housing",
    )
    _tag(housing, "powder_coat", "sealed_cnc_operator_console_housing")
    screen = modeling._box(
        "SUM_GrindingCell_OperatorConsoleDisplay",
        (0.030, 0.62, 0.42),
        collection,
        location=(1.966, -2.67, 2.40),
        parent=console,
        material=materials["screen_content"],
        bevel=0.012,
        role="sealed_cnc_process_hmi_display",
    )
    _tag(screen, "screen_glass", "sealed_cnc_process_hmi_display")
    keypad_boxes = []
    for row in range(3):
        for column in range(5):
            keypad_boxes.append(
                ((1.972, -2.87 + column * 0.10, 2.00 + row * 0.085), (0.022, 0.060, 0.045))
            )
    keypad = modeling._box_array(
        "SUM_GrindingCell_OperatorConsoleKeypad",
        keypad_boxes,
        collection,
        parent=console,
        material=materials["screen_frame"],
        bevel=0.006,
        role="sealed_cnc_membrane_keypad",
    )
    _tag(keypad, "screen_glass", "sealed_cnc_membrane_keypad")
    e_stop = modeling._cylinder(
        "SUM_GrindingCell_OperatorConsoleEmergencyStop",
        0.065,
        0.065,
        collection,
        location=(1.985, -2.36, 1.86),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=console,
        material=materials["indicator_red"],
        segments=28,
        bevel=0.006,
        role="guarded_operator_console_emergency_stop",
    )
    _tag(e_stop, "amber_signal", "guarded_operator_console_emergency_stop")
    warning = modeling._box(
        "SUM_GrindingCell_OperatorConsoleWheelHazardPlate",
        (0.026, 0.30, 0.23),
        collection,
        location=(1.982, -2.67, 1.65),
        parent=console,
        material=materials["safety_yellow"],
        bevel=0.010,
        role="abrasive_wheel_hazard_identification_plate",
    )
    _tag(warning, "safety_yellow", "abrasive_wheel_hazard_identification_plate")

    feet = []
    for x in (-1.30, 1.30):
        for y in (-2.20, 2.20):
            foot = modeling._cylinder(
                f"SUM_GrindingCell_LevelingMount_{'R' if x > 0 else 'L'}_{'B' if y > 0 else 'A'}",
                0.13,
                0.075,
                collection,
                location=(x, y, 0.075),
                parent=cell_root,
                material=materials["black_oxide"],
                segments=36,
                bevel=0.008,
                role="machine_anti_vibration_leveling_mount",
            )
            feet.append(_tag(foot, "dark_metal", "machine_anti_vibration_leveling_mount"))

    coolant_return = modeling._bezier_tube(
        "SUM_GrindingCell_FilteredCoolantReturnLine",
        [
            (-0.55, 1.42, 0.68),
            (-0.88, 1.82, 0.60),
            (-1.34, 2.10, 0.54),
            (-1.62, 2.22, 0.48),
        ],
        0.055,
        collection,
        parent=cell_root,
        material=materials["rubber"],
        role="filtered_grinding_coolant_return_hose",
        resolution=10,
    )
    _tag(
        coolant_return,
        "rubber",
        "filtered_grinding_coolant_return_hose_to_central_manifold",
    )
    drain_flange = modeling._cylinder_between(
        "SUM_GrindingCell_CoolantReturnFloorFlange",
        (-1.62, 2.22, 0.42),
        (-1.62, 2.22, 0.54),
        0.090,
        collection,
        parent=cell_root,
        material=materials["black_oxide"],
        segments=36,
        bevel=0.006,
        role="coolant_return_service_flange",
    )
    _tag(drain_flange, "dark_metal", "coolant_return_service_flange")

    return {
        "service_doors": service_doors,
        "fasteners": fasteners,
        "console": console,
        "screen": screen,
        "leveling_mounts": feet,
        "coolant_return": coolant_return,
    }


def _build_process_chamber(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    """Build the sealed, wet machine cavity visible behind the process."""
    dark = materials["paint_graphite"]
    black = materials["black_oxide"]
    steel = materials["brushed_steel"]

    rear_liner = modeling._box(
        "SUM_GrindingCell_ProcessChamber_RearLiner",
        (0.10, 3.00, 2.55),
        collection,
        location=(-1.55, 0.0, 1.92),
        parent=root,
        material=dark,
        bevel=0.018,
        role="sealed_coolant_chamber_rear_liner",
    )
    _tag(rear_liner, "dark_metal", "sealed_coolant_chamber_rear_liner")

    liner_panels = []
    for y in (-1.00, 0.0, 1.00):
        liner_panels.append(((-1.49, y, 1.94), (0.035, 0.90, 2.20)))
    panels = modeling._box_array(
        "SUM_GrindingCell_ProcessChamber_ServicePanels",
        liner_panels,
        collection,
        parent=root,
        material=black,
        bevel=0.012,
        role="replaceable_stainless_splash_service_panels",
    )
    _tag(panels, "dark_metal", "replaceable_stainless_splash_service_panels")

    seams = modeling._box_array(
        "SUM_GrindingCell_ProcessChamber_PanelSeams",
        [
            ((-1.465, -0.50, 1.94), (0.020, 0.018, 2.12)),
            ((-1.465, 0.50, 1.94), (0.020, 0.018, 2.12)),
            ((-1.465, 0.0, 0.89), (0.022, 2.82, 0.018)),
        ],
        collection,
        parent=root,
        material=steel,
        bevel=0.004,
        role="sealed_chamber_panel_seams",
    )
    _tag(seams, "brushed_metal", "sealed_chamber_panel_seams")

    side_returns = modeling._box_array(
        "SUM_GrindingCell_ProcessChamber_SideReturns",
        [
            ((0.05, -1.47, 1.88), (3.18, 0.10, 2.50)),
            ((0.05, 1.47, 1.88), (3.18, 0.10, 2.50)),
        ],
        collection,
        parent=root,
        material=dark,
        bevel=0.018,
        role="deep_drawn_chamber_side_returns",
    )
    _tag(side_returns, "dark_metal", "deep_drawn_chamber_side_returns")

    roof = modeling._box(
        "SUM_GrindingCell_ProcessChamber_Roof",
        (3.42, 3.00, 0.12),
        collection,
        location=(0.05, 0.0, 3.20),
        parent=root,
        material=dark,
        bevel=0.020,
        role="sealed_process_chamber_roof",
    )
    _tag(roof, "dark_metal", "sealed_process_chamber_roof")

    sump = modeling._box(
        "SUM_GrindingCell_ProcessChamber_CoolantSump",
        (3.38, 3.00, 0.18),
        collection,
        location=(0.05, 0.0, 0.70),
        parent=root,
        material=black,
        bevel=0.035,
        role="sloped_coolant_and_swarf_return_sump",
    )
    _tag(sump, "dark_metal", "sloped_coolant_and_swarf_return_sump")
    coolant_pool = modeling._box(
        "SUM_GrindingCell_ProcessChamber_CoolantPool",
        (2.92, 2.50, 0.018),
        collection,
        location=(0.05, 0.0, 0.805),
        parent=root,
        material=materials["safety_glass"],
        bevel=0.006,
        role="recirculating_milky_grinding_coolant_pool",
    )
    _tag(coolant_pool, "coolant", "recirculating_milky_grinding_coolant_pool")

    lamp_housing = modeling._box(
        "SUM_GrindingCell_ProcessChamber_InspectionLampHousing",
        (0.46, 0.10, 0.13),
        collection,
        location=(-1.42, -0.82, 2.96),
        parent=root,
        material=black,
        bevel=0.016,
        role="sealed_machine_inspection_lamp_housing",
    )
    _tag(lamp_housing, "dark_metal", "sealed_machine_inspection_lamp_housing")
    lamp = modeling._box(
        "SUM_GrindingCell_ProcessChamber_InspectionLamp",
        (0.28, 0.025, 0.060),
        collection,
        location=(-1.35, -0.82, 2.96),
        parent=root,
        material=materials["luminaire_diffuser"],
        bevel=0.010,
        role="sealed_neutral_white_process_inspection_lamp",
    )
    _tag(lamp, "light_fixture", "sealed_neutral_white_process_inspection_lamp")


def _build_b_axis_and_workhead(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, bpy.types.Object]:
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

    for index, x in enumerate((-0.62, -0.78, -0.94, -1.10), start=1):
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
        (-0.18, 0.0, 1.82),
        (-0.44, 0.0, 1.82),
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
        (-1.18, 0.0, 1.82),
        (-1.28, 0.0, 1.82),
        0.245,
        collection,
        parent=root,
        material=dark,
        segments=64,
        bevel=0.010,
        role="workhead_rear_service_cap",
    )
    _tag(service_cap, "dark_metal", "workhead_rear_service_cap")

    drive_plate = modeling._cylinder_between(
        "SUM_GrindingCell_WorkpieceMagneticDrivePlate",
        (-0.035, 0.0, 1.82),
        (-0.085, 0.0, 1.82),
        0.122,
        collection,
        parent=root,
        material=dark,
        segments=96,
        bevel=0.004,
        role="low_profile_magnetic_workpiece_drive_plate",
    )
    _tag(drive_plate, "dark_metal", "low_profile_magnetic_workpiece_drive_plate")
    bolts = modeling._add_bolt_circle(
        "SUM_GrindingCell_DrivePlate",
        (-0.090, 0.0, 1.82),
        (-1.0, 0.0, 0.0),
        0.084,
        0.006,
        0.018,
        8,
        collection,
        parent=root,
        material=steel,
    )
    for bolt in bolts:
        _tag(bolt, "brushed_metal", "magnetic_drive_plate_fastener")

    for index, angle_degrees in enumerate((215.0, 325.0), start=1):
        angle = math.radians(angle_degrees)
        shoe_root = modeling._empty(
            f"SUM_GrindingCell_SupportShoe_{index:02d}_Frame",
            collection,
            location=(0.0, 0.0, 1.82),
            rotation=(angle, 0.0, 0.0),
            parent=root,
            display_size=0.035,
        )
        shoe_root["sum_part_role"] = "hydrostatic_outer_ring_support_shoe_frame"
        shoe_base = modeling._box(
            f"SUM_GrindingCell_SupportShoe_{index:02d}_Body",
            (0.16, 0.090, 0.11),
            collection,
            location=(-0.030, 0.115, 0.0),
            parent=shoe_root,
            material=steel,
            bevel=0.012,
            role="precision_outer_ring_support_shoe_body",
        )
        _tag(shoe_base, "brushed_metal", "precision_outer_ring_support_shoe_body")
        contact_insert = modeling._box(
            f"SUM_GrindingCell_SupportShoe_{index:02d}_CarbideInsert",
            (0.090, 0.026, 0.070),
            collection,
            location=(-0.078, 0.132, 0.0),
            parent=shoe_root,
            material=materials["black_oxide"],
            bevel=0.008,
            role="replaceable_carbide_support_shoe_insert",
        )
        _tag(contact_insert, "dark_metal", "replaceable_carbide_support_shoe_insert")

    drive_roller = modeling._cylinder_between(
        "SUM_GrindingCell_RubberizedDriveRoller",
        (-0.015, 0.0, 1.994),
        (-0.145, 0.0, 1.994),
        0.052,
        collection,
        parent=root,
        material=materials["rubber"],
        segments=64,
        bevel=0.006,
        role="rubberized_outer_ring_drive_roller",
    )
    _tag(drive_roller, "rubber", "rubberized_outer_ring_drive_roller")
    drive_motor = modeling._cylinder_between(
        "SUM_GrindingCell_DriveRollerServo",
        (-0.145, 0.0, 1.994),
        (-0.350, 0.0, 1.994),
        0.068,
        collection,
        parent=root,
        material=dark,
        segments=56,
        bevel=0.010,
        role="direct_drive_workpiece_regulating_servo",
    )
    _tag(drive_motor, "powder_coat", "direct_drive_workpiece_regulating_servo")

    for index in range(3):
        angle = math.tau * index / 3.0
        locating_button = modeling._cylinder_between(
            f"SUM_GrindingCell_AxialLocatingButton_{index + 1:02d}",
            (-0.012, math.cos(angle) * 0.086, 1.82 + math.sin(angle) * 0.086),
            (0.030, math.cos(angle) * 0.086, 1.82 + math.sin(angle) * 0.086),
            0.012,
            collection,
            parent=root,
            material=materials["black_oxide"],
            segments=32,
            bevel=0.002,
            role="three_point_axial_workpiece_location_button",
        )
        _tag(
            locating_button,
            "dark_metal",
            "three_point_axial_workpiece_location_button",
        )
    return {"drive_plate": drive_plate, "drive_roller": drive_roller}

def _build_grinding_slide(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    steel = materials["machined_steel"]
    dark = materials["paint_graphite"]
    wheel_y = _WHEEL_RADIAL_OFFSET
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
        location=(1.03, wheel_y, 1.20),
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
        location=(1.16, wheel_y, 1.46),
        parent=root,
        material=dark,
        bevel=0.055,
        role="ribbed_cast_spindle_support",
    )
    _tag(spindle_support, "powder_coat", "ribbed_cast_spindle_support")
    spindle_motor = modeling._cylinder_between(
        "SUM_GrindingCell_HighSpeedSpindleMotor",
        (0.82, wheel_y, 1.82),
        (1.43, wheel_y, 1.82),
        0.165,
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
        (1.41, wheel_y, 1.82),
        (1.55, wheel_y, 1.82),
        0.138,
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
            0.155,
            0.012,
            collection,
            location=(x, wheel_y, 1.82),
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
        (0.56, wheel_y, 1.82),
        (0.70, wheel_y, 1.82),
        0.102,
        collection,
        parent=root,
        material=steel,
        segments=64,
        bevel=0.008,
        role="grinding_spindle_balance_collar",
    )
    _tag(balance_collar, "brushed_metal", "grinding_spindle_balance_collar")
    arbor_nose = modeling._cylinder_between(
        "SUM_GrindingCell_WheelArborNose",
        (0.095, wheel_y, 1.82),
        (0.155, wheel_y, 1.82),
        0.034,
        collection,
        parent=root,
        material=steel,
        segments=48,
        bevel=0.0015,
        role="short_precision_wheel_arbor_nose",
    )
    _tag(arbor_nose, "brushed_metal", "short_precision_wheel_arbor_nose")
    taper_arbor = modeling._cylinder_between(
        "SUM_GrindingCell_PrecisionTaperArbor",
        (0.145, wheel_y, 1.82),
        (0.405, wheel_y, 1.82),
        0.022,
        collection,
        parent=root,
        material=steel,
        segments=72,
        bevel=0.002,
        role="ground_short_straight_wheel_quill",
    )
    _tag(taper_arbor, "brushed_metal", "ground_short_straight_wheel_quill")
    nose_collar = modeling._cylinder_between(
        "SUM_GrindingCell_SpindleNoseCollar",
        (0.405, wheel_y, 1.82),
        (0.560, wheel_y, 1.82),
        0.060,
        collection,
        parent=root,
        material=materials["black_oxide"],
        segments=72,
        bevel=0.008,
        role="sealed_high_speed_spindle_nose_collar",
    )
    _tag(nose_collar, "dark_metal", "sealed_high_speed_spindle_nose_collar")
    for index, x in enumerate((0.430, 0.510), start=1):
        seal_ring = modeling._torus(
            f"SUM_GrindingCell_SpindleNoseSealRing_{index:02d}",
            0.068,
            0.006,
            collection,
            location=(x, wheel_y, 1.82),
            rotation=(0.0, math.pi * 0.5, 0.0),
            parent=root,
            material=steel,
            major_segments=72,
            minor_segments=10,
            role="spindle_nose_labyrinth_seal_ring",
        )
        _tag(seal_ring, "brushed_metal", "spindle_nose_labyrinth_seal_ring")

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
    coolant_feeds = (
        (
            ((0.58, -0.52, 2.20), (0.44, -0.34, 2.13), (0.26, -0.22, 2.03)),
            (0.14, -0.09, 1.96),
            0.0080,
        ),
        (
            ((0.58, -0.48, 2.16), (0.43, -0.08, 1.98), (0.24, 0.12, 1.93)),
            (0.13, 0.11, 1.91),
            0.0060,
        ),
    )
    for index, (points, nozzle_tip, jet_radius) in enumerate(
        coolant_feeds,
        start=1,
    ):
        line = modeling._bezier_tube(
            f"SUM_GrindingCell_HighPressureCoolantLine_{index:02d}",
            list(points),
            0.009,
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
            nozzle_tip,
            0.012,
            collection,
            parent=root,
            material=materials["black_oxide"],
            segments=20,
            bevel=0.002,
            role="focused_coolant_jet_nozzle",
        )
        _tag(nozzle, "dark_metal", "focused_coolant_jet_nozzle")
        jet_start = Vector(nozzle_tip)
        target_bias = Vector((0.0, (index - 1.5) * 0.0060, (index - 1.5) * 0.0040))
        jet_target = _CONTACT_POINT + target_bias
        jet_mid = jet_start.lerp(jet_target, 0.52) + Vector((0.0, 0.0, 0.006))
        jet = modeling._bezier_tube(
            f"SUM_GrindingCell_CoolantJet_Stream_{index:02d}",
            [tuple(jet_start), tuple(jet_mid), tuple(jet_target)],
            jet_radius,
            collection,
            parent=root,
            material=materials["safety_glass"],
            role="coherent_high_pressure_coolant_jet",
            resolution=8,
        )
        _tag(jet, "coolant", "coherent_coolant_stream_aimed_at_grinding_arc")

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
    workpiece = assets.get("grinding_workpiece")
    wheel_root = assets.get("grinding_wheel")
    process_root = bpy.data.objects.get("SUM_GrindingCell_ProcessFrame_BAxis")
    materials = assets.get("placeholder_materials")
    root_collection = assets.get("root_collection")
    if not isinstance(cell, bpy.types.Object):
        raise TypeError("assets must provide enclosed_grinding_cell")
    if not isinstance(workpiece, bpy.types.Object):
        raise TypeError("assets must provide grinding_workpiece")
    if not isinstance(wheel_root, bpy.types.Object):
        raise TypeError("assets must provide grinding_wheel")
    if not isinstance(process_root, bpy.types.Object):
        raise RuntimeError("Grinding process frame is missing")
    if not isinstance(materials, dict):
        raise TypeError("assets must provide placeholder_materials")
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")

    collection = _reset_detail_collection(root_collection)
    _exclude_old_doors()
    _exclude_replaced_process_proxies()
    workhead_housing = bpy.data.objects.get("SUM_GrindingCell_Workhead_Housing")
    if workhead_housing is not None:
        _tag(workhead_housing, "dark_metal", "sealed_workhead_motor_housing")
    left_door = _build_sliding_door(-1, cell, collection, materials)
    right_door = _build_sliding_door(1, cell, collection, materials)
    enclosure_detail = _build_enclosure_service_detail(
        cell,
        collection,
        materials,
    )

    detail_root = modeling._empty(
        "SUM_ASSET_InternalGrindingProcessDetail",
        collection,
        parent=process_root,
        display_size=0.18,
    )
    detail_root["sum_asset_type"] = "production_internal_raceway_grinding_process"
    detail_root["verified_process_axis"] = "horizontal X work and wheel spindle axes"
    detail_root["verified_contact"] = "small CBN wheel enters bore at radial offset"
    detail_root["verified_workholding"] = "shoe-supported outer ring with regulating drive roller and axial locators"
    detail_root["detail_gate"] = (
        "workhead, magnetic drive plate, support shoes, profiled raceway, "
        "layered CBN wheel, micro-grain surface, linear guides, bellows, servo, "
        "dresser, coolant jets, inspection camera"
    )
    chamber_root = modeling._empty(
        "SUM_ASSET_InternalGrindingChamber",
        collection,
        parent=cell,
        display_size=0.18,
    )
    chamber_root["sum_asset_type"] = "fixed_machine_coordinate_process_chamber"
    chamber_root["coordinate_policy"] = (
        "enclosure fixed to machine bed; B-axis process mechanism rotates independently"
    )
    raceway_band = _rebuild_raceway_workpiece(workpiece, collection, materials)
    wheel_root.location.y = _WHEEL_RADIAL_OFFSET
    wheel_root["wheel_diameter_m"] = _WHEEL_CENTER_RADIUS * 2.0
    wheel_root["nominal_radial_contact_offset_m"] = _WHEEL_RADIAL_OFFSET
    wheel_root["contact_relationship"] = (
        "profiled wheel tangent to the internal raceway at visible radial offset"
    )
    wheel_detail = _build_cbn_wheel_detail(wheel_root, collection, materials)
    _build_process_chamber(chamber_root, collection, materials)
    workholding = _build_b_axis_and_workhead(detail_root, collection, materials)
    _build_grinding_slide(detail_root, collection, materials)
    _build_coolant_and_dressing(detail_root, collection, materials)

    cell["door_state"] = "animated open during process shot"
    cell["process_detail_level"] = "foreground production"
    assets["grinder_detail"] = detail_root
    assets["grinder_chamber"] = chamber_root
    assets["grinding_raceway_band"] = raceway_band
    assets["grinding_wheel_detail"] = wheel_detail
    assets["grinding_drive_plate"] = workholding["drive_plate"]
    assets["grinding_drive_roller"] = workholding["drive_roller"]
    assets["grinder_enclosure_detail"] = enclosure_detail
    assets["grinding_contact_point_local"] = tuple(_CONTACT_POINT)
    assets["grinder_doors"] = (left_door, right_door)
    assets.setdefault("collections", {})["precision_grinder"] = collection
    bpy.context.view_layer.update()
    return assets
