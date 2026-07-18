"""Restrained physical VFX for the 38-second FPV director's cut.

The augmentation owns one managed collection and can be called repeatedly. It
adds only rail-bound data packets, one local grinding droplet layer, small
screen-edge practical fixtures, and a restrained closed-gate endpoint cue.
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
from mathutils import Vector

import modeling


COLLECTION_NAME = "SUM_FPV_VFX"
ROOT_OBJECT_NAME = "SUM_ASSET_FPV_VFX"
OWNER_KEY = "fpv_vfx_generated"

FILM_DURATION_SECONDS = 38.000
FILM_FPS = 24
FILM_FRAME_COUNT = 912
FILM_FOCUS_FRAMES = (91, 169, 301, 433, 553, 673, 793, 877)
PROJECT_FOCUS_FRAMES = FILM_FOCUS_FRAMES[3:7]

PASS_INDEX_DATA_PACKETS = 61
PASS_INDEX_GRINDING_MIST = 62
PASS_INDEX_SCREEN_PRACTICALS = 63
PASS_INDEX_ENDPOINT_GATE = 64

ENDPOINT_DIM_START_FRAME = 853
ENDPOINT_DIM_END_FRAME = 865
ENDPOINT_FOCUS_FRAME = 877
ENDPOINT_BREATH_PEAK_FRAME = 889
ENDPOINT_SETTLE_FRAME = 901
ENDPOINT_FINAL_FRAME = 912
ENDPOINT_LOCAL_DIM_STOPS = 0.40
ENDPOINT_FINAL_CUE_LEVEL = 0.72
ENDPOINT_MAX_EMISSION_STRENGTH = 1.80
ENDPOINT_MAX_LIGHT_ENERGY_W = 28.0

_ENDPOINT_DIM_OWNER_KEY = "fpv_vfx_endpoint_dim_driver"
_ENDPOINT_DIM_BASELINE_KEY = "fpv_vfx_endpoint_dim_baseline_w"


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
    _PacketWindow("notice_to_takt", 452, 480, 54.0, 72.0),
    _PacketWindow("takt_to_visibility", 572, 600, 77.0, 96.0),
    _PacketWindow("visibility_to_systems", 692, 720, 101.0, 118.0),
    _PacketWindow("systems_to_close", 818, 840, 123.0, 136.0),
)

GRINDING_MIST_WINDOW = (277, 319)
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
        ENDPOINT_FOCUS_FRAME,
    )
    breath = _progress_expression(
        clock,
        ENDPOINT_FOCUS_FRAME,
        ENDPOINT_SETTLE_FRAME,
    )
    return (
        f"({ENDPOINT_FINAL_CUE_LEVEL:.4f}*({activation})+"
        f"{1.0 - ENDPOINT_FINAL_CUE_LEVEL:.4f}*"
        f"sin(3.14159265*({breath})))"
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
                and candidate.name == "CIN_Aisle_LightPool_05"
            ):
                return candidate
    candidate = bpy.data.objects.get("CIN_Aisle_LightPool_05")
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


_DROPLETS = (
    (-0.052, -0.018, 0.004, 0.0060, 1.60),
    (-0.030, 0.012, 0.020, 0.0045, 1.85),
    (-0.014, -0.026, 0.036, 0.0050, 1.45),
    (0.004, 0.018, 0.012, 0.0040, 1.75),
    (0.019, -0.010, 0.050, 0.0055, 1.95),
    (0.034, 0.025, 0.027, 0.0040, 1.55),
    (0.047, -0.021, 0.064, 0.0050, 1.80),
    (0.061, 0.013, 0.041, 0.0035, 1.65),
    (0.078, -0.006, 0.078, 0.0040, 2.00),
    (0.094, 0.022, 0.055, 0.0035, 1.70),
    (-0.066, 0.026, 0.052, 0.0040, 1.80),
    (-0.044, -0.034, 0.073, 0.0035, 2.10),
    (-0.020, 0.032, 0.088, 0.0045, 1.65),
    (0.012, -0.036, 0.094, 0.0040, 2.20),
    (0.044, 0.036, 0.102, 0.0045, 1.85),
    (0.072, -0.032, 0.112, 0.0038, 2.05),
    (0.108, 0.028, 0.086, 0.0042, 1.75),
    (0.128, -0.020, 0.062, 0.0036, 1.95),
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
    scene = bpy.context.scene
    camera = scene.camera
    original_frame = scene.frame_current
    if camera is not None:
        try:
            scene.frame_set(FILM_FOCUS_FRAMES[2])
            bpy.context.view_layer.update()
            contact_world = contact.matrix_world.translation.copy()
            toward_camera = camera.matrix_world.translation - contact_world
            if toward_camera.length_squared > 1.0e-8:
                toward_camera.normalize()
                world_offset = toward_camera * 0.040 + Vector((0.0, 0.012, 0.0))
                droplets.location = root.matrix_world.inverted().to_3x3() @ world_offset
        finally:
            scene.frame_set(original_frame)
            bpy.context.view_layer.update()
    droplets.scale = (1.18, 1.18, 1.18)
    _tag_object(
        droplets,
        family="grinding_mist_droplets",
        pass_index=PASS_INDEX_GRINDING_MIST,
        role="single_local_coolant_mist_droplet_layer",
        lookdev_role="glass",
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
    _add_driver(root, "location", f"0.035*({progress})", clock, index=2)
    return root, [droplets]


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
            practicals.append(bar)

        light = _new_screen_area_light(index, screen, height, collection)
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
    cue_expression: str,
) -> bpy.types.Object:
    name = "SUM_FPV_VFX_FinalGate_SeamSpill"
    light_data = bpy.data.lights.new(name, type="AREA")
    light_data[OWNER_KEY] = True
    light_data["fpv_vfx_compositor_group"] = "endpoint_gate_cue"
    light_data.color = (1.0, 0.55, 0.24)
    light_data.energy = 0.0
    light_data.shape = "RECTANGLE"
    light_data.size = 0.16
    if hasattr(light_data, "size_y"):
        light_data.size_y = 2.80
    if hasattr(light_data, "use_shadow"):
        light_data.use_shadow = False
    if hasattr(light_data, "diffuse_factor"):
        light_data.diffuse_factor = 0.42
    if hasattr(light_data, "specular_factor"):
        light_data.specular_factor = 0.16
    if hasattr(light_data, "volume_factor"):
        light_data.volume_factor = 0.0
    if hasattr(light_data, "normalize"):
        light_data.normalize = True

    light = bpy.data.objects.new(name, light_data)
    collection.objects.link(light)
    modeling._apply_local_transform(
        light,
        location=(0.0, 2.30, -0.12),
        rotation=(math.pi * 0.5, 0.0, 0.0),
        parent=root,
    )
    _tag_object(
        light,
        family="endpoint_gate_cue",
        pass_index=PASS_INDEX_ENDPOINT_GATE,
        role="recessed_center_seam_local_spill",
        lookdev_role="luminaire",
        clean_plate=True,
    )
    light["fixture_cct_kelvin"] = 2800
    light["maximum_artistic_energy_w"] = ENDPOINT_MAX_LIGHT_ENERGY_W
    light["volume_contribution"] = 0.0
    light["time_source"] = clock.mode
    _add_driver(
        light_data,
        "energy",
        f"{ENDPOINT_MAX_LIGHT_ENERGY_W:.4f}*({cue_expression})",
        clock,
    )
    return light


def _build_endpoint_gate_cue(
    assets: Mapping[str, Any],
    collection: bpy.types.Collection,
    clock: _ClockBinding,
    material: bpy.types.Material,
) -> tuple[bpy.types.Object | None, list[bpy.types.Object]]:
    portal = _resolve_final_portal(assets)
    if portal is None:
        return None, []

    root = modeling._empty(
        "SUM_FPV_VFX_FinalGateCue",
        collection,
        parent=portal,
        display_size=0.12,
    )
    root[OWNER_KEY] = True
    root["fpv_vfx_family"] = "endpoint_gate_cue"
    root["gate_state"] = "closed_armed"
    root["door_leaf_motion"] = "none"
    root["cue_treatment"] = "single_recessed_center_seam"
    root["visibility_frame_start"] = ENDPOINT_DIM_START_FRAME
    root["focus_frame"] = ENDPOINT_FOCUS_FRAME
    root["breath_peak_frame"] = ENDPOINT_BREATH_PEAK_FRAME
    root["settle_frame"] = ENDPOINT_SETTLE_FRAME
    root["final_static_frame_window"] = (
        f"{ENDPOINT_SETTLE_FRAME}-{ENDPOINT_FINAL_FRAME}"
    )
    root["time_source"] = clock.mode
    root["no_neon_outline"] = True
    root["no_text"] = True
    root["no_particles"] = True
    root["no_volume"] = True

    seam = modeling._box(
        "SUM_FPV_VFX_FinalGate_CenterSeam",
        (0.012, 0.010, 3.10),
        collection,
        location=(0.0, 2.449, -0.12),
        parent=root,
        material=material,
        bevel=0.002,
        role="recessed_closed_gate_center_light_seam",
    )
    _tag_object(
        seam,
        family="endpoint_gate_cue",
        pass_index=PASS_INDEX_ENDPOINT_GATE,
        role="recessed_closed_gate_center_light_seam",
        lookdev_role="signal",
        clean_plate=True,
    )
    seam["physical_width_m"] = 0.012
    seam["not_a_door_opening"] = True
    seam["emission_policy"] = "single_breath_then_static_below_bloom_threshold"

    cue_expression = _endpoint_cue_expression(clock)
    emission_input = _principled_input(
        material,
        ("Emission Strength",),
    )
    emission_driver = False
    if emission_input is not None:
        emission_driver = _add_driver(
            emission_input,
            "default_value",
            f"{ENDPOINT_MAX_EMISSION_STRENGTH:.4f}*({cue_expression})",
            clock,
        )
    seam["emission_driver_available"] = emission_driver
    guide_light = _new_endpoint_guide_light(
        root,
        collection,
        clock,
        cue_expression,
    )
    return root, [seam, guide_light]


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
            "endpoint_gate_cue": {
                "object_index": PASS_INDEX_ENDPOINT_GATE,
                "objects": [obj.name for obj in endpoint_objects],
                "beauty": True,
                "clean_plate": True,
                "screen_matte": False,
                "frame_start": ENDPOINT_DIM_START_FRAME,
                "focus_frame": ENDPOINT_FOCUS_FRAME,
                "breath_peak_frame": ENDPOINT_BREATH_PEAK_FRAME,
                "settle_frame": ENDPOINT_SETTLE_FRAME,
                "final_static_frame_window": [
                    ENDPOINT_SETTLE_FRAME,
                    ENDPOINT_FINAL_FRAME,
                ],
                "door_state": "closed",
                "visible_design": "single_recessed_center_seam",
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
    effect family. The function never deletes or edits collections it does not
    mark as its own.
    """

    if not isinstance(assets, dict):
        raise TypeError("assets must be a dictionary")

    scene = bpy.context.scene
    _restore_endpoint_environment_dimming()
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
    root["endpoint_gate_state"] = "closed_armed"
    root["endpoint_gate_door_motion"] = "none"
    root["endpoint_cue_frame_window"] = (
        f"{ENDPOINT_DIM_START_FRAME}-{ENDPOINT_FINAL_FRAME}"
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
        (0.56, 0.68, 0.64, 0.48),
        metallic=0.0,
        roughness=0.25,
        alpha=0.48,
        transmission=0.12,
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
        (0.16, 0.045, 0.010, 1.0),
        metallic=0.04,
        roughness=0.28,
        emission_color=(1.0, 0.34, 0.065, 1.0),
        emission_strength=0.0,
    )
    endpoint_material["maximum_emission_strength"] = (
        ENDPOINT_MAX_EMISSION_STRENGTH
    )
    endpoint_material["emission_policy"] = (
        "single_center_seam_breath_then_static_no_added_bloom"
    )

    screens = _resolve_screens(assets)
    timing_frames: set[int] = set()
    for window in POST_PROJECT_WINDOWS:
        for side_delay in (0, 2):
            timing_frames.add(window.frame_start - 1 + side_delay)
            timing_frames.add(window.frame_end + 1)
    timing_frames.update(GRINDING_MIST_WINDOW)
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
            ENDPOINT_FOCUS_FRAME,
            ENDPOINT_BREATH_PEAK_FRAME,
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
    if assets.get("grinding_coolant_splash"):
        # The precision grinder now owns animated fluid sheets and spherical
        # droplets. Avoid the older faceted proxy layer, which reads as white
        # debris in the close process shot.
        mist_root, mist_objects = None, []
    else:
        mist_root, mist_objects = _build_grinding_mist(
            assets,
            collection,
            clock,
            mist_material,
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
