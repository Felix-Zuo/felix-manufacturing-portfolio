"""Generate a deterministic control-room environment loop.

The source photograph, camera, geometry, and black monitor surfaces remain
fixed. Motion is limited to localized practical lights, restrained machine
status lamps, and two distant equipment indicators. Screen quadrilaterals are
loaded from a shared calibration file and exported with every validation
report so the frontend can place live media without baking it into the video.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


FPS = 24
FRAME_COUNT = 120
DURATION_SECONDS = 5.0
REFERENCE_SIZE = (1672, 941)
ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_PATH = Path(__file__).with_name("screen-quads.json")
DEFAULT_FFMPEG = (
    ROOT.parent
    / "tools"
    / "ffmpeg-release-essentials"
    / "ffmpeg-8.1.2-essentials_build"
    / "bin"
    / "ffmpeg.exe"
)

Point = tuple[float, float]
Quad = tuple[Point, Point, Point, Point]


@dataclass(frozen=True)
class RenderConfig:
    width: int
    height: int
    frame_count: int = FRAME_COUNT
    fps: int = FPS


@dataclass(frozen=True)
class ScreenGeometry:
    screen_id: str
    outer_quad: Quad
    content_quad: Quad


@dataclass(frozen=True)
class ScreenCalibration:
    source_width: int
    source_height: int
    coordinate_system: str
    point_order: tuple[str, str, str, str]
    screens: tuple[ScreenGeometry, ...]


# Existing practical fixtures in the high-resolution source photograph.
# Radii are support bounds, not generated geometry dimensions.
CEILING_PRACTICALS: tuple[tuple[Point, Point, float], ...] = (
    ((500, 39), (31, 14), 0.0),
    ((846, 38), (31, 14), 1.1),
    ((1169, 38), (31, 14), 2.2),
    ((578, 112), (27, 12), 2.9),
    ((877, 111), (27, 12), 4.0),
    ((1100, 110), (27, 12), 5.1),
)

AMBER_PRACTICALS: tuple[tuple[Point, Point, float], ...] = (
    ((39, 511), (17, 24), 0.4),
    ((337, 462), (17, 24), 2.3),
    ((1337, 462), (17, 24), 4.2),
)

DISTANT_STATUS_LIGHTS: tuple[tuple[Point, tuple[int, int, int], float], ...] = (
    ((520, 472), (75, 221, 126), 0.3),
    ((650, 467), (75, 221, 126), 1.6),
    ((1038, 466), (75, 221, 126), 3.0),
    ((1136, 471), (75, 221, 126), 4.4),
    ((741, 450), (229, 170, 72), 2.2),
)

# Tiny work-light paths imply distant equipment activity without moving or
# redrawing any machine geometry.
DISTANT_EQUIPMENT_PATHS: tuple[tuple[Point, Point, tuple[int, int, int], float], ...] = (
    ((958, 342), (987, 350), (239, 183, 82), 0.0),
    ((768, 446), (795, 451), (111, 202, 151), math.pi),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("proof", "fallback", "public"), default="proof")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "public" / "media" / "control-room-base.jpg",
    )
    parser.add_argument("--screen-calibration", type=Path, default=CALIBRATION_PATH)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--ffmpeg", type=Path, default=DEFAULT_FFMPEG)
    parser.add_argument("--ffprobe", type=Path)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quad_area(quad: Sequence[Point]) -> float:
    return abs(
        sum(
            quad[index][0] * quad[(index + 1) % 4][1]
            - quad[(index + 1) % 4][0] * quad[index][1]
            for index in range(4)
        )
        / 2.0
    )


def _parse_quad(
    value: object,
    label: str,
    source_width: int,
    source_height: int,
) -> Quad:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"{label} must contain four points")

    points: list[Point] = []
    for index, raw_point in enumerate(value):
        if not isinstance(raw_point, list) or len(raw_point) != 2:
            raise ValueError(f"{label}[{index}] must be an [x, y] pair")
        x, y = float(raw_point[0]), float(raw_point[1])
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError(f"{label}[{index}] contains a non-finite coordinate")
        if not (0 <= x < source_width and 0 <= y < source_height):
            raise ValueError(f"{label}[{index}] lies outside the reference image")
        points.append((x, y))

    quad = tuple(points)
    if _quad_area(quad) < 100.0:
        raise ValueError(f"{label} is degenerate")
    return quad  # type: ignore[return-value]


def _reference_polygon_mask(quad: Quad, size: tuple[int, int]) -> np.ndarray:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon([(round(x), round(y)) for x, y in quad], fill=255)
    return np.asarray(mask, dtype=np.uint8) > 0


def load_screen_calibration(path: Path) -> ScreenCalibration:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported screen calibration schema")

    source = data.get("source")
    if not isinstance(source, dict):
        raise ValueError("Screen calibration is missing source metadata")
    source_width = int(source.get("width", 0))
    source_height = int(source.get("height", 0))
    if (source_width, source_height) != REFERENCE_SIZE:
        raise ValueError(
            f"Screen calibration reference is {source_width}x{source_height}; "
            f"expected {REFERENCE_SIZE[0]}x{REFERENCE_SIZE[1]}"
        )

    raw_order = data.get("point_order")
    expected_order = ("top_left", "top_right", "bottom_right", "bottom_left")
    if tuple(raw_order or ()) != expected_order:
        raise ValueError(f"Screen points must use order {expected_order}")

    raw_screens = data.get("screens")
    if not isinstance(raw_screens, list) or not raw_screens:
        raise ValueError("Screen calibration does not contain screens")

    screens: list[ScreenGeometry] = []
    seen: set[str] = set()
    for raw_screen in raw_screens:
        if not isinstance(raw_screen, dict):
            raise ValueError("Each screen calibration entry must be an object")
        screen_id = str(raw_screen.get("id", "")).strip()
        if not screen_id or screen_id in seen:
            raise ValueError(f"Invalid or duplicate screen id: {screen_id!r}")
        seen.add(screen_id)
        outer_quad = _parse_quad(
            raw_screen.get("outer_quad"),
            f"{screen_id}.outer_quad",
            source_width,
            source_height,
        )
        content_quad = _parse_quad(
            raw_screen.get("content_quad"),
            f"{screen_id}.content_quad",
            source_width,
            source_height,
        )
        outer_mask = _reference_polygon_mask(outer_quad, REFERENCE_SIZE)
        content_mask = _reference_polygon_mask(content_quad, REFERENCE_SIZE)
        if np.any(content_mask & ~outer_mask):
            raise ValueError(f"{screen_id}.content_quad must stay inside outer_quad")
        screens.append(ScreenGeometry(screen_id, outer_quad, content_quad))

    return ScreenCalibration(
        source_width=source_width,
        source_height=source_height,
        coordinate_system=str(data.get("coordinate_system", "")),
        point_order=expected_order,
        screens=tuple(screens),
    )


def _scaled_point(point: Point, config: RenderConfig) -> tuple[int, int]:
    x = round(point[0] * config.width / REFERENCE_SIZE[0])
    y = round(point[1] * config.height / REFERENCE_SIZE[1])
    return x, y


def _scaled_polygon(points: Iterable[Point], config: RenderConfig) -> list[tuple[int, int]]:
    return [_scaled_point(point, config) for point in points]


def _scaled_ellipse_box(center: Point, radii: Point, config: RenderConfig) -> tuple[int, int, int, int]:
    x, y = _scaled_point(center, config)
    rx = max(1, round(radii[0] * config.width / REFERENCE_SIZE[0]))
    ry = max(1, round(radii[1] * config.height / REFERENCE_SIZE[1]))
    return x - rx, y - ry, x + rx, y + ry


def load_base(source: Path, config: RenderConfig) -> Image.Image:
    with Image.open(source) as image:
        image = image.convert("RGB")
        if image.size != REFERENCE_SIZE:
            raise ValueError(
                f"Source image is {image.width}x{image.height}; "
                f"expected calibrated source {REFERENCE_SIZE[0]}x{REFERENCE_SIZE[1]}"
            )
        return image.resize((config.width, config.height), Image.Resampling.LANCZOS)


@lru_cache(maxsize=12)
def screen_masks(
    calibration: ScreenCalibration,
    config: RenderConfig,
    field: str = "content_quad",
) -> dict[str, np.ndarray]:
    result: dict[str, np.ndarray] = {}
    for screen in calibration.screens:
        quad = getattr(screen, field)
        mask = Image.new("L", (config.width, config.height), 0)
        ImageDraw.Draw(mask).polygon(_scaled_polygon(quad, config), fill=255)
        result[screen.screen_id] = np.asarray(mask, dtype=np.uint8) > 0
    return result


@lru_cache(maxsize=6)
def combined_screen_mask(calibration: ScreenCalibration, config: RenderConfig) -> np.ndarray:
    combined = np.zeros((config.height, config.width), dtype=bool)
    for mask in screen_masks(calibration, config).values():
        combined |= mask
    return combined


@lru_cache(maxsize=6)
def motion_support_mask(calibration: ScreenCalibration, config: RenderConfig) -> Image.Image:
    mask = Image.new("L", (config.width, config.height), 0)
    draw = ImageDraw.Draw(mask)

    for center, radii, _ in CEILING_PRACTICALS:
        draw.ellipse(_scaled_ellipse_box(center, radii, config), fill=255)
    for center, radii, _ in AMBER_PRACTICALS:
        draw.ellipse(_scaled_ellipse_box(center, radii, config), fill=255)
    for center, _, _ in DISTANT_STATUS_LIGHTS:
        draw.ellipse(_scaled_ellipse_box(center, (12, 12), config), fill=255)
    for start, end, _, _ in DISTANT_EQUIPMENT_PATHS:
        left = min(start[0], end[0]) - 12
        top = min(start[1], end[1]) - 10
        right = max(start[0], end[0]) + 12
        bottom = max(start[1], end[1]) + 10
        draw.rectangle(
            (
                *_scaled_point((left, top), config),
                *_scaled_point((right, bottom), config),
            ),
            fill=255,
        )

    pixels = np.asarray(mask, dtype=np.uint8).copy()
    pixels[combined_screen_mask(calibration, config)] = 0
    return Image.fromarray(pixels, mode="L")


def _clip_layer_to_motion_bounds(
    layer: Image.Image,
    support: Image.Image,
    calibration: ScreenCalibration,
    config: RenderConfig,
) -> Image.Image:
    alpha = np.asarray(layer.getchannel("A"), dtype=np.uint16).copy()
    support_pixels = np.asarray(support, dtype=np.uint16)
    alpha = (alpha * support_pixels) // 255
    alpha[combined_screen_mask(calibration, config)] = 0
    layer.putalpha(Image.fromarray(alpha.astype(np.uint8), mode="L"))
    return layer


def _practical_light_layer(
    config: RenderConfig,
    phase: float,
    calibration: ScreenCalibration,
) -> Image.Image:
    diffuse = Image.new("RGBA", (config.width, config.height), (0, 0, 0, 0))
    sharp = Image.new("RGBA", diffuse.size, (0, 0, 0, 0))
    diffuse_draw = ImageDraw.Draw(diffuse)
    sharp_draw = ImageDraw.Draw(sharp)

    for center, support_radii, offset in CEILING_PRACTICALS:
        pulse = 0.5 + 0.5 * math.sin(phase + offset)
        core_radii = (max(2.0, support_radii[0] * 0.28), max(1.0, support_radii[1] * 0.28))
        diffuse_draw.ellipse(
            _scaled_ellipse_box(center, core_radii, config),
            fill=(232, 239, 231, round(2 + 4 * pulse)),
        )

    for center, support_radii, offset in AMBER_PRACTICALS:
        pulse = 0.5 + 0.5 * math.sin(phase + offset)
        diffuse_draw.ellipse(
            _scaled_ellipse_box(center, (support_radii[0] * 0.5, support_radii[1] * 0.5), config),
            fill=(244, 172, 67, round(4 + 8 * pulse)),
        )
        sharp_draw.ellipse(
            _scaled_ellipse_box(center, (2.2, 4.2), config),
            fill=(255, 204, 109, round(8 + 14 * pulse)),
        )

    blur_radius = max(0.45, config.width / 900.0)
    layer = Image.alpha_composite(diffuse.filter(ImageFilter.GaussianBlur(blur_radius)), sharp)
    return _clip_layer_to_motion_bounds(
        layer,
        motion_support_mask(calibration, config),
        calibration,
        config,
    )


def _status_light_layer(
    config: RenderConfig,
    phase: float,
    calibration: ScreenCalibration,
) -> Image.Image:
    glow = Image.new("RGBA", (config.width, config.height), (0, 0, 0, 0))
    sharp = Image.new("RGBA", glow.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    sharp_draw = ImageDraw.Draw(sharp)

    for center, color, offset in DISTANT_STATUS_LIGHTS:
        pulse = 0.5 + 0.5 * math.sin(phase * 2.0 + offset)
        glow_draw.ellipse(
            _scaled_ellipse_box(center, (5.5, 5.5), config),
            fill=(*color, round(4 + 9 * pulse)),
        )
        sharp_draw.ellipse(
            _scaled_ellipse_box(center, (1.5, 1.5), config),
            fill=(*color, round(18 + 30 * pulse)),
        )

    blur_radius = max(0.35, config.width / 1500.0)
    layer = Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(blur_radius)), sharp)
    return _clip_layer_to_motion_bounds(
        layer,
        motion_support_mask(calibration, config),
        calibration,
        config,
    )


def _distant_equipment_layer(
    config: RenderConfig,
    phase: float,
    calibration: ScreenCalibration,
) -> Image.Image:
    glow = Image.new("RGBA", (config.width, config.height), (0, 0, 0, 0))
    sharp = Image.new("RGBA", glow.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    sharp_draw = ImageDraw.Draw(sharp)

    for start, end, color, offset in DISTANT_EQUIPMENT_PATHS:
        travel = 0.5 + 0.5 * math.sin(phase + offset)
        x = start[0] + (end[0] - start[0]) * travel
        y = start[1] + (end[1] - start[1]) * travel
        center = (x, y)
        intensity = 0.5 + 0.5 * math.sin(phase * 2.0 + offset + 0.7)
        glow_draw.ellipse(
            _scaled_ellipse_box(center, (5.0, 4.0), config),
            fill=(*color, round(3 + 6 * intensity)),
        )
        sharp_draw.ellipse(
            _scaled_ellipse_box(center, (1.2, 1.2), config),
            fill=(*color, round(12 + 18 * intensity)),
        )

    layer = Image.alpha_composite(
        glow.filter(ImageFilter.GaussianBlur(max(0.3, config.width / 1800.0))),
        sharp,
    )
    return _clip_layer_to_motion_bounds(
        layer,
        motion_support_mask(calibration, config),
        calibration,
        config,
    )


def allowed_motion_mask(calibration: ScreenCalibration, config: RenderConfig) -> np.ndarray:
    return np.asarray(motion_support_mask(calibration, config), dtype=np.uint8) > 0


def render_frame(
    base: Image.Image,
    frame_index: int,
    config: RenderConfig,
    calibration: ScreenCalibration,
) -> Image.Image:
    phase = math.tau * (frame_index % config.frame_count) / config.frame_count
    frame = base.convert("RGBA")
    frame = Image.alpha_composite(frame, _practical_light_layer(config, phase, calibration))
    frame = Image.alpha_composite(frame, _status_light_layer(config, phase, calibration))
    frame = Image.alpha_composite(frame, _distant_equipment_layer(config, phase, calibration))
    return frame.convert("RGB")


def frame_hash(frame: Image.Image) -> str:
    return hashlib.sha256(frame.tobytes()).hexdigest()


def _rms(difference: np.ndarray) -> float:
    if difference.size == 0:
        return 0.0
    values = difference.astype(np.float32)
    return float(np.sqrt(np.mean(values * values)))


def encode_outputs(
    base: Image.Image,
    config: RenderConfig,
    calibration: ScreenCalibration,
    ffmpeg: Path,
    output_webm: Path,
    output_mp4: Path,
) -> dict[str, object]:
    command = [
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s:v", f"{config.width}x{config.height}",
        "-r", str(config.fps), "-i", "pipe:0", "-an",
        "-map", "0:v:0", "-c:v", "libvpx-vp9", "-crf", "24", "-b:v", "0",
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

    allowed = allowed_motion_mask(calibration, config)
    screens = screen_masks(calibration, config)
    combined_screens = np.zeros((config.height, config.width), dtype=bool)
    for mask in screens.values():
        combined_screens |= mask

    base_pixels = np.asarray(base, dtype=np.int16)
    previous: np.ndarray | None = None
    adjacent_rms: list[float] = []
    fixed_region_max_error = 0
    screen_interior_max_error = 0
    screen_rms_by_id: dict[str, list[float]] = {screen_id: [] for screen_id in screens}
    changed_pixels = np.zeros((config.height, config.width), dtype=bool)
    first_pixels: np.ndarray | None = None
    last_pixels: np.ndarray | None = None
    try:
        for frame_index in range(config.frame_count):
            frame = render_frame(base, frame_index, config, calibration)
            pixels = np.asarray(frame, dtype=np.uint8)
            delta = np.abs(pixels.astype(np.int16) - base_pixels)
            changed_pixels |= np.any(delta > 0, axis=2)
            fixed_region_max_error = max(
                fixed_region_max_error,
                int(delta[~allowed].max(initial=0)),
            )
            screen_interior_max_error = max(
                screen_interior_max_error,
                int(delta[combined_screens].max(initial=0)),
            )
            for screen_id, mask in screens.items():
                screen_rms_by_id[screen_id].append(_rms(delta[mask]))
            if previous is not None:
                adjacent_rms.append(_rms(pixels.astype(np.float32) - previous.astype(np.float32)))
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

    seam_rms = _rms(last_pixels.astype(np.float32) - first_pixels.astype(np.float32))
    return {
        "fixed_region_max_error": fixed_region_max_error,
        "screen_interior_max_error": screen_interior_max_error,
        "screen_stability": {
            screen_id: {
                "rms_mean_vs_source": float(np.mean(values)),
                "rms_max_vs_source": float(np.max(values)),
            }
            for screen_id, values in screen_rms_by_id.items()
        },
        "adjacent_rms_mean": float(np.mean(adjacent_rms)),
        "adjacent_rms_max": float(np.max(adjacent_rms)),
        "seam_rms": seam_rms,
        "allowed_motion_coverage_percent": float(allowed.mean() * 100.0),
        "actual_changed_pixel_coverage_percent": float(changed_pixels.mean() * 100.0),
    }


def decoded_motion_stats(
    path: Path,
    ffmpeg: Path,
    config: RenderConfig,
    calibration: ScreenCalibration,
) -> dict[str, object]:
    command = [
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(path),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    if process.stdout is None:
        raise RuntimeError("FFmpeg decode stdout was not created")

    masks = screen_masks(calibration, config)
    frame_bytes = config.width * config.height * 3
    first: np.ndarray | None = None
    previous: np.ndarray | None = None
    last: np.ndarray | None = None
    adjacent_rms: list[float] = []
    screen_rms: dict[str, list[float]] = {screen_id: [] for screen_id in masks}
    screen_max_error: dict[str, int] = {screen_id: 0 for screen_id in masks}
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
                adjacent_rms.append(_rms(pixels.astype(np.float32) - previous.astype(np.float32)))
            if first is not None:
                temporal_delta = pixels.astype(np.int16) - first.astype(np.int16)
                for screen_id, mask in masks.items():
                    values = temporal_delta[mask]
                    screen_rms[screen_id].append(_rms(values))
                    screen_max_error[screen_id] = max(
                        screen_max_error[screen_id],
                        int(np.abs(values).max(initial=0)),
                    )
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

    return {
        "decoded_adjacent_rms_mean": float(np.mean(adjacent_rms)),
        "decoded_adjacent_rms_max": float(np.max(adjacent_rms)),
        "decoded_seam_rms": _rms(last.astype(np.float32) - first.astype(np.float32)),
        "decoded_screen_stability": {
            screen_id: {
                "temporal_rms_mean": float(np.mean(values)),
                "temporal_rms_max": float(np.max(values)),
                "temporal_max_error": screen_max_error[screen_id],
            }
            for screen_id, values in screen_rms.items()
        },
    }


def probe_media(
    path: Path,
    ffprobe: Path,
    ffmpeg: Path,
    config: RenderConfig,
    calibration: ScreenCalibration,
) -> dict[str, object]:
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
    report.update(decoded_motion_stats(path, ffmpeg, config, calibration))
    return report


def _percent(value: float, total: float) -> float:
    return round(value * 100.0 / total, 6)


def _quad_report(quad: Quad, config: RenderConfig) -> dict[str, object]:
    scaled = _scaled_polygon(quad, config)
    normalized = [
        [round(x / REFERENCE_SIZE[0], 8), round(y / REFERENCE_SIZE[1], 8)]
        for x, y in quad
    ]
    left = min(x for x, _ in quad)
    top = min(y for _, y in quad)
    right = max(x for x, _ in quad)
    bottom = max(y for _, y in quad)
    width = max(right - left, 1.0)
    height = max(bottom - top, 1.0)
    clip_path = [
        [round((x - left) * 100.0 / width, 4), round((y - top) * 100.0 / height, 4)]
        for x, y in quad
    ]
    return {
        "reference_pixels": [[round(x, 3), round(y, 3)] for x, y in quad],
        "output_pixels": [[x, y] for x, y in scaled],
        "normalized": normalized,
        "css_box_percent": {
            "left": _percent(left, REFERENCE_SIZE[0]),
            "top": _percent(top, REFERENCE_SIZE[1]),
            "width": _percent(width, REFERENCE_SIZE[0]),
            "height": _percent(height, REFERENCE_SIZE[1]),
        },
        "css_clip_path_percent": clip_path,
        "output_size": [config.width, config.height],
    }


def screen_geometry_report(
    calibration: ScreenCalibration,
    config: RenderConfig,
) -> dict[str, object]:
    return {
        "reference_size": [calibration.source_width, calibration.source_height],
        "coordinate_system": calibration.coordinate_system,
        "point_order": list(calibration.point_order),
        "screens": {
            screen.screen_id: {
                "outer": _quad_report(screen.outer_quad, config),
                "content": _quad_report(screen.content_quad, config),
            }
            for screen in calibration.screens
        },
    }


def save_calibration_preview(
    base: Image.Image,
    calibration: ScreenCalibration,
    config: RenderConfig,
    path: Path,
) -> None:
    preview = base.convert("RGB").copy()
    draw = ImageDraw.Draw(preview)
    line_width = max(2, round(config.width / 640))
    for screen in calibration.screens:
        outer = _scaled_polygon(screen.outer_quad, config)
        content = _scaled_polygon(screen.content_quad, config)
        draw.line(outer + [outer[0]], fill=(236, 177, 72), width=line_width, joint="curve")
        draw.line(content + [content[0]], fill=(81, 213, 187), width=line_width, joint="curve")
        for index, point in enumerate(content):
            radius = max(2, line_width + 1)
            draw.ellipse(
                (point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius),
                fill=(81, 213, 187),
            )
            draw.text((point[0] + radius + 1, point[1] - radius), str(index + 1), fill=(240, 244, 242))
        label_position = (content[0][0], max(2, content[0][1] - 12))
        draw.text(label_position, f"{screen.screen_id} content quad", fill=(81, 213, 187))
    preview.save(path, format="PNG", optimize=True)


def save_sample_sheet(
    base: Image.Image,
    calibration: ScreenCalibration,
    config: RenderConfig,
    path: Path,
) -> list[int]:
    frame_indices = [0, config.frame_count // 4, config.frame_count // 2, config.frame_count * 3 // 4]
    sheet = Image.new("RGB", (config.width * 2, config.height * 2), (3, 5, 6))
    draw = ImageDraw.Draw(sheet)
    for index, frame_index in enumerate(frame_indices):
        frame = render_frame(base, frame_index, config, calibration)
        left = (index % 2) * config.width
        top = (index // 2) * config.height
        sheet.paste(frame, (left, top))
        draw.rectangle((left, top, left + 82, top + 18), fill=(3, 5, 6))
        draw.text((left + 6, top + 4), f"frame {frame_index + 1:03d}", fill=(232, 236, 235))
    sheet.save(path, format="WEBP", quality=90, method=6)
    return frame_indices


def validate_media_contract(
    media: Sequence[Mapping[str, object]],
    config: RenderConfig,
) -> None:
    for item in media:
        if item["frames"] != config.frame_count:
            raise RuntimeError(
                f"{item['file']} has {item['frames']} frames; expected {config.frame_count}"
            )
        if abs(float(item["duration_seconds"]) - DURATION_SECONDS) > 0.001:
            raise RuntimeError(f"{item['file']} duration is not exactly {DURATION_SECONDS:.3f} seconds")
        if item["frame_rate"] != f"{config.fps}/1":
            raise RuntimeError(
                f"{item['file']} frame rate is {item['frame_rate']}; expected {config.fps}/1"
            )
        stability = item["decoded_screen_stability"]
        if not isinstance(stability, dict):
            raise RuntimeError(f"{item['file']} is missing decoded screen stability metrics")
        for screen_id, metrics in stability.items():
            if not isinstance(metrics, dict):
                raise RuntimeError(f"{item['file']} has invalid metrics for {screen_id}")
            if float(metrics["temporal_rms_max"]) > 2.5:
                raise RuntimeError(
                    f"{item['file']} decoded {screen_id} screen drift exceeds RMS 2.5"
                )
            if int(metrics["temporal_max_error"]) > 32:
                raise RuntimeError(
                    f"{item['file']} decoded {screen_id} screen drift exceeds 32 levels"
                )


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
    if not args.screen_calibration.is_file():
        raise FileNotFoundError(args.screen_calibration)
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

    calibration = load_screen_calibration(args.screen_calibration)
    base = load_base(args.source, config)
    frame_1 = render_frame(base, 0, config, calibration)
    frame_121 = render_frame(base, config.frame_count, config, calibration)
    frame_1_hash = frame_hash(frame_1)
    frame_121_hash = frame_hash(frame_121)
    if frame_1_hash != frame_121_hash:
        raise RuntimeError("Loop endpoint mismatch: generated frame 121 differs from frame 1")

    frame_1.save(poster_path, format="WEBP", quality=90, method=6)
    proof_artifacts: dict[str, object] = {}
    if args.mode == "proof":
        calibration_preview_path = output_dir / f"{basename}-screen-calibration.png"
        sample_sheet_path = output_dir / f"{basename}-samples.webp"
        save_calibration_preview(base, calibration, config, calibration_preview_path)
        sample_frames = save_sample_sheet(base, calibration, config, sample_sheet_path)
        proof_artifacts = {
            "screen_calibration_preview": calibration_preview_path.name,
            "sample_sheet": sample_sheet_path.name,
            "sample_frames": [frame + 1 for frame in sample_frames],
        }

    source_validation = encode_outputs(
        base,
        config,
        calibration,
        args.ffmpeg,
        webm_path,
        mp4_path,
    )
    media = [
        probe_media(webm_path, ffprobe, args.ffmpeg, config, calibration),
        probe_media(mp4_path, ffprobe, args.ffmpeg, config, calibration),
    ]
    validate_media_contract(media, config)

    if source_validation["fixed_region_max_error"] != 0:
        raise RuntimeError("Pixels outside the approved environment-light masks changed")
    if source_validation["screen_interior_max_error"] != 0:
        raise RuntimeError("Generated screen interiors changed")
    if float(source_validation["allowed_motion_coverage_percent"]) > 3.0:
        raise RuntimeError("Approved motion masks cover more than 3% of the frame")
    if float(source_validation["seam_rms"]) > float(source_validation["adjacent_rms_max"]) * 1.25 + 0.05:
        raise RuntimeError("The generated loop seam is a motion spike")

    report = {
        "contract": {
            "fps": config.fps,
            "frames_encoded": config.frame_count,
            "duration_seconds": DURATION_SECONDS,
            "loop_endpoint": "generated frame 121 equals generated frame 1",
            "camera": "fixed source frame",
            "geometry": "fixed source photograph; no generated project content",
            "screens": "source black/reflection pixels remain unchanged in every generated frame",
            "motion": "localized practical lights, status lamps, and distant equipment indicators only",
        },
        "source": str(args.source.resolve()),
        "source_sha256": file_sha256(args.source),
        "screen_calibration": str(args.screen_calibration.resolve()),
        "screen_calibration_sha256": file_sha256(args.screen_calibration),
        "screen_geometry": screen_geometry_report(calibration, config),
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
        "proof_artifacts": proof_artifacts,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (BrokenPipeError, KeyboardInterrupt):
        sys.exit(130)
