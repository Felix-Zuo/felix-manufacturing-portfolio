"""Build and render the pre-rendered portfolio journey in Blender."""

from __future__ import annotations

import argparse
import hashlib
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
import mature_factory  # noqa: E402
import industrial_robot  # noqa: E402
import precision_grinder  # noqa: E402
import fpv_stage  # noqa: E402
import fpv_vfx  # noqa: E402
import fpv_lighting  # noqa: E402
import animation  # noqa: E402


FALLBACK_CHAPTER_FRAMES = [91, 169, 301, 433, 553, 673, 793, 877]


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
    parser.add_argument("--render-step", type=int, choices=(1, 2), default=1)
    parser.add_argument("--frame-start", type=int)
    parser.add_argument("--frame-end", type=int)
    parser.add_argument("--resume", action="store_true")
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

    if mode in {"mobile", "blend-mobile"}:
        # 720p vertical is visually lossless at the site's <=767px mobile
        # breakpoint while keeping frame decode and thermal cost practical.
        render.resolution_x = 720
        render.resolution_y = 1280
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
        {
            "path": ROOT / "public" / "evidence" / "notice-cinematic.png",
        },
        {
            "path": ROOT / "public" / "evidence" / "takt-live-workbench.mp4",
            "frame_start": 481,
            "frame_duration": 332,
        },
        {
            "path": ROOT / "public" / "evidence" / "visibility-cinematic.png",
        },
        {
            "path": ROOT / "public" / "evidence" / "lab-cinematic.png",
        },
    ]

    screens = assets.get("screen_displays") or assets.get("screens", [])
    if not isinstance(screens, (list, tuple)):
        return

    for index, screen in enumerate(screens[: len(evidence)]):
        if not isinstance(screen, bpy.types.Object) or screen.type != "MESH":
            continue
        source = evidence[index]
        image_path = source["path"]
        if not image_path.exists():
            continue
        image = bpy.data.images.load(str(image_path), check_existing=True)
        if image_path.suffix.lower() == ".mp4":
            image.source = "MOVIE"
        material = bpy.data.materials.new(f"MAT_ProjectScreen_{index + 1:02d}")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = image
        texture.interpolation = "Linear"
        if image.source == "MOVIE":
            texture.image_user.use_auto_refresh = True
            texture.image_user.use_cyclic = False
            texture.image_user.frame_start = int(source["frame_start"])
            texture.image_user.frame_duration = int(source["frame_duration"])
        emission.inputs["Strength"].default_value = 1.35
        links.new(texture.outputs["Color"], emission.inputs["Color"])
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        screen.data.materials.clear()
        screen.data.materials.append(material)

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


def _source_fingerprint() -> str:
    digest = hashlib.sha256()
    source_paths = sorted(BLENDER_DIR.glob("*.py"))
    evidence_paths = sorted((ROOT / "public" / "evidence").glob("*"))
    for path in (*source_paths, *evidence_paths):
        if not path.is_file():
            continue
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _prepare_frame_output(
    mode: str,
    frame_start: int,
    frame_end: int,
    samples: int,
    duration: float,
    resume: bool,
) -> Path:
    output = RENDER_DIR / f"{mode}-frames"
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    manifest_path = output / "render-manifest.json"
    manifest = {
        "mode": mode,
        "fps": int(scene.render.fps),
        "frame_count": int(round(scene.render.fps * duration)),
        "duration_seconds": float(duration),
        "resolution": [int(scene.render.resolution_x), int(scene.render.resolution_y)],
        "samples": int(samples),
        "source_fingerprint": _source_fingerprint(),
    }

    existing_frames = list(output.glob("frame-*.png"))
    if resume and existing_frames:
        if not manifest_path.exists():
            raise RuntimeError(f"Cannot resume {output}: render-manifest.json is missing")
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing_manifest != manifest:
            raise RuntimeError(
                f"Cannot resume {output}: scene, quality, or resolution changed. "
                "Start a fresh frame directory instead of mixing renders."
            )
    elif existing_frames and not resume:
        overlapping = [
            output / f"frame-{frame:04d}.png"
            for frame in range(frame_start, frame_end + 1)
            if (output / f"frame-{frame:04d}.png").exists()
        ]
        if overlapping:
            raise RuntimeError(
                f"Refusing to overwrite {len(overlapping)} existing frames in {output}; "
                "use --resume to keep matching frames or clear the directory for a fresh render."
            )

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return output


def render_video_frames(
    mode: str,
    frame_start: int,
    frame_end: int,
    samples: int,
    duration: float,
    resume: bool,
) -> None:
    output = _prepare_frame_output(
        mode,
        frame_start,
        frame_end,
        samples,
        duration,
        resume,
    )
    scene = bpy.context.scene
    for frame in range(frame_start, frame_end + 1):
        frame_path = output / f"frame-{frame:04d}.png"
        if resume and frame_path.exists():
            print(f"RENDER_SKIP_EXISTING={frame_path.name}")
            continue
        scene.frame_set(frame)
        scene.render.filepath = str(frame_path)
        bpy.ops.render.render(write_still=True)
        print(f"RENDER_FRAME_COMPLETE={frame_path.name}")


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
    full_frame_end = int(round(args.fps * args.duration))
    render_frame_start = args.frame_start or 1
    render_frame_end = args.frame_end or full_frame_end
    if not 1 <= render_frame_start <= render_frame_end <= full_frame_end:
        raise ValueError(
            f"render frame range must be within 1-{full_frame_end}, got "
            f"{render_frame_start}-{render_frame_end}"
        )
    reset_scene()
    configure_scene(
        args.mode,
        args.fps,
        args.duration,
        args.samples,
        args.render_step,
    )

    assets = modeling.build_models()
    mature_factory.augment_factory(assets)
    industrial_robot.replace_robot(assets)
    precision_grinder.augment_grinder(assets)
    fpv_stage.augment_fpv_stage(assets)
    camera = cinematography.build_cinematography(
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
        bpy.context.scene.frame_start = render_frame_start
        bpy.context.scene.frame_end = render_frame_end
        render_playblast(args.mode)
    elif args.mode in {"desktop", "mobile"}:
        render_video_frames(
            args.mode,
            render_frame_start,
            render_frame_end,
            args.samples or 64,
            args.duration,
            args.resume,
        )


if __name__ == "__main__":
    main()
