"""Sparks on Paladin impacts. Three variants in one sheet.

Run from the repository root:

    python3 tools/make_spark_sheet.py

`idle` is the original star. `left` / `right` are yellow streaks flying
up-left and up-right. Greyscale turns them white-hot; thin lines still read.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, PngImagePlugin

FRAME = 64
FRAMES = 8
SS = 4
OUT = "mods/fracturedsteel/sequences/assets/sparks.png"
YELLOW = (255, 230, 140)
TIP = (255, 255, 220)


def cluster(seed, heading, spread, count=12):
    rng = random.Random(seed)
    sparks = []
    for _ in range(count):
        ang = heading + rng.uniform(-spread, spread)
        speed = rng.uniform(11, 24)
        length = rng.uniform(5, 11)
        thick = rng.uniform(0.7, 1.5)
        sparks.append((ang, speed, length, thick))
    return sparks


# Screen +Y is down. Up-left is ~225°, up-right is ~315°.
STAR = cluster(11, 0, math.pi, count=14)
# Rebuild the original full-circle star with the same seed as before.
random.seed(11)
STAR = []
for _ in range(14):
    STAR.append((
        random.uniform(0, 2 * math.pi),
        random.uniform(10, 22),
        random.uniform(4, 9),
        random.uniform(0.7, 1.4),
    ))

LEFT = cluster(21, math.radians(225), math.radians(28), count=13)
RIGHT = cluster(22, math.radians(315), math.radians(28), count=13)


def render(sparks, i, flash):
    t = i / (FRAMES - 1.0)
    size = FRAME * SS
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2

    if flash and i == 0:
        draw.ellipse((cx - 3 * SS, cy - 3 * SS, cx + 3 * SS, cy + 3 * SS), fill=(255, 255, 230, 255))

    alpha = int(255 * (1.0 - t) ** 0.7)
    for ang, speed, length, thick in sparks:
        dist = (2.0 + speed * t) * SS
        half = (length * (1.0 - 0.35 * t)) * SS
        x0 = cx + math.cos(ang) * max(0, dist - half)
        y0 = cy + math.sin(ang) * max(0, dist - half)
        x1 = cx + math.cos(ang) * (dist + half)
        y1 = cy + math.sin(ang) * (dist + half)
        w = max(1, int(thick * SS * (1.0 - 0.4 * t)))
        draw.line((x0, y0, x1, y1), fill=YELLOW + (alpha,), width=w)
        draw.ellipse((x1 - w, y1 - w, x1 + w, y1 + w), fill=TIP + (alpha,))

    img = img.filter(ImageFilter.GaussianBlur(0.6 * SS))
    return img.resize((FRAME, FRAME), Image.LANCZOS)


def main():
    variants = (STAR, LEFT, RIGHT)
    total = FRAMES * len(variants)
    sheet = Image.new("RGBA", (FRAME * FRAMES, FRAME * len(variants)), (0, 0, 0, 0))
    # Row-major: one row per variant so Start = row * 8 with 8 frames per row.
    for v, sparks in enumerate(variants):
        for i in range(FRAMES):
            f = render(sparks, i, flash=(v == 0))
            sheet.paste(f, (i * FRAME, v * FRAME), f)

    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{FRAME},{FRAME}")
    meta.add_text("FrameAmount", str(total))
    sheet.save(OUT, pnginfo=meta)
    print(f"wrote {OUT} {sheet.size} frames={total}")


if __name__ == "__main__":
    main()
