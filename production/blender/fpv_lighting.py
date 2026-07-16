"""Shot lighting and material-readable grade for the V7 industrial FPV master."""

from __future__ import annotations

import math
import json
from typing import Any

import bpy
from mathutils import Vector


COLLECTION_NAME = "SUM_FPV_LIGHTING"


def _film(coordinate: tuple[float, float, float]) -> Vector:
    x, travel, up = coordinate
    return Vector((x, up, -travel))


def _aim_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    if direction.length <= 1.0e-6:
        return
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _reset_collection() -> bpy.types.Collection:
    old = bpy.data.collections.get(COLLECTION_NAME)
    if old is not None:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for parent in list(bpy.data.collections):
            if old.name in {child.name for child in parent.children}:
                parent.children.unlink(old)
        bpy.data.collections.remove(old)
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    return collection


def _principled(material_name: str) -> Any | None:
    material = bpy.data.materials.get(material_name)
    if material is None or not material.use_nodes or material.node_tree is None:
        return None
    return next(
        (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
        None,
    )


def _set_material_color(material_name: str, color: tuple[float, float, float, float]) -> None:
    shader = _principled(material_name)
    if shader is not None and shader.inputs.get("Base Color") is not None:
        shader.inputs["Base Color"].default_value = color


def _set_material_scalar(material_name: str, sockets: tuple[str, ...], value: float) -> None:
    shader = _principled(material_name)
    if shader is None:
        return
    for name in sockets:
        socket = shader.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def _set_light_energy(obj: bpy.types.Object, scale: float) -> None:
    """Scale a lookdev light from its authored energy without compounding."""

    if obj.type != "LIGHT":
        return
    data = obj.data
    original_key = "sum_fpv_authored_energy"
    if original_key not in data:
        data[original_key] = float(data.energy)
    data.energy = float(data[original_key]) * scale


def _grade_abrasive() -> None:
    """Keep the wheel recognisably CBN without turning it into a mint beacon."""

    material = bpy.data.materials.get("LD_CBN_Profiled_Abrasive")
    if material is None or not material.use_nodes or material.node_tree is None:
        return
    ramp = next(
        (node for node in material.node_tree.nodes if node.type == "VALTORGB"),
        None,
    )
    if ramp is None:
        return
    elements = sorted(ramp.color_ramp.elements, key=lambda item: item.position)
    colors = (
        (0.006, 0.014, 0.013, 1.0),
        (0.022, 0.050, 0.044, 1.0),
        (0.070, 0.120, 0.102, 1.0),
    )
    for element, color in zip(elements, colors, strict=False):
        element.color = color


def _area_light(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    target: tuple[float, float, float],
    *,
    color: tuple[float, float, float],
    energy: float,
    size: float,
    size_y: float,
) -> bpy.types.Object:
    data = bpy.data.lights.new(f"{name}_Data", type="AREA")
    data.shape = "RECTANGLE"
    data.color = color
    data.energy = energy
    data.size = size
    data.size_y = size_y
    data.use_shadow = True
    data.diffuse_factor = 1.0
    data.specular_factor = 1.0
    if hasattr(data, "normalize"):
        data.normalize = True
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = _film(location)
    _aim_at(obj, _film(target))
    obj["sum_asset_type"] = "cinematic_industrial_area_light"
    obj["lighting_policy"] = "localized practical motivated light pool"
    obj["sum_light_energy_w"] = energy
    obj["sum_light_size_m"] = [size, size_y]
    obj["sum_light_target_world"] = list(_film(target))
    return obj


def _sun(collection: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.lights.new("CIN_SkylightSun_Data", type="SUN")
    data.color = (0.72, 0.84, 1.0)
    data.energy = 0.45
    data.angle = math.radians(7.0)
    data.use_shadow = True
    obj = bpy.data.objects.new("CIN_SkylightSun", data)
    collection.objects.link(obj)
    obj.rotation_euler = (math.radians(28.0), math.radians(-12.0), math.radians(-32.0))
    obj["sum_asset_type"] = "cool_skylight_directional_source"
    obj["sum_light_energy"] = data.energy
    obj["sum_light_angular_size_degrees"] = 7.0
    return obj


def _grade_existing_rig(scene: bpy.types.Scene) -> None:
    energy_scales = {
        "LD_Key_Softbox": 0.62,
        "LD_Fill_Softbox": 0.34,
        "LD_Rim_Strip": 0.78,
        "LD_Top_Softbox": 0.52,
    }
    for name, scale in energy_scales.items():
        light = bpy.data.objects.get(name)
        if light is not None:
            _set_light_energy(light, scale)

    for light in scene.objects:
        if light.name.startswith("LD_Ceiling_Panel_"):
            _set_light_energy(light, 0.56)

    scene.view_settings.exposure = -0.12
    scene.view_settings.gamma = 1.0
    scene["fpv_grade"] = "AgX medium-high contrast, cool daylight, restrained amber"
    scene["fpv_global_fill_scale"] = 0.34

    world = scene.world
    if world is not None and world.use_nodes and world.node_tree is not None:
        background = next(
            (node for node in world.node_tree.nodes if node.type == "BACKGROUND"),
            None,
        )
        if background is not None:
            background.inputs["Color"].default_value = (0.10, 0.13, 0.17, 1.0)
            background.inputs["Strength"].default_value = 0.11


def augment_fpv_lighting(assets: dict[str, Any]) -> dict[str, Any]:
    """Apply a restrained, practical-motivated cinematic lighting pass."""

    if not isinstance(assets, dict):
        raise TypeError("assets must be a dictionary")
    scene = bpy.context.scene
    collection = _reset_collection()

    _set_material_color("LD_Clean_Powder_Coat", (0.21, 0.23, 0.25, 1.0))
    _set_material_color("LD_Clean_Architecture", (0.34, 0.36, 0.38, 1.0))
    _set_material_color("LD_Clean_Industrial_Floor", (0.12, 0.13, 0.14, 1.0))
    _set_material_color("LD_Steel_Blue_Structure", (0.055, 0.080, 0.105, 1.0))
    _set_material_color("LD_Grinding_Workpiece_Steel", (0.17, 0.18, 0.19, 1.0))
    _grade_abrasive()
    _grade_existing_rig(scene)

    lights = [_sun(collection)]
    lights.extend(
        (
            _area_light(
                collection,
                "CIN_Bearing_Key",
                (-1.2, 4.2, 4.8),
                (0.0, 4.8, 0.85),
                color=(0.72, 0.84, 1.0),
                energy=120.0,
                size=3.2,
                size_y=2.0,
            ),
            _area_light(
                collection,
                "CIN_Robot_Rim",
                (2.4, 10.6, 4.7),
                (-0.8, 10.4, 1.45),
                color=(1.0, 0.68, 0.38),
                energy=215.0,
                size=3.6,
                size_y=1.2,
            ),
            _area_light(
                collection,
                "CIN_Grinding_Inspection",
                (1.85, 14.30, 3.20),
                (3.02, 15.08, 1.82),
                color=(0.70, 0.86, 1.0),
                energy=560.0,
                size=1.25,
                size_y=0.75,
            ),
            _area_light(
                collection,
                "CIN_Grinding_WarmEdge",
                (4.65, 14.65, 2.85),
                (3.02, 15.08, 1.82),
                color=(1.0, 0.46, 0.18),
                energy=165.0,
                size=1.0,
                size_y=0.55,
            ),
            _area_light(
                collection,
                "CIN_Grinding_SoftFill",
                (2.55, 15.75, 3.65),
                (3.02, 15.08, 1.72),
                color=(0.78, 0.88, 1.0),
                energy=260.0,
                size=2.8,
                size_y=1.5,
            ),
            _area_light(
                collection,
                "CIN_UtilityTray_Rake",
                (1.0, 22.0, 4.6),
                (-1.0, 24.0, 1.4),
                color=(0.72, 0.84, 1.0),
                energy=240.0,
                size=8.0,
                size_y=1.1,
            ),
        )
    )

    for index, travel in enumerate((4.0, 9.5, 15.0, 20.0, 25.0, 30.0, 34.0), start=1):
        lights.append(
            _area_light(
                collection,
                f"CIN_Aisle_LightPool_{index:02d}",
                (0.0, travel, 7.05),
                (0.0, travel + 4.0, 0.6),
                color=(0.76, 0.86, 1.0),
                energy=245.0,
                size=7.0,
                size_y=2.4,
            )
        )

    scene["fpv_lighting_build_interface"] = (
        "production.blender.fpv_lighting.augment_fpv_lighting"
    )
    scene["sum_material_readability_lighting"] = json.dumps(
        {
            "grade": "AgX medium-high contrast",
            "exposure": float(scene.view_settings.exposure),
            "white_field_policy": "no broad clipping; practical-motivated soft sources",
            "material_priorities": [
                "brushed steel directional highlights",
                "powder coat grazing response",
                "galvanized utility tray edge response",
                "CBN and coolant separation",
            ],
            "authored_light_count": len(lights),
        },
        separators=(",", ":"),
        ensure_ascii=True,
    )
    assets["fpv_lighting_collection"] = collection
    assets["fpv_lights"] = lights
    assets.setdefault("collections", {})["fpv_lighting"] = collection
    bpy.context.view_layer.update()
    return assets


__all__ = ["augment_fpv_lighting"]
