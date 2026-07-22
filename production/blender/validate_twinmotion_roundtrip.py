"""Import a Twinmotion handoff file back into Blender and verify motion survives."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--min-moving", type=int, default=10)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _matrix_changed(samples: list[Matrix], tolerance: float = 1.0e-5) -> bool:
    reference = samples[0]
    return any(
        abs(float(sample[row][column] - reference[row][column])) > tolerance
        for sample in samples[1:]
        for row in range(4)
        for column in range(4)
    )


def _scene_bounds(meshes: list[bpy.types.Object]) -> tuple[list[float], list[float]]:
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in meshes
        for corner in obj.bound_box
    ]
    return (
        [min(float(point[axis]) for point in points) for axis in range(3)],
        [max(float(point[axis]) for point in points) for axis in range(3)],
    )


def main() -> None:
    args = _args()
    source = args.input.resolve()
    report_path = args.report.resolve()
    if not source.exists():
        raise RuntimeError(f"Handoff file does not exist: {source}")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.users == 0:
            bpy.data.collections.remove(collection)

    suffix = source.suffix.lower()
    if suffix == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(source), automatic_bone_orientation=False)
    elif suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(source))
    else:
        raise RuntimeError(f"Unsupported handoff format: {suffix}")

    scene = bpy.context.scene
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("Roundtrip import contains no meshes")

    actions = [
        action
        for action in bpy.data.actions
        if action.frame_range[1] > action.frame_range[0]
    ]
    frame_start = int(min((action.frame_range[0] for action in actions), default=1))
    frame_end = int(max((action.frame_range[1] for action in actions), default=1))
    sample_frames = sorted({frame_start, (frame_start + frame_end) // 2, frame_end})
    samples: dict[bpy.types.Object, list[Matrix]] = {obj: [] for obj in meshes}
    frame_bounds: dict[str, dict[str, list[float]]] = {}
    for frame in sample_frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for obj in meshes:
            samples[obj].append(obj.matrix_world.copy())
        minimum, maximum = _scene_bounds(meshes)
        frame_bounds[str(frame)] = {"minimum": minimum, "maximum": maximum}

    moving = sorted(obj.name for obj, matrices in samples.items() if _matrix_changed(matrices))
    if not actions:
        raise RuntimeError("Roundtrip import contains no non-empty actions")
    if len(moving) < args.min_moving:
        raise RuntimeError(
            "Roundtrip import retained too few moving meshes: "
            f"{len(moving)} < {args.min_moving}"
        )

    report = {
        "status": "passed",
        "input": str(source),
        "format": suffix.lstrip("."),
        "mesh_count": len(meshes),
        "action_count": len(actions),
        "frame_range": [frame_start, frame_end],
        "sample_frames": sample_frames,
        "moving_mesh_count": len(moving),
        "minimum_moving_mesh_count": args.min_moving,
        "moving_meshes": moving,
        "frame_bounds": frame_bounds,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SUM_TWINMOTION_ROUNDTRIP=" + json.dumps(report))


if __name__ == "__main__":
    main()
