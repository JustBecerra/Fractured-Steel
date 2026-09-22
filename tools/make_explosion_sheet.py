"""Impact burst played on the target by CreateEffect warheads.

Run from the repository root:

    python3 tools/make_explosion_sheet.py

A short flash, then an expanding grey fireball that turns to smoke. Authored
for the greyscale palette: high contrast so it reads on units and buildings.
"""
from PIL import Image, ImageDraw, ImageFilter, PngImagePlugin

FRAME = 64
FRAMES = 10
SS = 4
OUT = "mods/fracturedsteel/sequences/assets/explosion.png"


def lerp(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def frame(i):
    t = i / (FRAMES - 1.0)
    size = FRAME * SS
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2

    # Expanding shell.
    radius = (6.0 + t * 22.0) * SS
    if i == 0:
        draw.ellipse((cx - 7 * SS, cy - 7 * SS, cx + 7 * SS, cy + 7 * SS), fill=(255, 245, 210, 255))
        draw.ellipse((cx - 3 * SS, cy - 3 * SS, cx + 3 * SS, cy + 3 * SS), fill=(255, 255, 255, 255))
    else:
        shell = lerp((210, 140, 60), (70, 68, 66), min(1.0, t * 1.2))
        alpha = int(230 * (1.0 - t * 0.75))
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=shell + (alpha,))
        # Hot core that shrinks.
        core_r = max(2 * SS, (10.0 - t * 12.0) * SS)
        core = lerp((255, 230, 140), (120, 110, 100), t)
        draw.ellipse((cx - core_r, cy - core_r, cx + core_r, cy + core_r), fill=core + (alpha,))
        # Smoke lobes drift up and out.
        for dx, dy, s in ((-0.45, 0.1, 0.55), (0.4, -0.15, 0.6), (0.05, -0.4, 0.5), (0.25, 0.35, 0.45)):
            r = radius * s
            x = cx + dx * radius * (0.4 + t)
            y = cy - t * 8 * SS + dy * radius * 0.35
            smoke = lerp((90, 86, 82), (150, 150, 152), t)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=smoke + (int(alpha * 0.85),))

    img = img.filter(ImageFilter.GaussianBlur(1.6 * SS))
    return img.resize((FRAME, FRAME), Image.LANCZOS)


def main():
    sheet = Image.new("RGBA", (FRAME * FRAMES, FRAME), (0, 0, 0, 0))
    for i in range(FRAMES):
        f = frame(i)
        sheet.paste(f, (i * FRAME, 0), f)

    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{FRAME},{FRAME}")
    meta.add_text("FrameAmount", str(FRAMES))
    sheet.save(OUT, pnginfo=meta)
    print(f"wrote {OUT} {sheet.size} frames={FRAMES}")


if __name__ == "__main__":
    main()
