"""Generate the exhaust smoke puff animation used by the tank's LeavesTrails.

Run from the repository root:

    python3 tools/make_smoke_sheet.py

Each frame is one puff at a later point in its life: it grows, drifts upward,
lightens as it disperses and fades out. LeavesTrails spawns the sequence as a
one-shot SpriteEffect at a fixed world position, so the drift has to be baked
into the frames rather than coming from actor movement.

Deliberately procedural rather than rendered: volumetric smoke is slow to render
and, at a 32px frame, soft blurred lobes read just as well.
"""
import random

from PIL import Image, ImageDraw, ImageFilter, PngImagePlugin

FRAME = 32
FRAMES = 12
SS = 4  # Supersample factor, downscaled with LANCZOS for soft edges.
OUT = "mods/fracturedsteel/sequences/assets/smoke.png"

PEAK_ALPHA = 235
BIRTH_COLOUR = (44, 42, 40)  # Sooty diesel exhaust.
DEATH_COLOUR = (92, 92, 96)  # Dispersed, but still darker than the terrain.

# Fixed lobe layout so the sheet regenerates byte-identically.
random.seed(7)
LOBES = [(random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0), random.uniform(0.55, 1.0))
         for _ in range(4)]


def lerp(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def puff(t):
    """One frame of the puff's life, t running 0 (fresh) to 1 (gone)."""
    size = FRAME * SS
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)

    radius = 3.5 + t * 5.5
    rise = t * 6.0
    for lx, ly, lr in LOBES:
        r = radius * lr * SS
        cx = (FRAME / 2.0 + lx * radius * 0.55) * SS
        cy = (FRAME / 2.0 - rise + ly * radius * 0.40) * SS
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)

    # Blur softens the edge, but too much of it also hollows out the core and the
    # puff stops registering against the terrain. Keep it tight.
    mask = mask.filter(ImageFilter.GaussianBlur(radius * SS * 0.20))
    mask = mask.resize((FRAME, FRAME), Image.LANCZOS)

    fade = PEAK_ALPHA * (1.0 - t) ** 1.1
    alpha = mask.point(lambda v: int(v * fade / 255.0))

    frame = Image.new("RGBA", (FRAME, FRAME), lerp(BIRTH_COLOUR, DEATH_COLOUR, t ** 1.5) + (0,))
    frame.putalpha(alpha)
    return frame


def main():
    sheet = Image.new("RGBA", (FRAME * FRAMES, FRAME), (0, 0, 0, 0))
    for i in range(FRAMES):
        sheet.paste(puff(i / (FRAMES - 1.0)), (i * FRAME, 0))

    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{FRAME},{FRAME}")
    meta.add_text("FrameAmount", str(FRAMES))
    sheet.save(OUT, pnginfo=meta)
    print(f"wrote {OUT} {sheet.size} frames={FRAMES}")
    peaks = [sheet.crop((i * FRAME, 0, (i + 1) * FRAME, FRAME)).getchannel("A").getextrema()[1]
             for i in range(FRAMES)]
    print("peak alpha per frame:", peaks)


if __name__ == "__main__":
    main()
