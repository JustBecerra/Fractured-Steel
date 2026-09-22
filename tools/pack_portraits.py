"""Pack close-up Blender portrait renders into a chrome atlas.

Run from the repository root:

    python3 tools/pack_portraits.py

Crops each render to its alpha hull, sharpens and darkens the silhouette
edge so the 3/4 close-up reads at HUD size, then drops a contact shadow
and lays the frames left-to-right in chrome/assets/portraits.png.

The atlas is padded to power-of-two dimensions: OpenRA's GL textures
reject any other size (Texture.SetData throws Non-power-of-two array).
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "art/placeholders/portraits"
OUT = ROOT / "mods/fracturedsteel/chrome/assets/portraits.png"

FRAME = 160
MARGIN = 14
SHADOW_OFFSET = (5, 7)
SHADOW_BLUR = 9
SHADOW_ALPHA = 110
UNITS = ("tank", "eship", "hq", "academy")

SKY = (176, 214, 238)
SAND = (201, 168, 112)
SAND_DARK = (168, 132, 82)
SAND_LIGHT = (224, 196, 148)


def crop_alpha(im, pad=2):
    bbox = im.getchannel("A").getbbox()
    if bbox is None:
        return im
    l, t, r, b = bbox
    l = max(0, l - pad)
    t = max(0, t - pad)
    r = min(im.width, r + pad)
    b = min(im.height, b + pad)
    return im.crop((l, t, r, b))


def fit(im, box):
    """Scale `im` to fit inside `box` x `box`, keeping aspect."""
    w, h = im.size
    scale = min(box / w, box / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    return im.resize((nw, nh), Image.LANCZOS)


def edge_darken(im, width=3, shade=0.55):
    """Darken a thin ring just inside the silhouette so edges read up close."""
    alpha = im.getchannel("A")
    inner = alpha
    for _ in range(width):
        inner = inner.filter(ImageFilter.MinFilter(3))
    ring = ImageChops.subtract(alpha, inner)
    rgb = im.convert("RGB")
    darkened = ImageEnhance_multiply(rgb, shade)
    out_rgb = Image.composite(darkened, rgb, ring)
    out = out_rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def ImageEnhance_multiply(rgb, factor):
    lut = [max(0, min(255, int(i * factor))) for i in range(256)]
    return rgb.point(lut * 3)


def unsharp(im):
    return im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=140, threshold=2))


def grain(size, sigma=28):
    return Image.effect_noise(size, sigma).convert("L")


CLOUD = (208, 226, 238)
CLOUD_SHADE = (192, 214, 230)


def desert_fill(size):
    """Flat desert slab with dusty blotches. No sky-to-sand gradient."""
    base = Image.new("RGB", size, SAND)
    n1 = grain((max(1, size[0] // 10), max(1, size[1] // 6)), 36).resize(size, Image.BILINEAR)
    n2 = grain((max(1, size[0] // 4), max(1, size[1] // 3)), 24).resize(size, Image.BILINEAR)
    dark = Image.new("RGB", size, SAND_DARK)
    light = Image.new("RGB", size, SAND_LIGHT)
    dark_m = n1.point(lambda v: max(0, min(255, (v - 132) * 3)))
    light_m = n2.point(lambda v: max(0, min(255, (v - 148) * 2)))
    out = Image.composite(dark, base, dark_m)
    out = Image.composite(light, out, light_m.point(lambda v: int(v * 0.45)))
    return out.convert("RGBA")


def backdrop(horizon_frac):
    """Clear sky above a hard desert horizon. `horizon_frac` is where sand starts."""
    horizon = int(FRAME * horizon_frac)
    canvas = Image.new("RGBA", (FRAME, FRAME), SKY + (255,))
    if horizon < FRAME:
        canvas.paste(desert_fill((FRAME, FRAME - horizon)), (0, horizon))
    return canvas


def paint_distant_clouds(canvas, horizon):
    """Two small distant clouds in the sky only. Flat puffs, no sky gradient."""
    from PIL import ImageDraw

    w, h = canvas.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def puff(cx, cy, rx, ry, fill):
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill)

    def cloud(cx, cy, scale, alpha=210):
        fill = CLOUD + (alpha,)
        shade = CLOUD_SHADE + (int(alpha * 0.8),)
        puffs = (
            (0, 2, 17, 7, shade),
            (-11, 0, 11, 6, fill),
            (1, -3, 15, 7, fill),
            (12, 1, 10, 5, fill),
        )
        for dx, dy, rx, ry, col in puffs:
            puff(
                cx + round(dx * scale),
                cy + round(dy * scale),
                max(2, round(rx * scale)),
                max(2, round(ry * scale)),
                col,
            )

    cloud(30, max(8, horizon - 26), 0.72)
    cloud(128, max(8, horizon - 20), 0.55)

    layer = layer.filter(ImageFilter.GaussianBlur(0.9))
    sky = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sky).rectangle((0, 0, w, horizon), fill=255)
    a = ImageChops.multiply(layer.getchannel("A"), sky)
    layer.putalpha(a)
    return Image.alpha_composite(canvas, layer)


def hq_scene(src):
    """Keep stairs, doors and annex intact; desert only where the render is empty."""
    im = Image.open(src).convert("RGBA")
    subject = im.resize((FRAME, FRAME), Image.LANCZOS)
    subject = unsharp(subject)
    subject = edge_darken(subject)

    canvas = backdrop(0.54)
    canvas.paste(subject, (0, 0), subject)
    return canvas


def tank_scene(src):
    """Same flat sky and dusty ground as the HQ; tank pixels are not painted."""
    im = Image.open(src).convert("RGBA")
    im = crop_alpha(im)
    # Fill more of the frame, but keep a strip of sky to the right of the muzzle.
    subject = fit(im, FRAME - 24)
    subject = unsharp(subject)
    subject = edge_darken(subject)

    horizon_frac = 0.50
    horizon = int(FRAME * horizon_frac)
    canvas = paint_distant_clouds(backdrop(horizon_frac), horizon)
    x = 8
    y = (FRAME - subject.height) // 2
    canvas.paste(subject, (x, y), subject)
    return canvas


def frame_unit(src, environment=None):
    if environment == "hq":
        return hq_scene(src)
    if environment in ("tank", "eship", "academy"):
        return tank_scene(src)

    im = Image.open(src).convert("RGBA")
    im = crop_alpha(im)
    subject = fit(im, FRAME - 2 * MARGIN)
    subject = unsharp(subject)
    subject = edge_darken(subject)

    canvas = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    x = (FRAME - subject.width) // 2 - SHADOW_OFFSET[0] // 2
    y = (FRAME - subject.height) // 2 - SHADOW_OFFSET[1] // 2

    shadow = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    sh = Image.new("RGBA", subject.size, (0, 0, 0, SHADOW_ALPHA))
    sh.putalpha(ImageChops.multiply(
        subject.getchannel("A"),
        Image.new("L", subject.size, SHADOW_ALPHA)))
    shadow.paste(sh, (x + SHADOW_OFFSET[0], y + SHADOW_OFFSET[1]), sh)
    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))

    canvas = Image.alpha_composite(canvas, shadow)
    canvas.paste(subject, (x, y), subject)
    return canvas


def next_pot(n):
    p = 1
    while p < n:
        p *= 2
    return p


def main():
    content_w, content_h = FRAME * len(UNITS), FRAME
    sheet = Image.new("RGBA", (next_pot(content_w), next_pot(content_h)), (0, 0, 0, 0))
    for i, name in enumerate(UNITS):
        src = SRC / f"{name}.png"
        if not src.is_file():
            raise SystemExit(f"missing render {src}")
        sheet.paste(frame_unit(src, environment=name if name in ("hq", "tank", "eship", "academy") else None), (i * FRAME, 0))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT)
    print(f"wrote {OUT} {sheet.size} frames={len(UNITS)} size={FRAME}")


if __name__ == "__main__":
    main()
