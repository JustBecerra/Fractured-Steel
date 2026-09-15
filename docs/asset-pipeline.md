# Asset pipeline: Blender to OpenRA sprite sheets

How unit sprites are produced. Read this before regenerating or adding any unit art.
The isometric facing math in particular is unintuitive and has caused real bugs.

## Source models

Models live **outside this repository**, currently at
`~/Desktop/FracturedSteel-assets/worker.blend`. Only the rendered PNG sheets are
committed. Renders are written to the untracked `art/placeholders/` directory before
being packed.

Model convention: the unit's **forward direction is `+X`**.

## Driving Blender

Blender is controlled over the Blender MCP server (`user-blender-mcp`), which executes
`bpy` code inside a running Blender instance. Start it with:

```bash
uv --directory $HOME/blender_mcp/mcp run blender-mcp --transport http --port 9191
```

Blender must be running with the MCP add-on enabled (bridge port 9876). Cursor connects
via `~/.cursor/mcp.json`. If the tools vanish mid-session, Cursor has cached a failed
connection — refresh the server in Settings → MCP after restarting it.

**Gotcha:** `bpy.context.active_object` is **not available** in the MCP execution
context. To get a reference to a newly created object, diff the object set:

```python
def add_and_get(opfunc, **kw):
    before = set(bpy.data.objects)
    opfunc(**kw)
    new = list(set(bpy.data.objects) - before)
    return new[0] if new else None
```

Render setup: orthographic camera aimed at the model centre, `film_transparent = True`,
and objects toggled per-frame with `hide_render` to produce variant states (e.g.
thrusters on/off).

**Gotcha:** `matrix_world` is cached and only recomputed when the depsgraph is
evaluated. Setting `location`/`rotation_euler`/`scale` and then reading `matrix_world`
in the same script returns **stale matrices**, so any bounding box you compute from
them is wrong. Call `bpy.context.view_layer.update()` first. This silently mis-aimed
the tank camera by 0.07 units before it was caught.

**Keep the world-units-per-pixel constant** across re-renders, or the unit will change
size on screen. For the current sheet: `WPP = 0.020569`, so the render resolution is
`ceil(ortho_scale / WPP)` — growing the model's bounding radius grows the render size
rather than shrinking the ship.

## Isometric facing math (important)

OpenRA's camera is isometric, which maps a model's **world yaw to an on-screen angle
non-linearly**. Rotating the model in even 45° steps does *not* produce facings that
appear 45° apart on screen. An early version did exactly this and the unit visibly
pointed the wrong way when moving diagonally.

For each facing `i` (0-7), solve numerically for the world yaw whose *projected* nose
lands at screen angle `i * 45°`, measured clockwise from up:

```python
R = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))   # camera right
U = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))   # camera up
def screen_angle(yaw):
    v = Vector((cos(yaw), sin(yaw), 0))
    return atan2(v.dot(R), v.dot(U)) % (2 * pi)
```

The solved yaws for the current camera are:

```
[135.0, 97.7, 45.0, 352.2, 315.0, 277.8, 225.0, 172.3]  # degrees, facings 0-7
```

Re-solve these if the camera ever changes. Do not hardcode uniform 45° steps.

### Negative `Facings`

The sequence uses `Facings: -8`, not `8`. A negative value sets `reverseFacings`, so
the engine computes `facingInner = (facings - facing) % facings`. This preserves
facings 0 (north) and 4 (south) while swapping east with west and the diagonals —
which is precisely the handedness flip between Blender's coordinate system and
OpenRA's. Symptom of getting this wrong: the unit turns correctly when moving up and
down, but mirrored when moving left and right.

## Sheet format (PngSheet)

The mod declares `SpriteFormats: PngSheet`. A multi-frame sheet is a single PNG whose
frames are read from embedded PNG text chunks:

- `FrameSize` — `"width,height"` of one frame
- `FrameAmount` — total frame count

Frames are laid out in a grid, left to right then top to bottom, with
`framesPerRow = image.Width / frameSize.Width`. Write the metadata with PIL:

```python
from PIL import PngImagePlugin
meta = PngImagePlugin.PngInfo()
meta.add_text("FrameSize", "60,60")
meta.add_text("FrameAmount", "16")
sheet.save(path, pnginfo=meta)
```

### Current sheets

`eship.png` — 480×120, sixteen 60×60 frames:

| Frames | Contents |
| --- | --- |
| 0-7 | Facings 0-7, thrusters off (`idle` sequence) |
| 8-15 | Facings 0-7, thrusters firing (`move` sequence, `Start: 8`) |

`tank.png` — 480×60, eight 60×60 frames, facings 0-7. Rendered from `tank.blend` through
the same camera and `ortho_scale` as `eship`, so the two units share a pixel scale.
Turret is part of the hull sprite: `WithSpriteTurret` requires an `Armament`, so an
independently rotating turret means building out a weapon first. The turret parts are
separate objects in the .blend, so splitting them into their own sheet is one extra
render pass.

`smoke.png` — 384×32, twelve 32×32 frames, one puff's life. Procedural, see
`tools/make_smoke_sheet.py`.

`hq.png` — 320×320, one isometric frame. Rendered from `hq.blend` at the same
world-units-per-pixel as the units (`ortho_scale = 320 × WPP_FINAL`). A central
drum (double door, circular skylight, roof antennas) sits on a wide terrace inside
a lower ring of annexes joined by corridors, with stacked sandbags and barbed wire
on the outer face. The entrance sector is left open. Buildings do not rotate, so
there is only one facing.

Frame index within a sequence is `start + facingInner * stride + frame`, where `stride`
defaults to `Length`. So a multi-frame *animated* sequence per facing must be laid out
facing-major, with `Length` and `Stride` set to the number of animation frames — and
any later sequence's `Start` must be shifted accordingly.

## Blender units to OpenRA world units

Traits that position things relative to an actor (`LeavesTrails.Offsets`,
`WithIdleOverlay.Offset`, `ConditionalTerrainLightSource.Offset`) take WVec triples of
`(forward, right, up)` in OpenRA world units. To place one at a feature you modelled,
convert from Blender units:

- One Blender unit is `1 / WPP_FINAL` = **9.52 px** in the final sprite.
- `TileSize` is 32×32 and one cell is 1024 world units, so **one pixel is 32 world units**.
- OpenRA projects world X/Y to screen 1:1 (square tiles), while the Blender camera
  foreshortens the ground plane by `sin(49.4°)` = **0.76**. Horizontal offsets must be
  multiplied by this or they overshoot by ~32%.

Net: **~231 world units per horizontal Blender unit** (`9.52 × 0.76 × 32`), and ~198 per
Blender unit of *height*, since height projects through the camera's up vector instead.
Measure the feature relative to the `Pivot`, since the sprite frame is centred on it.

Worked example — the tank's exhaust outlets sit at Blender `(-1.90, ±0.50, 0.76)` with the
pivot at `(0.02, 0, 0.80)`, so relative `(-1.92, ±0.50, -0.04)`, giving
`Offsets: -444,-116,0` and `-444,116,0`. The height difference is a quarter of a pixel and
rounds away.

Because the projections do not match exactly, treat the result as a good starting value
and check it in game.

## Legibility beats real scale

At a 60px frame, small details modelled to true scale disappear. The tank's FM MAG was
first built at its real size relative to the hull, which put the barrel at **0.6 px** —
sub-pixel, so it rendered as a faint smear. Roughly doubling it (1.5 px barrel, standing
~4 px above the turret roof) and pushing it outboard so it breaks the roof silhouette made
it read. Exaggerate small features and prefer positions that break an outline rather than
sit inside one.

## Colour: beware the AgX view transform

The scene's view transform is **AgX**, which desaturates bright, saturated colours
toward white. This is the main reason coloured emission renders wash out to grey — a
cyan emitter came back as `(149,186,205)` instead of cyan. Lowering emission strength
only partly hides it.

For effect sprites, set the transform to Standard for the render and restore it after:

```python
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
```

The same emitter then renders as `(112,207,255)`, a true cyan. Always restore the
original value — the `.blend` belongs to the user, and the hull renders are authored
under AgX.

Independently, keep `emission colour x strength` under 1.0 per channel; above that the
channel clips and the colour skews white regardless of transform.

## Post-processing

The blue thruster bloom is added in PIL, not Blender. Two lessons from getting it wrong:

1. Keep emission strength low. Too high clips all three channels and the exhaust
   renders **white** instead of blue.
2. Mask the bloom to **blue-dominant pixels only**, otherwise it also blooms the white
   hull:

```python
diff = ImageChops.subtract(b, r)
mask = diff.point(lambda v: 255 if v > 35 else 0)
```

Then blur the masked region and composite it back with a blue tint
(`R×0.30, G×0.62, B×1.0`).

For clean anti-aliased shapes drawn procedurally (such as `ring.png`, the 84×84 green
selection ellipse), draw at 4× resolution and downscale with `LANCZOS`.

## Checklist for new/changed sprites

1. Render frames to `art/placeholders/` (gitignored).
2. Pack into a sheet with correct `FrameSize` / `FrameAmount` metadata. The
   scanner's packer is `tools/pack_scanner_sheet.py`, run from the repo root;
   it is deterministic, so re-running it on unchanged renders is a no-op.
3. Add or update the sequence in `mods/fracturedsteel/sequences/fracturedsteel.yaml`.
4. Run `./utility.sh --check-yaml`.
5. Launch and verify facings by moving the unit in all eight directions.
6. Commit the sheet and YAML — **never** `art/`.
