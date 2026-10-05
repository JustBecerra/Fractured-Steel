"""Pack the HQ renders into its PngSheet, with team colour.

Run from the repository root after tools/render_hq.py:

    python3 tools/pack_hq.py

Three 320px frames side by side, one per flag pose (sequence `idle`,
Length 3). Team-colour parts come from the mask renders.
"""
from pathlib import Path

from PIL import Image, PngImagePlugin

from team_color import tint

SRC = Path("art/placeholders/hq")
OUT = Path("mods/fracturedsteel/sequences/assets/hq.png")
FRAME = 320
FRAMES = 3


def load(name):
    return Image.open(SRC / name).convert("RGBA").resize((FRAME, FRAME), Image.LANCZOS)


def main():
    sheet = Image.new("RGBA", (FRAME * FRAMES, FRAME), (0, 0, 0, 0))
    for i in range(FRAMES):
        frame = tint(load(f"idle{i}.png"), load(f"mask{i}.png"))
        sheet.paste(frame, (i * FRAME, 0))

    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{FRAME},{FRAME}")
    meta.add_text("FrameAmount", str(FRAMES))
    sheet.save(OUT, pnginfo=meta)
    print(f"wrote {OUT} {sheet.size}")


if __name__ == "__main__":
    main()
