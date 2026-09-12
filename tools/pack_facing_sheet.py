"""Pack per-facing Blender renders into an OpenRA PngSheet.

Run from the repository root, e.g.

    python3 tools/pack_facing_sheet.py \
        --src 'art/placeholders/tank/f{facing}.png' \
        --out mods/fracturedsteel/sequences/assets/tank.png \
        --frame 60 --facings 8

For animated sequences, pass --steps N and include {step} in --src. The engine
resolves a frame as `facingInner * stride + frame` (stride defaults to Length),
so multi-step sheets are written facing-major: one row per facing, one column
per animation step.

Renders are expected to be square and centred on the model, produced through a
camera whose ortho_scale keeps world-units-per-pixel consistent across units.
"""
import argparse

from PIL import Image, PngImagePlugin


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", required=True,
                   help="Source path template using {facing} and optionally {step}.")
    p.add_argument("--out", required=True, help="Destination PNG sheet.")
    p.add_argument("--frame", type=int, required=True, help="Output frame size in pixels.")
    p.add_argument("--facings", type=int, default=8)
    p.add_argument("--steps", type=int, default=1, help="Animation frames per facing.")
    args = p.parse_args()

    f, facings, steps = args.frame, args.facings, args.steps
    cols = steps if steps > 1 else facings
    rows = facings if steps > 1 else 1

    sheet = Image.new("RGBA", (f * cols, f * rows), (0, 0, 0, 0))
    for facing in range(facings):
        for step in range(steps):
            path = args.src.format(facing=facing, step=step)
            frame = Image.open(path).convert("RGBA").resize((f, f), Image.LANCZOS)
            index = facing * steps + step
            sheet.paste(frame, ((index % cols) * f, (index // cols) * f))

    meta = PngImagePlugin.PngInfo()
    meta.add_text("FrameSize", f"{f},{f}")
    meta.add_text("FrameAmount", str(facings * steps))
    sheet.save(args.out, pnginfo=meta)
    print(f"wrote {args.out} {sheet.size} frames={facings * steps}")


if __name__ == "__main__":
    main()
