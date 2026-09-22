"""Gun-smoke puff played at the Paladin barrel tip by WithMuzzleOverlay.

Run from the repository root:

    python3 tools/make_muzzle_sheet.py

Frame 0 is a bright muzzle flash; the rest is a mid-grey puff that grows
and fades. Larger and darker than the first pass so it reads at unit scale.
"""
from PIL import Image, ImageDraw, ImageFilter, PngImagePlugin

FRAME = 48
FRAMES = 8
SS = 4
OUT = "mods/fracturedsteel/sequences/assets/muzzle.png"


def lerp(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def frame(i):
    t = i / (FRAMES - 1.0)
    size = FRAME * SS
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2

    if i == 0:
        # Wide flash so the shot reads at 60px unit scale.
        draw.ellipse((cx - 10 * SS, cy - 8 * SS, cx + 10 * SS, cy + 8 * SS), fill=(255, 200, 90, 240))
        draw.ellipse((cx - 5 * SS, cy - 4 * SS, cx + 5 * SS, cy + 4 * SS), fill=(255, 240, 180, 255))
        draw.ellipse((cx - 2 * SS, cy - 2 * SS, cx + 2 * SS, cy + 2 * SS), fill=(255, 255, 240, 255))
    else:
        radius = (8.0 + t * 12.0) * SS
        rise = t * 7.0 * SS
        # Mid-grey, stays opaque through the middle frames.
        colour = lerp((96, 92, 86), (140, 140, 144), t) + (int(240 * (1.0 - t * 0.72)),)
        for dx, dy, s in ((-0.4, 0.15, 0.9), (0.35, -0.12, 1.05), (0.0, 0.28, 0.75), (0.15, -0.3, 0.65)):
            r = radius * s
            x = cx + dx * radius
            y = cy - rise + dy * radius
            draw.ellipse((x - r, y - r, x + r, y + r), fill=colour)

    img = img.filter(ImageFilter.GaussianBlur(1.4 * SS))
    return img.resize((FRAME, FRAME), Image.LANCZOS)


def main():
    sheet = Image.new("RGBA", (FRAME * FRAMES, FRAME), (0, 0, 0, 0))
    for i in range(FRAMES):
        sheet.paste(frame(i), (i * FRAME, 0), frame(i))

    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{FRAME},{FRAME}")
    meta.add_text("FrameAmount", str(FRAMES))
    sheet.save(OUT, pnginfo=meta)
    print(f"wrote {OUT} {sheet.size} frames={FRAMES}")


if __name__ == "__main__":
    main()
