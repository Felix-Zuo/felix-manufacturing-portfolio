"""Build a minimal animated scale probe for Twinmotion's glTF importer."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def _material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.metallic = 0.35
    material.roughness = 0.3
    return material


def _cube(
    name: str,
    location: tuple[float, float, float],
    material: bpy.types.Material,
    *,
    mesh_size: float = 1.0,
    node_scale: float = 1.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=mesh_size, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (node_scale, node_scale, node_scale)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("ProbeBevel", "BEVEL")
    bevel.width = 0.055
    bevel.segments = 3
    return obj


def _animate(obj: bpy.types.Object) -> None:
    origin = obj.location.copy()
    poses = (
        (1, origin, 0.0),
        (72, origin + Vector((0.0, 2.0, 0.75)), 1.57079632679),
        (144, origin, 0.0),
    )
    obj.rotation_mode = "XYZ"
    for frame, location, angle in poses:
        obj.location = location
        obj.rotation_euler = (0.0, 0.0, angle)
        obj.keyframe_insert(data_path="location", frame=frame)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    if obj.animation_data and obj.animation_data.action:
        for curve in obj.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"


def _world_dimensions(obj: bpy.types.Object) -> list[float]:
    bpy.context.view_layer.update()
    return [round(float(value), 6) for value in obj.dimensions]


def _inspect_glb(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    if payload[:4] != b"glTF":
        raise RuntimeError("Scale probe export is not a GLB file")
    _, version, declared_length = struct.unpack_from("<4sII", payload, 0)
    if version != 2 or declared_length != len(payload):
        raise RuntimeError("Scale probe GLB envelope is invalid")
    json_length, json_type = struct.unpack_from("<II", payload, 12)
    if json_type != 0x4E4F534A:
        raise RuntimeError("Scale probe GLB has no leading JSON chunk")
    document = json.loads(payload[20 : 20 + json_length].decode("utf-8"))
    animations = document.get("animations", [])
    return {
        "mesh_count": len(document.get("meshes", [])),
        "node_count": len(document.get("nodes", [])),
        "animation_count": len(animations),
        "animation_channel_count": sum(
            len(animation.get("channels", [])) for animation in animations
        ),
        "named_nodes": [node.get("name", "") for node in document.get("nodes", [])],
    }


def main() -> None:
    args = _args()
    output = args.output.resolve()
    blend = args.blend.resolve()
    report_path = args.report.resolve()
    for path in (output, blend, report_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    _clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.frame_start = 1
    scene.frame_end = 144
    scene.render.fps = 24

    dark = _material("Probe_Dark", (0.025, 0.035, 0.045, 1.0))
    amber = _material("Probe_Amber", (0.95, 0.42, 0.04, 1.0))
    cyan = _material("Probe_Cyan", (0.02, 0.62, 0.82, 1.0))
    green = _material("Probe_Green", (0.04, 0.72, 0.34, 1.0))
    magenta = _material("Probe_Magenta", (0.75, 0.08, 0.42, 1.0))
    white = _material("Probe_White", (0.72, 0.76, 0.8, 1.0))

    floor = _cube("TM_PROBE_FLOOR_24M", (0.0, 1.0, -0.1), dark, mesh_size=1.0)
    floor.dimensions = (24.0, 6.0, 0.2)
    bpy.context.view_layer.objects.active = floor
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    variants = (
        ("APPLIED_1M", -8.0, 1.0, 1.0, amber),
        ("INCH_NODE_1M", -4.0, 39.37007874, 0.0254, cyan),
        ("INCH_INVERSE_1M", 0.0, 0.0254, 39.37007874, green),
        ("CM_NODE_1M", 4.0, 100.0, 0.01, magenta),
        ("CM_INVERSE_1M", 8.0, 0.01, 100.0, white),
    )

    probe_objects: list[bpy.types.Object] = []
    manifest: list[dict[str, object]] = []
    for label, x, mesh_size, node_scale, material in variants:
        pedestal = _cube(
            f"TM_PROBE_STATIC_BASE_{label}",
            (x, 0.0, 0.1),
            material,
            mesh_size=1.0,
        )
        pedestal.dimensions = (1.5, 1.5, 0.2)
        bpy.context.view_layer.objects.active = pedestal
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        animated = _cube(
            f"TM_PROBE_ANIM_{label}",
            (x, 0.0, 0.7),
            material,
            mesh_size=mesh_size,
            node_scale=node_scale,
        )
        expected = _world_dimensions(animated)
        if any(abs(value - 1.0) > 1.0e-4 for value in expected):
            raise RuntimeError(f"{label} is not one metre in Blender: {expected}")
        animated["probe_variant"] = label
        animated["mesh_size_m"] = mesh_size
        animated["node_scale"] = node_scale
        _animate(animated)
        probe_objects.append(animated)
        manifest.append(
            {
                "variant": label,
                "mesh_size_m": mesh_size,
                "node_scale": node_scale,
                "world_dimensions_m": expected,
                "x_m": x,
            }
        )

    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLB",
        use_selection=True,
        export_animations=True,
        export_animation_mode="SCENE",
        export_anim_scene_split_object=False,
        export_nla_strips_merged_animation_name="SUM_TwinmotionScaleProbe_Loop",
        export_frame_range=True,
        export_frame_step=1,
        export_force_sampling=True,
        export_bake_animation=True,
        export_optimize_animation_size=False,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_extras=True,
        export_yup=True,
        export_apply=False,
    )

    gate = _inspect_glb(output)
    if gate["animation_count"] != 1 or gate["animation_channel_count"] < 10:
        raise RuntimeError(f"Scale probe animation gate failed: {gate}")

    report = {
        "status": "exported",
        "output": str(output),
        "blend": str(blend),
        "frames": [scene.frame_start, scene.frame_end],
        "fps": scene.render.fps,
        "variants": manifest,
        "format_gate": gate,
        "visual_gate": (
            "All five animated cubes must match their 1 m static pedestals in "
            "Twinmotion. Any giant or tiny cube identifies the failing node-scale encoding."
        ),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SUM_TWINMOTION_SCALE_PROBE=" + json.dumps(report))


if __name__ == "__main__":
    main()
