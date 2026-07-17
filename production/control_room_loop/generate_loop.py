"""Generate a deterministic five-second control-room idle loop.

The camera and source photograph stay fixed. Motion is limited to explicit
screen, indicator, conveyor, and fan masks so the production scene cannot warp.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


FPS = 24
FRAME_COUNT = 120
DURATION_SECONDS = 5.0
REFERENCE_SIZE = (1672, 941)
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FFMPEG = (
    ROOT.parent
    / "tools"
    / "ffmpeg-release-essentials"
    / "ffmpeg-8.1.2-essentials_build"
    / "bin"
    / "ffmpeg.exe"
)


@dataclass(frozen=True)
class RenderConfig:
    width: int
    height: int
    frame_count: int = FRAME_COUNT
    fps: int = FPS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("proof", "fallback", "public"), default="proof")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--source", type=Path, default=ROOT / "public" / "media" / "control-room-base.jpg")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--ffmpeg", type=Path, default=DEFAULT_FFMPEG)
    parser.add_argument("--ffprobe", type=Path)
    return parser.parse_args()


def _scaled_point(point: tuple[float, float], config: RenderConfig) -> tuple[int, int]:
    x = round(point[0] * config.width / REFERENCE_SIZE[0])
    y = round(point[1] * config.height / REFERENCE_SIZE[1])
    return x, y


def _scaled_polygon(points: Iterable[tuple[float, float]], config: RenderConfig) -> list[tuple[int, int]]:
    return [_scaled_point(point, config) for point in points]


def load_base(source: Path, config: RenderConfig) -> Image.Image:
    with Image.open(source) as image:
        image = image.convert("RGB")
        source_ratio = image.width / image.height
        target_ratio = config.width / config.height
        if source_ratio > target_ratio:
            crop_width = round(image.height * target_ratio)
            left = (image.width - crop_width) // 2
            image = image.crop((left, 0, left + crop_width, image.height))
        elif source_ratio < target_ratio:
            crop_height = round(image.width / target_ratio)
            top = (image.height - crop_height) // 2
            image = image.crop((0, top, image.width, top + crop_height))
        return image.resize((config.width, config.height), Image.Resampling.LANCZOS)


def _screen_layer(config: RenderConfig, phase: float) -> Image.Image:
    layer = Image.new("RGBA", (config.width, config.height), (0, 0, 0, 0))
    screens = (
        ((92, 261), (358, 291), (358, 481), (92, 454)),
        ((1355, 269), (1623, 199), (1623, 427), (1355, 485)),
    )

    for index, reference_polygon in enumerate(screens):
        polygon = _scaled_polygon(reference_polygon, config)
        mask = Image.new("L", layer.size, 0)
        ImageDraw.Draw(mask).polygon(polygon, fill=255)
        bounds = mask.getbbox()
        if bounds is None:
            continue

        content = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(content)
        left, top, right, bottom = bounds
        width = max(right - left, 1)
        height = max(bottom - top, 1)
        refresh = 0.5 + 0.5 * math.sin(phase + index * math.pi * 0.65)
        base_alpha = round(34 + 12 * refresh)
        draw.rectangle(bounds, fill=(5, 27, 27, base_alpha))

        grid_alpha = round(25 + 10 * refresh)
        for fraction in (0.25, 0.5, 0.75):
            x = round(left + width * fraction)
            y = round(top + height * fraction)
            draw.line((x, top, x, bottom), fill=(53, 120, 112, grid_alpha), width=max(1, config.width // 1280))
            draw.line((left, y, right, y), fill=(53, 120, 112, grid_alpha), width=max(1, config.width // 1280))

        points: list[tuple[int, int]] = []
        for sample in range(17):
            u = sample / 16.0
            wave = 0.50 + 0.16 * math.sin(u * math.tau * 1.5 + index) + 0.05 * math.sin(phase + u * math.tau)
            points.append((round(left + width * (0.08 + 0.84 * u)), round(top + height * wave)))
        draw.line(points, fill=(104, 211, 188, round(75 + 25 * refresh)), width=max(1, config.width // 640))

        scan_y = round(top + height * (0.5 + 0.42 * math.sin(phase + index * 0.9)))
        scan_width = max(1, config.height // 180)
        draw.rectangle((left, scan_y - scan_width, right, scan_y + scan_width), fill=(117, 223, 201, 24))
        content.putalpha(Image.composite(content.getchannel("A"), Image.new("L", layer.size, 0), mask))
        layer = Image.alpha_composite(layer, content)

    return layer


def _indicator_layer(config: RenderConfig, phase: float) -> Image.Image:
    sharp = Image.new("RGBA", (config.width, config.height), (0, 0, 0, 0))
    glow = Image.new("RGBA", sharp.size, (0, 0, 0, 0))
    sharp_draw = ImageDraw.Draw(sharp)
    glow_draw = ImageDraw.Draw(glow)
    indicators = (
        ((337, 462), (255, 164, 46), 0.0),
        ((68, 505), (255, 176, 54), 1.7),
        ((1371, 464), (255, 164, 46), 3.1),
        ((520, 472), (72, 222, 126), 0.8),
        ((1136, 471), (72, 222, 126), 2.4),
    )
    core_radius = max(1, round(config.width / 836))
    glow_radius = max(3, round(config.width / 209))
    for point, color, offset in indicators:
        x, y = _scaled_point(point, config)
        pulse = 0.55 + 0.45 * math.sin(phase * 2.0 + offset)
        glow_alpha = round(24 + 34 * pulse)
        core_alpha = round(95 + 90 * pulse)
        glow_draw.ellipse((x - glow_radius, y - glow_radius, x + glow_radius, y + glow_radius), fill=(*color, glow_alpha))
        sharp_draw.ellipse((x - core_radius, y - core_radius, x + core_radius, y + core_radius), fill=(*color, core_alpha))
    blur_radius = max(1.0, config.width / 650.0)
    return Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(blur_radius)), sharp)


def _factory_motion_layer(config: RenderConfig, phase: float) -> Image.Image:
    layer = Image.new("RGBA", (config.width, config.height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    # Repeating equally spaced markers translate by exactly one spacing per loop.
    x0, y0 = _scaled_point((612, 447), config)
    x1, y1 = _scaled_point((1095, 462), config)
    spacing = max(8, round(config.width * 0.035))
    offset = (phase / math.tau) * spacing
    marker_width = max(2, round(config.width * 0.007))
    marker_height = max(1, round(config.height * 0.004))
    x = x0 - spacing + offset
    while x <= x1 + spacing:
        t = (x - x0) / max(x1 - x0, 1)
        y = y0 + (y1 - y0) * t
        draw.rounded_rectangle(
            (round(x), round(y), round(x + marker_width), round(y + marker_height)),
            radius=max(1, marker_height // 2),
            fill=(118, 185, 143, 30),
        )
        x += spacing

    # Four whole rotations guarantee the fan returns to its starting transform.
    fan_center = _scaled_point((1113, 410), config)
    fan_radius = max(3, round(config.width * 0.0075))
    fan_angle = phase * 4.0
    for spoke in range(6):
        angle = fan_angle + spoke * math.tau / 6.0
        end = (
            round(fan_center[0] + fan_radius * math.cos(angle)),
            round(fan_center[1] + fan_radius * math.sin(angle)),
        )
        draw.line((fan_center, end), fill=(164, 190, 178, 34), width=max(1, config.width // 1280))
    hub = max(1, fan_radius // 4)
    draw.ellipse(
        (fan_center[0] - hub, fan_center[1] - hub, fan_center[0] + hub, fan_center[1] + hub),
        fill=(185, 205, 194, 42),
    )
    return layer.filter(ImageFilter.GaussianBlur(max(0.3, config.width / 2600.0)))


def allowed_motion_mask(config: RenderConfig) -> np.ndarray:
    mask = Image.new("L", (config.width, config.height), 0)
    draw = ImageDraw.Draw(mask)
    for polygon in (
        ((82, 251), (369, 280), (369, 492), (82, 465)),
        ((1343, 257), (1634, 185), (1634, 439), (1343, 497)),
    ):
        draw.polygon(_scaled_polygon(polygon, config), fill=255)
    for point in ((337, 462), (68, 505), (1371, 464), (520, 472), (1136, 471)):
        x, y = _scaled_point(point, config)
        radius = max(8, round(config.width / 50))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
    draw.polygon(_scaled_polygon(((535, 420), (1165, 420), (1165, 490), (535, 475)), config), fill=255)
    x, y = _scaled_point((1113, 410), config)
    radius = max(5, round(config.width * 0.011))
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
    return np.asarray(mask, dtype=np.uint8) > 0


def render_frame(base: Image.Image, frame_index: int, config: RenderConfig) -> Image.Image:
    phase = math.tau * (frame_index % config.frame_count) / config.frame_count
    frame = base.convert("RGBA")
    frame = Image.alpha_composite(frame, _screen_layer(config, phase))
    frame = Image.alpha_composite(frame, _indicator_layer(config, phase))
    frame = Image.alpha_composite(frame, _factory_motion_layer(config, phase))
    return frame.convert("RGB")


def frame_hash(frame: Image.Image) -> str:
    return hashlib.sha256(frame.tobytes()).hexdigest()


def encode_outputs(
    base: Image.Image,
    config: RenderConfig,
    ffmpeg: Path,
    output_webm: Path,
    output_mp4: Path,
) -> dict[str, float | int | str]:
    command = [
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s:v", f"{config.width}x{config.height}",
        "-r", str(config.fps), "-i", "pipe:0", "-an",
        "-map", "0:v:0", "-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "0",
        "-deadline", "good", "-cpu-used", "5", "-row-mt", "1", "-g", "120",
        "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", str(output_webm),
        "-map", "0:v:0", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-flags", "+cgop",
        "-x264-params", "keyint=24:min-keyint=24:scenecut=0:open-gop=0:colorprim=bt709:transfer=bt709:colormatrix=bt709",
        "-g", "24", "-keyint_min", "24", "-sc_threshold", "0",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        str(output_mp4),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if process.stdin is None:
        raise RuntimeError("FFmpeg stdin was not created")

    allowed = allowed_motion_mask(config)
    base_pixels = np.asarray(base, dtype=np.int16)
    previous: np.ndarray | None = None
    adjacent_rms: list[float] = []
    fixed_region_max_error = 0
    first_pixels: np.ndarray | None = None
    last_pixels: np.ndarray | None = None
    try:
        for frame_index in range(config.frame_count):
            frame = render_frame(base, frame_index, config)
            pixels = np.asarray(frame, dtype=np.uint8)
            delta = np.abs(pixels.astype(np.int16) - base_pixels)
            fixed_region_max_error = max(fixed_region_max_error, int(delta[~allowed].max(initial=0)))
            if previous is not None:
                difference = pixels.astype(np.float32) - previous.astype(np.float32)
                adjacent_rms.append(float(np.sqrt(np.mean(difference * difference))))
            else:
                first_pixels = pixels.copy()
            previous = pixels.copy()
            last_pixels = pixels.copy()
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        return_code = process.wait()
    except BaseException:
        process.kill()
        process.wait()
        raise
    if return_code != 0:
        raise RuntimeError(f"FFmpeg encoding failed with exit code {return_code}")
    if first_pixels is None or last_pixels is None:
        raise RuntimeError("No frames were generated")
    seam_difference = last_pixels.astype(np.float32) - first_pixels.astype(np.float32)
    seam_rms = float(np.sqrt(np.mean(seam_difference * seam_difference)))
    return {
        "fixed_region_max_error": fixed_region_max_error,
        "adjacent_rms_mean": float(np.mean(adjacent_rms)),
        "adjacent_rms_max": float(np.max(adjacent_rms)),
        "seam_rms": seam_rms,
        "allowed_motion_coverage_percent": float(allowed.mean() * 100.0),
    }


def decoded_motion_stats(path: Path, ffmpeg: Path, config: RenderConfig) -> dict[str, float]:
    command = [
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(path),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    if process.stdout is None:
        raise RuntimeError("FFmpeg decode stdout was not created")
    frame_bytes = config.width * config.height * 3
    first: np.ndarray | None = None
    previous: np.ndarray | None = None
    last: np.ndarray | None = None
    adjacent_rms: list[float] = []
    try:
        for _ in range(config.frame_count):
            chunks: list[bytes] = []
            remaining = frame_bytes
            while remaining:
                chunk = process.stdout.read(remaining)
                if not chunk:
                    raise RuntimeError(f"Decoded stream ended early for {path.name}")
                chunks.append(chunk)
                remaining -= len(chunk)
            pixels = np.frombuffer(b"".join(chunks), dtype=np.uint8).reshape(
                (config.height, config.width, 3)
            )
            if previous is None:
                first = pixels.copy()
            else:
                difference = pixels.astype(np.float32) - previous.astype(np.float32)
                adjacent_rms.append(float(np.sqrt(np.mean(difference * difference))))
            previous = pixels.copy()
            last = pixels.copy()
        if process.stdout.read(1):
            raise RuntimeError(f"Decoded stream contains more than {config.frame_count} frames")
        return_code = process.wait()
    except BaseException:
        process.kill()
        process.wait()
        raise
    if return_code != 0:
        raise RuntimeError(f"FFmpeg decode failed for {path.name} with exit code {return_code}")
    if first is None or last is None:
        raise RuntimeError(f"No decoded frames in {path.name}")
    seam = last.astype(np.float32) - first.astype(np.float32)
    return {
        "decoded_adjacent_rms_mean": float(np.mean(adjacent_rms)),
        "decoded_adjacent_rms_max": float(np.max(adjacent_rms)),
        "decoded_seam_rms": float(np.sqrt(np.mean(seam * seam))),
    }


def probe_media(path: Path, ffprobe: Path, ffmpeg: Path, config: RenderConfig) -> dict[str, object]:
    command = [
        str(ffprobe), "-v", "error", "-count_frames", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    video_streams = [stream for stream in data["streams"] if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in data["streams"] if stream.get("codec_type") == "audio"]
    if len(video_streams) != 1 or audio_streams:
        raise RuntimeError(f"Unexpected stream layout in {path.name}")
    stream = video_streams[0]
    report: dict[str, object] = {
        "file": path.name,
        "bytes": path.stat().st_size,
        "codec": stream.get("codec_name"),
        "pixel_format": stream.get("pix_fmt"),
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "frame_rate": stream.get("avg_frame_rate"),
        "frames": int(stream.get("nb_read_frames", 0)),
        "duration_seconds": float(data["format"]["duration"]),
        "color_space": stream.get("color_space"),
        "color_transfer": stream.get("color_transfer"),
        "color_primaries": stream.get("color_primaries"),
        "audio_streams": len(audio_streams),
    }
    report.update(decoded_motion_stats(path, ffmpeg, config))
    return report


def main() -> None:
    args = parse_args()
    defaults = {
        "proof": (640, 360),
        "fallback": (1280, 720),
        "public": (1920, 1080),
    }
    default_width, default_height = defaults[args.mode]
    config = RenderConfig(args.width or default_width, args.height or default_height)
    if config.width % 2 or config.height % 2:
        raise ValueError("Output dimensions must be even for yuv420p")
    if not args.source.is_file():
        raise FileNotFoundError(args.source)
    if not args.ffmpeg.is_file():
        raise FileNotFoundError(args.ffmpeg)
    ffprobe = args.ffprobe or args.ffmpeg.with_name("ffprobe.exe")
    if not ffprobe.is_file():
        raise FileNotFoundError(ffprobe)

    output_dir = args.output_dir or (
        ROOT / "production" / "renders" / "control-room-loop-proof"
        if args.mode == "proof"
        else ROOT / "public" / "media"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    basenames = {
        "proof": "control-room-loop-proof",
        "fallback": "control-room-loop-720p",
        "public": "control-room-loop",
    }
    basename = basenames[args.mode]
    webm_path = output_dir / f"{basename}.webm"
    mp4_path = output_dir / f"{basename}.mp4"
    poster_path = output_dir / f"{basename}-poster.webp"
    report_path = (
        output_dir / f"{basename}-validation.json"
        if args.mode == "proof"
        else ROOT / "production" / "renders" / f"control-room-loop-{args.mode}-validation.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    base = load_base(args.source, config)
    frame_1 = render_frame(base, 0, config)
    frame_121 = render_frame(base, config.frame_count, config)
    frame_1_hash = frame_hash(frame_1)
    frame_121_hash = frame_hash(frame_121)
    if frame_1_hash != frame_121_hash:
        raise RuntimeError("Loop endpoint mismatch: generated frame 121 differs from frame 1")

    frame_1.save(poster_path, format="WEBP", quality=88, method=6)
    source_validation = encode_outputs(base, config, args.ffmpeg, webm_path, mp4_path)
    media = [
        probe_media(webm_path, ffprobe, args.ffmpeg, config),
        probe_media(mp4_path, ffprobe, args.ffmpeg, config),
    ]
    for item in media:
        if item["frames"] != config.frame_count:
            raise RuntimeError(f"{item['file']} has {item['frames']} frames; expected {config.frame_count}")
        if abs(float(item["duration_seconds"]) - DURATION_SECONDS) > 0.001:
            raise RuntimeError(f"{item['file']} duration is not exactly {DURATION_SECONDS:.3f} seconds")
        if item["frame_rate"] != f"{config.fps}/1":
            raise RuntimeError(f"{item['file']} frame rate is {item['frame_rate']}; expected {config.fps}/1")
    if source_validation["fixed_region_max_error"] != 0:
        raise RuntimeError("Pixels outside the approved motion masks changed")

    report = {
        "contract": {
            "fps": config.fps,
            "frames_encoded": config.frame_count,
            "duration_seconds": DURATION_SECONDS,
            "loop_endpoint": "generated frame 121 equals generated frame 1",
            "camera": "fixed source frame",
            "geometry": "fixed; overlays restricted to approved masks",
        },
        "source": str(args.source.resolve()),
        "mode": args.mode,
        "width": config.width,
        "height": config.height,
        "frame_1_sha256": frame_1_hash,
        "frame_121_sha256": frame_121_hash,
        "endpoint_exact_match": frame_1_hash == frame_121_hash,
        "source_frame_validation": source_validation,
        "media": media,
        "poster": {
            "file": poster_path.name,
            "bytes": poster_path.stat().st_size,
            "format": "WebP",
            "width": config.width,
            "height": config.height,
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (BrokenPipeError, KeyboardInterrupt):
        sys.exit(130)
