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
import story_cinematography  # noqa: E402
import lookdev  # noqa: E402
import modeling  # noqa: E402
import mature_factory  # noqa: E402
import industrial_agv  # noqa: E402
import industrial_robot  # noqa: E402
import precision_grinder  # noqa: E402
import fpv_factory_systems  # noqa: E402
import fpv_stage  # noqa: E402
import fpv_vfx  # noqa: E402
import fpv_lighting  # noqa: E402
import animation  # noqa: E402
import story_scene  # noqa: E402
import story_animation  # noqa: E402


FALLBACK_CHAPTER_FRAMES = [1, 84, 132, 228, 300, 342, 420, 474, 588, 660, 798, 882, 904]


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
    parser.add_argument("--duration", type=float, default=38.0)
    parser.add_argument("--samples", type=int)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--render-start", type=int)
    parser.add_argument("--render-end", type=int)
    parser.add_argument("--render-step", type=int, choices=(1, 2), default=1)
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


def configure_scene(
    mode: str,
    fps: int,
    duration: float,
    samples: int | None,
    render_step: int,
    width: int | None,
    height: int | None,
) -> None:
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = round(fps * duration)
    scene.frame_step = render_step
    if render_step > 1 and not mode.startswith("playblast"):
        raise ValueError("--render-step is currently supported only for playblast modes")
    if fps % render_step != 0:
        raise ValueError("fps must be divisible by --render-step")
    scene.render.fps = fps // render_step
    scene.render.fps_base = 1.0
    scene.render.engine = "BLENDER_EEVEE_NEXT"

    render = scene.render
    render.image_settings.color_mode = "RGBA"
    render.film_transparent = False
    render.use_file_extension = True

    if (width is None) != (height is None):
        raise ValueError("--width and --height must be provided together")
    if width is not None and (width < 320 or height is None or height < 320):
        raise ValueError("custom render dimensions must both be at least 320 px")

    if mode in {"mobile", "blend-mobile"}:
        render.resolution_x = 1080
        render.resolution_y = 1920
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
        render.resolution_x = 1920
        render.resolution_y = 1080
        render.resolution_percentage = 100

    if width is not None and height is not None:
        render.resolution_x = width
        render.resolution_y = height
        render.resolution_percentage = 100

    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = (
        "16" if mode in {"desktop", "mobile", "blend", "blend-mobile"} else "8"
    )
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
        ROOT / "public" / "evidence" / "notice-cinematic.png",
        ROOT / "public" / "evidence" / "takt-cinematic.png",
        ROOT / "public" / "evidence" / "excel-ops-product.png",
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

    scan_line = assets.get("scan_line")
    if isinstance(scan_line, bpy.types.Object) and scan_line.type == "MESH":
        material = bpy.data.materials.new("MAT_V8_ScanTrace")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = (0.08, 0.72, 0.38, 1.0)
        emission.inputs["Strength"].default_value = 0.62
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        scan_line.data.materials.clear()
        scan_line.data.materials.append(material)

    inspection_laser = assets.get("inspection_laser_line")
    if isinstance(inspection_laser, bpy.types.Object) and inspection_laser.type == "MESH":
        material = bpy.data.materials.new("MAT_V8_InspectionLaser")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = (0.10, 0.70, 0.56, 1.0)
        emission.inputs["Strength"].default_value = 0.46
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        inspection_laser.data.materials.clear()
        inspection_laser.data.materials.append(material)

    # The entrance command bay is environmental scale only. Repeating a hero
    # project before the four evidence beats weakens the one-shot hierarchy.


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


def render_video_frames(
    mode: str,
    render_start: int | None = None,
    render_end: int | None = None,
) -> None:
    output = RENDER_DIR / f"{mode}-frames"
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    full_start = int(scene.frame_start)
    full_end = int(scene.frame_end)
    chunk_start = full_start if render_start is None else int(render_start)
    chunk_end = full_end if render_end is None else int(render_end)
    if not full_start <= chunk_start <= chunk_end <= full_end:
        raise ValueError(
            f"render range {chunk_start}-{chunk_end} is outside {full_start}-{full_end}"
        )
    scene.render.filepath = str(output / "frame-")
    scene["full_animation_frame_start"] = full_start
    scene["full_animation_frame_end"] = full_end
    scene["render_chunk_frame_start"] = chunk_start
    scene["render_chunk_frame_end"] = chunk_end
    scene.frame_start = chunk_start
    scene.frame_end = chunk_end
    try:
        bpy.ops.render.render(animation=True)
    finally:
        scene.frame_start = full_start
        scene.frame_end = full_end


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
    configure_scene(
        args.mode,
        args.fps,
        args.duration,
        args.samples,
        args.render_step,
        args.width,
        args.height,
    )

    assets = modeling.build_models()
    mature_factory.augment_factory(assets)
    industrial_agv.replace_agv(assets)
    industrial_robot.replace_robot(assets)
    precision_grinder.augment_grinder(assets)
    fpv_factory_systems.augment_factory_systems(
        assets,
        fps=args.fps,
        duration=args.duration,
    )
    fpv_stage.augment_fpv_stage(assets)
    story_scene.augment_story_scene(assets)
    camera = story_cinematography.build_cinematography(
        assets,
        fps=args.fps,
        duration=args.duration,
    )
    if args.mode in {"mobile", "storyboard-mobile", "playblast-mobile", "blend-mobile"}:
        widen_mobile_camera(camera)
    lookdev.setup_lookdev(assets, camera)
    fpv_lighting.augment_fpv_lighting(assets)
    set_screen_textures(assets)
    fpv_vfx.augment_fpv_vfx(assets)
    animation.animate_assets(assets, fps=args.fps, duration=args.duration)
    story_animation.animate_story(assets, fps=args.fps, duration=args.duration)
    restore_render_samples(args.mode, args.samples)
    # Lookdev owns general render defaults and restores 24 fps. Reassert the
    # intentional half-rate output only after every augmentation has run.
    bpy.context.scene.frame_step = args.render_step
    bpy.context.scene.render.fps = args.fps // args.render_step
    bpy.context.scene["source_animation_fps"] = args.fps
    bpy.context.scene["render_frame_step"] = args.render_step

    save_blend(args.mode)

    if args.mode in {"storyboard", "storyboard-mobile"}:
        render_storyboard(args.mode)
    elif args.mode in {"playblast", "playblast-mobile"}:
        render_playblast(args.mode)
    elif args.mode in {"desktop", "mobile"}:
        render_video_frames(args.mode, args.render_start, args.render_end)


if __name__ == "__main__":
    main()
