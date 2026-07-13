"""Build and render the pre-rendered portfolio journey in Blender."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[2]
BLENDER_DIR = Path(__file__).resolve().parent
RENDER_DIR = ROOT / "production" / "renders"

if str(BLENDER_DIR) not in sys.path:
    sys.path.insert(0, str(BLENDER_DIR))

import cinematography  # noqa: E402
import lookdev  # noqa: E402
import modeling  # noqa: E402
import animation  # noqa: E402


FALLBACK_CHAPTER_FRAMES = [1, 88, 168, 256, 352, 448, 544, 656]


def blender_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=(
            "storyboard",
            "storyboard-mobile",
            "playblast",
            "playblast-mobile",
            "desktop",
            "mobile",
            "blend",
            "blend-mobile",
        ),
        default="storyboard",
    )
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--duration", type=float, default=28.0)
    parser.add_argument("--samples", type=int)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(argv)


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.meshes,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def configure_scene(mode: str, fps: int, duration: float, samples: int | None) -> None:
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = round(fps * duration)
    scene.render.fps = fps
    scene.render.fps_base = 1.0
    scene.render.engine = "BLENDER_EEVEE_NEXT"

    render = scene.render
    render.image_settings.color_mode = "RGBA"
    render.film_transparent = False
    render.use_file_extension = True

    if mode in {"mobile", "blend-mobile"}:
        render.resolution_x = 900
        render.resolution_y = 1600
        render.resolution_percentage = 100
    elif mode == "playblast-mobile":
        render.resolution_x = 360
        render.resolution_y = 640
        render.resolution_percentage = 100
    elif mode == "playblast":
        render.resolution_x = 640
        render.resolution_y = 360
        render.resolution_percentage = 100
    elif mode == "storyboard-mobile":
        render.resolution_x = 1080
        render.resolution_y = 1920
        render.resolution_percentage = 40
    elif mode == "storyboard":
        render.resolution_x = 1280
        render.resolution_y = 720
        render.resolution_percentage = 60
    else:
        render.resolution_x = 1600
        render.resolution_y = 900
        render.resolution_percentage = 100

    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 30

    eevee = scene.eevee
    if mode.startswith("playblast"):
        default_samples = 24
    elif mode.startswith("storyboard"):
        default_samples = 32
    else:
        default_samples = 64
    render_samples = samples or default_samples
    if hasattr(eevee, "taa_samples"):
        eevee.taa_samples = render_samples
    if hasattr(eevee, "taa_render_samples"):
        eevee.taa_render_samples = render_samples


def restore_render_samples(mode: str, samples: int | None) -> None:
    """Reapply quality after lookdev, which also configures Eevee defaults."""
    if mode.startswith("playblast"):
        default_samples = 24
    elif mode.startswith("storyboard"):
        default_samples = 32
    else:
        default_samples = 64
    render_samples = samples or default_samples
    eevee = bpy.context.scene.eevee
    if hasattr(eevee, "taa_samples"):
        eevee.taa_samples = render_samples
    if hasattr(eevee, "taa_render_samples"):
        eevee.taa_render_samples = render_samples


def set_screen_textures(assets: dict[str, object]) -> None:
    evidence = [
        ROOT / "public" / "evidence" / "notice-workbench-product.png",
        ROOT / "public" / "evidence" / "takt-simulator-product.png",
        ROOT / "public" / "evidence" / "excel-ops-product.png",
        ROOT / "public" / "evidence" / "ops-platform-product.png",
    ]

    screens = assets.get("screen_displays") or assets.get("screens", [])
    if not isinstance(screens, (list, tuple)):
        return

    for index, screen in enumerate(screens[: len(evidence)]):
        if not isinstance(screen, bpy.types.Object) or screen.type != "MESH":
            continue
        image_path = evidence[index]
        if not image_path.exists():
            continue
        image = bpy.data.images.load(str(image_path), check_existing=True)
        material = bpy.data.materials.new(f"MAT_ProjectScreen_{index + 1:02d}")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = image
        emission.inputs["Strength"].default_value = 1.35
        links.new(texture.outputs["Color"], emission.inputs["Color"])
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        screen.data.materials.clear()
        screen.data.materials.append(material)


def widen_mobile_camera(camera: bpy.types.Object, factor: float = 0.68) -> None:
    if not camera or camera.type != "CAMERA":
        return
    camera.data.sensor_fit = "VERTICAL"
    action = camera.data.animation_data.action if camera.data.animation_data else None
    if action:
        for curve in action.fcurves:
            if curve.data_path != "lens":
                continue
            for point in curve.keyframe_points:
                point.co.y *= factor
                point.handle_left.y *= factor
                point.handle_right.y *= factor
    camera.data.lens *= factor


def save_blend(mode: str) -> Path:
    blend_dir = ROOT / "production" / "scenes"
    blend_dir.mkdir(parents=True, exist_ok=True)
    path = blend_dir / f"felix-journey-{mode}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    return path


def render_storyboard(mode: str) -> None:
    output_name = "storyboard-mobile" if mode == "storyboard-mobile" else "storyboard"
    output = RENDER_DIR / output_name
    output.mkdir(parents=True, exist_ok=True)
    encoded_frames = bpy.context.scene.get("cin_storyboard_frames")
    try:
        chapter_frames = json.loads(encoded_frames) if encoded_frames else FALLBACK_CHAPTER_FRAMES
    except (TypeError, ValueError, json.JSONDecodeError):
        chapter_frames = FALLBACK_CHAPTER_FRAMES
    for index, frame in enumerate(chapter_frames, start=1):
        bpy.context.scene.frame_set(min(frame, bpy.context.scene.frame_end))
        bpy.context.scene.render.filepath = str(output / f"{index:02d}-chapter.png")
        bpy.ops.render.render(write_still=True)


def render_video_frames(mode: str) -> None:
    output = RENDER_DIR / f"{mode}-frames"
    output.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(output / "frame-")
    bpy.ops.render.render(animation=True)


def render_playblast(mode: str) -> None:
    output = RENDER_DIR / "playblast"
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
    scene.render.ffmpeg.gopsize = 12
    scene.render.ffmpeg.audio_codec = "NONE"
    suffix = "mobile" if mode == "playblast-mobile" else "desktop"
    scene.render.filepath = str(output / f"felix-journey-{suffix}-playblast")
    bpy.ops.render.render(animation=True)


def main() -> None:
    args = blender_args()
    reset_scene()
    configure_scene(args.mode, args.fps, args.duration, args.samples)

    assets = modeling.build_models()
    camera = cinematography.build_cinematography(
        assets,
        fps=args.fps,
        duration=args.duration,
    )
    if args.mode in {"mobile", "storyboard-mobile", "playblast-mobile", "blend-mobile"}:
        widen_mobile_camera(camera)
    lookdev.setup_lookdev(assets, camera)
    set_screen_textures(assets)
    animation.animate_assets(assets, fps=args.fps, duration=args.duration)
    restore_render_samples(args.mode, args.samples)

    save_blend(args.mode)

    if args.mode in {"storyboard", "storyboard-mobile"}:
        render_storyboard(args.mode)
    elif args.mode in {"playblast", "playblast-mobile"}:
        render_playblast(args.mode)
    elif args.mode in {"desktop", "mobile"}:
        render_video_frames(args.mode)


if __name__ == "__main__":
    main()
