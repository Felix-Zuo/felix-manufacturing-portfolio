"""Bright industrial product look development for Blender 4.x and 5.x.

The public entry point is intentionally tolerant of partial asset dictionaries.  It
can be run repeatedly while scene construction is still in progress; generated
objects, materials, lights, and compositor nodes use stable ``LD_`` names.
"""

from __future__ import annotations

import math
import random
import re
from collections.abc import Mapping, Sequence
from typing import Any

import bpy
from mathutils import Vector


__all__ = ["setup_lookdev"]


_COLLECTION_NAME = "LD_Lookdev"
_PREFIX = "LD_"
_RENDERABLE_TYPES = {"MESH", "CURVE", "SURFACE", "META", "FONT", "VOLUME", "POINTCLOUD"}

_ROLE_KEYWORDS = (
    (
        "spark",
        {
            "spark",
            "sparks",
            "ember",
        },
    ),
    (
        "rubber",
        {"cable", "wire", "hose", "rubber", "conduit", "sleeve", "loom", "dress_pack", "coolant_line"},
    ),
    (
        "floor",
        {"floor", "ground", "plinth", "pedestal", "platform", "deck"},
    ),
    (
        "luminaire",
        {"luminaire", "light_diffuser", "linear_luminaire", "ceiling_light"},
    ),
    (
        "screen_glass",
        {"screen", "display", "monitor", "glass", "touchscreen", "hmi", "viewport", "lens"},
    ),
    (
        "safety_yellow",
        {"safety_yellow", "yellow_marking", "yellow_guard", "hazard_yellow"},
    ),
    (
        "amber_signal",
        {
            "amber",
            "beacon",
            "indicator",
            "signal",
            "warning",
            "status_light",
            "guide_light",
            "light_strip",
            "led",
            "flow_line",
            "path",
            "route",
            "trace",
            "trail",
        },
    ),
    (
        "architecture",
        {"wall", "ceiling", "room", "architecture", "backdrop", "cyclorama", "interior"},
    ),
    (
        "steel_blue",
        {
            "structure",
            "frame",
            "beam",
            "column",
            "truss",
            "rail",
            "gantry",
            "support",
            "steel_blue",
        },
    ),
    (
        "brushed_metal",
        {
            "metal",
            "steel",
            "aluminum",
            "aluminium",
            "chrome",
            "bearing",
            "spindle",
            "fastener",
            "bolt",
            "screw",
            "shaft",
            "blade",
            "tool",
            "robot",
            "machine_part",
        },
    ),
    (
        "powder_coat",
        {
            "powder",
            "housing",
            "enclosure",
            "casing",
            "shell",
            "cabinet",
            "panel",
            "body",
            "machine",
            "equipment",
            "product",
            "control_box",
            "kiosk",
        },
    ),
)

_EXPLICIT_ROLE_ALIASES = {
    "metal": "brushed_metal",
    "brushed": "brushed_metal",
    "brushed_metal": "brushed_metal",
    "dark_metal": "dark_metal",
    "fixture_dark": "fixture_dark",
    "black_oxide": "dark_metal",
    "galvanized": "galvanized",
    "galvanised": "galvanized",
    "zinc": "galvanized",
    "abrasive": "abrasive",
    "grinding_wheel": "abrasive",
    "abrasive_bond": "abrasive_bond",
    "abrasive_grain": "abrasive_grain",
    "fresh_ground_steel": "fresh_ground_steel",
    "workpiece_steel": "workpiece_steel",
    "coolant": "coolant",
    "powder": "powder_coat",
    "paint": "powder_coat",
    "painted": "powder_coat",
    "powder_coat": "powder_coat",
    "shell": "powder_coat",
    "structure": "steel_blue",
    "steel_blue": "steel_blue",
    "rubber": "rubber",
    "cable": "rubber",
    "glass": "screen_glass",
    "screen": "screen_glass",
    "screen_glass": "screen_glass",
    "safety_glass": "safety_glass",
    "luminaire": "luminaire",
    "light_diffuser": "luminaire",
    "signal": "amber_signal",
    "amber": "amber_signal",
    "amber_signal": "amber_signal",
    "safety_yellow": "safety_yellow",
    "yellow_marking": "safety_yellow",
    "spark": "spark",
    "sparks": "spark",
    "floor": "floor",
    "architecture": "architecture",
    "wall": "architecture",
}

_SPARK_ANCHOR_KEYS = {
    "spark_origin",
    "spark_point",
    "grind_point",
    "grinding_point",
    "tool_tip",
    "contact_point",
    "weld_point",
}


def _safe_set(target: Any, name: str, value: Any) -> bool:
    if target is None or not hasattr(target, name):
        return False
    try:
        setattr(target, name, value)
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return False
    return True


def _try_enum(target: Any, name: str, values: Sequence[str]) -> str | None:
    for value in values:
        if _safe_set(target, name, value):
            return value
    return None


def _socket(sockets: Any, names: Sequence[str]) -> Any | None:
    for name in names:
        try:
            found = sockets.get(name)
        except (AttributeError, TypeError):
            found = None
        if found is not None:
            return found
    return None


def _set_socket(node: Any, names: Sequence[str], value: Any) -> bool:
    socket = _socket(node.inputs, names)
    if socket is None:
        return False
    try:
        socket.default_value = value
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return False
    return True


def _link(tree: Any, output_socket: Any, input_socket: Any) -> bool:
    if output_socket is None or input_socket is None:
        return False
    try:
        tree.links.new(output_socket, input_socket)
    except (TypeError, ValueError, RuntimeError):
        return False
    return True


def _normalized_label(value: Any) -> str:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value or ""))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _explicit_role(value: Any) -> str | None:
    return _EXPLICIT_ROLE_ALIASES.get(_normalized_label(value))


def _infer_role(label: Any, default: str | None = None) -> str | None:
    normalized = _normalized_label(label)
    if not normalized:
        return default
    tokens = set(normalized.split("_"))
    if "safety_glass" in normalized or "guard_glass" in normalized:
        return "safety_glass"
    if "grinding_wheel" in normalized or "cbn" in tokens or "abrasive" in tokens:
        return "abrasive"
    if "black_oxide" in normalized or "blackoxide" in tokens:
        return "dark_metal"
    if "graphite" in tokens and ("powder" in tokens or "powder_coat" in normalized):
        return "steel_blue"
    if "screen" in tokens and tokens.intersection({"frame", "bezel", "anodized", "anodised"}):
        return "dark_metal"
    if "rail_steel" in normalized or ({"machined", "steel"} <= tokens):
        return "brushed_metal"
    if "luminaire" in tokens and tokens.intersection({"carrier", "channel", "load"}):
        return "steel_blue"
    if "luminaire" in tokens or "light_diffuser" in normalized:
        return "luminaire"
    for role, keywords in _ROLE_KEYWORDS:
        for keyword in keywords:
            if keyword in tokens or ("_" in keyword and keyword in normalized):
                return role
    return default


def _is_blender_object(value: Any) -> bool:
    return hasattr(value, "type") and hasattr(value, "matrix_world") and hasattr(value, "name")


def _is_blender_collection(value: Any) -> bool:
    return not _is_blender_object(value) and hasattr(value, "all_objects") and hasattr(value, "children")


def _asset_entries(assets: Any) -> list[tuple[Any, str]]:
    entries: dict[int, list[Any]] = {}
    visited_containers: set[int] = set()

    def record(obj: Any, hint: str) -> None:
        try:
            key = int(obj.as_pointer())
        except (AttributeError, TypeError, ValueError):
            key = id(obj)
        if key not in entries:
            entries[key] = [obj, []]
        if hint and hint not in entries[key][1]:
            entries[key][1].append(hint)

    def walk(value: Any, hint: str = "") -> None:
        if value is None:
            return
        if _is_blender_object(value):
            record(value, hint)
            try:
                children = value.children_recursive
            except AttributeError:
                children = value.children
            for child in children:
                record(child, hint)
            return
        if isinstance(value, str):
            obj = bpy.data.objects.get(value)
            if obj is not None:
                walk(obj, hint)
            return
        if _is_blender_collection(value):
            marker = id(value)
            if marker in visited_containers:
                return
            visited_containers.add(marker)
            for obj in value.all_objects:
                record(obj, hint)
            return
        if isinstance(value, Mapping):
            marker = id(value)
            if marker in visited_containers:
                return
            visited_containers.add(marker)
            for key, nested in value.items():
                nested_hint = "/".join(part for part in (hint, str(key)) if part)
                walk(nested, nested_hint)
            return
        if isinstance(value, (list, tuple, set, frozenset)):
            marker = id(value)
            if marker in visited_containers:
                return
            visited_containers.add(marker)
            for nested in value:
                walk(nested, hint)
            return
        values = getattr(value, "__dict__", None)
        if isinstance(values, Mapping):
            walk(values, hint)

    walk(assets)
    return [(item[0], "/".join(item[1])) for item in entries.values()]


def _object_role(obj: Any, hint: str) -> str:
    for property_name in ("lookdev_role", "material_role", "role"):
        try:
            raw_role = obj.get(property_name)
        except (AttributeError, TypeError):
            raw_role = None
        role = _explicit_role(raw_role) or _infer_role(raw_role)
        if role is not None:
            return role
    return _infer_role(f"{hint} {obj.name}", "powder_coat") or "powder_coat"


def _semantic_surface_override(obj: Any, hint: str) -> str | None:
    labels = [str(getattr(obj, "name", "")), hint]
    for property_name in ("sum_part_role", "sum_detail", "detail", "role"):
        try:
            labels.append(str(obj.get(property_name, "")))
        except (AttributeError, TypeError):
            continue
    normalized = _normalized_label(" ".join(labels))
    if any(
        token in normalized
        for token in (
            "utilitytray",
            "utility_tray",
            "cable_tray",
            "tray_rungs",
            "ladder_cable_tray",
        )
    ):
        return "galvanized"
    return None


def _clear_nodes(node_tree: Any) -> None:
    for node in list(node_tree.nodes):
        node_tree.nodes.remove(node)


def _add_micro_surface(
    material: Any,
    shader: Any,
    *,
    scale: float,
    strength: float,
    distance: float,
    roughness: float,
    roughness_variation: float,
    detail: float,
    distortion: float,
    pattern: str,
) -> None:
    nodes = material.node_tree.nodes
    coordinates = nodes.new("ShaderNodeTexCoord")
    coordinates.name = f"{material.name}_MicroCoordinates"
    coordinates.location = (-980.0, -180.0)
    vector = coordinates.outputs.get("Object") or coordinates.outputs.get("Generated")

    micro_noise = nodes.new("ShaderNodeTexNoise")
    micro_noise.name = f"{material.name}_MicroNormal"
    micro_noise.location = (-720.0, -240.0)
    _set_socket(micro_noise, ("Scale",), scale)
    _set_socket(micro_noise, ("Detail",), detail)
    _set_socket(micro_noise, ("Roughness",), 0.56)
    _set_socket(micro_noise, ("Distortion",), distortion)
    _link(material.node_tree, vector, micro_noise.inputs.get("Vector"))
    height = micro_noise.outputs.get("Fac")

    if pattern == "brushed":
        wave = nodes.new("ShaderNodeTexWave")
        wave.name = f"{material.name}_DirectionalBrush"
        wave.location = (-710.0, -430.0)
        _safe_set(wave, "wave_type", "BANDS")
        _safe_set(wave, "bands_direction", "X")
        _set_socket(wave, ("Scale",), scale * 1.55)
        _set_socket(wave, ("Distortion",), 2.2)
        _set_socket(wave, ("Detail",), 3.0)
        _set_socket(wave, ("Detail Scale",), 1.7)
        _link(material.node_tree, vector, wave.inputs.get("Vector"))
        mix = nodes.new("ShaderNodeMixRGB")
        mix.name = f"{material.name}_BrushBreakup"
        mix.location = (-430.0, -285.0)
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 0.38
        _link(material.node_tree, micro_noise.outputs.get("Fac"), mix.inputs[1])
        _link(material.node_tree, wave.outputs.get("Color"), mix.inputs[2])
        height = mix.outputs.get("Color")
    elif pattern == "galvanized":
        spangle = nodes.new("ShaderNodeTexVoronoi")
        spangle.name = f"{material.name}_ZincSpangle"
        spangle.location = (-690.0, -410.0)
        _safe_set(spangle, "feature", "DISTANCE_TO_EDGE")
        _set_socket(spangle, ("Scale",), 58.0)
        _set_socket(spangle, ("Randomness",), 0.76)
        _link(material.node_tree, vector, spangle.inputs.get("Vector"))
        height = spangle.outputs.get("Distance")

    bump = nodes.new("ShaderNodeBump")
    bump.name = f"{material.name}_MicroBump"
    bump.location = (-80.0, -185.0)
    _set_socket(bump, ("Strength",), strength)
    _set_socket(bump, ("Distance",), distance)
    _set_socket(bump, ("Midlevel",), 0.5)
    _link(material.node_tree, height, bump.inputs.get("Height"))
    _link(material.node_tree, bump.outputs.get("Normal"), shader.inputs.get("Normal"))

    roughness_noise = nodes.new("ShaderNodeTexNoise")
    roughness_noise.name = f"{material.name}_RoughnessVariation"
    roughness_noise.location = (-710.0, 70.0)
    roughness_scale = 1.35 if pattern == "floor" else max(1.0, scale * 0.075)
    _set_socket(roughness_noise, ("Scale",), roughness_scale)
    _set_socket(roughness_noise, ("Detail",), min(detail, 2.2))
    _set_socket(roughness_noise, ("Roughness",), 0.48)
    _set_socket(roughness_noise, ("Distortion",), distortion * 0.25)
    _link(material.node_tree, vector, roughness_noise.inputs.get("Vector"))

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = f"{material.name}_RoughnessRange"
    ramp.location = (-380.0, 75.0)
    low = max(0.02, roughness - roughness_variation)
    high = min(0.98, roughness + roughness_variation)
    ramp.color_ramp.elements[0].position = 0.18
    ramp.color_ramp.elements[0].color = (low, low, low, 1.0)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (high, high, high, 1.0)
    _link(material.node_tree, roughness_noise.outputs.get("Fac"), ramp.inputs.get("Fac"))
    _link(material.node_tree, ramp.outputs.get("Color"), shader.inputs.get("Roughness"))

    material["sum_material_surface_model"] = pattern
    material["sum_material_roughness_base"] = roughness
    material["sum_material_roughness_range"] = [low, high]
    material["sum_material_micro_scale_per_m"] = scale
    material["sum_material_micro_bump_distance_m"] = distance
    material["sum_material_procedural_policy"] = (
        "low-contrast microstructure; no screen-space speckle or decorative pattern"
    )


def _new_principled_material(
    name: str,
    *,
    base_color: tuple[float, float, float, float],
    metallic: float,
    roughness: float,
    coat: float = 0.0,
    coat_roughness: float = 0.12,
    transmission: float = 0.0,
    ior: float = 1.45,
    anisotropic: float = 0.0,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
    alpha: float = 1.0,
    micro_scale: float | None = None,
    micro_strength: float = 0.0,
    micro_distance: float = 0.005,
    roughness_variation: float = 0.0,
    micro_detail: float = 2.0,
    micro_distortion: float = 0.0,
    micro_pattern: str = "isotropic",
) -> Any:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = base_color
    _clear_nodes(material.node_tree)

    nodes = material.node_tree.nodes
    output = nodes.new("ShaderNodeOutputMaterial")
    output.name = f"{name}_Output"
    output.location = (560.0, 0.0)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.name = f"{name}_Principled"
    shader.location = (250.0, 0.0)

    _set_socket(shader, ("Base Color",), base_color)
    _set_socket(shader, ("Metallic",), metallic)
    _set_socket(shader, ("Roughness",), roughness)
    _set_socket(shader, ("IOR",), ior)
    _set_socket(shader, ("Coat Weight", "Clearcoat"), coat)
    _set_socket(shader, ("Coat Roughness", "Clearcoat Roughness"), coat_roughness)
    _set_socket(shader, ("Transmission Weight", "Transmission"), transmission)
    _set_socket(shader, ("Anisotropic IOR Level", "Anisotropic"), anisotropic)
    _set_socket(shader, ("Alpha",), alpha)
    if emission_color is not None:
        _set_socket(shader, ("Emission Color", "Emission"), emission_color)
        _set_socket(shader, ("Emission Strength",), emission_strength)

    _link(material.node_tree, shader.outputs.get("BSDF"), output.inputs.get("Surface"))

    if micro_scale is not None and micro_strength > 0.0:
        _add_micro_surface(
            material,
            shader,
            scale=micro_scale,
            strength=micro_strength,
            distance=micro_distance,
            roughness=roughness,
            roughness_variation=roughness_variation,
            detail=micro_detail,
            distortion=micro_distortion,
            pattern=micro_pattern,
        )

    return material


def _new_cbn_abrasive_material(name: str) -> Any:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (0.025, 0.085, 0.060, 1.0)
    _clear_nodes(material.node_tree)

    nodes = material.node_tree.nodes
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (620.0, 0.0)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (330.0, 0.0)
    _set_socket(shader, ("Metallic",), 0.22)
    _set_socket(shader, ("Roughness",), 0.58)
    _set_socket(shader, ("Coat Weight", "Clearcoat"), 0.08)
    _set_socket(shader, ("Coat Roughness", "Clearcoat Roughness"), 0.28)

    coordinates = nodes.new("ShaderNodeTexCoord")
    coordinates.location = (-880.0, 0.0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-650.0, 30.0)
    noise.name = "LD_CBN_BondStructure"
    _set_socket(noise, ("Scale",), 155.0)
    _set_socket(noise, ("Detail",), 2.6)
    _set_socket(noise, ("Roughness",), 0.62)

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-350.0, 120.0)
    ramp.name = "LD_CBN_SubtleColorVariation"
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (0.008, 0.016, 0.016, 1.0)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (0.050, 0.085, 0.078, 1.0)
    middle = ramp.color_ramp.elements.new(0.53)
    middle.color = (0.020, 0.043, 0.040, 1.0)

    bump = nodes.new("ShaderNodeBump")
    bump.location = (60.0, -150.0)
    bump.name = "LD_CBN_BondMicroBump"
    _set_socket(bump, ("Strength",), 0.18)
    _set_socket(bump, ("Distance",), 0.00038)

    roughness_noise = nodes.new("ShaderNodeTexNoise")
    roughness_noise.name = "LD_CBN_RoughnessVariation"
    roughness_noise.location = (-330.0, -320.0)
    _set_socket(roughness_noise, ("Scale",), 14.0)
    _set_socket(roughness_noise, ("Detail",), 1.8)
    _set_socket(roughness_noise, ("Roughness",), 0.52)
    roughness_ramp = nodes.new("ShaderNodeValToRGB")
    roughness_ramp.name = "LD_CBN_RoughnessRange"
    roughness_ramp.location = (15.0, -330.0)
    roughness_ramp.color_ramp.elements[0].color = (0.50, 0.50, 0.50, 1.0)
    roughness_ramp.color_ramp.elements[1].color = (0.66, 0.66, 0.66, 1.0)

    _link(material.node_tree, coordinates.outputs.get("Generated"), noise.inputs.get("Vector"))
    _link(
        material.node_tree,
        coordinates.outputs.get("Object") or coordinates.outputs.get("Generated"),
        roughness_noise.inputs.get("Vector"),
    )
    _link(material.node_tree, noise.outputs.get("Fac"), ramp.inputs.get("Fac"))
    _link(material.node_tree, ramp.outputs.get("Color"), shader.inputs.get("Base Color"))
    _link(material.node_tree, noise.outputs.get("Fac"), bump.inputs.get("Height"))
    _link(material.node_tree, bump.outputs.get("Normal"), shader.inputs.get("Normal"))
    _link(
        material.node_tree,
        roughness_noise.outputs.get("Fac"),
        roughness_ramp.inputs.get("Fac"),
    )
    _link(
        material.node_tree,
        roughness_ramp.outputs.get("Color"),
        shader.inputs.get("Roughness"),
    )
    _link(material.node_tree, shader.outputs.get("BSDF"), output.inputs.get("Surface"))
    material["sum_material_surface_model"] = "vitrified_cbn_with_modeled_grains"
    material["sum_material_roughness_range"] = [0.50, 0.66]
    material["sum_material_micro_scale_per_m"] = 155.0
    material["sum_material_micro_bump_distance_m"] = 0.00038
    material["sum_material_procedural_policy"] = (
        "modeled grains carry hero detail; shader texture stays below speckle threshold"
    )
    return material


def _new_coolant_material(name: str) -> Any:
    material = _new_principled_material(
        name,
        base_color=(0.46, 0.54, 0.43, 1.0),
        metallic=0.0,
        roughness=0.15,
        coat=0.12,
        coat_roughness=0.09,
        transmission=0.18,
        ior=1.34,
        emission_color=(0.025, 0.038, 0.020, 1.0),
        emission_strength=0.035,
        alpha=0.78,
    )
    tree = material.node_tree
    nodes = tree.nodes
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    coordinates = nodes.new("ShaderNodeTexCoord")
    coordinates.name = "LD_Coolant_FlowCoordinates"
    coordinates.location = (-900.0, -150.0)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.name = "LD_Coolant_FlowMapping"
    mapping.label = "Animated process-fluid advection"
    mapping.location = (-690.0, -150.0)
    _safe_set(mapping, "vector_type", "POINT")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "LD_Coolant_FlowNoise"
    noise.location = (-460.0, -150.0)
    _set_socket(noise, ("Scale",), 7.5)
    _set_socket(noise, ("Detail",), 3.0)
    _set_socket(noise, ("Roughness",), 0.62)
    _set_socket(noise, ("Distortion",), 0.72)
    roughness_ramp = nodes.new("ShaderNodeValToRGB")
    roughness_ramp.name = "LD_Coolant_RoughnessRange"
    roughness_ramp.location = (-190.0, 40.0)
    roughness_ramp.color_ramp.elements[0].color = (0.055, 0.055, 0.055, 1.0)
    roughness_ramp.color_ramp.elements[1].color = (0.115, 0.115, 0.115, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.name = "LD_Coolant_FlowNormal"
    bump.location = (-40.0, -180.0)
    _set_socket(bump, ("Strength",), 0.10)
    _set_socket(bump, ("Distance",), 0.00065)
    _link(tree, coordinates.outputs.get("Object"), mapping.inputs.get("Vector"))
    _link(tree, mapping.outputs.get("Vector"), noise.inputs.get("Vector"))
    _link(tree, noise.outputs.get("Fac"), roughness_ramp.inputs.get("Fac"))
    _link(tree, roughness_ramp.outputs.get("Color"), shader.inputs.get("Roughness"))
    _link(tree, noise.outputs.get("Fac"), bump.inputs.get("Height"))
    _link(tree, bump.outputs.get("Normal"), shader.inputs.get("Normal"))
    for axis, speed in ((0, 0.0035), (1, -0.012), (2, 0.0065)):
        curve = mapping.inputs["Location"].driver_add("default_value", axis)
        curve.driver.type = "SCRIPTED"
        curve.driver.expression = f"frame*{speed:.6f}"
    material["sum_material_surface_model"] = "moving_milky_grinding_coolant"
    material["sum_material_roughness_range"] = [0.055, 0.115]
    material["sum_material_flow_mapping_node"] = mapping.name
    material["sum_material_procedural_policy"] = "advected broad flow detail, no static dots"
    return material


def _new_emission_material(
    name: str,
    color: tuple[float, float, float, float],
    strength: float,
) -> Any:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = color
    _clear_nodes(material.node_tree)
    nodes = material.node_tree.nodes
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (320.0, 0.0)
    emission = nodes.new("ShaderNodeEmission")
    emission.location = (0.0, 0.0)
    _set_socket(emission, ("Color",), color)
    _set_socket(emission, ("Strength",), strength)
    _link(material.node_tree, emission.outputs.get("Emission"), output.inputs.get("Surface"))
    return material


def _make_materials() -> dict[str, Any]:
    materials = {
        "brushed_metal": _new_principled_material(
            "LD_Brushed_Metal",
            base_color=(0.34, 0.39, 0.44, 1.0),
            metallic=0.96,
            roughness=0.25,
            coat=0.08,
            anisotropic=0.34,
            micro_scale=120.0,
            micro_strength=0.018,
            micro_distance=0.00008,
            roughness_variation=0.022,
            micro_detail=1.8,
            micro_distortion=0.18,
            micro_pattern="brushed",
        ),
        "powder_coat": _new_principled_material(
            "LD_Clean_Powder_Coat",
            base_color=(0.38, 0.44, 0.50, 1.0),
            metallic=0.02,
            roughness=0.34,
            coat=0.18,
            coat_roughness=0.18,
            micro_scale=72.0,
            micro_strength=0.022,
            micro_distance=0.00012,
            roughness_variation=0.020,
            micro_detail=2.2,
            micro_distortion=0.22,
            micro_pattern="powder_coat",
        ),
        "steel_blue": _new_principled_material(
            "LD_Steel_Blue_Structure",
            base_color=(0.07, 0.13, 0.21, 1.0),
            metallic=0.08,
            roughness=0.31,
            coat=0.20,
            coat_roughness=0.16,
            micro_scale=64.0,
            micro_strength=0.018,
            micro_distance=0.00010,
            roughness_variation=0.018,
            micro_detail=2.0,
            micro_distortion=0.16,
            micro_pattern="powder_coat",
        ),
        "galvanized": _new_principled_material(
            "LD_Galvanized_Cable_Tray",
            base_color=(0.33, 0.37, 0.40, 1.0),
            metallic=0.82,
            roughness=0.34,
            coat=0.04,
            coat_roughness=0.22,
            micro_scale=62.0,
            micro_strength=0.010,
            micro_distance=0.00005,
            roughness_variation=0.026,
            micro_detail=1.6,
            micro_distortion=0.08,
            micro_pattern="galvanized",
        ),
        "dark_metal": _new_principled_material(
            "LD_Dark_Oxide_Metal",
            base_color=(0.018, 0.025, 0.035, 1.0),
            metallic=0.80,
            roughness=0.28,
            coat=0.08,
            anisotropic=0.12,
            micro_scale=70.0,
            micro_strength=0.015,
            micro_distance=0.00008,
            roughness_variation=0.018,
            micro_detail=1.8,
            micro_distortion=0.12,
            micro_pattern="brushed",
        ),
        "abrasive": _new_cbn_abrasive_material("LD_CBN_Profiled_Abrasive"),
        "abrasive_bond": _new_principled_material(
            "LD_CBN_Vitrified_Bond",
            base_color=(0.012, 0.050, 0.034, 1.0),
            metallic=0.04,
            roughness=0.72,
            coat=0.015,
            micro_scale=95.0,
            micro_strength=0.070,
            micro_distance=0.00025,
            roughness_variation=0.045,
            micro_detail=2.4,
            micro_distortion=0.30,
            micro_pattern="porous_bond",
        ),
        "abrasive_grain": _new_principled_material(
            "LD_CBN_Exposed_Grains",
            base_color=(0.080, 0.180, 0.135, 1.0),
            metallic=0.34,
            roughness=0.31,
            coat=0.12,
            coat_roughness=0.18,
            micro_scale=90.0,
            micro_strength=0.020,
            micro_distance=0.00005,
            roughness_variation=0.025,
            micro_detail=1.8,
            micro_distortion=0.10,
            micro_pattern="faceted_grain",
        ),
        "fresh_ground_steel": _new_principled_material(
            "LD_Fresh_Ground_Raceway_Steel",
            base_color=(0.30, 0.34, 0.37, 1.0),
            metallic=0.96,
            roughness=0.16,
            coat=0.08,
            coat_roughness=0.10,
            anisotropic=0.68,
            micro_scale=180.0,
            micro_strength=0.010,
            micro_distance=0.000025,
            roughness_variation=0.018,
            micro_detail=1.4,
            micro_distortion=0.06,
            micro_pattern="brushed",
        ),
        "fixture_dark": _new_principled_material(
            "LD_Dark_Anodized_Fixture",
            base_color=(0.018, 0.026, 0.036, 1.0),
            metallic=0.0,
            roughness=0.64,
            coat=0.0,
            ior=1.08,
            micro_scale=82.0,
            micro_strength=0.022,
            micro_distance=0.00010,
            roughness_variation=0.026,
            micro_detail=2.0,
            micro_distortion=0.16,
            micro_pattern="powder_coat",
        ),
        "workpiece_steel": _new_principled_material(
            "LD_Grinding_Workpiece_Steel",
            base_color=(0.050, 0.060, 0.064, 1.0),
            metallic=0.94,
            roughness=0.24,
            coat=0.08,
            coat_roughness=0.20,
            micro_scale=130.0,
            micro_strength=0.014,
            micro_distance=0.000045,
            roughness_variation=0.022,
            micro_detail=1.6,
            micro_distortion=0.08,
            micro_pattern="brushed",
        ),
        "coolant": _new_coolant_material("LD_Grinding_Coolant_Stream"),
        "rubber": _new_principled_material(
            "LD_Black_Rubber",
            base_color=(0.012, 0.016, 0.022, 1.0),
            metallic=0.0,
            roughness=0.56,
            coat=0.04,
            micro_scale=55.0,
            micro_strength=0.035,
            micro_distance=0.00022,
            roughness_variation=0.038,
            micro_detail=2.0,
            micro_distortion=0.28,
            micro_pattern="rubber",
        ),
        "screen_glass": _new_principled_material(
            "LD_Screen_Glass",
            base_color=(0.008, 0.018, 0.030, 1.0),
            metallic=0.0,
            roughness=0.065,
            coat=0.92,
            coat_roughness=0.045,
            transmission=0.28,
            ior=1.46,
            emission_color=(0.004, 0.018, 0.032, 1.0),
            emission_strength=0.16,
            alpha=0.92,
        ),
        "safety_glass": _new_principled_material(
            "LD_Clear_Safety_Glass",
            base_color=(0.045, 0.085, 0.11, 1.0),
            metallic=0.0,
            roughness=0.09,
            coat=0.30,
            coat_roughness=0.06,
            transmission=0.78,
            ior=1.48,
            alpha=0.24,
        ),
        "amber_signal": _new_principled_material(
            "LD_Amber_Signal",
            base_color=(0.70, 0.20, 0.008, 1.0),
            metallic=0.02,
            roughness=0.22,
            coat=0.34,
            coat_roughness=0.10,
            emission_color=(1.0, 0.34, 0.012, 1.0),
            emission_strength=1.7,
        ),
        "safety_yellow": _new_principled_material(
            "LD_Safety_Yellow_Powder_Coat",
            base_color=(0.72, 0.35, 0.006, 1.0),
            metallic=0.02,
            roughness=0.34,
            coat=0.18,
            coat_roughness=0.16,
            micro_scale=72.0,
            micro_strength=0.022,
            micro_distance=0.00012,
            roughness_variation=0.020,
            micro_detail=2.0,
            micro_distortion=0.18,
            micro_pattern="powder_coat",
        ),
        "floor": _new_principled_material(
            "LD_Clean_Industrial_Floor",
            base_color=(0.30, 0.32, 0.34, 1.0),
            metallic=0.04,
            roughness=0.42,
            coat=0.08,
            coat_roughness=0.24,
            micro_scale=18.0,
            micro_strength=0.018,
            micro_distance=0.00028,
            roughness_variation=0.055,
            micro_detail=2.0,
            micro_distortion=0.20,
            micro_pattern="floor",
        ),
        "architecture": _new_principled_material(
            "LD_Clean_Architecture",
            base_color=(0.50, 0.54, 0.58, 1.0),
            metallic=0.0,
            roughness=0.38,
            micro_scale=36.0,
            micro_strength=0.012,
            micro_distance=0.00016,
            roughness_variation=0.025,
            micro_detail=1.6,
            micro_distortion=0.12,
            micro_pattern="painted_architecture",
        ),
        "luminaire": _new_principled_material(
            "LD_Linear_Luminaire_Diffuser",
            base_color=(0.72, 0.80, 0.88, 1.0),
            metallic=0.0,
            roughness=0.20,
            coat=0.16,
            coat_roughness=0.10,
            emission_color=(0.82, 0.91, 1.0, 1.0),
            emission_strength=1.5,
        ),
        "spark": _new_emission_material(
            "LD_Grinding_Spark",
            color=(1.0, 0.20, 0.006, 1.0),
            strength=4.5,
        ),
    }

    glass = materials["screen_glass"]
    _safe_set(glass, "surface_render_method", "DITHERED")
    _safe_set(glass, "blend_method", "BLEND")
    _safe_set(glass, "use_screen_refraction", True)
    _safe_set(glass, "use_transparency_overlap", False)
    safety_glass = materials["safety_glass"]
    _safe_set(safety_glass, "surface_render_method", "DITHERED")
    _safe_set(safety_glass, "blend_method", "BLEND")
    _safe_set(safety_glass, "use_screen_refraction", True)
    _safe_set(safety_glass, "use_transparency_overlap", False)
    coolant = materials["coolant"]
    _safe_set(coolant, "surface_render_method", "DITHERED")
    _safe_set(coolant, "blend_method", "BLEND")
    _safe_set(coolant, "use_screen_refraction", True)
    _safe_set(coolant, "use_transparency_overlap", False)
    return materials


def _screen_media_material(material: Any) -> Any | None:
    """Keep an assigned screen image while adding a reflective glass response."""

    node_tree = getattr(material, "node_tree", None)
    if node_tree is None:
        return None
    image_node = next(
        (
            node
            for node in node_tree.nodes
            if node.bl_idname == "ShaderNodeTexImage" and getattr(node, "image", None) is not None
        ),
        None,
    )
    if image_node is None:
        return None

    image = image_node.image
    interpolation = getattr(image_node, "interpolation", "Linear")
    extension = getattr(image_node, "extension", "REPEAT")
    projection = getattr(image_node, "projection", "FLAT")
    _clear_nodes(node_tree)

    output = node_tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (620.0, 0.0)
    shader = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (260.0, 0.0)
    texture = node_tree.nodes.new("ShaderNodeTexImage")
    texture.location = (-180.0, 0.0)
    texture.image = image
    _safe_set(texture, "interpolation", interpolation)
    _safe_set(texture, "extension", extension)
    _safe_set(texture, "projection", projection)

    _set_socket(shader, ("Metallic",), 0.0)
    _set_socket(shader, ("Base Color",), (0.006, 0.010, 0.016, 1.0))
    _set_socket(shader, ("Roughness",), 0.08)
    _set_socket(shader, ("IOR",), 1.46)
    _set_socket(shader, ("Coat Weight", "Clearcoat"), 0.92)
    _set_socket(shader, ("Coat Roughness", "Clearcoat Roughness"), 0.045)
    _set_socket(shader, ("Transmission Weight", "Transmission"), 0.08)
    _set_socket(shader, ("Emission Strength",), 0.58)
    _link(
        node_tree,
        texture.outputs.get("Color"),
        _socket(shader.inputs, ("Emission Color", "Emission")),
    )
    _link(node_tree, shader.outputs.get("BSDF"), output.inputs.get("Surface"))
    material.diffuse_color = (0.008, 0.018, 0.030, 1.0)
    material["lookdev_screen_media"] = True
    _safe_set(material, "use_screen_refraction", True)
    return material


def _assign_materials(entries: Sequence[tuple[Any, str]], materials: Mapping[str, Any]) -> dict[int, str]:
    roles: dict[int, str] = {}
    for obj, hint in entries:
        if getattr(obj, "type", None) not in _RENDERABLE_TYPES:
            continue
        data = getattr(obj, "data", None)
        slots = getattr(data, "materials", None)
        if slots is None:
            continue
        explicit_role = _semantic_surface_override(obj, hint)
        if explicit_role is None:
            for property_name in ("lookdev_role", "material_role", "role"):
                try:
                    explicit_role = _explicit_role(obj.get(property_name))
                except (AttributeError, TypeError):
                    explicit_role = None
                if explicit_role is not None:
                    break
        role = explicit_role or _object_role(obj, hint)
        try:
            pointer = int(obj.as_pointer())
        except (AttributeError, TypeError, ValueError):
            pointer = id(obj)
        roles[pointer] = role
        try:
            if len(slots) == 0:
                slots.append(materials[role])
                continue
            for index in range(len(slots)):
                current = slots[index]
                slot_role = (
                    role
                    if explicit_role is not None
                    else _infer_role(getattr(current, "name", ""), role)
                    if current
                    else role
                )
                if slot_role == "screen_glass" and current is not None:
                    screen_media = _screen_media_material(current)
                    if screen_media is not None:
                        slots[index] = screen_media
                        continue
                slots[index] = materials.get(slot_role, materials[role])
        except (AttributeError, IndexError, KeyError, RuntimeError, TypeError):
            continue
    return roles


def _bounds_for_objects(objects: Sequence[Any]) -> tuple[Vector, Vector, Vector, Vector]:
    minimum: Vector | None = None
    maximum: Vector | None = None
    for obj in objects:
        if getattr(obj, "type", None) not in _RENDERABLE_TYPES or str(getattr(obj, "name", "")).startswith(_PREFIX):
            continue
        try:
            corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        except (AttributeError, TypeError, ValueError, RuntimeError):
            continue
        for point in corners:
            if minimum is None:
                minimum = point.copy()
                maximum = point.copy()
            else:
                minimum.x = min(minimum.x, point.x)
                minimum.y = min(minimum.y, point.y)
                minimum.z = min(minimum.z, point.z)
                maximum.x = max(maximum.x, point.x)
                maximum.y = max(maximum.y, point.y)
                maximum.z = max(maximum.z, point.z)

    if minimum is None or maximum is None:
        minimum = Vector((-4.0, -3.0, 0.0))
        maximum = Vector((4.0, 3.0, 4.0))
    size = maximum - minimum
    size.x = max(size.x, 1.0)
    size.y = max(size.y, 1.0)
    size.z = max(size.z, 1.0)
    center = (minimum + maximum) * 0.5
    return center, size, minimum, maximum


def _resolve_camera(camera: Any, scene: Any) -> Any | None:
    if _is_blender_object(camera) and getattr(camera, "type", None) == "CAMERA":
        return camera
    if isinstance(camera, str):
        candidate = bpy.data.objects.get(camera)
        if candidate is not None and candidate.type == "CAMERA":
            return candidate
    if isinstance(camera, Mapping):
        for key in ("camera", "hero_camera", "main_camera"):
            if key in camera:
                candidate = _resolve_camera(camera[key], scene)
                if candidate is not None:
                    return candidate
    if scene.camera is not None and scene.camera.type == "CAMERA":
        return scene.camera
    return next((obj for obj in scene.objects if obj.type == "CAMERA"), None)


def _ensure_collection(scene: Any) -> Any:
    collection = bpy.data.collections.get(_COLLECTION_NAME) or bpy.data.collections.new(_COLLECTION_NAME)
    if scene.collection.children.get(collection.name) is None:
        scene.collection.children.link(collection)
    return collection


def _ensure_object_linked(obj: Any, collection: Any) -> None:
    if collection.objects.get(obj.name) is None:
        collection.objects.link(obj)


def _remove_generated_object(name: str) -> None:
    obj = bpy.data.objects.get(name)
    if obj is not None:
        bpy.data.objects.remove(obj, do_unlink=True)


def _ensure_empty(collection: Any, name: str) -> Any:
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "EMPTY":
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
        obj = bpy.data.objects.new(name, None)
    _ensure_object_linked(obj, collection)
    return obj


def _ensure_light(collection: Any, name: str, light_type: str) -> Any:
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.type != "LIGHT":
        bpy.data.objects.remove(obj, do_unlink=True)
        obj = None
    if obj is None:
        data_name = f"{name}_Data"
        light_data = bpy.data.lights.get(data_name)
        if light_data is None:
            light_data = bpy.data.lights.new(data_name, light_type)
        else:
            _safe_set(light_data, "type", light_type)
        obj = bpy.data.objects.new(name, light_data)
    else:
        _safe_set(obj.data, "type", light_type)
    _ensure_object_linked(obj, collection)
    obj["lookdev_generated"] = True
    return obj


def _aim_at(obj: Any, target: Vector) -> None:
    direction = target - obj.location
    if direction.length_squared <= 1.0e-10:
        return
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _camera_basis(
    camera: Any | None,
    center: Vector,
    world_up: Vector,
) -> tuple[Vector, Vector, Vector]:
    world_up = world_up.normalized()
    if camera is not None:
        view = center - camera.matrix_world.translation
        if view.length_squared <= 1.0e-8:
            view = camera.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    else:
        view = Vector((0.0, 1.0, -0.15))
    view.normalize()
    right = view.cross(world_up)
    if right.length_squared <= 1.0e-8:
        right = Vector((1.0, 0.0, 0.0))
    else:
        right.normalize()
    up = right.cross(view).normalized()
    return view, right, up


def _configure_area_light(
    light: Any,
    *,
    location: Vector,
    target: Vector,
    color: tuple[float, float, float],
    energy: float,
    size: float,
    size_y: float | None = None,
    shape: str = "RECTANGLE",
    volume_factor: float = 0.25,
) -> None:
    light.location = location
    data = light.data
    data.color = color
    data.energy = energy
    _safe_set(data, "shape", shape)
    _safe_set(data, "size", size)
    if size_y is not None:
        _safe_set(data, "size_y", size_y)
    _safe_set(data, "normalize", True)
    _safe_set(data, "use_shadow", True)
    _safe_set(data, "diffuse_factor", 1.0)
    _safe_set(data, "specular_factor", 1.0)
    _safe_set(data, "volume_factor", volume_factor)
    _aim_at(light, target)


def _setup_lights(
    collection: Any,
    center: Vector,
    size: Vector,
    camera: Any | None,
    scene_up: Vector,
) -> tuple[dict[str, Any], float, tuple[Vector, Vector, Vector]]:
    diagonal = max(size.length, 1.0)
    distance = max(diagonal * 0.78, 3.0)
    base_energy = min(max(70.0 * diagonal * diagonal, 800.0), 11000.0)
    view, right, up = _camera_basis(camera, center, scene_up)

    lights = {
        "key": _ensure_light(collection, "LD_Key_Softbox", "AREA"),
        "fill": _ensure_light(collection, "LD_Fill_Softbox", "AREA"),
        "rim": _ensure_light(collection, "LD_Rim_Strip", "AREA"),
        "top": _ensure_light(collection, "LD_Top_Softbox", "AREA"),
    }

    _configure_area_light(
        lights["key"],
        location=center - view * distance * 0.55 - right * distance * 0.62 + up * distance * 0.68,
        target=center + up * size.z * 0.05,
        color=(0.88, 0.95, 1.0),
        energy=base_energy,
        size=diagonal * 0.48,
        size_y=diagonal * 0.34,
        volume_factor=0.06,
    )
    _configure_area_light(
        lights["fill"],
        location=center - view * distance * 0.24 + right * distance * 0.76 + up * distance * 0.32,
        target=center,
        color=(0.72, 0.83, 0.96),
        energy=base_energy * 0.30,
        size=diagonal * 0.58,
        size_y=diagonal * 0.40,
        volume_factor=0.03,
    )
    _configure_area_light(
        lights["rim"],
        location=center + view * distance * 0.58 - right * distance * 0.38 + up * distance * 0.54,
        target=center + up * size.z * 0.08,
        color=(1.0, 0.76, 0.48),
        energy=base_energy * 0.18,
        size=diagonal * 0.52,
        size_y=diagonal * 0.11,
        volume_factor=0.025,
    )
    _configure_area_light(
        lights["top"],
        location=center - view * distance * 0.06 + up * distance * 1.05,
        target=center,
        color=(1.0, 0.98, 0.94),
        energy=base_energy * 0.45,
        size=diagonal * 0.72,
        size_y=diagonal * 0.52,
        volume_factor=0.04,
    )
    return lights, base_energy, (view, right, up)


def _object_pointer(obj: Any) -> int:
    try:
        return int(obj.as_pointer())
    except (AttributeError, TypeError, ValueError):
        return id(obj)


def _scene_up(
    entries: Sequence[tuple[Any, str]],
    roles: Mapping[int, str],
    center: Vector,
) -> Vector:
    best_normal: Vector | None = None
    best_score = -1.0
    for obj, _hint in entries:
        if roles.get(_object_pointer(obj)) != "luminaire" or obj.type != "MESH":
            continue
        normal = obj.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
        if normal.length_squared <= 1.0e-8:
            continue
        normal.normalize()
        if (_object_center(obj) - center).dot(normal) < 0.0:
            normal.negate()
        score = max((float(value) for value in obj.dimensions), default=0.0)
        if score > best_score:
            best_score = score
            best_normal = normal
    return best_normal or Vector((0.0, 0.0, 1.0))


def _setup_ceiling_lights(
    collection: Any,
    entries: Sequence[tuple[Any, str]],
    roles: Mapping[int, str],
) -> dict[str, Any]:
    lights: dict[str, Any] = {}
    wanted_names: set[str] = set()
    row_index = 0

    for obj, _hint in entries:
        if roles.get(_object_pointer(obj)) != "luminaire" or obj.type != "MESH":
            continue
        try:
            points = [vertex.co.copy() for vertex in obj.data.vertices]
        except (AttributeError, TypeError, ValueError, RuntimeError):
            continue
        if not points:
            continue

        x_values = sorted({round(point.x, 4) for point in points})
        if not x_values:
            continue
        x_span = max(x_values) - min(x_values)
        split_distance = max(x_span * 0.08, 0.18)
        x_groups: list[list[float]] = [[x_values[0]]]
        for value in x_values[1:]:
            if value - x_groups[-1][-1] > split_distance:
                x_groups.append([value])
            else:
                x_groups[-1].append(value)

        y_min = min(point.y for point in points)
        y_max = max(point.y for point in points)
        z_bottom = min(point.z for point in points)
        run_length = max(y_max - y_min, 0.5)
        segment_count = max(1, int(math.ceil(run_length / 10.0)))
        segment_length = run_length / segment_count
        normal = obj.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
        if normal.length_squared <= 1.0e-8:
            normal = Vector((0.0, 0.0, 1.0))
        else:
            normal.normalize()

        for x_group in x_groups:
            row_index += 1
            x_center = (min(x_group) + max(x_group)) * 0.5
            for segment_index in range(segment_count):
                name = f"LD_Ceiling_Panel_{row_index:02d}_{segment_index + 1:02d}"
                wanted_names.add(name)
                light = _ensure_light(collection, name, "AREA")
                y_center = y_min + (segment_index + 0.5) * segment_length
                location = obj.matrix_world @ Vector((x_center, y_center, z_bottom - 0.045))
                is_task_light = run_length < 3.0
                _configure_area_light(
                    light,
                    location=location,
                    target=location - normal,
                    color=(0.84, 0.93, 1.0),
                    energy=(
                        140.0
                        if is_task_light
                        else min(max(segment_length * 80.0, 450.0), 950.0)
                    ),
                    size=(
                        0.55
                        if is_task_light
                        else min(max(segment_length * 0.55, 3.0), 5.5)
                    ),
                    shape="DISK",
                    volume_factor=0.015,
                )
                lights[f"ceiling_{row_index:02d}_{segment_index + 1:02d}"] = light

    for obj in list(bpy.data.objects):
        if obj.name.startswith("LD_Ceiling_Panel_") and obj.name not in wanted_names:
            bpy.data.objects.remove(obj, do_unlink=True)
    return lights


def _object_center(obj: Any) -> Vector:
    if getattr(obj, "type", None) in _RENDERABLE_TYPES:
        try:
            points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            return sum(points, Vector()) / len(points)
        except (AttributeError, TypeError, ValueError, RuntimeError, ZeroDivisionError):
            pass
    try:
        return obj.matrix_world.translation.copy()
    except AttributeError:
        return Vector((0.0, 0.0, 0.0))


def _coerce_point(value: Any) -> Vector | None:
    if _is_blender_object(value):
        return _object_center(value)
    if isinstance(value, Mapping) and all(axis in value for axis in ("x", "y", "z")):
        try:
            return Vector((float(value["x"]), float(value["y"]), float(value["z"])))
        except (TypeError, ValueError):
            return None
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) >= 3:
        try:
            return Vector((float(value[0]), float(value[1]), float(value[2])))
        except (TypeError, ValueError):
            return None
    location = getattr(value, "location", None)
    if location is not None:
        try:
            return Vector(location)
        except (TypeError, ValueError):
            return None
    return None


def _find_named_value(value: Any, wanted_keys: set[str], visited: set[int] | None = None) -> Any | None:
    if visited is None:
        visited = set()
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in visited:
            return None
        visited.add(marker)
        for key, nested in value.items():
            if _normalized_label(key) in wanted_keys:
                return nested
        for nested in value.values():
            found = _find_named_value(nested, wanted_keys, visited)
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        marker = id(value)
        if marker in visited:
            return None
        visited.add(marker)
        for nested in value:
            found = _find_named_value(nested, wanted_keys, visited)
            if found is not None:
                return found
    return None


def _find_spark_anchor(assets: Any, entries: Sequence[tuple[Any, str]]) -> Vector | None:
    explicit = _find_named_value(assets, _SPARK_ANCHOR_KEYS)
    point = _coerce_point(explicit)
    if point is not None:
        return point
    for obj, hint in entries:
        normalized = _normalized_label(f"{hint} {obj.name}")
        if any(key in normalized for key in _SPARK_ANCHOR_KEYS):
            return _object_center(obj)
    wheel_asset = _find_named_value(assets, {"grinding_wheel"})
    workpiece_asset = _find_named_value(assets, {"grinding_workpiece"})
    wheel = _coerce_point(wheel_asset)
    workpiece = _coerce_point(workpiece_asset)
    if wheel is not None and workpiece is not None:
        radial_direction = wheel - workpiece
        if radial_direction.length_squared > 1.0e-8:
            radial_direction.normalize()
            try:
                wheel_radius = float(wheel_asset.get("wheel_diameter_m", 0.096)) * 0.5
            except (AttributeError, TypeError, ValueError):
                wheel_radius = 0.048
            return wheel + radial_direction * wheel_radius * 1.03
    if wheel is not None:
        return wheel
    return None


def _spark_camera_basis(
    camera: Any | None,
    origin: Vector,
    scene_up: Vector,
    fallback: tuple[Vector, Vector, Vector],
) -> tuple[Vector, Vector, Vector]:
    if camera is None:
        return fallback

    scene = bpy.context.scene
    grinding_marker = next(
        (marker for marker in scene.timeline_markers if "GRIND" in marker.name.upper()),
        None,
    )
    if grinding_marker is None:
        return _camera_basis(camera, origin, scene_up)

    original_frame = scene.frame_current
    try:
        scene.frame_set(int(grinding_marker.frame))
        bpy.context.view_layer.update()
        return _camera_basis(camera, origin, scene_up)
    finally:
        scene.frame_set(original_frame)
        bpy.context.view_layer.update()


def _ensure_spark_curves(
    collection: Any,
    origin: Vector,
    diagonal: float,
    basis: tuple[Vector, Vector, Vector],
    material: Any,
) -> Any:
    name = "LD_Grinding_Sparks"
    focus_name = f"{name}_Focus"
    for object_name in (name, focus_name):
        obj = bpy.data.objects.get(object_name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
    old_curve = bpy.data.curves.get(f"{name}_Data")
    if old_curve is not None:
        bpy.data.curves.remove(old_curve)

    curve = bpy.data.curves.new(f"{name}_Data", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_resolution = 2
    curve.bevel_depth = min(max(diagonal * 0.000025, 0.00014), 0.00035)
    curve.resolution_v = 1
    curve.materials.append(material)

    view, right, up = basis
    rng = random.Random(74291)
    travel = min(max(diagonal * 0.0018, 0.025), 0.065)
    for _ in range(3):
        spline = curve.splines.new("POLY")
        spline.points.add(2)
        fan_axis = (-right * 0.82 - up * 0.30).normalized()
        direction = (
            fan_axis
            + up * rng.uniform(-0.58, 0.62)
            + right * rng.uniform(-0.12, 0.18)
            + view * rng.uniform(-0.035, 0.045)
        ).normalized()
        length = travel * rng.uniform(0.30, 1.0)
        sideways = up * rng.uniform(-0.10, 0.10) * length
        points = (
            Vector((0.0, 0.0, 0.0)),
            direction * length * 0.52 + sideways,
            direction * length + sideways * 1.4 - up * length * rng.uniform(0.04, 0.16),
        )
        for point, value in zip(spline.points, points):
            point.co = (*value, 1.0)

    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.location = origin
    obj["lookdev_generated"] = True
    _safe_set(obj, "visible_shadow", False)

    grinding_marker = next(
        (marker for marker in bpy.context.scene.timeline_markers if "GRIND" in marker.name.upper()),
        None,
    )
    if grinding_marker is not None:
        focus_obj = bpy.data.objects.new(focus_name, curve)
        collection.objects.link(focus_obj)
        focus_obj.location = origin
        focus_obj["lookdev_generated"] = True
        focus_obj["lookdev_focus_spark"] = True
        _safe_set(focus_obj, "visible_shadow", False)
        focus_frame = int(grinding_marker.frame)
        for frame, hidden in (
            (max(1, focus_frame - 13), True),
            (max(1, focus_frame - 12), False),
            (focus_frame + 12, False),
            (focus_frame + 13, True),
        ):
            focus_obj.hide_render = hidden
            focus_obj.keyframe_insert(data_path="hide_render", frame=frame)
        focus_obj.hide_render = not (focus_frame - 12 <= bpy.context.scene.frame_current <= focus_frame + 12)
    return obj


def _setup_accents(
    assets: Any,
    entries: Sequence[tuple[Any, str]],
    roles: Mapping[int, str],
    collection: Any,
    materials: Mapping[str, Any],
    diagonal: float,
    base_energy: float,
    basis: tuple[Vector, Vector, Vector],
    camera: Any | None,
    scene_up: Vector,
) -> tuple[dict[str, Any], Any | None]:
    accents: dict[str, Any] = {}
    signal_obj = None
    visible_spark_obj = None
    for obj, _hint in entries:
        try:
            pointer = int(obj.as_pointer())
        except (AttributeError, TypeError, ValueError):
            pointer = id(obj)
        role = roles.get(pointer)
        if role == "amber_signal" and signal_obj is None:
            signal_obj = obj
        if role == "spark" and getattr(obj, "type", None) in _RENDERABLE_TYPES and visible_spark_obj is None:
            visible_spark_obj = obj

    if signal_obj is not None:
        amber = _ensure_light(collection, "LD_Amber_Accent", "POINT")
        amber.location = _object_center(signal_obj)
        amber.data.color = (1.0, 0.34, 0.018)
        amber.data.energy = min(max(base_energy * 0.008, 18.0), 90.0)
        _safe_set(amber.data, "shadow_soft_size", max(diagonal * 0.018, 0.025))
        _safe_set(amber.data, "use_shadow", False)
        _safe_set(amber.data, "volume_factor", 0.02)
        accents["amber"] = amber
    else:
        _remove_generated_object("LD_Amber_Accent")

    spark_anchor = _find_spark_anchor(assets, entries)
    sparks = visible_spark_obj
    if sparks is None and spark_anchor is not None:
        spark_basis = _spark_camera_basis(camera, spark_anchor, scene_up, basis)
        sparks = _ensure_spark_curves(
            collection,
            spark_anchor,
            diagonal,
            spark_basis,
            materials["spark"],
        )
    elif spark_anchor is None:
        _remove_generated_object("LD_Grinding_Sparks")

    if sparks is not None:
        spark_fill = _ensure_light(collection, "LD_Spark_Bounce", "POINT")
        spark_fill.location = spark_anchor if spark_anchor is not None else _object_center(sparks)
        spark_fill.data.color = (1.0, 0.20, 0.006)
        spark_fill.data.energy = min(max(base_energy * 0.004, 10.0), 50.0)
        _safe_set(spark_fill.data, "shadow_soft_size", max(diagonal * 0.008, 0.012))
        _safe_set(spark_fill.data, "use_shadow", False)
        _safe_set(spark_fill.data, "volume_factor", 0.015)
        accents["spark"] = spark_fill
    else:
        _remove_generated_object("LD_Spark_Bounce")
    return accents, sparks


def _setup_world(scene: Any) -> Any:
    world = bpy.data.worlds.get("LD_Bright_Industrial_World")
    if world is None:
        world = bpy.data.worlds.new("LD_Bright_Industrial_World")
    scene.world = world
    world.use_nodes = True
    world.color = (0.30, 0.34, 0.39)
    _clear_nodes(world.node_tree)
    nodes = world.node_tree.nodes
    output = nodes.new("ShaderNodeOutputWorld")
    output.location = (320.0, 0.0)
    background = nodes.new("ShaderNodeBackground")
    background.location = (0.0, 0.0)
    _set_socket(background, ("Color",), (0.30, 0.34, 0.39, 1.0))
    _set_socket(background, ("Strength",), 0.40)
    _link(world.node_tree, background.outputs.get("Background"), output.inputs.get("Surface"))
    return world


def _volume_material(density: float) -> Any:
    material = bpy.data.materials.get("LD_Subtle_Atmosphere") or bpy.data.materials.new("LD_Subtle_Atmosphere")
    material.use_nodes = True
    _clear_nodes(material.node_tree)
    nodes = material.node_tree.nodes
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (320.0, 0.0)
    scatter = nodes.new("ShaderNodeVolumeScatter")
    scatter.location = (0.0, 0.0)
    _set_socket(scatter, ("Color",), (0.76, 0.84, 0.92, 1.0))
    _set_socket(scatter, ("Density",), density)
    _set_socket(scatter, ("Anisotropy",), 0.55)
    _link(material.node_tree, scatter.outputs.get("Volume"), output.inputs.get("Volume"))
    return material


def _ensure_volume_box(
    collection: Any,
    minimum: Vector,
    maximum: Vector,
    camera: Any | None,
    diagonal: float,
) -> Any:
    if camera is not None:
        camera_location = camera.matrix_world.translation
        minimum = Vector((
            min(minimum.x, camera_location.x),
            min(minimum.y, camera_location.y),
            min(minimum.z, camera_location.z),
        ))
        maximum = Vector((
            max(maximum.x, camera_location.x),
            max(maximum.y, camera_location.y),
            max(maximum.z, camera_location.z),
        ))
    margin = max(diagonal * 0.28, 1.0)
    minimum -= Vector((margin, margin, margin * 0.55))
    maximum += Vector((margin, margin, margin * 0.55))
    center = (minimum + maximum) * 0.5
    size = maximum - minimum

    mesh_name = "LD_Atmosphere_Box_Data"
    mesh = bpy.data.meshes.get(mesh_name)
    if mesh is None:
        mesh = bpy.data.meshes.new(mesh_name)
        vertices = [
            (-1.0, -1.0, -1.0),
            (1.0, -1.0, -1.0),
            (1.0, 1.0, -1.0),
            (-1.0, 1.0, -1.0),
            (-1.0, -1.0, 1.0),
            (1.0, -1.0, 1.0),
            (1.0, 1.0, 1.0),
            (-1.0, 1.0, 1.0),
        ]
        faces = [
            (0, 1, 2, 3),
            (4, 7, 6, 5),
            (0, 4, 5, 1),
            (1, 5, 6, 2),
            (2, 6, 7, 3),
            (4, 0, 3, 7),
        ]
        mesh.from_pydata(vertices, [], faces)
        mesh.update()

    obj = bpy.data.objects.get("LD_Atmosphere_Box")
    if obj is not None and obj.type != "MESH":
        bpy.data.objects.remove(obj, do_unlink=True)
        obj = None
    if obj is None:
        obj = bpy.data.objects.new("LD_Atmosphere_Box", mesh)
    elif obj.data != mesh:
        obj.data = mesh
    _ensure_object_linked(obj, collection)
    obj.location = center
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = size * 0.5
    obj.display_type = "WIRE"
    obj.hide_select = True
    obj["lookdev_generated"] = True
    _safe_set(obj, "visible_shadow", False)

    density = min(max(0.0015 / max(size.length, 1.0), 0.00001), 0.00015)
    material = _volume_material(density)
    obj.data.materials.clear()
    obj.data.materials.append(material)
    return obj


def _configure_camera(camera: Any | None, collection: Any, center: Vector, diagonal: float) -> Any | None:
    if camera is None:
        return None
    dof = getattr(camera.data, "dof", None)
    if dof is not None:
        if camera.name.startswith("CIN_"):
            return getattr(dof, "focus_object", None)
        focus = getattr(dof, "focus_object", None)
        if focus is None or focus.name.startswith(_PREFIX):
            focus = _ensure_empty(collection, "LD_Product_Focus")
            focus.location = center
            focus.empty_display_type = "SPHERE"
            focus.empty_display_size = max(diagonal * 0.018, 0.05)
            focus.hide_render = True
            focus["lookdev_generated"] = True
        _safe_set(dof, "use_dof", True)
        _safe_set(dof, "focus_object", focus)
        _safe_set(dof, "focus_distance", max((camera.matrix_world.translation - center).length, 0.1))
        _safe_set(dof, "aperture_fstop", 5.6)
        _safe_set(dof, "aperture_blades", 9)
        _safe_set(dof, "aperture_rotation", math.radians(12.0))
        _safe_set(dof, "aperture_ratio", 1.0)
        return focus
    return None


def _configure_render(scene: Any) -> None:
    supported_engines: set[str] = set()
    try:
        engine_property = scene.render.bl_rna.properties["engine"]
        supported_engines = {item.identifier for item in engine_property.enum_items}
    except (AttributeError, KeyError, TypeError):
        pass

    compatible = {"CYCLES", "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"}
    if scene.render.engine not in compatible:
        for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
            if not supported_engines or engine in supported_engines:
                if _safe_set(scene.render, "engine", engine):
                    break

    _safe_set(scene.render, "film_transparent", False)
    _safe_set(scene.render, "use_motion_blur", True)
    _safe_set(scene.render, "motion_blur_shutter", 0.32)
    _safe_set(scene.render, "use_high_quality_normals", True)

    eevee = getattr(scene, "eevee", None)
    if eevee is not None:
        _safe_set(eevee, "taa_render_samples", 128)
        _safe_set(eevee, "taa_samples", 64)
        _safe_set(eevee, "use_gtao", True)
        _safe_set(eevee, "gtao_distance", 3.0)
        _safe_set(eevee, "gtao_factor", 1.15)
        _safe_set(eevee, "use_soft_shadows", True)
        _try_enum(eevee, "shadow_pool_size", ("1024", "512"))
        _safe_set(eevee, "shadow_resolution_scale", 0.75)
        _safe_set(eevee, "use_raytracing", True)
        _safe_set(eevee, "use_motion_blur", True)
        _safe_set(eevee, "motion_blur_shutter", 0.32)
        _safe_set(eevee, "motion_blur_steps", 4)
        _safe_set(eevee, "use_volumetric_lights", True)
        _safe_set(eevee, "use_volumetric_shadows", False)
        _safe_set(eevee, "volumetric_samples", 32)
        _try_enum(eevee, "volumetric_tile_size", ("4", "8", "2"))

    cycles = getattr(scene, "cycles", None)
    if cycles is not None:
        _safe_set(cycles, "samples", 192)
        _safe_set(cycles, "preview_samples", 48)
        _safe_set(cycles, "use_denoising", True)
        _safe_set(cycles, "use_preview_denoising", True)
        _safe_set(cycles, "use_adaptive_sampling", True)
        _safe_set(cycles, "adaptive_threshold", 0.02)
        _safe_set(cycles, "max_bounces", 8)
        _safe_set(cycles, "diffuse_bounces", 3)
        _safe_set(cycles, "glossy_bounces", 4)
        _safe_set(cycles, "transmission_bounces", 6)
        _safe_set(cycles, "volume_bounces", 2)
        _try_enum(cycles, "motion_blur_position", ("CENTER", "START", "END"))

    for view_layer in scene.view_layers:
        _safe_set(view_layer, "use_pass_z", True)
        _safe_set(view_layer, "use_pass_vector", True)
        _safe_set(view_layer, "use_pass_ambient_occlusion", True)

    view = scene.view_settings
    _try_enum(view, "view_transform", ("AgX", "Filmic", "Standard"))
    _try_enum(
        view,
        "look",
        (
            "AgX - Medium High Contrast",
            "Medium High Contrast",
            "AgX - Medium Low Contrast",
            "Medium Low Contrast",
            "None",
        ),
    )
    _safe_set(view, "exposure", 0.45)
    _safe_set(view, "gamma", 1.0)
    _safe_set(view, "use_curve_mapping", False)


def _compositor_tree(scene: Any) -> tuple[Any, bool]:
    if hasattr(scene, "compositing_node_group"):
        tree = scene.compositing_node_group
        if tree is None:
            tree = bpy.data.node_groups.new(f"LD_{scene.name}_Compositor", "CompositorNodeTree")
            scene.compositing_node_group = tree
        elif getattr(tree, "users", 1) > 1 and not tree.name.startswith(_PREFIX):
            tree = tree.copy()
            tree.name = f"LD_{scene.name}_Compositor"
            scene.compositing_node_group = tree
        return tree, True

    scene.use_nodes = True
    return scene.node_tree, False


def _ensure_compositor_output(tree: Any, blender_five: bool) -> Any:
    if not blender_five:
        output = next((node for node in tree.nodes if node.bl_idname == "CompositorNodeComposite"), None)
        if output is None:
            output = tree.nodes.new("CompositorNodeComposite")
        output.name = "LD_COMP_Output"
        output.location = (760.0, 0.0)
        return output

    output = next((node for node in tree.nodes if node.bl_idname == "NodeGroupOutput"), None)
    if output is None:
        output = tree.nodes.new("NodeGroupOutput")
    output.name = "LD_COMP_Output"
    output.location = (760.0, 0.0)
    _safe_set(output, "is_active_output", True)
    if _socket(output.inputs, ("Image",)) is None:
        interface = getattr(tree, "interface", None)
        if interface is not None:
            try:
                interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            except (RuntimeError, TypeError, ValueError):
                pass
    return output


def _upstream_before_lookdev(socket: Any | None) -> Any | None:
    seen: set[int] = set()
    while socket is not None:
        node = socket.node
        if not node.name.startswith("LD_COMP_"):
            return socket
        marker = id(node)
        if marker in seen:
            return None
        seen.add(marker)
        image_input = _socket(node.inputs, ("Image",))
        if image_input is None or not image_input.is_linked:
            return None
        socket = image_input.links[0].from_socket
    return None


def _setup_compositor(scene: Any) -> dict[str, Any]:
    tree, blender_five = _compositor_tree(scene)
    output = _ensure_compositor_output(tree, blender_five)
    output_input = _socket(output.inputs, ("Image",))
    source = None
    if output_input is not None and output_input.is_linked:
        source = _upstream_before_lookdev(output_input.links[0].from_socket)

    for node in list(tree.nodes):
        if node.name.startswith("LD_COMP_") and node != output:
            tree.nodes.remove(node)

    if source is None:
        render_layers = next((node for node in tree.nodes if node.bl_idname == "CompositorNodeRLayers"), None)
        if render_layers is None:
            render_layers = tree.nodes.new("CompositorNodeRLayers")
        render_layers.name = "LD_Render_Layers"
        render_layers.location = (-520.0, 0.0)
        source = _socket(render_layers.outputs, ("Image",))

    glow = tree.nodes.new("CompositorNodeGlare")
    glow.name = "LD_COMP_Soft_Glow"
    glow.label = "Restrained highlight glow"
    glow.location = (-60.0, 0.0)
    _try_enum(glow, "glare_type", ("FOG_GLOW", "BLOOM"))
    _try_enum(glow, "quality", ("HIGH", "MEDIUM"))
    if not _set_socket(glow, ("Threshold",), 2.3):
        _safe_set(glow, "threshold", 2.3)
    if not _set_socket(glow, ("Size",), 0.68):
        _safe_set(glow, "size", 7)
    if not _set_socket(glow, ("Strength",), 0.07):
        _safe_set(glow, "mix", -0.93)

    glare = tree.nodes.new("CompositorNodeGlare")
    glare.name = "LD_COMP_Lens_Glare"
    glare.label = "Subtle product lens streak"
    glare.location = (310.0, 0.0)
    _try_enum(glare, "glare_type", ("STREAKS", "SIMPLE_STAR"))
    _try_enum(glare, "quality", ("HIGH", "MEDIUM"))
    if not _set_socket(glare, ("Threshold",), 7.0):
        _safe_set(glare, "threshold", 7.0)
    if not _set_socket(glare, ("Streaks",), 4):
        _safe_set(glare, "streaks", 4)
    if not _set_socket(glare, ("Streaks Angle",), math.radians(12.0)):
        _safe_set(glare, "angle_offset", math.radians(12.0))
    if not _set_socket(glare, ("Fade",), 0.92):
        _safe_set(glare, "fade", 0.92)
    if not _set_socket(glare, ("Iterations",), 2):
        _safe_set(glare, "iterations", 2)
    if not _set_socket(glare, ("Strength",), 0.018):
        _safe_set(glare, "mix", -0.982)

    glow_input = _socket(glow.inputs, ("Image",))
    glow_output = _socket(glow.outputs, ("Image",))
    glare_input = _socket(glare.inputs, ("Image",))
    glare_output = _socket(glare.outputs, ("Image",))
    output_input = _socket(output.inputs, ("Image",))
    if output_input is not None:
        for link in list(output_input.links):
            tree.links.remove(link)
    _link(tree, source, glow_input)
    _link(tree, glow_output, glare_input)
    _link(tree, glare_output, output_input)
    return {"tree": tree, "glow": glow, "glare": glare, "output": output}


def setup_lookdev(assets: Any, camera: Any) -> dict[str, Any]:
    """Apply a bright, clean industrial product-advertising look to the scene.

    ``assets`` may be a nested mapping, collection, object, object name, or a
    sequence containing any of those.  Mapping keys and object/material names are
    used as semantic hints, so absent asset groups are simply skipped.  Optional
    custom properties ``lookdev_role`` or ``material_role`` can explicitly select
    one of: ``metal``, ``powder_coat``, ``structure``, ``rubber``, ``glass``,
    ``signal``, ``spark``, ``floor``, or ``architecture``.

    The returned dictionary exposes generated datablocks for callers that want to
    make shot-specific adjustments; callers may also ignore the return value.
    """

    scene = bpy.context.scene
    collection = _ensure_collection(scene)
    entries = _asset_entries(assets)
    resolved_camera = _resolve_camera(camera, scene)
    if resolved_camera is not None:
        scene.camera = resolved_camera

    materials = _make_materials()
    roles = _assign_materials(entries, materials)
    bound_objects = [obj for obj, _hint in entries]
    if not bound_objects:
        bound_objects = [obj for obj in scene.objects if not obj.name.startswith(_PREFIX)]
    center, size, minimum, maximum = _bounds_for_objects(bound_objects)
    diagonal = max(size.length, 1.0)
    scene_up = _scene_up(entries, roles, center)

    world = _setup_world(scene)
    lights, base_energy, basis = _setup_lights(
        collection,
        center,
        size,
        resolved_camera,
        scene_up,
    )
    lights.update(_setup_ceiling_lights(collection, entries, roles))
    accents, sparks = _setup_accents(
        assets,
        entries,
        roles,
        collection,
        materials,
        diagonal,
        base_energy,
        basis,
        resolved_camera,
        scene_up,
    )
    atmosphere = _ensure_volume_box(collection, minimum, maximum, resolved_camera, diagonal)
    focus = _configure_camera(resolved_camera, collection, center, diagonal)
    _configure_render(scene)
    compositor = _setup_compositor(scene)

    return {
        "materials": materials,
        "lights": {**lights, **accents},
        "world": world,
        "atmosphere": atmosphere,
        "sparks": sparks,
        "camera": resolved_camera,
        "focus": focus,
        "compositor": compositor,
    }
