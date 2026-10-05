"""Repaint masked sprite pixels so the engine can swap in player colours.

rules/palettes.yaml has PlayerColorShift with its defaults: pixels whose hue
sits in (0.29, 0.37] are shifted to the player's colour, with saturation
offset from 0.925 and value scaled by the player's brightness. The shader
does that test in linear light and ignores saturation, so the tint is built
in linear at the reference hue and saturation, with the render's shading
carried in value.
"""
import colorsys

TEAM_HUE = 0.33
TEAM_SAT = 0.925
# Lifts the paint's linear value so a mid-grey player colour doesn't read as
# black. The engine multiplies value by the player's own brightness.
TEAM_GAIN = 1.15


def to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def to_srgb(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def tint(base, mask):
    """Return base with mask-white pixels repainted at the team hue."""
    out = base.copy()
    bp = out.load()
    mp = mask.load()
    for y in range(base.height):
        for x in range(base.width):
            m = mp[x, y][0] / 255
            r, g, b, a = bp[x, y]
            if m <= 0 or a == 0:
                continue
            lin = [to_linear(v / 255) for v in (r, g, b)]
            value = min(1.0, max(lin) * TEAM_GAIN)
            tr, tg, tb = colorsys.hsv_to_rgb(TEAM_HUE, TEAM_SAT, value)
            team = [round(to_srgb(v) * 255) for v in (tr, tg, tb)]
            mixed = [round(o + (t - o) * m) for o, t in zip((r, g, b), team)]
            bp[x, y] = (*mixed, a)
    return out
