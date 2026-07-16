"""V8 process-story set: one outer ring, four evidence events, one final door."""

from __future__ import annotations

import math
from typing import Any

import bpy

import modeling


COLLECTION_NAME = "SUM_MODEL_V8Story"


def _hide_tree(root: Any) -> None:
    if not isinstance(root, bpy.types.Object):
        return
    root.hide_render = True
    root["sum_export_exclude"] = True
    for child in root.children_recursive:
        child.hide_render = True
        child["sum_export_exclude"] = True


def _reset_collection(parent: bpy.types.Collection) -> bpy.types.Collection:
    existing = bpy.data.collections.get(COLLECTION_NAME)
    if existing is not None:
        modeling._remove_collection_tree(existing)
    return modeling._child_collection(parent, COLLECTION_NAME)


def _tag(obj: bpy.types.Object, lookdev: str, role: str) -> bpy.types.Object:
    obj["lookdev_role"] = lookdev
    obj["sum_part_role"] = role
    return obj


def _build_hero_ring(
    layout_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    ring = modeling._empty(
        "RING_HERO_01",
        collection,
        location=(0.0, -0.75, 0.58),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=layout_root,
        display_size=0.08,
    )
    ring["sum_asset_type"] = "single_traceable_bearing_outer_ring"
    ring["workpiece_id"] = "RING_HERO_01"
    ring["process"] = "outer-ring internal raceway wet grinding"
    ring["outer_diameter_m"] = 0.228
    ring["bore_diameter_m"] = 0.145
    ring["width_m"] = 0.052
    ring["continuity_policy"] = "same object from inbound AGV to outbound AGV"

    body = modeling._annular_prism(
        "RING_HERO_01_GroundSteelBody",
        0.114,
        0.0725,
        0.052,
        collection,
        parent=ring,
        material=materials["machined_steel"],
        segments=144,
        bevel=0.0032,
        role="bearing_outer_ring_ground_body",
    )
    _tag(body, "brushed_metal", "bearing_outer_ring_ground_body")
    raceway = modeling._torus(
        "RING_HERO_01_InternalRaceway",
        0.0825,
        0.0095,
        collection,
        parent=ring,
        material=materials["brushed_steel"],
        major_segments=144,
        minor_segments=24,
        role="bearing_outer_ring_internal_raceway_surface",
    )
    _tag(raceway, "brushed_metal", "bearing_outer_ring_internal_raceway_surface")
    wet_film = modeling._torus(
        "RING_HERO_01_RacewayWetFilm",
        0.0825,
        0.0098,
        collection,
        parent=ring,
        material=materials["safety_glass"],
        major_segments=144,
        minor_segments=20,
        role="centrifuged_raceway_coolant_wet_film",
    )
    _tag(wet_film, "coolant", "centrifuged_raceway_coolant_wet_film")

    datum = modeling._box(
        "RING_HERO_01_TraceDatum",
        (0.010, 0.022, 0.005),
        collection,
        location=(0.0, 0.101, 0.029),
        parent=ring,
        material=materials["black_oxide"],
        bevel=0.001,
        role="low_contrast_traceability_datum",
    )
    _tag(datum, "dark_metal", "low_contrast_traceability_datum")
    return ring


def _display_panel(
    name: str,
    location: tuple[float, float, float],
    rotation_z: float,
    width: float,
    height: float,
    parent: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    role: str,
) -> tuple[bpy.types.Object, bpy.types.Object]:
    panel = modeling._empty(
        f"{name}_Frame",
        collection,
        location=location,
        rotation=(0.0, 0.0, rotation_z),
        parent=parent,
        display_size=0.06,
    )
    panel["sum_part_role"] = role
    frame = modeling._box(
        f"{name}_Housing",
        (0.10, width + 0.14, height + 0.14),
        collection,
        parent=panel,
        material=materials["screen_frame"],
        bevel=0.025,
        role="sealed_industrial_hmi_housing",
    )
    _tag(frame, "dark_metal", "sealed_industrial_hmi_housing")
    display = modeling._display_surface(
        f"{name}_Display",
        width,
        height,
        collection,
        location=(-0.056, 0.0, 0.0),
        parent=panel,
        material=materials["screen_content"],
    )
    # The display mesh is mounted on the housing's -X face. Mirror its local
    # Y scale so evidence imagery reads correctly from the operator side.
    display.scale.y = -1.0
    display["sum_part_role"] = role
    display["lookdev_role"] = "screen_glass"
    return panel, display


def _build_scan_gate(
    layout_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, bpy.types.Object]:
    root = modeling._empty(
        "SUM_ASSET_V8_ScanReleaseGate",
        collection,
        location=(0.0, 6.2, 0.0),
        parent=layout_root,
        display_size=0.20,
    )
    root["sum_asset_type"] = "machine_vision_route_release_gate"
    for side in (-1.0, 1.0):
        post = modeling._box(
            f"SUM_V8_ScanGate_Post_{'L' if side < 0 else 'R'}",
            (0.14, 0.18, 2.45),
            collection,
            location=(side * 1.15, 0.0, 1.225),
            parent=root,
            material=materials["paint_graphite"],
            bevel=0.018,
            role="scan_gate_structural_post",
        )
        _tag(post, "dark_metal", "scan_gate_structural_post")
    header = modeling._box(
        "SUM_V8_ScanGate_Header",
        (2.44, 0.20, 0.16),
        collection,
        location=(0.0, 0.0, 2.38),
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.020,
        role="scan_gate_header",
    )
    _tag(header, "dark_metal", "scan_gate_header")
    scanner = modeling._cylinder_between(
        "SUM_V8_ScanGate_VisionHead",
        (0.0, -0.20, 2.22),
        (0.0, 0.02, 2.08),
        0.085,
        collection,
        parent=root,
        material=materials["screen_frame"],
        segments=40,
        bevel=0.006,
        role="industrial_vision_reader",
    )
    _tag(scanner, "screen_glass", "industrial_vision_reader")
    scan_line = modeling._box(
        "SUM_V8_ScanGate_TrackingLine",
        (0.28, 0.006, 0.006),
        collection,
        location=(0.0, -0.04, 0.68),
        parent=root,
        material=materials["indicator_green"],
        bevel=0.004,
        role="machine_vision_scan_line",
    )
    _tag(scan_line, "luminaire", "machine_vision_scan_line")
    beacon = modeling._cylinder(
        "SUM_V8_ScanGate_ReleaseBeacon",
        0.065,
        0.20,
        collection,
        location=(1.15, 0.0, 2.60),
        parent=root,
        material=materials["indicator_green"],
        segments=32,
        bevel=0.008,
        role="route_release_stack_light",
    )
    _tag(beacon, "luminaire", "route_release_stack_light")
    panel, display = _display_panel(
        "SUM_V8_ScanGate_ReleasePanel",
        (1.38, 0.10, 1.30),
        math.pi * 0.5,
        0.54,
        0.34,
        root,
        collection,
        materials,
        "notice_workflow_evidence_display",
    )
    return {"root": root, "scanner": scanner, "scan_line": scan_line, "beacon": beacon, "panel": panel, "display": display}


def _build_transfer_line(
    layout_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, Any]:
    root = modeling._empty(
        "SUM_ASSET_V8_RobotToGrinderTransfer",
        collection,
        parent=layout_root,
        display_size=0.20,
    )
    root["sum_asset_type"] = "servo_transfer_and_machine_loading_axis"
    root["process_logic"] = "robot places ring on nest; servo shuttle indexes; loader pushes ring into workhead"

    for side in (-1.0, 1.0):
        rail = modeling._box(
            f"SUM_V8_Transfer_GroundRail_{'L' if side < 0 else 'R'}",
            (0.075, 4.45, 0.070),
            collection,
            location=(0.25 + side * 0.23, 12.25, 0.76),
            parent=root,
            material=materials["machined_steel"],
            bevel=0.008,
            role="preloaded_robot_to_machine_linear_rail",
        )
        _tag(rail, "brushed_metal", "preloaded_robot_to_machine_linear_rail")
    cable_tray = modeling._box(
        "SUM_V8_Transfer_CableChainTray",
        (0.12, 4.35, 0.10),
        collection,
        location=(0.67, 12.25, 0.80),
        parent=root,
        material=materials["black_oxide"],
        bevel=0.010,
        role="covered_servo_cable_chain_tray",
    )
    _tag(cable_tray, "dark_metal", "covered_servo_cable_chain_tray")

    carriage = modeling._empty(
        "SUM_V8_Transfer_ServoCarriage",
        collection,
        location=(0.25, 10.15, 0.0),
        parent=root,
        display_size=0.10,
    )
    carriage["sum_part_role"] = "servo_indexing_transfer_carriage"
    deck = modeling._box(
        "SUM_V8_Transfer_CarriageDeck",
        (0.72, 0.78, 0.16),
        collection,
        location=(0.0, 0.0, 0.84),
        parent=carriage,
        material=materials["paint_graphite"],
        bevel=0.028,
        role="servo_transfer_carriage_deck",
    )
    _tag(deck, "powder_coat", "servo_transfer_carriage_deck")
    for side in (-1.0, 1.0):
        cradle = modeling._box(
            f"SUM_V8_Transfer_VNest_{'A' if side < 0 else 'B'}",
            (0.08, 0.18, 0.10),
            collection,
            location=(0.0, side * 0.10, 0.98),
            rotation=(0.0, math.radians(45.0) * side, 0.0),
            parent=carriage,
            material=materials["rubber"],
            bevel=0.018,
            role="replaceable_nonmarking_ring_v_nest",
        )
        _tag(cradle, "rubber", "replaceable_nonmarking_ring_v_nest")
    for side in (-1.0, 1.0):
        sensor = modeling._box(
            f"SUM_V8_Transfer_PartPresentSensor_{'L' if side < 0 else 'R'}",
            (0.055, 0.080, 0.055),
            collection,
            location=(side * 0.31, -0.27, 1.01),
            parent=carriage,
            material=materials["screen_frame"],
            bevel=0.008,
            role="opposed_part_present_photoeye",
        )
        _tag(sensor, "screen_glass", "opposed_part_present_photoeye")

    loader = modeling._empty(
        "SUM_V8_Transfer_MachineLoaderSlide",
        collection,
        location=(0.25, 14.25, 1.82),
        parent=root,
        display_size=0.10,
    )
    loader["sum_part_role"] = "telescopic_machine_loading_slide"
    cylinder = modeling._cylinder_between(
        "SUM_V8_Transfer_LoaderServoCylinder",
        (-0.42, 0.0, 0.0),
        (0.25, 0.0, 0.0),
        0.085,
        collection,
        parent=loader,
        material=materials["paint_graphite"],
        segments=56,
        bevel=0.010,
        role="sealed_electric_loader_cylinder",
    )
    _tag(cylinder, "powder_coat", "sealed_electric_loader_cylinder")
    ram = modeling._cylinder_between(
        "SUM_V8_Transfer_LoaderGroundRam",
        (0.12, 0.0, 0.0),
        (0.78, 0.0, 0.0),
        0.034,
        collection,
        parent=loader,
        material=materials["machined_steel"],
        segments=48,
        bevel=0.003,
        role="ground_machine_loader_ram",
    )
    _tag(ram, "brushed_metal", "ground_machine_loader_ram")
    load_head = modeling._cylinder_between(
        "SUM_V8_Transfer_LoaderExpandingHead",
        (0.74, 0.0, 0.0),
        (0.88, 0.0, 0.0),
        0.054,
        collection,
        parent=loader,
        material=materials["black_oxide"],
        segments=48,
        bevel=0.006,
        role="three_segment_internal_loading_mandrel",
    )
    _tag(load_head, "dark_metal", "three_segment_internal_loading_mandrel")
    for side in (-1.0, 1.0):
        airline = modeling._bezier_tube(
            f"SUM_V8_Transfer_LoaderAirline_{'A' if side < 0 else 'B'}",
            [(-0.36, side * 0.06, 0.07), (-0.05, side * 0.10, 0.10), (0.42, side * 0.08, 0.06)],
            0.009,
            collection,
            parent=loader,
            material=materials["rubber"],
            role="loader_gripper_pneumatic_line",
            resolution=8,
        )
        _tag(airline, "rubber", "loader_gripper_pneumatic_line")

    return {"root": root, "carriage": carriage, "loader": loader}


def _build_robot_hmi(
    layout_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, bpy.types.Object]:
    pedestal = modeling._box(
        "SUM_V8_RobotHMI_Pedestal",
        (0.22, 0.22, 1.25),
        collection,
        location=(1.25, 10.65, 0.625),
        parent=layout_root,
        material=materials["paint_graphite"],
        bevel=0.020,
        role="robot_cell_hmi_pedestal",
    )
    _tag(pedestal, "dark_metal", "robot_cell_hmi_pedestal")
    panel, display = _display_panel(
        "SUM_V8_RobotCell_TaktHMI",
        (1.25, 10.65, 1.62),
        math.pi * 0.5,
        0.86,
        0.54,
        layout_root,
        collection,
        materials,
        "takt_simulation_live_hmi",
    )
    return {"pedestal": pedestal, "panel": panel, "display": display}


def _cubic_belt_path(
    controls: tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ],
    samples: int = 48,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    centers: list[tuple[float, float]] = []
    normals: list[tuple[float, float]] = []
    p0, p1, p2, p3 = controls
    for index in range(samples + 1):
        t = index / samples
        u = 1.0 - t
        x = u**3 * p0[0] + 3.0 * u * u * t * p1[0] + 3.0 * u * t * t * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3.0 * u * u * t * p1[1] + 3.0 * u * t * t * p2[1] + t**3 * p3[1]
        dx = 3.0 * u * u * (p1[0] - p0[0]) + 6.0 * u * t * (p2[0] - p1[0]) + 3.0 * t * t * (p3[0] - p2[0])
        dy = 3.0 * u * u * (p1[1] - p0[1]) + 6.0 * u * t * (p2[1] - p1[1]) + 3.0 * t * t * (p3[1] - p2[1])
        length = max(math.hypot(dx, dy), 1.0e-6)
        centers.append((x, y))
        normals.append((-dy / length, dx / length))
    return centers, normals


def _belt_ribbon_geometry(
    centers: list[tuple[float, float]],
    normals: list[tuple[float, float]],
    width: float,
    top_z: float,
    thickness: float,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    half_width = width * 0.5
    bottom_z = top_z - thickness
    for (x, y), (nx, ny) in zip(centers, normals):
        vertices.extend(
            (
                (x + nx * half_width, y + ny * half_width, top_z),
                (x - nx * half_width, y - ny * half_width, top_z),
                (x + nx * half_width, y + ny * half_width, bottom_z),
                (x - nx * half_width, y - ny * half_width, bottom_z),
            )
        )
    for index in range(len(centers) - 1):
        offset = index * 4
        following = offset + 4
        faces.extend(
            (
                (offset, offset + 1, following + 1, following),
                (offset + 2, following + 2, following + 3, offset + 3),
                (offset, following, following + 2, offset + 2),
                (offset + 1, offset + 3, following + 3, following + 1),
            )
        )
    final = (len(centers) - 1) * 4
    faces.extend(((0, 2, 3, 1), (final, final + 1, final + 3, final + 2)))
    return vertices, faces


def _build_outfeed(
    layout_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, Any]:
    connector = modeling._empty(
        "SUM_ASSET_V8_GrinderOutfeedConnector",
        collection,
        parent=layout_root,
        display_size=0.14,
    )
    connector["sum_asset_type"] = "continuous_curved_wet_part_belt_conveyor"
    controls = ((2.55, 17.20), (2.55, 18.30), (1.20, 18.90), (1.20, 20.00))
    centers, normals = _cubic_belt_path(controls)
    tray_vertices, tray_faces = _belt_ribbon_geometry(centers, normals, 1.02, 0.94, 0.13)
    connector_tray = modeling._mesh_object(
        "SUM_V8_OutfeedConnector_CurvedDrainBed",
        tray_vertices,
        tray_faces,
        collection,
        parent=layout_root,
        material=materials["brushed_steel"],
        bevel=0.010,
        smooth=True,
    )
    _tag(connector_tray, "brushed_metal", "curved_belt_coolant_return_bed")
    belt_vertices, belt_faces = _belt_ribbon_geometry(centers, normals, 0.82, 1.07, 0.075)
    connector_belt = modeling._mesh_object(
        "SUM_V8_OutfeedConnector_ContinuousCurvedBelt",
        belt_vertices,
        belt_faces,
        collection,
        parent=layout_root,
        material=materials["rubber"],
        bevel=0.008,
        smooth=True,
    )
    _tag(connector_belt, "rubber", "continuous_curved_wet_part_conveyor_belt")
    connector_belt["path_control_points"] = [list(point) for point in controls]
    connector_belt["visual_motion"] = "workpiece follows cubic belt centerline"
    for side in (-1.0, 1.0):
        edge_points = []
        for (x, y), (nx, ny) in zip(centers, normals):
            edge_points.append((x + nx * 0.48 * side, y + ny * 0.48 * side, 1.12))
        rail = modeling._bezier_tube(
            f"SUM_V8_OutfeedConnector_CurvedRail_{'L' if side < 0 else 'R'}",
            edge_points,
            0.022,
            collection,
            parent=layout_root,
            material=materials["machined_steel"],
            role="curved_conveyor_low_profile_side_rail",
            resolution=8,
        )
        _tag(rail, "brushed_metal", "curved_conveyor_low_profile_side_rail")
    for index in (8, 24, 40):
        x, y = centers[index]
        leg = modeling._box(
            f"SUM_V8_OutfeedConnector_SupportLeg_{index:02d}",
            (0.12, 0.12, 0.82),
            collection,
            location=(x, y, 0.41),
            parent=layout_root,
            material=materials["paint_graphite"],
            bevel=0.014,
            role="curved_conveyor_floor_support",
        )
        _tag(leg, "powder_coat", "curved_conveyor_floor_support")

    root = modeling._empty(
        "SUM_ASSET_V8_OutfeedAirKnife",
        collection,
        location=(1.20, 20.0, 0.0),
        parent=layout_root,
        display_size=0.16,
    )
    root["sum_asset_type"] = "wet_part_outfeed_and_two_stage_air_knife"
    tray = modeling._box(
        "SUM_V8_Outfeed_DrainTray",
        (1.35, 1.65, 0.12),
        collection,
        location=(0.0, 0.0, 0.74),
        parent=root,
        material=materials["brushed_steel"],
        bevel=0.025,
        role="sloped_outfeed_drain_tray",
    )
    _tag(tray, "brushed_metal", "sloped_outfeed_drain_tray")
    straight_belt = modeling._box(
        "SUM_V8_Outfeed_ContinuousAirKnifeBelt",
        (0.82, 1.52, 0.075),
        collection,
        location=(0.0, 0.0, 1.0325),
        parent=root,
        material=materials["rubber"],
        bevel=0.018,
        role="continuous_air_knife_station_conveyor_belt",
    )
    _tag(straight_belt, "rubber", "continuous_air_knife_station_conveyor_belt")
    belts = [connector_belt, straight_belt]
    carrier = modeling._empty(
        "SUM_V8_Outfeed_TrackedNestCarrier",
        collection,
        location=(2.55, 17.20, 0.0),
        parent=layout_root,
        display_size=0.06,
    )
    carrier["sum_asset_type"] = "side_flex_belt_workpiece_nest"
    carrier["handling_orientation"] = "outer ring lies flat with axis vertical"
    carrier_base = modeling._cylinder_between(
        "SUM_V8_Outfeed_NestCarrierBase",
        (0.0, 0.0, 1.074),
        (0.0, 0.0, 1.094),
        0.145,
        collection,
        parent=carrier,
        material=materials["paint_graphite"],
        segments=64,
        bevel=0.006,
        role="curved_belt_low_profile_workpiece_carrier",
    )
    _tag(carrier_base, "fixture_dark", "curved_belt_low_profile_workpiece_carrier")
    for index in range(3):
        angle = math.tau * index / 3.0
        pad = modeling._box(
            f"SUM_V8_Outfeed_NestCarrierSupportPad_{index + 1:02d}",
            (0.040, 0.026, 0.016),
            collection,
            location=(math.cos(angle) * 0.080, math.sin(angle) * 0.080, 1.102),
            rotation=(0.0, 0.0, angle),
            parent=carrier,
            material=materials["rubber"],
            bevel=0.005,
            role="nonmarking_three_point_ring_support",
        )
        _tag(pad, "rubber", "nonmarking_three_point_ring_support")
    support = modeling._box_array(
        "SUM_V8_Outfeed_BeltSideFrames",
        (
            ((-0.56, 0.0, 1.00), (0.10, 1.42, 0.26)),
            ((0.56, 0.0, 1.00), (0.10, 1.42, 0.26)),
        ),
        collection,
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.018,
        role="outfeed_belt_side_frame",
    )
    _tag(support, "powder_coat", "outfeed_belt_side_frame")
    manifold = modeling._box(
        "SUM_V8_AirKnife_RegulatorManifold",
        (0.18, 0.28, 0.20),
        collection,
        location=(0.58, -0.50, 1.54),
        parent=root,
        material=materials["brushed_steel"],
        bevel=0.014,
        role="two_stage_air_knife_regulator_manifold",
    )
    _tag(manifold, "brushed_metal", "two_stage_air_knife_regulator_manifold")
    for index, y in enumerate((-0.22, 0.26), start=1):
        nozzle = modeling._box(
            f"SUM_V8_AirKnife_Nozzle_{index:02d}",
            (0.52, 0.06, 0.08),
            collection,
            location=(0.0, y, 1.55),
            rotation=(0.0, math.radians(18.0), 0.0),
            parent=root,
            material=materials["black_oxide"],
            bevel=0.010,
            role="two_stage_air_knife_nozzle",
        )
        _tag(nozzle, "dark_metal", "two_stage_air_knife_nozzle")
        hose = modeling._bezier_tube(
            f"SUM_V8_AirKnife_Hose_{index:02d}",
            [(0.58, -0.50, 1.54), (0.56, y, 1.72), (0.24, y, 1.60)],
            0.010,
            collection,
            parent=root,
            material=materials["rubber"],
            role="air_knife_flexible_supply_hose",
            resolution=8,
        )
        _tag(hose, "rubber", "air_knife_flexible_supply_hose")
    return {
        "root": root,
        "connector": connector,
        "tray": tray,
        "belts": belts,
        "connector_belt": connector_belt,
        "carrier": carrier,
    }


def _build_inspection(
    layout_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, Any]:
    root = modeling._empty(
        "SUM_ASSET_V8_InlineInspection",
        collection,
        location=(-2.20, 25.0, 0.0),
        parent=layout_root,
        display_size=0.18,
    )
    root["sum_asset_type"] = "inline_bearing_raceway_inspection_cell"
    base = modeling._box(
        "SUM_V8_Inspection_GraniteBase",
        (1.65, 1.45, 0.72),
        collection,
        location=(0.0, 0.0, 0.36),
        parent=root,
        material=materials["fixture"],
        bevel=0.035,
        role="inspection_polymer_concrete_base",
    )
    _tag(base, "powder_coat", "inspection_polymer_concrete_base")
    rotary = modeling._empty(
        "SUM_V8_Inspection_RotaryAirBearingAxis",
        collection,
        parent=root,
        display_size=0.08,
    )
    rotary["sum_asset_type"] = "precision_vertical_axis_air_bearing_table"
    rotary["workpiece_orientation"] = "flat, bearing axis vertical"
    rotary_housing = modeling._cylinder_between(
        "SUM_V8_Inspection_RotaryAirBearingHousing",
        (0.0, 0.0, 0.72),
        (0.0, 0.0, 0.90),
        0.34,
        collection,
        parent=root,
        material=materials["paint_graphite"],
        segments=64,
        bevel=0.018,
        role="inspection_air_bearing_rotary_housing",
    )
    _tag(rotary_housing, "powder_coat", "inspection_air_bearing_rotary_housing")
    platter = modeling._cylinder_between(
        "SUM_V8_Inspection_PrecisionRotaryPlatter",
        (0.0, 0.0, 0.90),
        (0.0, 0.0, 1.040),
        0.285,
        collection,
        parent=rotary,
        material=materials["black_oxide"],
        segments=96,
        bevel=0.010,
        role="inspection_precision_rotary_platter",
    )
    _tag(platter, "fixture_dark", "inspection_precision_rotary_platter")
    rotary_assets: list[bpy.types.Object] = [rotary]
    for index in range(3):
        angle = math.tau * index / 3.0
        support = modeling._box(
            f"SUM_V8_Inspection_CeramicFaceSupport_{index + 1:02d}",
            (0.046, 0.030, 0.030),
            collection,
            location=(math.cos(angle) * 0.082, math.sin(angle) * 0.082, 1.055),
            rotation=(0.0, 0.0, angle),
            parent=rotary,
            material=materials["fixture"],
            bevel=0.005,
            role="inspection_three_point_ceramic_face_support",
        )
        _tag(support, "fixture", "inspection_three_point_ceramic_face_support")
        locator = modeling._box(
            f"SUM_V8_Inspection_ODCenteringFinger_{index + 1:02d}",
            (0.030, 0.024, 0.085),
            collection,
            location=(math.cos(angle) * 0.132, math.sin(angle) * 0.132, 1.080),
            rotation=(0.0, 0.0, angle),
            parent=rotary,
            material=materials["black_oxide"],
            bevel=0.006,
            role="inspection_retractable_od_centering_finger",
        )
        _tag(locator, "dark_metal", "inspection_retractable_od_centering_finger")
    bridge = modeling._box_array(
        "SUM_V8_Inspection_GaugeBridge",
        (
            ((-0.64, 0.0, 1.58), (0.10, 0.16, 1.48)),
            ((0.64, 0.0, 1.58), (0.10, 0.16, 1.48)),
            ((0.0, 0.0, 2.28), (1.38, 0.16, 0.12)),
        ),
        collection,
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.020,
        role="inspection_gauge_bridge",
    )
    _tag(bridge, "dark_metal", "inspection_gauge_bridge")
    probe = modeling._empty(
        "SUM_V8_Inspection_RacewayProbe",
        collection,
        parent=root,
        display_size=0.04,
    )
    probe["sum_asset_type"] = "servo_lowered_internal_raceway_stylus"
    probe_stem = modeling._cylinder_between(
        "SUM_V8_Inspection_ProbeStem",
        (0.0, 0.0, 1.76),
        (0.0, 0.0, 1.145),
        0.022,
        collection,
        parent=probe,
        material=materials["machined_steel"],
        segments=32,
        bevel=0.004,
        role="raceway_probe_vertical_stem",
    )
    _tag(probe_stem, "brushed_metal", "raceway_probe_vertical_stem")
    stylus = modeling._cylinder_between(
        "SUM_V8_Inspection_InternalRacewayStylus",
        (0.0, 0.0, 1.145),
        (0.073, 0.0, 1.145),
        0.010,
        collection,
        parent=probe,
        material=materials["machined_steel"],
        segments=24,
        bevel=0.003,
        role="internal_raceway_radial_stylus",
    )
    _tag(stylus, "brushed_metal", "internal_raceway_radial_stylus")
    ruby = modeling._sphere(
        "SUM_V8_Inspection_RubyProbeTip",
        0.015,
        collection,
        location=(0.078, 0.0, 1.145),
        parent=probe,
        material=materials["safety_amber"],
        segments=32,
        rings=16,
        role="internal_raceway_probe_tip",
    )
    _tag(ruby, "safety_amber", "internal_raceway_probe_tip")
    probe_housing = modeling._box(
        "SUM_V8_Inspection_ProbeServoHousing",
        (0.28, 0.24, 0.22),
        collection,
        location=(0.0, 0.0, 2.15),
        parent=root,
        material=materials["screen_frame"],
        bevel=0.022,
        role="raceway_probe_servo_housing",
    )
    _tag(probe_housing, "dark_metal", "raceway_probe_servo_housing")
    laser_line = modeling._box(
        "SUM_V8_Inspection_LaserTrace",
        (0.075, 0.010, 0.008),
        collection,
        location=(0.038, -0.018, 1.145),
        parent=root,
        material=materials["indicator_green"],
        bevel=0.003,
        role="raceway_measurement_laser_trace",
    )
    _tag(laser_line, "luminaire", "raceway_measurement_laser_trace")
    encoder = modeling._cylinder_between(
        "SUM_V8_Inspection_MasterEncoder",
        (0.31, 0.0, 0.78),
        (0.31, 0.0, 0.94),
        0.065,
        collection,
        parent=root,
        material=materials["machined_steel"],
        segments=48,
        bevel=0.006,
        role="inspection_master_rotation_encoder",
    )
    _tag(encoder, "brushed_metal", "inspection_master_rotation_encoder")
    panel, display = _display_panel(
        "SUM_V8_Inspection_ExcelOpsHMI",
        (0.92, 0.20, 1.55),
        math.pi * 0.5,
        0.72,
        0.45,
        root,
        collection,
        materials,
        "excel_operations_inspection_evidence_display",
    )
    return {
        "root": root,
        "rotary_assets": rotary_assets,
        "probe": probe,
        "laser_line": laser_line,
        "panel": panel,
        "display": display,
    }


def _build_overhead_logistics(
    layout_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, bpy.types.Object]:
    root = modeling._empty(
        "SUM_ASSET_V8_OverheadLogistics",
        collection,
        parent=layout_root,
        display_size=0.20,
    )
    root["sum_asset_type"] = "overhead_linear_transfer_with_tooling_pallet"
    rail = modeling._box(
        "SUM_V8_Overhead_Monorail",
        (0.22, 23.0, 0.24),
        collection,
        location=(-2.70, 19.1, 3.48),
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.020,
        role="overhead_transfer_box_rail",
    )
    _tag(rail, "dark_metal", "overhead_transfer_box_rail")
    for index, y in enumerate((8.0, 13.5, 19.0, 24.5, 30.0), start=1):
        bracket = modeling._box(
            f"SUM_V8_Overhead_RoofBracket_{index:02d}",
            (0.72, 0.16, 0.16),
            collection,
            location=(-2.70, y, 3.62),
            parent=root,
            material=materials["machined_steel"],
            bevel=0.012,
            role="overhead_transfer_roof_bracket",
        )
        _tag(bracket, "brushed_metal", "overhead_transfer_roof_bracket")

    trolley = modeling._empty(
        "SUM_V8_Overhead_ServoTrolley",
        collection,
        location=(-2.70, 9.0, 3.30),
        parent=root,
        display_size=0.10,
    )
    trolley["sum_part_role"] = "overhead_servo_trolley"
    body = modeling._box(
        "SUM_V8_Overhead_TrolleyBody",
        (0.56, 0.64, 0.32),
        collection,
        parent=trolley,
        material=materials["fixture"],
        bevel=0.035,
        role="overhead_servo_trolley_body",
    )
    _tag(body, "powder_coat", "overhead_servo_trolley_body")
    mast = modeling._box(
        "SUM_V8_Overhead_TelescopicMast",
        (0.14, 0.14, 1.02),
        collection,
        location=(0.0, 0.0, -0.58),
        parent=trolley,
        material=materials["machined_steel"],
        bevel=0.012,
        role="overhead_gripper_telescopic_mast",
    )
    _tag(mast, "brushed_metal", "overhead_gripper_telescopic_mast")
    gripper = modeling._box(
        "SUM_V8_Overhead_ParallelGripper",
        (0.72, 0.30, 0.18),
        collection,
        location=(0.0, 0.0, -1.10),
        parent=trolley,
        material=materials["paint_graphite"],
        bevel=0.025,
        role="overhead_parallel_tooling_gripper",
    )
    _tag(gripper, "dark_metal", "overhead_parallel_tooling_gripper")
    for side in (-1.0, 1.0):
        jaw = modeling._box(
            f"SUM_V8_Overhead_GripperJaw_{'L' if side < 0 else 'R'}",
            (0.12, 0.30, 0.34),
            collection,
            location=(side * 0.28, 0.0, -1.27),
            parent=trolley,
            material=materials["machined_steel"],
            bevel=0.014,
            role="overhead_replaceable_gripper_jaw",
        )
        _tag(jaw, "brushed_metal", "overhead_replaceable_gripper_jaw")
    payload = modeling._box(
        "SUM_V8_Overhead_ToolingPallet",
        (0.58, 0.46, 0.20),
        collection,
        location=(0.0, 0.0, -1.49),
        parent=trolley,
        material=materials["safety_yellow"],
        bevel=0.025,
        role="overhead_change_tool_pallet",
    )
    _tag(payload, "safety_yellow", "overhead_change_tool_pallet")
    return {"root": root, "trolley": trolley, "payload": payload}


def _build_quality_transfer_gantry(
    layout_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, Any]:
    root = modeling._empty(
        "SUM_ASSET_V8_QualityTransferGantry",
        collection,
        parent=layout_root,
        display_size=0.20,
    )
    root["sum_asset_type"] = "xy_overhead_ring_transfer_gantry"
    for side in (-1.0, 1.0):
        rail = modeling._box(
            f"SUM_V8_QualityGantry_Runway_{'L' if side < 0 else 'R'}",
            (0.18, 11.0, 0.22),
            collection,
            location=(side * 3.0, 24.5, 3.48),
            parent=root,
            material=materials["paint_graphite"],
            bevel=0.018,
            role="quality_transfer_longitudinal_runway",
        )
        _tag(rail, "dark_metal", "quality_transfer_longitudinal_runway")

    bridge = modeling._empty(
        "SUM_V8_QualityGantry_MovingBridge",
        collection,
        location=(0.0, 20.0, 0.0),
        parent=root,
        display_size=0.10,
    )
    bridge["sum_part_role"] = "quality_transfer_moving_bridge"
    beam = modeling._box(
        "SUM_V8_QualityGantry_CrossBeam",
        (6.12, 0.20, 0.24),
        collection,
        location=(0.0, 0.0, 3.30),
        parent=bridge,
        material=materials["machined_steel"],
        bevel=0.020,
        role="quality_transfer_crossbeam",
    )
    _tag(beam, "brushed_metal", "quality_transfer_crossbeam")
    for side in (-1.0, 1.0):
        truck = modeling._box(
            f"SUM_V8_QualityGantry_EndTruck_{'L' if side < 0 else 'R'}",
            (0.46, 0.52, 0.32),
            collection,
            location=(side * 2.86, 0.0, 3.25),
            parent=bridge,
            material=materials["fixture"],
            bevel=0.030,
            role="quality_transfer_servo_end_truck",
        )
        _tag(truck, "powder_coat", "quality_transfer_servo_end_truck")

    trolley = modeling._empty(
        "SUM_V8_QualityGantry_XTrolley",
        collection,
        location=(1.20, 0.0, 0.0),
        parent=bridge,
        display_size=0.10,
    )
    trolley["sum_part_role"] = "quality_transfer_x_trolley"
    body = modeling._cylinder_between(
        "SUM_V8_QualityGantry_TrolleyBody",
        (0.0, 0.0, 3.07),
        (0.0, 0.0, 3.29),
        0.23,
        collection,
        parent=trolley,
        material=materials["paint_graphite"],
        segments=48,
        bevel=0.018,
        role="quality_transfer_trolley_body",
    )
    _tag(body, "powder_coat", "quality_transfer_trolley_body")
    mast = modeling._box(
        "SUM_V8_QualityGantry_TelescopicMast",
        (0.085, 0.085, 1.62),
        collection,
        location=(0.0, 0.0, 2.34),
        parent=trolley,
        material=materials["machined_steel"],
        bevel=0.012,
        role="quality_transfer_telescopic_mast",
    )
    _tag(mast, "brushed_metal", "quality_transfer_telescopic_mast")
    gripper = modeling._cylinder_between(
        "SUM_V8_QualityGantry_RingGripper",
        (0.0, 0.0, 1.44),
        (0.0, 0.0, 1.54),
        0.13,
        collection,
        parent=trolley,
        material=materials["paint_graphite"],
        segments=48,
        bevel=0.012,
        role="quality_transfer_internal_expanding_gripper_body",
    )
    _tag(gripper, "dark_metal", "quality_transfer_internal_expanding_gripper_body")
    collet_stem = modeling._cylinder_between(
        "SUM_V8_QualityGantry_ExpandingColletStem",
        (0.0, 0.0, 1.25),
        (0.0, 0.0, 1.48),
        0.038,
        collection,
        parent=trolley,
        material=materials["machined_steel"],
        segments=32,
        bevel=0.006,
        role="quality_transfer_expanding_collet_stem",
    )
    _tag(collet_stem, "brushed_metal", "quality_transfer_expanding_collet_stem")
    jaws: list[bpy.types.Object] = []
    for index in range(3):
        angle = math.tau * index / 3.0
        jaw = modeling._empty(
            f"SUM_V8_QualityGantry_GripperJawCarrier_{index + 1:02d}",
            collection,
            location=(math.cos(angle) * 0.035, math.sin(angle) * 0.035, 0.0),
            rotation=(0.0, 0.0, angle),
            parent=trolley,
            display_size=0.025,
        )
        jaw["sum_part_role"] = "quality_transfer_radial_jaw_carrier"
        jaw["grip_angle_rad"] = angle
        finger = modeling._box(
            f"SUM_V8_QualityGantry_ExpandingFinger_{index + 1:02d}",
            (0.060, 0.024, 0.080),
            collection,
            location=(0.0, 0.0, 1.25),
            parent=jaw,
            material=materials["machined_steel"],
            bevel=0.008,
            role="quality_transfer_internal_expanding_finger",
        )
        _tag(finger, "brushed_metal", "quality_transfer_internal_expanding_finger")
        pad = modeling._box(
            f"SUM_V8_QualityGantry_ExpandingPad_{index + 1:02d}",
            (0.018, 0.032, 0.060),
            collection,
            location=(0.038, 0.0, 1.25),
            parent=jaw,
            material=materials["rubber"],
            bevel=0.006,
            role="quality_transfer_nonmarking_bore_pad",
        )
        _tag(pad, "rubber", "quality_transfer_nonmarking_bore_pad")
        jaws.append(jaw)
    return {"root": root, "bridge": bridge, "trolley": trolley, "jaws": jaws}


def _build_final_door(
    layout_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, Any]:
    root = modeling._empty(
        "SUM_ASSET_V8_FinalDoor",
        collection,
        location=(0.0, 34.2, 0.0),
        parent=layout_root,
        display_size=0.20,
    )
    root["sum_asset_type"] = "interlocked_exit_door_to_dark_handoff"
    doors: list[bpy.types.Object] = []
    for side in (-1.0, 1.0):
        door = modeling._box(
            f"SUM_V8_FinalDoor_{'Left' if side < 0 else 'Right'}",
            (1.02, 0.14, 3.15),
            collection,
            location=(side * 0.52, 0.0, 1.575),
            parent=root,
            material=materials["paint_graphite"],
            bevel=0.025,
            role="final_interlocked_sliding_door_leaf",
        )
        _tag(door, "dark_metal", "final_interlocked_sliding_door_leaf")
        doors.append(door)
    header = modeling._box(
        "SUM_V8_FinalDoor_Header",
        (3.35, 0.28, 0.30),
        collection,
        location=(0.0, 0.0, 3.18),
        parent=root,
        material=materials["black_oxide"],
        bevel=0.020,
        role="final_door_drive_header",
    )
    _tag(header, "dark_metal", "final_door_drive_header")
    for side in (-1.0, 1.0):
        wall = modeling._box(
            f"SUM_V8_DarkVestibule_Wall_{'L' if side < 0 else 'R'}",
            (0.12, 4.0, 3.25),
            collection,
            location=(side * 1.65, 2.0, 1.625),
            parent=root,
            material=materials["black_oxide"],
            bevel=0.010,
            role="dark_handoff_vestibule_wall",
        )
        _tag(wall, "dark_metal", "dark_handoff_vestibule_wall")
    ceiling = modeling._box(
        "SUM_V8_DarkVestibule_Ceiling",
        (3.4, 4.0, 0.12),
        collection,
        location=(0.0, 2.0, 3.20),
        parent=root,
        material=materials["black_oxide"],
        bevel=0.010,
        role="dark_handoff_vestibule_ceiling",
    )
    _tag(ceiling, "dark_metal", "dark_handoff_vestibule_ceiling")
    return {"root": root, "doors": doors}


def augment_story_scene(assets: dict[str, Any]) -> dict[str, Any]:
    root_collection = assets.get("root_collection")
    layout_root = assets.get("layout_root")
    materials = assets.get("placeholder_materials")
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")
    if not isinstance(layout_root, bpy.types.Object):
        raise TypeError("assets must provide layout_root")
    if not isinstance(materials, dict):
        raise TypeError("assets must provide placeholder_materials")

    _hide_tree(assets.get("precision_bearing"))
    _hide_tree(assets.get("command_screen_bay"))
    _hide_tree(assets.get("grinding_workpiece"))
    robot_payload_reference = bpy.data.objects.get("SUM_KUKA_Gripper_HeldBearingRing_WIP")
    _hide_tree(robot_payload_reference)
    _hide_tree(bpy.data.objects.get("SUM_KUKA_Gripper_HeldBearingRing_RacewayWitness"))
    for station in assets.get("screen_stations", ()):
        _hide_tree(station)

    collection = _reset_collection(root_collection)
    hero_ring = _build_hero_ring(layout_root, collection, materials)
    scan = _build_scan_gate(layout_root, collection, materials)
    robot_hmi = _build_robot_hmi(layout_root, collection, materials)
    transfer = _build_transfer_line(layout_root, collection, materials)
    outfeed = _build_outfeed(layout_root, collection, materials)
    inspection = _build_inspection(layout_root, collection, materials)
    overhead = _build_overhead_logistics(layout_root, collection, materials)
    quality_gantry = _build_quality_transfer_gantry(layout_root, collection, materials)
    final_door = _build_final_door(layout_root, collection, materials)

    assets["hero_ring"] = hero_ring
    assets["ring_hero_01"] = hero_ring
    assets["hero_wet_film"] = bpy.data.objects.get("RING_HERO_01_RacewayWetFilm")
    assets["scan_gate"] = scan["root"]
    assets["scan_line"] = scan["scan_line"]
    assets["notice_display"] = scan["display"]
    assets["robot_takt_hmi"] = robot_hmi["display"]
    assets["robot_payload_reference"] = robot_payload_reference
    assets["transfer_station"] = transfer["root"]
    assets["transfer_carriage"] = transfer["carriage"]
    assets["machine_loader_slide"] = transfer["loader"]
    assets["outfeed_station"] = outfeed["root"]
    assets["outfeed_belts"] = outfeed["belts"]
    assets["outfeed_connector_belt"] = outfeed["connector_belt"]
    assets["outfeed_carrier"] = outfeed["carrier"]
    assets["inspection_station"] = inspection["root"]
    assets["inspection_rotary_assets"] = inspection["rotary_assets"]
    assets["inspection_probe"] = inspection["probe"]
    assets["inspection_laser_line"] = inspection["laser_line"]
    assets["inspection_display"] = inspection["display"]
    assets["overhead_logistics"] = overhead["root"]
    assets["overhead_trolley"] = overhead["trolley"]
    assets["quality_gantry"] = quality_gantry["root"]
    assets["quality_gantry_bridge"] = quality_gantry["bridge"]
    assets["quality_gantry_trolley"] = quality_gantry["trolley"]
    assets["quality_gantry_jaws"] = quality_gantry["jaws"]
    assets["final_story_door"] = final_door["root"]
    assets["final_story_door_leaves"] = final_door["doors"]
    assets["screen_displays"] = [scan["display"], robot_hmi["display"], inspection["display"]]
    assets["screens"] = assets["screen_displays"]
    assets.setdefault("anchors", {})["hero_ring"] = hero_ring
    assets["anchors"]["scan_release"] = scan["scanner"]
    assets["anchors"]["takt_hmi"] = robot_hmi["display"]
    assets["anchors"]["transfer"] = transfer["carriage"]
    assets["anchors"]["grinder_loader"] = transfer["loader"]
    assets["anchors"]["inspection"] = inspection["root"]
    assets["anchors"]["overhead_logistics"] = overhead["trolley"]
    assets["anchors"]["quality_transfer"] = quality_gantry["trolley"]
    assets["anchors"]["final_story_door"] = final_door["root"]
    assets.setdefault("collections", {})["v8_story"] = collection
    bpy.context.view_layer.update()
    return assets
