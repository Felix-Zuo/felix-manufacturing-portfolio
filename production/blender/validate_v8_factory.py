"""Fail-fast validation for the V8 one-ring factory journey."""

from __future__ import annotations

import json
import math

import bpy
from mathutils import Vector


REQUIRED_VISIBLE_OBJECTS = (
    "RING_HERO_01",
    "SUM_ASSET_DFKI_MiR100_AGV07",
    "SUM_ASSET_KUKA_KR210_L150",
    "SUM_KUKA_KR210_PrecisionBearingGripper",
    "SUM_GrindingCell_CBN_ProfiledAbrasiveLayer",
    "SUM_GrindingCell_WorkpieceMagneticDrivePlate",
    "SUM_GrindingCell_SupportShoe_01_CarbideInsert",
    "SUM_GrindingCell_SupportShoe_02_CarbideInsert",
    "SUM_GrindingCell_RubberizedDriveRoller",
    "SUM_V8_OutfeedConnector_ContinuousCurvedBelt",
    "SUM_V8_Outfeed_ContinuousAirKnifeBelt",
    "SUM_V8_Outfeed_TrackedNestCarrier",
    "SUM_V8_Inspection_RotaryAirBearingAxis",
    "SUM_V8_Inspection_PrecisionRotaryPlatter",
    "SUM_V8_Inspection_RacewayProbe",
    "SUM_V8_Inspection_InternalRacewayStylus",
    "SUM_V8_Inspection_RubyProbeTip",
    "SUM_V8_QualityGantry_GripperJawCarrier_01",
    "SUM_V8_QualityGantry_GripperJawCarrier_02",
    "SUM_V8_QualityGantry_GripperJawCarrier_03",
    "SUM_V8_ScanGate_TrackingLine",
    "SUM_V8_Inspection_LaserTrace",
    "SUM_V8_FinalDoor_Left",
    "SUM_V8_FinalDoor_Right",
    "CIN_BlackHandoff",
)

REPLACED_PROCESS_PROXIES = (
    "SUM_GrindingCell_Workhead_Housing",
    "SUM_GrindingCell_WorkSpindle_Nose",
    "SUM_GrindingCell_ThreeJawChuck",
    "SUM_GrindingCell_Workholding_BackupFlange",
    "SUM_GrindingCell_GrindingSpindle_Housing",
    "SUM_GrindingCell_GrindingSpindle_Shaft",
    "SUM_GrindingCell_OuterRing_Workpiece",
    "SUM_Bearing_OuterRing",
    "SUM_KUKA_Gripper_HeldBearingRing_WIP",
)


def _world_position(scene: bpy.types.Scene, name: str, frame: int) -> Vector:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return bpy.data.objects[name].matrix_world.translation.copy()


def _ring_axis(scene: bpy.types.Scene, frame: int) -> Vector:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    ring = bpy.data.objects["RING_HERO_01"]
    return (ring.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()


def _parse_scene_json(scene: bpy.types.Scene, key: str, errors: list[str]) -> dict[str, object]:
    encoded = scene.get(key)
    if not isinstance(encoded, str):
        errors.append(f"scene is missing {key}")
        return {}
    try:
        result = json.loads(encoded)
    except json.JSONDecodeError as exc:
        errors.append(f"{key} is invalid JSON: {exc}")
        return {}
    if not isinstance(result, dict):
        errors.append(f"{key} must decode to an object")
        return {}
    return result


def main() -> None:
    scene = bpy.context.scene
    errors: list[str] = []
    report: dict[str, object] = {
        "ok": False,
        "object_count": len(bpy.data.objects),
    }

    missing = [name for name in REQUIRED_VISIBLE_OBJECTS if bpy.data.objects.get(name) is None]
    report["missing"] = missing
    if missing:
        errors.append("missing required objects: " + ", ".join(missing))

    hidden_required = [
        name
        for name in REQUIRED_VISIBLE_OBJECTS
        if (obj := bpy.data.objects.get(name)) is not None and obj.hide_render
    ]
    report["hidden_required"] = hidden_required
    if hidden_required:
        errors.append("required objects hidden from render: " + ", ".join(hidden_required))

    visible_proxies = [
        name
        for name in REPLACED_PROCESS_PROXIES
        if (obj := bpy.data.objects.get(name)) is not None and not obj.hide_render
    ]
    visible_proxies.extend(
        obj.name
        for obj in scene.objects
        if obj.name.startswith("SUM_GrindingCell_ChuckJaw_") and not obj.hide_render
    )
    report["visible_replaced_proxies"] = visible_proxies
    if visible_proxies:
        errors.append("obsolete process proxies remain visible: " + ", ".join(visible_proxies))

    outfeed_rollers = [
        obj.name
        for obj in scene.objects
        if "Outfeed" in obj.name and "Roller" in obj.name and not obj.hide_render
    ]
    report["visible_outfeed_rollers"] = outfeed_rollers
    if outfeed_rollers:
        errors.append("outfeed must use continuous belts, not exposed rollers")

    curved_belt = bpy.data.objects.get("SUM_V8_OutfeedConnector_ContinuousCurvedBelt")
    if curved_belt is not None:
        controls = curved_belt.get("path_control_points")
        try:
            normalized_controls = [
                [float(value) for value in point]
                for point in controls
            ]
        except (TypeError, ValueError):
            normalized_controls = []
        report["curved_belt_controls"] = normalized_controls
        if len(normalized_controls) != 4:
            errors.append("curved belt is missing four cubic Bezier controls")
        elif not (
            math.isclose(normalized_controls[0][0], normalized_controls[1][0], abs_tol=1.0e-6)
            and math.isclose(normalized_controls[2][0], normalized_controls[3][0], abs_tol=1.0e-6)
        ):
            errors.append("curved belt does not enter and leave tangent to the straight conveyors")
        if curved_belt.type != "MESH" or len(curved_belt.data.vertices) < 160:
            errors.append("curved belt mesh is too coarse for a smooth side-flex transition")

    world_up = Vector((0.0, 1.0, 0.0))
    ring_axes = {
        frame: round(abs(float(_ring_axis(scene, frame).dot(world_up))), 5)
        for frame in (498, 550, 660, 798)
    }
    report["ring_axis_alignment_to_world_up"] = ring_axes
    if ring_axes[498] > 0.15:
        errors.append("ring axis must remain horizontal during internal raceway grinding")
    for frame in (550, 660, 798):
        if ring_axes[frame] < 0.96:
            errors.append(f"ring must lie flat at frame {frame}")

    jaw_carriers = [
        obj
        for obj in scene.objects
        if obj.get("sum_part_role") == "quality_transfer_radial_jaw_carrier"
    ]
    report["quality_internal_jaw_count"] = len(jaw_carriers)
    if len(jaw_carriers) != 3:
        errors.append(f"quality transfer requires three internal expanding jaws, got {len(jaw_carriers)}")

    camera = scene.camera
    if camera is None:
        errors.append("scene has no active camera")
    else:
        backward_frames: list[int] = []
        previous_z: float | None = None
        for frame in range(scene.frame_start, scene.frame_end + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            current_z = float(camera.matrix_world.translation.z)
            if previous_z is not None and current_z >= previous_z - 1.0e-7:
                backward_frames.append(frame)
            previous_z = current_z
        report["camera_nonforward_frames"] = backward_frames[:12]
        if backward_frames:
            errors.append(f"camera does not advance continuously at frames {backward_frames[:12]}")

    cinematography_manifest = _parse_scene_json(scene, "cinematography_manifest", errors)
    story_manifest = _parse_scene_json(scene, "v8_story_animation_manifest", errors)
    report["magnetic_stop_frames"] = cinematography_manifest.get("magnetic_stop_frames")
    if cinematography_manifest.get("magnetic_stop_frames") != [132, 228, 474, 660]:
        errors.append("cinematography must expose exactly four project magnetic stops")
    if cinematography_manifest.get("black_handoff_frame") != 904:
        errors.append("black handoff must start at frame 904")
    if story_manifest.get("handoff_order") != [
        "AGV",
        "robot",
        "grinder",
        "outfeed",
        "inspection",
        "AGV",
    ]:
        errors.append("story handoff order is incomplete")

    expected_actions = (
        "SUM_ANIM_V8ScanLine",
        "SUM_ANIM_V8InspectionLaser",
        "SUM_ANIM_V8OutfeedNestCarrier",
        "SUM_ANIM_V8InspectionRotaryTable_01",
    )
    missing_actions = [name for name in expected_actions if bpy.data.actions.get(name) is None]
    report["missing_actions"] = missing_actions
    if missing_actions:
        errors.append("missing required story actions: " + ", ".join(missing_actions))

    if bpy.data.objects.get("SUM_V8_FinalDoor_Left") and bpy.data.objects.get("SUM_V8_FinalDoor_Right"):
        door_travel = {}
        for name in ("SUM_V8_FinalDoor_Left", "SUM_V8_FinalDoor_Right"):
            closed = _world_position(scene, name, 828)
            opened = _world_position(scene, name, 882)
            travel = float((opened - closed).length)
            door_travel[name] = round(travel, 4)
            if travel < 0.85:
                errors.append(f"{name} does not open far enough")
        report["door_travel_m"] = door_travel

    black = bpy.data.objects.get("CIN_BlackHandoff")
    if black is not None:
        scene.frame_set(904)
        bpy.context.view_layer.update()
        black_scale = min(float(value) for value in black.scale)
        report["black_handoff_min_scale"] = round(black_scale, 4)
        if black_scale < 0.99:
            errors.append("frame 904 does not fully cover the camera with black")

    if (scene.frame_start, scene.frame_end, scene.render.fps) != (1, 912, 24):
        errors.append(
            f"expected 1-912 at 24 fps, got {scene.frame_start}-{scene.frame_end} at {scene.render.fps}"
        )

    report["ok"] = not errors
    report["errors"] = errors
    print("V8_FACTORY_VALIDATION=" + json.dumps(report, ensure_ascii=True, separators=(",", ":")))
    if errors:
        raise RuntimeError("V8 factory validation failed")


if __name__ == "__main__":
    main()
