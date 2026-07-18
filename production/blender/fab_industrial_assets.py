"""Import selected local Fab industrial assets without copying source FBX files.

The module deliberately keeps only a small, named hierarchy from each source
file. Geometry lives once in unlinked prototype collections; scene placement
uses collection instances so repeated equipment does not duplicate mesh data.
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any, Iterable

import bpy
from mathutils import Vector


MODULE_VERSION = "1.0.0"
OWNER_KEY = "fab_industrial_assets_owner"
VISIBLE_COLLECTION_NAME = "SUM_MODEL_FabIndustrialAssets"
PROTOTYPE_COLLECTION_NAME = "SUM_FAB_IndustrialPrototypes"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = PROJECT_ROOT.parent

HANDLING_PACKAGE = "FREE_Handling_Accessory_KITBASH_Set-b78db94f"
WAREHOUSE_PACKAGE = (
    "Industrial_Warehouse___Animated_Sectional_Doors___Control_Panel__Blender_"
    "-e27b7526"
)

SOURCE_SPECS = {
    "handling_accessory": {
        "package": HANDLING_PACKAGE,
        "filename": "handling_accessory_01.fbx",
        "cache": WORKSPACE_ROOT
        / "_asset-cache"
        / "fab"
        / "handling-kitbash-b78db94f"
        / "handling_accessory_01.fbx",
    },
    "warehouse": {
        "package": WAREHOUSE_PACKAGE,
        "filename": "lagerhalle.fbx",
        "cache": WORKSPACE_ROOT
        / "_asset-cache"
        / "fab"
        / "industrial-warehouse-e27b7526"
        / "lagerhalle.fbx",
    },
}

ROLE_TARGETS = {
    "handling_accessory": {"handling_accessory": "Gruzo_Kit_1126"},
    "warehouse": {
        "control_panel": "Schalter_Up_01",
        "door_track": "Track.001",
    },
}


def _vault_roots() -> list[Path]:
    roots: list[Path] = []
    configured = os.environ.get("FAB_VAULTCACHE")
    if configured:
        configured_path = Path(configured).expanduser()
        roots.append(
            configured_path / "FabLibrary"
            if configured_path.name.lower() == "vaultcache"
            else configured_path
        )

    program_data = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
    roots.append(program_data / "Epic" / "EpicGamesLauncher" / "VaultCache" / "FabLibrary")

    unique: list[Path] = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return unique


def _resolve_source(source_key: str) -> Path | None:
    spec = SOURCE_SPECS[source_key]
    candidates: list[Path] = []
    for root in _vault_roots():
        package_fbx = root / str(spec["package"]) / "fbx"
        candidates.extend(
            (
                package_fbx / "source_extracted" / str(spec["filename"]),
                package_fbx / str(spec["filename"]),
            )
        )
    candidates.append(Path(spec["cache"]))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _owned(id_block: Any) -> bool:
    try:
        return bool(id_block.get(OWNER_KEY))
    except (AttributeError, ReferenceError):
        return False


def _remove_previous_import() -> None:
    for obj in list(bpy.data.objects):
        if _owned(obj):
            bpy.data.objects.remove(obj, do_unlink=True)

    owned_collections = [collection for collection in bpy.data.collections if _owned(collection)]
    for collection in reversed(owned_collections):
        if collection.name in bpy.data.collections:
            bpy.data.collections.remove(collection)

    for data_blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.actions):
        for data_block in list(data_blocks):
            if _owned(data_block) and data_block.users == 0:
                data_blocks.remove(data_block)


def _new_collection(name: str, parent: bpy.types.Collection | None = None) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    collection[OWNER_KEY] = True
    if parent is not None:
        parent.children.link(collection)
    return collection


def _snapshot() -> dict[str, set[Any]]:
    return {
        "objects": set(bpy.data.objects),
        "meshes": set(bpy.data.meshes),
        "materials": set(bpy.data.materials),
        "images": set(bpy.data.images),
        "collections": set(bpy.data.collections),
        "actions": set(bpy.data.actions),
    }


def _new_since(snapshot: dict[str, set[Any]], kind: str, data_blocks: Any) -> list[Any]:
    return [data_block for data_block in data_blocks if data_block not in snapshot[kind]]


def _hierarchy(root: bpy.types.Object) -> list[bpy.types.Object]:
    result: list[bpy.types.Object] = []
    stack = [root]
    while stack:
        current = stack.pop()
        result.append(current)
        stack.extend(reversed(list(current.children)))
    return result


def _find_imported_object(
    imported_objects: Iterable[bpy.types.Object],
    target_name: str,
) -> bpy.types.Object | None:
    imported = list(imported_objects)
    exact = [obj for obj in imported if obj.name == target_name]
    if exact:
        return exact[0]

    # Blender appends another numeric suffix when an ID name already exists.
    suffixed = [obj for obj in imported if obj.name.startswith(f"{target_name}.")]
    return sorted(suffixed, key=lambda obj: obj.name)[0] if suffixed else None


def _move_to_collection(
    objects: Iterable[bpy.types.Object],
    destination: bpy.types.Collection,
) -> None:
    for obj in objects:
        for source_collection in list(obj.users_collection):
            source_collection.objects.unlink(obj)
        if obj.name not in destination.objects:
            destination.objects.link(obj)


def _world_bounds(objects: Iterable[bpy.types.Object]) -> tuple[Vector, Vector] | None:
    points: list[Vector] = []
    for obj in objects:
        if obj.type != "MESH" or not obj.data or not obj.bound_box:
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        return None
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return low, high


def _normalize_prototype(root: bpy.types.Object, objects: list[bpy.types.Object]) -> list[float]:
    bpy.context.view_layer.update()
    bounds = _world_bounds(objects)
    if bounds is None:
        return [0.0, 0.0, 0.0]
    low, high = bounds
    center = (low + high) * 0.5
    root.matrix_world.translation += Vector((-center.x, -center.y, -low.z))
    bpy.context.view_layer.update()
    return [round(float(value), 4) for value in (high - low)]


def _resolve_image_path(image: bpy.types.Image, source: Path) -> None:
    raw_path = Path(bpy.path.abspath(image.filepath)) if image.filepath else None
    if raw_path and raw_path.is_file():
        return

    filename = Path(image.filepath).name if image.filepath else image.name
    candidates = (
        source.parent / filename,
        source.parent / f"{source.stem}.fbm" / filename,
        source.parent / "lagerhalle.fbm" / filename,
    )
    for candidate in candidates:
        if candidate.is_file():
            image.filepath = str(candidate.resolve())
            image[OWNER_KEY] = True
            image["fab_source_file"] = str(source)
            try:
                image.reload()
            except RuntimeError:
                pass
            return


def _principled_node(material: bpy.types.Material) -> bpy.types.Node:
    material.use_nodes = True
    node_tree = material.node_tree
    if node_tree is None:
        raise RuntimeError(f"Material {material.name!r} has no node tree")

    for node in node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            return node

    output = next((node for node in node_tree.nodes if node.type == "OUTPUT_MATERIAL"), None)
    if output is None:
        output = node_tree.nodes.new("ShaderNodeOutputMaterial")
    principled = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return principled


def _set_unlinked(principled: bpy.types.Node, input_name: str, value: Any) -> None:
    socket = principled.inputs.get(input_name)
    if socket is not None and not socket.is_linked:
        socket.default_value = value


def _normalize_material(
    material: bpy.types.Material,
    role: str,
    source: Path,
) -> None:
    principled = _principled_node(material)
    material_name = material.name.lower()

    if role == "handling_accessory":
        metallic, roughness = 0.78, 0.34
    elif role == "door_track" or "tor" in material_name or "rail" in material_name:
        metallic, roughness = 0.72, 0.29
    elif "button" in material_name:
        metallic, roughness = 0.04, 0.30
    else:
        metallic, roughness = 0.16, 0.36

    # Imported color, texture and normal links are authoritative. Only tune
    # scalar PBR defaults that are not driven by an existing node connection.
    _set_unlinked(principled, "Metallic", metallic)
    _set_unlinked(principled, "Roughness", roughness)
    _set_unlinked(principled, "Alpha", 1.0)

    material[OWNER_KEY] = True
    material["fab_pbr_normalized"] = True
    material["fab_asset_role"] = role
    material["fab_source_file"] = str(source)

    if material.node_tree:
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                _resolve_image_path(node.image, source)


def _tag_and_normalize_objects(
    objects: Iterable[bpy.types.Object],
    role: str,
    source: Path,
) -> None:
    materials: set[bpy.types.Material] = set()
    for obj in objects:
        obj[OWNER_KEY] = True
        obj["fab_asset_role"] = role
        obj["fab_source_file"] = str(source)
        if obj.type == "MESH" and obj.data is not None:
            obj.data[OWNER_KEY] = True
            obj.data["fab_asset_role"] = role
            for slot in obj.material_slots:
                if slot.material is not None:
                    materials.add(slot.material)

    for material in materials:
        _normalize_material(material, role, source)


def _stats_for_objects(objects: Iterable[bpy.types.Object]) -> dict[str, Any]:
    object_list = list(objects)
    meshes = {
        obj.data
        for obj in object_list
        if obj.type == "MESH" and isinstance(obj.data, bpy.types.Mesh)
    }
    materials = {
        slot.material
        for obj in object_list
        if obj.type == "MESH"
        for slot in obj.material_slots
        if slot.material is not None
    }
    return {
        "objects": len(object_list),
        "meshes": len(meshes),
        "vertices": sum(len(mesh.vertices) for mesh in meshes),
        "polygons": sum(len(mesh.polygons) for mesh in meshes),
        "materials": len(materials),
    }


def _cleanup_new_import_data(
    snapshot: dict[str, set[Any]],
    kept_objects: set[bpy.types.Object],
) -> None:
    for obj in _new_since(snapshot, "objects", bpy.data.objects):
        if obj not in kept_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Empty importer collections can be nested. Remove leaves first.
    pending = _new_since(snapshot, "collections", bpy.data.collections)
    while pending:
        removed = False
        for collection in list(pending):
            if len(collection.objects) == 0 and len(collection.children) == 0:
                bpy.data.collections.remove(collection)
                pending.remove(collection)
                removed = True
        if not removed:
            break

    for kind, data_blocks in (
        ("meshes", bpy.data.meshes),
        ("materials", bpy.data.materials),
        ("images", bpy.data.images),
        ("actions", bpy.data.actions),
    ):
        for data_block in list(_new_since(snapshot, kind, data_blocks)):
            if data_block.users == 0:
                data_blocks.remove(data_block)


def _import_selected_hierarchies(
    source: Path,
    targets: dict[str, str],
    prototype_root: bpy.types.Collection,
) -> tuple[dict[str, dict[str, Any]], list[str], float]:
    role_collections = {
        role: _new_collection(f"SUM_FAB_PROTO_{role}", prototype_root)
        for role in targets
    }
    snapshot = _snapshot()
    started = time.perf_counter()
    warnings: list[str] = []
    imported_roles: dict[str, dict[str, Any]] = {}

    try:
        bpy.ops.object.select_all(action="DESELECT")
        result = bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False)
        if "FINISHED" not in result:
            raise RuntimeError(f"FBX importer returned {sorted(result)}")

        imported_objects = _new_since(snapshot, "objects", bpy.data.objects)
        kept_objects: set[bpy.types.Object] = set()
        for role, target_name in targets.items():
            root = _find_imported_object(imported_objects, target_name)
            if root is None:
                warnings.append(f"{source.name}: target {target_name!r} was not found")
                continue

            objects = _hierarchy(root)
            selected_set = set(objects)
            if root.parent is not None and root.parent not in selected_set:
                world_matrix = root.matrix_world.copy()
                root.parent = None
                root.matrix_world = world_matrix

            _move_to_collection(objects, role_collections[role])
            dimensions = _normalize_prototype(root, objects)
            _tag_and_normalize_objects(objects, role, source)
            role_collections[role]["fab_asset_role"] = role
            role_collections[role]["fab_source_file"] = str(source)
            kept_objects.update(objects)
            imported_roles[role] = {
                "root": root,
                "collection": role_collections[role],
                "objects": objects,
                "dimensions": dimensions,
                "stats": _stats_for_objects(objects),
            }

        _cleanup_new_import_data(snapshot, kept_objects)
    except Exception as exc:  # Keep a missing or malformed local asset non-fatal.
        warnings.append(f"{source.name}: import failed: {exc}")
        _cleanup_new_import_data(snapshot, set())
        imported_roles.clear()

    for role, collection in role_collections.items():
        if role not in imported_roles and collection.name in bpy.data.collections:
            bpy.data.collections.remove(collection)

    return imported_roles, warnings, time.perf_counter() - started


def _create_collection_instance(
    name: str,
    prototype: bpy.types.Collection,
    destination: bpy.types.Collection,
    parent: bpy.types.Object,
    location: tuple[float, float, float],
    rotation: tuple[float, float, float],
    scale: tuple[float, float, float],
    role: str,
) -> bpy.types.Object:
    instance = bpy.data.objects.new(name, None)
    destination.objects.link(instance)
    instance.parent = parent
    instance.location = location
    instance.rotation_euler = rotation
    instance.scale = scale
    instance.instance_type = "COLLECTION"
    instance.instance_collection = prototype
    instance.empty_display_type = "CUBE"
    instance.empty_display_size = 0.35
    instance[OWNER_KEY] = True
    instance["fab_asset_role"] = role
    instance["fab_linked_instance"] = True
    return instance


def _place_instances(
    imported_roles: dict[str, dict[str, Any]],
    destination: bpy.types.Collection,
    layout_root: bpy.types.Object,
) -> dict[str, list[bpy.types.Object]]:
    placements = {
        "handling_accessory": (
            ("FAB_Handling_Right", (6.25, 54.0, 2.85), (0.0, 0.0, math.pi + 0.10), (0.72,) * 3),
        ),
        "control_panel": (
            ("FAB_ControlPanel_01", (-7.55, 30.5, 1.0), (0.0, 0.0, -math.pi / 2), (0.94,) * 3),
            ("FAB_ControlPanel_02", (7.55, 62.0, 1.0), (0.0, 0.0, math.pi / 2), (0.94,) * 3),
            ("FAB_ControlPanel_Exit", (3.65, 136.0, 1.0), (0.0, 0.0, math.pi), (0.94,) * 3),
        ),
        "door_track": (
            ("FAB_SectionalDoorTrack", (0.0, 136.7, 0.0), (0.0, 0.0, 0.0), (0.47,) * 3),
        ),
    }

    instances: dict[str, list[bpy.types.Object]] = {}
    for role, role_placements in placements.items():
        role_data = imported_roles.get(role)
        if role_data is None:
            continue
        prototype = role_data["collection"]
        instances[role] = [
            _create_collection_instance(
                name,
                prototype,
                destination,
                layout_root,
                location,
                rotation,
                scale,
                role,
            )
            for name, location, rotation, scale in role_placements
        ]
    return instances


def _json_stats(imported_roles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    unique_meshes: set[bpy.types.Mesh] = set()
    objects: set[bpy.types.Object] = set()
    for role_data in imported_roles.values():
        objects.update(role_data["objects"])
        unique_meshes.update(
            obj.data
            for obj in role_data["objects"]
            if obj.type == "MESH" and isinstance(obj.data, bpy.types.Mesh)
        )
    return {
        "prototype_objects": len(objects),
        "unique_meshes": len(unique_meshes),
        "vertices": sum(len(mesh.vertices) for mesh in unique_meshes),
        "polygons": sum(len(mesh.polygons) for mesh in unique_meshes),
    }


def import_fab_industrial_assets(assets: dict[str, Any]) -> dict[str, Any]:
    """Import, isolate and instance the selected local Fab industrial assets.

    Missing source files and FBX import failures are recorded as warnings and do
    not stop the main scene build. Returned Blender IDs remain convenient for
    downstream inspection while scene custom properties store JSON-safe audit
    metadata in the saved blend file.
    """

    root_collection = assets.get("root_collection")
    layout_root = assets.get("layout_root")
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")
    if not isinstance(layout_root, bpy.types.Object):
        raise TypeError("assets must provide layout_root")

    started = time.perf_counter()
    _remove_previous_import()
    visible_collection = _new_collection(VISIBLE_COLLECTION_NAME, root_collection)
    prototype_root = _new_collection(PROTOTYPE_COLLECTION_NAME)
    prototype_root.use_fake_user = True

    sources: dict[str, str | None] = {}
    imported_roles: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    import_seconds: dict[str, float] = {}

    for source_key in ("handling_accessory", "warehouse"):
        source = _resolve_source(source_key)
        sources[source_key] = str(source) if source else None
        if source is None:
            filename = SOURCE_SPECS[source_key]["filename"]
            warnings.append(f"{source_key}: local source {filename!r} is unavailable; skipped")
            import_seconds[source_key] = 0.0
            continue

        roles, role_warnings, elapsed = _import_selected_hierarchies(
            source,
            ROLE_TARGETS[source_key],
            prototype_root,
        )
        imported_roles.update(roles)
        warnings.extend(role_warnings)
        import_seconds[source_key] = round(elapsed, 3)

    instances = _place_instances(
        imported_roles,
        visible_collection,
        layout_root,
    )
    stats = _json_stats(imported_roles)
    stats["visible_instances"] = sum(len(role_instances) for role_instances in instances.values())
    stats["import_seconds"] = import_seconds
    stats["total_seconds"] = round(time.perf_counter() - started, 3)

    expected_roles = {role for roles in ROLE_TARGETS.values() for role in roles}
    loaded_roles = set(imported_roles)
    if not loaded_roles:
        status = "skipped"
    elif loaded_roles == expected_roles and not warnings:
        status = "loaded"
    else:
        status = "partial"

    scene = bpy.context.scene
    scene["fab_industrial_assets_version"] = MODULE_VERSION
    scene["fab_industrial_assets_status"] = status
    scene["fab_industrial_asset_sources"] = json.dumps(sources, ensure_ascii=True)
    scene["fab_industrial_asset_stats"] = json.dumps(stats, ensure_ascii=True)
    scene["fab_industrial_asset_warnings"] = json.dumps(warnings, ensure_ascii=True)

    print(
        "[fab-assets] "
        f"status={status} roles={sorted(loaded_roles)} "
        f"meshes={stats['unique_meshes']} polygons={stats['polygons']} "
        f"instances={stats['visible_instances']} seconds={stats['total_seconds']}"
    )
    for warning in warnings:
        print(f"[fab-assets] warning: {warning}")

    result: dict[str, Any] = {
        "status": status,
        "collection": visible_collection,
        "prototype_collection": prototype_root,
        "prototypes": imported_roles,
        "instances": instances,
        "sources": sources,
        "stats": stats,
        "warnings": warnings,
    }
    for role, role_data in imported_roles.items():
        result[f"{role}_prototype"] = role_data["collection"]
        result[f"{role}_root"] = role_data["root"]
        result[f"{role}_instances"] = instances.get(role, [])
    return result


__all__ = ["import_fab_industrial_assets"]
