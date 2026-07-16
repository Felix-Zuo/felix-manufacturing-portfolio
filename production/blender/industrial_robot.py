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
MODEL_COLLECTION = "SUM_MODEL_KUKA_KR210"

# Tool-local dimensions before the uniform design scale is applied.  The
# resulting payload is approximately 228 mm OD x 52 mm wide in world space.
GRIPPER_SCALE = 0.94
WORKPIECE_OUTER_RADIUS = 0.121
WORKPIECE_INNER_RADIUS = 0.077
WORKPIECE_WIDTH = 0.056
GRIP_PAD_INNER_FACE = 0.122

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


def _reset_model_collection(
    parent: bpy.types.Collection,
) -> bpy.types.Collection:
    """Replace this generated asset collection without accumulating datablocks."""

    existing = bpy.data.collections.get(MODEL_COLLECTION)
    if existing is not None:
        owned_data = [
            obj.data
            for obj in existing.all_objects
            if getattr(obj, "data", None) is not None
        ]
        modeling._remove_collection_tree(existing)
        for datablock in owned_data:
            if datablock.users != 0:
                continue
            if isinstance(datablock, bpy.types.Mesh):
                bpy.data.meshes.remove(datablock)
            elif isinstance(datablock, bpy.types.Curve):
                bpy.data.curves.remove(datablock)
    return modeling._child_collection(parent, MODEL_COLLECTION)


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
    def hose(
        name: str,
        points: list[tuple[float, float, float]],
        radius: float,
        parent: bpy.types.Object,
        role: str,
    ) -> bpy.types.Object:
        result = modeling._bezier_tube(
            name,
            points,
            radius,
            collection,
            parent=parent,
            material=materials["rubber"],
            role=role,
            resolution=12,
        )
        result["lookdev_role"] = "rubber"
        result["dress_pack_function"] = "robot power, servo brake, and tool I/O"
        return result

    hose(
        "SUM_KUKA_KR210_BaseDressPack",
        [
            (-0.30, -0.30, 0.38),
            (-0.35, -0.25, 0.43),
            (-0.24, -0.14, 0.47),
            (-0.08, -0.04, 0.48),
            (-0.00262, 0.00098, 0.45099),
        ],
        0.038,
        root,
        "industrial_robot_base_dress_pack",
    )
    hose(
        "SUM_KUKA_KR210_ShoulderDressPack",
        [
            (0.00, 0.00, 0.12),
            (0.05, -0.08, 0.21),
            (0.16, -0.16, 0.34),
            (0.29, -0.17, 0.43),
            (0.35277, -0.13998, 0.41920),
        ],
        0.035,
        joints[0],
        "industrial_robot_shoulder_dress_pack",
    )
    hose(
        "SUM_KUKA_KR210_UpperArmDressPack",
        [
            (0.00, -0.10250, 0.00),
            (-0.14, -0.17, 0.22),
            (-0.18, -0.21, 0.58),
            (-0.15, -0.24, 0.94),
            (-0.05, -0.24, 1.13),
            (0.00, -0.23, 1.24990),
        ],
        0.032,
        joints[1],
        "industrial_robot_upper_arm_dress_pack",
    )
    hose(
        "SUM_KUKA_KR210_ForearmDressPack",
        [
            (0.00, -0.08250, 0.00),
            (0.04, -0.24, 0.16),
            (0.36, -0.28, 0.33),
            (0.65, -0.16, 0.26),
            (0.87, 0.02, 0.10),
            (0.95795, 0.184, -0.05506),
        ],
        0.029,
        joints[2],
        "industrial_robot_forearm_dress_pack",
    )
    hose(
        "SUM_KUKA_KR210_WristDressPack",
        [
            (0.00, 0.00, 0.00),
            (0.08, -0.16, 0.14),
            (0.27, -0.16, 0.13),
            (0.46, -0.10, 0.07),
            (0.542, -0.05, 0.00),
        ],
        0.024,
        joints[3],
        "industrial_robot_wrist_dress_pack",
    )
    hose(
        "SUM_KUKA_KR210_A5ServiceLoop",
        [
            (0.00, -0.05, 0.00),
            (0.04, -0.13, 0.11),
            (0.13, -0.15, 0.09),
            (0.20, -0.08, 0.03),
            (0.2025, 0.00, 0.00),
        ],
        0.021,
        joints[4],
        "industrial_robot_a5_service_loop",
    )
    hose(
        "SUM_KUKA_KR210_ToolIOUmbilical",
        [
            (0.01, 0.00, 0.00),
            (0.02, -0.075, 0.070),
            (0.05, -0.105, 0.080),
            (0.0563, -0.0987, 0.0705),
        ],
        0.016,
        joints[5],
        "industrial_robot_tool_io_umbilical",
    )

    clamp_specs = (
        (
            "SUM_KUKA_KR210_UpperArmDressPackClamps",
            joints[1],
            [
                ((-0.17, -0.205, 0.38), (0.095, 0.070, 0.045)),
                ((-0.17, -0.225, 0.73), (0.095, 0.070, 0.045)),
                ((-0.11, -0.235, 1.04), (0.095, 0.070, 0.045)),
            ],
        ),
        (
            "SUM_KUKA_KR210_ForearmDressPackClamps",
            joints[2],
            [
                ((0.20, -0.285, 0.29), (0.055, 0.090, 0.080)),
                ((0.49, -0.235, 0.31), (0.055, 0.090, 0.080)),
                ((0.76, -0.080, 0.19), (0.055, 0.090, 0.080)),
            ],
        ),
        (
            "SUM_KUKA_KR210_WristDressPackClamps",
            joints[3],
            [
                ((0.18, -0.155, 0.13), (0.045, 0.075, 0.065)),
                ((0.39, -0.125, 0.09), (0.045, 0.075, 0.065)),
            ],
        ),
    )
    for name, parent, boxes in clamp_specs:
        clamp_obj = modeling._box_array(
            name,
            boxes,
            collection,
            parent=parent,
            material=materials["black_oxide"],
            bevel=0.006,
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
    if WORKPIECE_OUTER_RADIUS >= GRIP_PAD_INNER_FACE:
        raise ValueError("bearing workpiece must clear both compliant pads")
    tool.scale = (GRIPPER_SCALE,) * 3
    tool["sum_asset_type"] = "servo_parallel_bearing_transfer_gripper"
    tool["design_scale"] = "production-scale KR210 bearing transfer end effector"
    tool["rated_payload_kg"] = 18.0

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
    faceplate = modeling._box(
        "SUM_KUKA_Gripper_ServoFaceplate",
        (0.035, 0.28, 0.20),
        collection,
        location=(0.315, 0.0, 0.0),
        parent=tool,
        material=materials["robot_paint"],
        bevel=0.010,
        role="servo_gripper_actuator_faceplate",
    )
    faceplate["lookdev_role"] = "powder_coat"
    rail = modeling._box(
        "SUM_KUKA_Gripper_CrossRail",
        (0.11, 0.58, 0.11),
        collection,
        location=(0.35, 0.0, 0.0),
        parent=tool,
        material=materials["brushed_steel"],
        bevel=0.012,
        role="precision_gripper_cross_slide",
    )
    rail["lookdev_role"] = "brushed_metal"

    leadscrew = modeling._cylinder_between(
        "SUM_KUKA_Gripper_ServoLeadscrew",
        (0.405, -0.245, 0.0),
        (0.405, 0.245, 0.0),
        0.018,
        collection,
        parent=tool,
        material=materials["machined_steel"],
        segments=40,
        bevel=0.002,
        role="servo_gripper_ground_ball_screw",
    )
    leadscrew["lookdev_role"] = "brushed_metal"
    leadscrew["mechanism"] = "opposed-thread synchronized parallel jaws"
    nut_block = modeling._box(
        "SUM_KUKA_Gripper_CentralBallNutHousing",
        (0.11, 0.10, 0.10),
        collection,
        location=(0.405, 0.0, 0.0),
        parent=tool,
        material=materials["black_oxide"],
        bevel=0.015,
        role="servo_gripper_ball_nut_housing",
    )
    nut_block["lookdev_role"] = "dark_metal"

    for z in (-0.052, 0.052):
        guide = modeling._cylinder_between(
            f"SUM_KUKA_Gripper_LinearGuide_{'Lower' if z < 0 else 'Upper'}",
            (0.405, -0.245, z),
            (0.405, 0.245, z),
            0.012,
            collection,
            parent=tool,
            material=materials["machined_steel"],
            segments=32,
            bevel=0.002,
            role="servo_gripper_linear_guide_rod",
        )
        guide["lookdev_role"] = "brushed_metal"

    for side in (-1.0, 1.0):
        suffix = "L" if side < 0 else "R"
        carrier = modeling._box(
            f"SUM_KUKA_Gripper_JawCarrier_{suffix}",
            (0.13, 0.13, 0.19),
            collection,
            location=(0.405, side * 0.21, 0.0),
            parent=tool,
            material=materials["machined_steel"],
            bevel=0.016,
            role="servo_parallel_gripper_jaw_carrier",
        )
        carrier["lookdev_role"] = "brushed_metal"
        finger = modeling._box(
            f"SUM_KUKA_Gripper_Finger_{suffix}",
            (0.26, 0.080, 0.125),
            collection,
            location=(0.525, side * 0.185, 0.0),
            parent=tool,
            material=materials["machined_steel"],
            bevel=0.014,
            role="servo_parallel_gripper_replaceable_finger",
        )
        finger["lookdev_role"] = "brushed_metal"
        pad = modeling._box(
            f"SUM_KUKA_Gripper_CompliantPad_{suffix}",
            (0.19, 0.044, 0.105),
            collection,
            location=(0.55, side * (GRIP_PAD_INNER_FACE + 0.022), 0.0),
            parent=tool,
            material=materials["rubber"],
            bevel=0.010,
            role="replaceable_nonmarking_bearing_grip_pad",
        )
        pad["lookdev_role"] = "rubber"
        for fastener_index, x in enumerate((0.50, 0.55, 0.60), start=1):
            bolt_y = side * (GRIP_PAD_INNER_FACE + 0.046)
            pad_fastener = modeling._cylinder_between(
                f"SUM_KUKA_Gripper_PadFastener_{suffix}_{fastener_index:02d}",
                (x, bolt_y - side * 0.010, -0.025),
                (x, bolt_y + side * 0.010, -0.025),
                0.010,
                collection,
                parent=tool,
                material=materials["machined_steel"],
                segments=6,
                bevel=0.001,
                role="replaceable_gripper_pad_fastener",
            )
            pad_fastener["lookdev_role"] = "brushed_metal"

    workpiece = modeling._annular_prism(
        "SUM_KUKA_Gripper_HeldBearingRing_WIP",
        WORKPIECE_OUTER_RADIUS,
        WORKPIECE_INNER_RADIUS,
        WORKPIECE_WIDTH,
        collection,
        location=(0.55, 0.0, 0.0),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=tool,
        material=materials["machined_steel"],
        segments=96,
        bevel=0.003,
        role="robot_held_in_process_bearing_outer_ring",
    )
    workpiece["lookdev_role"] = "brushed_metal"
    workpiece["manufacturing_state"] = "turned and heat-treated, awaiting finish grind"
    workpiece["nominal_outer_diameter_mm"] = 228
    workpiece["nominal_bore_diameter_mm"] = 145
    workpiece["nominal_width_mm"] = 52
    workpiece["radial_pad_clearance_mm"] = round(
        (GRIP_PAD_INNER_FACE - WORKPIECE_OUTER_RADIUS)
        * GRIPPER_SCALE
        * 1000.0,
        2,
    )
    raceway_witness = modeling._torus(
        "SUM_KUKA_Gripper_HeldBearingRing_RacewayWitness",
        0.097,
        0.0035,
        collection,
        location=(0.579, 0.0, 0.0),
        rotation=(0.0, math.pi * 0.5, 0.0),
        parent=tool,
        material=materials["brushed_steel"],
        major_segments=72,
        minor_segments=10,
        role="in_process_bearing_raceway_witness",
    )
    raceway_witness["lookdev_role"] = "brushed_metal"
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
            (0.02, -0.105, 0.075),
            (0.09, -0.145, 0.115),
            (0.18, -0.185, 0.105),
            (0.22, -0.205, 0.055),
        ],
        0.014,
        collection,
        parent=tool,
        material=materials["rubber"],
        role="gripper_power_and_sensor_cable",
        resolution=8,
    )
    cable["lookdev_role"] = "rubber"
    gland = modeling._cylinder_between(
        "SUM_KUKA_Gripper_ServiceCableGland",
        (0.22, -0.170, 0.055),
        (0.22, -0.205, 0.055),
        0.018,
        collection,
        parent=tool,
        material=materials["black_oxide"],
        segments=24,
        bevel=0.002,
        role="gripper_service_cable_strain_relief",
    )
    gland["lookdev_role"] = "dark_metal"
    tool["held_payload"] = workpiece.name
    tool["grip_strategy"] = "external-diameter parallel grip with compliant pads"
    return tool


def _build_base_service_interfaces(
    root: bpy.types.Object,
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
) -> dict[str, Any]:
    """Build credible robot anchoring and cell-side service connections."""

    grout_pad = modeling._box(
        "SUM_KUKA_KR210_PrecisionGroutPad",
        (1.30, 1.30, 0.055),
        collection,
        location=(0.0, 0.0, 0.028),
        parent=root,
        material=materials["fixture"],
        bevel=0.018,
        role="robot_precision_nonshrink_grout_pad",
    )
    grout_pad["lookdev_role"] = "floor"
    base_plate = modeling._cylinder(
        "SUM_KUKA_KR210_AnchorBasePlate",
        0.58,
        0.080,
        collection,
        location=(0.0, 0.0, 0.095),
        parent=root,
        material=materials["black_oxide"],
        segments=72,
        bevel=0.012,
        role="robot_machined_anchor_base_plate",
    )
    base_plate["lookdev_role"] = "dark_metal"
    anchors = modeling._add_bolt_circle(
        "SUM_KUKA_KR210_BaseAnchor",
        (0.0, 0.0, 0.145),
        (0.0, 0.0, 1.0),
        0.49,
        0.026,
        0.060,
        12,
        collection,
        parent=root,
        material=materials["machined_steel"],
    )
    for anchor in anchors:
        anchor["lookdev_role"] = "brushed_metal"
        anchor["fastener_spec"] = "preloaded robot base anchor with hardened washer"

    service_box = modeling._box(
        "SUM_KUKA_KR210_BaseServiceJunction",
        (0.32, 0.24, 0.38),
        collection,
        location=(-0.61, -0.36, 0.31),
        parent=root,
        material=materials["paint_graphite"],
        bevel=0.028,
        role="robot_base_power_io_service_junction",
    )
    service_box["lookdev_role"] = "powder_coat"
    service_box["interfaces"] = "motor power, resolver, safety I/O, tool air"

    connectors = []
    for index, (y, radius) in enumerate(((-0.425, 0.030), (-0.355, 0.026), (-0.285, 0.022)), start=1):
        connector = modeling._cylinder_between(
            f"SUM_KUKA_KR210_BaseServiceConnector_{index:02d}",
            (-0.785, y, 0.25),
            (-0.825, y, 0.25),
            radius,
            collection,
            parent=root,
            material=materials["black_oxide"],
            segments=24,
            bevel=0.003,
            role="sealed_robot_service_connector",
        )
        connector["lookdev_role"] = "dark_metal"
        connectors.append(connector)

    service_loom = modeling._bezier_tube(
        "SUM_KUKA_KR210_BaseServiceLoom",
        [
            (-0.78, -0.36, 0.25),
            (-0.68, -0.28, 0.21),
            (-0.45, -0.22, 0.19),
            (-0.24, -0.15, 0.22),
            (-0.08, -0.05, 0.31),
        ],
        0.032,
        collection,
        parent=root,
        material=materials["rubber"],
        role="robot_base_power_and_feedback_loom",
        resolution=10,
    )
    service_loom["lookdev_role"] = "rubber"

    regulator_body = modeling._cylinder(
        "SUM_KUKA_KR210_ToolAirRegulatorBody",
        0.052,
        0.17,
        collection,
        location=(-0.52, -0.49, 0.55),
        parent=root,
        material=materials["brushed_steel"],
        segments=32,
        bevel=0.006,
        role="robot_tool_air_filter_regulator",
    )
    regulator_body["lookdev_role"] = "brushed_metal"
    bowl = modeling._cylinder(
        "SUM_KUKA_KR210_ToolAirFilterBowl",
        0.045,
        0.12,
        collection,
        location=(-0.52, -0.49, 0.405),
        parent=root,
        material=materials["safety_glass"],
        segments=32,
        bevel=0.006,
        role="robot_tool_air_filter_bowl",
    )
    bowl["lookdev_role"] = "safety_glass"
    air_line = modeling._bezier_tube(
        "SUM_KUKA_KR210_BaseToolAirLine",
        [
            (-0.52, -0.49, 0.64),
            (-0.43, -0.43, 0.69),
            (-0.31, -0.34, 0.62),
            (-0.22, -0.25, 0.52),
        ],
        0.014,
        collection,
        parent=root,
        material=materials["rubber"],
        role="robot_filtered_tool_air_line",
        resolution=8,
    )
    air_line["lookdev_role"] = "rubber"

    return {
        "grout_pad": grout_pad,
        "base_plate": base_plate,
        "anchors": anchors,
        "service_box": service_box,
        "connectors": connectors,
        "regulator": regulator_body,
    }


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
    collection = _reset_model_collection(root_collection)
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
    base_interfaces = _build_base_service_interfaces(root, collection, materials)

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
    assets["kuka_base_interfaces"] = base_interfaces
    assets["kuka_visual_links"] = links
    assets.setdefault("anchors", {})["robot_handoff"] = tcp
    assets["anchors"]["robot"] = tcp
    assets.setdefault("travel_anchors", {})["robot"] = tcp
    assets.setdefault("collections", {})["robot"] = collection
    bpy.context.view_layer.update()
    return assets
