"""Production-detail augmentation for the internal raceway grinding cell."""

from __future__ import annotations

import math
import random
from typing import Any

import bpy
from mathutils import Vector

import modeling


# The hero machine handles a large outer ring. Its axis and the grinding-wheel
# spindle are both horizontal; the small wheel enters the bore at a radial
# offset and contacts the concave internal raceway.
_RACEWAY_CONTACT_RADIUS = 0.142
_WHEEL_CENTER_RADIUS = 0.050
_WHEEL_RADIAL_OFFSET = _RACEWAY_CONTACT_RADIUS - _WHEEL_CENTER_RADIUS
_WHEEL_CENTER = Vector((0.08, _WHEEL_RADIAL_OFFSET, 1.82))
_CONTACT_POINT = Vector((0.08, _RACEWAY_CONTACT_RADIUS, 1.82))
_WHEEL_HALF_WIDTH = 0.012
_WHEEL_EDGE_RADIUS = 0.047
_WHEEL_BOND_RADIUS = 0.040


def _tag(obj: bpy.types.Object, role: str, detail: str) -> bpy.types.Object:
    obj["lookdev_role"] = role
    obj["sum_quality_level"] = "production"
    obj["sum_design_detail"] = detail
    return obj


def _hex_fastener(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    detail: str,
) -> bpy.types.Object:
    fastener = modeling._cylinder_between(
        name,
        start,
        end,
        radius,
        collection,
        parent=parent,
        material=material,
        segments=6,
        bevel=radius * 0.12,
        role=detail,
    )
    return _tag(fastener, "brushed_metal", detail)


def _panel_fasteners(
    prefix: str,
    positions: list[tuple[float, float]],
    y: float,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
) -> None:
    for index, (x, z) in enumerate(positions, start=1):
        _hex_fastener(
            f"{prefix}_{index:02d}",
            (x, y - 0.018, z),
            (x, y + 0.010, z),
            0.010,
            collection,
            parent=parent,
            material=material,
            detail="sealed_machine_panel_socket_fastener",
        )


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
        (-0.042, 0.1310),
        (-0.037, 0.1280),
        (-0.031, 0.1270),
        (-0.025, 0.1305),
        (-0.018, 0.1355),
        (-0.010, 0.1400),
        (0.000, _RACEWAY_CONTACT_RADIUS),
        (0.010, 0.1400),
        (0.018, 0.1355),
        (0.025, 0.1305),
        (0.031, 0.1270),
        (0.037, 0.1280),
        (0.042, 0.1310),
    ]
    vertices, faces = _raceway_ring_geometry(profile, 0.205, 160)
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
    modeling._hard_surface(workpiece, 0.0012, segments=3, smooth=True)
    _tag(
        workpiece,
        "workpiece_steel",
        "bearing_outer_ring_with_concave_internal_raceway_profile",
    )
    workpiece["raceway_minor_depth_m"] = 0.015
    workpiece["raceway_contact_radius_m"] = _RACEWAY_CONTACT_RADIUS
    workpiece["workpiece_type"] = "bearing_outer_ring"

    highlight_profile = [
        (-0.026, 0.1300),
        (-0.018, 0.1350),
        (-0.010, 0.1396),
        (0.000, _RACEWAY_CONTACT_RADIUS - 0.0004),
        (0.010, 0.1396),
        (0.018, 0.1350),
        (0.026, 0.1300),
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
    datum_mark = modeling._box(
        "SUM_GrindingCell_Workpiece_RotationDatumEtch",
        (0.040, 0.006, 0.0025),
        collection,
        location=(0.176, 0.0, 0.0435),
        parent=workpiece,
        material=materials["black_oxide"],
        bevel=0.0008,
        role="laser_etched_workpiece_rotation_datum",
    )
    _tag(datum_mark, "dark_metal", "laser_etched_workpiece_rotation_datum")
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

    for _ in range(360):
        angle = rng.uniform(0.0, math.tau)
        axial = rng.uniform(-_WHEEL_HALF_WIDTH * 0.92, _WHEEL_HALF_WIDTH * 0.92)
        normal = Vector((math.cos(angle), math.sin(angle), 0.0))
        tangent = Vector((-math.sin(angle), math.cos(angle), 0.0))
        axis = Vector((0.0, 0.0, 1.0))
        center = normal * (_wheel_profile_radius(axial) - rng.uniform(0.00005, 0.00028))
        center.z = axial
        size = rng.uniform(0.00024, 0.00048)
        _append_crystal(
            vertices,
            faces,
            center,
            tangent,
            axis,
            normal,
            size,
            rng.uniform(0.00030, 0.00072),
        )

    for side in (-1.0, 1.0):
        normal = Vector((0.0, 0.0, side))
        for _ in range(72):
            angle = rng.uniform(0.0, math.tau)
            radius = rng.uniform(_WHEEL_BOND_RADIUS + 0.0005, _WHEEL_EDGE_RADIUS - 0.0004)
            radial = Vector((math.cos(angle), math.sin(angle), 0.0))
            tangent = Vector((-math.sin(angle), math.cos(angle), 0.0))
            center = radial * radius
            center.z = side * _WHEEL_HALF_WIDTH
            size = rng.uniform(0.00022, 0.00042)
            _append_crystal(
                vertices,
                faces,
                center,
                radial,
                tangent,
                normal,
                size,
                rng.uniform(0.00025, 0.00058),
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
    grains["modeled_grain_count"] = 504
    grains["visual_scale_note"] = "sub-millimetre grains, slightly enlarged for hero readability"

    wheel_root["abrasive_layer_thickness_center_m"] = (
        _WHEEL_CENTER_RADIUS - _WHEEL_BOND_RADIUS
    )
    wheel_root["abrasive_layer_thickness_edge_m"] = (
        _WHEEL_EDGE_RADIUS - _WHEEL_BOND_RADIUS
    )
    wheel_root["abrasive_profile"] = "convex dressed raceway profile"
    return {"bond": bond, "shell": shell, "grains": grains}


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
        "SUM_GrindingCell_ThreeJawChuck": "precision faceplate and stepped soft jaws",
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

    # The process shot looks through the open doors along +Y.  A layered wet
    # stainless back wall gives the close-up a believable sealed-machine scale
    # instead of reading as isolated parts against a black void.
    splash_back = modeling._box(
        "SUM_GrindingCell_ProcessChamber_WetSplashBack",
        (3.02, 0.055, 2.18),
        collection,
        location=(0.05, 1.395, 1.93),
        parent=root,
        material=steel,
        bevel=0.014,
        role="wet_stainless_process_chamber_back_wall",
    )
    _tag(splash_back, "wet_steel", "wet_stainless_process_chamber_back_wall")
    splash_panels = modeling._box_array(
        "SUM_GrindingCell_ProcessChamber_WetServicePanels",
        [
            ((-0.94, 1.355, 1.93), (0.88, 0.026, 2.02)),
            ((0.05, 1.355, 1.93), (0.88, 0.026, 2.02)),
            ((1.04, 1.355, 1.93), (0.88, 0.026, 2.02)),
        ],
        collection,
        parent=root,
        material=dark,
        bevel=0.012,
        role="removable_wet_process_chamber_panels",
    )
    _tag(splash_panels, "wet_steel", "removable_wet_process_chamber_panels")
    panel_reveals = modeling._box_array(
        "SUM_GrindingCell_ProcessChamber_WetPanelReveals",
        [
            ((-0.445, 1.328, 1.93), (0.018, 0.018, 2.00)),
            ((0.545, 1.328, 1.93), (0.018, 0.018, 2.00)),
            ((0.05, 1.328, 0.955), (2.86, 0.018, 0.026)),
        ],
        collection,
        parent=root,
        material=black,
        bevel=0.003,
        role="wet_chamber_gasketed_panel_reveals",
    )
    _tag(panel_reveals, "dark_metal", "wet_chamber_gasketed_panel_reveals")
    fastener_positions = [
        (x, z)
        for x in (-1.32, -0.56, -0.33, 0.43, 0.66, 1.42)
        for z in (1.05, 2.82)
    ]
    _panel_fasteners(
        "SUM_GrindingCell_ProcessChamber_BackPanelBolt",
        fastener_positions,
        1.315,
        collection,
        parent=root,
        material=steel,
    )
    drain_lips = modeling._box_array(
        "SUM_GrindingCell_ProcessChamber_DrainLips",
        [
            ((-0.70, 1.28, 0.92), (1.20, 0.13, 0.065)),
            ((0.76, 1.28, 0.92), (1.20, 0.13, 0.065)),
        ],
        collection,
        parent=root,
        material=steel,
        bevel=0.010,
        role="formed_stainless_coolant_return_lips",
    )
    _tag(drain_lips, "wet_steel", "formed_stainless_coolant_return_lips")

    sight_body = modeling._cylinder_between(
        "SUM_GrindingCell_ProcessChamber_CoolantSightGlassBody",
        (1.29, 1.285, 1.22),
        (1.29, 1.335, 1.22),
        0.072,
        collection,
        parent=root,
        material=black,
        segments=48,
        bevel=0.006,
        role="coolant_return_sight_glass_bezel",
    )
    _tag(sight_body, "dark_metal", "coolant_return_sight_glass_bezel")
    sight_window = modeling._cylinder_between(
        "SUM_GrindingCell_ProcessChamber_CoolantSightGlassWindow",
        (1.29, 1.275, 1.22),
        (1.29, 1.300, 1.22),
        0.052,
        collection,
        parent=root,
        material=materials["safety_glass"],
        segments=48,
        bevel=0.003,
        role="coolant_return_sight_glass_window",
    )
    _tag(sight_window, "screen_glass", "coolant_return_sight_glass_window")

    # Dense process-side hardware based on the photographed wet grinder.  The
    # plate is deliberately behind the chuck plane so it reads as real machine
    # structure without hiding the open raceway or the grinding quill.
    fixture_plate = modeling._box(
        "SUM_GrindingCell_ProcessFixturePlate",
        (0.055, 1.12, 1.42),
        collection,
        location=(-0.145, 0.02, 1.84),
        parent=root,
        material=steel,
        bevel=0.018,
        role="machined_process_fixture_backplate",
    )
    _tag(fixture_plate, "wet_steel", "machined_process_fixture_backplate")
    fixture_reveal = modeling._box(
        "SUM_GrindingCell_ProcessFixturePlate_Reveal",
        (0.020, 1.00, 1.30),
        collection,
        location=(-0.110, 0.02, 1.84),
        parent=root,
        material=black,
        bevel=0.014,
        role="sealed_fixture_plate_reveal",
    )
    _tag(fixture_reveal, "dark_metal", "sealed_fixture_plate_reveal")

    for index, (y, z, radius) in enumerate(
        ((-0.38, 2.30, 0.090), (-0.42, 1.38, 0.072), (0.41, 2.48, 0.060)),
        start=1,
    ):
        bezel = modeling._cylinder_between(
            f"SUM_GrindingCell_ProcessPlate_ServicePort_{index:02d}",
            (-0.130, y, z),
            (-0.065, y, z),
            radius,
            collection,
            parent=root,
            material=black,
            segments=64,
            bevel=0.006,
            role="sealed_process_plate_service_port",
        )
        _tag(bezel, "dark_metal", "sealed_process_plate_service_port")
        inner = modeling._cylinder_between(
            f"SUM_GrindingCell_ProcessPlate_ServicePortInner_{index:02d}",
            (-0.058, y, z),
            (-0.040, y, z),
            radius * 0.68,
            collection,
            parent=root,
            material=dark,
            segments=64,
            bevel=0.004,
            role="recessed_process_plate_service_port_inner",
        )
        _tag(inner, "cast_iron", "recessed_process_plate_service_port_inner")

    plate_fasteners = [
        (y, z)
        for y in (-0.48, -0.18, 0.18, 0.48)
        for z in (1.20, 1.52, 2.12, 2.46)
        if not (-0.28 < y < 0.28 and 1.55 < z < 2.10)
    ]
    for index, (y, z) in enumerate(plate_fasteners, start=1):
        fastener = modeling._cylinder_between(
            f"SUM_GrindingCell_ProcessPlate_Fastener_{index:02d}",
            (-0.070, y, z),
            (-0.030, y, z),
            0.009,
            collection,
            parent=root,
            material=steel,
            segments=6,
            bevel=0.0015,
            role="process_plate_socket_fastener",
        )
        _tag(fastener, "machined_steel", "process_plate_socket_fastener")

    # Two compact hydraulic cylinders and their clamped rigid lines provide the
    # loading/locating logic visible in a real bearing grinder.  Every line
    # terminates at a fitting; nothing is left floating in the chamber.
    for index, y in enumerate((-0.36, 0.38), start=1):
        cylinder = modeling._cylinder_between(
            f"SUM_GrindingCell_LocatingCylinder_{index:02d}",
            (-0.035, y, 2.42),
            (-0.035, y, 2.68),
            0.048,
            collection,
            parent=root,
            material=dark,
            segments=48,
            bevel=0.006,
            role="sealed_hydraulic_locating_cylinder",
        )
        _tag(cylinder, "dark_metal", "sealed_hydraulic_locating_cylinder")
        rod = modeling._cylinder_between(
            f"SUM_GrindingCell_LocatingCylinderRod_{index:02d}",
            (-0.035, y, 2.25),
            (-0.035, y, 2.45),
            0.018,
            collection,
            parent=root,
            material=steel,
            segments=40,
            bevel=0.002,
            role="ground_hydraulic_cylinder_rod",
        )
        _tag(rod, "machined_steel", "ground_hydraulic_cylinder_rod")
        line = modeling._bezier_tube(
            f"SUM_GrindingCell_LocatingCylinderLine_{index:02d}",
            [
                (-0.025, y, 2.65),
                (-0.015, y * 0.86, 2.80),
                (0.10, y * 0.72, 2.88),
                (0.28, y * 0.72, 2.88),
            ],
            0.006,
            collection,
            parent=root,
            material=steel,
            role="clamped_stainless_hydraulic_cylinder_line",
            resolution=10,
        )
        _tag(line, "brushed_metal", "clamped_stainless_hydraulic_cylinder_line")

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
) -> None:
    dark = materials["paint_graphite"]
    steel = materials["machined_steel"]
    brushed = materials["brushed_steel"]

    pedestal = modeling._box(
        "SUM_GrindingCell_BAxis_GranitePedestal",
        (0.72, 0.66, 0.32),
        collection,
        location=(-0.72, 0.0, 1.15),
        parent=root,
        material=materials["fixture"],
        bevel=0.035,
        role="polymer_concrete_workhead_pedestal",
    )
    _tag(pedestal, "powder_coat", "polymer_concrete_workhead_pedestal")
    rotary_base = modeling._cylinder(
        "SUM_GrindingCell_BAxis_RotaryTable",
        0.31,
        0.12,
        collection,
        location=(-0.72, 0.0, 1.37),
        parent=root,
        material=dark,
        segments=72,
        bevel=0.012,
        role="hydrostatic_b_axis_rotary_table",
    )
    _tag(rotary_base, "dark_metal", "hydrostatic_b_axis_rotary_table")
    scale_ring = modeling._torus(
        "SUM_GrindingCell_BAxis_EncoderScale",
        0.272,
        0.012,
        collection,
        location=(-0.72, 0.0, 1.445),
        parent=root,
        material=steel,
        major_segments=96,
        minor_segments=12,
        role="b_axis_optical_encoder_scale_ring",
    )
    _tag(scale_ring, "brushed_metal", "b_axis_optical_encoder_scale_ring")

    headstock = modeling._box(
        "SUM_GrindingCell_Workhead_CastHeadstock",
        (0.46, 0.46, 0.44),
        collection,
        location=(-0.68, 0.0, 1.82),
        parent=root,
        material=materials["fixture"],
        bevel=0.038,
        role="ribbed_cast_iron_workhead_headstock",
    )
    _tag(headstock, "cast_iron", "ribbed_cast_iron_workhead_headstock")
    camera_side_panel = modeling._box(
        "SUM_GrindingCell_Workhead_CameraSideServicePanel",
        (0.30, 0.018, 0.25),
        collection,
        location=(-0.68, -0.239, 1.82),
        parent=root,
        material=dark,
        bevel=0.018,
        role="gasketed_workhead_side_service_panel",
    )
    _tag(
        camera_side_panel,
        "dark_metal",
        "gasketed_workhead_side_service_panel",
    )
    _panel_fasteners(
        "SUM_GrindingCell_Workhead_SidePanelBolt",
        [
            (-0.80, 1.72),
            (-0.56, 1.72),
            (-0.80, 1.92),
            (-0.56, 1.92),
        ],
        -0.258,
        collection,
        parent=root,
        material=steel,
    )
    workhead_nameplate = modeling._box(
        "SUM_GrindingCell_Workhead_IdentificationPlate",
        (0.17, 0.010, 0.052),
        collection,
        location=(-0.68, -0.269, 1.82),
        parent=root,
        material=steel,
        bevel=0.004,
        role="etched_workhead_identification_plate",
    )
    _tag(workhead_nameplate, "brushed_metal", "etched_workhead_identification_plate")
    headstock_cover = modeling._cylinder_between(
        "SUM_GrindingCell_Workhead_RearServiceCover",
        (-0.98, 0.0, 1.82),
        (-0.93, 0.0, 1.82),
        0.168,
        collection,
        parent=root,
        material=dark,
        segments=72,
        bevel=0.010,
        role="gasketed_workhead_rear_service_cover",
    )
    _tag(headstock_cover, "dark_metal", "gasketed_workhead_rear_service_cover")
    rear_cover_bolts = modeling._add_bolt_circle(
        "SUM_GrindingCell_Workhead_RearServiceCover",
        (-0.99, 0.0, 1.82),
        (1.0, 0.0, 0.0),
        0.136,
        0.009,
        0.022,
        8,
        collection,
        parent=root,
        material=steel,
    )
    for bolt in rear_cover_bolts:
        _tag(bolt, "machined_steel", "workhead_rear_service_cover_fastener")
    workhead_ribs = modeling._box_array(
        "SUM_GrindingCell_Workhead_CastRibs",
        [
            ((-0.82, -0.23, 1.82), (0.035, 0.040, 0.32)),
            ((-0.68, -0.23, 1.82), (0.035, 0.040, 0.32)),
            ((-0.54, -0.23, 1.82), (0.035, 0.040, 0.32)),
            ((-0.82, 0.23, 1.82), (0.035, 0.040, 0.32)),
            ((-0.68, 0.23, 1.82), (0.035, 0.040, 0.32)),
            ((-0.54, 0.23, 1.82), (0.035, 0.040, 0.32)),
        ],
        collection,
        parent=root,
        material=dark,
        bevel=0.012,
        role="cast_workhead_stiffening_ribs",
    )
    _tag(workhead_ribs, "cast_iron", "cast_workhead_stiffening_ribs")
    workhead_mounts = modeling._box_array(
        "SUM_GrindingCell_Workhead_LevellingFeet",
        [
            ((-0.82, -0.19, 1.53), (0.12, 0.10, 0.06)),
            ((-0.82, 0.19, 1.53), (0.12, 0.10, 0.06)),
            ((-0.56, -0.19, 1.53), (0.12, 0.10, 0.06)),
            ((-0.56, 0.19, 1.53), (0.12, 0.10, 0.06)),
        ],
        collection,
        parent=root,
        material=steel,
        bevel=0.012,
        role="precision_workhead_levelling_and_clamping_feet",
    )
    _tag(
        workhead_mounts,
        "brushed_metal",
        "precision_workhead_levelling_and_clamping_feet",
    )

    for index, x in enumerate((-0.82, -0.72, -0.62, -0.52), start=1):
        fin = modeling._torus(
            f"SUM_GrindingCell_Workhead_CoolingFin_{index:02d}",
            0.205,
            0.011,
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
        0.128,
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
        (-0.97, 0.0, 1.82),
        (-0.90, 0.0, 1.82),
        0.164,
        collection,
        parent=root,
        material=dark,
        segments=64,
        bevel=0.010,
        role="workhead_rear_service_cap",
    )
    _tag(service_cap, "dark_metal", "workhead_rear_service_cap")

    spindle_labyrinth = modeling._cylinder_between(
        "SUM_GrindingCell_Workhead_SpindleLabyrinth",
        (-0.20, 0.0, 1.82),
        (-0.08, 0.0, 1.82),
        0.151,
        collection,
        parent=root,
        material=dark,
        segments=72,
        bevel=0.008,
        role="workhead_spindle_labyrinth_seal_housing",
    )
    _tag(spindle_labyrinth, "dark_metal", "workhead_spindle_labyrinth_seal_housing")
    for index, x in enumerate((-0.165, -0.125, -0.085), start=1):
        ring = modeling._torus(
            f"SUM_GrindingCell_Workhead_LabyrinthRing_{index:02d}",
            0.144,
            0.0045,
            collection,
            location=(x, 0.0, 1.82),
            rotation=(0.0, math.pi * 0.5, 0.0),
            parent=root,
            material=steel,
            major_segments=72,
            minor_segments=10,
            role="workhead_spindle_labyrinth_seal_ring",
        )
        _tag(ring, "brushed_metal", "workhead_spindle_labyrinth_seal_ring")

    lubrication_line = modeling._bezier_tube(
        "SUM_GrindingCell_Workhead_BearingLubricationLine",
        [
            (-0.92, -0.34, 2.12),
            (-0.70, -0.37, 2.18),
            (-0.40, -0.28, 2.08),
            (-0.27, -0.18, 1.98),
        ],
        0.006,
        collection,
        parent=root,
        material=materials["rubber"],
        role="metered_workhead_bearing_lubrication_line",
        resolution=10,
    )
    _tag(
        lubrication_line,
        "rubber",
        "metered_workhead_bearing_lubrication_line",
    )
    lubrication_line.hide_render = True
    lubrication_line["sum_visibility_policy"] = "service-side only; excluded from hero camera"
    lube_fitting = modeling._cylinder_between(
        "SUM_GrindingCell_Workhead_LubricationFitting",
        (-0.31, -0.22, 2.02),
        (-0.25, -0.17, 1.97),
        0.014,
        collection,
        parent=root,
        material=steel,
        segments=12,
        bevel=0.002,
        role="workhead_bearing_metering_fitting",
    )
    _tag(lube_fitting, "machined_steel", "workhead_bearing_metering_fitting")

    hydraulic_lines = (
        (
            "ChuckClamp",
            [
                (-1.10, 0.26, 2.06),
                (-0.94, 0.31, 2.18),
                (-0.58, 0.29, 2.17),
                (-0.32, 0.18, 2.04),
            ],
        ),
        (
            "SpindleCooling",
            [
                (-1.06, 0.30, 2.00),
                (-0.86, 0.37, 2.11),
                (-0.54, 0.34, 2.10),
                (-0.30, 0.22, 1.98),
            ],
        ),
    )
    for line_name, points in hydraulic_lines:
        line = modeling._bezier_tube(
            f"SUM_GrindingCell_Workhead_{line_name}Line",
            points,
            0.008,
            collection,
            parent=root,
            material=materials["rubber"],
            role="secured_workhead_hydraulic_service_line",
            resolution=12,
        )
        _tag(line, "rubber", "secured_workhead_hydraulic_service_line")
        line.hide_render = True
        line["sum_visibility_policy"] = "service-side only; excluded from hero camera"

    faceplate = modeling._annular_prism(
        "SUM_GrindingCell_ChuckPrecisionFaceplate",
        0.255,
        0.074,
        0.046,
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
        0.218,
        0.008,
        0.030,
        12,
        collection,
        parent=root,
        material=steel,
    )
    for bolt in bolts:
        _tag(bolt, "brushed_metal", "chuck_faceplate_fastener")

    # A ground axial backstop and three stepped hydraulic jaws locate the ring
    # without covering its raceway. The jaws sit behind the workpiece exactly
    # as they do in the photographed machine, leaving the bore open to the
    # horizontal grinding quill.
    backstop = modeling._annular_prism(
        "SUM_GrindingCell_ChuckGroundBackstopRing",
        0.230,
        0.207,
        0.028,
        collection,
        location=(0.030, 0.0, 1.82),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=root,
        material=brushed,
        segments=128,
        bevel=0.003,
        role="ground_axial_bearing_ring_backstop",
    )
    _tag(backstop, "machined_steel", "ground_axial_bearing_ring_backstop")

    jaw_parts = []
    for index in range(3):
        angle = math.radians(60.0) + math.tau * index / 3.0
        radial_y = math.cos(angle)
        radial_z = math.sin(angle)
        jaw_parts.extend(
            (
                (
                    (0.052, radial_y * 0.216, 1.82 + radial_z * 0.216),
                    (0.11, 0.060, 0.060),
                ),
                (
                    (0.118, radial_y * 0.198, 1.82 + radial_z * 0.198),
                    (0.074, 0.046, 0.046),
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

    for index in range(3):
        angle = math.radians(60.0) + math.tau * index / 3.0
        radial = Vector((0.0, math.cos(angle), math.sin(angle)))
        cylinder = modeling._cylinder_between(
            f"SUM_GrindingCell_ChuckHydraulicPlunger_{index + 1:02d}",
            tuple(Vector((-0.035, 0.0, 1.82)) + radial * 0.228),
            tuple(Vector((0.042, 0.0, 1.82)) + radial * 0.228),
            0.022,
            collection,
            parent=root,
            material=materials["black_oxide"],
            segments=32,
            bevel=0.004,
            role="sealed_radial_hydraulic_chuck_plunger",
        )
        _tag(cylinder, "dark_metal", "sealed_radial_hydraulic_chuck_plunger")

    workpiece_guard = modeling._torus(
        "SUM_GrindingCell_WorkpieceSplashGuardLip",
        0.216,
        0.009,
        collection,
        location=(-0.010, 0.0, 1.82),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=root,
        material=materials["brushed_steel"],
        major_segments=112,
        minor_segments=12,
        role="formed_stainless_workpiece_splash_guard_lip",
    )
    _tag(workpiece_guard, "wet_steel", "formed_stainless_workpiece_splash_guard_lip")

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
        (0.34, 0.44, 0.34),
        collection,
        location=(1.18, wheel_y, 1.45),
        parent=root,
        material=dark,
        bevel=0.032,
        role="ribbed_cast_spindle_support",
    )
    _tag(spindle_support, "powder_coat", "ribbed_cast_spindle_support")
    spindle_jacket = modeling._box(
        "SUM_GrindingCell_HighSpeedSpindleCoolingJacket",
        (0.62, 0.40, 0.34),
        collection,
        location=(1.18, wheel_y, 1.82),
        parent=root,
        material=materials["fixture"],
        bevel=0.035,
        role="angular_liquid_cooled_spindle_jacket",
    )
    _tag(spindle_jacket, "cast_iron", "angular_liquid_cooled_spindle_jacket")
    spindle_jacket.hide_render = True
    spindle_jacket["sum_replaced_by"] = "cylindrical liquid-cooled spindle cartridge"
    jacket_covers = modeling._box_array(
        "SUM_GrindingCell_SpindleJacket_ServiceCovers",
        [
            ((1.18, wheel_y - 0.208, 1.82), (0.42, 0.020, 0.22)),
            ((1.18, wheel_y + 0.208, 1.82), (0.42, 0.020, 0.22)),
            ((1.18, wheel_y, 1.995), (0.40, 0.24, 0.020)),
        ],
        collection,
        parent=root,
        material=dark,
        bevel=0.016,
        role="gasketed_spindle_jacket_service_covers",
    )
    _tag(jacket_covers, "cast_iron", "gasketed_spindle_jacket_service_covers")
    jacket_covers.hide_render = True
    front_cover_fasteners = [
        (x, z)
        for x in (0.98, 1.38)
        for z in (1.72, 1.92)
    ]
    _panel_fasteners(
        "SUM_GrindingCell_SpindleJacket_FrontCoverBolt",
        front_cover_fasteners,
        wheel_y - 0.228,
        collection,
        parent=root,
        material=steel,
    )
    spindle_nameplate = modeling._box(
        "SUM_GrindingCell_SpindleJacket_Nameplate",
        (0.18, 0.010, 0.058),
        collection,
        location=(1.18, wheel_y - 0.239, 1.82),
        parent=root,
        material=steel,
        bevel=0.004,
        role="engraved_high_speed_spindle_identification_plate",
    )
    _tag(
        spindle_nameplate,
        "brushed_metal",
        "engraved_high_speed_spindle_identification_plate",
    )
    spindle_ribs = modeling._box_array(
        "SUM_GrindingCell_SpindleJacket_CastRibs",
        [
            ((0.98, wheel_y - 0.218, 1.82), (0.032, 0.040, 0.25)),
            ((1.11, wheel_y - 0.218, 1.82), (0.032, 0.040, 0.25)),
            ((1.24, wheel_y - 0.218, 1.82), (0.032, 0.040, 0.25)),
            ((1.37, wheel_y - 0.218, 1.82), (0.032, 0.040, 0.25)),
        ],
        collection,
        parent=root,
        material=materials["fixture"],
        bevel=0.010,
        role="high_stiffness_spindle_jacket_cast_ribs",
    )
    _tag(spindle_ribs, "cast_iron", "high_stiffness_spindle_jacket_cast_ribs")
    spindle_ribs.hide_render = True
    spindle_motor = modeling._cylinder_between(
        "SUM_GrindingCell_HighSpeedSpindleMotor",
        (0.82, wheel_y, 1.82),
        (1.43, wheel_y, 1.82),
        0.180,
        collection,
        parent=root,
        material=dark,
        segments=72,
        bevel=0.018,
        role="liquid_cooled_high_speed_spindle_motor",
    )
    _tag(spindle_motor, "dark_metal", "liquid_cooled_high_speed_spindle_motor")
    for index, (start_x, end_x, radius) in enumerate(
        ((0.76, 0.88, 0.205), (0.88, 1.34, 0.188), (1.34, 1.46, 0.198)),
        start=1,
    ):
        cartridge = modeling._cylinder_between(
            f"SUM_GrindingCell_SpindleCartridgeSection_{index:02d}",
            (start_x, wheel_y, 1.82),
            (end_x, wheel_y, 1.82),
            radius,
            collection,
            parent=root,
            material=materials["fixture"] if index == 2 else dark,
            segments=96,
            bevel=0.012,
            role="precision_liquid_cooled_spindle_cartridge_section",
        )
        _tag(
            cartridge,
            "cast_iron" if index == 2 else "dark_metal",
            "precision_liquid_cooled_spindle_cartridge_section",
        )
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
    rear_gland = modeling._cylinder_between(
        "SUM_GrindingCell_SpindleMotorPowerCableGland",
        (1.54, wheel_y, 1.93),
        (1.66, wheel_y, 1.93),
        0.041,
        collection,
        parent=root,
        material=materials["black_oxide"],
        segments=12,
        bevel=0.004,
        role="sealed_spindle_motor_power_cable_gland",
    )
    _tag(rear_gland, "dark_metal", "sealed_spindle_motor_power_cable_gland")
    power_cable = modeling._bezier_tube(
        "SUM_GrindingCell_SpindleMotor_PowerCable",
        [
            (1.65, wheel_y + 0.01, 1.93),
            (1.75, wheel_y + 0.10, 2.08),
            (1.76, wheel_y + 0.34, 2.34),
            (1.58, wheel_y + 0.58, 2.54),
        ],
        0.006,
        collection,
        parent=root,
        material=materials["rubber"],
        role="shielded_high_speed_spindle_power_cable",
        resolution=12,
    )
    _tag(power_cable, "rubber", "shielded_high_speed_spindle_power_cable")
    power_cable.hide_render = True
    power_cable["sum_visibility_policy"] = "rear-routed; excluded from hero camera"

    service_lines = (
        (
            "CoolingSupply",
            [
                (1.43, wheel_y + 0.19, 1.99),
                (1.52, wheel_y + 0.25, 2.12),
                (1.48, wheel_y + 0.43, 2.32),
                (1.33, wheel_y + 0.58, 2.48),
            ],
        ),
        (
            "CoolingReturn",
            [
                (1.31, wheel_y + 0.20, 2.02),
                (1.38, wheel_y + 0.30, 2.16),
                (1.34, wheel_y + 0.46, 2.35),
                (1.21, wheel_y + 0.60, 2.49),
            ],
        ),
    )
    for line_name, points in service_lines:
        line = modeling._bezier_tube(
            f"SUM_GrindingCell_SpindleMotor_{line_name}",
            points,
            0.006,
            collection,
            parent=root,
            material=materials["rubber"],
            role="secured_spindle_cooling_service_line",
            resolution=12,
        )
        _tag(line, "rubber", "secured_spindle_cooling_service_line")
        line.hide_render = True
        line["sum_visibility_policy"] = "rear-routed; excluded from hero camera"
    service_line_clamps = modeling._box_array(
        "SUM_GrindingCell_SpindleMotor_ServiceLineClamps",
        [
            ((1.39, wheel_y + 0.245, 2.075), (0.11, 0.024, 0.032)),
            ((1.42, wheel_y + 0.405, 2.285), (0.11, 0.024, 0.032)),
        ],
        collection,
        parent=root,
        material=steel,
        bevel=0.005,
        role="stainless_spindle_service_line_clamps",
    )
    _tag(
        service_line_clamps,
        "brushed_metal",
        "stainless_spindle_service_line_clamps",
    )
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

    nose_flange = modeling._cylinder_between(
        "SUM_GrindingCell_SpindleNose_Flange",
        (0.385, wheel_y, 1.82),
        (0.425, wheel_y, 1.82),
        0.094,
        collection,
        parent=root,
        material=steel,
        segments=72,
        bevel=0.006,
        role="precision_spindle_nose_mounting_flange",
    )
    _tag(nose_flange, "machined_steel", "precision_spindle_nose_mounting_flange")
    for index, (x, radius) in enumerate(
        ((0.350, 0.083), (0.320, 0.069), (0.286, 0.054)),
        start=1,
    ):
        nose_step = modeling._cylinder_between(
            f"SUM_GrindingCell_SpindleNose_SteppedAdapter_{index:02d}",
            (x - 0.030, wheel_y, 1.82),
            (x, wheel_y, 1.82),
            radius,
            collection,
            parent=root,
            material=steel,
            segments=72,
            bevel=0.003,
            role="ground_stepped_spindle_nose_adapter",
        )
        _tag(nose_step, "machined_steel", "ground_stepped_spindle_nose_adapter")
    for index, angle in enumerate(
        (math.radians(45.0), math.radians(135.0), math.radians(225.0), math.radians(315.0)),
        start=1,
    ):
        y = wheel_y + math.cos(angle) * 0.073
        z = 1.82 + math.sin(angle) * 0.073
        _hex_fastener(
            f"SUM_GrindingCell_SpindleNose_FlangeBolt_{index:02d}",
            (0.370, y, z),
            (0.405, y, z),
            0.009,
            collection,
            parent=root,
            material=steel,
            detail="precision_spindle_nose_flange_fastener",
        )

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
) -> list[bpy.types.Object]:
    manifold = modeling._box(
        "SUM_GrindingCell_CoolantManifold",
        (0.12, 0.16, 0.09),
        collection,
        location=(0.62, 0.44, 2.31),
        parent=root,
        material=materials["black_oxide"],
        bevel=0.010,
        role="high_pressure_coolant_manifold",
    )
    _tag(manifold, "dark_metal", "high_pressure_coolant_manifold")
    manifold_caps = []
    for index, z in enumerate((2.285, 2.335), start=1):
        manifold_caps.append(
            _hex_fastener(
                f"SUM_GrindingCell_CoolantManifold_Plug_{index:02d}",
                (0.555, 0.545, z),
                (0.555, 0.605, z),
                0.013,
                collection,
                parent=root,
                material=materials["machined_steel"],
                detail="threaded_high_pressure_coolant_manifold_plug",
            )
        )
    supply_hose = modeling._bezier_tube(
        "SUM_GrindingCell_Coolant_MainSupplyHose",
        [
            (0.68, 0.44, 2.32),
            (0.92, 0.56, 2.50),
            (1.10, 0.74, 2.70),
            (0.96, 0.92, 2.92),
        ],
        0.028,
        collection,
        parent=root,
        material=materials["rubber"],
        role="braided_high_pressure_coolant_supply_hose",
        resolution=12,
    )
    _tag(supply_hose, "rubber", "braided_high_pressure_coolant_supply_hose")
    supply_hose.hide_render = True
    supply_hose["sum_visibility_policy"] = "supply-side only; excluded from hero camera"
    for index, (start, end) in enumerate(
        (
            ((0.555, 0.545, 2.28), (0.555, 0.605, 2.28)),
            ((0.555, 0.545, 2.34), (0.555, 0.605, 2.34)),
        ),
        start=1,
    ):
        fitting = modeling._cylinder_between(
            f"SUM_GrindingCell_CoolantSupply_Fitting_{index:02d}",
            start,
            end,
            0.040,
            collection,
            parent=root,
            material=materials["machined_steel"],
            segments=12,
            bevel=0.004,
            role="hexagonal_high_pressure_coolant_hose_fitting",
        )
        _tag(fitting, "machined_steel", "hexagonal_high_pressure_coolant_hose_fitting")
    splash_objects: list[bpy.types.Object] = []
    coolant_feeds = (
        (
            ((0.62, 0.44, 2.31), (0.45, 0.37, 2.18), (0.28, 0.28, 2.05)),
            (0.17, 0.23, 1.97),
            0.0065,
        ),
        (
            ((0.62, 0.40, 2.28), (0.43, 0.32, 2.12), (0.25, 0.24, 1.99)),
            (0.14, 0.20, 1.92),
            0.0052,
        ),
    )
    for index, (points, nozzle_tip, jet_radius) in enumerate(
        coolant_feeds,
        start=1,
    ):
        line = modeling._bezier_tube(
            f"SUM_GrindingCell_HighPressureCoolantLine_{index:02d}",
            list(points),
            0.006,
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
            0.009,
            collection,
            parent=root,
            material=materials["black_oxide"],
            segments=20,
            bevel=0.002,
            role="focused_coolant_jet_nozzle",
        )
        _tag(nozzle, "dark_metal", "focused_coolant_jet_nozzle")
        nozzle_collar = modeling._cylinder_between(
            f"SUM_GrindingCell_CoolantJetNozzle_Collar_{index:02d}",
            points[-1],
            Vector(points[-1]).lerp(Vector(nozzle_tip), 0.38),
            0.015,
            collection,
            parent=root,
            material=materials["machined_steel"],
            segments=12,
            bevel=0.003,
            role="adjustable_coolant_nozzle_locking_collar",
        )
        _tag(
            nozzle_collar,
            "machined_steel",
            "adjustable_coolant_nozzle_locking_collar",
        )
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
            material=materials["coolant"],
            role="coherent_high_pressure_coolant_jet",
            resolution=8,
        )
        _tag(jet, "coolant", "coherent_coolant_stream_aimed_at_grinding_arc")
        ribbon_vertices: list[tuple[float, float, float]] = []
        ribbon_faces: list[tuple[int, int, int, int]] = []
        for station, center in enumerate((jet_start, jet_mid, jet_target)):
            width = (0.0040, 0.0065, 0.0100)[station]
            ribbon_vertices.extend(
                (
                    tuple(center + Vector((0.0, width, 0.0))),
                    tuple(center - Vector((0.0, width, 0.0))),
                )
            )
            if station:
                start = (station - 1) * 2
                ribbon_faces.append((start, start + 1, start + 3, start + 2))
        ribbon = modeling._mesh_object(
            f"SUM_GrindingCell_CoolantSplashSheet_Jet_{index:02d}",
            ribbon_vertices,
            ribbon_faces,
            collection,
            parent=root,
            material=materials["coolant"],
        )
        ribbon["sum_splash_phase"] = index * 0.31
        tagged_ribbon = _tag(
            ribbon,
            "coolant",
            "continuous_milky_coolant_jet_ribbon",
        )
        tagged_ribbon.hide_render = True
        tagged_ribbon["sum_visibility_policy"] = (
            "replaced by volumetric droplets in the process hold loop"
        )
        splash_objects.append(tagged_ribbon)

    # A wet grinding contact produces a continuous thin film plus a cloud of
    # fine ballistic droplets, not rigid radial filaments.  Keep the sheets
    # close to the contact so the wheel and raceway remain legible.
    rng = random.Random(7419)
    sheet_specs = (
        (Vector((-0.040, 0.18, 0.10)), 0.010),
        (Vector((0.025, 0.15, -0.12)), 0.008),
        (Vector((-0.020, 0.11, -0.18)), 0.006),
    )
    for index, (direction, width) in enumerate(sheet_specs, start=1):
        vertices: list[tuple[float, float, float]] = []
        faces: list[tuple[int, ...]] = []
        stations = 7
        for station in range(stations):
            t = station / (stations - 1)
            center = _CONTACT_POINT + direction * t
            center.z += 0.025 * math.sin(math.pi * t) - 0.035 * t * t
            half_width = width * (0.20 + 0.80 * t)
            vertices.extend(
                (
                    tuple(center + Vector((0.0, -half_width, 0.0))),
                    tuple(center + Vector((0.0, half_width, 0.0))),
                )
            )
            if station:
                start = (station - 1) * 2
                faces.append((start, start + 1, start + 3, start + 2))
        sheet = modeling._mesh_object(
            f"SUM_GrindingCell_CoolantSplashSheet_{index:02d}",
            vertices,
            faces,
            collection,
            parent=root,
            material=materials["coolant_mist"],
        )
        sheet["sum_splash_phase"] = (index - 1) / len(sheet_specs)
        tagged_sheet = _tag(
            sheet,
            "coolant_mist",
            "thin_tangential_coolant_splash_sheet",
        )
        tagged_sheet.hide_render = True
        tagged_sheet["sum_visibility_policy"] = (
            "replaced by volumetric droplets in the process hold loop"
        )
        splash_objects.append(tagged_sheet)

    for index in range(18):
        phase = index / 18.0
        azimuth = rng.uniform(-0.82, 0.82)
        travel = rng.uniform(0.045, 0.21)
        start = _CONTACT_POINT + Vector(
            (
                rng.uniform(-0.009, 0.009),
                rng.uniform(-0.006, 0.006),
                rng.uniform(-0.008, 0.008),
            )
        )
        end = start + Vector(
            (
                rng.uniform(-0.055, 0.055),
                math.cos(azimuth) * travel,
                math.sin(azimuth) * travel - rng.uniform(0.0, 0.055),
            )
        )
        droplet = modeling._sphere(
            f"SUM_GrindingCell_CoolantSplashDroplet_{index + 1:02d}",
            rng.uniform(0.0010, 0.0024),
            collection,
            location=tuple(end),
            parent=root,
            material=materials["coolant_mist"],
            segments=16,
            rings=8,
            role="coolant_splash_ballistic_droplet",
        )
        droplet.scale = (0.62, 0.62, rng.uniform(1.15, 2.0))
        droplet["sum_splash_phase"] = phase
        splash_objects.append(
            _tag(droplet, "coolant_mist", "coolant_splash_ballistic_droplet")
        )

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
    return splash_objects


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

    collection = modeling._child_collection(
        root_collection, "SUM_MODEL_PrecisionGrinderDetail"
    )
    _exclude_old_doors()
    _exclude_replaced_process_proxies()
    workhead_housing = bpy.data.objects.get("SUM_GrindingCell_Workhead_Housing")
    if workhead_housing is not None:
        workhead_housing.hide_render = True
        workhead_housing["sum_export_exclude"] = True
        workhead_housing["sum_replaced_by"] = "compact cast workhead with service detail"
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
        "B-axis, workhead, faceplate, stepped jaws, profiled raceway, "
        "layered CBN wheel, exposed grains, linear guides, bellows, servo, "
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
    grinding_anchor = bpy.data.objects.get("SUM_ANCHOR_GrindingContact")
    if grinding_anchor is not None:
        grinding_anchor.location = tuple(_CONTACT_POINT)
        grinding_anchor["contact_relationship"] = (
            "small horizontal CBN wheel tangent to large internal raceway"
        )
    wheel_detail = _build_cbn_wheel_detail(wheel_root, collection, materials)
    _build_process_chamber(chamber_root, collection, materials)
    _build_b_axis_and_workhead(detail_root, collection, materials)
    _build_grinding_slide(detail_root, collection, materials)
    coolant_splash = _build_coolant_and_dressing(detail_root, collection, materials)

    cell["door_state"] = "animated open during process shot"
    cell["process_detail_level"] = "foreground production"
    assets["grinder_detail"] = detail_root
    assets["grinder_chamber"] = chamber_root
    assets["grinding_raceway_band"] = raceway_band
    assets["grinding_wheel_detail"] = wheel_detail
    assets["grinding_contact_point_local"] = tuple(_CONTACT_POINT)
    assets["grinding_coolant_splash"] = coolant_splash
    assets["grinder_doors"] = (left_door, right_door)
    assets.setdefault("collections", {})["precision_grinder"] = collection
    bpy.context.view_layer.update()
    return assets
