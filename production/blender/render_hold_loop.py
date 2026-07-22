from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a fixed-camera dynamic hold loop from a saved journey scene."
    )
    parser.add_argument("--mode", choices=("desktop", "mobile"), required=True)
    parser.add_argument("--chapter", required=True)
    parser.add_argument("--start-frame", type=int, required=True)
    parser.add_argument("--end-frame", type=int)
    parser.add_argument("--camera-frame", type=int)
    parser.add_argument("--frame-count", type=int, required=True)
    parser.add_argument("--samples", type=int, default=24)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def freeze_camera(scene: bpy.types.Scene, frame: int) -> None:
    camera = scene.camera
    if camera is None:
        raise RuntimeError("The scene has no active camera")

    scene.frame_set(frame)
    bpy.context.view_layer.update()
    frozen_matrix = camera.matrix_world.copy()
    frozen_lens = float(camera.data.lens)
    frozen_shift_x = float(camera.data.shift_x)
    frozen_shift_y = float(camera.data.shift_y)

    camera.animation_data_clear()
    camera.data.animation_data_clear()
    for constraint in camera.constraints:
        constraint.mute = True
    camera.parent = None
    camera.matrix_world = frozen_matrix
    camera.data.lens = frozen_lens
    camera.data.shift_x = frozen_shift_x
    camera.data.shift_y = frozen_shift_y

    camera["sum_hold_camera_frame"] = int(frame)
    camera["sum_hold_camera_frozen"] = True


def configure_render(scene: bpy.types.Scene, mode: str, samples: int) -> None:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1600 if mode == "desktop" else 720
    scene.render.resolution_y = 900 if mode == "desktop" else 1280
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    scene.render.use_placeholder = False
    if hasattr(scene, "eevee"):
        if hasattr(scene.eevee, "taa_samples"):
            scene.eevee.taa_samples = samples
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = samples


def _copy_process_spark_material() -> bpy.types.Material:
    material = bpy.data.materials.new("SUM_HOLD_ContactSpark_Material")
    material.use_nodes = True
    material.diffuse_color = (1.0, 0.24, 0.025, 1.0)
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        base_color = principled.inputs.get("Base Color")
        roughness = principled.inputs.get("Roughness")
        metallic = principled.inputs.get("Metallic")
        emission = principled.inputs.get("Emission Color")
        emission_strength = principled.inputs.get("Emission Strength")
        if base_color:
            base_color.default_value = (1.0, 0.18, 0.018, 1.0)
        if roughness:
            roughness.default_value = 0.28
        if metallic:
            metallic.default_value = 0.0
        if emission:
            emission.default_value = (1.0, 0.055, 0.002, 1.0)
        if emission_strength:
            emission_strength.default_value = 8.0
    return material


def _link_to_collection(
    obj: bpy.types.Object, collection: bpy.types.Collection
) -> None:
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def _freeze_object_animation(scene: bpy.types.Scene, frame: int) -> None:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    animated = [obj for obj in scene.objects if obj.animation_data is not None]
    matrices = {obj.name: obj.matrix_world.copy() for obj in animated}
    for obj in animated:
        obj.animation_data_clear()
    bpy.context.view_layer.update()
    for obj in animated:
        matrix = matrices.get(obj.name)
        if matrix is not None:
            obj.matrix_world = matrix


def _hide_process_artifacts(scene: bpy.types.Scene) -> int:
    hidden = 0
    for obj in scene.objects:
        is_discrete_droplet = "CoolantSplashDroplet" in obj.name
        is_legacy_spark = "LD_Grinding_Sparks" in obj.name
        is_streaky_sheet = (
            "CoolantSplashSheet_" in obj.name and "_Jet_" not in obj.name
        )
        if is_discrete_droplet or is_legacy_spark or is_streaky_sheet:
            obj.hide_render = True
            hidden += 1
    return hidden


def _copy_process_coolant_material(
    name: str,
    *,
    alpha: float,
    emission_strength: float,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (0.46, 0.62, 0.55, alpha)
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "BLENDED"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (520.0, 0.0)
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (240.0, 0.0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-480.0, -140.0)
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 22.0
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.62
    bump = nodes.new("ShaderNodeBump")
    bump.location = (-80.0, -120.0)
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.035
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    values = {
        "Base Color": (0.34, 0.54, 0.45, 1.0),
        "Roughness": 0.18,
        "Metallic": 0.0,
        "Alpha": alpha,
        "Transmission Weight": 0.18,
        "Emission Color": (0.012, 0.038, 0.025, 1.0),
        "Emission Strength": emission_strength,
        "Coat Weight": 0.12,
    }
    for socket_name, value in values.items():
        socket = principled.inputs.get(socket_name)
        if socket is not None:
            socket.default_value = value
    return material


def _replace_material(obj: bpy.types.Object, material: bpy.types.Material) -> None:
    if not hasattr(obj.data, "materials"):
        return
    obj.data.materials.clear()
    obj.data.materials.append(material)


def _configure_process_coolant(
    scene: bpy.types.Scene,
    start_frame: int,
    frame_count: int,
) -> int:
    stream_material = _copy_process_coolant_material(
        "SUM_HOLD_CoolantStream_Material",
        alpha=0.68,
        emission_strength=0.075,
    )
    sheet_material = _copy_process_coolant_material(
        "SUM_HOLD_CoolantSheet_Material",
        alpha=0.24,
        emission_strength=0.025,
    )

    configured = 0
    stream_names = (
        "SUM_GrindingCell_CoolantJet_Stream_01",
        "SUM_GrindingCell_CoolantJet_Stream_02",
    )
    for index, stream_name in enumerate(stream_names):
        stream = bpy.data.objects.get(stream_name)
        if stream is None:
            continue
        stream.hide_render = False
        stream.animation_data_clear()
        _replace_material(stream, stream_material)
        if stream.type == "CURVE":
            stream.data.bevel_depth *= 1.22
            stream.data.bevel_resolution = max(stream.data.bevel_resolution, 4)
            stream.data.resolution_u = max(stream.data.resolution_u, 16)
        base_scale = stream.scale.copy()
        for offset in range(frame_count):
            frame = start_frame + offset
            phase = math.tau * offset / max(frame_count - 1, 1)
            stream.scale = Vector(
                (
                    base_scale.x * (1.0 + 0.010 * math.sin(phase + index)),
                    base_scale.y * (1.0 + 0.022 * math.sin(phase + 1.2 + index)),
                    base_scale.z * (1.0 + 0.016 * math.sin(phase + 2.1 + index)),
                )
            )
            stream.keyframe_insert("scale", frame=frame)
        configured += 1

    sheet_names = (
        "SUM_GrindingCell_CoolantSplashSheet_Jet_01",
        "SUM_GrindingCell_CoolantSplashSheet_Jet_02",
    )
    for index, sheet_name in enumerate(sheet_names):
        sheet = bpy.data.objects.get(sheet_name)
        if sheet is None:
            continue
        sheet.hide_render = False
        sheet.animation_data_clear()
        _replace_material(sheet, sheet_material)
        base_scale = sheet.scale.copy()
        for offset in range(frame_count):
            frame = start_frame + offset
            phase = math.tau * offset / max(frame_count - 1, 1)
            pulse = 1.0 + 0.035 * math.sin(phase + index * 0.82)
            sheet.scale = base_scale * pulse
            sheet.keyframe_insert("scale", frame=frame)
        configured += 1

    return configured


def _configure_process_rotation(
    obj: bpy.types.Object | None,
    start_frame: int,
    frame_count: int,
    turns: float,
) -> None:
    if obj is None:
        return
    obj.animation_data_clear()
    obj.rotation_mode = "XYZ"
    raw_axis = obj.get("rotation_axis_local")
    try:
        axis = tuple(float(value) for value in raw_axis)
    except (TypeError, ValueError):
        raise ValueError(f"{obj.name} is missing rotation_axis_local")
    if len(axis) != 3:
        raise ValueError(f"{obj.name} is missing rotation_axis_local")
    axis_index = max(range(3), key=lambda index: abs(axis[index]))
    start_rotation = float(obj.delta_rotation_euler[axis_index])
    end_frame = start_frame + frame_count - 1
    obj.delta_rotation_euler[axis_index] = start_rotation
    obj.keyframe_insert(
        "delta_rotation_euler", index=axis_index, frame=start_frame
    )
    obj.delta_rotation_euler[axis_index] = start_rotation + math.tau * turns
    obj.keyframe_insert("delta_rotation_euler", index=axis_index, frame=end_frame)
    if obj.animation_data and obj.animation_data.action:
        for curve in obj.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"


def add_process_dynamics(
    scene: bpy.types.Scene, start_frame: int, frame_count: int
) -> int:
    contact = bpy.data.objects.get("SUM_ANCHOR_GrindingContact")
    if contact is None:
        raise RuntimeError("Grinding contact anchor was not found")

    collection = bpy.data.collections.new("SUM_HOLD_ProcessDynamics")
    scene.collection.children.link(collection)
    if hasattr(scene.render, "use_motion_blur"):
        scene.render.use_motion_blur = False
    _freeze_object_animation(scene, start_frame)
    hidden_artifacts = _hide_process_artifacts(scene)
    material = _copy_process_spark_material()
    contact_point = contact.matrix_world.translation.copy()
    rng = random.Random(730_301)
    spark_count = 14

    _configure_process_rotation(
        bpy.data.objects.get("SUM_GrindingCell_CBN_InternalGrindingWheel"),
        start_frame,
        frame_count,
        10.0,
    )
    _configure_process_rotation(
        bpy.data.objects.get("SUM_GrindingCell_OuterRing_Workpiece"),
        start_frame,
        frame_count,
        -2.0,
    )

    coolant_objects = _configure_process_coolant(scene, start_frame, frame_count)

    for index in range(spark_count):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1,
            radius=rng.uniform(0.0012, 0.0026),
            location=contact_point,
        )
        spark = bpy.context.active_object
        spark.name = f"SUM_HOLD_ContactSpark_{index + 1:02d}"
        _link_to_collection(spark, collection)
        spark.data.materials.append(material)
        for polygon in spark.data.polygons:
            polygon.use_smooth = True
        spark["sum_hold_role"] = "sparse_wet_grinding_contact_spark"
        spark["sum_hold_seed"] = index

        phase_offset = rng.random()
        lateral = rng.uniform(-0.018, 0.026)
        tangent = rng.uniform(-0.085, 0.10)
        lift = rng.uniform(0.045, 0.12)
        fall = rng.uniform(0.18, 0.34)
        yaw = rng.uniform(-0.35, 0.35)
        spark.rotation_euler = (rng.uniform(-0.35, 0.35), yaw, rng.uniform(-0.4, 0.4))

        for offset in range(frame_count):
            frame = start_frame + offset
            loop_progress = offset / max(frame_count - 1, 1)
            phase = (loop_progress + phase_offset) % 1.0
            local_phase = min(phase / 0.32, 1.0)
            envelope = math.sin(math.pi * local_phase) if phase < 0.32 else 0.0
            position = contact_point + Vector(
                (
                    lateral * local_phase,
                    lift * local_phase - fall * local_phase * local_phase,
                    tangent * local_phase,
                )
            )
            spark.location = position
            spark.scale = (
                max(envelope * 0.28, 0.001),
                max(envelope * 0.28, 0.001),
                max(envelope * 4.6, 0.001),
            )
            spark.keyframe_insert("location", frame=frame)
            spark.keyframe_insert("scale", frame=frame)

    return spark_count + hidden_artifacts + coolant_objects


def main() -> None:
    args = parse_args()
    if args.frame_count < 2:
        raise ValueError("frame-count must be at least 2")

    scene = bpy.context.scene
    args.output.mkdir(parents=True, exist_ok=True)
    configure_render(scene, args.mode, args.samples)
    camera_frame = args.camera_frame if args.camera_frame is not None else args.start_frame
    freeze_camera(scene, camera_frame)
    dynamic_object_count = 0
    if args.chapter in {"impact", "process"}:
        raise RuntimeError(
            f"The legacy {args.chapter} hold is rejected and disabled. Render "
            "the corresponding validated mechanical proof instead."
        )

    rendered = 0
    for output_index in range(1, args.frame_count + 1):
        output_path = args.output / f"frame-{output_index:04d}.png"
        if args.resume and output_path.exists():
            continue

        if args.end_frame is None:
            source_frame = args.start_frame + output_index - 1
        else:
            progress = (output_index - 1) / max(args.frame_count - 1, 1)
            eased = progress * progress * (3.0 - 2.0 * progress)
            source_frame = round(args.start_frame + (args.end_frame - args.start_frame) * eased)
        scene.frame_set(source_frame)
        scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        rendered += 1

    manifest = {
        "chapter": args.chapter,
        "mode": args.mode,
        "source_scene": bpy.data.filepath,
        "source_frame_start": args.start_frame,
        "source_frame_end": args.end_frame or args.start_frame + args.frame_count - 1,
        "camera_frame": camera_frame,
        "output_frames": args.frame_count,
        "rendered_this_run": rendered,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "samples": args.samples,
        "camera_frozen": True,
        "hold_dynamic_objects": dynamic_object_count,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
