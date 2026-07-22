"""Build a fixed-camera internal-raceway grinding proof from the production scene."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_robot_pick_place_proof import (
    _aim_object,
    _clear_animation,
    _fresh_scene_camera,
    _parent_keep_world,
    _pbr_material,
)


FRAME_START = 1
FRAME_END = 97
LOOP_FRAMES = FRAME_END - FRAME_START
FPS = 24
WORKPIECE_NAME = "SUM_GrindingCell_OuterRing_Workpiece"
WHEEL_NAME = "SUM_GrindingCell_CBN_InternalGrindingWheel"
CONTACT_NAME = "SUM_ANCHOR_GrindingContact"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--preview-output", type=Path)
    parser.add_argument("--preview-frame", type=int, default=49)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument(
        "--coolant-sprite-root",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "assets"
        / "generated"
        / "coolant-sprite-v2",
    )
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _required(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Missing grinding proof object: {name}")
    return obj


def _matrix_delta(a: Matrix, b: Matrix) -> float:
    return max(
        abs(float(x) - float(y))
        for row_a, row_b in zip(a, b)
        for x, y in zip(row_a, row_b)
    )


def _freeze_existing_animation(scene: bpy.types.Scene, source_frame: int) -> None:
    scene.frame_set(source_frame)
    bpy.context.view_layer.update()
    animated = [obj for obj in scene.objects if obj.animation_data is not None]
    matrices = {obj.name: obj.matrix_world.copy() for obj in animated}
    for obj in animated:
        obj.animation_data_clear()
    for data in (
        scene.camera.data if scene.camera else None,
        *[obj.data for obj in scene.objects if obj.type == "LIGHT"],
    ):
        if data is not None and getattr(data, "animation_data", None) is not None:
            data.animation_data_clear()
    def depth(item: bpy.types.Object) -> int:
        count = 0
        cursor = item.parent
        while cursor is not None:
            count += 1
            cursor = cursor.parent
        return count

    for obj in sorted(animated, key=depth):
        obj.matrix_world = matrices[obj.name]
    bpy.context.view_layer.update()


def _isolate_grinding_bay(scene: bpy.types.Scene) -> None:
    hidden_tokens = (
        "CoolantSplashDroplet",
        "CoolantSplashSheet",
        "LD_Grinding_Sparks",
        "ProductionSlidingDoor",
        "ProductionDoor_",
        "LeftDoor_",
        "RightDoor_",
    )
    for obj in scene.objects:
        if obj.type not in {"MESH", "CURVE"}:
            continue
        keep = obj.name.startswith(
            ("SUM_GrindingCell_", "SUM_ASSET_InternalGrinding", "SUM_PROOF_GRIND_")
        )
        hide = (not keep) or any(token in obj.name for token in hidden_tokens)
        obj.hide_render = hide
        obj["proof_visibility"] = "kept" if not hide else "cutaway_hidden"


def _configure_render(scene: bpy.types.Scene, args: argparse.Namespace) -> None:
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.render.fps = FPS
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.use_motion_blur = True
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = args.samples

    camera = _fresh_scene_camera(scene, "SUM_PROOF_GrindingCamera")
    # A three-quarter chamber view keeps the small internal wheel and raceway
    # contact readable without letting the spindle housing consume the frame.
    camera.location = (3.46, 2.28, -23.22)
    _aim_object(camera, Vector((5.58, 1.82, -25.88)))
    camera.data.lens = 78.0
    camera.data.sensor_width = 36.0
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = bpy.data.objects.get(CONTACT_NAME)
    camera.data.dof.aperture_fstop = 8.0
    camera["proof_camera_fixed"] = True
    bpy.context.view_layer.update()

    scene.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue
    scene.view_settings.exposure = -0.88

    if scene.world and scene.world.use_nodes:
        background = scene.world.node_tree.nodes.get("Background")
        if background is not None:
            background.inputs["Color"].default_value = (0.006, 0.010, 0.014, 1.0)
            background.inputs["Strength"].default_value = 0.10


def _material(name: str, color: tuple[float, float, float, float], metallic: float, roughness: float) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is None:
        raise RuntimeError(f"Material {name} has no Principled BSDF")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    if principled.inputs.get("Coat Weight"):
        principled.inputs["Coat Weight"].default_value = 0.18
    if principled.inputs.get("Coat Roughness"):
        principled.inputs["Coat Roughness"].default_value = 0.16
    material["proof_material"] = True
    return material


def _cbn_material() -> bpy.types.Material:
    material = bpy.data.materials.get("SUM_PROOF_CBN_Abrasive") or bpy.data.materials.new("SUM_PROOF_CBN_Abrasive")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = (0.18, 0.26, 0.28, 1.0)
    principled.inputs["Metallic"].default_value = 0.32
    principled.inputs["Roughness"].default_value = 0.58
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 185.0
    noise.inputs["Detail"].default_value = 7.0
    noise.inputs["Roughness"].default_value = 0.72
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.58
    bump.inputs["Distance"].default_value = 0.00075
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    material["proof_material"] = True
    material["material_role"] = "vitrified CBN bond and exposed grain response"
    return material


def _coolant_material(
    name: str,
    alpha: float,
    emission: float,
    *,
    animated_flow: bool = False,
    alpha_breakup: bool = False,
    base_color: tuple[float, float, float, float] = (0.022, 0.085, 0.060, 1.0),
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    if hasattr(material, "surface_render_method"):
        for render_method in ("BLENDED", "DITHERED"):
            try:
                material.surface_render_method = render_method
                break
            except TypeError:
                continue
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Roughness"].default_value = 0.18
    principled.inputs["Metallic"].default_value = 0.0
    if principled.inputs.get("Transmission Weight"):
        principled.inputs["Transmission Weight"].default_value = 0.08
    if principled.inputs.get("IOR"):
        principled.inputs["IOR"].default_value = 1.335
    if principled.inputs.get("Alpha"):
        principled.inputs["Alpha"].default_value = alpha
    if principled.inputs.get("Emission Color"):
        principled.inputs["Emission Color"].default_value = (0.004, 0.035, 0.018, 1.0)
    if principled.inputs.get("Emission Strength"):
        principled.inputs["Emission Strength"].default_value = emission
    coordinate = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 24.0
    noise.inputs["Detail"].default_value = 3.0
    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 13.0
    wave.inputs["Distortion"].default_value = 3.2
    wave.inputs["Detail"].default_value = 2.0
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.62
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.004
    links.new(coordinate.outputs["Generated"], noise.inputs["Vector"])
    links.new(coordinate.outputs["Generated"], wave.inputs["Vector"])
    links.new(noise.outputs["Fac"], mix.inputs[1])
    links.new(wave.outputs["Color"], mix.inputs[2])
    links.new(mix.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    if alpha_breakup and principled.inputs.get("Alpha"):
        alpha_modulation = nodes.new("ShaderNodeMath")
        alpha_modulation.operation = "MULTIPLY"
        alpha_modulation.inputs[1].default_value = alpha * 2.7
        alpha_floor = nodes.new("ShaderNodeMath")
        alpha_floor.operation = "ADD"
        alpha_floor.inputs[1].default_value = 0.022
        links.new(mix.outputs["Color"], alpha_modulation.inputs[0])
        links.new(alpha_modulation.outputs["Value"], alpha_floor.inputs[0])
        links.new(alpha_floor.outputs["Value"], principled.inputs["Alpha"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    phase = wave.inputs.get("Phase Offset")
    if animated_flow and phase is not None:
        phase.default_value = 0.0
        phase.keyframe_insert("default_value", frame=FRAME_START)
        phase.default_value = math.tau
        phase.keyframe_insert("default_value", frame=FRAME_END)
        action = material.node_tree.animation_data.action
        if action is not None:
            for curve in action.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation = "LINEAR"
        material["proof_flow_loop"] = True
    material["proof_material"] = True
    return material


def _spark_material() -> bpy.types.Material:
    material = bpy.data.materials.get("SUM_PROOF_WetGrindingSpark") or bpy.data.materials.new("SUM_PROOF_WetGrindingSpark")
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (1.0, 0.38, 0.015, 1.0)
    principled.inputs["Roughness"].default_value = 0.22
    principled.inputs["Emission Color"].default_value = (1.0, 0.12, 0.003, 1.0)
    principled.inputs["Emission Strength"].default_value = 28.0
    material["proof_material"] = True
    return material


def _replace_foreground_materials(scene: bpy.types.Scene, material_root: Path) -> dict[str, object]:
    materials = {
        "machined": _pbr_material(
            "SUM_PROOF_GRIND_MachinedSteel",
            material_root,
            "Metal012",
            tint=(0.080, 0.105, 0.120, 1.0),
            metallic_default=1.0,
            roughness_default=0.24,
            normal_strength=0.025,
            texture_scale=2.2,
            use_roughness_texture=False,
        ),
        "sheet": _pbr_material(
            "SUM_PROOF_GRIND_SheetSteel",
            material_root,
            "Metal049A",
            tint=(0.055, 0.070, 0.082, 1.0),
            metallic_default=0.82,
            roughness_default=0.37,
            normal_strength=0.025,
            texture_scale=2.0,
            use_roughness_texture=False,
        ),
        "graphite": _pbr_material(
            "SUM_PROOF_GRIND_GraphiteCoat",
            material_root,
            "Metal049A",
            tint=(0.010, 0.016, 0.020, 1.0),
            metallic_default=0.08,
            roughness_default=0.54,
            normal_strength=0.020,
            texture_scale=2.0,
            use_roughness_texture=False,
        ),
        "wet": _pbr_material(
            "SUM_PROOF_GRIND_WetMachinedSteel",
            material_root,
            "Metal012",
            tint=(0.060, 0.085, 0.095, 1.0),
            metallic_default=1.0,
            roughness_default=0.13,
            normal_strength=0.018,
            texture_scale=2.0,
            use_roughness_texture=False,
        ),
        "rubber": _pbr_material(
            "SUM_PROOF_GRIND_RubberHose",
            material_root,
            "Rubber002",
            tint=(0.012, 0.018, 0.020, 1.0),
            metallic_default=0.0,
            roughness_default=0.68,
            normal_strength=0.16,
            texture_scale=5.0,
            use_roughness_texture=False,
        ),
        "black_oxide": _material("SUM_PROOF_GRIND_BlackOxide", (0.012, 0.017, 0.019, 1.0), 0.68, 0.34),
        "cbn": _cbn_material(),
        "coolant": _coolant_material(
            "SUM_PROOF_GRIND_CoolantCore",
            0.52,
            0.01,
            animated_flow=True,
            base_color=(0.16, 0.22, 0.20, 1.0),
        ),
    }
    replaced = 0
    for obj in scene.objects:
        if obj.type not in {"MESH", "CURVE"} or obj.hide_render:
            continue
        role = str(obj.get("lookdev_role", "")).lower()
        name = obj.name.lower()
        if "coolantjet_stream" in name:
            chosen = materials["coolant"]
        elif "coolant" in role and "pool" in name:
            chosen = materials["coolant"]
        elif any(
            token in f"{role} {name}"
            for token in ("cable", "hose", "rubber", "bellows", "conduit", "pneumatic", "hydraulic")
        ):
            chosen = materials["rubber"]
        elif "cbn" in name or "abrasive" in role:
            chosen = materials["cbn"]
        elif any(token in role for token in ("black_oxide", "dark_metal", "tool_steel")):
            chosen = materials["black_oxide"]
        elif any(token in role for token in ("fresh_ground", "wet_steel")):
            chosen = materials["wet"]
        elif any(token in role for token in ("machined", "workpiece", "brushed")):
            chosen = materials["machined"]
        elif any(token in role for token in ("powder", "cast_iron", "dark")) or any(
            token in name for token in ("housing", "support", "panel", "carriage", "mount", "motor")
        ):
            chosen = materials["graphite"]
        else:
            chosen = materials["sheet"]
        if hasattr(obj.data, "materials"):
            obj.data.materials.clear()
            obj.data.materials.append(chosen)
            obj["proof_material_name"] = chosen.name
            replaced += 1
    return {"objects_replaced": replaced, "library": "ambientCG CC0 + authored process shaders"}


def _spin_driver(obj: bpy.types.Object, name: str, turns: int) -> bpy.types.Object:
    world = obj.matrix_world.copy()
    parent = obj.parent
    collection = obj.users_collection[0] if obj.users_collection else bpy.context.scene.collection
    orientation = bpy.data.objects.new(f"{name}_Orientation", None)
    collection.objects.link(orientation)
    orientation.parent = parent
    orientation.matrix_world = world
    bpy.context.view_layer.update()
    orientation["proof_role"] = "fixed_spindle_orientation_frame"

    driver = bpy.data.objects.new(name, None)
    collection.objects.link(driver)
    driver.parent = orientation
    driver.matrix_parent_inverse = Matrix.Identity(4)
    driver.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()

    # The orientation empty now carries the object's complete frozen world
    # transform. Keep both inserted levels at identity so Blender cannot apply
    # that transform a second time when evaluating the new parent hierarchy.
    obj.parent = driver
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj.delta_location = (0.0, 0.0, 0.0)
    obj.delta_rotation_euler = (0.0, 0.0, 0.0)
    obj.delta_rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    obj.delta_scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()

    hierarchy_delta = _matrix_delta(obj.matrix_world, world)
    if hierarchy_delta > 5.0e-6:
        raise RuntimeError(f"Spin hierarchy changed {obj.name}'s frozen world transform")

    driver.rotation_mode = "XYZ"
    for frame, angle in ((FRAME_START, 0.0), (FRAME_END, math.tau * turns)):
        driver.rotation_euler = (0.0, 0.0, angle)
        driver.keyframe_insert("rotation_euler", index=2, frame=frame)
    if driver.animation_data and driver.animation_data.action:
        for curve in driver.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
    driver["proof_spin_turns"] = turns
    driver["proof_spin_axis_local"] = [0.0, 0.0, 1.0]
    obj["rotation_axis_local"] = [0.0, 0.0, 1.0]
    return driver


def _shared_ico_mesh(name: str, subdivisions: int = 1) -> bpy.types.Mesh:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0)
    source = bpy.context.active_object
    source.name = f"{name}_Source"
    mesh = source.data
    mesh.name = f"{name}_Mesh"
    bpy.data.objects.remove(source, do_unlink=True)
    return mesh


def _new_particle(name: str, mesh: bpy.types.Mesh, material: bpy.types.Material) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if not mesh.materials:
        mesh.materials.append(material)
    obj.rotation_mode = "QUATERNION"
    obj["proof_particle"] = True
    return obj


def _coolant_sprite_material(sprite_root: Path) -> bpy.types.Material:
    first_frame = sprite_root / "coolant_0001.png"
    if not first_frame.is_file():
        raise RuntimeError(f"Missing coolant sprite sequence: {first_frame}")
    image = bpy.data.images.load(str(first_frame), check_existing=True)
    image.source = "SEQUENCE"

    material = bpy.data.materials.get("SUM_PROOF_GRIND_CoolantSprite") or bpy.data.materials.new(
        "SUM_PROOF_GRIND_CoolantSprite"
    )
    material.use_nodes = True
    if hasattr(material, "surface_render_method"):
        for render_method in ("DITHERED", "BLENDED"):
            try:
                material.surface_render_method = render_method
                break
            except TypeError:
                continue
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "CLIP"
    texture.image_user.frame_duration = LOOP_FRAMES
    texture.image_user.frame_start = FRAME_START
    texture.image_user.frame_offset = 0
    texture.image_user.use_auto_refresh = True
    texture.image_user.use_cyclic = True
    principled.inputs["Base Color"].default_value = (0.18, 0.24, 0.22, 1.0)
    principled.inputs["Metallic"].default_value = 0.0
    principled.inputs["Roughness"].default_value = 0.12
    if principled.inputs.get("Emission Strength"):
        principled.inputs["Emission Strength"].default_value = 0.35
    links.new(texture.outputs["Color"], principled.inputs["Base Color"])
    if principled.inputs.get("Emission Color"):
        links.new(texture.outputs["Color"], principled.inputs["Emission Color"])
    links.new(texture.outputs["Alpha"], principled.inputs["Alpha"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    material["proof_material"] = True
    material["proof_flow_loop"] = True
    material["proof_sprite_frames"] = LOOP_FRAMES
    material["proof_sprite_source"] = str(first_frame)
    return material


def _coolant_sprite_plane(contact: Vector, sprite_root: Path) -> bpy.types.Object:
    camera = bpy.context.scene.camera
    if camera is None:
        raise RuntimeError("Grinding proof camera is required before adding coolant sprite")
    right = (camera.matrix_world.to_quaternion() @ Vector((1.0, 0.0, 0.0))).normalized()
    up = (camera.matrix_world.to_quaternion() @ Vector((0.0, 1.0, 0.0))).normalized()
    to_camera = (camera.matrix_world.translation - contact).normalized()
    width = 0.38
    height = 0.38
    impact_from_top = 0.299
    center = contact + to_camera * 0.064 - up * ((0.5 - impact_from_top) * height)
    half_right = right * (width * 0.5)
    half_up = up * (height * 0.5)
    vertices = (
        center - half_right - half_up,
        center + half_right - half_up,
        center + half_right + half_up,
        center - half_right + half_up,
    )
    mesh = bpy.data.meshes.new("SUM_PROOF_GRIND_CoolantSprite_Mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop, uv in zip(uv_layer.data, ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))):
        loop.uv = uv
    mesh.materials.append(_coolant_sprite_material(sprite_root))
    obj = bpy.data.objects.new("SUM_PROOF_GRIND_ContactSplashSprite", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["proof_fluid_sheet"] = True
    obj["proof_fluid_sprite"] = True
    obj["proof_role"] = "continuous_contact_splash_sprite"
    obj["proof_impact_uv"] = [0.5, impact_from_top]
    return obj


def _key_particle(obj: bpy.types.Object, frame: int, location: Vector, scale: Vector, direction: Vector | None = None) -> None:
    obj.location = location
    obj.scale = scale
    if direction is not None and direction.length > 1.0e-8:
        obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())
        obj.keyframe_insert("rotation_quaternion", frame=frame)
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("scale", frame=frame)


def _linearize(obj: bpy.types.Object) -> None:
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = "LINEAR"


def _curve_world_points(obj: bpy.types.Object) -> tuple[Vector, Vector, Vector]:
    points: list[Vector] = []
    for spline in obj.data.splines:
        if spline.type == "BEZIER":
            points.extend(obj.matrix_world @ point.co for point in spline.bezier_points)
        else:
            points.extend(obj.matrix_world @ Vector(point.co[:3]) for point in spline.points)
    if len(points) < 3:
        raise RuntimeError(f"{obj.name} does not provide a three-point coolant path")
    return points[0], points[len(points) // 2], points[-1]


def _quadratic(p0: Vector, p1: Vector, p2: Vector, t: float) -> tuple[Vector, Vector]:
    point = p0 * ((1.0 - t) ** 2) + p1 * (2.0 * (1.0 - t) * t) + p2 * (t * t)
    tangent = (p1 - p0) * (2.0 * (1.0 - t)) + (p2 - p1) * (2.0 * t)
    return point, tangent


def _build_fluid_and_sparks(
    contact: Vector,
    wheel_axis: Vector,
    wheel_center: Vector,
    coolant_material: bpy.types.Material,
    coolant_sprite_root: Path,
) -> dict[str, object]:
    droplet_material = _coolant_material(
        "SUM_PROOF_GRIND_CoolantDroplet",
        0.12,
        0.002,
        base_color=(0.16, 0.23, 0.20, 1.0),
    )
    mist_material = _coolant_material(
        "SUM_PROOF_GRIND_CoolantMist",
        0.024,
        0.0005,
        base_color=(0.22, 0.27, 0.25, 1.0),
    )
    spark_material = _spark_material()
    fluid_mesh = _shared_ico_mesh("SUM_PROOF_GRIND_Fluid", subdivisions=2)
    mist_mesh = _shared_ico_mesh("SUM_PROOF_GRIND_Mist", subdivisions=2)
    spark_mesh = _shared_ico_mesh("SUM_PROOF_GRIND_Spark", subdivisions=1)
    stream_objects = [
        _required("SUM_GrindingCell_CoolantJet_Stream_01"),
        _required("SUM_GrindingCell_CoolantJet_Stream_02"),
    ]
    for stream in stream_objects:
        stream.hide_render = False
        stream.data.materials.clear()
        stream.data.materials.append(coolant_material)
        stream.data.bevel_depth = 0.0085
        stream.data.bevel_resolution = 5

    particles: list[bpy.types.Object] = []

    radial = (contact - wheel_center).normalized()
    tangent = wheel_axis.cross(radial).normalized()
    up = Vector((0.0, 1.0, 0.0))
    to_camera = (bpy.context.scene.camera.matrix_world.translation - contact).normalized()
    fluid_sheets = [_coolant_sprite_plane(contact, coolant_sprite_root)]
    rng = random.Random(20260722)
    for index in range(60):
        phase = (index / 60.0 + rng.uniform(-0.006, 0.006)) % 1.0
        velocity = (
            tangent * rng.uniform(0.10, 0.26)
            + up * rng.uniform(-0.015, 0.075)
            + radial * rng.uniform(-0.035, 0.055)
            + wheel_axis * rng.uniform(-0.040, 0.040)
            + to_camera * rng.uniform(0.018, 0.065)
        )
        radius = rng.uniform(0.00038, 0.00105)
        particle = _new_particle(f"SUM_PROOF_GRIND_Splash_{index + 1:02d}", fluid_mesh, droplet_material)
        particle["proof_particle_role"] = "ballistic_coolant_droplet"
        for frame in range(FRAME_START, FRAME_END + 1):
            cycle = ((frame - FRAME_START) / LOOP_FRAMES + phase) % 1.0
            life = cycle / 0.46
            if life >= 1.0:
                scale = Vector((0.00001, 0.00001, 0.00001))
                location = contact
                direction = velocity
            else:
                location = contact + velocity * life + up * (-0.16 * life * life)
                direction = velocity + up * (-0.32 * life)
                envelope = max(math.sin(math.pi * life), 0.0) ** 2.0
                scale = Vector(
                    (
                        max(radius * 0.55 * envelope, 0.00001),
                        max(radius * 0.55 * envelope, 0.00001),
                        max(radius * (1.2 + 1.8 * envelope) * envelope, 0.00001),
                    )
                )
            _key_particle(particle, frame, location, scale, direction)
        _linearize(particle)
        particles.append(particle)

    for index in range(16):
        phase = (index / 16.0 + rng.uniform(-0.012, 0.012)) % 1.0
        offset = tangent * rng.uniform(-0.03, 0.05) + up * rng.uniform(-0.015, 0.035) + wheel_axis * rng.uniform(-0.04, 0.04)
        mist = _new_particle(f"SUM_PROOF_GRIND_Mist_{index + 1:02d}", mist_mesh, mist_material)
        mist["proof_particle_role"] = "fine_coolant_mist"
        for frame in range(FRAME_START, FRAME_END + 1):
            progress = ((frame - FRAME_START) / LOOP_FRAMES + phase) % 1.0
            pulse = 0.78 + 0.22 * math.sin(math.tau * progress) ** 2
            location = contact + offset + up * (0.025 * math.sin(math.tau * progress))
            _key_particle(mist, frame, location, Vector((0.007, 0.014, 0.010)) * pulse)
        _linearize(mist)
        particles.append(mist)

    sparks: list[bpy.types.Object] = []
    spark_events = (31, 68)
    for index in range(6):
        event_start = spark_events[index // 3] + (index % 3) - 1
        visible_frames = 3 + (index % 2)
        direction = (
            tangent * rng.uniform(0.12, 0.24)
            + up * rng.uniform(0.015, 0.055)
            + wheel_axis * rng.uniform(-0.08, 0.08)
            + to_camera * rng.uniform(0.06, 0.12)
        )
        spark = _new_particle(f"SUM_PROOF_GRIND_Spark_{index + 1:02d}", spark_mesh, spark_material)
        spark["proof_particle_role"] = "sparse_wet_grinding_spark"
        spark["proof_burst_start"] = event_start
        spark["proof_burst_frames"] = visible_frames
        for frame in range(FRAME_START, FRAME_END + 1):
            local_frame = frame - event_start
            if local_frame < 0 or local_frame >= visible_frames:
                location = contact + to_camera * 0.060
                scale = Vector((0.00001, 0.00001, 0.00001))
            else:
                life = (local_frame + 1) / (visible_frames + 1)
                location = contact + to_camera * 0.060 + direction * (life * 0.09) + up * (-0.015 * life * life)
                envelope = max(math.sin(math.pi * life), 0.0) ** 3.0
                scale = Vector(
                    (
                        max(0.00085 * envelope, 0.00001),
                        max(0.00085 * envelope, 0.00001),
                        max(0.014 * envelope, 0.00001),
                    )
                )
            _key_particle(spark, frame, location, scale, direction)
        _linearize(spark)
        particles.append(spark)
        sparks.append(spark)

    return {
        "particle_count": len(particles),
        "spark_count": len(sparks),
        "coolant_stream_count": len(stream_objects),
        "fluid_sheet_count": len(fluid_sheets),
        "fluid_sprite_count": sum(bool(obj.get("proof_fluid_sprite")) for obj in fluid_sheets),
        "fluid_sprite_root": str(coolant_sprite_root),
        "particle_names": [obj.name for obj in particles],
    }


def _add_light(name: str, location: Vector, target: Vector, energy: float, size: float, color: tuple[float, float, float]) -> None:
    data = bpy.data.lights.new(f"{name}_Data", type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    light = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    _aim_object(light, target)
    light["proof_light"] = True


def _build() -> tuple[dict[str, object], argparse.Namespace]:
    args = _args()
    args.scene_output = args.scene_output.resolve()
    args.report = args.report.resolve()
    args.coolant_sprite_root = args.coolant_sprite_root.resolve()
    if args.preview_output is not None:
        args.preview_output = args.preview_output.resolve()
    scene = bpy.context.scene
    source_frame = 301
    scene.frame_set(source_frame)
    _freeze_existing_animation(scene, source_frame)
    _isolate_grinding_bay(scene)
    _configure_render(scene, args)
    frozen_camera = scene.camera.matrix_world.copy()
    frozen_lens = float(scene.camera.data.lens)

    workpiece = _required(WORKPIECE_NAME)
    wheel = _required(WHEEL_NAME)
    contact_obj = _required(CONTACT_NAME)
    contact = contact_obj.matrix_world.translation.copy()
    material_root = Path(__file__).resolve().parents[1] / "assets" / "local-library" / "ambientcg"
    material_report = _replace_foreground_materials(scene, material_root)
    coolant_material = bpy.data.materials["SUM_PROOF_GRIND_CoolantCore"]

    work_driver = _spin_driver(workpiece, "SUM_PROOF_GRIND_WorkpieceSpinDriver", 4)
    wheel_driver = _spin_driver(wheel, "SUM_PROOF_GRIND_WheelSpinDriver", 72)
    for name in (
        "SUM_GrindingCell_FreshGround_RacewayBand",
        "SUM_GrindingCell_Workpiece_RotationDatumEtch",
    ):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            _parent_keep_world(obj, work_driver)
            obj["proof_spin_group"] = "work spindle"
    for name in (
        "SUM_GrindingCell_CBN_VitrifiedBondBody",
        "SUM_GrindingCell_CBN_ProfiledAbrasiveLayer",
        "SUM_GrindingCell_CBN_ExposedAbrasiveCrystals",
    ):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            _parent_keep_world(obj, wheel_driver)
            obj["proof_spin_group"] = "grinding spindle"
    scene.frame_set(FRAME_START)
    wheel_axis = (wheel.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
    work_axis = (workpiece.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
    wheel_center = wheel.matrix_world.translation.copy()
    work_center = workpiece.matrix_world.translation.copy()

    datum = bpy.data.objects.get("SUM_GrindingCell_Workpiece_RotationDatumEtch")
    if datum is not None:
        datum.hide_render = False
        datum.location += work_axis * 0.0025
        datum.scale *= 1.15
        datum.data.materials.clear()
        datum.data.materials.append(
            _material(
                "SUM_PROOF_GRIND_RotationWitness",
                (0.055, 0.070, 0.078, 1.0),
                0.48,
                0.52,
            )
        )
        datum["proof_role"] = "workpiece_rotation_witness_mark"

    dynamics = _build_fluid_and_sparks(
        contact,
        wheel_axis,
        wheel_center,
        coolant_material,
        args.coolant_sprite_root,
    )
    _add_light(
        "SUM_PROOF_GRIND_Key",
        contact + Vector((-0.80, 0.95, 0.65)),
        contact,
        840.0,
        1.55,
        (0.76, 0.88, 1.0),
    )
    _add_light(
        "SUM_PROOF_GRIND_Rim",
        contact + Vector((0.75, 0.45, -0.55)),
        contact,
        460.0,
        0.85,
        (1.0, 0.72, 0.48),
    )

    scene.frame_set(FRAME_START)
    first_camera = scene.camera.matrix_world.copy()
    first_workpiece = workpiece.matrix_world.copy()
    first_wheel = wheel.matrix_world.copy()
    particle_first = {
        name: bpy.data.objects[name].matrix_world.copy()
        for name in dynamics["particle_names"]
    }
    scene.frame_set(FRAME_END)
    last_camera = scene.camera.matrix_world.copy()
    last_workpiece = workpiece.matrix_world.copy()
    last_wheel = wheel.matrix_world.copy()
    particle_seam_delta = max(
        _matrix_delta(particle_first[name], bpy.data.objects[name].matrix_world)
        for name in dynamics["particle_names"]
    )

    radial_work = contact - work_center
    radial_work -= work_axis * radial_work.dot(work_axis)
    radial_wheel = contact - wheel_center
    radial_wheel -= wheel_axis * radial_wheel.dot(wheel_axis)
    report: dict[str, object] = {
        "status": "mechanical-proof-generated",
        "source_scene": bpy.data.filepath,
        "frames": [FRAME_START, FRAME_END],
        "encoded_loop_frames": LOOP_FRAMES,
        "fps": FPS,
        "camera_fixed": _matrix_delta(first_camera, last_camera) <= 1.0e-7,
        "workpiece_axis_world": list(work_axis),
        "wheel_axis_world": list(wheel_axis),
        "axis_parallel_dot": abs(float(work_axis.dot(wheel_axis))),
        "workpiece_axis_up_dot": abs(float(work_axis.dot(Vector((0.0, 1.0, 0.0))))),
        "wheel_axis_up_dot": abs(float(wheel_axis.dot(Vector((0.0, 1.0, 0.0))))),
        "workpiece_contact_radius_m": radial_work.length,
        "wheel_contact_radius_m": radial_wheel.length,
        "workpiece_loop_matrix_delta": _matrix_delta(first_workpiece, last_workpiece),
        "wheel_loop_matrix_delta": _matrix_delta(first_wheel, last_wheel),
        "particle_loop_matrix_delta": particle_seam_delta,
        "workpiece_turns": int(work_driver["proof_spin_turns"]),
        "wheel_turns": int(wheel_driver["proof_spin_turns"]),
        "material_pass": material_report,
        "dynamics": {key: value for key, value in dynamics.items() if key != "particle_names"},
        "camera_matrix": [[float(value) for value in row] for row in frozen_camera],
    }
    args.scene_output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.scene_output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.preview_output is not None:
        args.preview_output.parent.mkdir(parents=True, exist_ok=True)
        scene.frame_set(max(FRAME_START, min(args.preview_frame, FRAME_END)))
        scene.render.filepath = str(args.preview_output)
        bpy.ops.render.render(write_still=True)
    return report, args


if __name__ == "__main__":
    built, _ = _build()
    print("SUM_GRINDING_PROOF=" + json.dumps(built))
