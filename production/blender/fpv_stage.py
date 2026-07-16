"""FPV evidence-stage augmentation for the V6 continuous industrial film.

The stage replaces the freestanding V5 evidence screens with machine-integrated
control bays while preserving the asset aliases consumed by texture, animation,
and cinematography passes. Geometry is authored in the modeling frame (X lateral,
+Y travel, +Z up) and inherits the existing layout transform.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Iterable

import bpy

import modeling


COLLECTION_NAME = "SUM_MODEL_FPV_EvidenceStage"
STAGE_OBJECT_NAME = "SUM_ASSET_FPV_EvidenceStage"

FILM_DURATION_SECONDS = 38.000
FILM_FPS = 24
FILM_FRAME_COUNT = 912
FILM_FOCUS_FRAMES = (91, 169, 301, 433, 553, 673, 793, 877)

DISPLAY_WIDTH_M = 2.40
DISPLAY_HEIGHT_M = 1.50
DISPLAY_CENTER_Z_M = 2.45
DISPLAY_ASPECT = "16:10"
APPROACH_TOE_IN_DEGREES = 8.0

PORTFOLIO_LAB_PROJECTS = (
    "operations-intelligence-platform",
    "factory-data-pocket-lab",
    "six-sigma-study-app",
    "hulunguard",
)


Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class EvidenceBaySpec:
    index: int
    display_x: float
    travel_y: float
    focus_frame: int
    content_id: str
    content_kind: str

    @property
    def side(self) -> int:
        return -1 if self.display_x < 0.0 else 1


BAY_SPECS = (
    EvidenceBaySpec(
        1,
        -2.65,
        52.0,
        433,
        "production-notice-workflow-standardization",
        "case_study",
    ),
    EvidenceBaySpec(
        2,
        2.65,
        75.0,
        553,
        "trial-production-takt-simulation-changeover-improvement",
        "case_study",
    ),
    EvidenceBaySpec(
        3,
        -2.65,
        99.0,
        673,
        "supply-production-delivery-operations-visibility",
        "case_study",
    ),
    EvidenceBaySpec(
        4,
        2.65,
        121.0,
        793,
        "portfolio-lab-four-project-matrix",
        "portfolio_lab_matrix",
    ),
)


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
    bevel: float = 0.012,
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


def _cylinder_between(
    name: str,
    start: Vec3,
    end: Vec3,
    radius: float,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    role: str,
    detail: str,
    segments: int = 24,
) -> bpy.types.Object:
    return _tag(
        modeling._cylinder_between(
            name,
            start,
            end,
            radius,
            collection,
            parent=parent,
            material=material,
            segments=segments,
            bevel=0.004,
            role=detail,
        ),
        role,
        detail,
    )


def _iter_object_tree(root: bpy.types.Object) -> Iterable[bpy.types.Object]:
    stack = [root]
    while stack:
        obj = stack.pop()
        yield obj
        stack.extend(obj.children)


def _exclude_object(obj: object, replacement: str) -> None:
    if not isinstance(obj, bpy.types.Object):
        return
    obj.hide_render = True
    obj.hide_viewport = True
    try:
        obj.hide_set(True)
    except RuntimeError:
        pass
    if hasattr(obj, "visible_camera"):
        obj.visible_camera = False
    obj["sum_export_exclude"] = True
    obj["sum_replaced_by"] = replacement


def _exclude_object_tree(root: object, replacement: str) -> None:
    if not isinstance(root, bpy.types.Object):
        return
    for obj in _iter_object_tree(root):
        _exclude_object(obj, replacement)


def _exclude_legacy_displays(assets: dict[str, Any]) -> None:
    legacy_roots: dict[str, bpy.types.Object] = {}
    stations = assets.get("screen_stations")
    if isinstance(stations, (list, tuple)):
        for station in stations:
            if isinstance(station, bpy.types.Object) and station.name.startswith(
                "SUM_ASSET_ScreenStation_"
            ):
                legacy_roots[station.name] = station

    for index in range(1, 5):
        name = f"SUM_ASSET_ScreenStation_{index:02d}"
        station = bpy.data.objects.get(name)
        if isinstance(station, bpy.types.Object):
            legacy_roots[name] = station

    for station in legacy_roots.values():
        _exclude_object_tree(station, STAGE_OBJECT_NAME)

    legacy_collection = bpy.data.collections.get("SUM_MODEL_ScreenStations")
    if isinstance(legacy_collection, bpy.types.Collection):
        legacy_collection.hide_render = True
        legacy_collection.hide_viewport = True
        legacy_collection["sum_export_exclude"] = True
        legacy_collection["sum_replaced_by"] = COLLECTION_NAME

    hero_screen = assets.get("hero_screen")
    if not isinstance(hero_screen, bpy.types.Object):
        hero_screen = bpy.data.objects.get("SUM_CommandBay_ProjectDisplay")
    _exclude_object(hero_screen, "FPV evidence bays; command-bay shell retained")
    if isinstance(hero_screen, bpy.types.Object):
        assets["legacy_hero_screen"] = hero_screen
        assets["hero_screen_excluded"] = True


def _reset_stage_collection(
    root_collection: bpy.types.Collection,
) -> bpy.types.Collection:
    existing = bpy.data.collections.get(COLLECTION_NAME)
    if isinstance(existing, bpy.types.Collection):
        modeling._remove_collection_tree(existing)
    collection = modeling._child_collection(root_collection, COLLECTION_NAME)
    collection["sum_managed_collection"] = True
    collection["build_interface"] = (
        "production.blender.fpv_stage.augment_fpv_stage"
    )
    return collection


def _validate_inputs(
    assets: dict[str, Any],
) -> tuple[bpy.types.Collection, bpy.types.Object, dict[str, bpy.types.Material]]:
    root_collection = assets.get("root_collection")
    layout_root = assets.get("layout_root")
    materials = assets.get("placeholder_materials") or assets.get("materials")
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")
    if not isinstance(layout_root, bpy.types.Object):
        raise TypeError("assets must provide layout_root")
    if not isinstance(materials, dict):
        raise TypeError("assets must provide placeholder_materials")

    required_materials = (
        "brushed_steel",
        "enclosure_paint",
        "factory_structure",
        "indicator_green",
        "indicator_red",
        "luminaire_diffuser",
        "machined_steel",
        "paint_graphite",
        "safety_amber",
        "safety_yellow",
        "screen_content",
        "screen_frame",
    )
    missing = [name for name in required_materials if name not in materials]
    if missing:
        raise KeyError(f"assets materials missing: {', '.join(missing)}")
    return root_collection, layout_root, materials


def _set_display_metadata(
    display: bpy.types.Object,
    bay: bpy.types.Object,
    spec: EvidenceBaySpec,
) -> None:
    display["project_image_slot"] = (
        "PORTFOLIO_LAB_MATRIX" if spec.index == 4 else f"PROJECT_IMAGE_{spec.index:02d}"
    )
    display["station_index"] = spec.index
    display["screen_index"] = spec.index
    display["content_id"] = spec.content_id
    display["content_kind"] = spec.content_kind
    display["portfolio_section"] = (
        "portfolio_lab" if spec.index == 4 else "featured_case_studies"
    )
    display["is_case_study"] = spec.index < 4
    display["focus_frame"] = spec.focus_frame
    display["active_aspect_ratio"] = DISPLAY_ASPECT
    display["active_width_m"] = DISPLAY_WIDTH_M
    display["active_height_m"] = DISPLAY_HEIGHT_M
    display["display_center_x_m"] = spec.display_x
    display["display_center_z_m"] = DISPLAY_CENTER_Z_M
    display["travel_y_m"] = spec.travel_y
    display["recommended_image_color_space"] = "sRGB"
    display["recommended_image_fit"] = "contain or center-crop to 16:10"

    bay["content_id"] = spec.content_id
    bay["content_kind"] = spec.content_kind
    bay["focus_frame"] = spec.focus_frame
    bay["display_surface_object"] = display.name

    if spec.index < 4:
        display["case_study_index"] = spec.index
        display["case_study_count"] = 3
        bay["case_study_index"] = spec.index
    else:
        project_ids = json.dumps(PORTFOLIO_LAB_PROJECTS, separators=(",", ":"))
        display["portfolio_lab_role"] = "four_project_matrix"
        display["portfolio_lab_project_count"] = 4
        display["portfolio_lab_project_ids"] = project_ids
        display["recommended_image_fit"] = "four-cell 2x2 matrix within 16:10"
        bay["portfolio_lab_role"] = "four_project_matrix"
        bay["portfolio_lab_project_count"] = 4
        bay["portfolio_lab_project_ids"] = project_ids


def _build_portfolio_lab_dividers(
    bay: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    dividers = _boxes(
        "SUM_FPV_EvidenceBay_04_PortfolioLabMatrixDividers",
        (
            ((0.035, 0.0, DISPLAY_CENTER_Z_M), (0.028, 0.022, 1.44)),
            ((0.035, 0.0, DISPLAY_CENTER_Z_M), (0.028, 2.34, 0.022)),
        ),
        collection,
        parent=bay,
        material=materials["screen_frame"],
        role="dark_metal",
        detail="four_project_portfolio_lab_matrix_dividers",
        bevel=0.002,
    )
    dividers["portfolio_lab_project_count"] = 4
    dividers["is_case_study"] = False


def _build_control_bay(
    spec: EvidenceBaySpec,
    stage_root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    base_yaw = math.pi if spec.side > 0 else 0.0
    toe_in = math.radians(APPROACH_TOE_IN_DEGREES) * spec.side
    bay = modeling._empty(
        f"SUM_ASSET_FPV_EvidenceBay_{spec.index:02d}",
        collection,
        location=(spec.display_x, spec.travel_y, 0.0),
        rotation=(0.0, 0.0, base_yaw + toe_in),
        parent=stage_root,
        display_size=0.24,
    )
    bay["sum_asset_type"] = "aisle_integrated_machine_control_evidence_bay"
    bay["station_index"] = spec.index
    bay["travel_y_m"] = spec.travel_y
    bay["display_center_x_m"] = spec.display_x
    bay["display_center_z_m"] = DISPLAY_CENTER_Z_M
    bay["faces_approaching_centerline"] = True
    bay["approach_toe_in_degrees"] = APPROACH_TOE_IN_DEGREES
    bay["aisle_clearance_half_width_m"] = 2.30
    bay["mounting_logic"] = (
        "machine plinth -> enclosed control spine -> recessed steel display frame"
    )

    prefix = f"SUM_FPV_EvidenceBay_{spec.index:02d}"
    _box(
        f"{prefix}_MachinePlinth",
        (1.86, 3.28, 0.18),
        collection,
        location=(-0.93, 0.0, 0.09),
        parent=bay,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="integrated_control_bay_vibration_plinth",
        bevel=0.022,
    )
    _box(
        f"{prefix}_MainEnclosure",
        (1.55, 3.05, 3.64),
        collection,
        location=(-0.86, 0.0, 1.91),
        parent=bay,
        material=materials["enclosure_paint"],
        role="powder_coat",
        detail="machine_integrated_control_enclosure",
        bevel=0.045,
    )
    _box(
        f"{prefix}_RearStructuralSpine",
        (0.22, 3.12, 3.78),
        collection,
        location=(-1.70, 0.0, 1.89),
        parent=bay,
        material=materials["factory_structure"],
        role="steel_blue",
        detail="control_bay_structural_machine_spine",
        bevel=0.018,
    )
    _box(
        f"{prefix}_ServiceCrown",
        (1.72, 3.16, 0.22),
        collection,
        location=(-0.88, 0.0, 3.80),
        parent=bay,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="restrained_graphite_service_crown",
        bevel=0.020,
    )

    _box(
        f"{prefix}_DisplayRearShell",
        (0.16, 2.72, 1.82),
        collection,
        location=(-0.12, 0.0, DISPLAY_CENTER_Z_M),
        parent=bay,
        material=materials["screen_frame"],
        role="dark_metal",
        detail="recessed_industrial_display_rear_shell",
        bevel=0.030,
    )
    _box(
        f"{prefix}_DisplayReveal",
        (0.055, 2.56, 1.66),
        collection,
        location=(-0.025, 0.0, DISPLAY_CENTER_Z_M),
        parent=bay,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="graphite_display_recess_reveal",
        bevel=0.012,
    )
    _boxes(
        f"{prefix}_DisplayFrame",
        (
            ((0.025, -1.265, DISPLAY_CENTER_Z_M), (0.085, 0.13, 1.76)),
            ((0.025, 1.265, DISPLAY_CENTER_Z_M), (0.085, 0.13, 1.76)),
            ((0.025, 0.0, 1.655), (0.085, 2.66, 0.13)),
            ((0.025, 0.0, 3.245), (0.085, 2.66, 0.13)),
        ),
        collection,
        parent=bay,
        material=materials["brushed_steel"],
        role="brushed_metal",
        detail="serviceable_steel_display_frame",
        bevel=0.007,
    )

    display = modeling._display_surface(
        f"{prefix}_DisplaySurface",
        DISPLAY_WIDTH_M,
        DISPLAY_HEIGHT_M,
        collection,
        # The active glass sits just proud of the reveal and flush with the
        # serviceable bezel. Keeping it at x=0 left the solid reveal plate in
        # front of the image surface, which correctly rendered as a blank bay.
        location=(0.070, 0.0, DISPLAY_CENTER_Z_M),
        parent=bay,
        material=materials["screen_content"],
    )
    _tag(display, "screen_glass", "active_16_10_evidence_display")
    _set_display_metadata(display, bay, spec)

    service_light = _box(
        f"{prefix}_ServiceLight",
        (0.075, 2.18, 0.075),
        collection,
        location=(0.075, 0.0, 3.43),
        parent=bay,
        material=materials["luminaire_diffuser"],
        role="luminaire",
        detail="recessed_neutral_service_light",
        bevel=0.006,
    )
    service_light["light_treatment"] = "restrained inspection wash"

    control_y = -1.45
    _box(
        f"{prefix}_ServiceControlPod",
        (0.25, 0.36, 0.72),
        collection,
        location=(-0.02, control_y, 1.15),
        parent=bay,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="flush_machine_service_control_pod",
        bevel=0.018,
    )
    _cylinder_between(
        f"{prefix}_EmergencyStopBackplate",
        (0.10, control_y, 1.30),
        (0.16, control_y, 1.30),
        0.050,
        collection,
        parent=bay,
        material=materials["safety_yellow"],
        role="safety_yellow",
        detail="emergency_stop_safety_backplate",
        segments=32,
    )
    _cylinder_between(
        f"{prefix}_EmergencyStopButton",
        (0.16, control_y, 1.30),
        (0.21, control_y, 1.30),
        0.035,
        collection,
        parent=bay,
        material=materials["indicator_red"],
        role="safety_red",
        detail="machine_control_emergency_stop",
        segments=32,
    )
    status = _cylinder_between(
        f"{prefix}_ServiceStatusIndicator",
        (0.10, control_y, 1.58),
        (0.17, control_y, 1.58),
        0.026,
        collection,
        parent=bay,
        material=materials["indicator_green"],
        role="luminaire",
        detail="screen_station_live_status_indicator",
        segments=24,
    )
    status["sum_part_role"] = "screen_station_live_status_indicator"

    _boxes(
        f"{prefix}_SafetyFloorDetails",
        (
            ((0.015, 0.0, 0.038), (0.065, 3.02, 0.065)),
            ((-0.82, -1.59, 0.032), (1.70, 0.055, 0.012)),
            ((-0.82, 1.59, 0.032), (1.70, 0.055, 0.012)),
        ),
        collection,
        parent=bay,
        material=materials["safety_yellow"],
        role="safety_yellow",
        detail="control_bay_floor_clearance_marking",
        bevel=0.002,
    )
    _boxes(
        f"{prefix}_ServiceAccessDetails",
        (
            ((-0.035, 0.35, 0.78), (0.055, 1.15, 0.62)),
            ((0.005, 0.83, 0.78), (0.025, 0.035, 0.34)),
        ),
        collection,
        parent=bay,
        material=materials["paint_graphite"],
        role="dark_metal",
        detail="flush_lower_service_access_panel",
        bevel=0.008,
    )

    wipe_local_y = -spec.side * 1.50
    wipe = _box(
        f"{prefix}_TrailingWipeEdge",
        (0.18, 0.14, 4.12),
        collection,
        location=(0.045, wipe_local_y, 2.06),
        parent=bay,
        material=materials["machined_steel"],
        role="brushed_metal",
        detail="fpv_foreground_trailing_edge_wipe_geometry",
        bevel=0.012,
    )
    wipe["fpv_wipe_role"] = "controlled_trailing_edge_occluder"
    wipe["fpv_wipe_order"] = spec.index
    wipe["focus_frame"] = spec.focus_frame

    if spec.index == 4:
        _build_portfolio_lab_dividers(bay, collection, materials)
    return bay, display, wipe


def _reassign_asset_contract(
    assets: dict[str, Any],
    stage_root: bpy.types.Object,
    collection: bpy.types.Collection,
    bays: list[bpy.types.Object],
    displays: list[bpy.types.Object],
    wipe_edges: list[bpy.types.Object],
) -> None:
    assets["fpv_stage"] = stage_root
    assets["fpv_evidence_stage"] = stage_root
    assets["fpv_evidence_bays"] = bays
    assets["fpv_wipe_edges"] = wipe_edges
    assets["screen_stations"] = bays
    assets["screen_displays"] = displays
    assets["screens"] = displays
    assets["case_study_displays"] = displays[:3]
    assets["portfolio_lab_displays"] = [displays[3]]

    for index, (bay, display) in enumerate(zip(bays, displays), start=1):
        assets[f"screen_station_{index:02d}"] = bay
        assets[f"screen_display_{index:02d}"] = display
        assets[f"screen_{index:02d}"] = display

    aliases = {
        "notice_screen": displays[0],
        "screen_notice": displays[0],
        "notice_card": displays[0],
        "case_study_01_screen": displays[0],
        "screen_takt": displays[1],
        "takt_screen": displays[1],
        "case_study_02_screen": displays[1],
        "screen_visibility": displays[2],
        "visibility_screen": displays[2],
        "case_study_03_screen": displays[2],
        "portfolio_lab": displays[3],
        "portfolio_lab_screen": displays[3],
        "screen_portfolio_lab": displays[3],
        "portfolio_lab_matrix": displays[3],
        "portfolio_lab_matrix_screen": displays[3],
        "screen_systems": displays[3],
    }
    assets.update(aliases)
    assets["portfolio_lab_bay"] = bays[3]

    anchors = assets.get("anchors")
    if isinstance(anchors, dict):
        anchors.update(
            {
                "screen_01": displays[0],
                "screen_02": displays[1],
                "screen_03": displays[2],
                "screen_04": displays[3],
                "notice_card": displays[0],
                "visibility_card": displays[2],
                "systems_card": displays[3],
                "portfolio_lab": displays[3],
                "portfolio_lab_matrix": displays[3],
            }
        )

    travel_anchors = assets.get("travel_anchors")
    if isinstance(travel_anchors, dict):
        for index, display in enumerate(displays, start=1):
            travel_anchors[f"screen_{index:02d}"] = display
        travel_anchors["portfolio_lab"] = displays[3]

    collections = assets.setdefault("collections", {})
    if not isinstance(collections, dict):
        raise TypeError("assets collections must be a dictionary")
    collections["fpv_evidence_stage"] = collection

    portfolio_lab_metadata = {
        "representation": "four_project_lab_matrix",
        "screen_index": 4,
        "is_case_study": False,
        "project_count": 4,
        "project_ids": PORTFOLIO_LAB_PROJECTS,
        "focus_frame": BAY_SPECS[3].focus_frame,
    }
    assets["portfolio_lab_metadata"] = portfolio_lab_metadata
    assets["fpv_stage_metadata"] = {
        "duration_seconds": FILM_DURATION_SECONDS,
        "fps": FILM_FPS,
        "frame_count": FILM_FRAME_COUNT,
        "frame_start": 1,
        "frame_end": FILM_FRAME_COUNT,
        "continuous_take": True,
        "camera_language": "continuous_fpv",
        "focus_frames": FILM_FOCUS_FRAMES,
        "display_travel_y": tuple(spec.travel_y for spec in BAY_SPECS),
        "portfolio_lab": portfolio_lab_metadata,
    }


def augment_fpv_stage(assets: dict[str, Any]) -> dict[str, Any]:
    """Build the managed V6 FPV evidence stage and update the asset contract."""

    if not isinstance(assets, dict):
        raise TypeError("assets must be a dictionary")
    root_collection, layout_root, materials = _validate_inputs(assets)

    _exclude_legacy_displays(assets)
    collection = _reset_stage_collection(root_collection)
    stage_root = modeling._empty(
        STAGE_OBJECT_NAME,
        collection,
        parent=layout_root,
        display_size=0.52,
    )
    stage_root["sum_asset_type"] = "continuous_fpv_industrial_evidence_stage"
    stage_root["film_duration_seconds"] = FILM_DURATION_SECONDS
    stage_root["film_fps"] = FILM_FPS
    stage_root["film_frame_count"] = FILM_FRAME_COUNT
    stage_root["film_focus_frames"] = json.dumps(
        FILM_FOCUS_FRAMES, separators=(",", ":")
    )
    stage_root["continuous_take"] = True
    stage_root["display_aspect_ratio"] = DISPLAY_ASPECT
    stage_root["case_study_display_count"] = 3
    stage_root["portfolio_lab_display_count"] = 1
    stage_root["portfolio_lab_representation"] = "four_project_matrix"

    bays: list[bpy.types.Object] = []
    displays: list[bpy.types.Object] = []
    wipe_edges: list[bpy.types.Object] = []
    for spec in BAY_SPECS:
        bay, display, wipe = _build_control_bay(
            spec, stage_root, collection, materials
        )
        bays.append(bay)
        displays.append(display)
        wipe_edges.append(wipe)

    _reassign_asset_contract(
        assets, stage_root, collection, bays, displays, wipe_edges
    )

    scene = bpy.context.scene
    scene["fpv_stage_build_interface"] = (
        "production.blender.fpv_stage.augment_fpv_stage"
    )
    scene["fpv_film_duration_seconds"] = FILM_DURATION_SECONDS
    scene["fpv_film_fps"] = FILM_FPS
    scene["fpv_film_frame_count"] = FILM_FRAME_COUNT
    scene["fpv_film_focus_frames"] = json.dumps(
        FILM_FOCUS_FRAMES, separators=(",", ":")
    )
    bpy.context.view_layer.update()
    return assets


__all__ = ["augment_fpv_stage"]
