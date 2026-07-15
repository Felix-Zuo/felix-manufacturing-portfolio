"""Report world-space bounds that can distort Twinmotion framing."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


OUTPUT_PATH = Path(__file__).with_name("import") / "scene-bounds.json"


def object_bounds(obj: bpy.types.Object) -> dict[str, object] | None:
    if obj.type not in {"MESH", "CURVE", "SURFACE", "META", "FONT"}:
        return None
    if not getattr(obj, "bound_box", None):
        return None

    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector(min(point[i] for point in corners) for i in range(3))
    maximum = Vector(max(point[i] for point in corners) for i in range(3))
    size = maximum - minimum
    center = (minimum + maximum) / 2
    return {
        "name": obj.name,
        "type": obj.type,
        "minimum": list(minimum),
        "maximum": list(maximum),
        "center": list(center),
        "size": list(size),
        "largest_dimension": max(size),
        "furthest_coordinate": max(abs(value) for value in (*minimum, *maximum)),
    }


def main() -> None:
    records = [record for obj in bpy.context.scene.objects if (record := object_bounds(obj))]
    records.sort(
        key=lambda record: (record["furthest_coordinate"], record["largest_dimension"]),
        reverse=True,
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")

    print("Largest or furthest scene bounds:")
    for record in records[:30]:
        print(
            record["name"],
            "center=", tuple(round(value, 3) for value in record["center"]),
            "size=", tuple(round(value, 3) for value in record["size"]),
            "extent=", round(record["furthest_coordinate"], 3),
        )


if __name__ == "__main__":
    main()
