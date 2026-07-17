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


def _copy_process_fluid_material() -> bpy.types.Material:
    material = bpy.data.materials.new("SUM_HOLD_CoolantDroplet_Material")
    material.use_nodes = True
    material.diffuse_color = (0.62, 0.76, 0.73, 0.48)
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        base_color = principled.inputs.get("Base Color")
        roughness = principled.inputs.get("Roughness")
        metallic = principled.inputs.get("Metallic")
        transmission = principled.inputs.get("Transmission Weight")
        alpha = principled.inputs.get("Alpha")
        if base_color:
            base_color.default_value = (0.58, 0.73, 0.70, 1.0)
        if roughness:
            roughness.default_value = 0.12
        if metallic:
            metallic.default_value = 0.0
        if transmission:
            transmission.default_value = 0.28
        if alpha:
            alpha.default_value = 0.48
    return material


def _link_to_collection(
    obj: bpy.types.Object, collection: bpy.types.Collection
) -> None:
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def add_process_dynamics(
    scene: bpy.types.Scene, start_frame: int, frame_count: int
) -> int:
    contact = bpy.data.objects.get("SUM_ANCHOR_GrindingContact")
    if contact is None:
        raise RuntimeError("Grinding contact anchor was not found")

    collection = bpy.data.collections.new("SUM_HOLD_ProcessDynamics")
    scene.collection.children.link(collection)
    material = _copy_process_fluid_material()
    contact_point = contact.matrix_world.translation.copy()
    rng = random.Random(730_301)
    droplet_count = 72

    for index in range(droplet_count):
        radius = rng.uniform(0.0018, 0.0062)
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=10,
            ring_count=6,
            radius=radius,
            location=contact_point,
        )
        droplet = bpy.context.active_object
        droplet.name = f"SUM_HOLD_CoolantDroplet_{index + 1:03d}"
        _link_to_collection(droplet, collection)
        droplet.data.materials.append(material)
        for polygon in droplet.data.polygons:
            polygon.use_smooth = True
        droplet["sum_hold_role"] = "tangential_coolant_splash_droplet"
        droplet["sum_hold_seed"] = index

        phase_offset = rng.random()
        lateral = rng.uniform(-0.14, 0.18)
        tangent = rng.uniform(-0.24, 0.28)
        lift = rng.uniform(0.06, 0.24)
        fall = rng.uniform(0.52, 0.86)
        drift = rng.uniform(-0.05, 0.05)
        aspect_y = rng.uniform(0.7, 1.15)
        aspect_z = rng.uniform(0.8, 1.35)

        for offset in range(frame_count):
            frame = start_frame + offset
            phase = ((offset / frame_count) + phase_offset) % 1.0
            envelope = math.sin(math.pi * phase) ** 0.65
            position = contact_point + Vector(
                (
                    lateral * phase + drift * math.sin(math.tau * phase),
                    lift * phase - fall * phase * phase,
                    tangent * phase + 0.035 * math.sin(math.tau * phase * 1.7),
                )
            )
            droplet.location = position
            droplet.scale = (
                max(envelope, 0.015),
                max(envelope * aspect_y, 0.015),
                max(envelope * aspect_z, 0.015),
            )
            droplet.keyframe_insert("location", frame=frame)
            droplet.keyframe_insert("scale", frame=frame)

    for stream_name in (
        "SUM_GrindingCell_CoolantJet_Stream_01",
        "SUM_GrindingCell_CoolantJet_Stream_02",
    ):
        stream = bpy.data.objects.get(stream_name)
        if stream is None:
            continue
        base_scale = stream.scale.copy()
        for offset in range(frame_count):
            frame = start_frame + offset
            phase = math.tau * offset / frame_count
            stream.scale = Vector(
                (
                    base_scale.x * (1.0 + 0.018 * math.sin(phase)),
                    base_scale.y * (1.0 + 0.045 * math.sin(phase + 1.2)),
                    base_scale.z * (1.0 + 0.035 * math.sin(phase + 2.1)),
                )
            )
            stream.keyframe_insert("scale", frame=frame)

    return droplet_count


def main() -> None:
    args = parse_args()
    if args.frame_count < 2:
        raise ValueError("frame-count must be at least 2")

    scene = bpy.context.scene
    args.output.mkdir(parents=True, exist_ok=True)
    configure_render(scene, args.mode, args.samples)
    freeze_camera(scene, args.start_frame)
    dynamic_object_count = 0
    if args.chapter == "process":
        dynamic_object_count = add_process_dynamics(
            scene, args.start_frame, args.frame_count
        )

    rendered = 0
    for output_index in range(1, args.frame_count + 1):
        output_path = args.output / f"frame-{output_index:04d}.png"
        if args.resume and output_path.exists():
            continue

        source_frame = args.start_frame + output_index - 1
        scene.frame_set(source_frame)
        scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        rendered += 1

    manifest = {
        "chapter": args.chapter,
        "mode": args.mode,
        "source_scene": bpy.data.filepath,
        "source_frame_start": args.start_frame,
        "source_frame_end": args.start_frame + args.frame_count - 1,
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
