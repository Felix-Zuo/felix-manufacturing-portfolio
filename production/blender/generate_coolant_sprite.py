"""Generate a seamless layered coolant-film sprite for the grinding proof."""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps


FRAME_COUNT = 96
SIZE = 512
SUPERSAMPLE = 2
CANVAS = SIZE * SUPERSAMPLE
TAU = math.tau


@dataclass(frozen=True)
class Droplet:
    phase: float
    frequency: int
    x_velocity: float
    y_velocity: float
    gravity: float
    width: float
    alpha: int
    trail: float
    wobble: float
    wobble_phase: float


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--plate",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "assets"
        / "generated"
        / "coolant-impact-plate-v1.png",
    )
    return parser.parse_args()


def _scale(value: float) -> float:
    return value * SUPERSAMPLE


def _point(x: float, y: float) -> tuple[float, float]:
    return _scale(x), _scale(y)


def _quadratic(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    progress: float,
) -> tuple[float, float]:
    inverse = 1.0 - progress
    return (
        inverse * inverse * start[0]
        + 2.0 * inverse * progress * control[0]
        + progress * progress * end[0],
        inverse * inverse * start[1]
        + 2.0 * inverse * progress * control[1]
        + progress * progress * end[1],
    )


def _curve_points(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    *,
    count: int = 36,
) -> list[tuple[float, float]]:
    return [
        _point(*_quadratic(start, control, end, index / (count - 1)))
        for index in range(count)
    ]


def _droplets() -> list[Droplet]:
    rng = random.Random(20260722)
    return [
        Droplet(
            phase=rng.random(),
            frequency=rng.choice((1, 1, 1, 2, 2, 3)),
            x_velocity=rng.triangular(-54.0, 188.0, 72.0),
            y_velocity=rng.uniform(82.0, 238.0),
            gravity=rng.uniform(32.0, 98.0),
            width=rng.uniform(0.42, 1.45),
            alpha=rng.randint(28, 96),
            trail=rng.uniform(0.018, 0.050),
            wobble=rng.uniform(0.5, 3.8),
            wobble_phase=rng.uniform(0.0, TAU),
        )
        for _ in range(128)
    ]


def _load_turbulence(path: Path) -> Image.Image:
    source = Image.open(path).convert("RGB")
    source = ImageOps.fit(source, (CANVAS, CANVAS), method=Image.Resampling.LANCZOS)
    aligned = Image.new("RGB", (CANVAS, CANVAS), (0, 0, 0))
    aligned.paste(source, (-round(_scale(54.0)), 0))
    source = aligned
    luminance = ImageEnhance.Contrast(ImageOps.grayscale(source)).enhance(1.15)
    alpha = luminance.point(
        lambda value: 0 if value < 14 else min(44, round((value - 14) * 0.18))
    )
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(
        (
            _scale(116.0),
            _scale(82.0),
            _scale(430.0),
            _scale(438.0),
        ),
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius=_scale(34.0)))
    alpha = ImageChops.multiply(alpha, mask)
    tone = luminance.point(lambda value: min(255, round(value * 0.82 + 28)))
    return Image.merge("RGBA", (tone, tone, tone, alpha))


def _animate_turbulence(plate: Image.Image, time: float) -> Image.Image:
    angle = 0.35 * math.sin(TAU * time)
    shifted = plate.rotate(
        angle,
        center=_point(256.0, 153.0),
        resample=Image.Resampling.BICUBIC,
    )
    x = round(_scale(1.8 * math.sin(TAU * time + 0.4)))
    y = round(_scale(1.1 * math.sin(TAU * time + 1.3)))
    moved = Image.new("RGBA", shifted.size, (0, 0, 0, 0))
    moved.alpha_composite(shifted, (x, y))
    return moved


def _draw_continuous_film(time: float) -> Image.Image:
    layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    origin = (256.0, 150.0)

    # Three overlapping translucent ribbons read as a liquid sheet dragged
    # tangentially by the rotating raceway instead of a radial particle fan.
    ribbons = (
        ((258.0, 153.0), (300.0, 214.0), (322.0, 348.0), 15, 44, 0.0),
        ((252.0, 154.0), (244.0, 238.0), (278.0, 414.0), 12, 36, 1.7),
        ((262.0, 156.0), (314.0, 194.0), (350.0, 268.0), 4, 18, 3.1),
    )
    for start, control, end, width, alpha, phase in ribbons:
        drift = 2.0 * math.sin(TAU * time + phase)
        adjusted_control = (control[0] + drift, control[1])
        draw.line(
            _curve_points(start, adjusted_control, end),
            fill=(202, 222, 214, alpha),
            width=round(_scale(width)),
            joint="curve",
        )
        for filament in range(7):
            offset = (filament - 3) * width * 0.13
            filament_start = (start[0] + offset * 0.18, start[1])
            filament_control = (
                adjusted_control[0] + offset,
                adjusted_control[1] + math.sin(TAU * time + filament) * 2.2,
            )
            filament_end = (end[0] + offset * 1.3, end[1])
            draw.line(
                _curve_points(filament_start, filament_control, filament_end),
                fill=(218, 234, 228, 13 + (filament % 3) * 5),
                width=max(1, round(_scale(width * 0.12))),
            )

        # Highlight packets travel down the stable sheet. Their random phases
        # and co-prime rates avoid the former six-times-per-loop sync pulse.
        for packet in range(5):
            rate = 1 + (packet % 3)
            progress = (time * rate + packet * 0.217 + phase * 0.071) % 1.0
            half = 0.025 + packet * 0.002
            a = _quadratic(start, adjusted_control, end, max(0.0, progress - half))
            b = _quadratic(start, adjusted_control, end, min(1.0, progress + half))
            envelope = math.sin(math.pi * progress) ** 0.65
            draw.line(
                (_point(*a), _point(*b)),
                fill=(226, 238, 233, round((28 + packet * 3) * envelope)),
                width=max(1, round(_scale(width * 0.16))),
            )

    # A compact impact film remains attached to the contact point. It is
    # deliberately soft and low-alpha so it cannot become a white frozen blob.
    impact = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    impact_draw = ImageDraw.Draw(impact, "RGBA")
    pulse = 1.0 + 0.045 * math.sin(TAU * time)
    for index in range(7):
        angle = index * 2.3999632297 + 0.18 * math.sin(TAU * time + index)
        radius_x = (11.0 + index * 1.9) * pulse
        radius_y = (5.0 + index * 1.1) * pulse
        x = origin[0] + math.cos(angle) * (5.0 + index * 1.1)
        y = origin[1] + math.sin(angle) * (3.0 + index * 0.7)
        impact_draw.ellipse(
            (
                _scale(x - radius_x),
                _scale(y - radius_y),
                _scale(x + radius_x),
                _scale(y + radius_y),
            ),
            fill=(205, 224, 217, 12 + index * 2),
        )
    impact = impact.filter(ImageFilter.GaussianBlur(radius=_scale(5.2)))
    layer = Image.alpha_composite(layer, impact)

    # Fine rivulets keep moving under gravity after the impact sheet passes.
    rivulet_draw = ImageDraw.Draw(layer, "RGBA")
    for index, x in enumerate((233.0, 253.0, 276.0, 298.0, 321.0)):
        sway = 3.0 * math.sin(TAU * time + index * 0.83)
        end_y = 438.0 + index * 9.0
        path = _curve_points(
            (x, 238.0),
            (x + sway + (index - 2) * 3.0, 338.0),
            (x + sway * 0.35, end_y),
            count=28,
        )
        rivulet_draw.line(
            path,
            fill=(188, 207, 201, 9 + (index % 2) * 5),
            width=max(1, round(_scale(1.1 + (index % 3) * 0.3))),
        )
        bead_progress = (time * (1 + index % 2) + index * 0.173) % 1.0
        bead = _quadratic(
            (x, 238.0),
            (x + sway + (index - 2) * 3.0, 338.0),
            (x + sway * 0.35, end_y),
            bead_progress,
        )
        radius = _scale(2.0 + (index % 3) * 0.5)
        bx, by = _point(*bead)
        rivulet_draw.ellipse(
            (bx - radius, by - radius * 1.4, bx + radius, by + radius * 1.4),
            fill=(218, 230, 226, 34),
        )

    return layer.filter(ImageFilter.GaussianBlur(radius=_scale(1.15)))


def _draw_mist(time: float) -> Image.Image:
    layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    rng = random.Random(14142)
    for index in range(18):
        phase = rng.random()
        frequency = rng.choice((1, 1, 2, 3))
        progress = (time * frequency + phase) % 1.0
        fade = math.sin(math.pi * progress) ** 1.8
        x = 256.0 + rng.uniform(-38.0, 82.0) + progress * rng.uniform(-12.0, 30.0)
        y = 154.0 + rng.uniform(-22.0, 48.0) + progress * rng.uniform(18.0, 90.0)
        radius = _scale(rng.uniform(8.0, 24.0) * (0.7 + progress * 0.7))
        cx, cy = _point(x, y)
        draw.ellipse(
            (cx - radius, cy - radius * 0.62, cx + radius, cy + radius * 0.62),
            fill=(198, 214, 208, round(rng.randint(5, 14) * fade)),
        )
    return layer.filter(ImageFilter.GaussianBlur(radius=_scale(11.0)))


def _draw_droplets(time: float, droplets: list[Droplet]) -> Image.Image:
    layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    origin_x = 256.0
    origin_y = 153.0

    def position(particle: Droplet, life: float) -> tuple[float, float]:
        return (
            origin_x
            + particle.x_velocity * life
            + particle.wobble
            * math.sin(TAU * time + particle.wobble_phase)
            * math.sin(math.pi * life),
            origin_y + particle.y_velocity * life + particle.gravity * life * life,
        )

    for particle in droplets:
        cycle = (time * particle.frequency + particle.phase) % 1.0
        life = cycle / 0.68
        if life >= 1.0:
            continue
        fade = math.sin(math.pi * life) ** 2.2
        x, y = position(particle, life)
        previous = max(0.0, life - particle.trail)
        px, py = position(particle, previous)
        alpha = max(1, round(particle.alpha * fade))
        width = max(1, round(_scale(particle.width * (0.55 + fade * 0.5))))
        draw.line(
            (_point(px, py), _point(x, y)),
            fill=(207, 223, 217, alpha),
            width=width,
        )
        radius = _scale(max(0.35, particle.width * (0.35 + fade * 0.42)))
        cx, cy = _point(x, y)
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=(221, 233, 229, min(132, alpha + 14)),
        )
    return layer


def _draw_frame(
    frame: int,
    droplets: list[Droplet],
    turbulence: Image.Image,
) -> Image.Image:
    time = frame / FRAME_COUNT
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    image = Image.alpha_composite(image, _draw_mist(time))
    image = Image.alpha_composite(image, _animate_turbulence(turbulence, time))
    image = Image.alpha_composite(image, _draw_continuous_film(time))
    image = Image.alpha_composite(image, _draw_droplets(time, droplets))
    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main() -> None:
    args = _args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    droplets = _droplets()
    turbulence = _load_turbulence(args.plate.resolve())
    selected: list[Image.Image] = []
    for frame in range(FRAME_COUNT):
        image = _draw_frame(frame, droplets, turbulence)
        image.save(output / f"coolant_{frame + 1:04d}.png", optimize=True)
        if frame in {0, 24, 48, 72}:
            selected.append(image.copy())

    contact_sheet = Image.new("RGB", (SIZE * 2, SIZE * 2), (0, 0, 0))
    for index, image in enumerate(selected):
        black = Image.new("RGBA", image.size, (0, 0, 0, 255))
        black.alpha_composite(image)
        contact_sheet.paste(
            black.convert("RGB"),
            ((index % 2) * SIZE, (index // 2) * SIZE),
        )
    contact_sheet.save(output / "contact-sheet.png", optimize=True)
    manifest = {
        "frames": FRAME_COUNT,
        "size": [SIZE, SIZE],
        "loop": "phase-wrapped film, mist, rivulets, and droplets",
        "seed": 20260722,
        "origin_uv": [0.50, 0.299],
        "practical_turbulence_reference": str(args.plate.resolve()),
        "layers": [
            "continuous tangential contact film",
            "traveling film highlights",
            "gravity rivulets",
            "asynchronous fine spray",
            "low-alpha mist",
        ],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print("SUM_COOLANT_SPRITE=" + json.dumps(manifest))


if __name__ == "__main__":
    main()
