"""Pack hull + turret renders into the tank PngSheet.

Run from the repository root after tools/render_tank_layers.py:

    python3 tools/pack_tank_layers.py

Side-on turret frames are shifted down so the gunhouse sits on the fenders.
The drop is 0 at north/south and peaks at east/west.
"""
from math import pi, sin
from pathlib import Path

from PIL import Image, PngImagePlugin

SRC = Path("art/placeholders/tank")
OUT = Path("mods/fracturedsteel/sequences/assets/tank.png")
FRAME = 60
FACINGS = 32
SIDE_DROP = 3


def turret_drop(facing):
    return round(SIDE_DROP * abs(sin(facing * 2 * pi / FACINGS)))


def main():
    sheet = Image.new("RGBA", (FRAME * FACINGS, FRAME * 2), (0, 0, 0, 0))
    for i in range(FACINGS):
        hull = Image.open(SRC / f"hull_{i:02d}.png").convert("RGBA").resize((FRAME, FRAME), Image.LANCZOS)
        turret = Image.open(SRC / f"turret_{i:02d}.png").convert("RGBA").resize((FRAME, FRAME), Image.LANCZOS)
        drop = turret_drop(i)
        if drop:
            seated = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
            seated.paste(turret, (0, drop), turret)
            turret = seated
        sheet.paste(hull, (i * FRAME, 0))
        sheet.paste(turret, (i * FRAME, FRAME))

    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{FRAME},{FRAME}")
    meta.add_text("FrameAmount", str(FACINGS * 2))
    sheet.save(OUT, pnginfo=meta)
    print(f"wrote {OUT} {sheet.size} side_drop={SIDE_DROP}")


if __name__ == "__main__":
    main()
