"""Build a fixed-camera KR210 pick-place proof from the production scene.

Run this script with Blender after opening `production/scenes/felix-journey-desktop.blend`.
It replaces the rejected pose-table/visibility-swap hold with target-solved motion
and one continuously animated workpiece.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector


JOINT_NAMES = tuple(
    f"SUM_KUKA_KR210_J{index}_{label}_Axis"
    for index, label in enumerate(("A1", "A2", "A3", "A4", "A5", "A6"), 1)
)
TCP_NAME = "SUM_KUKA_KR210_Tool0"
HELD_PROXY_NAMES = (
    "SUM_KUKA_Gripper_HeldBearingRing_WIP",
    "SUM_KUKA_Gripper_HeldBearingRing_RacewayWitness",
)
TRANSFER_RING_NAME = "SUM_RobotCell_InfeedBearingRing_02"
NEXT_RING_NAME = "SUM_RobotCell_InfeedBearingRing_03"
UPSTREAM_RING_NAME = "SUM_RobotCell_InfeedBearingRing_04"
NEW_RING_NAME = "SUM_RobotCell_InfeedBearingRing_05"
NEST_RING_NAME = "SUM_RobotCell_HandoffNest_BearingRing"
PICK_RING_NAME = "SUM_RobotCell_InfeedBearingRing_02"
PLACE_RING_NAME = "SUM_RobotCell_HandoffNest_BearingRing"
FRAME_END = 159
FPS = 24
GRASP_BEGIN_FRAME = 35
GRASP_FRAME = 47
PLACE_FRAME = 110
RELEASE_FRAME = 122
INDEX_FRAME = 137
HOME_RETURN_FRAME = 158


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--preview-output", type=Path)
    parser.add_argument("--preview-frame", type=int, default=70)
    parser.add_argument("--samples", type=int, default=48)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _required(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Missing required proof object: {name}")
    return obj


def _matrix_payload(matrix: Matrix) -> list[list[float]]:
    return [[round(float(value), 7) for value in row] for row in matrix]


def _clear_animation(owner: bpy.types.ID) -> None:
    if getattr(owner, "animation_data", None) is not None:
        owner.animation_data_clear()


def _fresh_scene_camera(scene: bpy.types.Scene, name: str) -> bpy.types.Object:
    existing = bpy.data.objects.get(name)
    if existing is not None:
        bpy.data.objects.remove(existing, do_unlink=True)
    source = scene.camera
    data = source.data.copy() if source is not None else bpy.data.cameras.new(f"{name}_Data")
    data.name = f"{name}_Data"
    _clear_animation(data)
    camera = bpy.data.objects.new(name, data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    return camera


def _quaternion_error(target: Quaternion, current: Quaternion) -> Vector:
    delta = target @ current.inverted()
    if delta.w < 0.0:
        delta.negate()
    axis, angle = delta.to_axis_angle()
    if angle > math.pi:
        angle -= math.tau
    return axis * angle


class RobotSolver:
    def __init__(
        self,
        joints: list[bpy.types.Object],
        tcp: bpy.types.Object,
        payload_relative_to_tcp: Matrix,
        *,
        full_orientation: bool = True,
    ):
        self.joints = joints
        self.tcp = tcp
        self.payload_relative_to_tcp = payload_relative_to_tcp.copy()
        self.full_orientation = full_orientation
        self.axes = [tuple(float(value) for value in joint.rotation_axis_angle[1:]) for joint in joints]
        self.limits = tuple(
            (math.radians(low), math.radians(high))
            for low, high in (
                (-185.0, 185.0),
                (-145.0, 145.0),
                (-160.0, 160.0),
                (-350.0, 350.0),
                (-135.0, 135.0),
                (-350.0, 350.0),
            )
        )

    def set_angles(self, angles: np.ndarray) -> None:
        for joint, axis, value in zip(self.joints, self.axes, angles):
            joint.rotation_mode = "AXIS_ANGLE"
            joint.rotation_axis_angle = (float(value), *axis)
        bpy.context.view_layer.update()

    def angles(self) -> np.ndarray:
        return np.array([float(joint.rotation_axis_angle[0]) for joint in self.joints])

    def residual(self, target_payload: Matrix) -> np.ndarray:
        current_payload = self.tcp.matrix_world @ self.payload_relative_to_tcp
        position = target_payload.translation - current_payload.translation
        if self.full_orientation:
            orientation = _quaternion_error(
                target_payload.to_quaternion(), current_payload.to_quaternion()
            )
        else:
            current_axis = (
                current_payload.to_3x3() @ Vector((0.0, 0.0, 1.0))
            ).normalized()
            target_axis = (
                target_payload.to_3x3() @ Vector((0.0, 0.0, 1.0))
            ).normalized()
            delta = current_axis.rotation_difference(target_axis)
            axis, angle = delta.to_axis_angle()
            orientation = axis * angle
        return np.array((*position, *(orientation * 0.62)), dtype=float)

    def errors(self, target_payload: Matrix) -> tuple[float, float]:
        current_payload = self.tcp.matrix_world @ self.payload_relative_to_tcp
        position_error = (target_payload.translation - current_payload.translation).length
        if self.full_orientation:
            orientation_error = _quaternion_error(
                target_payload.to_quaternion(), current_payload.to_quaternion()
            ).length
        else:
            current_axis = (
                current_payload.to_3x3() @ Vector((0.0, 0.0, 1.0))
            ).normalized()
            target_axis = (
                target_payload.to_3x3() @ Vector((0.0, 0.0, 1.0))
            ).normalized()
            orientation_error = math.acos(
                max(-1.0, min(1.0, float(current_axis.dot(target_axis))))
            )
        return position_error, orientation_error

    def solve(self, target: Matrix, seed: np.ndarray, label: str) -> tuple[np.ndarray, dict[str, float | int | str]]:
        angles = seed.copy()
        self.set_angles(angles)
        damping = 2.5e-3
        epsilon = 2.0e-4
        best_angles = angles.copy()
        best_norm = float("inf")

        for iteration in range(320):
            residual = self.residual(target)
            residual_norm = float(np.linalg.norm(residual))
            if residual_norm < best_norm:
                best_norm = residual_norm
                best_angles = angles.copy()
            position_error, orientation_error = self.errors(target)
            position_tolerance = 0.00015 if self.full_orientation else 0.003
            orientation_tolerance = math.radians(0.05 if self.full_orientation else 0.8)
            if position_error < position_tolerance and orientation_error < orientation_tolerance:
                return angles, {
                    "label": label,
                    "iterations": iteration,
                    "position_error_m": position_error,
                    "orientation_error_deg": math.degrees(orientation_error),
                }

            jacobian = np.zeros((6, 6), dtype=float)
            for column in range(6):
                perturbed = angles.copy()
                perturbed[column] += epsilon
                self.set_angles(perturbed)
                jacobian[:, column] = (self.residual(target) - residual) / epsilon
            self.set_angles(angles)

            lhs = jacobian.T @ jacobian + damping * np.eye(6)
            rhs = -(jacobian.T @ residual)
            step = np.linalg.solve(lhs, rhs)
            step = np.clip(step, -0.14, 0.14)

            accepted = False
            for scale in (1.0, 0.55, 0.25, 0.10):
                candidate = angles + step * scale
                candidate = np.array(
                    [
                        np.clip(value, low, high)
                        for value, (low, high) in zip(candidate, self.limits)
                    ]
                )
                self.set_angles(candidate)
                if np.linalg.norm(self.residual(target)) < residual_norm:
                    angles = candidate
                    accepted = True
                    break
            if not accepted:
                damping = min(damping * 2.0, 0.4)
                self.set_angles(angles)
            else:
                damping = max(damping * 0.82, 4.0e-5)

        self.set_angles(best_angles)
        position_error, orientation_error = self.errors(target)
        raise RuntimeError(
            f"IK failed for {label}: position={position_error:.4f}m "
            f"axis={math.degrees(orientation_error):.2f}deg"
        )


def _key_joint_pose(joints: list[bpy.types.Object], frame: int, angles: np.ndarray) -> None:
    for joint, angle in zip(joints, angles):
        joint.rotation_axis_angle[0] = float(angle)
        joint.keyframe_insert("rotation_axis_angle", index=0, frame=frame)


def _key_joint_s_curve(
    joints: list[bpy.types.Object],
    pose_keys: tuple[tuple[int, str], ...],
    solved: dict[str, np.ndarray],
) -> None:
    for segment_index in range(len(pose_keys) - 1):
        start_frame, start_pose = pose_keys[segment_index]
        end_frame, end_pose = pose_keys[segment_index + 1]
        start_angles = solved[start_pose]
        end_angles = solved[end_pose]
        first = start_frame if segment_index == 0 else start_frame + 1
        for frame in range(first, end_frame + 1):
            t = (frame - start_frame) / max(end_frame - start_frame, 1)
            blend = t * t * t * (10.0 + t * (-15.0 + 6.0 * t))
            _key_joint_pose(joints, frame, start_angles + (end_angles - start_angles) * blend)
    for joint in joints:
        _linearize(joint)


def _rigid_matrix(matrix: Matrix) -> Matrix:
    location, rotation, _ = matrix.decompose()
    return Matrix.Translation(location) @ rotation.to_matrix().to_4x4()


def _set_key_interpolation(owner: bpy.types.Object) -> None:
    action = owner.animation_data.action if owner.animation_data else None
    if action is None:
        return
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
            point.handle_left_type = "AUTO_CLAMPED"
            point.handle_right_type = "AUTO_CLAMPED"


def _key_world_matrix(obj: bpy.types.Object, frame: int, matrix: Matrix) -> None:
    obj.matrix_world = _rigid_matrix(matrix)
    obj.rotation_mode = "QUATERNION"
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_quaternion", frame=frame)
    obj.scale = (1.0, 1.0, 1.0)


def _linearize(owner: bpy.types.Object) -> None:
    action = owner.animation_data.action if owner.animation_data else None
    if action is None:
        return
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = "LINEAR"


def _load_texture(root: Path, asset: str, suffix: str) -> bpy.types.Image:
    matches = sorted((root / asset).glob(f"*{suffix}"))
    if not matches:
        raise FileNotFoundError(f"Missing {asset} texture ending in {suffix}")
    image = bpy.data.images.load(str(matches[0]), check_existing=True)
    return image


def _pbr_material(
    name: str,
    root: Path,
    asset: str,
    *,
    tint: tuple[float, float, float, float] | None = None,
    metallic_default: float = 0.0,
    roughness_default: float = 0.4,
    normal_strength: float = 0.22,
    texture_scale: float = 2.0,
    use_roughness_texture: bool = True,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Metallic"].default_value = metallic_default
    principled.inputs["Roughness"].default_value = roughness_default
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    coordinate = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (texture_scale,) * 3
    links.new(coordinate.outputs["Generated"], mapping.inputs["Vector"])

    if tint is None:
        color = nodes.new("ShaderNodeTexImage")
        color.image = _load_texture(root, asset, "_Color.jpg")
        links.new(mapping.outputs["Vector"], color.inputs["Vector"])
        links.new(color.outputs["Color"], principled.inputs["Base Color"])
    else:
        principled.inputs["Base Color"].default_value = tint

    if use_roughness_texture:
        roughness = nodes.new("ShaderNodeTexImage")
        roughness.image = _load_texture(root, asset, "_Roughness.jpg")
        roughness.image.colorspace_settings.name = "Non-Color"
        links.new(mapping.outputs["Vector"], roughness.inputs["Vector"])
        links.new(roughness.outputs["Color"], principled.inputs["Roughness"])

    metal_candidates = sorted((root / asset).glob("*_Metalness.jpg"))
    if metal_candidates and metallic_default >= 0.5:
        metal = nodes.new("ShaderNodeTexImage")
        metal.image = bpy.data.images.load(str(metal_candidates[0]), check_existing=True)
        metal.image.colorspace_settings.name = "Non-Color"
        links.new(mapping.outputs["Vector"], metal.inputs["Vector"])
        links.new(metal.outputs["Color"], principled.inputs["Metallic"])

    normal = nodes.new("ShaderNodeTexImage")
    normal.image = _load_texture(root, asset, "_NormalGL.jpg")
    normal.image.colorspace_settings.name = "Non-Color"
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.inputs["Strength"].default_value = normal_strength
    links.new(mapping.outputs["Vector"], normal.inputs["Vector"])
    links.new(normal.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])
    material["source_asset"] = f"ambientCG/{asset} 1K-JPG CC0"
    material["proof_material"] = True
    return material


def _replace_materials(material_root: Path, robot_root: bpy.types.Object) -> dict[str, str]:
    materials = {
        "brushed": _pbr_material(
            "SUM_PROOF_PBR_BrushedSteel",
            material_root,
            "Metal012",
            tint=(0.105, 0.125, 0.138, 1.0),
            metallic_default=1.0,
            roughness_default=0.29,
            normal_strength=0.035,
            use_roughness_texture=False,
        ),
        "clean": _pbr_material(
            "SUM_PROOF_PBR_CleanSteel",
            material_root,
            "Metal049A",
            tint=(0.16, 0.19, 0.205, 1.0),
            metallic_default=1.0,
            roughness_default=0.24,
            normal_strength=0.035,
            use_roughness_texture=False,
        ),
        "rubber": _pbr_material(
            "SUM_PROOF_PBR_Rubber",
            material_root,
            "Rubber002",
            tint=(0.018, 0.022, 0.024, 1.0),
            metallic_default=0.0,
            roughness_default=0.54,
            normal_strength=0.045,
            texture_scale=4.0,
            use_roughness_texture=False,
        ),
        "orange": _pbr_material(
            "SUM_PROOF_PBR_KukaOrange",
            material_root,
            "Metal049A",
            tint=(0.30, 0.050, 0.007, 1.0),
            metallic_default=0.06,
            roughness_default=0.46,
            normal_strength=0.025,
            use_roughness_texture=False,
        ),
        "graphite": _pbr_material(
            "SUM_PROOF_PBR_GraphitePowderCoat",
            material_root,
            "Metal049A",
            tint=(0.018, 0.025, 0.030, 1.0),
            metallic_default=0.22,
            roughness_default=0.48,
            use_roughness_texture=False,
        ),
        "black_oxide": _pbr_material(
            "SUM_PROOF_PBR_BlackOxideToolSteel",
            material_root,
            "Metal012",
            tint=(0.032, 0.042, 0.047, 1.0),
            metallic_default=0.88,
            roughness_default=0.37,
            normal_strength=0.035,
            use_roughness_texture=False,
        ),
        "panel_white": _pbr_material(
            "SUM_PROOF_PBR_WarmWhitePowderCoat",
            material_root,
            "Metal049A",
            tint=(0.30, 0.34, 0.36, 1.0),
            metallic_default=0.04,
            roughness_default=0.50,
            normal_strength=0.08,
            texture_scale=3.0,
            use_roughness_texture=False,
        ),
        "safety_yellow": _pbr_material(
            "SUM_PROOF_PBR_SafetyYellow",
            material_root,
            "Metal049A",
            tint=(0.86, 0.48, 0.018, 1.0),
            metallic_default=0.03,
            roughness_default=0.38,
            normal_strength=0.07,
            texture_scale=3.5,
            use_roughness_texture=False,
        ),
        "floor": _pbr_material(
            "SUM_PROOF_PBR_SealedConcrete",
            material_root,
            "Concrete034",
            tint=(0.13, 0.15, 0.16, 1.0),
            metallic_default=0.0,
            roughness_default=0.46,
            normal_strength=0.13,
            texture_scale=0.42,
        ),
    }

    targets = [robot_root, *robot_root.children_recursive]
    targets.extend(
        obj
        for obj in bpy.context.scene.objects
        if obj.name.startswith(("SUM_RobotCell_", "SUM_Factory_RobotCell_"))
        or obj.name in {
            "SUM_Factory_LightGray_FloorSlab",
            "SUM_MatureFactory_SealedEpoxyFloor",
        }
    )
    replaced = 0
    for obj in targets:
        if obj.type != "MESH":
            continue
        role = str(obj.get("lookdev_role", "")).lower()
        lower_name = obj.name.lower()
        if "floor" in lower_name:
            chosen = materials["floor"]
        elif "safetyyellow" in lower_name or "yellow" in role:
            chosen = materials["safety_yellow"]
        elif "rubber" in role or "belt" in lower_name:
            chosen = materials["rubber"]
        elif any(token in role for token in ("black_oxide", "tool_steel", "nitrided")):
            chosen = materials["black_oxide"]
        elif "bearingring" in lower_name or "workpiece" in role:
            chosen = materials["clean"]
        elif "robot" in role or "kuka" in lower_name:
            chosen = materials["orange"]
        elif any(token in lower_name for token in ("machineshell", "loadwall", "panel")):
            chosen = materials["panel_white"]
        elif any(token in role for token in ("brushed", "machined", "workpiece")):
            chosen = materials["brushed"]
        elif any(token in role for token in ("dark", "powder", "steel_blue")):
            chosen = materials["graphite"]
        else:
            continue
        for slot in obj.material_slots:
            slot.material = chosen
        if not obj.material_slots:
            obj.data.materials.append(chosen)
        replaced += 1
    return {"objects_replaced": replaced, "library": "ambientCG CC0 1K PBR"}


def _aim_object(
    obj: bpy.types.Object,
    target: Vector,
    world_up: Vector = Vector((0.0, 1.0, 0.0)),
) -> None:
    forward = (target - obj.location).normalized()
    right = forward.cross(world_up).normalized()
    corrected_up = right.cross(forward).normalized()
    rotation = Matrix((right, corrected_up, -forward)).transposed().to_quaternion()
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = rotation


def _add_proof_light(
    scene: bpy.types.Scene,
    name: str,
    location: tuple[float, float, float],
    target: tuple[float, float, float],
    energy: float,
    size: float,
    color: tuple[float, float, float],
) -> None:
    existing = bpy.data.objects.get(name)
    if existing is not None:
        bpy.data.objects.remove(existing, do_unlink=True)
    data = bpy.data.lights.new(name=f"{name}_Data", type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = location
    _aim_object(light, Vector(target))
    light["proof_light"] = True


def _parent_keep_world(obj: bpy.types.Object, parent: bpy.types.Object) -> None:
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def _add_cylinder_between(
    name: str,
    start: Vector,
    end: Vector,
    radius: float,
    parent: bpy.types.Object,
    role: str,
) -> bpy.types.Object:
    direction = end - start
    midpoint = (start + end) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=direction.length, location=midpoint)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new(name=f"{name}_EdgeBreak", type="BEVEL")
    bevel.width = min(radius * 0.18, 0.006)
    bevel.segments = 3
    obj["lookdev_role"] = role
    obj["proof_role"] = "three_jaw_internal_gripper"
    _parent_keep_world(obj, parent)
    return obj


def _add_oriented_box(
    name: str,
    center: Vector,
    radial: Vector,
    axis: Vector,
    dimensions: tuple[float, float, float],
    parent: bpy.types.Object,
    role: str,
) -> bpy.types.Object:
    tangent = axis.cross(radial).normalized()
    rotation = Matrix((radial, tangent, axis)).transposed().to_quaternion()
    bpy.ops.mesh.primitive_cube_add(location=center)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = rotation
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new(name=f"{name}_EdgeBreak", type="BEVEL")
    bevel.width = 0.006
    bevel.segments = 3
    obj["lookdev_role"] = role
    obj["proof_role"] = "three_jaw_internal_gripper"
    _parent_keep_world(obj, parent)
    return obj


def _build_internal_gripper(
    scene: bpy.types.Scene,
    tcp: bpy.types.Object,
    ring_relative_to_tcp: Matrix,
) -> list[bpy.types.Object]:
    scene.frame_set(1)
    bpy.context.view_layer.update()
    ring_world = tcp.matrix_world @ ring_relative_to_tcp
    ring_center = ring_world.translation.copy()
    ring_axis = (ring_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
    ring_x = (ring_world.to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
    ring_y = ring_axis.cross(ring_x).normalized()

    legacy_tokens = (
        "CrossRail",
        "ServoLeadScrew",
        "LeadScrewBearingBlock",
        "LinearGuide",
        "JawCarrier",
        "Finger_",
        "CompliantPad",
    )
    for obj in scene.objects:
        if obj.name.startswith("SUM_KUKA_Gripper_") and any(
            token in obj.name for token in legacy_tokens
        ):
            obj.hide_render = True
            obj.hide_viewport = True
            obj["proof_exclusion_reason"] = "replaced by collision-safe internal gripper"

    _add_cylinder_between(
        "SUM_PROOF_InternalGripper_Hub",
        ring_center + ring_axis * 0.105,
        ring_center + ring_axis * 0.225,
        0.064,
        tcp,
        "machined_steel",
    )
    _add_cylinder_between(
        "SUM_PROOF_InternalGripper_Stem",
        ring_center + ring_axis * 0.205,
        ring_center + ring_axis * 0.315,
        0.034,
        tcp,
        "dark_tool_steel",
    )

    jaw_roots: list[bpy.types.Object] = []
    jaw_phase = math.radians(30.0)
    for index, angle in enumerate(
        (jaw_phase, jaw_phase + math.tau / 3.0, jaw_phase + 2.0 * math.tau / 3.0),
        1,
    ):
        radial = (ring_x * math.cos(angle) + ring_y * math.sin(angle)).normalized()
        jaw_root = bpy.data.objects.new(f"SUM_PROOF_InternalGripper_JawRoot_{index:02d}", None)
        scene.collection.objects.link(jaw_root)
        jaw_root.parent = tcp
        jaw_root.matrix_parent_inverse = Matrix.Identity(4)
        jaw_root.matrix_local = Matrix.Identity(4)
        jaw_root["proof_role"] = "internal_gripper_radial_slide"

        _add_oriented_box(
            f"SUM_PROOF_InternalGripper_Slide_{index:02d}",
            ring_center + radial * 0.067 + ring_axis * 0.125,
            radial,
            ring_axis,
            (0.145, 0.042, 0.038),
            jaw_root,
            "machined_steel",
        )
        _add_cylinder_between(
            f"SUM_PROOF_InternalGripper_Pin_{index:02d}",
            ring_center + radial * 0.146 - ring_axis * 0.018,
            ring_center + radial * 0.146 + ring_axis * 0.115,
            0.012,
            jaw_root,
            "machined_steel",
        )

        radial_local = tcp.matrix_world.to_3x3().inverted() @ radial
        retracted = -radial_local * 0.052
        for frame, location in (
            (1, retracted),
            (GRASP_BEGIN_FRAME, retracted),
            (GRASP_FRAME, Vector((0.0, 0.0, 0.0))),
            (PLACE_FRAME, Vector((0.0, 0.0, 0.0))),
            (RELEASE_FRAME, retracted),
            (FRAME_END, retracted),
        ):
            jaw_root.location = location
            jaw_root.keyframe_insert("location", frame=frame)
        _set_key_interpolation(jaw_root)
        jaw_roots.append(jaw_root)
    return jaw_roots


def _build_outfeed(
    scene: bpy.types.Scene,
    place_matrix: Matrix,
    nest_top_y: float,
) -> Matrix:
    root = bpy.data.objects.new("SUM_RobotCell_HandoffOutfeedRoot", None)
    scene.collection.objects.link(root)
    exit_matrix = place_matrix.copy()
    exit_matrix.translation.x -= 3.80
    start = place_matrix.translation.copy()
    end = exit_matrix.translation.copy()
    radial = (end - start).normalized()
    center = (start + end) * 0.5
    axis = Vector((0.0, 1.0, 0.0))
    length = (end - start).length + 0.72
    _add_oriented_box(
        "SUM_RobotCell_HandoffOutfeedBelt",
        Vector((center.x, nest_top_y - 0.035, center.z)),
        radial,
        axis,
        (length, 0.62, 0.07),
        root,
        "belt",
    )
    _add_oriented_box(
        "SUM_RobotCell_HandoffOutfeedBed",
        Vector((center.x, nest_top_y - 0.135, center.z)),
        radial,
        axis,
        (length + 0.14, 0.76, 0.20),
        root,
        "dark_powder_coat",
    )
    return exit_matrix


def _build_infeed_extension(
    scene: bpy.types.Scene,
    pick_matrix: Matrix,
    belt_top_y: float,
) -> None:
    root = bpy.data.objects.new("SUM_RobotCell_InfeedExtensionRoot", None)
    scene.collection.objects.link(root)
    radial = Vector((0.0, 0.0, -1.0))
    axis = Vector((0.0, 1.0, 0.0))
    center = Vector((pick_matrix.translation.x, belt_top_y - 0.05, -12.08))
    _add_oriented_box(
        "SUM_RobotCell_InfeedExtensionBelt",
        center,
        radial,
        axis,
        (1.15, 1.02, 0.10),
        root,
        "belt",
    )
    _add_oriented_box(
        "SUM_RobotCell_InfeedExtensionBed",
        Vector((center.x, belt_top_y - 0.17, center.z)),
        radial,
        axis,
        (1.25, 1.18, 0.19),
        root,
        "dark_powder_coat",
    )
    for index, x in enumerate((center.x - 0.55, center.x + 0.55), 1):
        _add_oriented_box(
            f"SUM_RobotCell_InfeedExtensionRail_{index:02d}",
            Vector((x, belt_top_y + 0.12, center.z)),
            radial,
            axis,
            (1.20, 0.045, 0.28),
            root,
            "brushed_steel",
        )


def _configure_render(scene: bpy.types.Scene, args: argparse.Namespace) -> None:
    scene.frame_start = 1
    scene.frame_end = FRAME_END
    scene.render.fps = FPS
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.use_motion_blur = True
    scene.render.image_settings.color_depth = "8"

    camera = _fresh_scene_camera(scene, "SUM_PROOF_RobotCamera")
    camera.location = (2.75, 3.05, -5.20)
    _aim_object(camera, Vector((-3.58, 1.18, -9.86)))
    camera.data.lens = 46.0
    camera.data.sensor_width = 36.0
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = bpy.data.objects.get("SUM_ASSET_KUKA_KR210_L150")
    camera.data.dof.aperture_fstop = 7.1
    camera["proof_camera_fixed"] = True
    bpy.context.view_layer.update()

    scene.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue
    scene.view_settings.exposure = -0.45

    _add_proof_light(
        scene,
        "SUM_PROOF_Robot_Key",
        (-1.10, 5.80, -8.30),
        (-3.80, 1.30, -10.65),
        900.0,
        4.0,
        (1.0, 0.93, 0.82),
    )
    _add_proof_light(
        scene,
        "SUM_PROOF_Robot_Fill",
        (-1.80, 3.10, -13.70),
        (-3.80, 1.20, -10.80),
        460.0,
        3.2,
        (0.72, 0.86, 1.0),
    )
    _add_proof_light(
        scene,
        "SUM_PROOF_Robot_Rim",
        (-6.20, 4.30, -10.20),
        (-3.85, 1.45, -10.70),
        620.0,
        2.6,
        (1.0, 0.68, 0.35),
    )
    if scene.world and scene.world.use_nodes:
        background = scene.world.node_tree.nodes.get("Background")
        if background is not None:
            background.inputs["Strength"].default_value = 0.12

    if args.preview_output:
        args.preview_output.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(args.preview_output)


def _is_descendant(obj: bpy.types.Object, ancestor: bpy.types.Object) -> bool:
    cursor = obj.parent
    while cursor is not None:
        if cursor is ancestor:
            return True
        cursor = cursor.parent
    return False


def _world_y_bounds(obj: bpy.types.Object) -> tuple[float, float]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return min(point.y for point in points), max(point.y for point in points)


def _world_y_bounds_at_matrix(
    obj: bpy.types.Object, matrix: Matrix
) -> tuple[float, float]:
    points = [matrix @ Vector(corner) for corner in obj.bound_box]
    return min(point.y for point in points), max(point.y for point in points)


def _isolate_mechanism_proof(scene: bpy.types.Scene, robot_root: bpy.types.Object) -> None:
    allowed_prefixes = (
        "SUM_KUKA_",
        "SUM_RobotCell_Infeed",
        "SUM_RobotCell_Handoff",
        "SUM_RobotCell_DownstreamMachine",
        "SUM_RobotCell_Gantry",
        "SUM_PROOF_",
    )
    allowed_exact = {
        "SUM_Factory_LightGray_FloorSlab",
        "SUM_MatureFactory_SealedEpoxyFloor",
        "SUM_Factory_RobotCell_GuardFence_Frame",
        "SUM_Factory_RobotCell_GuardFence_Panels",
    }
    rejected_occluders = {
        "SUM_RobotCell_SafetyYellowPosts",
        "SUM_RobotCell_BlackGuardRails",
        "SUM_RobotCell_HandoffNest_Locator_01",
        "SUM_RobotCell_HandoffNest_Locator_02",
        "SUM_RobotCell_HandoffNest_Locator_03",
    }
    for obj in scene.objects:
        if obj.type not in {"MESH", "CURVE"}:
            continue
        keep = (
            obj.name in allowed_exact
            or obj.name.startswith(allowed_prefixes)
            or _is_descendant(obj, robot_root)
        )
        obj.hide_render = (not keep) or obj.name in rejected_occluders
        obj["proof_visibility"] = "kept" if not obj.hide_render else "cutaway_hidden"


def _build() -> tuple[dict[str, object], argparse.Namespace]:
    args = _args()
    args.scene_output = args.scene_output.resolve()
    args.report = args.report.resolve()
    if args.preview_output is not None:
        args.preview_output = args.preview_output.resolve()
    scene = bpy.context.scene
    _configure_render(scene, args)
    scene.frame_set(1)

    # The old destination sat deep inside a hidden machine shell. For this
    # mechanism gate, move the complete receiving nest beside the conveyor so
    # the fixed camera can read pickup and placement in one composition.
    handoff_root = _required("SUM_RobotCell_HandoffNest")
    _clear_animation(handoff_root)
    handoff_world = handoff_root.matrix_world.copy()
    handoff_world.translation.x -= 1.23
    handoff_world.translation.z += 3.65
    handoff_root.matrix_world = handoff_world
    bpy.context.view_layer.update()

    joints = [_required(name) for name in JOINT_NAMES]
    tcp = _required(TCP_NAME)
    robot_root = _required("SUM_ASSET_KUKA_KR210_L150")
    pick_reference = _required(PICK_RING_NAME)
    place_reference = _required(PLACE_RING_NAME)
    transfer_ring = _required(TRANSFER_RING_NAME)
    next_ring = _required(NEXT_RING_NAME)
    upstream_ring = _required(UPSTREAM_RING_NAME)
    previous_nest_ring = _required(NEST_RING_NAME)
    held_proxy = _required(HELD_PROXY_NAMES[0])

    _isolate_mechanism_proof(scene, robot_root)

    camera_matrix = scene.camera.matrix_world.copy()
    pick_matrix = _rigid_matrix(pick_reference.matrix_world)
    place_matrix = _rigid_matrix(place_reference.matrix_world)
    next_ring_start = _rigid_matrix(next_ring.matrix_world)
    upstream_ring_start = _rigid_matrix(upstream_ring.matrix_world)
    previous_nest_start = _rigid_matrix(previous_nest_ring.matrix_world)
    # The legacy proxy is used only to discover an equivalent reachable TCP
    # pose. Its inherited scale is never applied to the production workpiece.
    held_relative_to_tcp = tcp.matrix_world.inverted() @ held_proxy.matrix_world
    layout = _required("SUM_ASSET_LayoutTransform")
    factory_up = (layout.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
    source_payload_axis = (
        (tcp.matrix_world @ held_relative_to_tcp).to_3x3()
        @ Vector((0.0, 0.0, 1.0))
    ).normalized()
    if source_payload_axis.dot(factory_up) < 0.0:
        # The ring is symmetric, but the tool is not. Select the equivalent
        # ring orientation that keeps the gripper body above the support plane.
        held_relative_to_tcp = held_relative_to_tcp @ Matrix.Rotation(
            math.pi, 4, "X"
        )

    # Locate both flat rings on real support planes rather than trusting the
    # source proxy offsets, which left visible air gaps above the belt and nest.
    belt_surface = _required("SUM_RobotCell_InfeedBeltSurface")
    precision_nest = _required("SUM_RobotCell_HandoffPrecisionNest")
    # Measure the workpiece with the rigid production matrix. The source proxy
    # carried a non-unit scale, which otherwise lowered the placed ring into the
    # nest even though the solved TCP target itself was accurate.
    ring_min_y, ring_max_y = _world_y_bounds_at_matrix(transfer_ring, pick_matrix)
    ring_half_height = (ring_max_y - ring_min_y) * 0.5
    _, belt_top_y = _world_y_bounds(belt_surface)
    _, nest_top_y = _world_y_bounds(precision_nest)
    pick_matrix.translation.y = belt_top_y + ring_half_height
    place_matrix.translation.y = nest_top_y + ring_half_height
    # The evaluated armature can tilt the flat ring by a few hundredths of a
    # degree at the solved key. A 0.35 mm seating allowance keeps its lowest
    # edge above the support instead of visually cutting into the nest.
    place_matrix.translation.y += 0.00035
    previous_nest_start = place_matrix.copy()
    new_ring = upstream_ring.copy()
    new_ring.data = upstream_ring.data
    new_ring.name = NEW_RING_NAME
    scene.collection.objects.link(new_ring)
    new_ring.parent = None
    new_ring_start = upstream_ring_start.copy()
    new_ring_start.translation.z += (
        upstream_ring_start.translation.z - next_ring_start.translation.z
    )
    new_ring.matrix_world = new_ring_start
    _clear_animation(new_ring)
    _build_infeed_extension(scene, pick_matrix, belt_top_y)

    source_home_angles = np.array([float(joint.rotation_axis_angle[0]) for joint in joints])
    for joint in joints:
        _clear_animation(joint)

    for name in HELD_PROXY_NAMES:
        obj = _required(name)
        obj.hide_render = True
        obj.hide_viewport = True
        obj["proof_exclusion_reason"] = "replaced by one continuously animated workpiece"

    # Keep one physical transfer ring and preserve its world transform while
    # detaching it from the conveyor hierarchy for matrix animation.
    transfer_ring.parent = None
    transfer_ring.matrix_world = pick_matrix
    _clear_animation(transfer_ring)
    transfer_ring["proof_role"] = "single_continuous_pick_place_workpiece"
    next_ring.parent = None
    next_ring.matrix_world = next_ring_start
    _clear_animation(next_ring)
    upstream_ring.parent = None
    upstream_ring.matrix_world = upstream_ring_start
    _clear_animation(upstream_ring)
    previous_nest_ring.parent = None
    previous_nest_ring.matrix_world = previous_nest_start
    previous_nest_ring.data = transfer_ring.data
    _clear_animation(previous_nest_ring)

    approach_pick = pick_matrix.copy()
    approach_pick.translation += factory_up * 0.48
    lift_pick = pick_matrix.copy()
    lift_pick.translation += factory_up * 0.62
    transfer_high = Matrix.Translation(
        (pick_matrix.translation + place_matrix.translation) * 0.5 + factory_up * 0.78
    ) @ place_matrix.to_quaternion().to_matrix().to_4x4()
    standby = transfer_high.copy()
    standby.translation += factory_up * 0.28
    approach_place = place_matrix.copy()
    approach_place.translation += factory_up * 0.52
    retract_place = place_matrix.copy()
    retract_place.translation += factory_up * 0.66

    alignment_solver = RobotSolver(
        joints,
        tcp,
        held_relative_to_tcp,
        full_orientation=False,
    )
    alignment_angles, _ = alignment_solver.solve(
        pick_matrix, source_home_angles.copy(), "pick_alignment_probe"
    )
    alignment_solver.set_angles(alignment_angles)
    bpy.context.view_layer.update()
    held_relative_to_tcp = _rigid_matrix(
        tcp.matrix_world.inverted() @ pick_matrix
    )

    solver = RobotSolver(joints, tcp, held_relative_to_tcp)
    targets = (
        ("home", standby),
        ("approach_pick", approach_pick),
        ("pick", pick_matrix),
        ("lift", lift_pick),
        ("transfer", transfer_high),
        ("approach_place", approach_place),
        ("place", place_matrix),
        ("retract", retract_place),
    )
    solved: dict[str, np.ndarray] = {}
    solve_report: list[dict[str, float | int | str]] = []
    seed = source_home_angles.copy()
    for label, ring_target in targets:
        angles, report = solver.solve(ring_target, seed, label)
        solved[label] = angles.copy()
        solve_report.append(report)
        seed = angles

    pose_keys = (
        (1, "home"),
        (23, "approach_pick"),
        (GRASP_BEGIN_FRAME, "pick"),
        (GRASP_FRAME, "pick"),
        (61, "lift"),
        (79, "transfer"),
        (98, "approach_place"),
        (PLACE_FRAME, "place"),
        (RELEASE_FRAME, "place"),
        (INDEX_FRAME, "retract"),
        (HOME_RETURN_FRAME, "home"),
        (FRAME_END, "home"),
    )
    _key_joint_s_curve(joints, pose_keys, solved)

    # The workpiece is stationary on the conveyor, follows the solved TCP only
    # after the jaws close, and remains in the nest after release.
    for frame in range(1, FRAME_END + 1):
        scene.frame_set(frame)
        if frame < GRASP_FRAME:
            matrix = pick_matrix
        elif frame <= RELEASE_FRAME:
            matrix = tcp.matrix_world @ held_relative_to_tcp
        else:
            matrix = place_matrix
        _key_world_matrix(transfer_ring, frame, matrix)
    _linearize(transfer_ring)

    # Previous cycle exits the nest through the downstream machine opening.
    machine_target = _build_outfeed(scene, place_matrix, nest_top_y)
    for frame, matrix in (
        (1, previous_nest_start),
        (8, previous_nest_start),
        (20, machine_target),
        (FRAME_END, machine_target),
    ):
        _key_world_matrix(previous_nest_ring, frame, matrix)
    _set_key_interpolation(previous_nest_ring)

    # A physically separate upstream ring indexes into the pickup station only
    # after the robot has retracted. At the loop seam it occupies the same pose
    # as the prior cycle's pickup ring.
    for frame, matrix in (
        (1, next_ring_start),
        (INDEX_FRAME, next_ring_start),
        (HOME_RETURN_FRAME, pick_matrix),
        (FRAME_END, pick_matrix),
    ):
        _key_world_matrix(next_ring, frame, matrix)
    _set_key_interpolation(next_ring)
    for obj, start_matrix, end_matrix in (
        (upstream_ring, upstream_ring_start, next_ring_start),
        (new_ring, new_ring_start, upstream_ring_start),
    ):
        for frame, matrix in (
            (1, start_matrix),
            (INDEX_FRAME, start_matrix),
            (HOME_RETURN_FRAME, end_matrix),
            (FRAME_END, end_matrix),
        ):
            _key_world_matrix(obj, frame, matrix)
        _set_key_interpolation(obj)

    jaw_objects = _build_internal_gripper(scene, tcp, held_relative_to_tcp)

    material_root = (
        Path(__file__).resolve().parents[1]
        / "assets"
        / "local-library"
        / "ambientcg"
    )
    material_report = _replace_materials(material_root, robot_root)
    scene["proof_grasp_frame"] = GRASP_FRAME
    scene["proof_grasp_begin_frame"] = GRASP_BEGIN_FRAME
    scene["proof_place_frame"] = PLACE_FRAME
    scene["proof_release_frame"] = RELEASE_FRAME
    scene["proof_index_frame"] = INDEX_FRAME

    scene.frame_set(1)
    first_camera = scene.camera.matrix_world.copy()
    first_angles = [float(joint.rotation_axis_angle[0]) for joint in joints]
    first_pick = transfer_ring.matrix_world.copy()
    first_nest = previous_nest_ring.matrix_world.copy()
    first_conveyor = [
        _required("SUM_RobotCell_InfeedBearingRing_01").matrix_world.copy(),
        transfer_ring.matrix_world.copy(),
        next_ring.matrix_world.copy(),
        upstream_ring.matrix_world.copy(),
    ]
    scene.frame_set(FRAME_END)
    last_camera = scene.camera.matrix_world.copy()
    last_angles = [float(joint.rotation_axis_angle[0]) for joint in joints]
    last_pick = next_ring.matrix_world.copy()
    last_nest = transfer_ring.matrix_world.copy()
    last_conveyor = [
        _required("SUM_RobotCell_InfeedBearingRing_01").matrix_world.copy(),
        next_ring.matrix_world.copy(),
        upstream_ring.matrix_world.copy(),
        new_ring.matrix_world.copy(),
    ]

    report: dict[str, object] = {
        "status": "mechanical-proof-generated",
        "source_scene": bpy.data.filepath,
        "frames": FRAME_END,
        "fps": FPS,
        "camera_fixed": all(
            abs(a - b) < 1.0e-7
            for row_a, row_b in zip(first_camera, last_camera)
            for a, b in zip(row_a, row_b)
        ),
        "robot_home_closed": max(abs(a - b) for a, b in zip(first_angles, last_angles)),
        "visual_pick_state_closed_m": (first_pick.translation - last_pick.translation).length,
        "visual_nest_state_closed_m": (first_nest.translation - last_nest.translation).length,
        "visual_conveyor_state_closed_m": max(
            (first.translation - last.translation).length
            for first, last in zip(first_conveyor, last_conveyor)
        ),
        "workpiece_transfer": "single object follows conveyor, TCP, then destination",
        "visibility_swap_used": False,
        "gripper": "three-jaw internal expanding proof head",
        "grasp_duration_frames": GRASP_FRAME - GRASP_BEGIN_FRAME,
        "release_duration_frames": RELEASE_FRAME - PLACE_FRAME,
        "animated_gripper_jaws": [obj.name for obj in jaw_objects],
        "ik": solve_report,
        "material_pass": material_report,
        "camera_matrix": _matrix_payload(camera_matrix),
        "pick_matrix": _matrix_payload(pick_matrix),
        "place_matrix": _matrix_payload(place_matrix),
    }

    args.scene_output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.scene_output))
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.preview_output:
        scene.frame_set(max(1, min(args.preview_frame, FRAME_END)))
        scene.render.filepath = str(args.preview_output)
        bpy.ops.render.render(write_still=True)

    return report, args


if __name__ == "__main__":
    built_report, _ = _build()
    print("SUM_ROBOT_PROOF=" + json.dumps(built_report))
