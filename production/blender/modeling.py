"""Parametric hard-surface assets for the SUM industrial long-take scene.

All dimensions are meters. Geometry is authored in an intuitive local frame
(X lateral, +Y travel, Z up), then one managed layout transform converts it to
the film frame (X lateral, +Y up, -Z travel). The two guide rails remain the
only continuous longitudinal visual lines. This module intentionally does not
create lights, cameras, a world, final textures, or web assets.

Typical Blender usage::

    from production.blender.modeling import build_models
    assets = build_models()
    screen = assets["screen_display_01"]

The build is idempotent inside ``SUM_MODELS``. It removes and recreates only
that managed collection, leaving collaborator-owned scene data untouched.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import bpy
from mathutils import Quaternion, Vector


Vec3 = Tuple[float, float, float]
Rotation = Union[Vec3, Quaternion]


@dataclass(frozen=True)
class ModelParameters:
    """Top-level controls for the complete modeling pass."""

    collection_name: str = "SUM_MODELS"
    rail_start_y: float = -10.0
    rail_end_y: float = 145.0
    rail_gauge: float = 2.40
    rail_mount_spacing: float = 3.40
    entry_anchor_travel: float = 2.0
    handoff_anchor_travel: float = 11.5
    final_anchor_travel: float = 138.0
    robot_location: Vec3 = (-4.50, 10.50, 0.0)
    bearing_location: Vec3 = (-3.70, 8.00, 0.0)
    grinding_location: Vec3 = (5.60, 26.00, 0.0)
    screen_station_locations: Tuple[Vec3, Vec3, Vec3, Vec3] = (
        (-5.80, 52.0, 0.0),
        (5.80, 75.0, 0.0),
        (-5.80, 99.0, 0.0),
        (5.80, 121.0, 0.0),
    )
    bearing_outer_diameter: float = 0.360
    bearing_bore_diameter: float = 0.200
    bearing_width: float = 0.072
    bearing_ball_diameter: float = 0.032
    bearing_ball_count: int = 18
    screen_active_width: float = 2.40
    screen_active_height: float = 1.50


def _validate_parameters(params: ModelParameters) -> None:
    if params.rail_end_y <= params.rail_start_y:
        raise ValueError("rail_end_y must be greater than rail_start_y")
    if params.rail_gauge <= 0.80:
        raise ValueError("rail_gauge must leave credible clearance between rails")
    if params.rail_mount_spacing <= 1.50:
        raise ValueError("rail_mount_spacing must not recreate railway-like sleepers")
    if len(params.screen_station_locations) != 4:
        raise ValueError("exactly four screen station locations are required")
    if not (
        params.bearing_bore_diameter
        < params.bearing_outer_diameter
        and params.bearing_ball_diameter < params.bearing_width
    ):
        raise ValueError("bearing dimensions are inconsistent")
    if params.bearing_ball_count < 8:
        raise ValueError("bearing_ball_count is too low for this bearing scale")
    narrative_travel = (
        params.entry_anchor_travel,
        params.bearing_location[1],
        params.handoff_anchor_travel,
        params.grinding_location[1],
        *(location[1] for location in params.screen_station_locations),
        params.final_anchor_travel,
    )
    if not all(
        current < following
        for current, following in zip(narrative_travel, narrative_travel[1:])
    ):
        raise ValueError(
            "travel order must be entry -> bearing -> robot -> grinding -> screens -> final"
        )
    if abs(params.robot_location[1] - params.handoff_anchor_travel) > 2.0:
        raise ValueError("robot and handoff anchor must occupy the same production bay")


def _remove_collection_tree(collection: bpy.types.Collection) -> None:
    for child in list(collection.children):
        _remove_collection_tree(child)
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def _reset_root_collection(name: str) -> bpy.types.Collection:
    existing = bpy.data.collections.get(name)
    if existing is not None:
        _remove_collection_tree(existing)
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def _child_collection(
    parent: bpy.types.Collection, name: str
) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def _set_node_input(node: bpy.types.Node, names: Sequence[str], value: Any) -> None:
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def _placeholder_material(
    name: str,
    base_color: Tuple[float, float, float, float],
    *,
    metallic: float,
    roughness: float,
    alpha: float = 1.0,
    transmission: float = 0.0,
    emission_color: Optional[Tuple[float, float, float, float]] = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = base_color
    material["sum_placeholder_material"] = True
    material["intended_workflow"] = "Replace or refine in lookdev; preserve slot name"

    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        _set_node_input(principled, ("Base Color",), base_color)
        _set_node_input(principled, ("Metallic",), metallic)
        _set_node_input(principled, ("Roughness",), roughness)
        _set_node_input(principled, ("Alpha",), alpha)
        _set_node_input(
            principled, ("Transmission Weight", "Transmission"), transmission
        )
        if emission_color is not None:
            _set_node_input(
                principled, ("Emission Color", "Emission"), emission_color
            )
            _set_node_input(
                principled, ("Emission Strength",), emission_strength
            )

    if alpha < 1.0:
        try:
            material.blend_method = "BLEND"
            material.show_transparent_back = True
        except (AttributeError, TypeError):
            pass
    return material


def _build_placeholder_materials() -> Dict[str, bpy.types.Material]:
    return {
        "robot_paint": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Robot_PowderCoat_Ochre",
            (0.48, 0.22, 0.035, 1.0),
            metallic=0.30,
            roughness=0.31,
        ),
        "paint_graphite": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Graphite_PowderCoat",
            (0.035, 0.045, 0.052, 1.0),
            metallic=0.42,
            roughness=0.30,
        ),
        "enclosure_paint": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Enclosure_WarmGray_PowderCoat",
            (0.33, 0.35, 0.35, 1.0),
            metallic=0.24,
            roughness=0.36,
        ),
        "machined_steel": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Steel_Machined",
            (0.34, 0.38, 0.40, 1.0),
            metallic=0.94,
            roughness=0.16,
        ),
        "brushed_steel": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Steel_Brushed",
            (0.23, 0.27, 0.29, 1.0),
            metallic=0.88,
            roughness=0.26,
        ),
        "black_oxide": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Steel_BlackOxide",
            (0.018, 0.022, 0.024, 1.0),
            metallic=0.78,
            roughness=0.24,
        ),
        "rubber": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Rubber_CableAndPads",
            (0.012, 0.014, 0.015, 1.0),
            metallic=0.0,
            roughness=0.63,
        ),
        "bearing_cage": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Bearing_Cage_Bronze",
            (0.40, 0.25, 0.075, 1.0),
            metallic=0.80,
            roughness=0.23,
        ),
        "grinding_wheel": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_CBN_GrindingWheel",
            (0.10, 0.12, 0.15, 1.0),
            metallic=0.18,
            roughness=0.68,
        ),
        "safety_glass": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_SafetyGlass_Smoked",
            (0.055, 0.095, 0.105, 0.28),
            metallic=0.0,
            roughness=0.12,
            alpha=0.28,
            transmission=0.72,
        ),
        "coolant": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_GrindingCoolant_Stream",
            (0.64, 0.72, 0.66, 0.76),
            metallic=0.0,
            roughness=0.18,
            alpha=0.76,
            transmission=0.12,
        ),
        "coolant_mist": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_GrindingCoolant_Mist",
            (0.72, 0.78, 0.74, 0.34),
            metallic=0.0,
            roughness=0.24,
            alpha=0.34,
            transmission=0.08,
        ),
        "rail_steel": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Rail_Steel",
            (0.16, 0.19, 0.21, 1.0),
            metallic=0.95,
            roughness=0.19,
        ),
        "screen_frame": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Screen_AnodizedFrame",
            (0.025, 0.031, 0.036, 1.0),
            metallic=0.74,
            roughness=0.22,
        ),
        "screen_content": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Screen_Content_ReplaceWithProjectImage",
            (0.012, 0.021, 0.027, 1.0),
            metallic=0.0,
            roughness=0.20,
            emission_color=(0.018, 0.060, 0.072, 1.0),
            emission_strength=0.22,
        ),
        "safety_amber": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Safety_Amber",
            (0.95, 0.47, 0.025, 1.0),
            metallic=0.20,
            roughness=0.28,
            emission_color=(0.95, 0.22, 0.015, 1.0),
            emission_strength=0.12,
        ),
        "safety_yellow": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_SafetyYellow_PowderCoat",
            (0.92, 0.58, 0.025, 1.0),
            metallic=0.06,
            roughness=0.36,
        ),
        "indicator_green": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Indicator_Green",
            (0.025, 0.52, 0.22, 1.0),
            metallic=0.05,
            roughness=0.24,
            emission_color=(0.015, 0.70, 0.23, 1.0),
            emission_strength=1.4,
        ),
        "indicator_red": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Indicator_Red",
            (0.65, 0.025, 0.012, 1.0),
            metallic=0.05,
            roughness=0.26,
            emission_color=(0.85, 0.012, 0.005, 1.0),
            emission_strength=0.65,
        ),
        "factory_floor": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_FactoryFloor_LightGray",
            (0.50, 0.53, 0.54, 1.0),
            metallic=0.04,
            roughness=0.40,
        ),
        "factory_wall": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_FactoryWall_WhitePanel",
            (0.72, 0.74, 0.74, 1.0),
            metallic=0.12,
            roughness=0.31,
        ),
        "factory_structure": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_FactoryStructure_GalvanizedSteel",
            (0.24, 0.28, 0.30, 1.0),
            metallic=0.78,
            roughness=0.27,
        ),
        "luminaire_diffuser": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_Luminaire_NeutralWhiteDiffuser",
            (0.82, 0.84, 0.82, 1.0),
            metallic=0.0,
            roughness=0.24,
            emission_color=(0.86, 0.91, 0.92, 1.0),
            emission_strength=0.55,
        ),
        "fixture": _placeholder_material(
            "SUM_MAT_PLACEHOLDER_InspectionFixture_Composite",
            (0.075, 0.082, 0.085, 1.0),
            metallic=0.05,
            roughness=0.42,
        ),
    }


def _assign_material(
    obj: bpy.types.Object, material: Optional[bpy.types.Material]
) -> None:
    if material is None or not hasattr(obj.data, "materials"):
        return
    obj.data.materials.clear()
    obj.data.materials.append(material)


def _hard_surface(
    obj: bpy.types.Object,
    bevel: float,
    *,
    segments: int = 3,
    smooth: bool = True,
) -> bpy.types.Object:
    if obj.type != "MESH":
        return obj
    for polygon in obj.data.polygons:
        polygon.use_smooth = smooth
    if bevel > 0.0:
        modifier = obj.modifiers.new("SUM_Bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = segments
        modifier.limit_method = "ANGLE"
        modifier.angle_limit = math.radians(28.0)
        modifier.use_clamp_overlap = True
        if hasattr(modifier, "harden_normals"):
            modifier.harden_normals = True
    try:
        normal = obj.modifiers.new("SUM_WeightedNormals", "WEIGHTED_NORMAL")
        normal.keep_sharp = True
        normal.weight = 50
    except RuntimeError:
        pass
    return obj


def _mark_part(
    obj: bpy.types.Object,
    role: str,
    dimensions_m: Optional[Sequence[float]] = None,
) -> bpy.types.Object:
    obj["sum_part_role"] = role
    if dimensions_m is not None:
        obj["dimensions_m"] = " x ".join(f"{value:.3f}" for value in dimensions_m)
    return obj


def _apply_local_transform(
    obj: bpy.types.Object,
    *,
    location: Vec3,
    rotation: Rotation,
    parent: Optional[bpy.types.Object],
) -> None:
    if parent is not None:
        obj.parent = parent
    obj.location = location
    if isinstance(rotation, Quaternion):
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = rotation
    else:
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = rotation


def _mesh_object(
    name: str,
    vertices: Sequence[Vec3],
    faces: Sequence[Sequence[int]],
    collection: bpy.types.Collection,
    *,
    location: Vec3 = (0.0, 0.0, 0.0),
    rotation: Rotation = (0.0, 0.0, 0.0),
    parent: Optional[bpy.types.Object] = None,
    material: Optional[bpy.types.Material] = None,
    bevel: float = 0.0,
    smooth: bool = True,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    _apply_local_transform(obj, location=location, rotation=rotation, parent=parent)
    _assign_material(obj, material)
    _hard_surface(obj, bevel, smooth=smooth)
    return obj


def _empty(
    name: str,
    collection: bpy.types.Collection,
    *,
    location: Vec3 = (0.0, 0.0, 0.0),
    rotation: Rotation = (0.0, 0.0, 0.0),
    parent: Optional[bpy.types.Object] = None,
    display_size: float = 0.25,
) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    _apply_local_transform(obj, location=location, rotation=rotation, parent=parent)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = display_size
    return obj


def _box_geometry(dimensions: Vec3) -> Tuple[List[Vec3], List[Tuple[int, ...]]]:
    dx, dy, dz = (value * 0.5 for value in dimensions)
    vertices: List[Vec3] = [
        (-dx, -dy, -dz),
        (dx, -dy, -dz),
        (dx, dy, -dz),
        (-dx, dy, -dz),
        (-dx, -dy, dz),
        (dx, -dy, dz),
        (dx, dy, dz),
        (-dx, dy, dz),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    return vertices, faces


def _box(
    name: str,
    dimensions: Vec3,
    collection: bpy.types.Collection,
    *,
    location: Vec3 = (0.0, 0.0, 0.0),
    rotation: Rotation = (0.0, 0.0, 0.0),
    parent: Optional[bpy.types.Object] = None,
    material: Optional[bpy.types.Material] = None,
    bevel: float = 0.01,
    role: str = "hard_surface_panel",
) -> bpy.types.Object:
    vertices, faces = _box_geometry(dimensions)
    obj = _mesh_object(
        name,
        vertices,
        faces,
        collection,
        location=location,
        rotation=rotation,
        parent=parent,
        material=material,
        bevel=min(bevel, min(dimensions) * 0.22),
        smooth=True,
    )
    return _mark_part(obj, role, dimensions)


def _box_array(
    name: str,
    boxes: Sequence[Tuple[Vec3, Vec3]],
    collection: bpy.types.Collection,
    *,
    parent: Optional[bpy.types.Object],
    material: bpy.types.Material,
    bevel: float,
    role: str,
) -> bpy.types.Object:
    vertices: List[Vec3] = []
    faces: List[Tuple[int, ...]] = []
    for center, dimensions in boxes:
        local_vertices, local_faces = _box_geometry(dimensions)
        offset = len(vertices)
        vertices.extend(
            (x + center[0], y + center[1], z + center[2])
            for x, y, z in local_vertices
        )
        faces.extend(tuple(index + offset for index in face) for face in local_faces)
    obj = _mesh_object(
        name,
        vertices,
        faces,
        collection,
        parent=parent,
        material=material,
        bevel=bevel,
        smooth=True,
    )
    return _mark_part(obj, role)


def _cylinder_geometry(
    radius: float,
    depth: float,
    segments: int,
    radius_top: Optional[float] = None,
) -> Tuple[List[Vec3], List[Tuple[int, ...]]]:
    radius_top = radius if radius_top is None else radius_top
    half = depth * 0.5
    vertices: List[Vec3] = []
    for z, loop_radius in ((-half, radius), (half, radius_top)):
        for index in range(segments):
            angle = math.tau * index / segments
            vertices.append((math.cos(angle) * loop_radius, math.sin(angle) * loop_radius, z))
    faces: List[Tuple[int, ...]] = [
        tuple(reversed(range(segments))),
        tuple(range(segments, segments * 2)),
    ]
    for index in range(segments):
        next_index = (index + 1) % segments
        faces.append(
            (index, next_index, next_index + segments, index + segments)
        )
    return vertices, faces


def _cylinder(
    name: str,
    radius: float,
    depth: float,
    collection: bpy.types.Collection,
    *,
    location: Vec3 = (0.0, 0.0, 0.0),
    rotation: Rotation = (0.0, 0.0, 0.0),
    parent: Optional[bpy.types.Object] = None,
    material: Optional[bpy.types.Material] = None,
    segments: int = 32,
    radius_top: Optional[float] = None,
    bevel: float = 0.005,
    role: str = "cylindrical_housing",
) -> bpy.types.Object:
    vertices, faces = _cylinder_geometry(radius, depth, segments, radius_top)
    obj = _mesh_object(
        name,
        vertices,
        faces,
        collection,
        location=location,
        rotation=rotation,
        parent=parent,
        material=material,
        bevel=min(bevel, radius * 0.16, depth * 0.12),
        smooth=True,
    )
    return _mark_part(obj, role, (radius * 2.0, radius * 2.0, depth))


def _align_z_to(direction: Union[Vec3, Vector]) -> Quaternion:
    vector = Vector(direction)
    if vector.length < 1.0e-8:
        raise ValueError("cannot align to a zero-length direction")
    return vector.normalized().to_track_quat("Z", "Y")


def _cylinder_between(
    name: str,
    start: Union[Vec3, Vector],
    end: Union[Vec3, Vector],
    radius: float,
    collection: bpy.types.Collection,
    *,
    parent: Optional[bpy.types.Object],
    material: bpy.types.Material,
    segments: int = 32,
    bevel: float = 0.005,
    role: str = "cylindrical_housing",
) -> bpy.types.Object:
    start_vector = Vector(start)
    end_vector = Vector(end)
    direction = end_vector - start_vector
    return _cylinder(
        name,
        radius,
        direction.length,
        collection,
        location=tuple((start_vector + end_vector) * 0.5),
        rotation=_align_z_to(direction),
        parent=parent,
        material=material,
        segments=segments,
        bevel=bevel,
        role=role,
    )


def _sphere_geometry(
    radius: float, segments: int, rings: int
) -> Tuple[List[Vec3], List[Tuple[int, ...]]]:
    vertices: List[Vec3] = [(0.0, 0.0, radius)]
    for ring in range(1, rings):
        phi = math.pi * ring / rings
        z = radius * math.cos(phi)
        ring_radius = radius * math.sin(phi)
        for segment in range(segments):
            theta = math.tau * segment / segments
            vertices.append(
                (ring_radius * math.cos(theta), ring_radius * math.sin(theta), z)
            )
    bottom_index = len(vertices)
    vertices.append((0.0, 0.0, -radius))

    faces: List[Tuple[int, ...]] = []
    first_ring = 1
    for segment in range(segments):
        next_segment = (segment + 1) % segments
        faces.append((0, first_ring + segment, first_ring + next_segment))
    for ring in range(rings - 2):
        ring_start = 1 + ring * segments
        next_ring_start = ring_start + segments
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append(
                (
                    ring_start + segment,
                    next_ring_start + segment,
                    next_ring_start + next_segment,
                    ring_start + next_segment,
                )
            )
    last_ring = 1 + (rings - 2) * segments
    for segment in range(segments):
        next_segment = (segment + 1) % segments
        faces.append((last_ring + next_segment, last_ring + segment, bottom_index))
    return vertices, faces


def _sphere(
    name: str,
    radius: float,
    collection: bpy.types.Collection,
    *,
    location: Vec3,
    parent: Optional[bpy.types.Object],
    material: bpy.types.Material,
    segments: int = 24,
    rings: int = 12,
    role: str = "precision_sphere",
) -> bpy.types.Object:
    vertices, faces = _sphere_geometry(radius, segments, rings)
    obj = _mesh_object(
        name,
        vertices,
        faces,
        collection,
        location=location,
        parent=parent,
        material=material,
        smooth=True,
    )
    return _mark_part(obj, role, (radius * 2.0,) * 3)


def _torus_geometry(
    major_radius: float,
    minor_radius: float,
    major_segments: int,
    minor_segments: int,
) -> Tuple[List[Vec3], List[Tuple[int, ...]]]:
    vertices: List[Vec3] = []
    faces: List[Tuple[int, ...]] = []
    for major_index in range(major_segments):
        major_angle = math.tau * major_index / major_segments
        for minor_index in range(minor_segments):
            minor_angle = math.tau * minor_index / minor_segments
            radial = major_radius + minor_radius * math.cos(minor_angle)
            vertices.append(
                (
                    radial * math.cos(major_angle),
                    radial * math.sin(major_angle),
                    minor_radius * math.sin(minor_angle),
                )
            )
    for major_index in range(major_segments):
        next_major = (major_index + 1) % major_segments
        for minor_index in range(minor_segments):
            next_minor = (minor_index + 1) % minor_segments
            a = major_index * minor_segments + minor_index
            b = next_major * minor_segments + minor_index
            c = next_major * minor_segments + next_minor
            d = major_index * minor_segments + next_minor
            faces.append((a, b, c, d))
    return vertices, faces


def _torus(
    name: str,
    major_radius: float,
    minor_radius: float,
    collection: bpy.types.Collection,
    *,
    location: Vec3 = (0.0, 0.0, 0.0),
    rotation: Rotation = (0.0, 0.0, 0.0),
    parent: Optional[bpy.types.Object],
    material: bpy.types.Material,
    major_segments: int = 64,
    minor_segments: int = 12,
    role: str = "machined_ring_detail",
) -> bpy.types.Object:
    vertices, faces = _torus_geometry(
        major_radius, minor_radius, major_segments, minor_segments
    )
    obj = _mesh_object(
        name,
        vertices,
        faces,
        collection,
        location=location,
        rotation=rotation,
        parent=parent,
        material=material,
        smooth=True,
    )
    return _mark_part(
        obj,
        role,
        (
            (major_radius + minor_radius) * 2.0,
            (major_radius + minor_radius) * 2.0,
            minor_radius * 2.0,
        ),
    )


def _annular_prism(
    name: str,
    outer_radius: float,
    inner_radius: float,
    depth: float,
    collection: bpy.types.Collection,
    *,
    location: Vec3 = (0.0, 0.0, 0.0),
    rotation: Rotation = (0.0, 0.0, 0.0),
    parent: Optional[bpy.types.Object],
    material: bpy.types.Material,
    segments: int = 96,
    bevel: float = 0.002,
    role: str = "precision_annular_component",
) -> bpy.types.Object:
    if inner_radius <= 0.0 or outer_radius <= inner_radius:
        raise ValueError("annular prism radii are invalid")
    vertices: List[Vec3] = []
    half = depth * 0.5
    for z in (-half, half):
        for radius in (outer_radius, inner_radius):
            for segment in range(segments):
                angle = math.tau * segment / segments
                vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, z))

    outer_bottom = 0
    inner_bottom = segments
    outer_top = segments * 2
    inner_top = segments * 3
    faces: List[Tuple[int, ...]] = []
    for segment in range(segments):
        next_segment = (segment + 1) % segments
        faces.extend(
            (
                (
                    outer_bottom + segment,
                    outer_bottom + next_segment,
                    outer_top + next_segment,
                    outer_top + segment,
                ),
                (
                    inner_bottom + next_segment,
                    inner_bottom + segment,
                    inner_top + segment,
                    inner_top + next_segment,
                ),
                (
                    outer_top + segment,
                    outer_top + next_segment,
                    inner_top + next_segment,
                    inner_top + segment,
                ),
                (
                    outer_bottom + next_segment,
                    outer_bottom + segment,
                    inner_bottom + segment,
                    inner_bottom + next_segment,
                ),
            )
        )
    obj = _mesh_object(
        name,
        vertices,
        faces,
        collection,
        location=location,
        rotation=rotation,
        parent=parent,
        material=material,
        bevel=bevel,
        smooth=True,
    )
    return _mark_part(
        obj, role, (outer_radius * 2.0, outer_radius * 2.0, depth)
    )


def _tapered_link(
    name: str,
    start: Union[Vec3, Vector],
    end: Union[Vec3, Vector],
    start_width: float,
    end_width: float,
    start_depth: float,
    end_depth: float,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    bevel: float,
    role: str,
) -> bpy.types.Object:
    start_vector = Vector(start)
    end_vector = Vector(end)
    direction = end_vector - start_vector
    length = direction.length
    z0 = -length * 0.5
    z1 = length * 0.5
    vertices: List[Vec3] = [
        (-start_width * 0.5, -start_depth * 0.5, z0),
        (start_width * 0.5, -start_depth * 0.5, z0),
        (start_width * 0.5, start_depth * 0.5, z0),
        (-start_width * 0.5, start_depth * 0.5, z0),
        (-end_width * 0.5, -end_depth * 0.5, z1),
        (end_width * 0.5, -end_depth * 0.5, z1),
        (end_width * 0.5, end_depth * 0.5, z1),
        (-end_width * 0.5, end_depth * 0.5, z1),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    obj = _mesh_object(
        name,
        vertices,
        faces,
        collection,
        location=tuple((start_vector + end_vector) * 0.5),
        rotation=_align_z_to(direction),
        parent=parent,
        material=material,
        bevel=bevel,
        smooth=True,
    )
    return _mark_part(
        obj,
        role,
        (max(start_width, end_width), max(start_depth, end_depth), length),
    )


def _bezier_tube(
    name: str,
    points: Sequence[Vec3],
    radius: float,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    role: str,
    resolution: int = 12,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_Curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    curve.resolution_u = resolution
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.parent = parent
    _assign_material(obj, material)
    return _mark_part(obj, role, (radius * 2.0,))


def _text_label(
    name: str,
    text: str,
    size: float,
    collection: bpy.types.Collection,
    *,
    location: Vec3,
    rotation: Rotation,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    role: str,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_Curve", type="FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = size * 0.035
    curve.bevel_depth = size * 0.007
    curve.bevel_resolution = 2
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    _apply_local_transform(
        obj,
        location=location,
        rotation=rotation,
        parent=parent,
    )
    _assign_material(obj, material)
    return _mark_part(obj, role, (size,))


def _prism_array(
    name: str,
    centers: Sequence[Vec3],
    radius: float,
    depth: float,
    segments: int,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    bevel: float,
    role: str,
) -> bpy.types.Object:
    vertices: List[Vec3] = []
    faces: List[Tuple[int, ...]] = []
    base_vertices, base_faces = _cylinder_geometry(radius, depth, segments)
    for center in centers:
        offset = len(vertices)
        vertices.extend(
            (x + center[0], y + center[1], z + center[2])
            for x, y, z in base_vertices
        )
        faces.extend(tuple(index + offset for index in face) for face in base_faces)
    obj = _mesh_object(
        name,
        vertices,
        faces,
        collection,
        parent=parent,
        material=material,
        bevel=bevel,
        smooth=True,
    )
    return _mark_part(obj, role)


def _display_surface(
    name: str,
    width: float,
    height: float,
    collection: bpy.types.Collection,
    *,
    location: Vec3,
    parent: bpy.types.Object,
    material: bpy.types.Material,
) -> bpy.types.Object:
    vertices: List[Vec3] = [
        (0.0, -width * 0.5, -height * 0.5),
        (0.0, width * 0.5, -height * 0.5),
        (0.0, width * 0.5, height * 0.5),
        (0.0, -width * 0.5, height * 0.5),
    ]
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="ProjectImageUV")
    for loop, uv in zip(
        mesh.polygons[0].loop_indices,
        ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
    ):
        uv_layer.data[loop].uv = uv
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    _apply_local_transform(
        obj, location=location, rotation=(0.0, 0.0, 0.0), parent=parent
    )
    _assign_material(obj, material)
    obj["sum_part_role"] = "replaceable_project_image_surface"
    obj["active_area_m"] = f"{width:.3f} x {height:.3f}"
    obj["aspect_ratio"] = width / height
    obj["uv_map"] = uv_layer.name
    return obj


def _joint_empty(
    name: str,
    location: Vec3,
    axis: Union[Vec3, Vector],
    collection: bpy.types.Collection,
    parent: bpy.types.Object,
    index: int,
) -> bpy.types.Object:
    joint = _empty(
        name,
        collection,
        location=location,
        parent=parent,
        display_size=0.18,
    )
    axis_vector = Vector(axis).normalized()
    joint.rotation_mode = "AXIS_ANGLE"
    joint.rotation_axis_angle = (
        0.0,
        axis_vector.x,
        axis_vector.y,
        axis_vector.z,
    )
    joint["joint_index"] = index
    joint["joint_axis_local"] = [axis_vector.x, axis_vector.y, axis_vector.z]
    joint["animation_channel"] = "rotation_axis_angle[0]"
    joint["sum_part_role"] = "robot_kinematic_axis"
    return joint


def _add_bolt_circle(
    prefix: str,
    center: Union[Vec3, Vector],
    axis: Union[Vec3, Vector],
    circle_radius: float,
    bolt_radius: float,
    bolt_depth: float,
    count: int,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
) -> List[bpy.types.Object]:
    axis_vector = Vector(axis).normalized()
    reference = Vector((0.0, 0.0, 1.0))
    if abs(axis_vector.dot(reference)) > 0.95:
        reference = Vector((0.0, 1.0, 0.0))
    u = axis_vector.cross(reference).normalized()
    v = axis_vector.cross(u).normalized()
    center_vector = Vector(center)
    bolts: List[bpy.types.Object] = []
    for index in range(count):
        angle = math.tau * index / count
        position = center_vector + circle_radius * (
            math.cos(angle) * u + math.sin(angle) * v
        )
        half_axis = axis_vector * (bolt_depth * 0.5)
        bolts.append(
            _cylinder_between(
                f"{prefix}_Bolt_{index + 1:02d}",
                position - half_axis,
                position + half_axis,
                bolt_radius,
                collection,
                parent=parent,
                material=material,
                segments=6,
                bevel=bolt_radius * 0.12,
                role="serviceable_hex_fastener",
            )
        )
    return bolts


def _build_robot(
    params: ModelParameters,
    collection: bpy.types.Collection,
    materials: Dict[str, bpy.types.Material],
) -> Tuple[bpy.types.Object, List[bpy.types.Object], bpy.types.Object]:
    root = _empty(
        "SUM_ASSET_Robot_6Axis",
        collection,
        location=params.robot_location,
        display_size=0.45,
    )
    root["sum_asset_type"] = "six_axis_industrial_robot"
    root["axis_count"] = 6
    root["nominal_reach_m"] = 2.65
    root["nominal_payload_class_kg"] = "35-60"
    root["travel_position_m"] = params.robot_location[1]
    root["modeling_intent"] = "credible medium-payload grinding-cell handling robot"

    _box(
        "SUM_Robot_BasePlate",
        (1.08, 0.98, 0.16),
        collection,
        location=(0.0, 0.0, 0.08),
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.025,
        role="floor_anchored_robot_base_plate",
    )
    anchor_centers = [
        (x, y, 0.18)
        for x in (-0.43, 0.43)
        for y in (-0.38, 0.38)
    ]
    _prism_array(
        "SUM_Robot_Base_AnchorBolts",
        anchor_centers,
        0.035,
        0.045,
        6,
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.003,
        role="robot_floor_anchor_bolts",
    )
    _cylinder(
        "SUM_Robot_Base_Pedestal",
        0.46,
        0.34,
        collection,
        location=(0.0, 0.0, 0.31),
        parent=root,
        material=materials["paint_graphite"],
        radius_top=0.39,
        bevel=0.018,
        role="tapered_robot_pedestal",
    )

    points = [
        Vector((0.0, 0.0, 0.52)),
        Vector((0.0, 0.0, 1.22)),
        Vector((0.48, 0.0, 2.40)),
        Vector((1.34, 0.0, 2.96)),
        Vector((2.02, 0.0, 2.68)),
        Vector((2.37, 0.0, 2.43)),
        Vector((2.67, 0.0, 2.30)),
    ]
    deltas = [points[index + 1] - points[index] for index in range(6)]
    joint_axes = [
        Vector((0.0, 0.0, 1.0)),
        Vector((0.0, 1.0, 0.0)),
        Vector((0.0, 1.0, 0.0)),
        deltas[2].normalized(),
        Vector((0.0, 1.0, 0.0)),
        deltas[4].normalized(),
    ]
    joints: List[bpy.types.Object] = []
    parent = root
    local_location = tuple(points[0])
    for index in range(6):
        joint = _joint_empty(
            f"SUM_Robot_J{index + 1}_Axis",
            local_location,
            joint_axes[index],
            collection,
            parent,
            index + 1,
        )
        joints.append(joint)
        parent = joint
        local_location = tuple(deltas[index]) if index < 5 else (0.0, 0.0, 0.0)

    j1, j2, j3, j4, j5, j6 = joints

    _cylinder(
        "SUM_Robot_J1_RotaryHousing",
        0.38,
        0.31,
        collection,
        parent=j1,
        material=materials["robot_paint"],
        bevel=0.015,
        role="joint_1_rotary_housing",
    )
    _torus(
        "SUM_Robot_J1_BearingCollar",
        0.345,
        0.018,
        collection,
        location=(0.0, 0.0, 0.10),
        parent=j1,
        material=materials["machined_steel"],
        role="joint_1_bearing_retainer",
    )
    _tapered_link(
        "SUM_Robot_WaistCasting",
        (0.0, 0.0, 0.08),
        tuple(deltas[0] - Vector((0.0, 0.0, 0.08))),
        0.58,
        0.50,
        0.50,
        0.42,
        collection,
        parent=j1,
        material=materials["robot_paint"],
        bevel=0.035,
        role="load_bearing_waist_casting",
    )
    _cylinder_between(
        "SUM_Robot_J2_ShoulderHousing",
        deltas[0] + Vector((0.0, -0.32, 0.0)),
        deltas[0] + Vector((0.0, 0.32, 0.0)),
        0.34,
        collection,
        parent=j1,
        material=materials["robot_paint"],
        bevel=0.014,
        role="joint_2_shoulder_housing",
    )
    _torus(
        "SUM_Robot_J2_ServiceCollar",
        0.275,
        0.018,
        collection,
        location=tuple(deltas[0] + Vector((0.0, -0.335, 0.0))),
        rotation=(math.pi * 0.5, 0.0, 0.0),
        parent=j1,
        material=materials["machined_steel"],
        role="joint_2_service_retainer",
    )
    _add_bolt_circle(
        "SUM_Robot_J2",
        deltas[0] + Vector((0.0, -0.355, 0.0)),
        (0.0, 1.0, 0.0),
        0.245,
        0.018,
        0.025,
        8,
        collection,
        parent=j1,
        material=materials["black_oxide"],
    )
    _box(
        "SUM_Robot_J2_ServoHousing",
        (0.42, 0.30, 0.46),
        collection,
        location=tuple(deltas[0] + Vector((0.0, 0.44, 0.02))),
        parent=j1,
        material=materials["paint_graphite"],
        bevel=0.035,
        role="joint_2_servo_and_gearbox_housing",
    )
    cooling_fins = [
        (
            tuple(deltas[0] + Vector((0.0, 0.605, z))),
            (0.34, 0.025, 0.028),
        )
        for z in (-0.13, -0.065, 0.0, 0.065, 0.13)
    ]
    _box_array(
        "SUM_Robot_J2_ServoCoolingFins",
        cooling_fins,
        collection,
        parent=j1,
        material=materials["black_oxide"],
        bevel=0.004,
        role="servo_housing_cooling_fins",
    )

    for side, y_offset in (("Front", -0.18), ("Rear", 0.18)):
        _tapered_link(
            f"SUM_Robot_UpperArm_{side}_Casting",
            (0.0, y_offset, 0.0),
            (deltas[1].x, y_offset, deltas[1].z),
            0.32,
            0.25,
            0.15,
            0.13,
            collection,
            parent=j2,
            material=materials["robot_paint"],
            bevel=0.035,
            role="upper_arm_fork_casting",
        )
    _box(
        "SUM_Robot_UpperArm_TorsionBridge",
        (0.28, 0.34, 0.20),
        collection,
        location=tuple(deltas[1] * 0.46),
        rotation=_align_z_to(deltas[1]),
        parent=j2,
        material=materials["paint_graphite"],
        bevel=0.025,
        role="upper_arm_torsion_bridge",
    )
    _box(
        "SUM_Robot_UpperArm_ServicePanel",
        (0.22, 0.025, 0.62),
        collection,
        location=tuple(deltas[1] * 0.48 + Vector((0.0, -0.275, 0.0))),
        rotation=_align_z_to(deltas[1]),
        parent=j2,
        material=materials["paint_graphite"],
        bevel=0.012,
        role="upper_arm_cable_service_panel",
    )
    _cylinder_between(
        "SUM_Robot_J3_ElbowHousing",
        deltas[1] + Vector((0.0, -0.29, 0.0)),
        deltas[1] + Vector((0.0, 0.29, 0.0)),
        0.31,
        collection,
        parent=j2,
        material=materials["robot_paint"],
        bevel=0.014,
        role="joint_3_elbow_housing",
    )
    _add_bolt_circle(
        "SUM_Robot_J3",
        deltas[1] + Vector((0.0, -0.315, 0.0)),
        (0.0, 1.0, 0.0),
        0.225,
        0.016,
        0.023,
        8,
        collection,
        parent=j2,
        material=materials["black_oxide"],
    )

    _tapered_link(
        "SUM_Robot_Forearm_StructuralCasting",
        (0.0, 0.0, 0.0),
        tuple(deltas[2]),
        0.38,
        0.30,
        0.34,
        0.28,
        collection,
        parent=j3,
        material=materials["robot_paint"],
        bevel=0.038,
        role="forearm_load_path_casting",
    )
    forearm_direction = deltas[2].normalized()
    _cylinder_between(
        "SUM_Robot_J4_RollHousing",
        deltas[2] - forearm_direction * 0.22,
        deltas[2] + forearm_direction * 0.20,
        0.235,
        collection,
        parent=j3,
        material=materials["paint_graphite"],
        bevel=0.012,
        role="joint_4_axial_roll_housing",
    )
    _torus(
        "SUM_Robot_J4_MachinedCollar",
        0.205,
        0.015,
        collection,
        location=tuple(deltas[2] + forearm_direction * 0.17),
        rotation=_align_z_to(forearm_direction),
        parent=j3,
        material=materials["machined_steel"],
        role="joint_4_bearing_collaring",
    )

    _tapered_link(
        "SUM_Robot_Wrist_Link_45",
        (0.0, 0.0, 0.0),
        tuple(deltas[3]),
        0.30,
        0.24,
        0.28,
        0.22,
        collection,
        parent=j4,
        material=materials["robot_paint"],
        bevel=0.030,
        role="wrist_4_to_5_structural_link",
    )
    _cylinder_between(
        "SUM_Robot_J5_WristBendHousing",
        deltas[3] + Vector((0.0, -0.235, 0.0)),
        deltas[3] + Vector((0.0, 0.235, 0.0)),
        0.245,
        collection,
        parent=j4,
        material=materials["robot_paint"],
        bevel=0.011,
        role="joint_5_wrist_bend_housing",
    )
    _add_bolt_circle(
        "SUM_Robot_J5",
        deltas[3] + Vector((0.0, -0.255, 0.0)),
        (0.0, 1.0, 0.0),
        0.175,
        0.014,
        0.020,
        6,
        collection,
        parent=j4,
        material=materials["black_oxide"],
    )

    _tapered_link(
        "SUM_Robot_Wrist_Link_56",
        (0.0, 0.0, 0.0),
        tuple(deltas[4]),
        0.22,
        0.18,
        0.21,
        0.17,
        collection,
        parent=j5,
        material=materials["robot_paint"],
        bevel=0.022,
        role="wrist_5_to_6_structural_link",
    )
    j6_direction = deltas[4].normalized()
    _cylinder_between(
        "SUM_Robot_J6_ToolRollHousing",
        deltas[4] - j6_direction * 0.13,
        deltas[4] + j6_direction * 0.17,
        0.175,
        collection,
        parent=j5,
        material=materials["paint_graphite"],
        bevel=0.009,
        role="joint_6_tool_roll_housing",
    )

    tool_direction = deltas[5].normalized()
    _cylinder_between(
        "SUM_Robot_J6_OutputSpindle",
        (0.0, 0.0, 0.0),
        deltas[5] - tool_direction * 0.060,
        0.125,
        collection,
        parent=j6,
        material=materials["paint_graphite"],
        bevel=0.007,
        role="joint_6_output_spindle",
    )
    _cylinder_between(
        "SUM_Robot_ISO_ToolFlange",
        deltas[5] - tool_direction * 0.075,
        deltas[5],
        0.155,
        collection,
        parent=j6,
        material=materials["machined_steel"],
        bevel=0.006,
        role="iso_style_tool_mounting_flange",
    )
    tool_frame = _empty(
        "SUM_Robot_EndEffector_Frame",
        collection,
        location=tuple(deltas[5]),
        rotation=_align_z_to(tool_direction),
        parent=j6,
        display_size=0.13,
    )
    tool_frame["sum_part_role"] = "end_effector_tool_center_point"
    tool_frame["tcp_offset_m"] = 0.34
    _cylinder(
        "SUM_Robot_Gripper_FlangeAdapter",
        0.15,
        0.075,
        collection,
        location=(0.0, 0.0, -0.038),
        parent=tool_frame,
        material=materials["machined_steel"],
        bevel=0.006,
        role="gripper_flange_adapter",
    )
    _add_bolt_circle(
        "SUM_Robot_ToolFlange",
        (0.0, 0.0, 0.005),
        (0.0, 0.0, 1.0),
        0.105,
        0.010,
        0.015,
        6,
        collection,
        parent=tool_frame,
        material=materials["black_oxide"],
    )
    _box(
        "SUM_Robot_Gripper_ActuatorBody",
        (0.30, 0.24, 0.18),
        collection,
        location=(0.0, 0.0, 0.14),
        parent=tool_frame,
        material=materials["paint_graphite"],
        bevel=0.025,
        role="parallel_gripper_actuator_body",
    )
    _cylinder_between(
        "SUM_Robot_Gripper_CrossActuator",
        (-0.17, 0.0, 0.15),
        (0.17, 0.0, 0.15),
        0.052,
        collection,
        parent=tool_frame,
        material=materials["brushed_steel"],
        bevel=0.005,
        role="parallel_gripper_cross_actuator",
    )
    for side, x_position in (("Left", -0.115), ("Right", 0.115)):
        _box(
            f"SUM_Robot_Gripper_{side}_Jaw",
            (0.055, 0.14, 0.32),
            collection,
            location=(x_position, 0.0, 0.36),
            parent=tool_frame,
            material=materials["machined_steel"],
            bevel=0.010,
            role="replaceable_parallel_gripper_jaw",
        )
        pad_x = x_position + (0.031 if x_position < 0 else -0.031)
        _box(
            f"SUM_Robot_Gripper_{side}_CompliantPad",
            (0.014, 0.10, 0.17),
            collection,
            location=(pad_x, 0.0, 0.40),
            parent=tool_frame,
            material=materials["rubber"],
            bevel=0.004,
            role="replaceable_gripper_contact_pad",
        )

    cable_points = [
        (0.0, -0.40, 0.54),
        (-0.03, -0.43, 1.28),
        (0.46, -0.42, 2.42),
        (1.35, -0.36, 3.02),
        (2.01, -0.30, 2.74),
        (2.38, -0.24, 2.47),
    ]
    _bezier_tube(
        "SUM_Robot_Main_DressPack_Cable",
        cable_points,
        0.022,
        collection,
        parent=root,
        material=materials["rubber"],
        role="robot_main_power_and_signal_dress_pack",
    )
    _bezier_tube(
        "SUM_Robot_Auxiliary_PneumaticLine",
        [(x, y - 0.045, z + 0.025) for x, y, z in cable_points],
        0.010,
        collection,
        parent=root,
        material=materials["safety_amber"],
        role="gripper_pneumatic_supply_line",
    )
    clamp_boxes = [
        ((0.0, -0.395, 1.20), (0.11, 0.035, 0.07)),
        ((0.46, -0.39, 2.40), (0.11, 0.035, 0.07)),
        ((1.34, -0.33, 2.97), (0.10, 0.035, 0.065)),
        ((2.02, -0.27, 2.70), (0.085, 0.030, 0.055)),
    ]
    _box_array(
        "SUM_Robot_DressPack_RoutingClamps",
        clamp_boxes,
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.006,
        role="dress_pack_routing_clamps",
    )
    return root, joints, tool_frame


def _build_bearing(
    params: ModelParameters,
    collection: bpy.types.Collection,
    materials: Dict[str, bpy.types.Material],
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    root = _empty(
        "SUM_ASSET_Precision_Bearing",
        collection,
        location=params.bearing_location,
        display_size=0.24,
    )
    root["sum_asset_type"] = "open_single_row_precision_ball_bearing"
    root["model_scale"] = "1:1 meters"
    root["outer_diameter_m"] = params.bearing_outer_diameter
    root["bore_diameter_m"] = params.bearing_bore_diameter
    root["width_m"] = params.bearing_width
    root["ball_count"] = params.bearing_ball_count
    root["presentation_pose"] = "three-quarter inspection view; dimensions unchanged"

    _box(
        "SUM_Bearing_InspectionPedestal",
        (0.58, 0.48, 0.86),
        collection,
        location=(0.0, 0.0, 0.43),
        parent=root,
        material=materials["fixture"],
        bevel=0.025,
        role="bearing_inspection_pedestal",
    )
    _box(
        "SUM_Bearing_InspectionSurface",
        (0.70, 0.56, 0.065),
        collection,
        location=(0.0, 0.0, 0.895),
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.010,
        role="precision_inspection_surface",
    )
    for side in (-1.0, 1.0):
        _box(
            f"SUM_Bearing_Cradle_{'L' if side < 0 else 'R'}",
            (0.09, 0.18, 0.13),
            collection,
            location=(side * 0.125, 0.0, 1.055),
            rotation=(0.0, side * math.radians(16.0), 0.0),
            parent=root,
            material=materials["fixture"],
            bevel=0.012,
            role="bearing_v_cradle_support",
        )
        _tapered_link(
            f"SUM_Bearing_TiltYoke_{'L' if side < 0 else 'R'}",
            (side * 0.215, 0.015, 0.94),
            (side * 0.205, 0.015, 1.205),
            0.075,
            0.055,
            0.13,
            0.10,
            collection,
            parent=root,
            material=materials["black_oxide"],
            bevel=0.009,
            role="bearing_inspection_tilt_yoke_arm",
        )

    assembly = _empty(
        "SUM_Bearing_Assembly_RotationRoot",
        collection,
        location=(0.0, -0.015, 1.30),
        rotation=(
            math.radians(78.0),
            math.radians(18.0),
            math.radians(-6.0),
        ),
        parent=root,
        display_size=0.14,
    )
    assembly["sum_part_role"] = "bearing_rotation_axis"
    assembly["rotation_axis_local"] = [0.0, 0.0, 1.0]
    assembly["inspection_pose_degrees_xyz"] = [78.0, 18.0, -6.0]

    outer_radius = params.bearing_outer_diameter * 0.5
    bore_radius = params.bearing_bore_diameter * 0.5
    ball_radius = params.bearing_ball_diameter * 0.5
    pitch_radius = (outer_radius + bore_radius) * 0.5
    outer_race_inner = pitch_radius + ball_radius * 0.98
    inner_race_outer = pitch_radius - ball_radius * 0.98

    _annular_prism(
        "SUM_Bearing_OuterRing",
        outer_radius,
        outer_race_inner,
        params.bearing_width,
        collection,
        parent=assembly,
        material=materials["machined_steel"],
        bevel=0.0035,
        role="precision_ground_outer_ring",
    )
    _annular_prism(
        "SUM_Bearing_InnerRing",
        inner_race_outer,
        bore_radius,
        params.bearing_width * 0.94,
        collection,
        parent=assembly,
        material=materials["machined_steel"],
        bevel=0.0030,
        role="precision_ground_inner_ring",
    )
    _torus(
        "SUM_Bearing_OuterRaceway_GrooveSurface",
        pitch_radius + ball_radius * 0.66,
        ball_radius * 0.36,
        collection,
        parent=assembly,
        material=materials["brushed_steel"],
        major_segments=96,
        minor_segments=16,
        role="outer_ring_raceway_contact_surface",
    )
    _torus(
        "SUM_Bearing_InnerRaceway_GrooveSurface",
        pitch_radius - ball_radius * 0.66,
        ball_radius * 0.36,
        collection,
        parent=assembly,
        material=materials["brushed_steel"],
        major_segments=96,
        minor_segments=16,
        role="inner_ring_raceway_contact_surface",
    )

    for index in range(params.bearing_ball_count):
        angle = math.tau * index / params.bearing_ball_count
        _sphere(
            f"SUM_Bearing_Ball_{index + 1:02d}",
            ball_radius,
            collection,
            location=(
                math.cos(angle) * pitch_radius,
                math.sin(angle) * pitch_radius,
                0.0,
            ),
            parent=assembly,
            material=materials["brushed_steel"],
            segments=24,
            rings=12,
            role="grade_precision_bearing_ball",
        )

    cage_outer = pitch_radius + ball_radius * 0.28
    cage_inner = pitch_radius - ball_radius * 0.28
    for side in (-1.0, 1.0):
        _annular_prism(
            f"SUM_Bearing_Cage_Rail_{'Front' if side < 0 else 'Rear'}",
            cage_outer,
            cage_inner,
            0.0025,
            collection,
            location=(0.0, 0.0, side * params.bearing_width * 0.30),
            parent=assembly,
            material=materials["bearing_cage"],
            segments=96,
            bevel=0.0007,
            role="bearing_cage_side_rail",
        )
    for index in range(params.bearing_ball_count):
        angle = math.tau * (index + 0.5) / params.bearing_ball_count
        _box(
            f"SUM_Bearing_Cage_Bridge_{index + 1:02d}",
            (ball_radius * 0.58, ball_radius * 0.88, params.bearing_width * 0.72),
            collection,
            location=(
                math.cos(angle) * pitch_radius,
                math.sin(angle) * pitch_radius,
                0.0,
            ),
            rotation=(0.0, 0.0, angle),
            parent=assembly,
            material=materials["bearing_cage"],
            bevel=0.002,
            role="bearing_cage_ball_separator",
        )
    return root, assembly


def _build_grinding_cell(
    params: ModelParameters,
    collection: bpy.types.Collection,
    materials: Dict[str, bpy.types.Material],
) -> Tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    process_bay_offset = 1.20
    cell_location = (
        params.grinding_location[0],
        params.grinding_location[1] - process_bay_offset,
        params.grinding_location[2],
    )
    root = _empty(
        "SUM_ASSET_Enclosed_InternalGrindingCell",
        collection,
        location=cell_location,
        rotation=(0.0, 0.0, math.pi),
        display_size=0.55,
    )
    root["sum_asset_type"] = "enclosed_internal_raceway_grinding_cell"
    root["cell_envelope_m"] = "3.20 depth x 4.80 width x 4.05 height"
    root["process_axis"] = (
        "B-axis process frame X, parallel work spindle and grinding spindle"
    )
    root["enclosure_center_travel_m"] = cell_location[1]
    root["process_station_travel_m"] = params.grinding_location[1]
    root["process_bay_local_offset_m"] = -process_bay_offset
    root["door_state"] = "closed"

    depth, width, height = 3.20, 4.80, 4.05
    front_x = depth * 0.5
    frame_x = depth * 0.5 - 0.10
    frame_y = width * 0.5 - 0.10
    _box(
        "SUM_GrindingCell_BasePlinth",
        (3.55, 5.10, 0.30),
        collection,
        location=(0.0, 0.0, 0.15),
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.035,
        role="machine_floor_plinth_and_coolant_sump",
    )
    frame_boxes: List[Tuple[Vec3, Vec3]] = []
    for x in (-frame_x, frame_x):
        for y in (-frame_y, frame_y):
            frame_boxes.append(((x, y, height * 0.5), (0.16, 0.16, height)))
    frame_boxes.extend(
        [
            ((0.0, -frame_y, height - 0.08), (depth, 0.16, 0.16)),
            ((0.0, frame_y, height - 0.08), (depth, 0.16, 0.16)),
            ((-frame_x, 0.0, height - 0.08), (0.16, width, 0.16)),
            ((frame_x, 0.0, height - 0.08), (0.16, width, 0.16)),
        ]
    )
    _box_array(
        "SUM_GrindingCell_StructuralFrame",
        frame_boxes,
        collection,
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.018,
        role="enclosure_structural_frame",
    )
    _box(
        "SUM_GrindingCell_RearPanel",
        (0.075, width - 0.24, height - 0.34),
        collection,
        location=(-depth * 0.5 + 0.055, 0.0, height * 0.5),
        parent=root,
        material=materials["enclosure_paint"],
        bevel=0.012,
        role="sealed_rear_service_panel",
    )
    for side in (-1.0, 1.0):
        _box(
            f"SUM_GrindingCell_SidePanel_{'L' if side < 0 else 'R'}",
            (depth - 0.24, 0.075, height - 0.34),
            collection,
            location=(0.0, side * (width * 0.5 - 0.055), height * 0.5),
            parent=root,
            material=materials["enclosure_paint"],
            bevel=0.012,
            role="sealed_side_access_panel",
        )
    _box(
        "SUM_GrindingCell_RoofPanel",
        (depth - 0.22, width - 0.22, 0.10),
        collection,
        location=(0.0, 0.0, height - 0.06),
        parent=root,
        material=materials["enclosure_paint"],
        bevel=0.016,
        role="sealed_enclosure_roof",
    )

    door_width = 2.24
    door_center_z = 1.92
    for side in (-1.0, 1.0):
        label = "Left" if side < 0 else "Right"
        center_y = side * 1.15
        lower_panel = _box(
            f"SUM_GrindingCell_{label}Door_LowerPanel",
            (0.085, door_width - 0.12, 0.92),
            collection,
            location=(front_x + 0.005, center_y, 0.86),
            parent=root,
            material=materials["enclosure_paint"],
            bevel=0.012,
            role="closed_enclosure_door_lower_panel",
        )
        lower_panel["door_side"] = label.lower()
        stile_boxes = [
            (
                (front_x + 0.005, center_y - door_width * 0.5 + 0.07, door_center_z),
                (0.085, 0.14, 2.92),
            ),
            (
                (front_x + 0.005, center_y + door_width * 0.5 - 0.07, door_center_z),
                (0.085, 0.14, 2.92),
            ),
            (
                (front_x + 0.005, center_y, 3.32),
                (0.085, door_width, 0.14),
            ),
            (
                (front_x + 0.005, center_y, 1.30),
                (0.085, door_width, 0.14),
            ),
        ]
        _box_array(
            f"SUM_GrindingCell_{label}Door_Frame",
            stile_boxes,
            collection,
            parent=root,
            material=materials["paint_graphite"],
            bevel=0.012,
            role="closed_door_window_frame",
        )
        glass = _box(
            f"SUM_GrindingCell_{label}Door_SafetyGlass",
            (0.025, door_width - 0.32, 1.78),
            collection,
            location=(front_x + 0.055, center_y, 2.31),
            parent=root,
            material=materials["safety_glass"],
            bevel=0.006,
            role="laminated_machine_safety_window",
        )
        glass["safety_glazing"] = "laminated impact-resistant placeholder"
        inner_trim = [
            (
                (front_x + 0.082, center_y - 0.96, 2.31),
                (0.060, 0.055, 1.90),
            ),
            (
                (front_x + 0.082, center_y + 0.96, 2.31),
                (0.060, 0.055, 1.90),
            ),
            (
                (front_x + 0.082, center_y, 1.37),
                (0.060, 1.975, 0.055),
            ),
            (
                (front_x + 0.082, center_y, 3.25),
                (0.060, 1.975, 0.055),
            ),
        ]
        _box_array(
            f"SUM_GrindingCell_{label}Door_InnerWindowTrim",
            inner_trim,
            collection,
            parent=root,
            material=materials["brushed_steel"],
            bevel=0.007,
            role="safety_window_retaining_trim",
        )
        handle_y = center_y - side * (door_width * 0.5 - 0.20)
        _cylinder(
            f"SUM_GrindingCell_{label}Door_Handle",
            0.024,
            0.32,
            collection,
            location=(front_x + 0.12, handle_y, 1.65),
            parent=root,
            material=materials["black_oxide"],
            segments=20,
            bevel=0.004,
            role="machine_door_pull_handle",
        )
        hinge_boxes = [
            (
                (front_x + 0.11, center_y + side * (door_width * 0.5 - 0.05), z),
                (0.16, 0.08, 0.19),
            )
            for z in (0.68, 1.90, 3.08)
        ]
        _box_array(
            f"SUM_GrindingCell_{label}Door_Hinges",
            hinge_boxes,
            collection,
            parent=root,
            material=materials["black_oxide"],
            bevel=0.008,
            role="machine_door_hinge_blocks",
        )

    _box(
        "SUM_GrindingCell_ProcessBed",
        (2.25, 3.80, 0.30),
        collection,
        location=(-0.10, -0.20, 0.64),
        parent=root,
        material=materials["fixture"],
        bevel=0.025,
        role="mineral_cast_process_bed",
    )
    _box(
        "SUM_GrindingCell_XSlide_Carriage",
        (1.55, 2.40, 0.18),
        collection,
        location=(0.30, -0.65, 0.88),
        parent=root,
        material=materials["brushed_steel"],
        bevel=0.015,
        role="grinding_spindle_linear_carriage",
    )
    _box(
        "SUM_GrindingCell_SwarfTray",
        (1.75, 3.10, 0.10),
        collection,
        location=(0.12, -0.35, 0.48),
        parent=root,
        material=materials["black_oxide"],
        bevel=0.018,
        role="coolant_and_swarf_collection_tray",
    )

    process_root = _empty(
        "SUM_GrindingCell_ProcessFrame_BAxis",
        collection,
        location=(0.0, -process_bay_offset, 0.0),
        rotation=(0.0, 0.0, math.radians(25.0)),
        parent=root,
        display_size=0.12,
    )
    process_root["sum_part_role"] = "precision_grinding_process_axis_reference"
    process_root["process_axis_yaw_degrees"] = 25.0
    process_root["bed_lateral_offset_m"] = -process_bay_offset
    process_root["layout_reason"] = (
        "serviceable B-axis presentation exposing wheel-to-bore contact"
    )

    process_center = Vector((0.08, 0.0, 1.82))
    # The profiled CBN layer is tangent to the deepest point of the internal
    # raceway.  A 49 mm wheel radius inside a 96 mm raceway radius leaves the
    # wheel spindle 47 mm off the workhead axis.
    wheel_contact_offset = 0.096 - 0.049
    _cylinder_between(
        "SUM_GrindingCell_Workhead_Housing",
        (-1.20, 0.0, 1.82),
        (-0.38, 0.0, 1.82),
        0.30,
        collection,
        parent=process_root,
        material=materials["paint_graphite"],
        bevel=0.018,
        role="workpiece_spindle_headstock",
    )
    _cylinder_between(
        "SUM_GrindingCell_WorkSpindle_Nose",
        (-0.46, 0.0, 1.82),
        (-0.05, 0.0, 1.82),
        0.115,
        collection,
        parent=process_root,
        material=materials["machined_steel"],
        bevel=0.007,
        role="precision_work_spindle_nose",
    )
    _cylinder_between(
        "SUM_GrindingCell_ThreeJawChuck",
        (-0.10, 0.0, 1.82),
        (0.02, 0.0, 1.82),
        0.19,
        collection,
        parent=process_root,
        material=materials["black_oxide"],
        segments=48,
        bevel=0.008,
        role="workpiece_precision_chuck",
    )
    for index in range(3):
        angle = math.tau * index / 3.0
        _box(
            f"SUM_GrindingCell_ChuckJaw_{index + 1}",
            (0.10, 0.060, 0.095),
            collection,
            location=(
                0.055,
                math.cos(angle) * 0.115,
                1.82 + math.sin(angle) * 0.115,
            ),
            rotation=(angle, 0.0, 0.0),
            parent=process_root,
            material=materials["machined_steel"],
            bevel=0.006,
            role="three_jaw_chuck_gripper",
        )

    workpiece = _annular_prism(
        "SUM_GrindingCell_OuterRing_Workpiece",
        0.145,
        0.085,
        0.060,
        collection,
        location=tuple(process_center),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=process_root,
        material=materials["machined_steel"],
        segments=96,
        bevel=0.003,
        role="bearing_outer_ring_internal_raceway_workpiece",
    )
    workpiece["process"] = "bearing outer-ring internal raceway grinding"
    workpiece["workpiece_type"] = "bearing_outer_ring"
    workpiece["workpiece_outer_diameter_m"] = 0.290
    workpiece["workpiece_bore_diameter_m"] = 0.170
    workpiece["rotation_axis_local"] = [0.0, 0.0, 1.0]

    _annular_prism(
        "SUM_GrindingCell_Workholding_BackupFlange",
        0.180,
        0.052,
        0.030,
        collection,
        location=(0.025, 0.0, 1.82),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=process_root,
        material=materials["black_oxide"],
        segments=72,
        bevel=0.005,
        role="workpiece_chuck_backup_and_axial_location_flange",
    )

    _cylinder_between(
        "SUM_GrindingCell_GrindingSpindle_Housing",
        (0.70, wheel_contact_offset, 1.82),
        (1.30, wheel_contact_offset, 1.82),
        0.105,
        collection,
        parent=process_root,
        material=materials["paint_graphite"],
        bevel=0.011,
        role="high_speed_internal_grinding_spindle_housing",
    )
    _cylinder_between(
        "SUM_GrindingCell_GrindingSpindle_Shaft",
        (0.092, wheel_contact_offset, 1.82),
        (0.86, wheel_contact_offset, 1.82),
        0.014,
        collection,
        parent=process_root,
        material=materials["machined_steel"],
        bevel=0.003,
        role="internal_grinding_spindle_shaft",
    )
    grinding_wheel = _cylinder_between(
        "SUM_GrindingCell_CBN_InternalGrindingWheel",
        (0.065, wheel_contact_offset, 1.82),
        (0.095, wheel_contact_offset, 1.82),
        0.012,
        collection,
        parent=process_root,
        material=materials["machined_steel"],
        segments=72,
        bevel=0.0015,
        role="cbn_internal_grinding_wheel_rotation_core",
    )
    grinding_wheel["lookdev_role"] = "brushed_metal"
    grinding_wheel["wheel_diameter_m"] = 0.098
    grinding_wheel["wheel_width_m"] = 0.024
    grinding_wheel["wheel_core_diameter_m"] = 0.024
    grinding_wheel["wheel_bond"] = "vitrified CBN"
    grinding_wheel["maximum_surface_speed_mps"] = 60.0
    # `_cylinder_between` aligns the mesh's local Z axis to the modeled shaft.
    grinding_wheel["rotation_axis_local"] = [0.0, 0.0, 1.0]
    grinding_wheel["nominal_radial_contact_offset_m"] = wheel_contact_offset
    grinding_wheel["contact_relationship"] = (
        "profiled wheel radius 0.049 m tangent to internal raceway radius 0.096 m"
    )

    _box_array(
        "SUM_GrindingCell_TaskLight_Carrier",
        [
            ((0.90, -0.58, 2.25), (0.075, 0.075, 0.72)),
            ((0.59, -0.47, 2.58), (0.70, 0.075, 0.075)),
        ],
        collection,
        parent=process_root,
        material=materials["paint_graphite"],
        bevel=0.010,
        role="local_process_task_light_structural_carrier",
    )
    _box(
        "SUM_GrindingCell_TaskLight_Diffuser",
        (0.42, 0.14, 0.045),
        collection,
        location=(0.28, -0.34, 2.54),
        rotation=(0.0, math.radians(12.0), 0.0),
        parent=process_root,
        material=materials["luminaire_diffuser"],
        bevel=0.008,
        role="local_process_task_light_diffuser_placeholder",
    )

    _box(
        "SUM_GrindingCell_Dresser_Post",
        (0.16, 0.13, 0.42),
        collection,
        location=(0.35, -0.31, 1.27),
        parent=process_root,
        material=materials["black_oxide"],
        bevel=0.012,
        role="grinding_wheel_dresser_post",
    )
    _sphere(
        "SUM_GrindingCell_Dresser_DiamondTip",
        0.018,
        collection,
        location=(0.35, -0.31, 1.49),
        parent=process_root,
        material=materials["machined_steel"],
        segments=16,
        rings=8,
        role="single_point_dressing_tool_tip",
    )
    _bezier_tube(
        "SUM_GrindingCell_CoolantSupplyLine",
        [
            (0.96, -0.42, 2.18),
            (0.69, -0.34, 2.10),
            (0.39, -0.22, 1.94),
            (0.22, -0.12, 1.87),
        ],
        0.012,
        collection,
        parent=process_root,
        material=materials["brushed_steel"],
        role="directed_grinding_coolant_line",
    )
    _cylinder_between(
        "SUM_GrindingCell_CoolantNozzle",
        (0.22, -0.12, 1.87),
        (0.14, -0.05, 1.83),
        0.018,
        collection,
        parent=process_root,
        material=materials["black_oxide"],
        segments=20,
        bevel=0.002,
        role="adjustable_coolant_nozzle",
    )

    tower_parent = _empty(
        "SUM_GrindingCell_StatusTower_Root",
        collection,
        location=(0.0, -2.08, height),
        parent=root,
        display_size=0.10,
    )
    _cylinder(
        "SUM_GrindingCell_StatusTower_Stem",
        0.018,
        0.30,
        collection,
        location=(0.0, 0.0, 0.15),
        parent=tower_parent,
        material=materials["black_oxide"],
        segments=16,
        bevel=0.002,
        role="machine_status_tower_stem",
    )
    for index, (label, material) in enumerate(
        (
            ("Red", materials["indicator_red"]),
            ("Amber", materials["safety_amber"]),
            ("Green", materials["indicator_green"]),
        )
    ):
        _cylinder(
            f"SUM_GrindingCell_StatusTower_{label}",
            0.052,
            0.075,
            collection,
            location=(0.0, 0.0, 0.34 + index * 0.078),
            parent=tower_parent,
            material=material,
            segments=24,
            bevel=0.004,
            role=f"machine_status_indicator_{label.lower()}",
        )
    return root, workpiece, grinding_wheel


def _extruded_profile_y(
    name: str,
    profile_xz: Sequence[Tuple[float, float]],
    y_start: float,
    y_end: float,
    collection: bpy.types.Collection,
    *,
    parent: bpy.types.Object,
    material: bpy.types.Material,
    bevel: float,
    role: str,
) -> bpy.types.Object:
    count = len(profile_xz)
    vertices: List[Vec3] = [
        (x, y_start, z) for x, z in profile_xz
    ] + [
        (x, y_end, z) for x, z in profile_xz
    ]
    faces: List[Tuple[int, ...]] = [
        tuple(reversed(range(count))),
        tuple(range(count, count * 2)),
    ]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, next_index + count, index + count))
    obj = _mesh_object(
        name,
        vertices,
        faces,
        collection,
        parent=parent,
        material=material,
        bevel=bevel,
        smooth=True,
    )
    return _mark_part(obj, role)


def _build_guide_system(
    params: ModelParameters,
    collection: bpy.types.Collection,
    materials: Dict[str, bpy.types.Material],
) -> bpy.types.Object:
    root = _empty(
        "SUM_ASSET_DualRail_GuideSystem",
        collection,
        display_size=0.45,
    )
    root["sum_asset_type"] = "scene_length_dual_rail_guide"
    root["guide_count"] = 2
    root["rail_gauge_m"] = params.rail_gauge
    root["guide_length_m"] = params.rail_end_y - params.rail_start_y
    root["visual_rule"] = "only continuous longitudinal leading lines in scene"
    root["guide_type"] = "floor_embedded_low_profile_logistics_linear_rail"

    half_gauge = params.rail_gauge * 0.5
    base_profile = [
        (-0.095, 0.004),
        (0.095, 0.004),
        (0.095, 0.022),
        (0.058, 0.032),
        (0.045, 0.074),
        (0.035, 0.090),
        (-0.035, 0.090),
        (-0.045, 0.074),
        (-0.058, 0.032),
        (-0.095, 0.022),
    ]
    for side, x_offset in (("Left", -half_gauge), ("Right", half_gauge)):
        profile = [(x + x_offset, z) for x, z in base_profile]
        rail = _extruded_profile_y(
            f"SUM_Guide_{side}_RailProfile",
            profile,
            params.rail_start_y,
            params.rail_end_y,
            collection,
            parent=root,
            material=materials["rail_steel"],
            bevel=0.004,
            role="floor_embedded_logistics_linear_guide_profile",
        )
        rail["rail_side"] = side.lower()
        rail["profile_height_m"] = 0.086

    mounting_plates: List[Tuple[Vec3, Vec3]] = []
    bolt_centers: List[Vec3] = []
    mount_y = params.rail_start_y
    while mount_y <= params.rail_end_y + 1.0e-6:
        for x in (-half_gauge, half_gauge):
            mounting_plates.append(
                ((x, mount_y, 0.012), (0.30, 0.26, 0.024))
            )
            for x_offset in (-0.105, 0.105):
                for y_offset in (-0.075, 0.075):
                    bolt_centers.append(
                        (x + x_offset, mount_y + y_offset, 0.034)
                    )
        mount_y += params.rail_mount_spacing
    _box_array(
        "SUM_Guide_EmbeddedMountingPlates",
        mounting_plates,
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.004,
        role="rhythmic_floor_embedded_rail_mounting_plates",
    )
    _prism_array(
        "SUM_Guide_MountingPlateBolts",
        bolt_centers,
        0.012,
        0.018,
        6,
        collection,
        parent=root,
        material=materials["machined_steel"],
        bevel=0.0015,
        role="embedded_guide_mounting_fasteners",
    )
    root["mounting_plate_spacing_m"] = params.rail_mount_spacing
    root["cross_sleepers_removed"] = True
    return root


def _build_factory_envelope(
    params: ModelParameters,
    collection: bpy.types.Collection,
    materials: Dict[str, bpy.types.Material],
) -> bpy.types.Object:
    root = _empty(
        "SUM_ASSET_FactoryEnvelope",
        collection,
        display_size=0.75,
    )
    floor_start = params.rail_start_y - 4.0
    floor_end = params.rail_end_y + 4.0
    floor_length = floor_end - floor_start
    floor_center = (floor_start + floor_end) * 0.5
    hall_width = 16.0
    clear_height = 6.30

    root["sum_asset_type"] = "bright_clean_factory_envelope"
    root["bounds_m"] = f"{hall_width:.2f} x {floor_length:.2f} x 6.65"
    root["structural_logic"] = (
        "floor slab, repeated portal frames, upper wall panels, roof panels, "
        "luminaire carriers, and robot-cell guard fence"
    )

    _box(
        "SUM_Factory_LightGray_FloorSlab",
        (hall_width, floor_length, 0.18),
        collection,
        location=(0.0, floor_center, -0.09),
        parent=root,
        material=materials["factory_floor"],
        bevel=0.012,
        role="clean_factory_floor_slab",
    )
    expansion_joint_boxes: List[Tuple[Vec3, Vec3]] = []
    joint_y = floor_start + 8.0
    while joint_y < floor_end - 2.0:
        expansion_joint_boxes.append(
            ((0.0, joint_y, 0.002), (hall_width - 0.24, 0.026, 0.006))
        )
        joint_y += 12.0
    _box_array(
        "SUM_Factory_Floor_ExpansionJoints",
        expansion_joint_boxes,
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.001,
        role="inlaid_floor_expansion_joints",
    )

    portal_positions: List[float] = []
    portal_y = -2.0
    while portal_y <= floor_end - 4.0:
        portal_positions.append(portal_y)
        portal_y += 16.0
    column_x = hall_width * 0.5 - 0.70
    portal_boxes: List[Tuple[Vec3, Vec3]] = []
    portal_base_boxes: List[Tuple[Vec3, Vec3]] = []
    portal_anchor_centers: List[Vec3] = []
    for position in portal_positions:
        for x in (-column_x, column_x):
            portal_boxes.append(((x, position, clear_height * 0.5), (0.24, 0.32, clear_height)))
            portal_base_boxes.append(((x, position, 0.035), (0.52, 0.58, 0.07)))
            for x_offset in (-0.16, 0.16):
                for y_offset in (-0.18, 0.18):
                    portal_anchor_centers.append(
                        (x + x_offset, position + y_offset, 0.082)
                    )
        portal_boxes.append(
            ((0.0, position, clear_height + 0.12), (column_x * 2.0 + 0.24, 0.32, 0.28))
        )
    _box_array(
        "SUM_Factory_Repeated_StructuralPortalFrames",
        portal_boxes,
        collection,
        parent=root,
        material=materials["factory_structure"],
        bevel=0.018,
        role="repeated_load_bearing_factory_portal_frames",
    )
    _box_array(
        "SUM_Factory_Portal_BasePlates",
        portal_base_boxes,
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.010,
        role="portal_column_floor_base_plates",
    )
    _prism_array(
        "SUM_Factory_Portal_AnchorBolts",
        portal_anchor_centers,
        0.018,
        0.035,
        6,
        collection,
        parent=root,
        material=materials["machined_steel"],
        bevel=0.002,
        role="portal_column_floor_anchor_fasteners",
    )

    marker_boxes: List[Tuple[Vec3, Vec3]] = []
    for portal_position in portal_positions[:2]:
        for x in (-column_x, column_x):
            for meter_height in (1.0, 2.0, 3.0, 4.0, 5.0):
                marker_boxes.append(
                    ((x, portal_position - 0.174, meter_height), (0.14, 0.020, 0.035))
                )
    _box_array(
        "SUM_Factory_Entrance_ClearanceScaleMarkers",
        marker_boxes,
        collection,
        parent=root,
        material=materials["safety_amber"],
        bevel=0.003,
        role="one_meter_clearance_scale_markers",
    )

    upper_wall_height = 3.25
    upper_wall_center_z = 4.72
    for side, x in (("Left", -hall_width * 0.5 + 0.05), ("Right", hall_width * 0.5 - 0.05)):
        _box(
            f"SUM_Factory_{side}_UpperWall_Panels",
            (0.10, floor_length, upper_wall_height),
            collection,
            location=(x, floor_center, upper_wall_center_z),
            parent=root,
            material=materials["factory_wall"],
            bevel=0.012,
            role="white_insulated_factory_upper_wall_panels",
        )
    _box(
        "SUM_Factory_White_RoofPanels",
        (hall_width - 0.20, floor_length, 0.10),
        collection,
        location=(0.0, floor_center, 6.58),
        parent=root,
        material=materials["factory_wall"],
        bevel=0.014,
        role="white_insulated_factory_roof_panels",
    )

    carrier_boxes = [
        ((x, floor_center, 6.43), (0.20, floor_length - 0.40, 0.12))
        for x in (-2.85, 2.85)
    ]
    diffuser_boxes = [
        ((x, floor_center, 6.355), (0.085, floor_length - 0.80, 0.025))
        for x in (-2.85, 2.85)
    ]
    _box_array(
        "SUM_Factory_Longitudinal_LuminaireCarrierChannels",
        carrier_boxes,
        collection,
        parent=root,
        material=materials["factory_structure"],
        bevel=0.012,
        role="ceiling_luminaire_load_carrier_channels",
    )
    _box_array(
        "SUM_Factory_Longitudinal_LuminaireDiffusers",
        diffuser_boxes,
        collection,
        parent=root,
        material=materials["luminaire_diffuser"],
        bevel=0.006,
        role="neutral_white_linear_luminaire_diffusers",
    )

    fence_x = -5.10
    fence_y_positions = (14.5, 17.0, 19.5, 22.0)
    fence_posts = [
        ((fence_x, y, 0.82), (0.085, 0.085, 1.64))
        for y in fence_y_positions
    ]
    fence_rails = [
        ((fence_x, 18.25, z), (0.075, 7.50, 0.075))
        for z in (0.34, 1.48)
    ]
    fence_returns = [
        ((-4.48, y, z), (1.24, 0.075, 0.075))
        for y in (14.5, 22.0)
        for z in (0.34, 1.48)
    ]
    _box_array(
        "SUM_Factory_RobotCell_GuardFence_Frame",
        [*fence_posts, *fence_rails, *fence_returns],
        collection,
        parent=root,
        material=materials["factory_structure"],
        bevel=0.009,
        role="robot_cell_machine_guard_fence_frame",
    )
    fence_panels = [
        ((fence_x + 0.012, (start + end) * 0.5, 0.91), (0.025, end - start - 0.14, 1.02))
        for start, end in zip(fence_y_positions, fence_y_positions[1:])
    ]
    _box_array(
        "SUM_Factory_RobotCell_GuardFence_Panels",
        fence_panels,
        collection,
        parent=root,
        material=materials["safety_glass"],
        bevel=0.006,
        role="transparent_robot_cell_guard_fence_panels",
    )
    root["portal_spacing_m"] = 16.0
    root["expansion_joint_spacing_m"] = 12.0
    root["guarded_machine_bay"] = "robot at travel 18.5 m"
    return root


def _build_final_inspection_portal(
    params: ModelParameters,
    collection: bpy.types.Collection,
    materials: Dict[str, bpy.types.Material],
) -> bpy.types.Object:
    root = _empty(
        "SUM_ASSET_FinalPrecisionInspectionPortal",
        collection,
        location=(0.0, params.final_anchor_travel, 2.70),
        display_size=0.40,
    )
    root["sum_asset_type"] = "end_wall_integrated_precision_inspection_portal"
    root["portal_clear_opening_m"] = "5.00 x 4.20"
    root["anchor_height_m"] = 2.70
    root["design_rule"] = "rectilinear layered steel frame; no circular neon motif"

    _box(
        "SUM_FinalPortal_Integrated_EndWall",
        (15.80, 0.18, 6.50),
        collection,
        location=(0.0, 3.00, 0.55),
        parent=root,
        material=materials["factory_wall"],
        bevel=0.014,
        role="factory_end_wall_insulated_panel",
    )
    _box_array(
        "SUM_FinalPortal_InspectionDoor_Panels",
        [
            ((-1.22, 2.56, -0.20), (2.38, 0.14, 4.46)),
            ((1.22, 2.56, -0.20), (2.38, 0.14, 4.46)),
        ],
        collection,
        parent=root,
        material=materials["enclosure_paint"],
        bevel=0.035,
        role="precision_split_inspection_door_panels",
    )
    _box_array(
        "SUM_FinalPortal_DoorPanel_Datums",
        [
            ((0.0, 2.475, -0.20), (0.045, 0.025, 4.38)),
            ((0.0, 2.472, -1.15), (4.72, 0.025, 0.045)),
        ],
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.004,
        role="inspection_door_center_seam_and_datum",
    )

    outer_frame = [
        ((-3.05, 1.72, 0.00), (0.38, 0.52, 5.42)),
        ((3.05, 1.72, 0.00), (0.38, 0.52, 5.42)),
        ((0.0, 1.72, 2.72), (6.48, 0.52, 0.40)),
    ]
    middle_frame = [
        ((-2.76, 1.43, -0.06), (0.22, 0.32, 4.88)),
        ((2.76, 1.43, -0.06), (0.22, 0.32, 4.88)),
        ((0.0, 1.43, 2.39), (5.74, 0.32, 0.24)),
    ]
    inner_frame = [
        ((-2.52, 1.20, -0.13), (0.14, 0.22, 4.28)),
        ((2.52, 1.20, -0.13), (0.14, 0.22, 4.28)),
        ((0.0, 1.20, 2.02), (5.18, 0.22, 0.16)),
    ]
    _box_array(
        "SUM_FinalPortal_Outer_StructuralFrame",
        outer_frame,
        collection,
        parent=root,
        material=materials["factory_structure"],
        bevel=0.035,
        role="inspection_portal_primary_load_frame",
    )
    _box_array(
        "SUM_FinalPortal_Middle_MachinedFrame",
        middle_frame,
        collection,
        parent=root,
        material=materials["brushed_steel"],
        bevel=0.022,
        role="inspection_portal_secondary_machined_frame",
    )
    _box_array(
        "SUM_FinalPortal_Inner_GraphiteFrame",
        inner_frame,
        collection,
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.016,
        role="inspection_portal_inner_sealing_frame",
    )

    light_recesses = [
        ((-2.43, 1.075, -0.15), (0.080, 0.045, 3.94)),
        ((2.43, 1.075, -0.15), (0.080, 0.045, 3.94)),
        ((0.0, 1.075, 1.84), (4.94, 0.045, 0.080)),
    ]
    amber_guides = [
        ((-2.43, 1.045, -0.15), (0.025, 0.018, 3.76)),
        ((2.43, 1.045, -0.15), (0.025, 0.018, 3.76)),
        ((0.0, 1.045, 1.75), (4.885, 0.018, 0.025)),
    ]
    _box_array(
        "SUM_FinalPortal_EmbeddedGuideLight_Recesses",
        light_recesses,
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.008,
        role="recessed_rectilinear_guide_light_channels",
    )
    _box_array(
        "SUM_FinalPortal_EmbeddedGuideLight_Amber",
        amber_guides,
        collection,
        parent=root,
        material=materials["safety_amber"],
        bevel=0.005,
        role="embedded_amber_inspection_portal_guide_lines",
    )

    _box(
        "SUM_FinalPortal_InspectionWindow_Recess",
        (3.10, 0.045, 0.64),
        collection,
        location=(0.0, 2.455, 0.56),
        parent=root,
        material=materials["black_oxide"],
        bevel=0.018,
        role="inspection_door_window_recess",
    )
    _box(
        "SUM_FinalPortal_InspectionWindow_Glass",
        (2.86, 0.025, 0.44),
        collection,
        location=(0.0, 2.420, 0.56),
        parent=root,
        material=materials["safety_glass"],
        bevel=0.012,
        role="laminated_inspection_door_window",
    )

    _box_array(
        "SUM_FinalPortal_Floor_BasePlates",
        [
            ((-3.05, 1.72, -2.66), (0.72, 0.80, 0.08)),
            ((3.05, 1.72, -2.66), (0.72, 0.80, 0.08)),
        ],
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.012,
        role="inspection_portal_floor_base_plates",
    )
    portal_anchor_bolts = [
        (x + x_offset, 1.72 + y_offset, -2.57)
        for x in (-3.05, 3.05)
        for x_offset in (-0.22, 0.22)
        for y_offset in (-0.25, 0.25)
    ]
    _prism_array(
        "SUM_FinalPortal_Floor_AnchorBolts",
        portal_anchor_bolts,
        0.026,
        0.055,
        6,
        collection,
        parent=root,
        material=materials["machined_steel"],
        bevel=0.003,
        role="inspection_portal_floor_anchor_fasteners",
    )
    wall_ties = [
        ((x, 2.36, z), (0.22, 1.12, 0.22))
        for x in (-3.05, 3.05)
        for z in (-1.65, 0.45, 2.35)
    ]
    _box_array(
        "SUM_FinalPortal_EndWall_ConnectionBrackets",
        wall_ties,
        collection,
        parent=root,
        material=materials["factory_structure"],
        bevel=0.014,
        role="portal_frame_to_end_wall_connection_brackets",
    )

    _box(
        "SUM_FinalPortal_FelixZuo_Nameplate",
        (0.68, 0.045, 0.18),
        collection,
        location=(-1.92, 1.025, 2.28),
        parent=root,
        material=materials["black_oxide"],
        bevel=0.012,
        role="small_low_contrast_metal_nameplate",
    )
    name = _text_label(
        "SUM_FinalPortal_FelixZuo_NameplateText",
        "Felix Zuo",
        0.085,
        collection,
        location=(-1.92, 0.995, 2.28),
        rotation=(math.pi * 0.5, 0.0, 0.0),
        parent=root,
        material=materials["brushed_steel"],
        role="single_low_contrast_felix_zuo_nameplate_text",
    )
    name["brand_treatment"] = "single small environmental metal plaque"
    return root


def _build_screen_station(
    index: int,
    location: Vec3,
    params: ModelParameters,
    collection: bpy.types.Collection,
    materials: Dict[str, bpy.types.Material],
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    on_right = location[0] > 0.0
    rotation_z = math.pi if on_right else 0.0
    root = _empty(
        f"SUM_ASSET_ScreenStation_{index:02d}",
        collection,
        location=location,
        rotation=(0.0, 0.0, rotation_z),
        display_size=0.32,
    )
    root["sum_asset_type"] = "floor_anchored_project_screen_station"
    root["station_index"] = index
    root["faces_scene_centerline"] = True
    root["project_image_slot"] = f"PROJECT_IMAGE_{index:02d}"
    root["mounting_logic"] = (
        "floor anchors -> equipment cabinet -> structural mast -> pivoted VESA arm"
    )

    _box(
        f"SUM_ScreenStation_{index:02d}_BasePlinth",
        (0.86, 1.02, 0.11),
        collection,
        location=(-0.30, 0.0, 0.055),
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.018,
        role="screen_station_floor_plinth",
    )
    _prism_array(
        f"SUM_ScreenStation_{index:02d}_FloorAnchorBolts",
        [
            (-0.62, -0.39, 0.135),
            (-0.62, 0.39, 0.135),
            (0.02, -0.39, 0.135),
            (0.02, 0.39, 0.135),
        ],
        0.022,
        0.040,
        6,
        collection,
        parent=root,
        material=materials["machined_steel"],
        bevel=0.002,
        role="screen_station_floor_anchor_fasteners",
    )
    _box(
        f"SUM_ScreenStation_{index:02d}_EquipmentCabinet",
        (0.68, 0.84, 1.02),
        collection,
        location=(-0.34, 0.0, 0.61),
        parent=root,
        material=materials["enclosure_paint"],
        bevel=0.035,
        role="screen_station_power_and_media_cabinet",
    )
    _box(
        f"SUM_ScreenStation_{index:02d}_CabinetDoor",
        (0.025, 0.69, 0.80),
        collection,
        location=(0.012, 0.0, 0.63),
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.008,
        role="screen_station_service_door",
    )
    vent_boxes = [
        ((0.031, -0.22 + slot * 0.11, 0.35), (0.018, 0.065, 0.018))
        for slot in range(5)
    ]
    _box_array(
        f"SUM_ScreenStation_{index:02d}_CabinetVents",
        vent_boxes,
        collection,
        parent=root,
        material=materials["black_oxide"],
        bevel=0.003,
        role="cabinet_filtered_vent_slots",
    )
    _box(
        f"SUM_ScreenStation_{index:02d}_SupportMast",
        (0.19, 0.24, 1.72),
        collection,
        location=(-0.33, 0.0, 1.78),
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.025,
        role="screen_station_structural_mast",
    )
    for side in (-1.0, 1.0):
        _box(
            f"SUM_ScreenStation_{index:02d}_MastGusset_{'L' if side < 0 else 'R'}",
            (0.34, 0.035, 0.25),
            collection,
            location=(-0.25, side * 0.115, 1.13),
            rotation=(0.0, math.radians(-34.0), 0.0),
            parent=root,
            material=materials["factory_structure"],
            bevel=0.008,
            role="screen_mast_load_transfer_gusset",
        )
    _box(
        f"SUM_ScreenStation_{index:02d}_VESA_MountArm",
        (0.48, 0.18, 0.16),
        collection,
        location=(-0.09, 0.0, 2.46),
        parent=root,
        material=materials["brushed_steel"],
        bevel=0.018,
        role="screen_station_serviceable_mount_arm",
    )
    _cylinder_between(
        f"SUM_ScreenStation_{index:02d}_MountPivot",
        (-0.31, -0.13, 2.46),
        (-0.31, 0.13, 2.46),
        0.105,
        collection,
        parent=root,
        material=materials["black_oxide"],
        segments=32,
        bevel=0.007,
        role="screen_mount_tilt_pivot",
    )

    active_width = params.screen_active_width
    active_height = params.screen_active_height
    outer_width = active_width + 0.30
    outer_height = active_height + 0.30
    screen_center_z = 2.54
    _box(
        f"SUM_ScreenStation_{index:02d}_RearShell",
        (0.15, outer_width, outer_height),
        collection,
        location=(0.14, 0.0, screen_center_z),
        parent=root,
        material=materials["screen_frame"],
        bevel=0.045,
        role="industrial_display_rear_shell",
    )
    bezel_boxes = [
        ((0.226, 0.0, screen_center_z + active_height * 0.5 + 0.075), (0.055, outer_width, 0.15)),
        ((0.226, 0.0, screen_center_z - active_height * 0.5 - 0.075), (0.055, outer_width, 0.15)),
        ((0.226, active_width * 0.5 + 0.075, screen_center_z), (0.055, 0.15, active_height)),
        ((0.226, -active_width * 0.5 - 0.075, screen_center_z), (0.055, 0.15, active_height)),
    ]
    _box_array(
        f"SUM_ScreenStation_{index:02d}_FrontBezel",
        bezel_boxes,
        collection,
        parent=root,
        material=materials["screen_frame"],
        bevel=0.018,
        role="replaceable_industrial_display_bezel",
    )
    display = _display_surface(
        f"SUM_ScreenStation_{index:02d}_DisplaySurface",
        active_width,
        active_height,
        collection,
        location=(0.257, 0.0, screen_center_z),
        parent=root,
        material=materials["screen_content"],
    )
    display["project_image_slot"] = f"PROJECT_IMAGE_{index:02d}"
    display["station_index"] = index
    display["recommended_image_color_space"] = "sRGB"
    display["recommended_image_fit"] = "contain or center-crop to 16:10"

    bezel_bolt_centers = [
        (0.262, y, z)
        for y in (-outer_width * 0.5 + 0.07, outer_width * 0.5 - 0.07)
        for z in (-outer_height * 0.5 + screen_center_z + 0.07, outer_height * 0.5 + screen_center_z - 0.07)
    ]
    # Axis is local X; each fastener remains individually replaceable if needed.
    for bolt_index, center in enumerate(bezel_bolt_centers, start=1):
        _cylinder_between(
            f"SUM_ScreenStation_{index:02d}_BezelBolt_{bolt_index:02d}",
            Vector(center) - Vector((0.008, 0.0, 0.0)),
            Vector(center) + Vector((0.008, 0.0, 0.0)),
            0.012,
            collection,
            parent=root,
            material=materials["machined_steel"],
            segments=6,
            bevel=0.0015,
            role="display_bezel_service_fastener",
        )

    _cylinder_between(
        f"SUM_ScreenStation_{index:02d}_EmergencyStop_Base",
        (0.008, -0.28, 0.82),
        (0.075, -0.28, 0.82),
        0.052,
        collection,
        parent=root,
        material=materials["safety_amber"],
        segments=32,
        bevel=0.004,
        role="emergency_stop_yellow_backplate",
    )
    _cylinder_between(
        f"SUM_ScreenStation_{index:02d}_EmergencyStop_Button",
        (0.075, -0.28, 0.82),
        (0.125, -0.28, 0.82),
        0.038,
        collection,
        parent=root,
        material=materials["indicator_red"],
        segments=32,
        bevel=0.005,
        role="emergency_stop_mushroom_button",
    )
    _cylinder_between(
        f"SUM_ScreenStation_{index:02d}_StatusIndicator",
        (0.225, -outer_width * 0.5 + 0.09, screen_center_z + outer_height * 0.5 - 0.08),
        (0.275, -outer_width * 0.5 + 0.09, screen_center_z + outer_height * 0.5 - 0.08),
        0.026,
        collection,
        parent=root,
        material=materials["indicator_green"],
        segments=24,
        bevel=0.003,
        role="screen_station_live_status_indicator",
    )
    _bezier_tube(
        f"SUM_ScreenStation_{index:02d}_PowerDataConduit",
        [
            (-0.38, 0.34, 0.92),
            (-0.40, 0.34, 1.55),
            (-0.34, 0.28, 2.26),
            (0.05, 0.20, 2.46),
        ],
        0.016,
        collection,
        parent=root,
        material=materials["rubber"],
        role="screen_station_power_and_data_conduit",
    )
    root["display_surface_object"] = display.name
    root["active_screen_dimensions_m"] = f"{active_width:.3f} x {active_height:.3f}"
    return root, display


def build_models(
    parameters: Optional[ModelParameters] = None,
) -> Dict[str, Any]:
    """Build and return all named modeling assets.

    Args:
        parameters: Optional immutable meter-based controls. Calling without an
            argument uses production defaults.

    Returns:
        A stable dictionary containing asset roots, six robot joint controls,
        four UV-mapped display surfaces, placeholder materials, and managed
        collections. Values are live Blender datablocks.
    """

    params = parameters or ModelParameters()
    _validate_parameters(params)

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.unit_settings.scale_length = 1.0
    scene["sum_modeling_units"] = "meters"
    scene["sum_model_authoring_frame"] = "X lateral, +Y travel, +Z up"
    scene["sum_scene_forward_axis"] = "-Z"
    scene["sum_scene_up_axis"] = "+Y"

    root_collection = _reset_root_collection(params.collection_name)
    layout_root = _empty(
        "SUM_ASSET_LayoutTransform",
        root_collection,
        rotation=(-math.pi * 0.5, 0.0, 0.0),
        display_size=0.65,
    )
    layout_root["sum_asset_type"] = "authoring_to_film_coordinate_transform"
    layout_root["coordinate_mapping"] = "(x, travel, up) -> (x, up, -travel)"
    collections = {
        "robot": _child_collection(root_collection, "SUM_MODEL_Robot"),
        "bearing": _child_collection(root_collection, "SUM_MODEL_Bearing"),
        "grinding_cell": _child_collection(root_collection, "SUM_MODEL_GrindingCell"),
        "guide_system": _child_collection(root_collection, "SUM_MODEL_GuideSystem"),
        "factory_envelope": _child_collection(root_collection, "SUM_MODEL_FactoryEnvelope"),
        "screen_stations": _child_collection(root_collection, "SUM_MODEL_ScreenStations"),
    }
    materials = _build_placeholder_materials()

    factory_envelope = _build_factory_envelope(
        params, collections["factory_envelope"], materials
    )
    final_inspection_portal = _build_final_inspection_portal(
        params, collections["factory_envelope"], materials
    )
    final_inspection_portal.parent = factory_envelope
    guide_system = _build_guide_system(
        params, collections["guide_system"], materials
    )
    robot, robot_joints, robot_tcp = _build_robot(
        params, collections["robot"], materials
    )
    bearing, bearing_rotation_root = _build_bearing(
        params, collections["bearing"], materials
    )
    grinding_cell, grinding_workpiece, grinding_wheel = _build_grinding_cell(
        params, collections["grinding_cell"], materials
    )

    screen_stations: List[bpy.types.Object] = []
    display_surfaces: List[bpy.types.Object] = []
    for index, location in enumerate(params.screen_station_locations, start=1):
        station, display = _build_screen_station(
            index,
            location,
            params,
            collections["screen_stations"],
            materials,
        )
        screen_stations.append(station)
        display_surfaces.append(display)

    for asset_root in (
        factory_envelope,
        guide_system,
        robot,
        bearing,
        grinding_cell,
        *screen_stations,
    ):
        asset_root.parent = layout_root

    entry_anchor = _empty(
        "SUM_ANCHOR_Entry",
        root_collection,
        location=(0.0, params.entry_anchor_travel, 0.75),
        parent=layout_root,
        display_size=0.16,
    )
    impact_anchor = _empty(
        "SUM_ANCHOR_BearingImpact",
        collections["bearing"],
        location=(0.0, -0.015, 1.30),
        parent=bearing,
        display_size=0.16,
    )
    grinding_contact = _empty(
        "SUM_ANCHOR_GrindingContact",
        collections["grinding_cell"],
        location=(0.08, 0.096, 1.82),
        parent=grinding_wheel.parent,
        display_size=0.08,
    )
    handoff_anchor = _empty(
        "SUM_ANCHOR_RobotHandoff",
        collections["robot"],
        location=(
            -params.robot_location[0],
            params.handoff_anchor_travel - params.robot_location[1],
            2.30,
        ),
        parent=robot,
        display_size=0.14,
    )
    final_anchor = _empty(
        "SUM_ANCHOR_FinalPortal",
        collections["factory_envelope"],
        location=(0.0, 0.0, 0.0),
        parent=final_inspection_portal,
        display_size=0.18,
    )
    for anchor, role in (
        (entry_anchor, "cinematography_entry_anchor"),
        (impact_anchor, "cinematography_impact_anchor"),
        (grinding_contact, "grinding_wheel_to_workpiece_contact_anchor"),
        (handoff_anchor, "robot_handoff_action_anchor"),
        (final_anchor, "cinematography_final_anchor"),
    ):
        anchor["sum_part_role"] = role
        anchor.hide_render = True

    anchors = {
        "entry_anchor": entry_anchor,
        "impact_anchor": impact_anchor,
        "bearing_anchor": impact_anchor,
        "robot_anchor": handoff_anchor,
        "robot_handoff": handoff_anchor,
        "grinding_contact": grinding_contact,
        "screen_01": display_surfaces[0],
        "screen_02": display_surfaces[1],
        "screen_03": display_surfaces[2],
        "screen_04": display_surfaces[3],
        "notice_card": display_surfaces[0],
        "visibility_card": display_surfaces[2],
        "systems_card": display_surfaces[3],
        "final_portal": final_inspection_portal,
        "close_anchor": final_anchor,
    }

    travel_anchors = {
        "entry": entry_anchor,
        "impact_bearing": impact_anchor,
        "robot": handoff_anchor,
        "grinding": grinding_contact,
        "screen_01": display_surfaces[0],
        "screen_02": display_surfaces[1],
        "screen_03": display_surfaces[2],
        "screen_04": display_surfaces[3],
        "final": final_anchor,
    }

    bpy.context.view_layer.update()

    assets: Dict[str, Any] = {
        "root_collection": root_collection,
        "layout_root": layout_root,
        "factory_envelope": factory_envelope,
        "final_inspection_portal": final_inspection_portal,
        "dual_rail_guide": guide_system,
        "robot_arm_6axis": robot,
        "robot_joints": robot_joints,
        "robot_tcp": robot_tcp,
        "precision_bearing": bearing,
        "bearing_rotation_root": bearing_rotation_root,
        "enclosed_grinding_cell": grinding_cell,
        "grinding_workpiece": grinding_workpiece,
        "grinding_wheel": grinding_wheel,
        "screen_stations": screen_stations,
        "screen_displays": display_surfaces,
        "screens": display_surfaces,
        "anchors": anchors,
        "travel_anchors": travel_anchors,
        "placeholder_materials": materials,
        "materials": materials,
        "collections": collections,
        "parameters": params,
        # Compatibility aliases consumed by the current assembly and camera scripts.
        "entry_anchor": entry_anchor,
        "rail_entry_anchor": entry_anchor,
        "impact_anchor": impact_anchor,
        "bearing_anchor": impact_anchor,
        "grinding_cell": grinding_cell,
        "grinding_anchor": grinding_contact,
        "grinding_contact": grinding_contact,
        "spark_origin": grinding_contact,
        "notice_screen": display_surfaces[0],
        "screen_notice": display_surfaces[0],
        "robot_handoff": handoff_anchor,
        "handoff_anchor": handoff_anchor,
        "mechanical_arm_handoff": handoff_anchor,
        "screen_takt": display_surfaces[1],
        "screen_visibility": display_surfaces[2],
        "screen_systems": display_surfaces[3],
        "final_anchor": final_anchor,
        "final_portal": final_inspection_portal,
        "close_anchor": final_anchor,
        "exit_portal": final_inspection_portal,
    }
    for index, (station, display) in enumerate(
        zip(screen_stations, display_surfaces), start=1
    ):
        assets[f"screen_station_{index:02d}"] = station
        assets[f"screen_display_{index:02d}"] = display
    for index, joint in enumerate(robot_joints, start=1):
        assets[f"robot_joint_{index}"] = joint

    root_collection["sum_managed_collection"] = True
    root_collection["build_interface"] = "production.blender.modeling.build_models"
    root_collection["asset_count"] = 10
    return assets


__all__ = ["ModelParameters", "build_models"]
