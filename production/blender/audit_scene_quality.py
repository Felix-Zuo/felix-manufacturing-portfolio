"""Audit visible mesh and material quality at the portfolio's key camera frames."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


KEY_FRAMES = (1, 84, 132, 169, 228, 301, 433, 553, 673, 793, 877, 904)


def parse_args() -> argparse.Namespace:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(args)


def material_stats(material: bpy.types.Material) -> dict[str, object]:
    nodes = list(material.node_tree.nodes) if material.use_nodes and material.node_tree else []
    image_nodes = [node for node in nodes if node.type == "TEX_IMAGE"]
    images = sorted({node.image.name for node in image_nodes if node.image})
    principled = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)

    def input_value(name: str) -> object | None:
        if principled is None or name not in principled.inputs:
            return None
        value = principled.inputs[name].default_value
        if hasattr(value, "__len__"):
            return [round(float(component), 4) for component in value]
        return round(float(value), 4)

    return {
        "image_count": len(images),
        "images": images,
        "metallic": input_value("Metallic"),
        "node_count": len(nodes),
        "normal_linked": bool(
            principled
            and "Normal" in principled.inputs
            and principled.inputs["Normal"].is_linked
        ),
        "roughness": input_value("Roughness"),
    }


def object_stats(obj: bpy.types.Object) -> dict[str, object]:
    mesh = obj.data
    materials = [slot.material.name for slot in obj.material_slots if slot.material]
    return {
        "materials": materials,
        "name": obj.name,
        "polygons": len(mesh.polygons),
        "vertices": len(mesh.vertices),
    }


def visible_in_camera(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    obj: bpy.types.Object,
) -> bool:
    if obj.hide_render or obj.type != "MESH":
        return False
    points = [
        world_to_camera_view(scene, camera, obj.matrix_world @ Vector(corner))
        for corner in obj.bound_box
    ]
    return any(point.z > 0 and -0.05 <= point.x <= 1.05 and -0.05 <= point.y <= 1.05 for point in points)


def main() -> None:
    args = parse_args()
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("Scene has no active camera")

    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    materials = [material for material in bpy.data.materials if material.users > 0]
    material_report = {material.name: material_stats(material) for material in materials}

    frames: dict[str, object] = {}
    for frame in KEY_FRAMES:
        scene.frame_set(frame)
        visible = [object_stats(obj) for obj in meshes if visible_in_camera(scene, camera, obj)]
        visible.sort(key=lambda item: int(item["polygons"]), reverse=True)
        material_names = Counter(name for item in visible for name in item["materials"])
        textured = sum(
            count
            for name, count in material_names.items()
            if material_report.get(name, {}).get("image_count", 0)
        )
        frames[str(frame)] = {
            "camera": camera.name,
            "mesh_count": len(visible),
            "polygon_count": sum(int(item["polygons"]) for item in visible),
            "textured_material_uses": textured,
            "top_meshes": visible[:40],
        }

    report = {
        "file": bpy.data.filepath,
        "frame_end": scene.frame_end,
        "frame_start": scene.frame_start,
        "frames": frames,
        "materials": material_report,
        "summary": {
            "image_texture_materials": sum(
                1 for item in material_report.values() if item["image_count"]
            ),
            "mesh_count": len(meshes),
            "material_count": len(materials),
            "total_polygons": sum(len(obj.data.polygons) for obj in meshes),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
