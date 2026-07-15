"""Import and rig the ROS-Industrial KUKA KR 210 L150 visual meshes."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import bpy
from mathutils import Matrix

import modeling


ROOT = Path(__file__).resolve().parents[2]
VENDOR_ROOT = ROOT / "production" / "vendor" / "ros-industrial-kuka-kr210"
VISUAL_ROOT = VENDOR_ROOT / "meshes" / "visual"
UPSTREAM_COMMIT = "8d9292b04a22628b1b78d989e2ddd3abb913bf92"

JOINTS = (
    ("A1", (-0.00262, 0.00097586, 0.33099), (0.0, 0.0, 1.0)),
    ("A2", (0.35277, -0.037476, 0.4192), (0.0, 1.0, 0.0)),
    ("A3", (-0.000098483, -0.1475, 1.2499), (0.0, 1.0, 0.0)),
    ("A4", (0.95795, 0.184, -0.055059), (1.0, 0.0, 0.0)),
    ("A5", (0.542, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ("A6", (0.1925, 0.0, 0.0), (1.0, 0.0, 0.0)),
)

VISUAL_ROTATIONS = {
    "base_link": (-math.pi * 0.5, 0.0, 0.0),
    "link_1": (0.0, 0.0, 0.0),
    "link_2": (-math.pi * 0.5, 0.0, 0.0),
    "link_3": (-math.pi * 0.5, 0.0, 0.0),
    "link_4": (-math.pi * 0.5, 0.0, 0.0),
    "link_5": (-math.pi * 0.5, 0.0, 0.0),
    "link_6": (0.0, 0.0, 0.0),
}


def _descendants(root: bpy.types.Object) -> list[bpy.types.Object]:
    return [
        obj
        for obj in bpy.context.scene.objects
        if any(parent is root for parent in _parent_chain(obj))
    ]


def _parent_chain(obj: bpy.types.Object):
    cursor: bpy.types.Object | None = obj
    while cursor is not None:
        yield cursor
        cursor = cursor.parent


def _exclude_proxy_robot(assets: dict[str, Any]) -> None:
    proxy = assets.get("robot_arm_6axis")
    if not isinstance(proxy, bpy.types.Object):
        return
    for obj in _descendants(proxy):
        obj.hide_render = True
        obj["sum_export_exclude"] = True
        obj["sum_replaced_by"] = "KUKA KR 210 L150"


def _move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for current in tuple(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def _import_link_mesh(
    link_name: str,
    parent: bpy.types.Object,
    collection: bpy.types.Collection,
    material: bpy.types.Material,
) -> bpy.types.Object:
    path = VISUAL_ROOT / f"{link_name}.dae"
    if not path.exists():
        raise FileNotFoundError(f"Missing ROS-Industrial visual mesh: {path}")

    before_objects = set(bpy.data.objects)
    before_materials = set(bpy.data.materials)
    result = bpy.ops.wm.collada_import(filepath=str(path))
    if "FINISHED" not in result:
        raise RuntimeError(f"Collada import failed for {path.name}: {result}")

    imported = [obj for obj in bpy.data.objects if obj not in before_objects]
    meshes = [obj for obj in imported if obj.type == "MESH"]
    cleanup_objects = [obj for obj in imported if obj.type != "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh objects were imported from {path.name}")

    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
        _move_to_collection(obj, collection)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    joined = meshes[0]
    joined.name = f"SUM_KUKA_KR210_{link_name}_Visual"
    joined.data.name = f"{joined.name}_Mesh"

    local_matrix = joined.matrix_world.copy()
    joined.parent = parent
    joined.matrix_parent_inverse = Matrix.Identity(4)
    joined.matrix_basis = local_matrix
    joined.data.materials.clear()
    joined.data.materials.append(material)
    for polygon in joined.data.polygons:
        polygon.use_smooth = True
    joined["lookdev_role"] = "architecture"
    joined["sum_part_role"] = "licensed_industrial_robot_visual_link"
    joined["source_package"] = "ros-industrial/kuka_experimental:kuka_kr210_support"
    joined["source_commit"] = UPSTREAM_COMMIT
    joined["source_link"] = link_name
    joined["triangle_count"] = sum(max(len(poly.vertices) - 2, 1) for poly in joined.data.polygons)

    for obj in cleanup_objects:
        try:
            existing = bpy.data.objects.get(obj.name)
        except ReferenceError:
            existing = None
        if existing is obj:
            bpy.data.objects.remove(existing, do_unlink=True)
    for imported_material in set(bpy.data.materials) - before_materials:
        if imported_material.users == 0:
            bpy.data.materials.remove(imported_material)
    bpy.ops.object.select_all(action="DESELECT")
    return joined


def _build_joint_details(
    joint: bpy.types.Object,
    index: int,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    axis = JOINTS[index - 1][2]
    if axis[0]:
        rotation = (0.0, math.pi * 0.5, 0.0)
    elif axis[1]:
        rotation = (math.pi * 0.5, 0.0, 0.0)
    else:
        rotation = (0.0, 0.0, 0.0)
    radius = 0.23 if index <= 3 else 0.13 if index <= 5 else 0.095
    depth = 0.055 if index <= 3 else 0.038
    collar = modeling._cylinder(
        f"SUM_KUKA_KR210_A{index}_BlackJointCollar",
        radius,
        depth,
        collection,
        rotation=rotation,
        parent=joint,
        material=materials["black_oxide"],
        segments=48,
        bevel=0.006,
        role="industrial_robot_joint_service_collar",
    )
    collar["lookdev_role"] = "dark_metal"
    collar["joint_index"] = index

    bolt_centers = []
    bolt_radius = radius * 0.72
    for bolt_index in range(8):
        angle = math.tau * bolt_index / 8.0
        if axis[0]:
            center = (0.032, math.cos(angle) * bolt_radius, math.sin(angle) * bolt_radius)
        elif axis[1]:
            center = (math.cos(angle) * bolt_radius, 0.032, math.sin(angle) * bolt_radius)
        else:
            center = (math.cos(angle) * bolt_radius, math.sin(angle) * bolt_radius, 0.032)
        bolt_centers.append(center)
    bolts = modeling._prism_array(
        f"SUM_KUKA_KR210_A{index}_CollarFasteners",
        bolt_centers,
        radius * 0.055,
        0.020,
        8,
        collection,
        parent=joint,
        material=materials["machined_steel"],
        bevel=0.0015,
        role="industrial_robot_joint_fasteners",
    )
    bolts["lookdev_role"] = "brushed_metal"


def _build_dress_pack(
    root: bpy.types.Object,
    joints: list[bpy.types.Object],
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> None:
    base_hose = modeling._bezier_tube(
        "SUM_KUKA_KR210_BaseDressPack",
        [
            (-0.30, -0.30, 0.42),
            (-0.42, -0.28, 0.78),
            (-0.36, -0.18, 1.12),
            (-0.20, -0.10, 1.46),
        ],
        0.038,
        collection,
        parent=root,
        material=materials["rubber"],
        role="industrial_robot_base_dress_pack",
        resolution=10,
    )
    base_hose["lookdev_role"] = "rubber"

    upper_hose = modeling._bezier_tube(
        "SUM_KUKA_KR210_UpperArmDressPack",
        [
            (0.04, -0.24, 0.10),
            (0.22, -0.30, 0.30),
            (0.48, -0.25, 0.38),
            (0.76, -0.16, 0.28),
            (0.94, -0.10, 0.12),
        ],
        0.028,
        collection,
        parent=joints[2],
        material=materials["rubber"],
        role="industrial_robot_forearm_dress_pack",
        resolution=10,
    )
    upper_hose["lookdev_role"] = "rubber"

    clamps = []
    for x in (0.18, 0.48, 0.78):
        clamps.append(((x, -0.22, 0.22), (0.055, 0.10, 0.16)))
    clamp_obj = modeling._box_array(
        "SUM_KUKA_KR210_DressPackClamps",
        clamps,
        collection,
        parent=joints[2],
        material=materials["black_oxide"],
        bevel=0.008,
        role="industrial_robot_dress_pack_clamps",
    )
    clamp_obj["lookdev_role"] = "dark_metal"


def _build_end_effector(
    tcp: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    tool = modeling._empty(
        "SUM_KUKA_KR210_PrecisionBearingGripper",
        collection,
        parent=tcp,
        display_size=0.10,
    )
    tool.scale = (0.78, 0.78, 0.78)
    tool["sum_asset_type"] = "servo_parallel_bearing_transfer_gripper"
    tool["design_scale"] = "compact 78 percent production end effector"

    flange = modeling._cylinder_between(
        "SUM_KUKA_Gripper_ISOFlange",
        (0.0, 0.0, 0.0),
        (0.09, 0.0, 0.0),
        0.105,
        collection,
        parent=tool,
        material=materials["machined_steel"],
        segments=48,
        bevel=0.004,
        role="robot_iso_tool_flange_adapter",
    )
    flange["lookdev_role"] = "brushed_metal"
    housing = modeling._box(
        "SUM_KUKA_Gripper_ServoHousing",
        (0.24, 0.34, 0.24),
        collection,
        location=(0.19, 0.0, 0.0),
        parent=tool,
        material=materials["paint_graphite"],
        bevel=0.035,
        role="sealed_servo_gripper_housing",
    )
    housing["lookdev_role"] = "powder_coat"
    rail = modeling._box(
        "SUM_KUKA_Gripper_CrossRail",
        (0.10, 0.54, 0.10),
        collection,
        location=(0.33, 0.0, 0.0),
        parent=tool,
        material=materials["brushed_steel"],
        bevel=0.012,
        role="precision_gripper_cross_slide",
    )
    rail["lookdev_role"] = "brushed_metal"

    for side in (-1.0, 1.0):
        jaw = modeling._box(
            f"SUM_KUKA_Gripper_Jaw_{'L' if side < 0 else 'R'}",
            (0.30, 0.11, 0.18),
            collection,
            location=(0.43, side * 0.20, 0.0),
            parent=tool,
            material=materials["machined_steel"],
            bevel=0.020,
            role="servo_parallel_gripper_jaw",
        )
        jaw["lookdev_role"] = "brushed_metal"
        pad = modeling._box(
            f"SUM_KUKA_Gripper_CompliantPad_{'L' if side < 0 else 'R'}",
            (0.16, 0.045, 0.14),
            collection,
            location=(0.50, side * 0.137, 0.0),
            parent=tool,
            material=materials["rubber"],
            bevel=0.014,
            role="replaceable_nonmarking_bearing_grip_pad",
        )
        pad["lookdev_role"] = "rubber"
    sensor = modeling._box(
        "SUM_KUKA_Gripper_PositionSensor",
        (0.11, 0.08, 0.075),
        collection,
        location=(0.22, -0.21, 0.02),
        parent=tool,
        material=materials["screen_frame"],
        bevel=0.012,
        role="gripper_jaw_position_sensor",
    )
    sensor["lookdev_role"] = "screen_glass"
    cable = modeling._bezier_tube(
        "SUM_KUKA_Gripper_ServiceCable",
        [
            (0.02, -0.11, 0.08),
            (0.10, -0.17, 0.12),
            (0.22, -0.19, 0.10),
        ],
        0.012,
        collection,
        parent=tool,
        material=materials["rubber"],
        role="gripper_power_and_sensor_cable",
        resolution=8,
    )
    cable["lookdev_role"] = "rubber"
    return tool


def replace_robot(assets: dict[str, Any]) -> dict[str, Any]:
    """Replace the procedural proxy with licensed KR 210 link geometry."""

    root_collection = assets.get("root_collection")
    layout_root = assets.get("layout_root")
    materials = assets.get("placeholder_materials")
    params = assets.get("parameters")
    if not isinstance(root_collection, bpy.types.Collection):
        raise TypeError("assets must provide root_collection")
    if not isinstance(layout_root, bpy.types.Object):
        raise TypeError("assets must provide layout_root")
    if not isinstance(materials, dict):
        raise TypeError("assets must provide placeholder_materials")
    if params is None:
        raise TypeError("assets must provide parameters")

    for link_name in ("base_link", "link_1", "link_2", "link_3", "link_4", "link_5", "link_6"):
        if not (VISUAL_ROOT / f"{link_name}.dae").exists():
            raise FileNotFoundError(f"Incomplete KUKA source package: {link_name}.dae")

    _exclude_proxy_robot(assets)
    collection = modeling._child_collection(root_collection, "SUM_MODEL_KUKA_KR210")
    root = modeling._empty(
        "SUM_ASSET_KUKA_KR210_L150",
        collection,
        location=tuple(params.robot_location),
        parent=layout_root,
        display_size=0.42,
    )
    root["sum_asset_type"] = "licensed_six_axis_industrial_robot"
    root["manufacturer_model"] = "KUKA KR 210 L150"
    root["source_repository"] = "https://github.com/ros-industrial/kuka_experimental"
    root["source_commit"] = UPSTREAM_COMMIT
    root["kinematic_source"] = "kuka_kr210_support/urdf/kr210l150.urdf"
    base_visual = modeling._empty(
        "SUM_KUKA_KR210_base_link_VisualFrame",
        collection,
        rotation=VISUAL_ROTATIONS["base_link"],
        parent=root,
        display_size=0.08,
    )
    links = [
        _import_link_mesh(
            "base_link", base_visual, collection, materials["factory_wall"]
        )
    ]

    joints: list[bpy.types.Object] = []
    parent = root
    for index, (label, location, axis) in enumerate(JOINTS, start=1):
        joint = modeling._joint_empty(
            f"SUM_KUKA_KR210_J{index}_{label}_Axis",
            location,
            axis,
            collection,
            parent,
            index,
        )
        joint["manufacturer_joint"] = label
        joint["kinematic_source"] = "ROS-Industrial URDF"
        joints.append(joint)
        visual_name = f"link_{index}"
        visual_frame = modeling._empty(
            f"SUM_KUKA_KR210_{visual_name}_VisualFrame",
            collection,
            rotation=VISUAL_ROTATIONS[visual_name],
            parent=joint,
            display_size=0.07,
        )
        links.append(
            _import_link_mesh(
                visual_name, visual_frame, collection, materials["factory_wall"]
            )
        )
        _build_joint_details(joint, index, collection, materials)
        parent = joint

    tcp = modeling._empty(
        "SUM_KUKA_KR210_Tool0",
        collection,
        location=(0.0375, 0.0, -0.00023924),
        parent=joints[-1],
        display_size=0.08,
    )
    tcp["sum_part_role"] = "robot_tcp"
    gripper = _build_end_effector(tcp, collection, materials)
    _build_dress_pack(root, joints, collection, materials)

    triangle_count = sum(int(link.get("triangle_count", 0)) for link in links)
    root["visual_mesh_triangles"] = triangle_count
    root["link_count"] = 7
    root["joint_count"] = 6
    root["foreground_asset_gate"] = "licensed geometry, URDF pivots, custom gripper"

    assets["robot_arm_6axis"] = root
    assets["robot_joints"] = joints
    assets["robot_tcp"] = tcp
    assets["robot_handoff"] = tcp
    assets["handoff_anchor"] = tcp
    assets["mechanical_arm_handoff"] = tcp
    assets["kuka_gripper"] = gripper
    assets["kuka_visual_links"] = links
    assets.setdefault("anchors", {})["robot_handoff"] = tcp
    assets["anchors"]["robot"] = tcp
    assets.setdefault("travel_anchors", {})["robot"] = tcp
    assets.setdefault("collections", {})["robot"] = collection
    bpy.context.view_layer.update()
    return assets
