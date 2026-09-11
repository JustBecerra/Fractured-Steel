"""Pack the Blender-rendered scanner cone into scanner.png.

Run from the repository root:  python3 tools/pack_scanner_sheet.py

Renders come from art/placeholders/scanner/f{facing}_{step}.png, produced through
the same camera as eship.png with ortho_scale scaled to keep world-units-per-pixel
identical, so frames are centred on the same point as the 60px ship frames.

DefaultSpriteSequence resolves a frame as `facingInner * stride + frame`, with
stride defaulting to Length, so the sheet must be facing-major: one row per
facing, one column per sweep step.
"""
from PIL import Image, ImageFilter, PngImagePlugin

SRC = "art/placeholders/scanner/f%d_%d.png"
OUT = "mods/fracturedsteel/sequences/assets/scanner.png"
F = 128              # frame size
FACINGS = 8
STEPS = 8            # sweep frames per facing
GLOW_RADIUS = 6      # at render resolution, before downscaling
GLOW_STRENGTH = 0.5


def with_glow(frame):
    """Composite a blurred copy underneath so the cone reads as light."""
    glow = frame.filter(ImageFilter.GaussianBlur(GLOW_RADIUS))
    a = glow.getchannel("A").point(lambda v: int(v * GLOW_STRENGTH))
    glow.putalpha(a)
    glow.alpha_composite(frame)
    return glow


def load(facing, step):
    return with_glow(Image.open(SRC % (facing, step)).convert("RGBA")).resize(
        (F, F), Image.LANCZOS)


sheet = Image.new("RGBA", (F * STEPS, F * FACINGS), (0, 0, 0, 0))
for facing in range(FACINGS):
    for step in range(STEPS):
        sheet.paste(load(facing, step), (step * F, facing * F))

meta = PngImagePlugin.PngInfo()
meta.add_text("FrameSize", f"{F},{F}")
meta.add_text("FrameAmount", str(FACINGS * STEPS))
sheet.save(OUT, pnginfo=meta)
print("wrote", OUT, sheet.size, "frames:", FACINGS * STEPS)

# Preview: one facing across the whole sweep, with the ship underneath, so the
# vertical travel of the beam is visible.
ship = Image.open("mods/fracturedsteel/sequences/assets/eship.png").convert("RGBA")
PREV_FACING = 2
prev = Image.new("RGBA", (F * STEPS, F), (34, 40, 34, 255))
for step in range(STEPS):
    prev.alpha_composite(ship.crop((PREV_FACING * 60, 0, PREV_FACING * 60 + 60, 60)),
                         (step * F + (F - 60) // 2, (F - 60) // 2))
    prev.alpha_composite(load(PREV_FACING, step), (step * F, 0))
prev.resize((F * STEPS * 2, F * 2), Image.NEAREST).save(
    "art/placeholders/_scanner_sweep.png")
print("wrote sweep preview")
