"""Gray/brown Alloy dump sprites for the resource layer.

Run from the repository root:

    python3 tools/make_alloy_sheet.py

Each sequence is one scrap-heap variant with 3 density frames (sparse scatter,
then a proper pile, then a packed junkyard cell). Drawn as isometric crates,
plates and barrels so a 2x3 dump reads as a junkyard rather than a flat stain.
"""
from PIL import Image, ImageDraw, ImageFilter, PngImagePlugin

FRAME = 48
DENSITY = 3
VARIANTS = 3
SS = 4
OUT = "mods/fracturedsteel/sequences/assets/alloy.png"

# Weathered steel, rust, dirt — gray/brown as requested.
STEEL = (118, 114, 110)
STEEL_DK = (72, 68, 64)
RUST = (132, 86, 48)
RUST_DK = (86, 52, 28)
DIRT = (96, 78, 52)
DIRT_LT = (148, 118, 78)
SHADOW = (28, 22, 16, 110)

# Isometric cell diamond inscribed in the frame, matching OpenRA's rectangular
# iso camera enough that a heap sits in the tile instead of floating on it.
CX = FRAME * SS / 2
CY = FRAME * SS / 2 + 6 * SS
HALF_W = 20 * SS
HALF_H = 10 * SS


def iso(x, y, z):
    """Ground (x, y) plus height z, in supersampled pixels. +y is screen-down."""
    sx = CX + (x - y) * (HALF_W / 16)
    sy = CY + (x + y) * (HALF_H / 16) - z * SS
    return sx, sy


def box(draw, x, y, w, d, h, top, side_l, side_r):
    """Isometric box with ground origin at (x, y), size (w, d, h)."""
    p = {
        "fl": iso(x, y, 0),
        "fr": iso(x + w, y, 0),
        "bl": iso(x, y + d, 0),
        "br": iso(x + w, y + d, 0),
        "ftl": iso(x, y, h),
        "ftr": iso(x + w, y, h),
        "btl": iso(x, y + d, h),
        "btr": iso(x + w, y + d, h),
    }
    draw.polygon([p["ftl"], p["ftr"], p["br"], p["fr"]], fill=side_r)
    draw.polygon([p["ftl"], p["btl"], p["bl"], p["fl"]], fill=side_l)
    draw.polygon([p["ftl"], p["ftr"], p["btr"], p["btl"]], fill=top)


def barrel(draw, x, y, r, h, body, rim, band):
    """Short isometric drum standing on the cell."""
    top = iso(x, y, h)
    bot = iso(x, y, 0)
    rx, ry = r * SS * 0.9, r * SS * 0.45
    draw.ellipse((bot[0] - rx, bot[1] - ry, bot[0] + rx, bot[1] + ry), fill=body)
    draw.rectangle((bot[0] - rx, top[1], bot[0] + rx, bot[1]), fill=body)
    draw.ellipse((top[0] - rx, top[1] - ry, top[0] + rx, top[1] + ry), fill=rim)
    mid = iso(x, y, h * 0.45)
    draw.ellipse((mid[0] - rx, mid[1] - ry * 0.85, mid[0] + rx, mid[1] + ry * 0.85), outline=band, width=max(1, SS // 2))


# Per-variant piece lists: (kind, args...). kind is "box" or "barrel".
# Positions are in the 0..16 cell space used by iso().
LAYOUTS = [
    [
        ("box", (0, 1, 9, 7, 5), STEEL, STEEL_DK, RUST),
        ("barrel", (11, 3, 4, 6), RUST, RUST_DK, STEEL_DK),
        ("box", (5, 7, 8, 7, 4), DIRT_LT, DIRT, STEEL_DK),
        ("box", (-1, 8, 7, 6, 3), STEEL, DIRT, STEEL_DK),
        ("barrel", (13, 9, 3, 5), DIRT, RUST_DK, STEEL),
    ],
    [
        ("barrel", (3, 2, 4, 7), STEEL, STEEL_DK, RUST),
        ("box", (8, 1, 8, 7, 4), RUST, RUST_DK, DIRT),
        ("box", (1, 8, 10, 6, 5), STEEL, STEEL_DK, DIRT_LT),
        ("barrel", (12, 8, 4, 5), DIRT, DIRT_LT, STEEL_DK),
        ("box", (6, 4, 6, 5, 3), RUST_DK, STEEL, DIRT),
    ],
    [
        ("box", (1, 0, 7, 8, 6), DIRT, DIRT_LT, STEEL_DK),
        ("box", (8, 3, 8, 6, 4), STEEL, STEEL_DK, RUST_DK),
        ("barrel", (2, 8, 4, 6), RUST, RUST_DK, STEEL),
        ("box", (9, 9, 7, 6, 3), STEEL_DK, DIRT, RUST),
        ("barrel", (7, 6, 3, 4), STEEL, RUST, STEEL_DK),
    ],
]


def ground_shadow(draw, pieces, t):
    """Soft blob under the heap, growing with density."""
    rx = (14 + 6 * t) * SS
    ry = (7 + 3 * t) * SS
    draw.ellipse((CX - rx, CY - ry + 2 * SS, CX + rx, CY + ry + 2 * SS), fill=SHADOW)


def draw_piece(draw, piece):
    kind, args, *rest = piece
    if kind == "box":
        x, y, w, d, h = args
        top, side_l, side_r = rest
        box(draw, x, y, w, d, h, top, side_l, side_r)
    else:
        x, y, r, h = args
        body, rim, band = rest
        barrel(draw, x, y, r, h, body, rim, band)


def frame(variant, density):
    """density 0..2: how much of the layout is showing, and how tall."""
    size = FRAME * SS
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    t = density / (DENSITY - 1)
    pieces = LAYOUTS[variant]
    n = max(1, int(round(1 + t * (len(pieces) - 1))))
    ground_shadow(draw, pieces[:n], t)
    for piece in pieces[:n]:
        kind, args, *rest = piece
        if kind == "box":
            x, y, w, d, h = args
            h = max(1, int(round(h * (0.45 + 0.55 * t))))
            draw_piece(draw, ("box", (x, y, w, d, h), *rest))
        else:
            x, y, r, h = args
            h = max(2, int(round(h * (0.5 + 0.5 * t))))
            draw_piece(draw, ("barrel", (x, y, r, h), *rest))
    img = img.filter(ImageFilter.GaussianBlur(0.4 * SS))
    return img.resize((FRAME, FRAME), Image.LANCZOS)


def main():
    sheet = Image.new("RGBA", (FRAME * DENSITY * VARIANTS, FRAME), (0, 0, 0, 0))
    i = 0
    for v in range(VARIANTS):
        for d in range(DENSITY):
            im = frame(v, d)
            sheet.paste(im, (i * FRAME, 0), im)
            i += 1
    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{FRAME},{FRAME}")
    meta.add_text("FrameAmount", str(DENSITY * VARIANTS))
    sheet.save(OUT, pnginfo=meta)
    print(f"wrote {OUT} {sheet.size} variants={VARIANTS} density={DENSITY}")


if __name__ == "__main__":
    main()
