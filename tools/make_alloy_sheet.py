"""Junkyard sprites: a brown pad with blinking rim lights, steel-strand mounds on top.

Run from the repository root:

    python3 tools/make_alloy_sheet.py

Writes two sheets:
  alloy.png   — pad + mound (resource layer; scrap is painted on the pad)
  junkpad.png — rim lights only, 2 frames (on / off) for the blink actor

The pad is a near-ground brown plate. Lights are a separate actor so they
can blink; painting the pad into the resource sheet keeps the scrap on top.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, PngImagePlugin

FRAME = 288
DENSITY = 4
VARIANTS = 3
SS = 2
ALLOY_OUT = "mods/fracturedsteel/sequences/assets/alloy.png"
PAD_OUT = "mods/fracturedsteel/sequences/assets/junkpad.png"

STEEL = (142, 138, 132)
STEEL_DK = (78, 74, 70)
STEEL_LT = (188, 184, 176)
BROWN = (128, 86, 52)
BROWN_DK = (82, 54, 32)
BROWN_LT = (164, 118, 72)
PAD_TOP = (118, 84, 52)
PAD_SIDE = (72, 50, 32)
PAD_EDGE = (56, 38, 24)
SHADOW = (28, 20, 14, 150)
LIGHT = (255, 252, 240)
LIGHT_GLOW = (255, 236, 180, 160)
SOCKET = (40, 32, 24)

CX = FRAME * SS / 2
CY = FRAME * SS / 2 + 18 * SS
HALF_W = 108 * SS
HALF_H = 54 * SS
# Almost ground level — a plate, not a box.
PAD_H = 0.55


def iso(x, y, z=0):
    sx = CX + (x - y) * (HALF_W / 20)
    sy = CY + (x + y) * (HALF_H / 20) - z * (HALF_H / 10)
    return sx, sy


# Screen-space centre of the deck. Mounds are authored around this, not CY.
PAD_CX, PAD_CY = iso(10, 10, PAD_H)


def lerp(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def pad_points():
    """Iso diamond of the deck, inset slightly so lights sit on the rim."""
    return [
        iso(1, 1, PAD_H),
        iso(19, 1, PAD_H),
        iso(19, 19, PAD_H),
        iso(1, 19, PAD_H),
    ]


def light_sites():
    """Corners and edge midpoints of the deck."""
    pts = [
        (1, 1), (10, 1), (19, 1),
        (19, 10), (19, 19),
        (10, 19), (1, 19),
        (1, 10),
    ]
    return [iso(x, y, PAD_H + 0.15) for x, y in pts]


def draw_pad(draw):
    """Near-ground brown plate. No lights — those are a separate overlay."""
    top = [iso(0, 0, PAD_H), iso(20, 0, PAD_H), iso(20, 20, PAD_H), iso(0, 20, PAD_H)]
    # Hairline edge so it reads as a slab, not a crate.
    draw.polygon([iso(0, 0, PAD_H), iso(20, 0, PAD_H), iso(20, 0, 0), iso(0, 0, 0)], fill=PAD_EDGE)
    draw.polygon([iso(20, 0, PAD_H), iso(20, 20, PAD_H), iso(20, 20, 0), iso(20, 0, 0)], fill=PAD_EDGE)
    draw.polygon(top, fill=PAD_TOP)
    inset = [
        iso(0.4, 0.4, PAD_H + 0.05),
        iso(19.6, 0.4, PAD_H + 0.05),
        iso(19.6, 19.6, PAD_H + 0.05),
        iso(0.4, 19.6, PAD_H + 0.05),
    ]
    draw.line(inset + [inset[0]], fill=PAD_EDGE, width=max(1, SS))

    r_socket = 1.8 * SS
    for p in light_sites():
        draw.ellipse((p[0] - r_socket, p[1] - r_socket * 0.5, p[0] + r_socket, p[1] + r_socket * 0.5), fill=SOCKET)


def draw_lights(draw, lights_on):
    r_light = 1.55 * SS
    for p in light_sites():
        if lights_on:
            glow = 4.0 * SS
            draw.ellipse((p[0] - glow, p[1] - glow * 0.5, p[0] + glow, p[1] + glow * 0.5), fill=LIGHT_GLOW)
            draw.ellipse((p[0] - r_light, p[1] - r_light * 0.5, p[0] + r_light, p[1] + r_light * 0.5), fill=LIGHT)


def mound_height(x, y, peaks, t):
    h = 0.0
    for cx, cy, rx, ry, amp in peaks:
        nx = (x - cx) / rx
        ny = (y - cy) / ry
        d2 = nx * nx + ny * ny
        if d2 < 1.0:
            h += amp * (1.0 - d2) ** 2
    return h * t


# Wider peaks, still centred on the pad so the pile stays on the deck.
PEAKS = [
    [
        (PAD_CX, PAD_CY, 72 * SS, 36 * SS, 1.0),
        (PAD_CX + 22 * SS, PAD_CY + 8 * SS, 48 * SS, 24 * SS, 0.8),
        (PAD_CX - 20 * SS, PAD_CY + 6 * SS, 46 * SS, 22 * SS, 0.75),
        (PAD_CX + 6 * SS, PAD_CY - 10 * SS, 40 * SS, 20 * SS, 0.6),
    ],
    [
        (PAD_CX + 4 * SS, PAD_CY, 74 * SS, 35 * SS, 1.0),
        (PAD_CX - 24 * SS, PAD_CY + 8 * SS, 46 * SS, 24 * SS, 0.75),
        (PAD_CX + 24 * SS, PAD_CY + 10 * SS, 44 * SS, 22 * SS, 0.7),
        (PAD_CX - 2 * SS, PAD_CY - 8 * SS, 38 * SS, 18 * SS, 0.55),
    ],
    [
        (PAD_CX - 2 * SS, PAD_CY + 2 * SS, 76 * SS, 36 * SS, 1.0),
        (PAD_CX + 26 * SS, PAD_CY - 2 * SS, 44 * SS, 22 * SS, 0.7),
        (PAD_CX - 26 * SS, PAD_CY + 8 * SS, 46 * SS, 22 * SS, 0.75),
        (PAD_CX + 8 * SS, PAD_CY + 12 * SS, 38 * SS, 18 * SS, 0.55),
    ],
]


def draw_strands(draw, peaks, t, rng):
    n = int(700 + 3200 * t)
    colors = (STEEL, STEEL_DK, STEEL_LT, BROWN, BROWN_DK, BROWN_LT)
    tries = 0
    drawn = 0
    while drawn < n and tries < n * 8:
        tries += 1
        x = rng.uniform(PAD_CX - 78 * SS, PAD_CX + 78 * SS)
        y = rng.uniform(PAD_CY - 40 * SS, PAD_CY + 40 * SS)
        h = mound_height(x, y, peaks, t)
        if h < 0.06:
            continue
        angle = rng.choice((0.15, -0.15, 2.0, 2.2, 1.0, -1.0)) + rng.uniform(-0.25, 0.25)
        length = (8 + h * 12) * SS
        steps = 3
        # Taller pile, still rooted on the plate.
        lift = h * 32 * SS
        pts = []
        px, py = x, y
        for i in range(steps):
            a = angle + rng.uniform(-0.2, 0.2)
            px += math.cos(a) * length / steps
            py += math.sin(a) * length / steps * 0.5
            pts.append((px, py - lift))
        if len(pts) < 2:
            continue
        color = colors[rng.randrange(len(colors))]
        width = 1 if h < 0.3 else max(1, int(round(SS * (0.6 + h))))
        draw.line(pts, fill=color, width=width)
        drawn += 1


def draw_mound_shadow(peaks, t):
    """Ground shadow in the mound's footprint, cast slightly down-right."""
    size = FRAME * SS
    sh = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pix = sh.load()
    # Shadow is drawn at (+ox, +oy) from the mound. Negative oy is screen-up,
    # which is north / behind the pile on this camera.
    ox, oy = 0, -26 * SS
    step = 2
    for y in range(0, size, step):
        for x in range(0, size, step):
            sx = PAD_CX + (x - ox - PAD_CX) * 0.78
            sy = PAD_CY + (y - oy - PAD_CY) * 0.78
            h = mound_height(sx, sy, peaks, t)
            if h < 0.025:
                continue
            a = int(80 + 100 * min(1.0, h * 1.2))
            for dy in range(step):
                for dx in range(step):
                    if x + dx < size and y + dy < size:
                        pix[x + dx, y + dy] = (28, 20, 14, min(210, a))
    return sh.filter(ImageFilter.GaussianBlur(2.6 * SS))


def draw_mound_blob(draw, peaks, t):
    """Soft under-fill so the strands sit on a mass, not on air."""
    size = FRAME * SS
    blob = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pix = blob.load()
    step = 2
    for y in range(0, size, step):
        for x in range(0, size, step):
            h = mound_height(x, y, peaks, t)
            if h < 0.06:
                continue
            shade = lerp(BROWN_DK, STEEL, min(1.0, h))
            a = int(40 + 90 * min(1.0, h))
            yy = int(y - h * 28 * SS)
            for dy in range(step):
                for dx in range(step):
                    if x + dx < size and 0 <= yy + dy < size:
                        pix[x + dx, yy + dy] = shade + (a,)
    return blob.filter(ImageFilter.GaussianBlur(1.2 * SS))


def scrap_frame(variant, density):
    rng = random.Random(100 + variant * 17 + density)
    t = 0.28 + 0.72 * (density / (DENSITY - 1))
    size = FRAME * SS
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    peaks = PEAKS[variant]
    img = Image.alpha_composite(img, draw_mound_shadow(peaks, t))
    draw = ImageDraw.Draw(img)
    draw_pad(draw)
    blob = draw_mound_blob(None, peaks, t)
    img = Image.alpha_composite(img, blob)
    draw = ImageDraw.Draw(img)
    draw_strands(draw, peaks, t, rng)
    draw_strands(draw, peaks, t * 0.35, rng)
    img = img.filter(ImageFilter.GaussianBlur(0.2 * SS))
    return img.resize((FRAME, FRAME), Image.LANCZOS)


def lights_frame(lights_on):
    size = FRAME * SS
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_lights(draw, lights_on)
    img = img.filter(ImageFilter.GaussianBlur(0.15 * SS))
    return img.resize((FRAME, FRAME), Image.LANCZOS)


def save_sheet(path, frames, frame_w, frame_h):
    sheet = Image.new("RGBA", (frame_w * len(frames), frame_h), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        sheet.paste(im, (i * frame_w, 0), im)
    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{frame_w},{frame_h}")
    meta.add_text("FrameAmount", str(len(frames)))
    sheet.save(path, pnginfo=meta)
    print(f"wrote {path} {sheet.size}")


def main():
    scraps = []
    for v in range(VARIANTS):
        for d in range(DENSITY):
            scraps.append(scrap_frame(v, d))
    save_sheet(ALLOY_OUT, scraps, FRAME, FRAME)
    save_sheet(PAD_OUT, [lights_frame(True), lights_frame(False)], FRAME, FRAME)


if __name__ == "__main__":
    main()
