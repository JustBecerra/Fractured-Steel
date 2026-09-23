"""Cell overlays for building placement: green valid, red blocked.

Run from the repository root:

    python3 tools/make_build_overlay.py

Two 32px frames, matching the map tile size. The placement preview looks
these up as overlay.build-valid and overlay.build-invalid.
"""
from PIL import Image, ImageDraw, PngImagePlugin

FRAME = 32
OUT = "mods/fracturedsteel/sequences/assets/build-overlay.png"


def cell(fill, edge):
    img = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((1, 1, FRAME - 2, FRAME - 2), fill=fill, outline=edge)
    return img


def main():
    sheet = Image.new("RGBA", (FRAME * 2, FRAME), (0, 0, 0, 0))
    valid = cell((70, 170, 70, 110), (150, 230, 140, 220))
    blocked = cell((170, 50, 40, 120), (230, 90, 70, 230))
    sheet.paste(valid, (0, 0), valid)
    sheet.paste(blocked, (FRAME, 0), blocked)
    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{FRAME},{FRAME}")
    meta.add_text("FrameAmount", "2")
    sheet.save(OUT, pnginfo=meta)
    print(f"wrote {OUT} {sheet.size}")


if __name__ == "__main__":
    main()
