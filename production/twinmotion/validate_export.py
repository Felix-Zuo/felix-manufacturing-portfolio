"""Validate the Twinmotion GLB mechanical core inside a clean Blender scene."""

from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
IMPORT_DIR = ROOT / "production" / "twinmotion" / "import"
CORE_GLB = IMPORT_DIR / "felix-v5-mechanical-core.glb"

REQUIRED_ACTIONS = {
    "SUM_ANIM_BearingInspection_Portable",
    "SUM_ANIM_GrindingWheel_Portable",
    "SUM_ANIM_GrindingWorkpiece_Portable",
    "SUM_ANIM_RobotJ1",
    "SUM_ANIM_RobotJ2",
    "SUM_ANIM_RobotJ3",
    "SUM_ANIM_RobotJ4",
    "SUM_ANIM_RobotJ5",
    "SUM_ANIM_RobotJ6",
}


def main() -> None:
    if not CORE_GLB.exists():
        raise FileNotFoundError(f"Missing export: {CORE_GLB}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(CORE_GLB))

    object_count = len(bpy.data.objects)
    material_count = len(bpy.data.materials)
    actions = {action.name for action in bpy.data.actions}
    missing_actions = REQUIRED_ACTIONS - actions

    mesh_corners = [
        obj.matrix_world @ Vector(corner)
        for obj in bpy.data.objects
        if obj.type == "MESH"
        for corner in obj.bound_box
    ]
    minimum = Vector(min(point[i] for point in mesh_corners) for i in range(3))
    maximum = Vector(max(point[i] for point in mesh_corners) for i in range(3))
    scene_size = maximum - minimum

    failures: list[str] = []
    if object_count < 280:
        failures.append(f"expected at least 280 objects, found {object_count}")
    if material_count < 10:
        failures.append(f"expected at least 10 materials, found {material_count}")
    if missing_actions:
        failures.append(f"missing actions: {sorted(missing_actions)}")
    if scene_size.y < 100 or scene_size.z > 20:
        failures.append(
            "invalid Twinmotion orientation: expected a long Y axis and compact Z "
            f"height, found size {tuple(round(value, 3) for value in scene_size)}"
        )

    if failures:
        raise RuntimeError("Twinmotion export validation failed: " + "; ".join(failures))

    print(
        "Twinmotion export validation passed:",
        f"{object_count} objects,",
        f"{material_count} materials,",
        f"{len(actions)} actions,",
        f"bounds {tuple(round(value, 3) for value in scene_size)}",
    )


if __name__ == "__main__":
    main()
