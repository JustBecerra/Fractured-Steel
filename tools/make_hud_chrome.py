"""Armor plating for the bottom HUD.

Run from the repository root:

    python3 tools/make_hud_chrome.py

Writes chrome/assets/hud.png. The cap and the vertical breaks are solid
beveled plates — straight, S, and tilde. The cap is all blue. The
separators are shiny silver.

Original plating. The beveled hull-panel idea follows the blue-faction
command bar of Metal Fatigue (2000); none of that game's art is used.

  hud-bar    9-slice at (0, 0): 16, 22, 512, 32, 16, 6
  hud-strand one vertical run at (0, 64), 24x160
  hud-well   dark inset at (40, 64): 6, 6, 16, 16, 6, 6
  hud-pipes  corner pipes, left at (96, 64) and right at (160, 64), 64x40
  hud-pipe-run tiling pipes along the whole cap at (256, 64), 512x40
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

OUT = "mods/fracturedsteel/chrome/assets/hud.png"
SS = 3

PANEL = (24, 36, 52, 255)
PANEL_DK = (16, 24, 36, 255)
PANEL_HI = (38, 54, 74, 255)
SILVER = (186, 194, 204)
SILVER_HI = (232, 238, 244)
BLUE = (16, 58, 108)
BLUE_HI = (72, 130, 176)
EDGE = (18, 26, 38)

# Top cap, period 512. First and last vertical seams stay straight so the
# tile joins. "none" is one full-height plate; the others are split by an
# S, a tilde, or a straight cut so plates stack as well as sit side by side.
BANDS = [64, 80, 56, 72, 48, 88, 44, 60]
V_KINDS = ["straight", "s", "tilde", "straight", "s", "tilde", "straight", "s", "straight"]
H_KINDS = ["none", "tilde", "s", "none", "tilde", "s", "straight", "tilde"]
# height, bottom edge, vertical seam, then two unused flags. Heights sum to 160.
# One edge per plate is curved, so an S or tilde does not meet another
# curve and turn into a spike. Heights sum to 160.
DIV_ROWS = [
	(26, "straight", "tilde", False, False),
	(30, "tilde", "straight", True, False),
	(22, "straight", "s", False, True),
	(24, "s", "straight", False, False),
	(20, "straight", "tilde", True, False),
	(18, "tilde", "straight", False, True),
	(20, None, "straight", False, False),
]


def clamp(c):
	return tuple(max(0, min(255, int(v))) for v in c)


def mix(a, b, t):
	return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def wave(kind, t, amp):
	if kind in (None, "none", "straight"):
		return 0.0
	if kind == "s":
		return math.sin(t * math.tau) * amp
	return math.sin(t * 2 * math.tau) * amp * 0.85


def rust_mask(width, height, scale, seed, coverage, margin=0, cell=(6, 14)):
	"""0..255 per pixel. Continuous rust patches, stretched downward.

	A coarse random grid is smoothed up to full size, so rust forms
	connected patches rather than dots. Cells are taller than wide, which
	reads as runoff streaking down. coverage is roughly the rusted
	fraction. margin fades rust out at the left and right edges so
	tiling strips still join.
	"""
	rng = random.Random(seed)
	cx, cy = cell
	gw = width // cx + 3
	gh = height // cy + 3
	grid = Image.new("L", (gw, gh))
	grid.putdata([rng.randint(0, 255) for _ in range(gw * gh)])
	field = grid.resize((gw * cx * scale, gh * cy * scale), Image.Resampling.BICUBIC)
	field = field.crop((cx * scale, cy * scale, (cx + width) * scale, (cy + height) * scale))
	field = field.filter(ImageFilter.GaussianBlur(scale * 1.2))

	values = sorted(field.getdata())
	cut = values[int(len(values) * (1 - coverage))]
	soft = 28
	w_px, h_px = width * scale, height * scale
	out = Image.new("L", (w_px, h_px))
	src = field.load()
	dst = out.load()
	for y in range(h_px):
		for x in range(w_px):
			v = (src[x, y] - cut + soft / 2) / soft
			v = min(1.0, max(0.0, v))
			v = v * v * (3 - 2 * v)
			if margin:
				edge = min(x, w_px - 1 - x) / (margin * scale)
				v *= min(1.0, edge)
			# Deeper toward the middle of a patch.
			depth = min(1.0, max(0.0, (src[x, y] - cut) / 60))
			dst[x, y] = int(255 * v * (0.55 + 0.45 * depth))
	return dst


def paint(width, height, sample, scale, shine=False, rust=None):
	"""sample(x, y) -> (plate id, base rgb, local 0..1 from top of plate)."""
	img = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 255))
	px = img.load()
	ids = {}

	def at(x, y):
		key = (x, y)
		if key not in ids:
			ids[key] = sample(x, y)[0]
		return ids[key]

	for sy in range(height * scale):
		y = sy / scale
		for sx in range(width * scale):
			x = sx / scale
			ident, base, t = sample(x, y)
			if shine:
				# Brushed steel: bright near the top of each plate, a soft
				# band of light across the width, darker toward the far edge.
				# Same steel as the pipes.
				col = mix(PIPE_HI, PIPE, 0.2 + 0.6 * t)
				across = x / max(1, width - 1)
				band = max(0.0, 1 - abs(across - 0.3) * 3.2)
				col = mix(col, PIPE_HI, 0.6 * band)
				col = mix(col, PIPE_DK, 0.4 * across * across)
			else:
				col = mix(mix(base, (255, 255, 255), 0.08), base, t)
			if rust is not None:
				amount = rust[sx, sy] / 255
				if amount > 0.12:
					deep = (96, 44, 20)
					light = (168, 92, 44)
					tone = mix(light, deep, min(1, amount * 1.2))
					col = mix(col, tone, min(0.92, (amount - 0.12) * 1.6))
			left = x <= 0 or at(x - 1, y) != ident
			up = y <= 0 or at(x, y - 1) != ident
			right = x >= width - 1 or at(x + 1, y) != ident
			down = y >= height - 1 or at(x, y + 1) != ident
			if left or up:
				col = mix(col, PIPE_HI if shine else (255, 255, 255), 0.7 if shine else 0.34)
			elif right or down:
				col = mix(col, PIPE_DK if shine else EDGE, 0.55 if shine else 0.42)
			px[sx, sy] = clamp(col) + (255,)
	return img


def top_sample(x, y):
	# Map the 544px strip onto the 512px period, including both end caps.
	if x < 16:
		px = 512 - 16 + x
	elif x < 528:
		px = x - 16
	else:
		px = x - 528
	px %= 512
	y = min(max(y, 0), 21.999)
	acc = 0
	band = 0
	for i, w in enumerate(BANDS):
		# Seam leans with y so side-by-side plates meet on an S or a tilde.
		t = y / 21
		left = acc + wave(V_KINDS[i], t, 2.4)
		right = acc + w + wave(V_KINDS[i + 1], t, 2.4)
		if px < right or i == len(BANDS) - 1:
			band = i
			break
		acc += w
	kind = H_KINDS[band]
	if kind == "none":
		return (band, 0), BLUE, y / 22
	local = (px - sum(BANDS[:band])) / BANDS[band]
	split = 11 + wave(kind, local, 4.5)
	row = 0 if y < split else 1
	if row == 0:
		t = y / max(split, 1)
	else:
		t = (y - split) / max(22 - split, 1)
	return (band, row), BLUE, min(1, max(0, t))


def div_bounds():
	edges = [0]
	for height, _bottom, _v, _bl, _br in DIV_ROWS[:-1]:
		edges.append(edges[-1] + height)
	edges.append(160)
	return edges


DIV_EDGES = None


def div_sample(x, y):
	global DIV_EDGES
	if DIV_EDGES is None:
		DIV_EDGES = div_bounds()
	y = min(max(y, 0), 159.999)
	x = min(max(x, 0), 23.999)
	row = 0
	for i in range(len(DIV_ROWS) - 1):
		t = (x / 23)
		split = DIV_EDGES[i + 1] + wave(DIV_ROWS[i][1], t, 2.6)
		if y < split:
			row = i
			break
		row = i + 1
	else:
		row = len(DIV_ROWS) - 1
	top = DIV_EDGES[row]
	bot = DIV_EDGES[row + 1]
	if row > 0:
		top += wave(DIV_ROWS[row - 1][1], x / 23, 2.6)
	if row < len(DIV_ROWS) - 1:
		bot = DIV_EDGES[row + 1] + wave(DIV_ROWS[row][1], x / 23, 2.6)
	local = (y - top) / max(bot - top, 1)
	mid = 12 + wave(DIV_ROWS[row][2], local, 2.8)
	col = 0 if x < mid else 1
	return (row, col), (214, 220, 228), min(1, max(0, local))


def panel(scale):
	w, h = 544, 60
	img = Image.new("RGBA", (w * scale, h * scale), PANEL)
	px = img.load()
	top = 22 * scale
	for y in range(top, h * scale, 4 * scale):
		col = PANEL_HI if (y // scale) % 8 == 0 else PANEL_DK
		for x in range(w * scale):
			px[x, y] = col
	cap = paint(544, 22, top_sample, scale)
	img.paste(cap, (0, 0))
	# Steel lip under the cap and along the outer edges of the plate body.
	draw_y = top
	for x in range(w * scale):
		px[x, draw_y] = (8, 12, 18, 255)
	body_bottom = (22 + 32) * scale
	for y in range(top, body_bottom):
		px[0, y] = (8, 12, 18, 255)
		px[scale, y] = SILVER_HI + (255,)
		px[w * scale - 1, y] = (8, 12, 18, 255)
		px[w * scale - 1 - scale, y] = (70, 78, 88, 255)
	for x in range(w * scale):
		px[x, h * scale - 1] = (8, 12, 18, 255)
		px[x, h * scale - 1 - scale] = (70, 78, 88, 255)
	return img


def divider(scale):
	rust = rust_mask(24, 160, scale, seed=11, coverage=0.3)
	return paint(24, 160, div_sample, scale, shine=True, rust=rust)


PIPE = (92, 100, 110)
PIPE_HI = (196, 204, 212)
PIPE_DK = (34, 38, 46)
FLANGE = (58, 64, 72)


def pipe_color(t):
	"""t runs 0..1 across the pipe. Lit from the upper left."""
	if t < 0.25:
		return mix(PIPE_DK, PIPE_HI, t / 0.25)
	if t < 0.45:
		return mix(PIPE_HI, PIPE, (t - 0.25) / 0.2)
	return mix(PIPE, PIPE_DK, (t - 0.45) / 0.55)


RUST_DEEP = (104, 46, 20)
RUST_LIGHT = (156, 80, 36)


class PipeKit:
	"""Shaded pipes, elbows, flanges, and valves on one transparent image."""

	def __init__(self, w, h, scale, seed, coverage, margin=0):
		self.scale = scale
		self.img = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
		self.px = self.img.load()
		self.w, self.h = w, h
		self.rust = rust_mask(w, h, scale, seed, coverage, margin, cell=(8, 6))

	def put(self, sx, sy, col):
		if 0 <= sx < self.w * self.scale and 0 <= sy < self.h * self.scale:
			amount = self.rust[sx, sy] / 255
			if amount > 0.18:
				tone = mix(RUST_LIGHT, RUST_DEEP, min(1, amount))
				col = mix(col, tone, min(0.85, (amount - 0.18) * 1.5))
			self.px[sx, sy] = clamp(col) + (255,)

	def cylinder(self, x0, y0, x1, y1, vertical):
		s = self.scale
		for sy in range(int(y0 * s), int(y1 * s)):
			for sx in range(int(x0 * s), int(x1 * s)):
				t = (sx / s - x0) / (x1 - x0) if vertical else (sy / s - y0) / (y1 - y0)
				self.put(sx, sy, pipe_color(t))

	def elbow(self, cx, cy, r_in, r_out, quadrant):
		"""Quarter torus. quadrant (qx, qy) picks the corner of the circle."""
		s = self.scale
		qx, qy = quadrant
		for sy in range(int((cy - r_out) * s), int((cy + r_out) * s)):
			for sx in range(int((cx - r_out) * s), int((cx + r_out) * s)):
				dx = sx / s - cx
				dy = sy / s - cy
				if dx * qx < 0 or dy * qy < 0:
					continue
				d = math.hypot(dx, dy)
				if r_in <= d < r_out:
					self.put(sx, sy, pipe_color((d - r_in) / (r_out - r_in)))

	def flange(self, x0, y0, x1, y1):
		s = self.scale
		for sy in range(int(y0 * s), int(y1 * s)):
			for sx in range(int(x0 * s), int(x1 * s)):
				edge = min(sx - x0 * s, sy - y0 * s, x1 * s - 1 - sx, y1 * s - 1 - sy)
				self.put(sx, sy, PIPE_HI if edge < s * 0.8 else FLANGE)

	def wheel(self, cx, cy, r):
		s = self.scale
		for sy in range(int((cy - r - 1) * s), int((cy + r + 1) * s)):
			for sx in range(int((cx - r - 1) * s), int((cx + r + 1) * s)):
				dx = sx / s - cx
				dy = sy / s - cy
				d = math.hypot(dx, dy)
				ring = r - 1.3 <= d <= r
				spoke = d < r and (abs(dx) < 0.6 or abs(dy) < 0.6)
				hub = d < 1.4
				if ring or spoke or hub:
					self.put(sx, sy, (150, 44, 30) if ring else FLANGE)

	def loop_up(self, x_left, x_right, top, bottom, r_in, r_out):
		"""Rise from bottom, arc over at top, come back down to bottom."""
		thick = r_out - r_in
		cy = top + r_out
		self.cylinder(x_left, cy, x_left + thick, bottom, vertical=True)
		self.elbow(x_left + r_out, cy, r_in, r_out, (-1, -1))
		self.cylinder(x_left + r_out, top, x_right - r_out, top + thick, vertical=False)
		self.elbow(x_right - r_out, cy, r_in, r_out, (1, -1))
		self.cylinder(x_right - thick, cy, x_right, bottom, vertical=True)


def corner_pipes(scale):
	"""Pipes rising off the left corner of the cap. Mirror for the right.

	The image is 64x40 and sits with its bottom 18px over the cap. Nothing
	is drawn below the cap, so the radar and counters stay clear.
	"""
	k = PipeKit(64, 40, scale, seed=5, coverage=0.25)
	# Thick pipe: rises from the cap, bends, and runs off the screen edge.
	k.cylinder(18, 14, 26, 40, vertical=True)
	k.elbow(12, 14, 6, 14, (1, -1))
	k.cylinder(0, 0, 12, 8, vertical=False)
	k.flange(16, 26, 28, 30)

	# Thin stub with a valve cap beside it.
	k.cylinder(34, 18, 38, 40, vertical=True)
	k.flange(32, 15, 40, 19)
	k.cylinder(35, 11, 37, 15, vertical=True)
	k.flange(33, 9, 39, 11)
	return k.img


def pipe_run(scale):
	"""512x40 tile of pipes along the whole cap.

	The bottom 22px overlay the cap; the top 18px stick up above it. Only
	the two long mains cross the tile edges, so the run tiles seamlessly.
	"""
	k = PipeKit(512, 40, scale, seed=23, coverage=0.25, margin=10)

	# Thin line along the back of the cap, with brackets.
	k.cylinder(0, 21, 512, 25, vertical=False)
	for x in (40, 196, 330, 470):
		k.flange(x, 20, x + 4, 26)

	# Loops that rise off the cap and drop back into it.
	k.loop_up(70, 150, 2, 34, 4, 10)
	k.flange(68, 24, 82, 28)
	k.flange(138, 24, 152, 28)
	k.loop_up(360, 404, 8, 34, 3, 8)

	# Valve riser with a hand wheel.
	k.cylinder(236, 12, 242, 34, vertical=True)
	k.flange(233, 22, 245, 26)
	k.wheel(239, 9, 6)

	# Exhaust stubs.
	k.cylinder(292, 6, 300, 34, vertical=True)
	k.flange(290, 4, 302, 8)
	k.flange(290, 24, 302, 27)
	k.cylinder(448, 14, 452, 34, vertical=True)
	k.flange(446, 12, 454, 15)

	# Main line along the cap. Drawn last so the risers seat into it.
	k.cylinder(0, 30, 512, 37, vertical=False)
	for x in (20, 110, 176, 264, 318, 420, 492):
		k.flange(x, 29, x + 5, 38)
	return k.img


def well(scale):
	w = h = 28 * scale
	img = Image.new("RGBA", (w, h), (6, 10, 16, 255))
	px = img.load()
	for y in range(h):
		for x in range(w):
			edge = min(x, y, w - 1 - x, h - 1 - y)
			if edge == 0:
				px[x, y] = SILVER_HI + (255,)
			elif edge == 1 * scale or edge < scale:
				px[x, y] = (90, 98, 108, 255)
			elif edge < 2 * scale:
				px[x, y] = BLUE_HI + (255,)
			elif edge < 3 * scale:
				px[x, y] = (16, 48, 90, 255)
			else:
				px[x, y] = (6, 10, 16, 255)
	return img


def main():
	assert sum(BANDS) == 512, sum(BANDS)
	assert len(V_KINDS) == len(BANDS) + 1
	assert len(H_KINDS) == len(BANDS)
	assert sum(r[0] for r in DIV_ROWS) == 160, sum(r[0] for r in DIV_ROWS)
	sheet = Image.new("RGBA", (1024 * SS, 256 * SS), (0, 0, 0, 0))
	sheet.paste(panel(SS), (0, 0))
	sheet.paste(divider(SS), (0, 64 * SS))
	sheet.paste(well(SS), (40 * SS, 64 * SS))
	pipes = corner_pipes(SS)
	sheet.paste(pipes, (96 * SS, 64 * SS), pipes)
	mirrored = pipes.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
	sheet.paste(mirrored, (160 * SS, 64 * SS), mirrored)
	run = pipe_run(SS)
	sheet.paste(run, (256 * SS, 64 * SS), run)
	sheet = sheet.resize((1024, 256), Image.Resampling.LANCZOS)
	sheet.save(OUT)
	print(f"wrote {OUT} {sheet.size}")


if __name__ == "__main__":
	main()
