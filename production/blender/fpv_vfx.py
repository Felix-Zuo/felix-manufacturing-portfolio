"""Restrained physical VFX for the 38-second FPV director's cut.

The augmentation owns one managed collection and can be called repeatedly. It
adds only rail-bound data packets, one local grinding droplet layer, physical
screen interaction cues, and a split-gate black-field endpoint transition.
Animated values follow ``CIN_TimeControl`` when its visual clock is available,
with scene-frame drivers as a safe fallback.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import bpy

import modeling


COLLECTION_NAME = "SUM_FPV_VFX"
ROOT_OBJECT_NAME = "SUM_ASSET_FPV_VFX"
OWNER_KEY = "fpv_vfx_generated"

FILM_DURATION_SECONDS = 38.000
FILM_FPS = 24
FILM_FRAME_COUNT = 912
FILM_FOCUS_FRAMES = (1, 84, 132, 188, 228, 342, 420, 474, 588, 660, 798, 882)
PROJECT_FOCUS_FRAMES = (132, 228, 660, 798)

PASS_INDEX_DATA_PACKETS = 61
PASS_INDEX_GRINDING_MIST = 62
PASS_INDEX_SCREEN_PRACTICALS = 63
PASS_INDEX_ENDPOINT_GATE = 64
PASS_INDEX_OVERHEAD_REVEAL = 65

ENDPOINT_DIM_START_FRAME = 841
ENDPOINT_DIM_END_FRAME = 857
ENDPOINT_DOOR_OPEN_START_FRAME = 853
ENDPOINT_DOOR_OPEN_END_FRAME = 895
ENDPOINT_FOCUS_FRAME = 877
ENDPOINT_BREATH_PEAK_FRAME = 853
ENDPOINT_BLACKOUT_START_FRAME = 865
ENDPOINT_BLACKOUT_END_FRAME = 901
ENDPOINT_SETTLE_FRAME = 901
ENDPOINT_FINAL_FRAME = 912
ENDPOINT_LOCAL_DIM_STOPS = 2.25
ENDPOINT_MAX_EMISSION_STRENGTH = 1.60
ENDPOINT_BLACK_FIELD_EMISSION_STRENGTH = 0.0
ENDPOINT_MAX_LIGHT_ENERGY_W = 0.0
ENDPOINT_DOOR_LEAF_TRAVEL_M = 2.62

_ENDPOINT_DIM_OWNER_KEY = "fpv_vfx_endpoint_dim_driver"
_ENDPOINT_DIM_BASELINE_KEY = "fpv_vfx_endpoint_dim_baseline_w"
_ENDPOINT_STATIC_HIDE_OWNER_KEY = "fpv_vfx_endpoint_static_hide"
_ENDPOINT_STATIC_HIDE_RENDER_KEY = "fpv_vfx_endpoint_static_hide_render_baseline"
_ENDPOINT_STATIC_HIDE_VIEWPORT_KEY = "fpv_vfx_endpoint_static_hide_viewport_baseline"


@dataclass(frozen=True)
class _PacketWindow:
    slug: str
    frame_start: int
    frame_end: int
    travel_start_m: float
    travel_end_m: float


# Each interval starts after the approved project hold and ends with its beat.
# Boundaries are inclusive presentation frames in the locked 24 fps timeline.
POST_PROJECT_WINDOWS = (
    _PacketWindow("notice_to_takt", 150, 228, 18.0, 31.0),
    _PacketWindow("takt_to_grind", 252, 342, 34.0, 49.0),
    _PacketWindow("grind_to_inspection", 498, 660, 53.0, 82.0),
    _PacketWindow("inspection_to_close", 702, 840, 86.0, 112.0),
)

GRINDING_MIST_WINDOW = (386, 498)
OVERHEAD_REVEAL_WINDOW = (205, 330)
_SCREEN_PRACTICAL_HALF_WINDOW_FRAMES = 24
_PACKET_HEIGHT_M = 0.119


@dataclass(frozen=True)
class _ClockBinding:
    control: Any | None
    frame_values: Mapping[int, float]
    mode: str

    @property
    def token(self) -> str:
        return "t" if self.control is not None else "frame"

    def value(self, frame: int) -> float:
        return float(self.frame_values.get(int(frame), frame))


def _asset_value(assets: Mapping[str, Any], key: str) -> Any | None:
    return assets.get(key)


def _owned_collection_name() -> str:
    existing = bpy.data.collections.get(COLLECTION_NAME)
    if existing is None or bool(existing.get(OWNER_KEY)):
        return COLLECTION_NAME

    alternate = f"{COLLECTION_NAME}_Augmentation"
    candidate = bpy.data.collections.get(alternate)
    if candidate is None or bool(candidate.get(OWNER_KEY)):
        return alternate
    raise RuntimeError("No unclaimed collection name is available for FPV VFX")


def _purge_owned_orphans() -> None:
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.lights,
        bpy.data.materials,
    ):
        for datablock in list(datablocks):
            try:
                owned = bool(datablock.get(OWNER_KEY))
            except (AttributeError, TypeError):
                owned = False
            if owned and datablock.users == 0:
                datablocks.remove(datablock)


def _reset_collection(
    root_collection: bpy.types.Collection | None,
) -> bpy.types.Collection:
    name = _owned_collection_name()
    existing = bpy.data.collections.get(name)
    if isinstance(existing, bpy.types.Collection) and bool(existing.get(OWNER_KEY)):
        modeling._remove_collection_tree(existing)
    _purge_owned_orphans()

    if isinstance(root_collection, bpy.types.Collection):
        collection = modeling._child_collection(root_collection, name)
    else:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    collection[OWNER_KEY] = True
    collection["sum_managed_collection"] = True
    collection["build_interface"] = "production.blender.fpv_vfx.augment_fpv_vfx"
    return collection


def _owned_material_name(base_name: str) -> str:
    for candidate_name in (
        base_name,
        f"{base_name}_Augmentation",
        f"{base_name}_Owned",
    ):
        existing = bpy.data.materials.get(candidate_name)
        if existing is None or bool(existing.get(OWNER_KEY)):
            return candidate_name
    raise RuntimeError(f"No unclaimed material name is available for {base_name}")


def _vfx_material(
    name: str,
    base_color: tuple[float, float, float, float],
    *,
    metallic: float,
    roughness: float,
    alpha: float = 1.0,
    transmission: float = 0.0,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    material = modeling._placeholder_material(
        _owned_material_name(name),
        base_color,
        metallic=metallic,
        roughness=roughness,
        alpha=alpha,
        transmission=transmission,
        emission_color=emission_color,
        emission_strength=emission_strength,
    )
    material[OWNER_KEY] = True
    material["fpv_vfx_material"] = True
    for property_name in ("sum_placeholder_material", "intended_workflow"):
        if property_name in material:
            del material[property_name]
    if alpha < 1.0:
        try:
            material.surface_render_method = "DITHERED"
        except (AttributeError, TypeError, ValueError):
            pass
        try:
            material.blend_method = "BLEND"
        except (AttributeError, TypeError, ValueError):
            pass
    return material


def _tag_object(
    obj: bpy.types.Object,
    *,
    family: str,
    pass_index: int,
    role: str,
    lookdev_role: str,
    clean_plate: bool,
) -> bpy.types.Object:
    obj[OWNER_KEY] = True
    obj["fpv_vfx_family"] = family
    obj["fpv_vfx_compositor_group"] = family
    obj["fpv_vfx_pass_index"] = pass_index
    obj["fpv_vfx_clean_plate_visible"] = clean_plate
    obj["fpv_vfx_screen_matte_visible"] = False
    obj["sum_part_role"] = role
    obj["lookdev_role"] = lookdev_role
    if hasattr(obj, "pass_index"):
        obj.pass_index = pass_index

    data = getattr(obj, "data", None)
    if data is not None:
        try:
            data[OWNER_KEY] = True
            data["fpv_vfx_compositor_group"] = family
        except (AttributeError, TypeError):
            pass
    return obj


def _resolve_time_control(scene: bpy.types.Scene) -> bpy.types.Object | None:
    configured_name = scene.get("cin_visual_time_object")
    names = [configured_name, "CIN_TimeControl"]
    for name in names:
        if not isinstance(name, str):
            continue
        candidate = bpy.data.objects.get(name)
        if isinstance(candidate, bpy.types.Object) and "visual_time_seconds" in candidate:
            return candidate
    return None


def _clock_binding(
    scene: bpy.types.Scene,
    frames: Sequence[int],
) -> _ClockBinding:
    unique_frames = tuple(sorted({int(frame) for frame in frames}))
    fallback = {frame: float(frame) for frame in unique_frames}
    control = _resolve_time_control(scene)
    if control is None or len(unique_frames) < 2:
        return _ClockBinding(None, fallback, "scene_frame")

    original_frame = int(scene.frame_current)
    sampled: dict[int, float] = {}
    try:
        for frame in unique_frames:
            scene.frame_set(frame)
            value = float(control.get("visual_time_seconds", float("nan")))
            if not math.isfinite(value):
                raise ValueError("visual clock produced a non-finite value")
            sampled[frame] = value
    except (RuntimeError, TypeError, ValueError):
        sampled.clear()
    finally:
        try:
            scene.frame_set(original_frame)
        except RuntimeError:
            pass

    ordered_values = [sampled.get(frame) for frame in unique_frames]
    monotone = bool(ordered_values) and all(
        current is not None
        and following is not None
        and following > current
        for current, following in zip(ordered_values, ordered_values[1:])
    )
    if not monotone:
        return _ClockBinding(None, fallback, "scene_frame")
    return _ClockBinding(
        control,
        sampled,
        "CIN_TimeControl.visual_time_seconds",
    )


def _add_driver(
    owner: Any,
    data_path: str,
    expression: str,
    clock: _ClockBinding,
    *,
    index: int | None = None,
) -> bool:
    try:
        fcurve = (
            owner.driver_add(data_path)
            if index is None
            else owner.driver_add(data_path, index)
        )
        driver = fcurve.driver
        driver.type = "SCRIPTED"
        driver.expression = expression
        if clock.control is not None:
            variable = driver.variables.new()
            variable.name = "t"
            variable.type = "SINGLE_PROP"
            target = variable.targets[0]
            if hasattr(target, "id_type"):
                try:
                    target.id_type = "OBJECT"
                except (AttributeError, TypeError, ValueError):
                    pass
            target.id = clock.control
            target.data_path = '["visual_time_seconds"]'
        return True
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return False


def _window_expression(
    clock: _ClockBinding,
    frame_start: int,
    frame_end: int,
    *,
    ramp_fraction: float = 0.22,
) -> str:
    start = clock.value(frame_start)
    end = clock.value(frame_end)
    ramp = max((end - start) * ramp_fraction, 1.0e-5)
    token = clock.token
    return (
        "max(0.0,min(1.0,min("
        f"({token}-{start:.8f})/{ramp:.8f},"
        f"({end:.8f}-{token})/{ramp:.8f})))"
    )


def _progress_expression(
    clock: _ClockBinding,
    frame_start: int,
    frame_end: int,
) -> str:
    start = clock.value(frame_start)
    end = clock.value(frame_end)
    span = max(end - start, 1.0e-5)
    return (
        f"min(1.0,max(0.0,({clock.token}-{start:.8f})/{span:.8f}))"
    )


def _ease_progress_expression(
    clock: _ClockBinding,
    frame_start: int,
    frame_end: int,
) -> str:
    progress = _progress_expression(clock, frame_start, frame_end)
    return f"(0.5-0.5*cos(3.14159265*({progress})))"


def _endpoint_cue_expression(clock: _ClockBinding) -> str:
    activation = _ease_progress_expression(
        clock,
        ENDPOINT_DIM_START_FRAME,
        ENDPOINT_DOOR_OPEN_START_FRAME,
    )
    opening = _ease_progress_expression(
        clock,
        ENDPOINT_DOOR_OPEN_START_FRAME,
        ENDPOINT_FOCUS_FRAME,
    )
    return f"(({activation})*(1.0-({opening})))"


def _endpoint_open_expression(clock: _ClockBinding) -> str:
    return _ease_progress_expression(
        clock,
        ENDPOINT_DOOR_OPEN_START_FRAME,
        ENDPOINT_DOOR_OPEN_END_FRAME,
    )


def _endpoint_blackout_expression(clock: _ClockBinding) -> str:
    return _ease_progress_expression(
        clock,
        ENDPOINT_BLACKOUT_START_FRAME,
        ENDPOINT_BLACKOUT_END_FRAME,
    )


def _drive_windowed_scale(
    obj: bpy.types.Object,
    clock: _ClockBinding,
    frame_start: int,
    frame_end: int,
    *,
    ramp_fraction: float = 0.22,
) -> None:
    expression = _window_expression(
        clock,
        frame_start,
        frame_end,
        ramp_fraction=ramp_fraction,
    )
    obj.scale = (0.0, 0.0, 0.0)
    for axis in range(3):
        _add_driver(obj, "scale", expression, clock, index=axis)


def _resolve_guide(assets: Mapping[str, Any]) -> bpy.types.Object | None:
    candidate = _asset_value(assets, "dual_rail_guide")
    if not isinstance(candidate, bpy.types.Object):
        candidate = bpy.data.objects.get("SUM_ASSET_DualRail_GuideSystem")
    return candidate if isinstance(candidate, bpy.types.Object) else None


def _rail_gauge(assets: Mapping[str, Any], guide: bpy.types.Object) -> float:
    try:
        gauge = float(guide.get("rail_gauge_m", 0.0))
    except (TypeError, ValueError):
        gauge = 0.0
    parameters = _asset_value(assets, "parameters")
    if gauge <= 0.0 and parameters is not None:
        try:
            gauge = float(parameters.rail_gauge)
        except (AttributeError, TypeError, ValueError):
            gauge = 0.0
    return gauge if gauge > 0.0 else 2.40


def _resolve_screens(assets: Mapping[str, Any]) -> list[bpy.types.Object]:
    screens: list[bpy.types.Object] = []
    value = _asset_value(assets, "screen_displays")
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        screens.extend(item for item in value if isinstance(item, bpy.types.Object))

    for index in range(1, 5):
        candidate = _asset_value(assets, f"screen_display_{index:02d}")
        if not isinstance(candidate, bpy.types.Object):
            candidate = bpy.data.objects.get(
                f"SUM_FPV_EvidenceBay_{index:02d}_DisplaySurface"
            )
        if isinstance(candidate, bpy.types.Object):
            screens.append(candidate)

    unique: list[bpy.types.Object] = []
    pointers: set[int] = set()
    for screen in screens:
        pointer = int(screen.as_pointer())
        if pointer not in pointers:
            pointers.add(pointer)
            unique.append(screen)
    return unique[:4]


def _resolve_overhead_gripper(assets: Mapping[str, Any]) -> bpy.types.Object | None:
    for key in (
        "overhead_gantry_gripper",
        "overhead_transfer_gripper",
        "gantry_gripper",
    ):
        candidate = _asset_value(assets, key)
        if isinstance(candidate, bpy.types.Object):
            return candidate
    candidate = bpy.data.objects.get("SUM_V7_Gantry_ThreeJawBearingGripper")
    return candidate if isinstance(candidate, bpy.types.Object) else None


def _resolve_final_portal(assets: Mapping[str, Any]) -> bpy.types.Object | None:
    for key in (
        "final_inspection_portal",
        "final_precision_inspection_portal",
        "final_portal",
        "exit_portal",
    ):
        candidate = _asset_value(assets, key)
        if isinstance(candidate, bpy.types.Object):
            return candidate
    candidate = bpy.data.objects.get("SUM_ASSET_FinalPrecisionInspectionPortal")
    return candidate if isinstance(candidate, bpy.types.Object) else None


def _resolve_endpoint_environment_light(
    assets: Mapping[str, Any],
) -> bpy.types.Object | None:
    lights = _asset_value(assets, "fpv_lights")
    if isinstance(lights, Sequence) and not isinstance(lights, (str, bytes)):
        for candidate in lights:
            if (
                isinstance(candidate, bpy.types.Object)
                and candidate.type == "LIGHT"
                and candidate.name == "CIN_Aisle_LightPool_07"
            ):
                return candidate
    candidate = bpy.data.objects.get("CIN_Aisle_LightPool_07")
    if isinstance(candidate, bpy.types.Object) and candidate.type == "LIGHT":
        return candidate
    return None


def _has_driver(owner: Any, data_path: str) -> bool:
    animation_data = getattr(owner, "animation_data", None)
    drivers = getattr(animation_data, "drivers", ())
    return any(fcurve.data_path == data_path for fcurve in drivers)


def _restore_endpoint_environment_dimming() -> None:
    for light_data in list(bpy.data.lights):
        if not bool(light_data.get(_ENDPOINT_DIM_OWNER_KEY)):
            continue
        try:
            light_data.driver_remove("energy")
        except (AttributeError, RuntimeError, TypeError):
            pass
        try:
            baseline = float(light_data.get(_ENDPOINT_DIM_BASELINE_KEY))
        except (TypeError, ValueError):
            baseline = float("nan")
        if math.isfinite(baseline) and baseline >= 0.0:
            light_data.energy = baseline
        for key in (
            _ENDPOINT_DIM_OWNER_KEY,
            _ENDPOINT_DIM_BASELINE_KEY,
            "fpv_vfx_endpoint_dim_factor",
            "fpv_vfx_endpoint_dim_stops",
            "fpv_vfx_endpoint_dim_frame_start",
            "fpv_vfx_endpoint_dim_frame_end",
        ):
            if key in light_data:
                del light_data[key]


def _restore_endpoint_static_door_overrides() -> None:
    for obj in list(bpy.data.objects):
        if not bool(obj.get(_ENDPOINT_STATIC_HIDE_OWNER_KEY)):
            continue
        obj.hide_render = bool(obj.get(_ENDPOINT_STATIC_HIDE_RENDER_KEY, False))
        obj.hide_viewport = bool(obj.get(_ENDPOINT_STATIC_HIDE_VIEWPORT_KEY, False))
        for key in (
            _ENDPOINT_STATIC_HIDE_OWNER_KEY,
            _ENDPOINT_STATIC_HIDE_RENDER_KEY,
            _ENDPOINT_STATIC_HIDE_VIEWPORT_KEY,
        ):
            if key in obj:
                del obj[key]


def _hide_endpoint_static_door_components() -> list[str]:
    prefixes = (
        "SUM_FinalPortal_InspectionDoor_Panels",
        "SUM_FinalPortal_DoorPanel_Datums",
        "SUM_FinalPortal_InspectionWindow_Recess",
        "SUM_FinalPortal_InspectionWindow_Glass",
    )
    hidden: list[str] = []
    for obj in bpy.data.objects:
        if not any(obj.name.startswith(prefix) for prefix in prefixes):
            continue
        obj[_ENDPOINT_STATIC_HIDE_OWNER_KEY] = True
        obj[_ENDPOINT_STATIC_HIDE_RENDER_KEY] = bool(obj.hide_render)
        obj[_ENDPOINT_STATIC_HIDE_VIEWPORT_KEY] = bool(obj.hide_viewport)
        obj.hide_render = True
        obj.hide_viewport = True
        hidden.append(obj.name)
    return hidden


def _apply_endpoint_environment_dimming(
    light: bpy.types.Object | None,
    clock: _ClockBinding,
) -> bpy.types.Object | None:
    if light is None or light.type != "LIGHT" or light.data is None:
        return None
    light_data = light.data
    if _has_driver(light_data, "energy"):
        return None
    try:
        baseline = float(light_data.energy)
    except (AttributeError, TypeError, ValueError):
        return None
    if not math.isfinite(baseline) or baseline <= 0.0:
        return None

    final_factor = 2.0 ** (-ENDPOINT_LOCAL_DIM_STOPS)
    dim_progress = _ease_progress_expression(
        clock,
        ENDPOINT_DIM_START_FRAME,
        ENDPOINT_DIM_END_FRAME,
    )
    expression = (
        f"{baseline:.8f}*(1.0-{1.0 - final_factor:.8f}*({dim_progress}))"
    )
    if not _add_driver(light_data, "energy", expression, clock):
        try:
            light_data.driver_remove("energy")
        except (AttributeError, RuntimeError, TypeError):
            pass
        return None

    light_data[_ENDPOINT_DIM_OWNER_KEY] = True
    light_data[_ENDPOINT_DIM_BASELINE_KEY] = baseline
    light_data["fpv_vfx_endpoint_dim_factor"] = final_factor
    light_data["fpv_vfx_endpoint_dim_stops"] = -ENDPOINT_LOCAL_DIM_STOPS
    light_data["fpv_vfx_endpoint_dim_frame_start"] = ENDPOINT_DIM_START_FRAME
    light_data["fpv_vfx_endpoint_dim_frame_end"] = ENDPOINT_DIM_END_FRAME
    return light


def _resolve_grinding_contact(
    assets: Mapping[str, Any],
) -> bpy.types.Object | None:
    for key in ("grinding_contact", "grinding_anchor", "spark_origin"):
        candidate = _asset_value(assets, key)
        if isinstance(candidate, bpy.types.Object):
            return candidate
    candidate = bpy.data.objects.get("SUM_ANCHOR_GrindingContact")
    return candidate if isinstance(candidate, bpy.types.Object) else None


def _build_data_packets(
    assets: Mapping[str, Any],
    collection: bpy.types.Collection,
    clock: _ClockBinding,
    housing_material: bpy.types.Material,
    lens_material: bpy.types.Material,
) -> tuple[list[bpy.types.Object], list[bpy.types.Object]]:
    guide = _resolve_guide(assets)
    if guide is None:
        return [], []

    packet_roots: list[bpy.types.Object] = []
    render_objects: list[bpy.types.Object] = []
    half_gauge = _rail_gauge(assets, guide) * 0.5
    for window_index, window in enumerate(POST_PROJECT_WINDOWS, start=1):
        for side_index, (side_name, x) in enumerate(
            (("Left", -half_gauge), ("Right", half_gauge))
        ):
            prefix = f"SUM_FPV_VFX_Packet_{window_index:02d}_{side_name}"
            packet = modeling._empty(
                prefix,
                collection,
                location=(x, window.travel_start_m, _PACKET_HEIGHT_M),
                parent=guide,
                display_size=0.05,
            )
            packet[OWNER_KEY] = True
            packet["fpv_vfx_family"] = "guide_data_packets"
            packet["transition_slug"] = window.slug
            packet["visibility_frame_start"] = window.frame_start
            packet["visibility_frame_end"] = window.frame_end
            packet["rail_side"] = side_name.lower()
            packet["physical_fixture"] = True
            packet["time_source"] = clock.mode

            housing = modeling._box(
                f"{prefix}_Housing",
                (0.14, 0.42, 0.055),
                collection,
                parent=packet,
                material=housing_material,
                bevel=0.010,
                role="rail_clipped_data_packet_housing",
            )
            _tag_object(
                housing,
                family="guide_data_packets",
                pass_index=PASS_INDEX_DATA_PACKETS,
                role="rail_clipped_data_packet_housing",
                lookdev_role="dark_metal",
                clean_plate=False,
            )
            lens = modeling._box(
                f"{prefix}_Lens",
                (0.075, 0.29, 0.014),
                collection,
                location=(0.0, 0.0, 0.034),
                parent=packet,
                material=lens_material,
                bevel=0.004,
                role="restrained_physical_data_light_lens",
            )
            _tag_object(
                lens,
                family="guide_data_packets",
                pass_index=PASS_INDEX_DATA_PACKETS,
                role="restrained_physical_data_light_lens",
                lookdev_role="signal",
                clean_plate=False,
            )

            boundary_start = window.frame_start - 1 + side_index * 2
            boundary_end = window.frame_end + 1
            _drive_windowed_scale(
                packet,
                clock,
                boundary_start,
                boundary_end,
                ramp_fraction=0.18,
            )
            progress = _progress_expression(
                clock,
                boundary_start,
                boundary_end,
            )
            travel = window.travel_end_m - window.travel_start_m
            _add_driver(
                packet,
                "location",
                f"{window.travel_start_m:.6f}+{travel:.6f}*({progress})",
                clock,
                index=1,
            )
            packet_roots.append(packet)
            render_objects.extend((housing, lens))
    return packet_roots, render_objects


_DROPLETS = tuple(
    (
        -0.018 + (index / 95.0) * 0.145,
        math.sin(index * 2.399) * (0.006 + (index / 95.0) * 0.026),
        0.003 + (index % 13) * 0.0038 + (index / 95.0) * 0.035,
        0.00072 + (index % 5) * 0.00016,
        1.45 + (index % 7) * 0.11,
    )
    for index in range(96)
)


def _droplet_geometry() -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    local_faces = (
        (0, 2, 4),
        (2, 1, 4),
        (1, 3, 4),
        (3, 0, 4),
        (2, 0, 5),
        (1, 2, 5),
        (3, 1, 5),
        (0, 3, 5),
    )
    for x, y, z, radius, stretch in _DROPLETS:
        offset = len(vertices)
        vertices.extend(
            (
                (x - radius, y, z),
                (x + radius, y, z),
                (x, y - radius * 0.70, z),
                (x, y + radius * 0.70, z),
                (x, y, z + radius * stretch),
                (x, y, z - radius * stretch),
            )
        )
        faces.extend(tuple(offset + index for index in face) for face in local_faces)
    return vertices, faces


def _splash_sheet_geometry() -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    segment_count = 10
    for ribbon in range(5):
        base = (ribbon - 2) * 0.008
        start = len(vertices)
        for segment in range(segment_count + 1):
            phase = segment / segment_count
            x = 0.004 + phase * (0.115 + ribbon * 0.008)
            center_y = base + math.sin(phase * math.pi) * (ribbon - 2) * 0.003
            z = 0.004 + phase * 0.072 - phase * phase * (0.038 + ribbon * 0.002)
            half_width = 0.0012 + phase * (0.0026 + ribbon * 0.00035)
            vertices.extend(((x, center_y - half_width, z), (x, center_y + half_width, z)))
        for segment in range(segment_count):
            offset = start + segment * 2
            faces.append((offset, offset + 1, offset + 3, offset + 2))
    return vertices, faces


def _build_grinding_mist(
    assets: Mapping[str, Any],
    collection: bpy.types.Collection,
    clock: _ClockBinding,
    material: bpy.types.Material,
) -> tuple[bpy.types.Object | None, list[bpy.types.Object]]:
    contact = _resolve_grinding_contact(assets)
    if contact is None:
        return None, []

    root = modeling._empty(
        "SUM_FPV_VFX_GrindingMistLayer",
        collection,
        parent=contact,
        display_size=0.035,
    )
    root[OWNER_KEY] = True
    root["fpv_vfx_family"] = "grinding_mist_droplets"
    root["layer_count"] = 1
    root["droplet_count"] = len(_DROPLETS)
    root["simulation"] = "deterministic_low_density_mesh"
    root["duplicates_existing_sparks"] = False
    root["visibility_frame_start"] = GRINDING_MIST_WINDOW[0]
    root["visibility_frame_end"] = GRINDING_MIST_WINDOW[1]
    root["time_source"] = clock.mode

    vertices, faces = _droplet_geometry()
    droplets = modeling._mesh_object(
        "SUM_FPV_VFX_GrindingMistDroplets",
        vertices,
        faces,
        collection,
        parent=root,
        material=material,
        smooth=True,
    )
    _tag_object(
        droplets,
        family="grinding_mist_droplets",
        pass_index=PASS_INDEX_GRINDING_MIST,
        role="single_local_coolant_mist_droplet_layer",
        lookdev_role="glass",
        clean_plate=True,
    )
    sheet_vertices, sheet_faces = _splash_sheet_geometry()
    splash_sheets = modeling._mesh_object(
        "SUM_FPV_VFX_GrindingCoolantSplashSheets",
        sheet_vertices,
        sheet_faces,
        collection,
        parent=root,
        material=material,
        smooth=True,
    )
    _tag_object(
        splash_sheets,
        family="grinding_mist_droplets",
        pass_index=PASS_INDEX_GRINDING_MIST,
        role="thin_centrifuged_coolant_splash_fan",
        lookdev_role="coolant",
        clean_plate=True,
    )
    _drive_windowed_scale(
        root,
        clock,
        GRINDING_MIST_WINDOW[0],
        GRINDING_MIST_WINDOW[1],
        ramp_fraction=0.20,
    )
    progress = _progress_expression(
        clock,
        GRINDING_MIST_WINDOW[0],
        GRINDING_MIST_WINDOW[1],
    )
    _add_driver(root, "location", f"0.105*({progress})", clock, index=0)
    _add_driver(root, "location", f"0.024*sin(6.283185*({progress}))", clock, index=1)
    _add_driver(
        root,
        "location",
        f"0.115*({progress})-0.072*({progress})*({progress})",
        clock,
        index=2,
    )
    _add_driver(root, "rotation_euler", f"1.2*({progress})", clock, index=0)
    return root, [splash_sheets, droplets]


def _build_overhead_reveal_practical(
    assets: Mapping[str, Any],
    collection: bpy.types.Collection,
    clock: _ClockBinding,
    housing_material: bpy.types.Material,
) -> list[bpy.types.Object]:
    gripper = _resolve_overhead_gripper(assets)
    if gripper is None:
        return []

    housing = modeling._box(
        "SUM_FPV_VFX_GantryInspectionLight_Housing",
        (0.20, 0.11, 0.08),
        collection,
        location=(0.55, -0.65, 0.15),
        parent=gripper,
        material=housing_material,
        bevel=0.018,
        role="gantry_gripper_inspection_light_housing",
    )
    _tag_object(
        housing,
        family="overhead_reveal_practical",
        pass_index=PASS_INDEX_OVERHEAD_REVEAL,
        role="gantry_gripper_inspection_light_housing",
        lookdev_role="mechanism",
        clean_plate=True,
    )

    light_data = bpy.data.lights.new(
        "SUM_FPV_VFX_GantryInspectionLight_Point",
        type="POINT",
    )
    light_data[OWNER_KEY] = True
    light_data["fpv_vfx_compositor_group"] = "overhead_reveal_practical"
    light_data.color = (0.82, 0.90, 1.0)
    light_data.energy = 0.0
    light_data.shadow_soft_size = 0.34
    if hasattr(light_data, "use_shadow"):
        light_data.use_shadow = True
    if hasattr(light_data, "diffuse_factor"):
        light_data.diffuse_factor = 0.86
    if hasattr(light_data, "specular_factor"):
        light_data.specular_factor = 0.42
    if hasattr(light_data, "volume_factor"):
        light_data.volume_factor = 0.0

    light = bpy.data.objects.new(
        "SUM_FPV_VFX_GantryInspectionLight_Point",
        light_data,
    )
    collection.objects.link(light)
    modeling._apply_local_transform(
        light,
        location=(0.55, -0.65, 0.15),
        rotation=(0.0, 0.0, 0.0),
        parent=gripper,
    )
    _tag_object(
        light,
        family="overhead_reveal_practical",
        pass_index=PASS_INDEX_OVERHEAD_REVEAL,
        role="gantry_gripper_local_inspection_practical",
        lookdev_role="luminaire",
        clean_plate=True,
    )
    envelope = _window_expression(
        clock,
        OVERHEAD_REVEAL_WINDOW[0],
        OVERHEAD_REVEAL_WINDOW[1],
        ramp_fraction=0.24,
    )
    _add_driver(light_data, "energy", f"680.0*({envelope})", clock)
    light["fixture_cct_kelvin"] = 4800
    light["energy_frame_start"] = OVERHEAD_REVEAL_WINDOW[0]
    light["energy_frame_end"] = OVERHEAD_REVEAL_WINDOW[1]
    light["maximum_artistic_energy_w"] = 680.0
    light["time_source"] = clock.mode
    return [housing, light]


def _screen_dimensions(screen: bpy.types.Object) -> tuple[float, float]:
    data = getattr(screen, "data", None)
    vertices = getattr(data, "vertices", None)
    if vertices is None or len(vertices) == 0:
        return 2.40, 1.50
    y_values = [float(vertex.co.y) for vertex in vertices]
    z_values = [float(vertex.co.z) for vertex in vertices]
    width = max(y_values) - min(y_values)
    height = max(z_values) - min(z_values)
    if width <= 0.10 or height <= 0.10:
        return 2.40, 1.50
    return width, height


def _new_screen_area_light(
    index: int,
    screen: bpy.types.Object,
    height: float,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    name = f"SUM_FPV_VFX_ScreenPractical_{index:02d}_Area"
    light_data = bpy.data.lights.new(name, type="AREA")
    light_data[OWNER_KEY] = True
    light_data["fpv_vfx_compositor_group"] = "screen_edge_practicals"
    light_data.color = (1.0, 0.72, 0.46)
    light_data.energy = 0.0
    light_data.shape = "RECTANGLE"
    light_data.size = max(0.40, height * 0.72)
    if hasattr(light_data, "size_y"):
        light_data.size_y = 0.08
    if hasattr(light_data, "use_shadow"):
        light_data.use_shadow = False
    if hasattr(light_data, "diffuse_factor"):
        light_data.diffuse_factor = 0.32
    if hasattr(light_data, "specular_factor"):
        light_data.specular_factor = 0.12
    if hasattr(light_data, "volume_factor"):
        light_data.volume_factor = 0.0

    light = bpy.data.objects.new(name, light_data)
    collection.objects.link(light)
    modeling._apply_local_transform(
        light,
        location=(0.045, 0.0, 0.0),
        rotation=(0.0, -math.pi * 0.5, 0.0),
        parent=screen,
    )
    _tag_object(
        light,
        family="screen_edge_practicals",
        pass_index=PASS_INDEX_SCREEN_PRACTICALS,
        role="low_energy_screen_edge_practical_area_light",
        lookdev_role="luminaire",
        clean_plate=True,
    )
    light["fixture_cct_kelvin"] = 3500
    light["maximum_artistic_energy_w"] = 18.0
    return light


def _build_screen_practicals(
    screens: Sequence[bpy.types.Object],
    collection: bpy.types.Collection,
    clock: _ClockBinding,
    material: bpy.types.Material,
) -> list[bpy.types.Object]:
    practicals: list[bpy.types.Object] = []
    for index, screen in enumerate(screens[:4], start=1):
        width, height = _screen_dimensions(screen)
        focus_frame = int(screen.get("focus_frame", PROJECT_FOCUS_FRAMES[index - 1]))
        frame_start = max(1, focus_frame - _SCREEN_PRACTICAL_HALF_WINDOW_FRAMES)
        frame_end = min(
            FILM_FRAME_COUNT,
            focus_frame + _SCREEN_PRACTICAL_HALF_WINDOW_FRAMES,
        )
        envelope = _window_expression(
            clock,
            frame_start,
            frame_end,
            ramp_fraction=0.28,
        )
        scan_progress = _progress_expression(clock, frame_start, frame_end)
        edge_y = width * 0.5 + 0.045
        for side_name, side in (("Lower", -1.0), ("Upper", 1.0)):
            bar = modeling._box(
                f"SUM_FPV_VFX_ScreenPractical_{index:02d}_{side_name}Edge",
                (0.024, 0.035, height * 0.82),
                collection,
                location=(0.022, side * edge_y, 0.0),
                parent=screen,
                material=material,
                bevel=0.005,
                role="recessed_screen_edge_practical_fixture",
            )
            _tag_object(
                bar,
                family="screen_edge_practicals",
                pass_index=PASS_INDEX_SCREEN_PRACTICALS,
                role="recessed_screen_edge_practical_fixture",
                lookdev_role="signal",
                clean_plate=True,
            )
            bar["fixture_cct_kelvin"] = 3500
            bar["emission_policy"] = "below_existing_compositor_glow_threshold"
            bar["interaction_motion"] = "screen_normal_lift_55mm"
            _add_driver(
                bar,
                "location",
                f"0.022+0.055*({envelope})",
                clock,
                index=0,
            )
            practicals.append(bar)

        for segment_name, segment_side in (("Left", -1.0), ("Right", 1.0)):
            scan_line = modeling._box(
                f"SUM_FPV_VFX_ScreenPractical_{index:02d}_ScanLine_{segment_name}",
                (0.014, width * 0.39, 0.012),
                collection,
                location=(
                    0.086,
                    segment_side * width * 0.25,
                    -height * 0.42,
                ),
                parent=screen,
                material=material,
                bevel=0.003,
                role="split_physical_screen_focus_scan_line",
            )
            _tag_object(
                scan_line,
                family="screen_edge_practicals",
                pass_index=PASS_INDEX_SCREEN_PRACTICALS,
                role="split_physical_screen_focus_scan_line",
                lookdev_role="signal",
                clean_plate=True,
            )
            _drive_windowed_scale(
                scan_line,
                clock,
                frame_start,
                frame_end,
                ramp_fraction=0.28,
            )
            _add_driver(
                scan_line,
                "location",
                f"{-height * 0.42:.6f}+{height * 0.84:.6f}*({scan_progress})",
                clock,
                index=2,
            )
            scan_line["focus_frame"] = focus_frame
            scan_line["interaction_motion"] = (
                "split_vertical_readout_scan_with_center_content_clearance"
            )
            practicals.append(scan_line)

        light = _new_screen_area_light(index, screen, height, collection)
        _add_driver(
            light.data,
            "energy",
            f"18.0*({envelope})",
            clock,
        )
        light["focus_frame"] = focus_frame
        light["energy_frame_start"] = frame_start
        light["energy_frame_end"] = frame_end
        light["time_source"] = clock.mode
        practicals.append(light)
    return practicals


def _principled_input(
    material: bpy.types.Material,
    names: Sequence[str],
) -> Any | None:
    if not material.use_nodes or material.node_tree is None:
        return None
    for node in material.node_tree.nodes:
        if node.type != "BSDF_PRINCIPLED":
            continue
        for name in names:
            socket = node.inputs.get(name)
            if socket is not None:
                return socket
    return None


def _new_endpoint_guide_light(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    clock: _ClockBinding,
    blackout_expression: str,
) -> bpy.types.Object:
    name = "SUM_FPV_VFX_FinalGate_BlackFieldNoSpill"
    light_data = bpy.data.lights.new(name, type="AREA")
    light_data[OWNER_KEY] = True
    light_data["fpv_vfx_compositor_group"] = "endpoint_gate_cue"
    light_data.color = (0.02, 0.025, 0.03)
    light_data.energy = 0.0
    light_data.shape = "RECTANGLE"
    light_data.size = 4.80
    if hasattr(light_data, "size_y"):
        light_data.size_y = 3.90
    if hasattr(light_data, "use_shadow"):
        light_data.use_shadow = False
    if hasattr(light_data, "diffuse_factor"):
        light_data.diffuse_factor = 0.88
    if hasattr(light_data, "specular_factor"):
        light_data.specular_factor = 0.30
    if hasattr(light_data, "volume_factor"):
        light_data.volume_factor = 0.0
    if hasattr(light_data, "normalize"):
        light_data.normalize = True

    light = bpy.data.objects.new(name, light_data)
    collection.objects.link(light)
    modeling._apply_local_transform(
        light,
        location=(0.0, 2.64, -0.12),
        rotation=(-math.pi * 0.5, 0.0, 0.0),
        parent=root,
    )
    _tag_object(
        light,
        family="endpoint_gate_cue",
        pass_index=PASS_INDEX_ENDPOINT_GATE,
        role="threshold_black_field_no_spill",
        lookdev_role="luminaire",
        clean_plate=True,
    )
    light["fixture_cct_kelvin"] = 6200
    light["maximum_artistic_energy_w"] = ENDPOINT_MAX_LIGHT_ENERGY_W
    light["volume_contribution"] = 0.0
    light["time_source"] = clock.mode
    _add_driver(
        light_data,
        "energy",
        f"{ENDPOINT_MAX_LIGHT_ENERGY_W:.4f}*({blackout_expression})",
        clock,
    )
    return light


def _build_endpoint_door_leaf(
    side: float,
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    clock: _ClockBinding,
    panel_material: bpy.types.Material,
    trim_material: bpy.types.Material,
    glass_material: bpy.types.Material,
    open_expression: str,
) -> tuple[bpy.types.Object, list[bpy.types.Object]]:
    label = "Left" if side < 0.0 else "Right"
    leaf = modeling._empty(
        f"SUM_FPV_VFX_FinalGate_{label}Leaf",
        collection,
        parent=root,
        display_size=0.10,
    )
    _tag_object(
        leaf,
        family="endpoint_gate_cue",
        pass_index=PASS_INDEX_ENDPOINT_GATE,
        role="motorized_split_inspection_door_leaf",
        lookdev_role="mechanism",
        clean_plate=True,
    )
    _add_driver(
        leaf,
        "location",
        f"{side * ENDPOINT_DOOR_LEAF_TRAVEL_M:.6f}*({open_expression})",
        clock,
        index=0,
    )
    leaf["door_side"] = label.lower()
    leaf["door_open_frame_start"] = ENDPOINT_DOOR_OPEN_START_FRAME
    leaf["door_open_frame_end"] = ENDPOINT_DOOR_OPEN_END_FRAME
    leaf["door_leaf_travel_m"] = ENDPOINT_DOOR_LEAF_TRAVEL_M
    leaf["drive_type"] = "synchronized_servo_linear_track"

    center_x = side * 1.22
    parts: list[bpy.types.Object] = []
    panel = modeling._box(
        f"SUM_FPV_VFX_FinalGate_{label}Leaf_Panel",
        (2.38, 0.14, 4.46),
        collection,
        location=(center_x, 2.50, -0.20),
        parent=leaf,
        material=panel_material,
        bevel=0.032,
        role="double_skin_powder_coated_door_panel",
    )
    parts.append(panel)

    for suffix, x, z, dimensions in (
        ("SeamStile", side * 0.10, -0.20, (0.085, 0.17, 4.30)),
        ("OuterStile", side * 2.34, -0.20, (0.085, 0.17, 4.30)),
        ("TopRail", center_x, 1.93, (2.26, 0.17, 0.085)),
        ("BottomRail", center_x, -2.33, (2.26, 0.17, 0.085)),
    ):
        parts.append(
            modeling._box(
                f"SUM_FPV_VFX_FinalGate_{label}Leaf_{suffix}",
                dimensions,
                collection,
                location=(x, 2.415, z),
                parent=leaf,
                material=trim_material,
                bevel=0.008,
                role="machined_inspection_door_edge_frame",
            )
        )

    window_x = side * 0.76
    recess = modeling._box(
        f"SUM_FPV_VFX_FinalGate_{label}Leaf_WindowRecess",
        (1.38, 0.050, 0.64),
        collection,
        location=(window_x, 2.405, 0.56),
        parent=leaf,
        material=trim_material,
        bevel=0.014,
        role="split_door_observation_window_recess",
    )
    glass = modeling._box(
        f"SUM_FPV_VFX_FinalGate_{label}Leaf_WindowGlass",
        (1.22, 0.026, 0.46),
        collection,
        location=(window_x, 2.374, 0.56),
        parent=leaf,
        material=glass_material,
        bevel=0.010,
        role="laminated_split_door_observation_glass",
    )
    handle = modeling._box(
        f"SUM_FPV_VFX_FinalGate_{label}Leaf_Handle",
        (0.075, 0.11, 0.54),
        collection,
        location=(side * 0.30, 2.31, -0.72),
        parent=leaf,
        material=trim_material,
        bevel=0.020,
        role="recessed_vertical_door_service_handle",
    )
    parts.extend((recess, glass, handle))

    for roller_index, x in enumerate((side * 0.58, side * 1.84), start=1):
        parts.append(
            modeling._box(
                f"SUM_FPV_VFX_FinalGate_{label}Leaf_Roller_{roller_index:02d}",
                (0.18, 0.18, 0.12),
                collection,
                location=(x, 2.49, 2.08),
                parent=leaf,
                material=trim_material,
                bevel=0.018,
                role="enclosed_linear_door_track_roller",
            )
        )

    for part in parts:
        _tag_object(
            part,
            family="endpoint_gate_cue",
            pass_index=PASS_INDEX_ENDPOINT_GATE,
            role=str(part.get("sum_part_role", "motorized_split_gate_component")),
            lookdev_role="glass" if part is glass else "mechanism",
            clean_plate=True,
        )
    return leaf, parts


def _build_endpoint_gate_cue(
    assets: Mapping[str, Any],
    collection: bpy.types.Collection,
    clock: _ClockBinding,
    seam_material: bpy.types.Material,
    blackout_material: bpy.types.Material,
    panel_material: bpy.types.Material,
    trim_material: bpy.types.Material,
    glass_material: bpy.types.Material,
) -> tuple[bpy.types.Object | None, list[bpy.types.Object]]:
    portal = _resolve_final_portal(assets)
    if portal is None:
        return None, []

    hidden_components = _hide_endpoint_static_door_components()
    root = modeling._empty(
        "SUM_FPV_VFX_FinalGateCue",
        collection,
        parent=portal,
        display_size=0.12,
    )
    root[OWNER_KEY] = True
    root["fpv_vfx_family"] = "endpoint_gate_cue"
    root["gate_state"] = "split_sliding_open"
    root["door_leaf_motion"] = "synchronized_lateral_open"
    root["cue_treatment"] = "restrained_seam_to_physical_black_field"
    root["visibility_frame_start"] = ENDPOINT_DIM_START_FRAME
    root["door_open_frame_start"] = ENDPOINT_DOOR_OPEN_START_FRAME
    root["door_open_frame_end"] = ENDPOINT_DOOR_OPEN_END_FRAME
    root["blackout_frame_start"] = ENDPOINT_BLACKOUT_START_FRAME
    root["blackout_frame_end"] = ENDPOINT_BLACKOUT_END_FRAME
    root["focus_frame"] = ENDPOINT_FOCUS_FRAME
    root["settle_frame"] = ENDPOINT_SETTLE_FRAME
    root["final_static_frame_window"] = (
        f"{ENDPOINT_SETTLE_FRAME}-{ENDPOINT_FINAL_FRAME}"
    )
    root["static_door_components_replaced"] = json.dumps(hidden_components)
    root["time_source"] = clock.mode
    root["no_neon_outline"] = True
    root["no_text"] = True
    root["no_particles"] = True
    root["no_volume"] = True

    open_expression = _endpoint_open_expression(clock)
    blackout_expression = _endpoint_blackout_expression(clock)
    cue_expression = _endpoint_cue_expression(clock)

    black_field = modeling._box(
        "SUM_FPV_VFX_FinalGate_BlackField",
        (5.06, 0.045, 4.22),
        collection,
        location=(0.0, 2.70, -0.16),
        parent=root,
        material=blackout_material,
        bevel=0.012,
        role="physical_threshold_black_field",
    )
    _tag_object(
        black_field,
        family="endpoint_gate_cue",
        pass_index=PASS_INDEX_ENDPOINT_GATE,
        role="physical_threshold_black_field",
        lookdev_role="absorption",
        clean_plate=True,
    )
    black_field["handoff_frame"] = ENDPOINT_SETTLE_FRAME
    black_field["handoff_target"] = "web_summary_surface_from_black"
    black_field["emission_policy"] = "none"

    seam = modeling._box(
        "SUM_FPV_VFX_FinalGate_CenterSeam",
        (0.014, 0.018, 3.98),
        collection,
        location=(0.0, 2.365, -0.12),
        parent=root,
        material=seam_material,
        bevel=0.002,
        role="recessed_low_energy_gate_center_seam",
    )
    _tag_object(
        seam,
        family="endpoint_gate_cue",
        pass_index=PASS_INDEX_ENDPOINT_GATE,
        role="recessed_low_energy_gate_center_seam",
        lookdev_role="signal",
        clean_plate=True,
    )
    seam["physical_width_m"] = 0.014
    seam["emission_policy"] = "low_energy_seam_fades_as_split_gate_opens"
    _add_driver(seam, "scale", f"1.0-({open_expression})", clock, index=0)

    seam_emission = _principled_input(seam_material, ("Emission Strength",))
    seam_driver = False
    if seam_emission is not None:
        seam_driver = _add_driver(
            seam_emission,
            "default_value",
            f"{ENDPOINT_MAX_EMISSION_STRENGTH:.4f}*({cue_expression})",
            clock,
        )
    seam["emission_driver_available"] = seam_driver

    black_field["emission_driver_available"] = False

    door_objects: list[bpy.types.Object] = []
    for side in (-1.0, 1.0):
        leaf, parts = _build_endpoint_door_leaf(
            side,
            root,
            collection,
            clock,
            panel_material,
            trim_material,
            glass_material,
            open_expression,
        )
        door_objects.extend((leaf, *parts))

    track_cover = modeling._box(
        "SUM_FPV_VFX_FinalGate_ServoTrackCover",
        (5.36, 0.22, 0.20),
        collection,
        location=(0.0, 2.48, 2.16),
        parent=root,
        material=trim_material,
        bevel=0.020,
        role="enclosed_synchronized_door_servo_track",
    )
    _tag_object(
        track_cover,
        family="endpoint_gate_cue",
        pass_index=PASS_INDEX_ENDPOINT_GATE,
        role="enclosed_synchronized_door_servo_track",
        lookdev_role="mechanism",
        clean_plate=True,
    )
    guide_light = _new_endpoint_guide_light(
        root,
        collection,
        clock,
        blackout_expression,
    )
    return root, [black_field, seam, track_cover, guide_light, *door_objects]


def _enable_metadata_passes(scene: bpy.types.Scene) -> None:
    for view_layer in scene.view_layers:
        for property_name in ("use_pass_object_index", "use_pass_emit"):
            if hasattr(view_layer, property_name):
                try:
                    setattr(view_layer, property_name, True)
                except (AttributeError, TypeError, ValueError):
                    pass


def _compositor_manifest(
    clock: _ClockBinding,
    packet_objects: Sequence[bpy.types.Object],
    mist_objects: Sequence[bpy.types.Object],
    practical_objects: Sequence[bpy.types.Object],
    overhead_objects: Sequence[bpy.types.Object],
    endpoint_objects: Sequence[bpy.types.Object],
    endpoint_environment_light: bpy.types.Object | None,
    missing_assets: Sequence[str],
) -> dict[str, Any]:
    return {
        "version": 1,
        "film": {
            "duration_seconds": FILM_DURATION_SECONDS,
            "fps": FILM_FPS,
            "frame_start": 1,
            "frame_end": FILM_FRAME_COUNT,
            "focus_frames": FILM_FOCUS_FRAMES,
        },
        "time_source": clock.mode,
        "post_project_windows": [
            {
                "id": window.slug,
                "frame_start": window.frame_start,
                "frame_end": window.frame_end,
                "travel_start_m": window.travel_start_m,
                "travel_end_m": window.travel_end_m,
            }
            for window in POST_PROJECT_WINDOWS
        ],
        "groups": {
            "guide_data_packets": {
                "object_index": PASS_INDEX_DATA_PACKETS,
                "objects": [obj.name for obj in packet_objects],
                "beauty": True,
                "clean_plate": False,
                "screen_matte": False,
            },
            "grinding_mist_droplets": {
                "object_index": PASS_INDEX_GRINDING_MIST,
                "objects": [obj.name for obj in mist_objects],
                "beauty": True,
                "clean_plate": True,
                "screen_matte": False,
            },
            "screen_edge_practicals": {
                "object_index": PASS_INDEX_SCREEN_PRACTICALS,
                "objects": [obj.name for obj in practical_objects],
                "beauty": True,
                "clean_plate": True,
                "screen_matte": False,
            },
            "overhead_reveal_practical": {
                "object_index": PASS_INDEX_OVERHEAD_REVEAL,
                "objects": [obj.name for obj in overhead_objects],
                "beauty": True,
                "clean_plate": True,
                "screen_matte": False,
                "frame_window": list(OVERHEAD_REVEAL_WINDOW),
                "design": "gripper_mounted_inspection_luminaire",
            },
            "endpoint_gate_cue": {
                "object_index": PASS_INDEX_ENDPOINT_GATE,
                "objects": [obj.name for obj in endpoint_objects],
                "beauty": True,
                "clean_plate": True,
                "screen_matte": False,
                "frame_start": ENDPOINT_DIM_START_FRAME,
                "focus_frame": ENDPOINT_FOCUS_FRAME,
                "breath_peak_frame": ENDPOINT_BREATH_PEAK_FRAME,
                "door_open_frame_window": [
                    ENDPOINT_DOOR_OPEN_START_FRAME,
                    ENDPOINT_DOOR_OPEN_END_FRAME,
                ],
                "blackout_frame_window": [
                    ENDPOINT_BLACKOUT_START_FRAME,
                    ENDPOINT_BLACKOUT_END_FRAME,
                ],
                "settle_frame": ENDPOINT_SETTLE_FRAME,
                "final_static_frame_window": [
                    ENDPOINT_SETTLE_FRAME,
                    ENDPOINT_FINAL_FRAME,
                ],
                "door_state": "split_sliding_open",
                "visible_design": "physical_door_leaves_to_black_field",
                "web_handoff": "summary_surface",
            },
        },
        "endpoint_environment_dimming": {
            "light": (
                endpoint_environment_light.name
                if endpoint_environment_light is not None
                else None
            ),
            "scope": "final_aisle_light_pool_only",
            "frame_start": ENDPOINT_DIM_START_FRAME,
            "frame_end": ENDPOINT_DIM_END_FRAME,
            "stops": -ENDPOINT_LOCAL_DIM_STOPS,
            "final_energy_factor": 2.0 ** (-ENDPOINT_LOCAL_DIM_STOPS),
            "evidence_screen_materials_modified": False,
            "global_exposure_modified": False,
            "world_strength_modified": False,
        },
        "compositor_policy": {
            "add_nodes": False,
            "chromatic_aberration": False,
            "full_screen_holograms": False,
            "extra_bloom": False,
            "duplicate_sparks": False,
            "neon_outlines": False,
            "volumetric_fog": False,
            "endpoint_particles": False,
        },
        "missing_optional_assets": list(missing_assets),
    }


def augment_fpv_vfx(assets: dict[str, Any]) -> dict[str, Any]:
    """Build the managed FPV VFX layer and return the updated asset mapping.

    Missing guide, grinding-contact, or screen objects skip only their related
    effect family. The function never deletes collections it does not mark as
    its own; the legacy static portal door receives a reversible visibility
    override while the managed animated leaves are present.
    """

    if not isinstance(assets, dict):
        raise TypeError("assets must be a dictionary")

    scene = bpy.context.scene
    _restore_endpoint_environment_dimming()
    _restore_endpoint_static_door_overrides()
    root_collection = _asset_value(assets, "root_collection")
    collection = _reset_collection(
        root_collection if isinstance(root_collection, bpy.types.Collection) else None
    )
    layout_root = _asset_value(assets, "layout_root")
    root = modeling._empty(
        ROOT_OBJECT_NAME,
        collection,
        parent=layout_root if isinstance(layout_root, bpy.types.Object) else None,
        display_size=0.30,
    )
    root[OWNER_KEY] = True
    root["sum_asset_type"] = "restrained_physical_fpv_vfx_augmentation"
    root["film_duration_seconds"] = FILM_DURATION_SECONDS
    root["film_fps"] = FILM_FPS
    root["film_frame_count"] = FILM_FRAME_COUNT
    root["film_focus_frames"] = json.dumps(
        FILM_FOCUS_FRAMES,
        separators=(",", ":"),
    )
    root["no_camera_attached_overlay"] = True
    root["single_grinding_droplet_layer"] = True
    root["duplicate_sparks"] = False
    root["endpoint_gate_state"] = "split_sliding_open"
    root["endpoint_gate_door_motion"] = "synchronized_lateral_open"
    root["endpoint_cue_frame_window"] = (
        f"{ENDPOINT_DIM_START_FRAME}-{ENDPOINT_FINAL_FRAME}"
    )
    root["endpoint_door_open_frame_window"] = (
        f"{ENDPOINT_DOOR_OPEN_START_FRAME}-{ENDPOINT_DOOR_OPEN_END_FRAME}"
    )
    root["endpoint_blackout_frame_window"] = (
        f"{ENDPOINT_BLACKOUT_START_FRAME}-{ENDPOINT_BLACKOUT_END_FRAME}"
    )
    root["endpoint_final_static_frame_window"] = (
        f"{ENDPOINT_SETTLE_FRAME}-{ENDPOINT_FINAL_FRAME}"
    )
    root["endpoint_local_dim_stops"] = -ENDPOINT_LOCAL_DIM_STOPS
    root["evidence_screen_materials_modified"] = False
    root["global_exposure_modified"] = False
    root["world_strength_modified"] = False
    root["no_neon_outline"] = True
    root["no_endpoint_particles"] = True
    root["no_endpoint_volume"] = True

    materials = _asset_value(assets, "placeholder_materials")
    if not isinstance(materials, Mapping):
        materials = _asset_value(assets, "materials")
    housing_material = (
        materials.get("black_oxide")
        if isinstance(materials, Mapping)
        else None
    )
    if not isinstance(housing_material, bpy.types.Material):
        housing_material = _vfx_material(
            "SUM_FPV_VFX_MAT_PacketHousing",
            (0.018, 0.024, 0.028, 1.0),
            metallic=0.72,
            roughness=0.28,
        )
    packet_material = _vfx_material(
        "SUM_FPV_VFX_MAT_DataPacketLens",
        (0.025, 0.20, 0.24, 1.0),
        metallic=0.08,
        roughness=0.22,
        emission_color=(0.045, 0.52, 0.60, 1.0),
        emission_strength=1.45,
    )
    mist_material = _vfx_material(
        "SUM_FPV_VFX_MAT_GrindingCoolantMist",
        (0.66, 0.72, 0.61, 0.68),
        metallic=0.0,
        roughness=0.22,
        alpha=0.68,
        transmission=0.06,
    )
    practical_material = _vfx_material(
        "SUM_FPV_VFX_MAT_ScreenPractical",
        (0.42, 0.24, 0.10, 1.0),
        metallic=0.04,
        roughness=0.30,
        emission_color=(1.0, 0.58, 0.28, 1.0),
        emission_strength=0.82,
    )
    endpoint_material = _vfx_material(
        "SUM_FPV_VFX_MAT_FinalGateSeam",
        (0.72, 0.82, 0.90, 1.0),
        metallic=0.04,
        roughness=0.20,
        emission_color=(0.94, 0.975, 1.0, 1.0),
        emission_strength=0.0,
    )
    endpoint_material["maximum_emission_strength"] = (
        ENDPOINT_MAX_EMISSION_STRENGTH
    )
    endpoint_material["emission_policy"] = (
        "low_energy_center_seam_fades_into_physical_split_gate_opening"
    )
    blackout_material = _vfx_material(
        "SUM_FPV_VFX_MAT_FinalGateBlackField",
        (0.0015, 0.0020, 0.0030, 1.0),
        metallic=0.0,
        roughness=1.0,
        emission_color=(0.0, 0.0, 0.0, 1.0),
        emission_strength=0.0,
    )
    blackout_material["maximum_emission_strength"] = (
        ENDPOINT_BLACK_FIELD_EMISSION_STRENGTH
    )
    blackout_material["handoff_role"] = "web_summary_black_field"
    blackout_material["light_absorption_intent"] = "near_total"

    panel_material = (
        materials.get("enclosure_paint")
        if isinstance(materials, Mapping)
        else None
    )
    if not isinstance(panel_material, bpy.types.Material):
        panel_material = _vfx_material(
            "SUM_FPV_VFX_MAT_FinalGatePanel",
            (0.20, 0.23, 0.25, 1.0),
            metallic=0.42,
            roughness=0.30,
        )
    trim_material = housing_material
    glass_material = (
        materials.get("safety_glass")
        if isinstance(materials, Mapping)
        else None
    )
    if not isinstance(glass_material, bpy.types.Material):
        glass_material = _vfx_material(
            "SUM_FPV_VFX_MAT_FinalGateGlass",
            (0.10, 0.16, 0.18, 0.36),
            metallic=0.0,
            roughness=0.12,
            alpha=0.36,
            transmission=0.62,
        )

    screens = _resolve_screens(assets)
    timing_frames: set[int] = set()
    for window in POST_PROJECT_WINDOWS:
        for side_delay in (0, 2):
            timing_frames.add(window.frame_start - 1 + side_delay)
            timing_frames.add(window.frame_end + 1)
    timing_frames.update(GRINDING_MIST_WINDOW)
    timing_frames.update(OVERHEAD_REVEAL_WINDOW)
    for index, screen in enumerate(screens[:4]):
        focus_frame = int(screen.get("focus_frame", PROJECT_FOCUS_FRAMES[index]))
        timing_frames.update(
            (
                max(1, focus_frame - _SCREEN_PRACTICAL_HALF_WINDOW_FRAMES),
                min(
                    FILM_FRAME_COUNT,
                    focus_frame + _SCREEN_PRACTICAL_HALF_WINDOW_FRAMES,
                ),
            )
        )
    timing_frames.update(
        (
            ENDPOINT_DIM_START_FRAME,
            ENDPOINT_DIM_END_FRAME,
            ENDPOINT_DOOR_OPEN_START_FRAME,
            ENDPOINT_DOOR_OPEN_END_FRAME,
            ENDPOINT_FOCUS_FRAME,
            ENDPOINT_BREATH_PEAK_FRAME,
            ENDPOINT_BLACKOUT_START_FRAME,
            ENDPOINT_BLACKOUT_END_FRAME,
            ENDPOINT_SETTLE_FRAME,
            ENDPOINT_FINAL_FRAME,
        )
    )
    clock = _clock_binding(scene, tuple(timing_frames))

    packet_roots, packet_objects = _build_data_packets(
        assets,
        collection,
        clock,
        housing_material,
        packet_material,
    )
    mist_root, mist_objects = _build_grinding_mist(
        assets,
        collection,
        clock,
        mist_material,
    )
    overhead_objects = _build_overhead_reveal_practical(
        assets,
        collection,
        clock,
        housing_material,
    )
    practical_objects = _build_screen_practicals(
        screens,
        collection,
        clock,
        practical_material,
    )
    endpoint_root, endpoint_objects = _build_endpoint_gate_cue(
        assets,
        collection,
        clock,
        endpoint_material,
        blackout_material,
        panel_material,
        trim_material,
        glass_material,
    )
    endpoint_environment_light = None
    if endpoint_root is not None:
        endpoint_environment_light = _apply_endpoint_environment_dimming(
            _resolve_endpoint_environment_light(assets),
            clock,
        )

    missing_assets: list[str] = []
    if not packet_roots:
        missing_assets.append("dual_rail_guide")
    if mist_root is None:
        missing_assets.append("grinding_contact")
    if not overhead_objects:
        missing_assets.append("overhead_gantry_gripper")
    if len(screens) < 4:
        missing_assets.append(f"screen_displays:{len(screens)}/4")
    if endpoint_root is None:
        missing_assets.append("final_inspection_portal")
    elif endpoint_environment_light is None:
        missing_assets.append("endpoint_environment_light")

    manifest = _compositor_manifest(
        clock,
        packet_objects,
        mist_objects,
        practical_objects,
        overhead_objects,
        endpoint_objects,
        endpoint_environment_light,
        missing_assets,
    )
    encoded_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=True)
    root["compositor_manifest"] = encoded_manifest
    root["time_source"] = clock.mode
    root["missing_optional_assets"] = json.dumps(
        missing_assets,
        separators=(",", ":"),
    )
    scene["fpv_vfx_compositor_manifest"] = encoded_manifest
    scene["fpv_vfx_time_source"] = clock.mode
    scene["fpv_vfx_build_interface"] = (
        "production.blender.fpv_vfx.augment_fpv_vfx"
    )
    _enable_metadata_passes(scene)

    assets["fpv_vfx"] = root
    assets["fpv_vfx_collection"] = collection
    assets["fpv_vfx_data_packets"] = packet_roots
    assets["fpv_vfx_grinding_mist"] = mist_root
    assets["fpv_vfx_overhead_reveal_practical"] = overhead_objects
    assets["fpv_vfx_screen_practicals"] = practical_objects
    assets["fpv_vfx_endpoint_gate"] = endpoint_root
    assets["fpv_vfx_endpoint_gate_objects"] = endpoint_objects
    assets["fpv_vfx_endpoint_environment_light"] = endpoint_environment_light
    assets["fpv_vfx_metadata"] = manifest
    collections = assets.get("collections")
    if isinstance(collections, dict):
        collections["fpv_vfx"] = collection

    bpy.context.view_layer.update()
    return assets


__all__ = ["augment_fpv_vfx"]
