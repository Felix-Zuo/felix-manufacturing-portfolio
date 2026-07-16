"""V8 one-shot camera: the camera follows one ring instead of touring screens."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Sequence

import bpy
from mathutils import Quaternion, Vector

import cinematography


BASE_DURATION = 38.0


@dataclass(frozen=True)
class CameraBeat:
    frame: int
    camera: tuple[float, float, float]
    target: tuple[float, float, float]
    lens: float
    fstop: float
    roll: float = 0.0


CAMERA_BEATS = (
    CameraBeat(1, (0.34, -1.45, 0.74), (0.0, -0.75, 0.58), 76.0, 4.0, 0.0),
    CameraBeat(24, (0.25, -0.55, 0.69), (0.0, 0.15, 0.58), 56.0, 4.0, -0.4),
    CameraBeat(84, (0.38, 3.25, 0.78), (0.0, 4.30, 0.60), 35.0, 4.5, 0.0),
    CameraBeat(132, (-0.55, 5.05, 0.82), (0.0, 6.20, 0.58), 40.0, 5.6, 0.5),
    CameraBeat(166, (-0.80, 7.75, 1.08), (0.0, 9.15, 0.65), 36.0, 5.6, -0.3),
    CameraBeat(188, (-1.05, 8.55, 1.18), (-0.05, 10.35, 0.95), 34.0, 5.6, -0.5),
    CameraBeat(228, (-0.25, 9.15, 1.35), (0.45, 10.35, 1.25), 30.0, 5.6, 0.4),
    CameraBeat(252, (0.20, 10.10, 1.35), (0.25, 10.75, 1.10), 38.0, 5.6, 0.0),
    CameraBeat(300, (1.70, 12.55, 2.10), (0.25, 14.25, 1.78), 34.0, 6.3, -0.5),
    CameraBeat(330, (2.20, 12.90, 2.35), (1.65, 14.55, 1.82), 38.0, 6.3, -0.3),
    CameraBeat(342, (2.80, 13.05, 2.55), (2.80, 15.00, 1.82), 42.0, 6.3, 0.0),
    CameraBeat(386, (3.62, 13.20, 2.68), (2.95, 15.00, 1.82), 46.0, 6.3, 0.3),
    CameraBeat(420, (3.58, 13.35, 2.64), (2.98, 15.03, 1.82), 52.0, 7.1, 0.4),
    CameraBeat(474, (3.48, 13.64, 2.48), (2.98, 15.03, 1.82), 58.0, 7.1, 0.0),
    CameraBeat(498, (3.32, 14.10, 2.30), (2.93, 15.00, 1.82), 50.0, 6.3, -0.2),
    CameraBeat(510, (3.55, 16.20, 1.72), (3.55, 16.92, 1.70), 58.0, 7.1, -0.2),
    CameraBeat(522, (3.70, 18.20, 1.62), (2.55, 17.20, 1.19), 36.0, 6.3, -0.4),
    CameraBeat(588, (2.10, 18.25, 1.48), (1.20, 20.00, 1.30), 36.0, 5.6, -0.4),
    CameraBeat(620, (0.80, 21.60, 1.85), (-0.80, 23.50, 1.15), 36.0, 5.6, 0.3),
    CameraBeat(660, (-0.45, 23.35, 1.95), (-1.65, 25.00, 1.12), 38.0, 5.6, 0.3),
    CameraBeat(702, (-1.00, 24.25, 1.75), (-2.20, 25.00, 1.10), 48.0, 6.3, 0.0),
    CameraBeat(735, (-0.65, 26.20, 1.20), (-0.80, 27.50, 1.00), 38.0, 5.6, -0.3),
    CameraBeat(798, (0.42, 27.65, 0.92), (0.0, 29.00, 0.64), 36.0, 5.6, 0.2),
    CameraBeat(840, (-0.32, 30.15, 0.95), (0.0, 31.80, 0.72), 32.0, 6.3, 0.3),
    CameraBeat(882, (0.00, 32.65, 1.15), (0.0, 34.30, 0.72), 32.0, 5.6, 0.0),
    CameraBeat(904, (0.00, 34.70, 1.66), (0.0, 36.00, 1.62), 35.0, 5.6, 0.0),
    CameraBeat(912, (0.00, 35.80, 1.65), (0.0, 36.90, 1.62), 35.0, 5.6, 0.0),
)

MAGNETIC_STOPS = (132, 228, 474, 660)
STORYBOARD_FRAMES = (
    1,
    84,
    132,
    166,
    188,
    228,
    252,
    300,
    342,
    386,
    420,
    474,
    498,
    522,
    588,
    620,
    660,
    702,
    735,
    798,
    840,
    882,
    904,
)


def _scaled_frame(frame: int, fps: int, duration: float) -> int:
    seconds = (frame - 1) / 24.0
    scaled_seconds = seconds * duration / BASE_DURATION
    return max(1, min(round(duration * fps), 1 + int(round(scaled_seconds * fps))))


def _authoring_to_film(value: Sequence[float]) -> Vector:
    return Vector((float(value[0]), float(value[2]), -float(value[1])))


def _tangents(frames: Sequence[int], vectors: Sequence[Vector]) -> list[Vector]:
    tangents: list[Vector] = []
    for index, vector in enumerate(vectors):
        if index == 0:
            dt = frames[1] - frames[0]
            tangent = (vectors[1] - vector) / dt
        elif index == len(vectors) - 1:
            dt = frames[-1] - frames[-2]
            tangent = (vector - vectors[-2]) / dt
        else:
            dt = frames[index + 1] - frames[index - 1]
            tangent = (vectors[index + 1] - vectors[index - 1]) / dt
        tangents.append(tangent)
    return tangents


def _sample_vectors(
    frame_end: int,
    control_frames: Sequence[int],
    control_vectors: Sequence[Vector],
) -> list[Vector]:
    tangents = _tangents(control_frames, control_vectors)
    result: list[Vector] = []
    segment = 0
    for frame in range(1, frame_end + 1):
        while segment + 1 < len(control_frames) - 1 and frame > control_frames[segment + 1]:
            segment += 1
        start_frame = control_frames[segment]
        end_frame = control_frames[segment + 1]
        span = max(1, end_frame - start_frame)
        phase = min(1.0, max(0.0, (frame - start_frame) / span))
        p0 = control_vectors[segment]
        p1 = control_vectors[segment + 1]
        m0 = tangents[segment] * span
        m1 = tangents[segment + 1] * span
        h00 = 2.0 * phase**3 - 3.0 * phase**2 + 1.0
        h10 = phase**3 - 2.0 * phase**2 + phase
        h01 = -2.0 * phase**3 + 3.0 * phase**2
        h11 = phase**3 - phase**2
        sampled = p0 * h00 + m0 * h10 + p1 * h01 + m1 * h11
        # Film Z is the story-travel axis. Linear interpolation here prevents
        # cubic lateral/elevation easing from ever introducing a backward frame.
        sampled.z = p0.z + (p1.z - p0.z) * phase
        result.append(sampled)
    return result


def _sample_scalars(
    frame_end: int,
    control_frames: Sequence[int],
    values: Sequence[float],
) -> list[float]:
    vectors = [Vector((float(value), 0.0, 0.0)) for value in values]
    return [value.x for value in _sample_vectors(frame_end, control_frames, vectors)]


def _vector_channels(path: str, values: Sequence[Vector]) -> list[tuple[str, int, list[tuple[int, float, float]]]]:
    frames = list(range(1, len(values) + 1))
    channels = []
    for axis in range(3):
        scalars = [float(value[axis]) for value in values]
        slopes = cinematography._finite_slopes(frames, scalars)
        channels.append(
            (path, axis, [(frame, scalars[index], slopes[index]) for index, frame in enumerate(frames)])
        )
    return channels


def _build_black_handoff(
    camera: bpy.types.Object,
    collection: bpy.types.Collection,
    handoff_frame: int,
    frame_end: int,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new("CIN_BlackHandoffMesh")
    mesh.from_pydata(
        [(-3.0, -2.0, -0.05), (3.0, -2.0, -0.05), (3.0, 2.0, -0.05), (-3.0, 2.0, -0.05)],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.update()
    material = bpy.data.materials.get("CIN_MAT_BlackHandoff") or bpy.data.materials.new(
        "CIN_MAT_BlackHandoff"
    )
    material.use_nodes = True
    material.diffuse_color = (0.0, 0.0, 0.0, 1.0)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    emission.inputs["Strength"].default_value = 0.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    mesh.materials.append(material)
    wipe = bpy.data.objects.new("CIN_BlackHandoff", mesh)
    wipe.parent = camera
    wipe.scale = (0.0001, 0.0001, 0.0001)
    wipe["sum_part_role"] = "camera_locked_black_web_handoff"
    collection.objects.link(wipe)
    keys = (
        (1, 0.0001, 0.0),
        (max(1, handoff_frame - 1), 0.0001, 0.0),
        (handoff_frame, 1.0, 0.0),
        (frame_end, 1.0, 0.0),
    )
    cinematography._create_action_curves(
        wipe,
        "CIN_BlackHandoffAction",
        (("scale", 0, keys), ("scale", 1, keys), ("scale", 2, keys)),
    )
    return wipe


def build_cinematography(assets: dict[str, object], fps: int = 24, duration: float = 38.0) -> bpy.types.Object:
    frame_end = int(round(fps * duration))
    if frame_end < 120:
        raise ValueError("V8 cinematography needs enough frames for the process story")

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = frame_end
    scene.frame_preview_start = 1
    scene.frame_preview_end = frame_end
    scene.render.fps = fps
    scene.render.fps_base = 1.0

    collection = cinematography._remove_previous_build()
    frames = [_scaled_frame(beat.frame, fps, duration) for beat in CAMERA_BEATS]
    if len(set(frames)) != len(frames):
        raise ValueError("V8 camera beats collapsed at the requested fps/duration")
    camera_controls = [_authoring_to_film(beat.camera) for beat in CAMERA_BEATS]
    target_controls = [_authoring_to_film(beat.target) for beat in CAMERA_BEATS]
    camera_positions = _sample_vectors(frame_end, frames, camera_controls)
    target_positions = _sample_vectors(frame_end, frames, target_controls)

    if any(camera_positions[index].z >= camera_positions[index - 1].z for index in range(1, frame_end)):
        raise ValueError("V8 camera must advance continuously along film -Z")

    path = cinematography._build_bezier_path(collection, camera_controls)
    path["usage"] = "auditable C1 guide; camera is baked per frame for deterministic scroll scrubbing"

    look_at = bpy.data.objects.new("CIN_LookAt", None)
    look_at.empty_display_type = "SPHERE"
    look_at.empty_display_size = 0.10
    look_at.hide_render = True
    collection.objects.link(look_at)
    cinematography._create_action_curves(
        look_at,
        "CIN_LookAtAction",
        _vector_channels("location", target_positions),
    )

    camera_data = bpy.data.cameras.new("CIN_CameraData")
    camera_data.type = "PERSP"
    camera_data.sensor_width = 36.0
    camera_data.clip_start = 0.025
    camera_data.clip_end = 180.0
    camera_data.dof.use_dof = True
    camera_data.dof.focus_object = look_at
    camera_data.dof.aperture_blades = 9
    camera_data.lens = CAMERA_BEATS[0].lens
    camera_data.dof.aperture_fstop = CAMERA_BEATS[0].fstop
    camera = bpy.data.objects.new("CIN_Camera", camera_data)
    camera.rotation_mode = "QUATERNION"
    collection.objects.link(camera)
    scene.camera = camera
    black_handoff_frame = _scaled_frame(904, fps, duration)
    black_handoff = _build_black_handoff(camera, collection, black_handoff_frame, frame_end)

    camera_action = cinematography._create_action_curves(
        camera,
        "CIN_CameraAction",
        _vector_channels("location", camera_positions),
    )

    roll_values = _sample_scalars(frame_end, frames, [beat.roll for beat in CAMERA_BEATS])
    quaternions: list[Quaternion] = []
    previous: Quaternion | None = None
    for index, (position, target) in enumerate(zip(camera_positions, target_positions)):
        quaternion = cinematography._film_look_quaternion(position, target)
        quaternion = quaternion @ Quaternion((0.0, 0.0, 1.0), math.radians(roll_values[index]))
        if previous is not None and previous.dot(quaternion) < 0.0:
            quaternion.negate()
        quaternions.append(quaternion)
        previous = quaternion
    rotation_channels = []
    integer_frames = list(range(1, frame_end + 1))
    for component in range(4):
        values = [float(value[component]) for value in quaternions]
        slopes = cinematography._finite_slopes(integer_frames, values)
        rotation_channels.append(
            (
                "rotation_quaternion",
                component,
                [(frame, values[index], slopes[index]) for index, frame in enumerate(integer_frames)],
            )
        )
    cinematography._append_action_curves(camera, camera_action, rotation_channels)

    lens_values = _sample_scalars(frame_end, frames, [beat.lens for beat in CAMERA_BEATS])
    fstop_values = _sample_scalars(frame_end, frames, [beat.fstop for beat in CAMERA_BEATS])
    lens_slopes = cinematography._finite_slopes(integer_frames, lens_values)
    fstop_slopes = cinematography._finite_slopes(integer_frames, fstop_values)
    cinematography._create_action_curves(
        camera_data,
        "CIN_CameraDataAction",
        (
            ("lens", 0, [(frame, lens_values[index], lens_slopes[index]) for index, frame in enumerate(integer_frames)]),
            (
                "dof.aperture_fstop",
                0,
                [(frame, fstop_values[index], fstop_slopes[index]) for index, frame in enumerate(integer_frames)],
            ),
        ),
    )

    windows = (
        cinematography.BulletWindow("robot_pickup", 6.90 * duration / BASE_DURATION, 8.25 * duration / BASE_DURATION, 0.32, 0.34, max(fps, 96)),
        cinematography.BulletWindow("wet_grinding", 17.58 * duration / BASE_DURATION, 19.38 * duration / BASE_DURATION, 0.22, 0.20, max(fps, 120)),
    )
    time_control = cinematography._build_visual_clock(collection, fps, frame_end, windows)

    for marker in list(scene.timeline_markers):
        if marker.name.startswith("CIN_"):
            scene.timeline_markers.remove(marker)
    marker_frames = {
        "ENTRY": 1,
        "SCAN_NOTICE": 132,
        "ROBOT_TAKT": 228,
        "GRIND_IMPACT": 474,
        "INSPECTION_EXCEL": 660,
        "BLACK_HANDOFF": 904,
    }
    for label, authored_frame in marker_frames.items():
        scene.timeline_markers.new(f"CIN_{label}", frame=_scaled_frame(authored_frame, fps, duration))

    manifest = {
        "version": 8,
        "fps": fps,
        "duration_seconds": duration,
        "frame_start": 1,
        "frame_end": frame_end,
        "one_shot": True,
        "story": "one outer ring from inbound AGV through wet grinding and inspection",
        "camera": {
            "object": camera.name,
            "path": path.name,
            "look_at": look_at.name,
            "travel_axis": "film -Z / authoring +Y",
            "position_bake": "per-frame cubic Hermite",
            "orientation_bake": "per-frame world quaternion",
            "roll_limit_degrees": 0.7,
            "starts_on_subject": True,
            "screen_tour": False,
        },
        "magnetic_stop_frames": [_scaled_frame(frame, fps, duration) for frame in MAGNETIC_STOPS],
        "storyboard_focus_frames": [_scaled_frame(frame, fps, duration) for frame in STORYBOARD_FRAMES],
        "black_handoff_frame": black_handoff_frame,
        "black_handoff_object": black_handoff.name,
        "visual_clock": time_control.name,
    }
    scene["cinematography_manifest"] = json.dumps(manifest, separators=(",", ":"), ensure_ascii=True)
    scene["cin_storyboard_frames"] = json.dumps(manifest["storyboard_focus_frames"], separators=(",", ":"))
    scene["cin_visual_time_object"] = time_control.name
    scene["cin_camera_speed_continuous"] = True
    scene["cin_terminal_settle_frame"] = _scaled_frame(904, fps, duration)
    camera["cin_camera_path"] = path.name
    camera["cin_look_at"] = look_at.name
    camera["cin_orientation"] = "per-frame world quaternion"
    camera["cin_story_version"] = 8
    camera["cin_time_control"] = time_control.name
    scene.frame_set(1)
    return camera
