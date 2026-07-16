"""Replace the procedural AGV with the licensed DFKI MiR100 visual meshes."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import bpy
from mathutils import Matrix

import modeling


ROOT = Path(__file__).resolve().parents[2]
VENDOR_ROOT = ROOT / "production" / "vendor" / "dfki-mir100"
VISUAL_ROOT = VENDOR_ROOT / "meshes" / "visual"
UPSTREAM_COMMIT = "7d9c72942d512b191f2b326ca89c066710db4e34"
MODEL_COLLECTION = "SUM_MODEL_DFKI_MiR100"

DRIVE_WHEEL_RADIUS = 0.0625
DRIVE_WHEEL_Y = 0.222604
BODY_X_OFFSET = 0.037646
CASTER_Z = DRIVE_WHEEL_RADIUS - (-0.094)


def _parent_chain(obj: bpy.types.Object):
    cursor: bpy.types.Object | None = obj
    while cursor is not None:
        yield cursor
        cursor = cursor.parent


def _descendants(root: bpy.types.Object) -> list[bpy.types.Object]:
    return [
        obj
        for obj in bpy.context.scene.objects
        if any(parent is root for parent in _parent_chain(obj))
    ]


def _hide_proxy_agv(assets: dict[str, Any]) -> None:
    proxy = assets.get("agv")
    if not isinstance(proxy, bpy.types.Object):
        return
    proxy.hide_render = True
    proxy["sum_export_exclude"] = True
    proxy["sum_replaced_by"] = "DFKI MiR100 visual geometry"
    for obj in _descendants(proxy):
        obj.hide_render = True
        obj["sum_export_exclude"] = True
        obj["sum_replaced_by"] = "DFKI MiR100 visual geometry"


def _move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for current in tuple(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def _reset_model_collection(parent: bpy.types.Collection) -> bpy.types.Collection:
    existing = bpy.data.collections.get(MODEL_COLLECTION)
    if existing is not None:
        owned_data = [
            obj.data for obj in existing.all_objects if getattr(obj, "data", None) is not None
        ]
        modeling._remove_collection_tree(existing)
        for datablock in owned_data:
            if datablock.users == 0 and isinstance(datablock, bpy.types.Mesh):
                bpy.data.meshes.remove(datablock)
    return modeling._child_collection(parent, MODEL_COLLECTION)


def _import_stl(
    filename: str,
    name: str,
    parent: bpy.types.Object,
    collection: bpy.types.Collection,
    material: bpy.types.Material,
    *,
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    role: str,
) -> bpy.types.Object:
    path = VISUAL_ROOT / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing MiR100 visual mesh: {path}")

    before_objects = set(bpy.data.objects)
    result = bpy.ops.wm.stl_import(filepath=str(path), use_scene_unit=True)
    if "FINISHED" not in result:
        raise RuntimeError(f"STL import failed for {path.name}: {result}")
    imported = [obj for obj in bpy.data.objects if obj not in before_objects]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh object imported from {path.name}")

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        _move_to_collection(obj, collection)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    joined = meshes[0]
    joined.name = name
    joined.data.name = f"{name}_Mesh"
    joined.parent = parent
    joined.matrix_parent_inverse = Matrix.Identity(4)
    joined.location = location
    joined.rotation_mode = "XYZ"
    joined.rotation_euler = rotation
    joined.data.materials.clear()
    joined.data.materials.append(material)
    for polygon in joined.data.polygons:
        polygon.use_smooth = True
    joined["lookdev_role"] = "dark_metal" if "wheel" in role or "scanner" in role else "architecture"
    joined["sum_part_role"] = role
    joined["source_package"] = "DFKI-NI/mir_robot:mir_description"
    joined["source_commit"] = UPSTREAM_COMMIT
    joined["source_mesh"] = filename
    joined["triangle_count"] = sum(max(len(poly.vertices) - 2, 1) for poly in joined.data.polygons)
    bpy.ops.object.select_all(action="DESELECT")
    return joined


def _build_payload_fixture(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> tuple[bpy.types.Object, bpy.types.Object]:
    deck = modeling._box(
        "SUM_MiR100_PayloadDeck",
        (0.66, 0.46, 0.055),
        collection,
        location=(0.015, 0.0, 0.405),
        parent=root,
        material=materials["brushed_steel"],
        bevel=0.015,
        role="agv_precision_payload_deck",
    )
    deck["lookdev_role"] = "brushed_metal"

    for index, x in enumerate((-0.19, 0.19), start=1):
        cradle = modeling._box(
            f"SUM_MiR100_RingCradle_{index:02d}",
            (0.055, 0.30, 0.09),
            collection,
            location=(x, 0.0, 0.475),
            parent=root,
            material=materials["black_oxide"],
            bevel=0.012,
            role="agv_ring_transport_cradle",
        )
        cradle["lookdev_role"] = "dark_metal"

    output_nest = modeling._cylinder_between(
        "SUM_MiR100_OutputNestBase",
        (0.0, 0.0, 0.436),
        (0.0, 0.0, 0.462),
        0.145,
        collection,
        parent=root,
        material=materials["black_oxide"],
        segments=64,
        bevel=0.006,
        role="agv_flat_ring_output_nest",
    )
    output_nest["lookdev_role"] = "dark_metal"
    output_nest["handling_orientation"] = "finished outer ring flat, axis vertical"
    for index in range(3):
        angle = math.tau * index / 3.0
        pad = modeling._box(
            f"SUM_MiR100_OutputNestPad_{index + 1:02d}",
            (0.042, 0.026, 0.028),
            collection,
            location=(math.cos(angle) * 0.080, math.sin(angle) * 0.080, 0.476),
            rotation=(0.0, 0.0, angle),
            parent=root,
            material=materials["rubber"],
            bevel=0.005,
            role="agv_nonmarking_output_nest_pad",
        )
        pad["lookdev_role"] = "rubber"

    pallet_locator = modeling._empty(
        "SUM_MiR100_PalletLocator",
        collection,
        location=(0.0, 0.0, 0.58),
        parent=root,
        display_size=0.055,
    )
    pallet_locator["sum_part_role"] = "agv_inbound_workpiece_locator"
    output_locator = modeling._empty(
        "SUM_MiR100_OutputLocator",
        collection,
        location=(0.0, 0.0, 0.58),
        parent=root,
        display_size=0.055,
    )
    output_locator["sum_part_role"] = "agv_outbound_workpiece_locator"
    return pallet_locator, output_locator


def replace_agv(assets: dict[str, Any]) -> dict[str, Any]:
    """Install a URDF-positioned MiR100 and preserve the V8 handoff contract."""

    root_collection = assets.get("root_collection")
    layout_root = assets.get("layout_root")
    materials = assets.get("placeholder_materials")
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")
    if not isinstance(layout_root, bpy.types.Object):
        raise TypeError("assets must provide layout_root")
    if not isinstance(materials, dict):
        raise TypeError("assets must provide placeholder_materials")

    for filename in ("mir_100_base.stl", "wheel.stl", "caster_wheel_base.stl", "sick_lms-100.stl"):
        if not (VISUAL_ROOT / filename).exists():
            raise FileNotFoundError(f"Incomplete MiR100 source package: {filename}")

    _hide_proxy_agv(assets)
    collection = _reset_model_collection(root_collection)
    root = modeling._empty(
        "SUM_ASSET_DFKI_MiR100_AGV07",
        collection,
        location=(0.0, 7.2, 0.0),
        rotation=(0.0, 0.0, math.pi * 0.5),
        parent=layout_root,
        display_size=0.20,
    )
    root["sum_asset_type"] = "licensed_autonomous_mobile_robot"
    root["vehicle_number"] = "07"
    root["route"] = "painted_floor_route_no_raised_rail"
    root["manufacturer_geometry"] = "MiR100 visual model from DFKI mir_robot"
    root["source_repository"] = "https://github.com/DFKI-NI/mir_robot"
    root["source_commit"] = UPSTREAM_COMMIT
    root["license"] = "BSD-3-Clause"
    root["agv_drive_wheel_radius_m"] = DRIVE_WHEEL_RADIUS

    body = _import_stl(
        "mir_100_base.stl",
        "SUM_MiR100_BaseVisual",
        root,
        collection,
        materials["factory_wall"],
        location=(BODY_X_OFFSET, 0.0, 0.0),
        role="licensed_agv_body_visual",
    )
    body["lookdev_role"] = "architecture"

    drive_wheels: list[bpy.types.Object] = []
    for side, y in (("Left", DRIVE_WHEEL_Y), ("Right", -DRIVE_WHEEL_Y)):
        wheel = _import_stl(
            "wheel.stl",
            f"SUM_AGV07_ProtectedWheel_{side}",
            root,
            collection,
            materials["rubber"],
            location=(0.0, y, DRIVE_WHEEL_RADIUS),
            role="agv_recessed_protected_drive_wheel",
        )
        wheel["lookdev_role"] = "rubber"
        wheel["sum_animation_wheel_radius_m"] = DRIVE_WHEEL_RADIUS
        drive_wheels.append(wheel)

    casters: list[bpy.types.Object] = []
    for label, x, y in (
        ("FL", 0.341346, 0.203),
        ("FR", 0.341346, -0.203),
        ("BL", -0.270154, 0.203),
        ("BR", -0.270154, -0.203),
    ):
        caster_root = modeling._empty(
            f"SUM_MiR100_Caster_{label}_Axis",
            collection,
            location=(x, y, CASTER_Z),
            parent=root,
            display_size=0.025,
        )
        _import_stl(
            "caster_wheel_base.stl",
            f"SUM_MiR100_Caster_{label}_Fork",
            caster_root,
            collection,
            materials["machined_steel"],
            role="agv_caster_fork",
        )["lookdev_role"] = "brushed_metal"
        caster_wheel = _import_stl(
            "wheel.stl",
            f"SUM_MiR100_Caster_{label}_Wheel",
            caster_root,
            collection,
            materials["rubber"],
            location=(-0.0382, 0.0, -0.094),
            role="agv_passive_caster_wheel",
        )
        caster_wheel["lookdev_role"] = "rubber"
        casters.append(caster_root)

    scanners: list[bpy.types.Object] = []
    for label, location, heading in (
        ("Front", (0.4288, 0.2358, 0.1914), math.pi * 0.25),
        ("Rear", (-0.3548, -0.2352, 0.1914), -math.pi * 0.75),
    ):
        scanner_frame = modeling._empty(
            f"SUM_MiR100_{label}ScannerFrame",
            collection,
            location=location,
            rotation=(0.0, 0.0, heading),
            parent=root,
            display_size=0.03,
        )
        scanner = _import_stl(
            "sick_lms-100.stl",
            f"SUM_MiR100_{label}SafetyScanner",
            scanner_frame,
            collection,
            materials["screen_frame"],
            rotation=(math.pi, 0.0, 0.0),
            role="agv_safety_laser_scanner",
        )
        scanner["lookdev_role"] = "dark_metal"
        scanners.append(scanner)

    for end, x in (("Front", 0.445), ("Rear", -0.365)):
        strip = modeling._box(
            f"SUM_MiR100_{end}StatusStrip",
            (0.022, 0.34, 0.025),
            collection,
            location=(x, 0.0, 0.285),
            parent=root,
            material=materials["indicator_green"],
            bevel=0.006,
            role="agv_directional_status_light_strip",
        )
        strip["lookdev_role"] = "luminaire"

    number_plate = modeling._text_label(
        "SUM_MiR100_FleetNumber",
        "07",
        0.105,
        collection,
        location=(-0.42, 0.0, 0.245),
        rotation=(math.pi * 0.5, 0.0, -math.pi * 0.5),
        parent=root,
        material=materials["factory_wall"],
        role="agv_fleet_number_plate",
    )
    number_plate["lookdev_role"] = "architecture"
    pallet_locator, output_locator = _build_payload_fixture(root, collection, materials)

    root["visual_mesh_triangles"] = sum(
        int(obj.get("triangle_count", 0))
        for obj in (body, *drive_wheels, *scanners)
    )
    root["foreground_asset_gate"] = "licensed body, URDF wheel/sensor transforms, project payload"
    assets["agv"] = root
    assets["agv_07"] = root
    assets["agv_drive_wheels"] = drive_wheels
    assets["agv_casters"] = casters
    assets["agv_scanners"] = scanners
    assets["agv_pallet_locator"] = pallet_locator
    assets["agv_output_locator"] = output_locator
    assets.setdefault("anchors", {})["agv_pallet"] = pallet_locator
    assets["anchors"]["agv_output"] = output_locator
    assets.setdefault("collections", {})["agv"] = collection
    bpy.context.view_layer.update()
    return assets
