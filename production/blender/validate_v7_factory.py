"""Fail-fast validation for the V7 factory systems and finale handoff."""

from __future__ import annotations

import json

import bpy
from bpy_extras.object_utils import world_to_camera_view


REQUIRED_OBJECTS = (
    "SUM_Bearing_OuterRing",
    "SUM_KUKA_KR210_PrecisionBearingGripper",
    "SUM_GrindingCell_CBN_ProfiledAbrasiveLayer",
    "SUM_GrindingCell_SoftJaw_01_ContactPad",
    "SUM_GrindingCell_CoolantManifold",
    "SUM_V7_UtilityTray_L_LongitudinalFrame",
    "SUM_V7_Gantry_TwinLongitudinalRails",
    "SUM_V7_Gantry_MovingBridge",
    "SUM_V7_Gantry_ZAxisCarriage",
    "SUM_V7_Gantry_ThreeJawBearingGripper",
    "SUM_V7_Gantry_CarriedBearingOuterRing",
    "SUM_FPV_VFX_FinalGate_LeftLeaf",
    "SUM_FPV_VFX_FinalGate_RightLeaf",
    "SUM_FPV_VFX_FinalGate_BlackField",
)


def _world_position(scene: bpy.types.Scene, name: str, frame: int):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return bpy.data.objects[name].matrix_world.translation.copy()


def main() -> None:
    scene = bpy.context.scene
    camera = scene.camera
    errors: list[str] = []

    missing = [name for name in REQUIRED_OBJECTS if bpy.data.objects.get(name) is None]
    if missing:
        errors.append("missing required objects: " + ", ".join(missing))

    report: dict[str, object] = {
        "ok": False,
        "object_count": len(bpy.data.objects),
        "missing": missing,
    }

    if camera is None:
        errors.append("scene has no active camera")
    elif bpy.data.objects.get("SUM_Bearing_OuterRing") is not None:
        scene.frame_set(1)
        bpy.context.view_layer.update()
        bearing = bpy.data.objects["SUM_Bearing_OuterRing"]
        bearing_view = world_to_camera_view(scene, camera, bearing.matrix_world.translation)
        bearing_center = [round(float(bearing_view.x), 4), round(float(bearing_view.y), 4)]
        report["opening_bearing_center"] = bearing_center
        if not (0.18 <= bearing_view.x <= 0.82 and 0.18 <= bearing_view.y <= 0.82):
            errors.append(f"frame 1 bearing center is outside the hero guard: {bearing_center}")

    if bpy.data.objects.get("SUM_V7_Gantry_MovingBridge") is not None:
        bridge_start = _world_position(scene, "SUM_V7_Gantry_MovingBridge", 193)
        bridge_end = _world_position(scene, "SUM_V7_Gantry_MovingBridge", 245)
        bridge_travel = (bridge_end - bridge_start).length
        report["gantry_bridge_travel_m"] = round(bridge_travel, 4)
        if bridge_travel < 0.35:
            errors.append(f"gantry bridge travel is not visually meaningful: {bridge_travel:.3f} m")

    if bpy.data.objects.get("SUM_V7_Gantry_ZAxisCarriage") is not None:
        z_start = _world_position(scene, "SUM_V7_Gantry_ZAxisCarriage", 193)
        z_end = _world_position(scene, "SUM_V7_Gantry_ZAxisCarriage", 245)
        z_travel = (z_end - z_start).length
        report["gantry_z_axis_travel_m"] = round(z_travel, 4)
        if z_travel < 0.15:
            errors.append(f"gantry Z-axis travel is not visible: {z_travel:.3f} m")

    door_names = (
        "SUM_FPV_VFX_FinalGate_LeftLeaf",
        "SUM_FPV_VFX_FinalGate_RightLeaf",
    )
    if all(bpy.data.objects.get(name) is not None for name in door_names):
        door_travel = {}
        for name in door_names:
            closed = _world_position(scene, name, 853)
            opened = _world_position(scene, name, 895)
            door_travel[name] = round((opened - closed).length, 4)
            if (opened - closed).length < 1.5:
                errors.append(f"{name} does not open far enough")
        report["door_leaf_travel_m"] = door_travel

    black_field = bpy.data.objects.get("SUM_FPV_VFX_FinalGate_BlackField")
    if black_field is not None:
        material = black_field.active_material
        if material is None:
            errors.append("final black field has no material")
        else:
            rgb = [round(float(value), 5) for value in material.diffuse_color[:3]]
            report["final_black_field_rgb"] = rgb
            if max(rgb) > 0.02:
                errors.append(f"final field is not near black: {rgb}")
            if float(material.get("maximum_emission_strength", 1.0)) > 0.001:
                errors.append("final black field still permits emission")

    spill = bpy.data.objects.get("SUM_FPV_VFX_FinalGate_BlackFieldNoSpill")
    if spill is not None and hasattr(spill.data, "energy"):
        scene.frame_set(901)
        bpy.context.view_layer.update()
        spill_energy = round(float(spill.data.energy), 5)
        report["final_black_field_spill_w"] = spill_energy
        if spill_energy > 0.001:
            errors.append(f"final black field emits spill light: {spill_energy} W")

    if tuple((scene.frame_start, scene.frame_end, scene.render.fps)) != (1, 912, 24):
        errors.append(
            f"expected 1-912 at 24 fps, got {scene.frame_start}-{scene.frame_end} at {scene.render.fps}"
        )

    report["ok"] = not errors
    report["errors"] = errors
    print("V7_FACTORY_VALIDATION=" + json.dumps(report, ensure_ascii=True, separators=(",", ":")))
    if errors:
        raise RuntimeError("V7 factory validation failed")


if __name__ == "__main__":
    main()
