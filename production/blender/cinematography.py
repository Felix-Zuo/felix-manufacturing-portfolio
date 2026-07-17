"""One-shot cinematography for the SUM industrial product film.

The camera runs on its own continuous clock. Scene motion can consume the
separate visual clock on ``CIN_TimeControl`` for bullet-time moments without
introducing a velocity cut in the camera move.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

try:
    import bpy
    from mathutils import Matrix, Quaternion, Vector
except ModuleNotFoundError:  # Allow static checks outside Blender.
    bpy = None
    Matrix = None
    Quaternion = None
    Vector = None


BASE_DURATION = 38.0
COLLECTION_NAME = "CINEMATOGRAPHY"
CORRIDOR_WAYPOINT_SECONDS = 14.45
GRINDING_PULLBACK_SECONDS = 13.25
GRINDING_CLEAR_SECONDS = 14.05
GRINDING_APPROACH_SECONDS = 10.75
CORRIDOR_GUIDE_START_SECONDS = 14.10
CORRIDOR_GUIDE_END_SECONDS = 14.85
TERMINAL_SETTLE_SECONDS = 37.25
AGV_OPENING_END_SECONDS = 2.40
ORIENTATION_SMOOTHING_PASSES = 4
MAX_ANGULAR_STEP_DEGREES = 1.70
MAX_ANGULAR_ACCEL_DEGREES = 0.30
ORIENTATION_BAKE_ACCELERATION_DEGREES = 0.25
ORIENTATION_LIMIT_SAFETY_FACTOR = 0.96

# Screen exits must hand the gaze back to the aisle before the camera passes
# the bay. Without these forward-looking keys the target briefly fell behind
# the moving camera, producing accidental full-frame enclosure wipes.
SCREEN_TRANSITION_LOOKS = (
    (19.45, (0.0, 63.0, 2.05)),
    (21.50, (0.0, 70.0, 2.12)),
    (24.55, (0.0, 86.0, 2.05)),
    (26.55, (0.0, 94.0, 2.12)),
    (29.55, (0.0, 109.0, 2.08)),
    (31.35, (0.0, 117.0, 2.14)),
    (34.70, (0.0, 132.0, 2.12)),
    (35.55, (0.0, 138.0, 2.32)),
)

GRINDING_TRANSITION_LOOKS = (
    # Hand the gaze forward before the camera passes the robot.  Keeping every
    # target in front of the lens avoids the near-180 degree correction that
    # previously made the stabilized camera stare into the machine shell.
    (7.20, (-2.80, 11.80, 1.55)),
    (7.55, (-2.30, 13.20, 1.65)),
    (8.00, (-1.40, 16.00, 1.70)),
    (8.55, (-0.40, 19.20, 1.75)),
    (9.15, (0.20, 22.30, 1.80)),
    (9.85, (1.50, 24.20, 1.82)),
    (10.25, (3.20, 25.20, 1.82)),
    (10.75, (5.45, 26.03, 1.82)),
    (13.00, (5.45, 26.03, 1.82)),
    # Leave the process cavity on a forward guide rather than carrying a
    # side-looking target behind the camera after the grinding hold.
    (13.20, (4.50, 28.00, 1.82)),
    (13.50, (3.00, 34.00, 1.78)),
    (13.80, (1.50, 40.00, 1.70)),
    (14.10, (0.00, 45.00, 1.58)),
)

# The camera deliberately escorts the AGV before handing attention to the
# bearing datum. Coordinates are authored as (lateral, aisle travel, height).
AGV_OPENING_LOOKS = (
    (0.00, (0.00, -0.15, 0.35)),
    (AGV_OPENING_END_SECONDS, (-0.62, 7.20, 0.75)),
)

# The bank is a transition accent, not a permanent FPV horizon effect. Every
# subject focus returns to level so machinery and project screens remain easy
# to inspect. Values are authored in seconds and degrees.
ROLL_KEYFRAMES = (
    (0.00, 0.0),
    (3.25, -1.00),
    (3.75, 0.0),
    (6.10, 0.75),
    (7.00, 0.0),
    (9.15, 1.25),
    (12.50, 0.0),
    (13.35, -0.85),
    (15.00, 0.0),
    (20.35, 0.75),
    (23.00, 0.0),
    (25.35, -0.75),
    (28.00, 0.0),
    (30.35, 0.75),
    (33.00, 0.0),
    (34.55, -0.60),
    (36.50, 0.0),
    (38.00, 0.0),
)


@dataclass(frozen=True)
class NarrativeBeat:
    slug: str
    label: str
    start_s: float
    end_s: float
    focus_s: float
    focus_hold_s: float
    fallback_target: tuple[float, float, float]
    fallback_camera: tuple[float, float, float]
    lens_mm: float
    speed_scale: float
    asset_aliases: tuple[str, ...]


@dataclass(frozen=True)
class BulletWindow:
    slug: str
    start_s: float
    end_s: float
    ramp_s: float
    minimum_scale: float
    capture_fps: int


# Eight focus beats, 912 frames at the default settings. The opening rail
# takeover is the approach into the bearing beat rather than a separate hero
# frame. Fallbacks use authoring (X lateral, +Y travel, +Z up) and are converted
# to film (X lateral, +Y up, -Z travel).
NARRATIVE_BEATS = (
    NarrativeBeat(
        "bearing",
        "Bearing datum",
        0.0,
        4.5,
        3.75,
        1.20,
        (-3.70, 8.00, 1.23),
        (-1.55, 6.30, 2.75),
        70.0,
        0.28,
        ("bearing_rotation_root",),
    ),
    NarrativeBeat(
        "handoff",
        "Mechanical arm handoff",
        4.5,
        9.0,
        7.00,
        1.50,
        (-4.00, 11.50, 1.83),
        (1.15, 11.20, 2.10),
        35.0,
        0.22,
        ("SUM_Robot_EndEffector_Frame", "robot_tcp"),
    ),
    NarrativeBeat(
        "grinding",
        "Grinding evidence",
        9.0,
        15.0,
        12.50,
        1.60,
        (5.45, 26.03, 1.82),
        (2.80, 23.20, 2.15),
        72.0,
        0.16,
        ("SUM_ANCHOR_GrindingContact",),
    ),
    NarrativeBeat(
        "notice",
        "Notice control card",
        15.0,
        20.0,
        18.00,
        1.50,
        (-2.65, 52.0, 2.45),
        (0.35, 49.15, 2.45),
        42.0,
        0.24,
        ("screen_display_01",),
    ),
    NarrativeBeat(
        "takt",
        "Takt control card",
        20.0,
        25.0,
        23.00,
        1.50,
        (2.65, 75.0, 2.45),
        (-0.35, 72.10, 2.55),
        42.0,
        0.24,
        ("screen_display_02", "screen_takt"),
    ),
    NarrativeBeat(
        "visibility",
        "Operations visibility",
        25.0,
        30.0,
        28.00,
        1.50,
        (-2.65, 99.0, 2.45),
        (0.30, 96.05, 2.34),
        40.0,
        0.24,
        ("screen_display_03",),
    ),
    NarrativeBeat(
        "systems",
        "Connected systems",
        30.0,
        35.0,
        33.00,
        2.00,
        (2.65, 121.0, 2.45),
        (-0.30, 117.85, 2.28),
        38.0,
        0.22,
        ("screen_display_04",),
    ),
    NarrativeBeat(
        "close",
        "Final improvement loop",
        35.0,
        38.0,
        36.50,
        1.25,
        (0.0, 140.0, 2.75),
        (0.0, 132.20, 2.00),
        35.0,
        0.45,
        (
            "final_inspection_portal",
            "final_precision_inspection_portal",
            "SUM_ASSET_FinalPrecisionInspectionPortal",
            "final_portal",
            "close_anchor",
            "exit_portal",
        ),
    ),
)


BULLET_WINDOWS = (
    BulletWindow("bearing_inspection", 3.25, 4.25, 0.34, 0.42, 48),
    BulletWindow("arm_handoff", 6.00, 8.00, 0.48, 0.22, 96),
    BulletWindow("grinding_sparks", 11.50, 13.25, 0.22, 0.16, 120),
)


def _require_blender() -> None:
    if bpy is None or Matrix is None or Quaternion is None or Vector is None:
        raise RuntimeError("build_cinematography() must run inside Blender")


def _authoring_to_film(coordinate: Any) -> Any:
    """Convert (x, travel, up) authoring coordinates to (x, up, -travel)."""

    x, travel, up = coordinate
    return Vector((float(x), float(up), -float(travel)))


def _normalized_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _walk_asset_value(container: Any, aliases: set[str], depth: int = 0) -> tuple[Any, str] | None:
    if container is None or depth > 4:
        return None

    if isinstance(container, Mapping):
        for key, value in container.items():
            if _normalized_name(key) in aliases:
                return value, str(key)
        for key in ("anchors", "objects", "assets", "screens", "cards", "rigs", "collections"):
            nested = container.get(key)
            found = _walk_asset_value(nested, aliases, depth + 1)
            if found:
                return found
        for value in container.values():
            if isinstance(value, Mapping):
                found = _walk_asset_value(value, aliases, depth + 1)
                if found:
                    return found
        return None

    for attribute in dir(container):
        if _normalized_name(attribute) in aliases:
            return getattr(container, attribute), attribute
    return None


def _average_vectors(values: Sequence[Any]) -> Any | None:
    vectors = [_world_location(value) for value in values]
    vectors = [value for value in vectors if value is not None]
    if not vectors:
        return None
    total = Vector((0.0, 0.0, 0.0))
    for value in vectors:
        total += value
    return total / len(vectors)


def _world_location(value: Any) -> Any | None:
    if value is None:
        return None
    if isinstance(value, Vector):
        return value.copy()
    if isinstance(value, str):
        return _world_location(bpy.data.objects.get(value))
    if isinstance(value, Mapping):
        for key in ("focus", "anchor", "target", "object", "location", "position"):
            if key in value:
                location = _world_location(value[key])
                if location is not None:
                    return location
        return _average_vectors(list(value.values()))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) >= 3 and all(isinstance(component, (int, float)) for component in value[:3]):
            return Vector((float(value[0]), float(value[1]), float(value[2])))
        return _average_vectors(value)
    if hasattr(value, "objects"):
        return _average_vectors(list(value.objects))
    if hasattr(value, "matrix_world"):
        return value.matrix_world.translation.copy()
    if hasattr(value, "location"):
        return Vector(value.location)
    return None


def _renderable_bounds_center(value: Any) -> Any | None:
    if isinstance(value, str):
        value = bpy.data.objects.get(value)
    if value is None or not hasattr(value, "matrix_world"):
        return None

    objects = [value]
    if hasattr(value, "children_recursive"):
        objects.extend(value.children_recursive)
    corners = []
    for obj in objects:
        if getattr(obj, "type", None) not in {"MESH", "CURVE", "FONT", "SURFACE"}:
            continue
        bound_box = getattr(obj, "bound_box", None)
        if bound_box is None:
            continue
        corners.extend(obj.matrix_world @ Vector(corner) for corner in bound_box)
    if not corners:
        return None

    minimum = Vector(
        (
            min(corner.x for corner in corners),
            min(corner.y for corner in corners),
            min(corner.z for corner in corners),
        )
    )
    maximum = Vector(
        (
            max(corner.x for corner in corners),
            max(corner.y for corner in corners),
            max(corner.z for corner in corners),
        )
    )
    return (minimum + maximum) * 0.5


def _resolve_bounds_center(assets: Any, aliases: Sequence[str]) -> tuple[Any, str] | None:
    normalized_aliases = {_normalized_name(alias) for alias in aliases}
    found = _walk_asset_value(assets, normalized_aliases)
    if found:
        center = _renderable_bounds_center(found[0])
        if center is not None:
            return center, found[1]

    for obj in bpy.data.objects:
        if _normalized_name(obj.name) in normalized_aliases:
            center = _renderable_bounds_center(obj)
            if center is not None:
                return center, obj.name
    return None


def _resolve_anchor(assets: Any, beat: NarrativeBeat) -> tuple[Any, str]:
    aliases = {_normalized_name(alias) for alias in beat.asset_aliases}
    found = _walk_asset_value(assets, aliases)
    if found:
        location = _world_location(found[0])
        if location is not None:
            return location, found[1]

    for obj in bpy.data.objects:
        if _normalized_name(obj.name) in aliases:
            return obj.matrix_world.translation.copy(), obj.name

    return _authoring_to_film(beat.fallback_target), "fallback"


def _rail_limits(assets: Any) -> tuple[float, float]:
    start, end = -10.0, 145.0
    parameters = assets.get("parameters") if isinstance(assets, Mapping) else None
    if parameters is not None:
        start = float(getattr(parameters, "rail_start_y", start))
        end = float(getattr(parameters, "rail_end_y", end))
    if not math.isfinite(start) or not math.isfinite(end) or end <= start:
        raise ValueError("assets.parameters must provide valid authoring +Y rail limits")
    return start, end


def _parameter_value(assets: Any, name: str, default: float) -> float:
    parameters = assets.get("parameters") if isinstance(assets, Mapping) else None
    value = float(getattr(parameters, name, default)) if parameters is not None else float(default)
    if not math.isfinite(value):
        raise ValueError(f"assets.parameters.{name} must be finite")
    return value


def _scaled_seconds(seconds: float, duration: float) -> float:
    return seconds * duration / BASE_DURATION


def _frame_at(seconds: float, fps: int, frame_end: int) -> int:
    return min(frame_end, 1 + int(round(seconds * fps)))


def _c1_progress_slopes(
    frames: Sequence[int], values: Sequence[float], speed_scales: Sequence[float]
) -> list[float]:
    if not (len(frames) == len(values) == len(speed_scales)) or len(frames) < 2:
        raise ValueError("Camera progress frames, values, and speed scales must align")
    if any(following <= current for current, following in zip(frames, frames[1:])):
        raise ValueError("Camera progress frames must increase strictly")
    secants = [
        (values[index + 1] - values[index]) / (frames[index + 1] - frames[index])
        for index in range(len(values) - 1)
    ]
    if not all(secant > 0.0 and math.isfinite(secant) for secant in secants):
        raise ValueError("Camera progress values must increase strictly before the terminal hold")
    if not all(scale > 0.0 and math.isfinite(scale) for scale in speed_scales[:-1]):
        raise ValueError("Moving camera waypoints require finite, positive speed scales")
    if not math.isfinite(speed_scales[-1]) or not math.isclose(speed_scales[-1], 0.0):
        raise ValueError("The terminal camera waypoint must arrive with zero speed")
    slopes = [secants[0] * speed_scales[0]]
    for index in range(1, len(values) - 1):
        slopes.append(min(secants[index - 1], secants[index]) * speed_scales[index])
    slopes.append(secants[-1] * speed_scales[-1])
    # Keep every Hermite interval monotone. This prevents a locally negative
    # speed even when adjacent narrative beats have very different pacing.
    for index, secant in enumerate(secants):
        alpha = slopes[index] / secant
        beta = slopes[index + 1] / secant
        magnitude = alpha * alpha + beta * beta
        if magnitude > 9.0:
            scale = 3.0 / math.sqrt(magnitude)
            slopes[index] = scale * alpha * secant
            slopes[index + 1] = scale * beta * secant
    if not all(slope > 0.0 and math.isfinite(slope) for slope in slopes[:-1]):
        raise ValueError("Camera progress must stay finite and positive while moving")
    if not math.isclose(slopes[-1], 0.0, abs_tol=1.0e-12):
        raise ValueError("Camera progress must ease to rest at the terminal waypoint")
    return slopes


def _finite_slopes(frames: Sequence[int], values: Sequence[float]) -> list[float]:
    if len(frames) == 1:
        return [0.0]
    slopes = [(values[1] - values[0]) / (frames[1] - frames[0])]
    for index in range(1, len(values) - 1):
        slopes.append((values[index + 1] - values[index - 1]) / (frames[index + 1] - frames[index - 1]))
    slopes.append((values[-1] - values[-2]) / (frames[-1] - frames[-2]))
    return slopes


def _add_hermite_keys(fcurve: Any, keys: Sequence[tuple[int, float, float]]) -> None:
    ordered = sorted(keys, key=lambda item: item[0])
    fcurve.keyframe_points.add(len(ordered))
    for index, (frame, value, slope) in enumerate(ordered):
        point = fcurve.keyframe_points[index]
        point.co = (float(frame), float(value))
        point.interpolation = "BEZIER"
        point.handle_left_type = "FREE"
        point.handle_right_type = "FREE"

        left_dt = frame - ordered[index - 1][0] if index else ordered[1][0] - frame
        right_dt = ordered[index + 1][0] - frame if index + 1 < len(ordered) else frame - ordered[index - 1][0]
        point.handle_left = (frame - left_dt / 3.0, value - slope * left_dt / 3.0)
        point.handle_right = (frame + right_dt / 3.0, value + slope * right_dt / 3.0)
    fcurve.extrapolation = "CONSTANT"
    fcurve.update()


def _create_action_curves(
    owner: Any,
    action_name: str,
    channels: Sequence[tuple[str, int, Sequence[tuple[int, float, float]]]],
) -> Any:
    action = bpy.data.actions.new(action_name)

    if hasattr(action, "slots") and hasattr(action, "layers"):
        slot = action.slots.new(owner.id_type, owner.name)
        layer = action.layers.new("Cinematography")
        strip = layer.strips.new(type="KEYFRAME")
        channelbag = strip.channelbag(slot, ensure=True)
        for data_path, index, keys in channels:
            fcurve = channelbag.fcurves.new(data_path=data_path, index=index)
            _add_hermite_keys(fcurve, keys)
        animation_data = owner.animation_data_create()
        animation_data.action = action
        animation_data.action_slot = slot
        return action

    animation_data = owner.animation_data_create()
    animation_data.action = action
    for data_path, index, keys in channels:
        fcurve = action.fcurves.new(data_path=data_path, index=index, action_group="Cinematography")
        _add_hermite_keys(fcurve, keys)
    return action


def _append_action_curves(
    owner: Any,
    action: Any,
    channels: Sequence[tuple[str, int, Sequence[tuple[int, float, float]]]],
) -> None:
    if hasattr(action, "slots") and hasattr(action, "layers"):
        animation_data = owner.animation_data
        slot = animation_data.action_slot if animation_data is not None else None
        if slot is None or not action.layers or not action.layers[0].strips:
            raise RuntimeError(f"Cannot append cinematography channels to {action.name}")
        strip = action.layers[0].strips[0]
        channelbag = strip.channelbag(slot, ensure=True)
        for data_path, index, keys in channels:
            fcurve = channelbag.fcurves.new(data_path=data_path, index=index)
            _add_hermite_keys(fcurve, keys)
        return

    for data_path, index, keys in channels:
        fcurve = action.fcurves.new(data_path=data_path, index=index, action_group="Cinematography")
        _add_hermite_keys(fcurve, keys)


def _remove_previous_build() -> Any:
    exact_objects = (
        "CIN_Camera",
        "CIN_CameraPath",
        "CIN_LookAt",
        "CIN_CorridorGuide",
        "CIN_TimeControl",
    )
    for name in exact_objects:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)

    for datablocks, name in (
        (bpy.data.cameras, "CIN_CameraData"),
        (bpy.data.curves, "CIN_CameraPathData"),
    ):
        datablock = datablocks.get(name)
        if datablock is not None and datablock.users == 0:
            datablocks.remove(datablock)

    for action in list(bpy.data.actions):
        if action.name.startswith("CIN_") and action.users == 0:
            bpy.data.actions.remove(action)

    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(collection)
    elif collection.name not in {child.name for child in bpy.context.scene.collection.children}:
        bpy.context.scene.collection.children.link(collection)
    return collection


def _monotone_film_z_slopes(coordinates: Sequence[Any]) -> list[float]:
    values = [float(coordinate[2]) for coordinate in coordinates]
    deltas = [following - current for current, following in zip(values, values[1:])]
    if not all(delta < -1.0e-6 for delta in deltas):
        raise ValueError("Camera waypoints must advance strictly along film -Z")

    slopes = [deltas[0]]
    for previous, following in zip(deltas, deltas[1:]):
        slopes.append(2.0 * previous * following / (previous + following))
    slopes.append(deltas[-1])
    return slopes


def _path_tangents(coordinates: Sequence[Any]) -> list[Any]:
    film_z_slopes = _monotone_film_z_slopes(coordinates)
    tangents = []
    for index in range(len(coordinates)):
        if index == 0:
            tangent = coordinates[1] - coordinates[0]
        elif index == len(coordinates) - 1:
            tangent = coordinates[-1] - coordinates[-2]
        else:
            tangent = (coordinates[index + 1] - coordinates[index - 1]) * 0.5
        tangent[2] = film_z_slopes[index]
        tangents.append(tangent)
    return tangents


def _bezier_point(p0: Any, p1: Any, p2: Any, p3: Any, factor: float) -> Any:
    inverse = 1.0 - factor
    return (
        p0 * (inverse**3)
        + p1 * (3.0 * inverse * inverse * factor)
        + p2 * (3.0 * inverse * factor * factor)
        + p3 * (factor**3)
    )


def _path_progress_values(coordinates: Sequence[Any], samples_per_segment: int = 128) -> list[float]:
    tangents = _path_tangents(coordinates)
    cumulative = [0.0]
    total = 0.0
    for index in range(len(coordinates) - 1):
        p0 = coordinates[index]
        p1 = p0 + tangents[index] / 3.0
        p3 = coordinates[index + 1]
        p2 = p3 - tangents[index + 1] / 3.0
        previous = p0
        segment_length = 0.0
        for sample in range(1, samples_per_segment + 1):
            current = _bezier_point(p0, p1, p2, p3, sample / samples_per_segment)
            segment_length += (current - previous).length
            previous = current
        total += segment_length
        cumulative.append(total)
    if total <= 0.0 or not math.isfinite(total):
        raise ValueError("Camera path must have a finite, non-zero length")
    return [value / total for value in cumulative]


def _assert_monotone_film_path(coordinates: Sequence[Any], samples_per_segment: int = 128) -> None:
    tangents = _path_tangents(coordinates)
    previous_z = float(coordinates[0][2])
    for index in range(len(coordinates) - 1):
        p0 = coordinates[index]
        p1 = p0 + tangents[index] / 3.0
        p3 = coordinates[index + 1]
        p2 = p3 - tangents[index + 1] / 3.0
        for sample in range(1, samples_per_segment + 1):
            current_z = float(
                _bezier_point(p0, p1, p2, p3, sample / samples_per_segment)[2]
            )
            if current_z >= previous_z - 1.0e-9:
                raise ValueError("Bezier camera path reverses or stalls along film -Z")
            previous_z = current_z


def _build_bezier_path(collection: Any, coordinates: Sequence[Any]) -> Any:
    curve_data = bpy.data.curves.new("CIN_CameraPathData", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 64
    curve_data.render_resolution_u = 128
    curve_data.twist_smooth = 16

    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(coordinates) - 1)
    tangents = _path_tangents(coordinates)
    for index, coordinate in enumerate(coordinates):
        point = spline.bezier_points[index]
        point.co = coordinate
        point.handle_left_type = "FREE"
        point.handle_right_type = "FREE"
        point.handle_left = coordinate - tangents[index] / 3.0
        point.handle_right = coordinate + tangents[index] / 3.0

    path = bpy.data.objects.new("CIN_CameraPath", curve_data)
    path.hide_render = True
    path.display_type = "WIRE"
    path["continuity"] = "C1 spatial Bezier"
    collection.objects.link(path)
    return path


def _smootherstep(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return value * value * value * (value * (value * 6.0 - 15.0) + 10.0)


def _smootherstep_derivative(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return 30.0 * value * value * (value - 1.0) * (value - 1.0)


def _window_scale_and_derivative(seconds: float, window: BulletWindow) -> tuple[float, float]:
    if seconds <= window.start_s or seconds >= window.end_s:
        return 1.0, 0.0
    if seconds < window.start_s + window.ramp_s:
        phase = (seconds - window.start_s) / window.ramp_s
        blend = _smootherstep(phase)
        derivative = _smootherstep_derivative(phase) / window.ramp_s
        return 1.0 + (window.minimum_scale - 1.0) * blend, (window.minimum_scale - 1.0) * derivative
    if seconds > window.end_s - window.ramp_s:
        phase = (seconds - (window.end_s - window.ramp_s)) / window.ramp_s
        blend = _smootherstep(phase)
        derivative = _smootherstep_derivative(phase) / window.ramp_s
        return window.minimum_scale + (1.0 - window.minimum_scale) * blend, (1.0 - window.minimum_scale) * derivative
    return window.minimum_scale, 0.0


def _visual_state(seconds: float, windows: Sequence[BulletWindow], base_fps: int) -> tuple[float, float, float]:
    selected_scale = 1.0
    selected_derivative = 0.0
    capture_hint = float(base_fps)
    for window in windows:
        scale, derivative = _window_scale_and_derivative(seconds, window)
        if scale < selected_scale:
            selected_scale = scale
            selected_derivative = derivative
        if scale < 1.0:
            weight = (1.0 - scale) / (1.0 - window.minimum_scale)
            capture_hint = max(capture_hint, base_fps + (window.capture_fps - base_fps) * weight)
    return selected_scale, selected_derivative, capture_hint


def _build_visual_clock(
    collection: Any,
    fps: int,
    frame_end: int,
    windows: Sequence[BulletWindow],
) -> Any:
    control = bpy.data.objects.new("CIN_TimeControl", None)
    control.empty_display_type = "PLAIN_AXES"
    control.empty_display_size = 0.35
    control.hide_render = True
    collection.objects.link(control)

    control["visual_time_scale"] = 1.0
    control["visual_time_seconds"] = 0.0
    control["capture_fps_hint"] = float(fps)
    control["camera_clock_is_independent"] = True
    control["usage"] = "Drive scene motion from visual_time_seconds; never remap the camera action."

    frames = list(range(1, frame_end + 1))
    scales: list[float] = []
    scale_slopes: list[float] = []
    capture_values: list[float] = []
    visual_times = [0.0]

    for frame in frames:
        seconds = (frame - 1) / fps
        scale, derivative_per_second, capture_hint = _visual_state(seconds, windows, fps)
        scales.append(scale)
        scale_slopes.append(derivative_per_second / fps)
        capture_values.append(capture_hint)
        if frame > 1:
            visual_times.append(visual_times[-1] + (scales[-2] + scale) * 0.5 / fps)

    capture_slopes = _finite_slopes(frames, capture_values)
    channels = (
        (
            '["visual_time_scale"]',
            0,
            [(frame, scales[index], scale_slopes[index]) for index, frame in enumerate(frames)],
        ),
        (
            '["visual_time_seconds"]',
            0,
            [(frame, visual_times[index], scales[index] / fps) for index, frame in enumerate(frames)],
        ),
        (
            '["capture_fps_hint"]',
            0,
            [(frame, capture_values[index], capture_slopes[index]) for index, frame in enumerate(frames)],
        ),
    )
    _create_action_curves(control, "CIN_TimeControlAction", channels)
    return control


def _dedupe_vector_keys(keys: Sequence[tuple[int, Any]]) -> list[tuple[int, Any]]:
    deduped: dict[int, Any] = {}
    for frame, value in keys:
        deduped[frame] = value.copy()
    return sorted(deduped.items(), key=lambda item: item[0])


def _film_look_quaternion(camera_position: Any, target_position: Any) -> Any:
    forward = target_position - camera_position
    if forward.length <= 1.0e-6:
        raise ValueError("Camera and look-at target cannot occupy the same position")
    forward.normalize()

    film_up = Vector((0.0, 1.0, 0.0))
    projected_up = film_up - forward * film_up.dot(forward)
    if projected_up.length <= 1.0e-6:
        fallback_up = Vector((0.0, 0.0, 1.0))
        projected_up = fallback_up - forward * fallback_up.dot(forward)
    projected_up.normalize()

    right = forward.cross(projected_up).normalized()
    corrected_up = right.cross(forward).normalized()
    backward = -forward
    rotation = Matrix((right, corrected_up, backward)).transposed()
    return rotation.to_quaternion().normalized()


def _smooth_scalar_keyframes(seconds: float, keys: Sequence[tuple[float, float]]) -> float:
    """Interpolate authored scalar keys with zero velocity at each control point."""

    if not keys:
        return 0.0
    if seconds <= keys[0][0]:
        return float(keys[0][1])
    for (start_s, start_value), (end_s, end_value) in zip(keys, keys[1:]):
        if seconds <= end_s:
            span = max(end_s - start_s, 1.0e-6)
            phase = _smootherstep((seconds - start_s) / span)
            return float(start_value + (end_value - start_value) * phase)
    return float(keys[-1][1])


def _aligned_quaternion(reference: Any, value: Any) -> Any:
    aligned = value.copy()
    if reference.dot(aligned) < 0.0:
        aligned.negate()
    return aligned


def _quaternion_step_vector(start: Any, end: Any) -> Any:
    delta = start.rotation_difference(_aligned_quaternion(start, end))
    if delta.w < 0.0:
        delta.negate()
    angle = min(math.pi, max(0.0, float(delta.angle)))
    if angle <= 1.0e-10:
        return Vector((0.0, 0.0, 0.0))
    return delta.axis.normalized() * angle


def _clamp_vector_length(value: Any, maximum: float) -> Any:
    if value.length <= maximum or value.length <= 1.0e-12:
        return value
    return value.normalized() * maximum


def _quaternion_from_step(value: Any) -> Any:
    if value.length <= 1.0e-10:
        return Quaternion((1.0, 0.0, 0.0, 0.0))
    return Quaternion(value.normalized(), value.length)


def _stabilize_quaternions(
    quaternions: Sequence[Any],
    hold_from_frame: int | None,
) -> list[Any]:
    """Low-pass authored aim and cap per-frame angular acceleration."""

    if len(quaternions) < 2:
        return [value.copy() for value in quaternions]
    hold_index = (
        min(len(quaternions) - 1, max(0, hold_from_frame - 1))
        if hold_from_frame is not None
        else len(quaternions)
    )
    smoothed = [value.copy() for value in quaternions]
    for _ in range(ORIENTATION_SMOOTHING_PASSES):
        updated = [value.copy() for value in smoothed]
        for index in range(1, min(hold_index, len(smoothed) - 1)):
            following = _aligned_quaternion(smoothed[index - 1], smoothed[index + 1])
            midpoint = smoothed[index - 1].slerp(following, 0.5)
            midpoint = _aligned_quaternion(smoothed[index], midpoint)
            updated[index] = smoothed[index].slerp(midpoint, 0.55).normalized()
        smoothed = updated

    # Quaternion component curves are normalized again by Blender evaluation.
    # Keep a small margin so evaluated world rotations remain inside the gate.
    max_step = math.radians(
        MAX_ANGULAR_STEP_DEGREES * ORIENTATION_LIMIT_SAFETY_FACTOR
    )
    max_acceleration = math.radians(
        ORIENTATION_BAKE_ACCELERATION_DEGREES * ORIENTATION_LIMIT_SAFETY_FACTOR
    )
    stabilized = [smoothed[0].copy()]
    previous_step = Vector((0.0, 0.0, 0.0))
    for target in smoothed[1:]:
        desired_step = _clamp_vector_length(
            _quaternion_step_vector(stabilized[-1], target), max_step
        )
        acceleration = _clamp_vector_length(
            desired_step - previous_step, max_acceleration
        )
        step = _clamp_vector_length(previous_step + acceleration, max_step)
        value = (stabilized[-1] @ _quaternion_from_step(step)).normalized()
        value = _aligned_quaternion(stabilized[-1], value)
        stabilized.append(value)
        previous_step = step

    if hold_from_frame is not None:
        locked = stabilized[hold_index].copy()
        for index in range(hold_index, len(stabilized)):
            stabilized[index] = locked.copy()
    return stabilized


def _bake_camera_orientation(
    scene: Any,
    camera: Any,
    look_at: Any,
    camera_action: Any,
    frame_end: int,
    fps: int,
    duration: float,
    hold_from_frame: int | None = None,
) -> None:
    frames = list(range(1, frame_end + 1))
    quaternions = []
    previous = None
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        quaternion = _film_look_quaternion(
            camera.matrix_world.translation.copy(),
            look_at.matrix_world.translation.copy(),
        )
        seconds = (frame - 1) / float(fps)
        authored_seconds = seconds * BASE_DURATION / float(duration)
        bank_degrees = _smooth_scalar_keyframes(authored_seconds, ROLL_KEYFRAMES)
        quaternion = quaternion @ Quaternion(
            (0.0, 0.0, 1.0), math.radians(bank_degrees)
        )
        if previous is not None and previous.dot(quaternion) < 0.0:
            quaternion.negate()
        quaternions.append(quaternion)
        previous = quaternion

    quaternions = _stabilize_quaternions(quaternions, hold_from_frame)
    channels = []
    for component in range(4):
        values = [float(quaternion[component]) for quaternion in quaternions]
        slopes = _finite_slopes(frames, values)
        if hold_from_frame is not None:
            slopes = [
                0.0 if frame >= hold_from_frame else slope
                for frame, slope in zip(frames, slopes)
            ]
        channels.append(
            (
                "rotation_quaternion",
                component,
                [
                    (frame, values[index], slopes[index])
                    for index, frame in enumerate(frames)
                ],
            )
        )
    _append_action_curves(camera, camera_action, channels)


def _create_markers(scene: Any, beats: Sequence[NarrativeBeat], fps: int, duration: float, frame_end: int) -> None:
    for marker in list(scene.timeline_markers):
        if marker.name.startswith("CIN_"):
            scene.timeline_markers.remove(marker)
    for index, beat in enumerate(beats, start=1):
        focus = _scaled_seconds(beat.focus_s, duration)
        scene.timeline_markers.new(
            f"CIN_{index:02d}_{beat.slug.upper()}",
            frame=_frame_at(focus, fps, frame_end),
        )


def build_cinematography(assets: Any, fps: int = 24, duration: float = 38) -> Any:
    """Build the continuous 8-beat camera move and return the camera object.

    ``assets`` may be a mapping, namespace, Blender collection, or nested set of
    those values. Named anchors are preferred; canonical SUM coordinates are
    used when a matching anchor is absent.
    """

    _require_blender()
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        raise ValueError("fps must be a positive integer")
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be a positive finite number")

    frame_end = int(round(float(duration) * fps))
    if frame_end < len(NARRATIVE_BEATS) * 2:
        raise ValueError("duration is too short for eight continuous narrative beats")

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = frame_end
    scene.frame_preview_start = 1
    scene.frame_preview_end = frame_end
    scene.render.fps = fps
    scene.render.fps_base = 1.0

    collection = _remove_previous_build()
    bpy.context.view_layer.update()
    rail_start_y, rail_end_y = _rail_limits(assets)
    final_travel = _parameter_value(assets, "final_anchor_travel", rail_end_y - 7.0)
    if not rail_start_y < final_travel < rail_end_y:
        raise ValueError("final_anchor_travel must sit within the guide rail limits")
    targets: list[Any] = []
    anchor_sources: list[str] = []
    camera_positions: list[Any] = []
    scaled_beats: list[dict[str, Any]] = []

    for beat in NARRATIVE_BEATS:
        target, source = _resolve_anchor(assets, beat)
        if beat.slug == "handoff":
            robot_bounds = _resolve_bounds_center(
                assets,
                ("robot_arm_6axis", "SUM_ASSET_Robot_6Axis"),
            )
            if robot_bounds is not None:
                chain_center, chain_source = robot_bounds
                target = chain_center * 0.70 + target * 0.30
                source = f"{chain_source}+tcp_bias"
        elif beat.slug == "close":
            final_subject = _resolve_bounds_center(
                assets,
                (
                    "final_inspection_portal",
                    "final_precision_inspection_portal",
                    "SUM_ASSET_FinalPrecisionInspectionPortal",
                ),
            )
            if final_subject is not None:
                target, final_source = final_subject
                target += Vector((0.0, -0.45, 0.0))
                source = f"{final_source}+lowered_bounds_center"
            elif source == "fallback":
                target = _authoring_to_film((0.0, final_travel, 2.20))
                source = "parameters.final_anchor_travel"
            else:
                target = Vector((float(target[0]), max(2.20, float(target[1])), float(target[2])))
                source = f"{source}+elevated_end_frame"
        fallback_target = Vector(beat.fallback_target)
        authoring_offset = Vector(beat.fallback_camera) - fallback_target
        camera_offset = _authoring_to_film(authoring_offset)
        targets.append(target)
        anchor_sources.append(source)
        camera_positions.append(target + camera_offset)
        scaled_beats.append(
            {
                "beat": beat,
                "start_s": _scaled_seconds(beat.start_s, duration),
                "end_s": _scaled_seconds(beat.end_s, duration),
                "focus_s": _scaled_seconds(beat.focus_s, duration),
                "hold_s": _scaled_seconds(beat.focus_hold_s, duration),
            }
        )

    if not all(
        following[2] < current[2] - 1.0e-6
        for current, following in zip(targets, targets[1:])
    ):
        raise ValueError(
            "Narrative anchors must progress bearing -> robot -> grinding -> screens -> final along film -Z"
        )

    opening_start = _authoring_to_film((0.0, -4.0, 2.25))
    grinding_approach_camera = _authoring_to_film((2.40, 21.80, 1.92))
    grinding_pullback_camera = _authoring_to_film((-1.20, 23.85, 2.00))
    grinding_clear_camera = _authoring_to_film((-0.40, 30.00, 1.90))
    corridor_camera = _authoring_to_film((0.0, 34.0, 1.72))
    corridor_look = _authoring_to_film((0.0, 45.0, 1.55))
    closing_end = _authoring_to_film((0.0, final_travel - 4.0, 1.65))
    closing_look = targets[-1].copy()
    path_coordinates = [
        opening_start,
        *camera_positions[:2],
        grinding_approach_camera,
        camera_positions[2],
        grinding_pullback_camera,
        grinding_clear_camera,
        corridor_camera,
        *camera_positions[3:],
        closing_end,
    ]
    _assert_monotone_film_path(path_coordinates)
    path = _build_bezier_path(collection, path_coordinates)

    look_at = bpy.data.objects.new("CIN_LookAt", None)
    look_at.empty_display_type = "SPHERE"
    look_at.empty_display_size = 0.22
    look_at.hide_render = True
    collection.objects.link(look_at)

    corridor_guide = bpy.data.objects.new("CIN_CorridorGuide", None)
    corridor_guide.empty_display_type = "PLAIN_AXES"
    corridor_guide.empty_display_size = 0.35
    corridor_guide.location = corridor_look
    corridor_guide.hide_render = True
    corridor_guide["purpose"] = "Stable dual-rail corridor look-at guide"
    collection.objects.link(corridor_guide)

    camera_data = bpy.data.cameras.new("CIN_CameraData")
    camera_data.type = "PERSP"
    camera_data.lens = 24.0
    camera_data.sensor_width = 36.0
    camera_data.clip_start = 0.02
    camera_data.clip_end = 260.0
    camera_data.dof.use_dof = False
    camera_data.dof.focus_object = None
    camera_data.dof.aperture_fstop = 4.0
    camera_data.dof.aperture_blades = 9
    if hasattr(camera_data, "show_safe_areas"):
        camera_data.show_safe_areas = True
    camera_data["mobile_center_safe_width"] = 0.316
    camera_data["mobile_vertical_safe_height"] = 0.80

    camera = bpy.data.objects.new("CIN_Camera", camera_data)
    camera.rotation_mode = "QUATERNION"
    collection.objects.link(camera)
    scene.camera = camera

    follow = camera.constraints.new("FOLLOW_PATH")
    follow.name = "CIN_FollowPath"
    follow.target = path
    follow.use_fixed_location = True
    follow.use_curve_follow = False
    follow.offset_factor = 0.0

    focus_seconds = [item["focus_s"] for item in scaled_beats]
    grinding_approach_seconds = _scaled_seconds(GRINDING_APPROACH_SECONDS, duration)
    grinding_pullback_seconds = _scaled_seconds(GRINDING_PULLBACK_SECONDS, duration)
    grinding_clear_seconds = _scaled_seconds(GRINDING_CLEAR_SECONDS, duration)
    corridor_seconds = _scaled_seconds(CORRIDOR_WAYPOINT_SECONDS, duration)
    terminal_settle_seconds = _scaled_seconds(TERMINAL_SETTLE_SECONDS, duration)
    path_times = [
        0.0,
        *focus_seconds[:2],
        grinding_approach_seconds,
        focus_seconds[2],
        grinding_pullback_seconds,
        grinding_clear_seconds,
        corridor_seconds,
        *focus_seconds[3:],
        terminal_settle_seconds,
    ]
    path_frames = [_frame_at(value, fps, frame_end) for value in path_times]
    if len(set(path_frames)) != len(path_frames):
        raise ValueError("fps and duration collapse two camera waypoints onto the same frame")
    terminal_settle_frame = path_frames[-1]
    if terminal_settle_frame >= frame_end:
        raise ValueError("fps and duration must leave frames for the terminal camera hold")
    # offset_factor is measured along path length, so match each timed waypoint
    # to the cumulative arc length of its Bezier control point.
    progress_values = _path_progress_values(path_coordinates)
    speed_scales = [
        1.0,
        *[beat.speed_scale for beat in NARRATIVE_BEATS[:2]],
        0.72,
        NARRATIVE_BEATS[2].speed_scale,
        0.30,
        0.45,
        0.62,
        *[beat.speed_scale for beat in NARRATIVE_BEATS[3:]],
        0.0,
    ]
    progress_slopes = _c1_progress_slopes(path_frames, progress_values, speed_scales)
    progress_keys = [
        (frame, progress_values[index], progress_slopes[index])
        for index, frame in enumerate(path_frames)
    ]
    progress_keys.append((frame_end, progress_values[-1], 0.0))
    camera_action = _create_action_curves(
        camera,
        "CIN_CameraAction",
        ((f'constraints["{follow.name}"].offset_factor', 0, progress_keys),),
    )

    lens_values = [
        24.0,
        *[beat.lens_mm for beat in NARRATIVE_BEATS[:2]],
        48.0,
        NARRATIVE_BEATS[2].lens_mm,
        72.0,
        50.0,
        36.0,
        *[beat.lens_mm for beat in NARRATIVE_BEATS[3:]],
        46.0,
    ]
    lens_keys = [(frame, lens_values[index], 0.0) for index, frame in enumerate(path_frames)]
    lens_keys.append((frame_end, lens_values[-1], 0.0))
    aperture_values = [
        5.6,
        4.8,
        5.0,
        5.6,
        8.0,
        8.0,
        6.3,
        5.6,
        4.5,
        4.5,
        4.5,
        4.5,
        5.6,
        5.6,
    ]
    aperture_keys = [
        (frame, aperture_values[index], 0.0)
        for index, frame in enumerate(path_frames)
    ]
    aperture_keys.append((frame_end, aperture_values[-1], 0.0))
    _create_action_curves(
        camera_data,
        "CIN_CameraDataAction",
        (
            ("lens", 0, lens_keys),
            ("dof.aperture_fstop", 0, aperture_keys),
        ),
    )

    target_keys: list[tuple[int, Any]] = [(1, targets[0])]
    for index, item in enumerate(scaled_beats):
        half_hold = item["hold_s"] * 0.5
        enter = max(item["start_s"], item["focus_s"] - half_hold)
        leave = min(item["end_s"], item["focus_s"] + half_hold)
        target_keys.append((_frame_at(enter, fps, frame_end), targets[index]))
        target_keys.append((_frame_at(leave, fps, frame_end), targets[index]))
    for seconds, coordinate in AGV_OPENING_LOOKS:
        target_keys.append(
            (
                _frame_at(_scaled_seconds(seconds, duration), fps, frame_end),
                _authoring_to_film(coordinate),
            )
        )
    corridor_guide_start_frame = _frame_at(
        _scaled_seconds(CORRIDOR_GUIDE_START_SECONDS, duration), fps, frame_end
    )
    corridor_guide_end_frame = _frame_at(
        _scaled_seconds(CORRIDOR_GUIDE_END_SECONDS, duration), fps, frame_end
    )
    target_keys.append((corridor_guide_start_frame, corridor_look))
    target_keys.append((corridor_guide_end_frame, corridor_look))
    for seconds, coordinate in GRINDING_TRANSITION_LOOKS:
        target_keys.append(
            (
                _frame_at(_scaled_seconds(seconds, duration), fps, frame_end),
                _authoring_to_film(coordinate),
            )
        )
    for seconds, coordinate in SCREEN_TRANSITION_LOOKS:
        target_keys.append(
            (
                _frame_at(_scaled_seconds(seconds, duration), fps, frame_end),
                _authoring_to_film(coordinate),
            )
        )
    target_keys.append((terminal_settle_frame, closing_look))
    target_keys.append((frame_end, closing_look))
    target_keys = _dedupe_vector_keys(target_keys)
    target_channels = []
    for axis in range(3):
        target_channels.append(
            (
                "location",
                axis,
                [(frame, float(value[axis]), 0.0) for frame, value in target_keys],
            )
        )
    _create_action_curves(look_at, "CIN_LookAtAction", target_channels)
    _bake_camera_orientation(
        scene,
        camera,
        look_at,
        camera_action,
        frame_end,
        fps,
        float(duration),
        hold_from_frame=terminal_settle_frame,
    )

    scale_factor = float(duration) / BASE_DURATION
    scaled_windows = tuple(
        BulletWindow(
            window.slug,
            window.start_s * scale_factor,
            window.end_s * scale_factor,
            window.ramp_s * scale_factor,
            window.minimum_scale,
            max(fps, int(round(window.capture_fps * fps / 24.0))),
        )
        for window in BULLET_WINDOWS
    )
    time_control = _build_visual_clock(collection, fps, frame_end, scaled_windows)

    _create_markers(scene, NARRATIVE_BEATS, fps, float(duration), frame_end)

    beat_manifest = []
    for index, item in enumerate(scaled_beats):
        beat = item["beat"]
        start_frame = _frame_at(item["start_s"], fps, frame_end)
        next_frame = _frame_at(item["end_s"], fps, frame_end)
        beat_manifest.append(
            {
                "index": index + 1,
                "id": beat.slug,
                "label": beat.label,
                "start_seconds": round(item["start_s"], 4),
                "end_seconds": round(item["end_s"], 4),
                "frame_start": start_frame,
                "frame_end": frame_end if index == len(scaled_beats) - 1 else next_frame - 1,
                "focus_frame": _frame_at(item["focus_s"], fps, frame_end),
                "lens_mm": beat.lens_mm,
                "anchor_source": anchor_sources[index],
                "look_at": [round(float(component), 4) for component in targets[index]],
            }
        )

    storyboard_focus_frames = [beat["focus_frame"] for beat in beat_manifest]

    manifest = {
        "version": 1,
        "fps": fps,
        "duration_seconds": float(duration),
        "frame_start": 1,
        "frame_end": frame_end,
        "one_shot": True,
        "opening": {
            "lens_mm": 24.0,
            "rail_takeover_frame": path_frames[1],
            "starts_with_nonzero_velocity": True,
            "agv_escort_end_frame": _frame_at(
                _scaled_seconds(AGV_OPENING_END_SECONDS, duration), fps, frame_end
            ),
            "look_policy": "agv_escort_then_bearing_handoff",
        },
        "camera": {
            "object": camera.name,
            "path": path.name,
            "look_at": look_at.name,
            "path_continuity": "C1",
            "progress_continuity": "C1",
            "offset_parameterization": "sampled_arc_length",
            "moving_interval_speed_positive": True,
            "speed_never_zero": False,
            "film_z_monotone": True,
            "film_z_strict_until_terminal_settle": True,
            "orientation": "stabilized_per_frame_world_quaternion_with_restrained_bank",
            "look_at_exact_at_integer_frames": False,
            "look_at_policy": "smoothed_aim_preserves_authored_target_holds",
            "horizon_up_axis": "+Y",
            "roll_limit_degrees": 1.25,
            "orientation_smoothing_passes": ORIENTATION_SMOOTHING_PASSES,
            "max_angular_step_degrees_per_frame": MAX_ANGULAR_STEP_DEGREES,
            "max_angular_acceleration_degrees_per_frame2": MAX_ANGULAR_ACCEL_DEGREES,
            "roll_keyframes_seconds_degrees": [
                [seconds, degrees] for seconds, degrees in ROLL_KEYFRAMES
            ],
            "corridor_guide": corridor_guide.name,
            "grinding_pullback_frame": path_frames[5],
            "grinding_clear_frame": path_frames[6],
            "corridor_waypoint_frame": path_frames[7],
            "corridor_guide_hold_frames": [
                corridor_guide_start_frame,
                corridor_guide_end_frame,
            ],
            "terminal_settle_frame": terminal_settle_frame,
            "terminal_hold_frame_window": [terminal_settle_frame, frame_end],
            "terminal_hold_seconds": round(
                (frame_end - terminal_settle_frame) / float(fps), 4
            ),
            "terminal_pose_locked": True,
        },
        "composition": {
            "leading_lines": "dual_rail",
            "authoring_travel_axis": "+Y",
            "travel_axis": "-Z",
            "rail_start_y": rail_start_y,
            "rail_end_y": rail_end_y,
            "final_anchor_travel": final_travel,
            "mobile_center_safe_width": 0.316,
            "mobile_vertical_safe_height": 0.80,
            "felix_zuo_treatment": "low_key_environment_nameplate_only",
        },
        "visual_clock": {
            "object": time_control.name,
            "time_property": "visual_time_seconds",
            "scale_property": "visual_time_scale",
            "capture_hint_property": "capture_fps_hint",
            "camera_clock_is_independent": True,
        },
        "beats": beat_manifest,
        "storyboard_focus_frames": storyboard_focus_frames,
        "bullet_windows": [
            {
                "id": window.slug,
                "start_seconds": round(window.start_s, 4),
                "end_seconds": round(window.end_s, 4),
                "minimum_scale": window.minimum_scale,
                "capture_fps": window.capture_fps,
            }
            for window in scaled_windows
        ],
    }
    scene["cinematography_manifest"] = json.dumps(manifest, separators=(",", ":"), ensure_ascii=True)
    scene["cin_storyboard_frames"] = json.dumps(storyboard_focus_frames, separators=(",", ":"))
    scene["cin_visual_time_object"] = time_control.name
    scene["cin_camera_speed_continuous"] = True
    scene["cin_terminal_settle_frame"] = terminal_settle_frame
    camera["cin_camera_path"] = path.name
    camera["cin_look_at"] = look_at.name
    camera["cin_corridor_guide"] = corridor_guide.name
    camera["cin_orientation"] = (
        "stabilized_per_frame_world_quaternion_with_restrained_bank"
    )
    camera["cin_roll_limit_degrees"] = 1.25
    camera["cin_max_angular_step_degrees"] = MAX_ANGULAR_STEP_DEGREES
    camera["cin_max_angular_acceleration_degrees"] = MAX_ANGULAR_ACCEL_DEGREES
    camera["cin_terminal_hold_frames"] = frame_end - terminal_settle_frame + 1
    camera["cin_time_control"] = time_control.name
    camera["cin_beat_count"] = len(beat_manifest)
    scene.frame_set(1)
    return camera


__all__ = ["BULLET_WINDOWS", "NARRATIVE_BEATS", "build_cinematography"]
