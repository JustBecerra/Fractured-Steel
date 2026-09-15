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
UNITS = ("tank", "eship")


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


def frame_unit(src):
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
        sheet.paste(frame_unit(src), (i * FRAME, 0))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT)
    print(f"wrote {OUT} {sheet.size} frames={len(UNITS)} size={FRAME}")


if __name__ == "__main__":
    main()
