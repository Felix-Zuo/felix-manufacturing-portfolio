"""Continuous mechanical asset animation for the SUM portfolio journey.

The camera owns scene time.  This module bakes eased asset motion directly to
FCurves and never remaps the camera action or the cinematography time control.
Call :func:`animate_assets` after modeling and look development so the generated
grinding sparks and screen emission materials are available.
"""

from __future__ import annotations

import json
import hashlib
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import bpy


__all__ = ["animate_assets"]


_BASE_DURATION = 38.0
_ACTION_PREFIX = "SUM_ANIM_"
_ACTION_TAG = "sum_animation_generated"
_BASE_VALUE_PREFIX = "sum_animation_base_"


@dataclass(frozen=True)
class _SlowWindow:
    slug: str
    start_s: float
    end_s: float
    minimum_scale: float
    ramp_s: float


_BEARING_WINDOW = _SlowWindow("bearing_inspection", 0.25, 2.50, 0.42, 0.34)
_HANDOFF_WINDOW = _SlowWindow("arm_handoff", 6.90, 8.25, 0.34, 0.32)
_GRINDING_WINDOW = _SlowWindow("grinding_contact", 17.58, 19.38, 0.20, 0.22)
_MECHANICAL_WINDOWS = (_BEARING_WINDOW, _HANDOFF_WINDOW, _GRINDING_WINDOW)

_GRINDING_FEED_RETRACT_M = 0.014
_GRINDING_FEED_TIMES = (16.00, 16.40, 17.50, 19.38, 20.05, 20.75)
_GRINDING_SLIDE_NAMES = {
    "SUM_GrindingCell_XSlide_Carriage",
    "SUM_GrindingCell_XSlide_LinearBlocks",
    "SUM_GrindingCell_GrindingSpindle_Housing",
    "SUM_GrindingCell_GrindingSpindle_Shaft",
    "SUM_GrindingCell_GrindingSpindleMount",
    "SUM_GrindingCell_GrindingSpindleCastSupport",
    "SUM_GrindingCell_HighSpeedSpindleMotor",
    "SUM_GrindingCell_SpindleMotorRearCap",
    "SUM_GrindingCell_SpindleBalanceCollar",
    "SUM_GrindingCell_WheelArborNose",
    "SUM_GrindingCell_PrecisionTaperArbor",
    "SUM_GrindingCell_SpindleNoseCollar",
}
_GRINDING_SLIDE_PREFIXES = (
    "SUM_GrindingCell_SpindleCoolingRing_",
    "SUM_GrindingCell_SpindleNoseSealRing_",
)


@dataclass(frozen=True)
class _ClockSamples:
    frames: tuple[int, ...]
    seconds: tuple[float, ...]
    rates: tuple[float, ...]
    visual_seconds: tuple[float, ...]


def _validate_timing(fps: int, duration: float) -> tuple[int, float]:
    if isinstance(fps, bool) or not isinstance(fps, int) or fps <= 0:
        raise ValueError("fps must be a positive integer")
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or duration <= 0.0
    ):
        raise ValueError("duration must be a positive finite number")
    frame_end = int(round(float(duration) * fps))
    if frame_end < 8:
        raise ValueError("duration is too short for continuous asset animation")
    return frame_end, float(duration)


def _smootherstep(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return value * value * value * (value * (value * 6.0 - 15.0) + 10.0)


def _scaled_window(window: _SlowWindow, duration: float) -> _SlowWindow:
    factor = duration / _BASE_DURATION
    return _SlowWindow(
        window.slug,
        window.start_s * factor,
        window.end_s * factor,
        window.minimum_scale,
        window.ramp_s * factor,
    )


def _window_rate(seconds: float, window: _SlowWindow) -> float:
    if seconds <= window.start_s or seconds >= window.end_s:
        return 1.0
    ramp = min(window.ramp_s, (window.end_s - window.start_s) * 0.5)
    if seconds < window.start_s + ramp:
        phase = (seconds - window.start_s) / ramp
        return 1.0 + (window.minimum_scale - 1.0) * _smootherstep(phase)
    if seconds > window.end_s - ramp:
        phase = (seconds - (window.end_s - ramp)) / ramp
        return window.minimum_scale + (1.0 - window.minimum_scale) * _smootherstep(phase)
    return window.minimum_scale


def _clock_samples(
    fps: int,
    frame_end: int,
    duration: float,
    window: _SlowWindow,
) -> _ClockSamples:
    scaled = _scaled_window(window, duration)
    frames = tuple(range(1, frame_end + 1))
    seconds = tuple((frame - 1) / fps for frame in frames)
    rates = tuple(_window_rate(value, scaled) for value in seconds)
    visual_seconds = [0.0]
    for index in range(1, len(frames)):
        dt = seconds[index] - seconds[index - 1]
        visual_seconds.append(
            visual_seconds[-1] + (rates[index - 1] + rates[index]) * 0.5 * dt
        )
    return _ClockSamples(frames, seconds, rates, tuple(visual_seconds))


def _uniform_clock_samples(fps: int, frame_end: int) -> _ClockSamples:
    frames = tuple(range(1, frame_end + 1))
    seconds = tuple((frame - 1) / fps for frame in frames)
    return _ClockSamples(frames, seconds, tuple(1.0 for _ in frames), seconds)


def _frame_at(seconds: float, fps: int, frame_end: int, duration: float) -> int:
    scaled_seconds = seconds * duration / _BASE_DURATION
    return min(frame_end, max(1, 1 + int(round(scaled_seconds * fps))))


def _asset_value(assets: Any, key: str) -> Any | None:
    if isinstance(assets, Mapping):
        return assets.get(key)
    return getattr(assets, key, None)


def _require_object(assets: Any, key: str, fallback_name: str) -> bpy.types.Object:
    value = _asset_value(assets, key)
    if not isinstance(value, bpy.types.Object):
        value = bpy.data.objects.get(fallback_name)
    if not isinstance(value, bpy.types.Object):
        raise ValueError(f"assets is missing required Blender object: {key}")
    return value


def _resolve_robot_joints(assets: Any) -> list[bpy.types.Object]:
    value = _asset_value(assets, "robot_joints")
    joints: list[bpy.types.Object] = []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        joints = [item for item in value if isinstance(item, bpy.types.Object)]
    if len(joints) != 6:
        joints = []
        for index in range(1, 7):
            candidate = _asset_value(assets, f"robot_joint_{index}")
            if not isinstance(candidate, bpy.types.Object):
                candidate = bpy.data.objects.get(f"SUM_Robot_J{index}_Axis")
            if isinstance(candidate, bpy.types.Object):
                joints.append(candidate)
    joints.sort(key=lambda item: int(item.get("joint_index", 99)))
    if len(joints) != 6 or len({joint.as_pointer() for joint in joints}) != 6:
        raise ValueError("assets must provide exactly six distinct robot joint objects")
    return joints


def _nested_named_value(value: Any, keys: set[str], depth: int = 0) -> Any | None:
    if depth > 3:
        return None
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).lower() in keys:
                return nested
        for key in ("lookdev", "assets", "objects", "accents"):
            if key in value:
                found = _nested_named_value(value[key], keys, depth + 1)
                if found is not None:
                    return found
    return None


def _resolve_sparks(assets: Any) -> bpy.types.Object | None:
    value = _nested_named_value(assets, {"sparks", "spark", "lookdev_sparks"})
    if isinstance(value, bpy.types.Object):
        return value
    named = bpy.data.objects.get("LD_Grinding_Sparks")
    if isinstance(named, bpy.types.Object):
        return named
    for obj in bpy.context.scene.objects:
        if obj.get("lookdev_generated") and "spark" in obj.name.lower():
            return obj
    return None


def _safe_action_suffix(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")[:48] or "Data"


def _stored_scalar(owner: Any, key: str, current: float) -> float:
    property_name = f"{_BASE_VALUE_PREFIX}{key}"
    if property_name not in owner:
        owner[property_name] = float(current)
    return float(owner[property_name])


def _stored_vector(owner: Any, key: str, current: Sequence[float]) -> tuple[float, ...]:
    property_name = f"{_BASE_VALUE_PREFIX}{key}"
    if property_name not in owner:
        owner[property_name] = [float(value) for value in current]
    return tuple(float(value) for value in owner[property_name])


def _preserve_base_as_quaternion(obj: bpy.types.Object) -> None:
    property_name = f"{_BASE_VALUE_PREFIX}rotation_quaternion"
    if property_name not in obj:
        if obj.rotation_mode == "QUATERNION":
            quaternion = obj.rotation_quaternion.copy()
        elif obj.rotation_mode == "AXIS_ANGLE":
            quaternion = obj.matrix_basis.to_quaternion()
        else:
            quaternion = obj.rotation_euler.to_quaternion()
        obj[property_name] = [
            quaternion.w,
            quaternion.x,
            quaternion.y,
            quaternion.z,
        ]
        obj["sum_animation_original_rotation_mode"] = obj.rotation_mode
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = tuple(float(value) for value in obj[property_name])


def _finite_slopes(
    frames: Sequence[int], values: Sequence[float], *, close_loop: bool = False
) -> list[float]:
    if len(frames) != len(values) or len(frames) < 2:
        raise ValueError("curve samples require matching frame/value sequences")
    slopes = [(values[1] - values[0]) / (frames[1] - frames[0])]
    for index in range(1, len(values) - 1):
        slopes.append(
            (values[index + 1] - values[index - 1])
            / (frames[index + 1] - frames[index - 1])
        )
    slopes.append((values[-1] - values[-2]) / (frames[-1] - frames[-2]))
    if close_loop and math.isclose(values[0], values[-1], rel_tol=0.0, abs_tol=1.0e-8):
        wrapped = (values[1] - values[-2]) / (
            (frames[1] - frames[0]) + (frames[-1] - frames[-2])
        )
        slopes[0] = wrapped
        slopes[-1] = wrapped
    return slopes


def _sampled_keys(
    frames: Sequence[int], values: Sequence[float], *, close_loop: bool = False
) -> list[tuple[int, float, float]]:
    slopes = _finite_slopes(frames, values, close_loop=close_loop)
    return [
        (int(frame), float(value), float(slope))
        for frame, value, slope in zip(frames, values, slopes)
    ]


def _add_hermite_keys(
    fcurve: Any, keys: Sequence[tuple[int, float, float]]
) -> None:
    ordered_map = {int(frame): (float(value), float(slope)) for frame, value, slope in keys}
    ordered = [(frame, *ordered_map[frame]) for frame in sorted(ordered_map)]
    if len(ordered) < 2:
        raise ValueError("every animated FCurve needs at least two keys")

    fcurve.keyframe_points.add(len(ordered))
    for index, (frame, value, slope) in enumerate(ordered):
        point = fcurve.keyframe_points[index]
        point.co = (float(frame), value)
        point.interpolation = "BEZIER"
        point.handle_left_type = "FREE"
        point.handle_right_type = "FREE"

        left_dt = frame - ordered[index - 1][0] if index else ordered[1][0] - frame
        right_dt = (
            ordered[index + 1][0] - frame
            if index + 1 < len(ordered)
            else frame - ordered[index - 1][0]
        )
        point.handle_left = (frame - left_dt / 3.0, value - slope * left_dt / 3.0)
        point.handle_right = (frame + right_dt / 3.0, value + slope * right_dt / 3.0)
    fcurve.extrapolation = "CONSTANT"
    fcurve.update()


def _action_owner_key(owner: Any) -> str:
    return f"{owner.id_type}:{owner.name}"


def _available_action_name(action_name: str, owner_key: str) -> str:
    digest = hashlib.blake2s(owner_key.encode("utf-8"), digest_size=4).hexdigest()
    candidates = [action_name, f"{action_name}_{digest}"]
    candidates.extend(f"{action_name}_{digest}_{index:02d}" for index in range(2, 100))
    for candidate in candidates:
        existing = bpy.data.actions.get(candidate)
        if existing is None:
            return candidate
        if bool(existing.get(_ACTION_TAG)) and existing.users == 0:
            bpy.data.actions.remove(existing)
            return candidate
    raise RuntimeError(f"No stable action name is available for {owner_key!r}")


def _remove_owned_action(owner: Any, action_name: str, owner_key: str) -> str:
    animation_data = getattr(owner, "animation_data", None)
    active = animation_data.action if animation_data is not None else None
    if active is not None:
        if not bool(active.get(_ACTION_TAG)):
            raise RuntimeError(
                f"Refusing to replace non-SUM action {active.name!r} on {owner.name!r}"
            )
        animation_data.action = None
        if active.users == 0:
            bpy.data.actions.remove(active)

    return _available_action_name(action_name, owner_key)


def _create_action(
    owner: Any,
    action_name: str,
    role: str,
    channels: Sequence[tuple[str, int, Sequence[tuple[int, float, float]]]],
    fps: int,
    duration: float,
    *,
    owner_key: str | None = None,
) -> bpy.types.Action:
    owner_key = owner_key or _action_owner_key(owner)
    action_name = _remove_owned_action(owner, action_name, owner_key)
    action = bpy.data.actions.new(action_name)
    action[_ACTION_TAG] = True
    action["sum_animation_role"] = role
    action["sum_animation_owner"] = owner.name
    action["sum_animation_owner_key"] = owner_key
    action["sum_animation_fps"] = fps
    action["sum_animation_duration"] = duration
    action["sum_animation_interpolation"] = "C1 Hermite Bezier"

    if hasattr(action, "slots") and hasattr(action, "layers"):
        slot = action.slots.new(owner.id_type, owner.name)
        layer = action.layers.new("SUM Asset Animation")
        strip = layer.strips.new(type="KEYFRAME")
        channelbag = strip.channelbag(slot, ensure=True)
        for data_path, index, keys in channels:
            fcurve = channelbag.fcurves.new(data_path=data_path, index=index)
            _add_hermite_keys(fcurve, keys)
        animation_data = owner.animation_data_create()
        animation_data.action = action
        animation_data.action_slot = slot
    else:
        animation_data = owner.animation_data_create()
        animation_data.action = action
        for data_path, index, keys in channels:
            fcurve = action.fcurves.new(
                data_path=data_path,
                index=index,
                action_group="SUM Asset Animation",
            )
            _add_hermite_keys(fcurve, keys)

    owner["sum_animation_action"] = action.name
    return action


def _spin_channel(
    obj: bpy.types.Object,
    clock: _ClockSamples,
    nominal_rpm: float,
    direction: float,
) -> tuple[list[tuple[int, float, float]], float, int]:
    _preserve_base_as_quaternion(obj)
    base_delta = _stored_vector(obj, "delta_rotation", obj.delta_rotation_euler)
    obj.delta_rotation_euler = base_delta
    visual_duration = clock.visual_seconds[-1]
    turns = max(1, int(round(abs(nominal_rpm) * visual_duration / 60.0)))
    angular_speed = direction * math.tau * turns / visual_duration
    seconds_per_frame = clock.seconds[1] - clock.seconds[0]
    keys = [
        (
            frame,
            base_delta[2] + angular_speed * visual_time,
            angular_speed * rate * seconds_per_frame,
        )
        for frame, visual_time, rate in zip(
            clock.frames, clock.visual_seconds, clock.rates
        )
    ]
    effective_rpm = abs(angular_speed) * 60.0 / math.tau
    obj["sum_animation_nominal_rpm"] = float(nominal_rpm)
    obj["sum_animation_effective_rpm"] = float(effective_rpm)
    obj["sum_animation_spin_axis_geometry_local"] = [0.0, 0.0, 1.0]
    return keys, effective_rpm, turns


def _grinding_feed_keys(
    obj: bpy.types.Object,
    fps: int,
    frame_end: int,
    duration: float,
) -> list[tuple[int, float, float]]:
    base_delta = _stored_vector(obj, "process_delta_location", obj.delta_location)
    obj.delta_location = base_delta
    frames = tuple(
        _frame_at(seconds, fps, frame_end, duration)
        for seconds in _GRINDING_FEED_TIMES
    )
    retracted = base_delta[1] - _GRINDING_FEED_RETRACT_M
    values = (retracted, retracted, base_delta[1], base_delta[1], retracted, retracted)
    obj["sum_process_motion_role"] = "radial_grinding_infeed"
    obj["sum_animation_radial_feed_m"] = _GRINDING_FEED_RETRACT_M
    obj["sum_animation_feed_axis_parent_local"] = [0.0, 1.0, 0.0]
    obj["sum_animation_feed_frames"] = list(frames)
    return [(frame, value, 0.0) for frame, value in zip(frames, values)]


def _grinding_slide_members(wheel: bpy.types.Object) -> list[bpy.types.Object]:
    members = [wheel]
    for obj in bpy.context.scene.objects:
        if obj is wheel:
            continue
        if obj.name in _GRINDING_SLIDE_NAMES or obj.name.startswith(
            _GRINDING_SLIDE_PREFIXES
        ):
            members.append(obj)
    return members


def _coolant_jet_objects() -> list[bpy.types.Object]:
    return sorted(
        (
            obj
            for obj in bpy.context.scene.objects
            if obj.get("sum_part_role") == "coherent_high_pressure_coolant_jet"
            or obj.name.startswith("SUM_GrindingCell_CoolantJet_Stream_")
        ),
        key=lambda item: item.name,
    )


def _coolant_jet_keys(
    curve: Any,
    clock: _ClockSamples,
    duration: float,
    phase_offset: float,
) -> list[tuple[int, float, float]]:
    base_depth = _stored_scalar(curve, "coolant_bevel_depth", curve.bevel_depth)
    curve.bevel_depth = base_depth
    factor = duration / _BASE_DURATION
    full_start = 16.00 * factor
    full_end = 20.75 * factor
    ramp = max(0.35 * factor, 1.0e-4)
    values: list[float] = []
    for seconds, visual_time in zip(clock.seconds, clock.visual_seconds):
        envelope = _window_envelope(seconds, full_start, full_end, ramp)
        pulse = 1.0 + 0.035 * envelope * math.sin(
            math.tau * 4.2 * visual_time + phase_offset
        )
        values.append(base_depth * (0.025 + 0.975 * envelope) * pulse)
    return _sampled_keys(clock.frames, values)


def _coolant_flow_action(
    clock: _ClockSamples,
    fps: int,
    duration: float,
) -> bpy.types.Action | None:
    material = bpy.data.materials.get("LD_Grinding_Coolant_Stream")
    if material is None or not material.use_nodes or material.node_tree is None:
        return None
    mapping = material.node_tree.nodes.get("LD_Coolant_FlowMapping")
    if mapping is None:
        return None
    location = mapping.inputs.get("Location")
    if location is None:
        return None
    base = _stored_vector(
        material.node_tree,
        "coolant_flow_location",
        location.default_value,
    )
    location.default_value = base
    stride = max(1, fps // 4)
    sample_indices = list(range(0, len(clock.frames), stride))
    if sample_indices[-1] != len(clock.frames) - 1:
        sample_indices.append(len(clock.frames) - 1)
    frames = [clock.frames[index] for index in sample_indices]
    x_values = [
        base[0] + 0.018 * math.sin(math.tau * 0.37 * clock.visual_seconds[index])
        for index in sample_indices
    ]
    y_values = [
        base[1] + 0.22 * clock.visual_seconds[index]
        for index in sample_indices
    ]
    z_values = [
        base[2]
        + 0.045 * math.sin(math.tau * 0.71 * clock.visual_seconds[index] + 0.8)
        for index in sample_indices
    ]
    data_path = location.path_from_id("default_value")
    material["sum_micro_surface_motion"] = "advected coolant noise coordinates"
    material["sum_flow_texture_units_per_second"] = 0.22
    return _create_action(
        material.node_tree,
        f"{_ACTION_PREFIX}CoolantSurfaceFlow",
        "coolant_surface_advection",
        (
            (data_path, 0, _sampled_keys(frames, x_values)),
            (data_path, 1, _sampled_keys(frames, y_values)),
            (data_path, 2, _sampled_keys(frames, z_values)),
        ),
        fps,
        duration,
        owner_key=f"NODETREE:coolant_flow:{material.node_tree.name}",
    )


def _coolant_pool_channels(
    pool: bpy.types.Object,
    clock: _ClockSamples,
    duration: float,
) -> list[tuple[str, int, Sequence[tuple[int, float, float]]]]:
    base_delta = _stored_vector(pool, "coolant_pool_delta_location", pool.delta_location)
    base_scale = _stored_vector(pool, "coolant_pool_scale", pool.scale)
    pool.delta_location = base_delta
    pool.scale = base_scale
    window = _scaled_window(_GRINDING_WINDOW, duration)
    ramp = max(0.72 * duration / _BASE_DURATION, 1.0e-4)
    z_values: list[float] = []
    x_values: list[float] = []
    y_values: list[float] = []
    for seconds, visual_time in zip(clock.seconds, clock.visual_seconds):
        envelope = _window_envelope(seconds, window.start_s, window.end_s, ramp)
        primary = math.sin(math.tau * 1.35 * visual_time)
        secondary = math.sin(math.tau * 0.83 * visual_time + 1.7)
        z_values.append(base_delta[2] + envelope * 0.0012 * primary)
        x_values.append(base_scale[0] * (1.0 + envelope * 0.0018 * secondary))
        y_values.append(base_scale[1] * (1.0 - envelope * 0.0015 * secondary))
    pool["sum_process_motion_role"] = "coolant_return_surface_ripple"
    pool["sum_return_surface_vertical_amplitude_m"] = 0.0012
    return [
        ("delta_location", 2, _sampled_keys(clock.frames, z_values)),
        ("scale", 0, _sampled_keys(clock.frames, x_values)),
        ("scale", 1, _sampled_keys(clock.frames, y_values)),
    ]


_ROBOT_POSES_DEGREES: tuple[tuple[float, tuple[float, ...]], ...] = (
    (0.00, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
    (6.10, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
    (6.55, (5.0, -10.0, 15.0, -10.0, 8.0, -12.0)),
    (6.90, (12.0, -25.0, 38.0, -28.0, 20.0, -32.0)),
    (7.25, (15.0, -30.0, 45.0, -35.0, 25.0, -40.0)),
    (7.75, (15.0, -30.0, 45.0, -35.0, 25.0, -40.0)),
    (8.35, (24.0, -40.0, 56.0, -48.0, 31.0, -62.0)),
    (9.60, (-8.0, -36.0, 51.0, -30.0, 28.0, -22.0)),
    (11.80, (-24.0, -26.0, 42.0, -18.0, 30.0, 12.0)),
    (13.20, (-24.0, -26.0, 42.0, -18.0, 30.0, 12.0)),
    (14.20, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
    (38.00, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
)


def _robot_joint_keys(
    joint: bpy.types.Object,
    joint_index: int,
    fps: int,
    frame_end: int,
    duration: float,
) -> list[tuple[int, float, float]]:
    joint.rotation_mode = "AXIS_ANGLE"
    base_angle = _stored_scalar(joint, "joint_angle", joint.rotation_axis_angle[0])
    keyed: dict[int, tuple[float, float]] = {}
    for seconds, pose in _ROBOT_POSES_DEGREES:
        frame = _frame_at(seconds, fps, frame_end, duration)
        keyed[frame] = (base_angle + math.radians(pose[joint_index]), 0.0)
    keyed[1] = (base_angle, 0.0)
    keyed[frame_end] = (base_angle, 0.0)
    return [(frame, *keyed[frame]) for frame in sorted(keyed)]


def _window_envelope(seconds: float, start: float, end: float, ramp: float) -> float:
    if seconds <= start - ramp or seconds >= end + ramp:
        return 0.0
    if seconds < start:
        return _smootherstep((seconds - (start - ramp)) / ramp)
    if seconds <= end:
        return 1.0
    return 1.0 - _smootherstep((seconds - end) / ramp)


def _spark_channels(
    sparks: bpy.types.Object,
    clock: _ClockSamples,
    duration: float,
) -> list[tuple[str, int, Sequence[tuple[int, float, float]]]]:
    base_scale = _stored_vector(sparks, "spark_scale", sparks.scale)
    base_delta = _stored_vector(sparks, "spark_delta_rotation", sparks.delta_rotation_euler)
    sparks.scale = base_scale
    sparks.delta_rotation_euler = base_delta

    window = _scaled_window(_GRINDING_WINDOW, duration)
    ramp = max(0.18 * duration / _BASE_DURATION, 1.0e-4)
    scales = ([], [], [])
    rotations: list[float] = []
    for seconds, visual_time in zip(clock.seconds, clock.visual_seconds):
        envelope = _window_envelope(seconds, window.start_s, window.end_s, ramp)
        phase = math.tau * 7.5 * visual_time
        floor = 0.002
        visible = floor + (1.0 - floor) * envelope
        scales[0].append(base_scale[0] * visible * (1.0 + 0.055 * envelope * math.sin(phase)))
        scales[1].append(
            base_scale[1] * visible * (1.0 + 0.035 * envelope * math.sin(phase + 1.7))
        )
        scales[2].append(
            base_scale[2] * visible * (1.0 + 0.090 * envelope * math.sin(phase + 3.4))
        )
        rotations.append(
            base_delta[2] + math.radians(2.4) * envelope * math.sin(phase * 0.37)
        )

    channels: list[tuple[str, int, Sequence[tuple[int, float, float]]]] = []
    for index, values in enumerate(scales):
        channels.append(("scale", index, _sampled_keys(clock.frames, values, close_loop=True)))
    channels.append(
        (
            "delta_rotation_euler",
            2,
            _sampled_keys(clock.frames, rotations, close_loop=True),
        )
    )
    sparks["sum_animation_contact_window"] = f"{window.start_s:.4f}-{window.end_s:.4f}s"
    return channels


def _iter_descendants(root: bpy.types.Object) -> list[bpy.types.Object]:
    descendants: list[bpy.types.Object] = []
    pending = list(root.children)
    while pending:
        child = pending.pop()
        descendants.append(child)
        pending.extend(child.children)
    return descendants


def _material_emission_socket(material: bpy.types.Material) -> Any | None:
    if not material.use_nodes or material.node_tree is None:
        return None
    emission_nodes = [node for node in material.node_tree.nodes if node.type == "EMISSION"]
    principled_nodes = [
        node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"
    ]
    for node in (*emission_nodes, *principled_nodes):
        for name in ("Strength", "Emission Strength"):
            socket = node.inputs.get(name)
            if socket is not None and isinstance(socket.default_value, (int, float)):
                return socket
    return None


def _screen_emission_targets(assets: Any) -> list[tuple[Any, Any, str, int, str]]:
    targets: list[tuple[Any, Any, str, int, str]] = []
    seen: set[int] = set()

    screens = _asset_value(assets, "screen_displays") or _asset_value(assets, "screens")
    if isinstance(screens, Sequence) and not isinstance(screens, (str, bytes)):
        for index, screen in enumerate(screens):
            if not isinstance(screen, bpy.types.Object):
                continue
            for slot in screen.material_slots:
                material = slot.material
                if material is None or material.node_tree is None:
                    continue
                pointer = material.node_tree.as_pointer()
                if pointer in seen:
                    continue
                socket = _material_emission_socket(material)
                if socket is not None:
                    seen.add(pointer)
                    targets.append(
                        (
                            material.node_tree,
                            socket,
                            "screen_breath",
                            index,
                            material.name,
                        )
                    )

    stations = _asset_value(assets, "screen_stations")
    if isinstance(stations, Sequence) and not isinstance(stations, (str, bytes)):
        for index, station in enumerate(stations):
            if not isinstance(station, bpy.types.Object):
                continue
            for obj in _iter_descendants(station):
                if obj.get("sum_part_role") != "screen_station_live_status_indicator":
                    continue
                for slot in obj.material_slots:
                    material = slot.material
                    if material is None or material.node_tree is None:
                        continue
                    pointer = material.node_tree.as_pointer()
                    if pointer in seen:
                        continue
                    socket = _material_emission_socket(material)
                    if socket is not None:
                        seen.add(pointer)
                        targets.append(
                            (
                                material.node_tree,
                                socket,
                                "indicator_pulse",
                                index,
                                material.name,
                            )
                        )
    return targets


def _screen_emission_keys(
    tree: Any,
    socket: Any,
    role: str,
    index: int,
    clock: _ClockSamples,
    duration: float,
) -> tuple[str, list[tuple[int, float, float]]]:
    base = _stored_scalar(tree, f"{role}_emission", float(socket.default_value))
    socket.default_value = base
    factor = duration / _BASE_DURATION
    start = 15.00 * factor
    end = 35.20 * factor
    ramp = max(0.65 * factor, 1.0e-4)
    amplitude = 0.025 if role == "screen_breath" else 0.10
    frequency = 0.42 if role == "screen_breath" else 0.72
    values: list[float] = []
    for seconds in clock.seconds:
        envelope = _window_envelope(seconds, start, end, ramp)
        base_seconds = seconds / max(factor, 1.0e-8)
        pulse = math.sin(math.tau * frequency * base_seconds + index * 0.8)
        values.append(max(0.0, base * (1.0 + amplitude * envelope * pulse)))
    return socket.path_from_id("default_value"), _sampled_keys(
        clock.frames, values, close_loop=True
    )


def _spark_light_action(
    light_object: bpy.types.Object,
    clock: _ClockSamples,
    duration: float,
    fps: int,
) -> bpy.types.Action | None:
    if light_object.type != "LIGHT" or light_object.data is None:
        return None
    light = light_object.data
    base_energy = _stored_scalar(light, "spark_energy", light.energy)
    window = _scaled_window(_GRINDING_WINDOW, duration)
    ramp = max(0.18 * duration / _BASE_DURATION, 1.0e-4)
    values: list[float] = []
    for seconds, visual_time in zip(clock.seconds, clock.visual_seconds):
        envelope = _window_envelope(seconds, window.start_s, window.end_s, ramp)
        pulse = 0.88 + 0.12 * math.sin(math.tau * 6.0 * visual_time + 0.5)
        values.append(max(0.0, base_energy * envelope * pulse))
    return _create_action(
        light,
        f"{_ACTION_PREFIX}SparkBounceLight",
        "spark_bounce_light",
        (("energy", 0, _sampled_keys(clock.frames, values, close_loop=True)),),
        fps,
        duration,
    )


def animate_assets(assets: Any, fps: int = 24, duration: float = 38) -> dict[str, Any]:
    """Animate SUM mechanical assets without changing the camera clock.

    The function is idempotent: it replaces only actions tagged as generated by
    this module, uses stable action names, and preserves authored base transforms.
    It returns both live Blender datablocks and name-only summaries for pipeline
    logging.
    """

    frame_end, duration = _validate_timing(fps, duration)
    scene = bpy.context.scene
    original_frame = scene.frame_current
    camera_action_before = (
        scene.camera.animation_data.action
        if scene.camera is not None and scene.camera.animation_data is not None
        else None
    )

    scene.frame_start = 1
    scene.frame_end = frame_end
    scene.frame_preview_start = 1
    scene.frame_preview_end = frame_end
    scene.render.fps = fps
    scene.render.fps_base = 1.0

    bearing = _require_object(
        assets, "bearing_rotation_root", "SUM_Bearing_Assembly_RotationRoot"
    )
    wheel = _require_object(
        assets, "grinding_wheel", "SUM_GrindingCell_CBN_InternalGrindingWheel"
    )
    workpiece = _require_object(
        assets, "grinding_workpiece", "SUM_GrindingCell_OuterRing_Workpiece"
    )
    robot_joints = _resolve_robot_joints(assets)
    sparks = _resolve_sparks(assets)
    agv = _asset_value(assets, "agv")
    grinder_doors = _asset_value(assets, "grinder_doors")

    bearing_clock = _clock_samples(fps, frame_end, duration, _BEARING_WINDOW)
    grinding_clock = _clock_samples(fps, frame_end, duration, _GRINDING_WINDOW)
    uniform_clock = _uniform_clock_samples(fps, frame_end)
    actions: dict[str, bpy.types.Action] = {}
    animated_objects: list[bpy.types.Object] = []
    animated_data: list[Any] = []
    rpm_summary: dict[str, dict[str, float | int]] = {}
    missing_optional: list[str] = []

    bearing_keys, bearing_rpm, bearing_turns = _spin_channel(
        bearing, bearing_clock, nominal_rpm=84.0, direction=1.0
    )
    actions["bearing_rotation"] = _create_action(
        bearing,
        f"{_ACTION_PREFIX}BearingInspection",
        "bearing_inspection_rotation",
        (("delta_rotation_euler", 2, bearing_keys),),
        fps,
        duration,
    )
    animated_objects.append(bearing)
    rpm_summary["bearing"] = {"effective_rpm": bearing_rpm, "loop_turns": bearing_turns}

    for index, joint in enumerate(robot_joints):
        joint_key = f"robot_joint_{index + 1}"
        keys = _robot_joint_keys(joint, index, fps, frame_end, duration)
        actions[joint_key] = _create_action(
            joint,
            f"{_ACTION_PREFIX}RobotJ{index + 1}",
            f"robot_axis_{index + 1}_handoff",
            (("rotation_axis_angle", 0, keys),),
            fps,
            duration,
        )
        joint["sum_animation_slow_window"] = (
            f"{_scaled_window(_HANDOFF_WINDOW, duration).start_s:.4f}-"
            f"{_scaled_window(_HANDOFF_WINDOW, duration).end_s:.4f}s"
        )
        animated_objects.append(joint)

    if isinstance(agv, bpy.types.Object):
        base_location = _stored_vector(agv, "location", agv.location)
        travel_distance = 24.0
        agv_frames = (1, frame_end)
        agv_values = (base_location[1], base_location[1] + travel_distance)
        actions["agv_translation"] = _create_action(
            agv,
            f"{_ACTION_PREFIX}AGV07Translation",
            "agv_constant_speed_translation",
            (("location", 1, _sampled_keys(agv_frames, agv_values)),),
            fps,
            duration,
        )
        agv["sum_animation_speed_mps"] = travel_distance / duration
        agv["sum_animation_route"] = "painted_center_aisle"
        animated_objects.append(agv)
        wheel_radius = float(agv.get("agv_drive_wheel_radius_m", 0.17))
        wheel_rpm = (travel_distance / duration) * 60.0 / (math.tau * wheel_radius)
        agv_wheels = sorted(
            (
                obj
                for obj in _iter_descendants(agv)
                if obj.get("sum_part_role") == "agv_recessed_protected_drive_wheel"
                or obj.name.startswith("SUM_AGV07_ProtectedWheel_")
            ),
            key=lambda item: item.name,
        )
        for wheel_index, agv_wheel in enumerate(agv_wheels, start=1):
            keys, effective_rpm, turns = _spin_channel(
                agv_wheel,
                uniform_clock,
                nominal_rpm=wheel_rpm,
                direction=1.0,
            )
            actions[f"agv_wheel_{wheel_index}"] = _create_action(
                agv_wheel,
                f"{_ACTION_PREFIX}AGV07Wheel_{wheel_index:02d}",
                "agv_driven_wheel_rotation",
                (("delta_rotation_euler", 2, keys),),
                fps,
                duration,
            )
            agv_wheel["sum_animation_wheel_radius_m"] = float(
                agv_wheel.get("sum_animation_wheel_radius_m", wheel_radius)
            )
            agv_wheel["sum_animation_no_slip_nominal_rpm"] = wheel_rpm
            animated_objects.append(agv_wheel)
            rpm_summary[f"agv_wheel_{wheel_index}"] = {
                "effective_rpm": effective_rpm,
                "loop_turns": turns,
            }
    else:
        missing_optional.append("agv")

    if isinstance(grinder_doors, Sequence) and not isinstance(
        grinder_doors, (str, bytes)
    ):
        door_frames = tuple(
            _frame_at(seconds, fps, frame_end, duration)
            for seconds in (10.50, 11.00, 20.75, 21.25)
        )
        for door_index, door in enumerate(grinder_doors, start=1):
            if not isinstance(door, bpy.types.Object):
                continue
            base_location = _stored_vector(door, "location", door.location)
            open_offset = float(door.get("open_offset_m", 0.0))
            door_values = (
                base_location[1],
                base_location[1] + open_offset,
                base_location[1] + open_offset,
                base_location[1],
            )
            actions[f"grinder_door_{door_index}"] = _create_action(
                door,
                f"{_ACTION_PREFIX}GrindingDoor_{door_index:02d}",
                "grinding_cell_sliding_door",
                (("location", 1, _sampled_keys(door_frames, door_values)),),
                fps,
                duration,
            )
            door["sum_animation_window"] = "6.60-10.90s"
            animated_objects.append(door)
    else:
        missing_optional.append("grinder_doors")

    wheel_keys, wheel_rpm, wheel_turns = _spin_channel(
        wheel, grinding_clock, nominal_rpm=11500.0, direction=1.0
    )
    wheel_feed_keys = _grinding_feed_keys(wheel, fps, frame_end, duration)
    actions["grinding_wheel"] = _create_action(
        wheel,
        f"{_ACTION_PREFIX}GrindingWheel",
        "grinding_wheel_rotation_and_radial_infeed",
        (
            ("delta_rotation_euler", 2, wheel_keys),
            ("delta_location", 1, wheel_feed_keys),
        ),
        fps,
        duration,
    )
    animated_objects.append(wheel)
    rpm_summary["grinding_wheel"] = {
        "effective_rpm": wheel_rpm,
        "loop_turns": wheel_turns,
    }
    wheel["sum_animation_rotation_direction"] = "positive local spindle axis"
    wheel["sum_animation_contact_speed_scale"] = _GRINDING_WINDOW.minimum_scale

    grinding_slide = _grinding_slide_members(wheel)
    for slide_index, slide_obj in enumerate(grinding_slide[1:], start=1):
        actions[f"grinding_slide_{slide_index}"] = _create_action(
            slide_obj,
            f"{_ACTION_PREFIX}GrindingSlide_{slide_index:02d}_{_safe_action_suffix(slide_obj.name)}",
            "radial_grinding_slide_infeed",
            (("delta_location", 1, _grinding_feed_keys(slide_obj, fps, frame_end, duration)),),
            fps,
            duration,
        )
        animated_objects.append(slide_obj)

    workpiece_keys, workpiece_rpm, workpiece_turns = _spin_channel(
        workpiece, grinding_clock, nominal_rpm=240.0, direction=-1.0
    )
    actions["grinding_workpiece"] = _create_action(
        workpiece,
        f"{_ACTION_PREFIX}GrindingWorkpiece",
        "grinding_workpiece_counter_rotation",
        (("delta_rotation_euler", 2, workpiece_keys),),
        fps,
        duration,
    )
    animated_objects.append(workpiece)
    rpm_summary["grinding_workpiece"] = {
        "effective_rpm": workpiece_rpm,
        "loop_turns": workpiece_turns,
    }
    workpiece["sum_animation_rotation_direction"] = "counter rotation to CBN wheel"
    workpiece["sum_animation_nominal_speed_ratio_to_wheel"] = 240.0 / 11500.0

    coolant_jets = _coolant_jet_objects()
    for jet_index, jet in enumerate(coolant_jets, start=1):
        curve = getattr(jet, "data", None)
        if curve is None or not hasattr(curve, "bevel_depth"):
            continue
        actions[f"coolant_jet_{jet_index}"] = _create_action(
            curve,
            f"{_ACTION_PREFIX}CoolantJet_{jet_index:02d}",
            "coherent_coolant_jet_pressure_envelope",
            ((
                "bevel_depth",
                0,
                _coolant_jet_keys(curve, grinding_clock, duration, jet_index * 1.1),
            ),),
            fps,
            duration,
        )
        jet["sum_process_motion_role"] = "coherent_coolant_jet"
        jet["sum_coolant_target_policy"] = "fixed nozzle-to-contact endpoints"
        jet["sum_animation_pressure_pulse_fraction"] = 0.035
        animated_data.append(curve)

    coolant_flow = _coolant_flow_action(grinding_clock, fps, duration)
    if coolant_flow is not None:
        actions["coolant_surface_flow"] = coolant_flow
        coolant_material = bpy.data.materials.get("LD_Grinding_Coolant_Stream")
        if coolant_material is not None and coolant_material.node_tree is not None:
            animated_data.append(coolant_material.node_tree)
    else:
        missing_optional.append("coolant_flow_mapping")

    coolant_pool = bpy.data.objects.get("SUM_GrindingCell_ProcessChamber_CoolantPool")
    if isinstance(coolant_pool, bpy.types.Object):
        actions["coolant_return_pool"] = _create_action(
            coolant_pool,
            f"{_ACTION_PREFIX}CoolantReturnPool",
            "coolant_return_surface_ripple",
            _coolant_pool_channels(coolant_pool, grinding_clock, duration),
            fps,
            duration,
        )
        animated_objects.append(coolant_pool)
    else:
        missing_optional.append("coolant_return_pool")

    if sparks is not None:
        actions["grinding_sparks"] = _create_action(
            sparks,
            f"{_ACTION_PREFIX}GrindingSparks",
            "grinding_spark_envelope",
            _spark_channels(sparks, grinding_clock, duration),
            fps,
            duration,
        )
        animated_objects.append(sparks)
    else:
        missing_optional.append("lookdev_grinding_sparks")

    spark_light = bpy.data.objects.get("LD_Spark_Bounce")
    if isinstance(spark_light, bpy.types.Object):
        light_action = _spark_light_action(
            spark_light, grinding_clock, duration, fps
        )
        if light_action is not None:
            actions["spark_bounce_light"] = light_action
            animated_objects.append(spark_light)
            animated_data.append(spark_light.data)

    screen_targets = _screen_emission_targets(assets)
    for target_index, (tree, socket, role, screen_index, material_name) in enumerate(
        screen_targets
    ):
        data_path, keys = _screen_emission_keys(
            tree, socket, role, screen_index, grinding_clock, duration
        )
        summary_key = f"{role}_{target_index + 1}"
        owner_key = (
            f"NODETREE:{role}:screen={screen_index + 1:02d}:"
            f"material={material_name}:tree={tree.name}"
        )
        action_name = (
            f"{_ACTION_PREFIX}{'ScreenBreath' if role == 'screen_breath' else 'IndicatorPulse'}_"
            f"{screen_index + 1:02d}_{_safe_action_suffix(material_name)}"
        )
        actions[summary_key] = _create_action(
            tree,
            action_name,
            role,
            ((data_path, 0, keys),),
            fps,
            duration,
            owner_key=owner_key,
        )
        animated_data.append(tree)

    camera_action_after = (
        scene.camera.animation_data.action
        if scene.camera is not None and scene.camera.animation_data is not None
        else None
    )
    camera_action_unchanged = camera_action_before is camera_action_after
    if not camera_action_unchanged:
        raise RuntimeError("Asset animation must not replace or remap the camera action")

    windows = [
        {
            "id": window.slug,
            "start_seconds": _scaled_window(window, duration).start_s,
            "end_seconds": _scaled_window(window, duration).end_s,
            "minimum_motion_scale": window.minimum_scale,
        }
        for window in _MECHANICAL_WINDOWS
    ]
    manifest = {
        "fps": fps,
        "duration": duration,
        "frame_start": 1,
        "frame_end": frame_end,
        "camera_clock": "independent_unmodified",
        "screen_motion": "emission_only_no_card_transforms",
        "actions": {key: action.name for key, action in actions.items()},
        "animated_objects": [obj.name for obj in animated_objects],
        "windows": windows,
        "grinding_process": {
            "wheel_nominal_rpm": 11500.0,
            "workpiece_nominal_rpm": 240.0,
            "counter_rotation": True,
            "radial_feed_m": _GRINDING_FEED_RETRACT_M,
            "feed_frames": [
                _frame_at(seconds, fps, frame_end, duration)
                for seconds in _GRINDING_FEED_TIMES
            ],
            "coolant_jet_count": len(coolant_jets),
            "coolant_endpoint_policy": "fixed nozzle-to-contact endpoints",
        },
        "ambient_motion": {
            "agv_translation": isinstance(agv, bpy.types.Object),
            "agv_driven_wheel_count": len(
                [key for key in actions if key.startswith("agv_wheel_")]
            ),
            "screen_emission_target_count": len(screen_targets),
        },
    }
    scene["sum_animation_manifest"] = json.dumps(
        manifest, separators=(",", ":"), ensure_ascii=True
    )
    scene["sum_asset_clock_is_camera_independent"] = True
    scene["sum_screen_motion_policy"] = "emission_only_no_card_transforms"
    scene["sum_grinding_process_motion"] = json.dumps(
        manifest["grinding_process"], separators=(",", ":"), ensure_ascii=True
    )
    scene["sum_continuous_factory_motion"] = json.dumps(
        manifest["ambient_motion"], separators=(",", ":"), ensure_ascii=True
    )
    scene.frame_set(min(max(original_frame, scene.frame_start), scene.frame_end))

    return {
        "fps": fps,
        "duration": duration,
        "frame_start": 1,
        "frame_end": frame_end,
        "camera_clock_is_independent": True,
        "camera_action_unchanged": camera_action_unchanged,
        "actions": actions,
        "action_names": {key: action.name for key, action in actions.items()},
        "animated_objects": tuple(animated_objects),
        "animated_object_names": tuple(obj.name for obj in animated_objects),
        "animated_data": tuple(animated_data),
        "animated_data_names": tuple(data.name for data in animated_data),
        "rpm": rpm_summary,
        "slow_motion_windows": tuple(windows),
        "screen_motion_policy": "emission_only_no_card_transforms",
        "missing_optional": tuple(missing_optional),
    }
