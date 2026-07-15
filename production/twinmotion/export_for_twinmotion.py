"""Export the existing mechanical scene as Twinmotion-ready GLB packages.

The V4 Blender scene is used only as a dimensional and mechanical source. Final
materials, environment dressing, lighting, and camera work are authored in
Twinmotion.
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "production" / "twinmotion" / "import"
SOURCE_SCENE = ROOT / "production" / "source-scenes" / "felix-journey-v4-desktop.blend"

EXPORT_TYPES = {"EMPTY", "MESH"}
EXCLUDED_PREFIXES = ("CIN_", "LD_")


def is_excluded(obj: bpy.types.Object) -> bool:
    return obj.type not in EXPORT_TYPES or obj.name.startswith(EXCLUDED_PREFIXES)


def has_animation(obj: bpy.types.Object) -> bool:
    data = obj.animation_data
    return bool(data and (data.action or data.nla_tracks))


def descendants(root: bpy.types.Object) -> set[bpy.types.Object]:
    result: set[bpy.types.Object] = {root}
    pending = list(root.children)
    while pending:
        child = pending.pop()
        if child in result:
            continue
        result.add(child)
        pending.extend(child.children)
    return result


def bake_delta_rotation_actions() -> list[str]:
    """Convert Blender-only delta Euler animation to portable quaternions."""
    scene = bpy.context.scene
    converted: list[str] = []

    for obj in bpy.data.objects:
        data = obj.animation_data
        action = data.action if data else None
        if not action or not any(
            curve.data_path == "delta_rotation_euler" for curve in action.fcurves
        ):
            continue

        samples: list[tuple[int, object]] = []
        for frame in range(scene.frame_start, scene.frame_end + 1):
            scene.frame_set(frame)
            _location, rotation, _scale = obj.matrix_basis.decompose()
            samples.append((frame, rotation.copy()))

        obj.animation_data_clear()
        obj.rotation_mode = "QUATERNION"
        obj.delta_rotation_euler = (0.0, 0.0, 0.0)
        for frame, rotation in samples:
            obj.rotation_quaternion = rotation
            obj.keyframe_insert(
                data_path="rotation_quaternion",
                frame=frame,
                group="PortableRotation",
            )

        if obj.animation_data and obj.animation_data.action:
            obj.animation_data.action.name = f"{action.name}_Portable"
        converted.append(obj.name)

    scene.frame_set(scene.frame_start)
    return converted


def export_objects(
    objects: set[bpy.types.Object],
    path: Path,
    *,
    animations: bool,
) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    exportable = [obj for obj in objects if not is_excluded(obj)]
    for obj in exportable:
        obj.hide_viewport = False
        obj.hide_render = False
        obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_animations=animations,
        export_frame_range=True,
        export_force_sampling=True,
        export_cameras=False,
        export_lights=False,
        export_yup=True,
        export_apply=False,
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    converted_delta_rotations = bake_delta_rotation_actions()

    candidates = {obj for obj in bpy.data.objects if not is_excluded(obj)}
    animated_roots = {
        obj
        for obj in candidates
        if has_animation(obj) and not (obj.parent and has_animation(obj.parent))
    }

    animated: set[bpy.types.Object] = set()
    for root in animated_roots:
        animated.update(descendants(root))

    # Preserve parent transforms for animated descendants.
    for obj in tuple(animated):
        parent = obj.parent
        while parent:
            if not is_excluded(parent):
                animated.add(parent)
            parent = parent.parent

    static = candidates - animated

    export_objects(
        static,
        OUTPUT_DIR / "felix-v5-environment-static.glb",
        animations=False,
    )
    export_objects(
        animated,
        OUTPUT_DIR / "felix-v5-mechanical-animation.glb",
        animations=True,
    )
    export_objects(
        candidates,
        OUTPUT_DIR / "felix-v5-mechanical-core.glb",
        animations=True,
    )

    scene = bpy.context.scene
    inventory = {
        "source_scene": str(SOURCE_SCENE),
        "fps": scene.render.fps / scene.render.fps_base,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "object_count": len(candidates),
        "static_object_count": len(static),
        "animated_object_count": len(animated),
        "animated_roots": sorted(obj.name for obj in animated_roots),
        "converted_delta_rotations": converted_delta_rotations,
        "static_objects": sorted(obj.name for obj in static),
        "animated_objects": sorted(obj.name for obj in animated),
        "materials": sorted(material.name for material in bpy.data.materials),
    }
    (OUTPUT_DIR / "scene-inventory.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        "Twinmotion export complete:",
        f"{len(static)} static objects,",
        f"{len(animated)} animated objects",
    )


if __name__ == "__main__":
    main()
