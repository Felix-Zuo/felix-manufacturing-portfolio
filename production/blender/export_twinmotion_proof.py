"""Export a validated proof scene for Twinmotion lookdev."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--family", choices=("robot", "grinding"), required=True)
    parser.add_argument(
        "--format",
        choices=("glb", "fbx"),
        help="Defaults to the output file suffix.",
    )
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _belongs_to_family(obj: bpy.types.Object, family: str) -> bool:
    prefixes = {
        "robot": ("SUM_KUKA_", "SUM_RobotCell_", "SUM_PROOF_InternalGripper_"),
        "grinding": (
            "SUM_GrindingCell_",
            "SUM_ASSET_InternalGrinding",
            "SUM_PROOF_GRIND_",
        ),
    }[family]
    cursor: bpy.types.Object | None = obj
    while cursor is not None:
        if cursor.name.startswith(prefixes):
            return True
        cursor = cursor.parent
    return False


def _export_set(scene: bpy.types.Scene, family: str) -> set[bpy.types.Object]:
    selected: set[bpy.types.Object] = set()
    for obj in scene.objects:
        if (
            obj.type not in {"MESH", "CURVE"}
            or obj.hide_render
            or not _belongs_to_family(obj, family)
        ):
            continue
        cursor: bpy.types.Object | None = obj
        while cursor is not None:
            selected.add(cursor)
            cursor = cursor.parent
    return selected


def _recenter_export(
    objects: set[bpy.types.Object], minimum: list[float], maximum: list[float]
) -> list[float]:
    center = Vector(
        tuple((minimum[axis] + maximum[axis]) * 0.5 for axis in range(3))
    )
    root = bpy.data.objects.new("SUM_TWINMOTION_EXPORT_ROOT", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = -center
    root["export_center_source_m"] = list(center)

    top_level = [obj for obj in objects if obj.parent not in objects]
    for obj in top_level:
        world = obj.matrix_world.copy()
        obj.parent = root
        obj.matrix_world = world
    objects.add(root)
    bpy.context.view_layer.update()
    return list(center)


def _bounds(objects: set[bpy.types.Object]) -> tuple[list[float], list[float]]:
    points: list[Vector] = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        return [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    return (
        [min(float(point[axis]) for point in points) for axis in range(3)],
        [max(float(point[axis]) for point in points) for axis in range(3)],
    )


def _matrix_changed(samples: list[Matrix], tolerance: float = 1.0e-6) -> bool:
    reference = samples[0]
    return any(
        abs(float(sample[row][column] - reference[row][column])) > tolerance
        for sample in samples[1:]
        for row in range(4)
        for column in range(4)
    )


def _assign_local_matrix(
    obj: bpy.types.Object,
    matrix: Matrix,
    previous_rotation: Quaternion | None = None,
) -> Quaternion:
    location, rotation, scale = matrix.decompose()
    if previous_rotation is not None:
        rotation.make_compatible(previous_rotation)
    obj.location = location
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = rotation
    obj.scale = scale
    return rotation.copy()


def _rigid_matrix(matrix: Matrix) -> tuple[Matrix, Vector]:
    """Split a world transform into rigid motion and source geometry scale."""
    location, rotation, scale = matrix.decompose()
    rigid = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
    return rigid, scale


def _scale_changed(scales: list[Vector], tolerance: float = 1.0e-5) -> bool:
    reference = scales[0]
    return any(
        abs(float(scale[axis] - reference[axis])) > tolerance
        for scale in scales[1:]
        for axis in range(3)
    )


def _flatten_world_animation(
    scene: bpy.types.Scene,
    source_objects: set[bpy.types.Object],
    center: list[float],
) -> tuple[
    set[bpy.types.Object],
    list[str],
    dict[str, list[float]],
    dict[str, dict[str, list[float]]],
]:
    """Bake inherited world motion onto independent mesh objects.

    Twinmotion accepts transform animation but is less reliable with a deep
    robotics hierarchy. Each visible mesh therefore receives the exact sampled
    world transform from the validated Blender scene. The only remaining parent
    is a static recentering root.
    """
    sources = sorted(
        (
            obj
            for obj in source_objects
            if obj.type in {"MESH", "CURVE"} and not obj.hide_render
        ),
        key=lambda obj: obj.name,
    )
    frames = list(range(scene.frame_start, scene.frame_end + 1))
    original_frame = scene.frame_current
    samples: dict[bpy.types.Object, list[Matrix]] = {obj: [] for obj in sources}
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for source in sources:
            samples[source].append(source.matrix_world.copy())

    collection = bpy.data.collections.new("SUM_TWINMOTION_FLAT_EXPORT")
    scene.collection.children.link(collection)
    root = bpy.data.objects.new("SUM_TWINMOTION_EXPORT_ROOT", None)
    collection.objects.link(root)
    root.location = -Vector(center)
    root["hierarchy_mode"] = "flattened_world_transform_animation"
    root["export_center_source_m"] = center

    export_objects: set[bpy.types.Object] = {root}
    dynamic_sources: list[str] = []
    baked_source_scales: dict[str, list[float]] = {}
    stripped_scale_animation: dict[str, dict[str, list[float]]] = {}
    for source in sources:
        duplicate = source.copy()
        duplicate.name = f"TM_FLAT_{source.name}"
        duplicate.animation_data_clear()
        duplicate.data = source.data.copy()
        duplicate.parent = root
        duplicate.matrix_parent_inverse = Matrix.Identity(4)
        duplicate.hide_render = False
        duplicate.hide_viewport = False
        duplicate["twinmotion_source_object"] = source.name
        collection.objects.link(duplicate)
        export_objects.add(duplicate)

        rigid_samples: list[Matrix] = []
        scale_samples: list[Vector] = []
        for matrix in samples[source]:
            rigid, scale = _rigid_matrix(matrix)
            rigid_samples.append(rigid)
            scale_samples.append(scale)
        source_scale = scale_samples[0]
        if _scale_changed(scale_samples):
            minimum = [
                min(float(scale[axis]) for scale in scale_samples)
                for axis in range(3)
            ]
            maximum = [
                max(float(scale[axis]) for scale in scale_samples)
                for axis in range(3)
            ]
            source_scale = Vector(
                tuple(
                    max(abs(minimum[axis]), abs(maximum[axis]))
                    * (-1.0 if scale_samples[0][axis] < 0.0 else 1.0)
                    for axis in range(3)
                )
            )
            stripped_scale_animation[source.name] = {
                "minimum": minimum,
                "maximum": maximum,
                "replacement": [float(value) for value in source_scale],
            }
        duplicate.data.transform(
            Matrix.Diagonal(
                (source_scale.x, source_scale.y, source_scale.z, 1.0)
            )
        )
        duplicate["baked_source_world_scale"] = list(source_scale)
        if any(abs(float(value) - 1.0) > 1.0e-6 for value in source_scale):
            baked_source_scales[source.name] = [
                float(value) for value in source_scale
            ]

        if not _matrix_changed(rigid_samples):
            _assign_local_matrix(duplicate, rigid_samples[0])
            continue

        dynamic_sources.append(source.name)
        previous_rotation: Quaternion | None = None
        for frame, matrix in zip(frames, rigid_samples):
            previous_rotation = _assign_local_matrix(
                duplicate, matrix, previous_rotation
            )
            duplicate.keyframe_insert("location", frame=frame)
            duplicate.keyframe_insert("rotation_quaternion", frame=frame)
        if duplicate.animation_data and duplicate.animation_data.action:
            for curve in duplicate.animation_data.action.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation = "LINEAR"

    scene.frame_set(original_frame)
    bpy.context.view_layer.update()
    root["stripped_scale_animation_count"] = len(stripped_scale_animation)
    return (
        export_objects,
        dynamic_sources,
        baked_source_scales,
        stripped_scale_animation,
    )


def _ensure_export_uvs(objects: set[bpy.types.Object]) -> list[str]:
    """Give texture-bearing proof meshes a deterministic box-projected UV set."""
    updated: list[str] = []
    visited: set[int] = set()
    for obj in sorted(objects, key=lambda item: item.name):
        if obj.type != "MESH" or not obj.data.materials:
            continue
        mesh = obj.data
        mesh_pointer = mesh.as_pointer()
        if mesh_pointer in visited:
            continue
        visited.add(mesh_pointer)
        if mesh.uv_layers:
            continue

        uv_layer = mesh.uv_layers.new(name="UVMap")
        for polygon in mesh.polygons:
            dominant_axis = max(
                range(3), key=lambda axis: abs(float(polygon.normal[axis]))
            )
            for loop_index in polygon.loop_indices:
                coordinate = mesh.vertices[
                    mesh.loops[loop_index].vertex_index
                ].co
                if dominant_axis == 0:
                    uv = (float(coordinate.y), float(coordinate.z))
                elif dominant_axis == 1:
                    uv = (float(coordinate.x), float(coordinate.z))
                else:
                    uv = (float(coordinate.x), float(coordinate.y))
                uv_layer.data[loop_index].uv = uv
        mesh.update()
        updated.append(mesh.name)
    return updated


def _inspect_glb(path: Path) -> dict[str, object]:
    """Reject exports Twinmotion cannot parse before they reach its UI."""
    payload = path.read_bytes()
    if len(payload) < 20 or payload[:4] != b"glTF":
        raise RuntimeError(f"Invalid GLB header: {path}")
    _, version, declared_length = struct.unpack_from("<4sII", payload, 0)
    if version != 2 or declared_length != len(payload):
        raise RuntimeError(
            f"Invalid GLB envelope: version={version}, "
            f"declared={declared_length}, actual={len(payload)}"
        )
    json_length, json_type = struct.unpack_from("<II", payload, 12)
    if json_type != 0x4E4F534A:
        raise RuntimeError("GLB does not begin with a JSON chunk")
    document = json.loads(payload[20 : 20 + json_length].decode("utf-8"))

    textured_materials: dict[int, set[int]] = {}
    texture_slots = (
        "baseColorTexture",
        "metallicRoughnessTexture",
        "normalTexture",
        "occlusionTexture",
        "emissiveTexture",
    )
    for material_index, material in enumerate(document.get("materials", [])):
        required_texcoords: set[int] = set()
        containers = [material, material.get("pbrMetallicRoughness", {})]
        for container in containers:
            for slot in texture_slots:
                texture_info = container.get(slot)
                if isinstance(texture_info, dict) and "index" in texture_info:
                    required_texcoords.add(int(texture_info.get("texCoord", 0)))
        if required_texcoords:
            textured_materials[material_index] = required_texcoords

    missing_texcoords: list[str] = []
    for mesh_index, mesh in enumerate(document.get("meshes", [])):
        for primitive_index, primitive in enumerate(mesh.get("primitives", [])):
            material_index = primitive.get("material")
            required = textured_materials.get(material_index, set())
            attributes = primitive.get("attributes", {})
            for texcoord in sorted(required):
                attribute = f"TEXCOORD_{texcoord}"
                if attribute not in attributes:
                    missing_texcoords.append(
                        f"mesh[{mesh_index}].primitive[{primitive_index}].{attribute}"
                    )

    animations = document.get("animations", [])
    if len(animations) != 1:
        raise RuntimeError(
            "Twinmotion proof exports must contain exactly one scene animation; "
            f"found {len(animations)}"
        )
    channel_count = len(animations[0].get("channels", []))
    if channel_count == 0:
        raise RuntimeError("Twinmotion proof export has no animation channels")
    if missing_texcoords:
        raise RuntimeError(
            "Twinmotion proof export has textured primitives without UVs: "
            + ", ".join(missing_texcoords[:12])
        )
    return {
        "version": version,
        "animation_count": len(animations),
        "animation_name": animations[0].get("name", ""),
        "animation_channel_count": channel_count,
        "mesh_count": len(document.get("meshes", [])),
        "material_count": len(document.get("materials", [])),
        "missing_texcoord_count": len(missing_texcoords),
    }


def _inspect_fbx(path: Path) -> dict[str, object]:
    """Apply a lightweight envelope gate before the file reaches Twinmotion."""
    payload = path.read_bytes()
    binary_header = b"Kaydara FBX Binary  \x00\x1a\x00"
    if not payload.startswith(binary_header):
        raise RuntimeError(f"Invalid binary FBX header: {path}")
    if len(payload) < 1_000_000:
        raise RuntimeError(
            f"FBX proof export is unexpectedly small: {len(payload)} bytes"
        )
    return {
        "encoding": "binary",
        "byte_length": len(payload),
        "header": "Kaydara FBX Binary",
    }


def main() -> None:
    args = _args()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    export_format = (args.format or args.output.suffix.lstrip(".")).lower()
    if export_format not in {"glb", "fbx"}:
        raise RuntimeError(
            "Export format must be provided with --format or a .glb/.fbx suffix"
        )
    scene = bpy.context.scene
    scene.frame_set(scene.frame_start)
    bpy.context.view_layer.update()

    export_objects = _export_set(scene, args.family)
    if not export_objects:
        raise RuntimeError("No visible proof geometry was found")
    minimum, maximum = _bounds(export_objects)
    center = [
        (minimum[axis] + maximum[axis]) * 0.5 for axis in range(3)
    ]
    flattened_dynamic: list[str] = []
    baked_source_scales: dict[str, list[float]] = {}
    stripped_scale_animation: dict[str, dict[str, list[float]]] = {}
    hierarchy_mode = "source_hierarchy"
    if args.family == "robot":
        (
            export_objects,
            flattened_dynamic,
            baked_source_scales,
            stripped_scale_animation,
        ) = _flatten_world_animation(scene, export_objects, center)
        hierarchy_mode = "flattened_world_transform_animation"
    else:
        center = _recenter_export(export_objects, minimum, maximum)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in export_objects:
        obj.select_set(True)

    generated_uv_meshes = _ensure_export_uvs(export_objects)
    animated = sorted(
        obj.name for obj in export_objects if obj.animation_data is not None
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    format_gate: dict[str, object]
    if export_format == "glb":
        bpy.ops.export_scene.gltf(
            filepath=str(args.output),
            export_format="GLB",
            use_selection=True,
            export_animations=True,
            export_animation_mode="SCENE",
            export_anim_scene_split_object=False,
            export_nla_strips_merged_animation_name=f"SUM_{args.asset_id}_Loop",
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
        format_gate = _inspect_glb(args.output)
    else:
        bpy.ops.export_scene.fbx(
            filepath=str(args.output),
            use_selection=True,
            object_types={"MESH", "EMPTY", "OTHER"},
            apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_UNITS",
            use_space_transform=True,
            axis_forward="-Z",
            axis_up="Y",
            use_mesh_modifiers=True,
            mesh_smooth_type="FACE",
            use_tspace=True,
            use_custom_props=True,
            add_leaf_bones=False,
            bake_anim=True,
            bake_anim_use_all_bones=False,
            bake_anim_use_nla_strips=False,
            bake_anim_use_all_actions=False,
            bake_anim_force_startend_keying=True,
            bake_anim_step=1.0,
            bake_anim_simplify_factor=0.0,
            path_mode="COPY",
            embed_textures=True,
        )
        format_gate = _inspect_fbx(args.output)

    report = {
        "status": "exported",
        "asset_id": args.asset_id,
        "family": args.family,
        "format": export_format,
        "source_scene": bpy.data.filepath,
        "output": str(args.output),
        "frames": [scene.frame_start, scene.frame_end],
        "fps": scene.render.fps,
        "selected_object_count": len(export_objects),
        "animated_object_count": len(animated),
        "animated_objects": animated,
        "hierarchy_mode": hierarchy_mode,
        "flattened_dynamic_source_count": len(flattened_dynamic),
        "flattened_dynamic_sources": flattened_dynamic,
        "baked_source_scale_count": len(baked_source_scales),
        "baked_source_scales": baked_source_scales,
        "stripped_scale_animation_count": len(stripped_scale_animation),
        "stripped_scale_animation": stripped_scale_animation,
        "generated_uv_mesh_count": len(generated_uv_meshes),
        "generated_uv_meshes": generated_uv_meshes,
        "format_gate": format_gate,
        "bounds_min_m": minimum,
        "bounds_max_m": maximum,
        "export_center_source_m": center,
        "twinmotion_role": "mechanically validated source; materials and lighting require visual approval",
    }
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SUM_TWINMOTION_EXPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
