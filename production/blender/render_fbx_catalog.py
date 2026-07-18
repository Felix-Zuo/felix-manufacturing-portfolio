"""Render a neutral catalog preview for an external FBX asset pack."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args() -> argparse.Namespace:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fbx", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1800)
    parser.add_argument("--height", type=int, default=700)
    return parser.parse_args(args)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    args = parse_args()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(args.fbx.resolve()))

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("FBX has no mesh objects")
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    center = (low + high) * 0.5
    width = max(high.x - low.x, 1.0)
    height = max(high.z - low.z, 1.0)

    bpy.ops.mesh.primitive_plane_add(size=max(width * 1.5, 20.0), location=(center.x, center.y + 0.8, low.z - 0.02))
    floor = bpy.context.object
    floor.name = "CatalogFloor"
    floor_material = bpy.data.materials.new("CatalogFloorMaterial")
    floor_material.diffuse_color = (0.025, 0.03, 0.034, 1.0)
    floor.data.materials.append(floor_material)

    camera_data = bpy.data.cameras.new("CatalogCameraData")
    camera = bpy.data.objects.new("CatalogCamera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(width * args.height / args.width, height) * 1.18
    camera.location = (center.x, low.y - max(width, height) * 1.15, center.z)
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for name, location, energy, size in (
        ("CatalogKey", (center.x - width * 0.25, low.y - width * 0.45, high.z + height), 1600.0, width * 0.55),
        ("CatalogFill", (center.x + width * 0.4, low.y - width * 0.2, center.z), 900.0, width * 0.45),
        ("CatalogRim", (center.x, high.y + width * 0.25, high.z), 1300.0, width * 0.45),
    ):
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = max(size, 2.0)
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = location
        look_at(light, center)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = str(args.out.resolve())
    scene.render.film_transparent = False
    scene.world.color = (0.008, 0.01, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
