# Fractured Steel — agent context

Read this before making changes. It describes what the project is, how to build and
validate it, and the conventions and gotchas that are easy to get wrong.

## What this is

Fractured Steel is a real-time strategy game built on the **OpenRA** engine using the
**OpenRA Mod SDK**. The design goal is a game about large, *modularly assembled* combat
walkers ("Frames") — you build a chassis and bolt on parts that change its stats and
weapons.

The concept is inspired by the 1999 RTS *Metal Fatigue*, but this is an **original,
legally clean work**. See "Legal constraints" below; it is the one rule in this document
that must never be broken.

- Engine: OpenRA, pinned to `release-20250330` (see `mod.config` → `ENGINE_VERSION`).
- Engine license: GPLv3. Custom C# loaded by the engine must be GPLv3-compatible.
- Mod id: `fracturedsteel`. Platform: developed on Linux.

## Legal constraints (do not violate)

- **No *Metal Fatigue* assets may ship.** No sprites, sounds, names, logos, or text
  derived from Zono/Metal Fatigue in any released build.
- The `art/` directory holds scratch placeholders, some of which *are* derived from
  Metal Fatigue. It is **deliberately untracked** and must stay out of every commit.
  Never `git add art/`.
- Anything shipped must be originally authored (e.g. rendered from our own Blender
  models) or under a compatible license.

## Repository layout

| Path | Purpose |
| --- | --- |
| `mods/fracturedsteel/` | All mod data (MiniYaml + PNG assets). The game itself. |
| `OpenRA.Mods.Example/` | Our custom C# traits, compiled to `OpenRA.Mods.Example.dll`. |
| `engine/` | The OpenRA engine, auto-downloaded. **Gitignored — never edit.** Read it for reference. |
| `art/` | Scratch placeholder art and render output. **Gitignored.** |
| `tools/` | Asset pipeline scripts, run from the repo root. |
| `docs/` | Longer-form documentation. |
| `mod.config` | Mod id, engine version, packaging settings. |

Inside `mods/fracturedsteel/`: `rules/` (actor definitions), `sequences/` (sprite
definitions + `assets/*.png`), `weapons/`, `tilesets/`, `cursors/`, `chrome/` (UI),
`maps/`, `fluent/` (localized strings).

## Commands

Run all of these from the repository root.

```bash
# Build custom C# (OpenRA.Mods.Example) and fetch the engine if missing.
make RUNTIME=net6

# Launch the game.
./launch-game.sh

# Validate all MiniYaml. ALWAYS run this after editing anything under mods/.
export DOTNET_ROOT="$HOME/.dotnet" && export PATH="$HOME/.dotnet:$PATH"
./utility.sh --check-yaml
```

`--check-yaml` is the primary safety net: it catches unknown traits, bad field names,
undefined cursors/palettes/sequences, and broken inheritance. A silent run listing the
mod and its maps means success.

To confirm what an actor *actually* ends up with after inheritance — rather than reading
the yaml and hoping — ask the engine to resolve it:

```bash
./utility.sh --resolved-rules fs_tank
```

There are matching `--resolved-sequences` and `--resolved-weapons` commands. Use these to
verify inheritance instead of assuming a template merged correctly.

Note for sandboxed agents: `make` restores NuGet packages and needs unrestricted network
access, as does `git push`. Both fail with DNS errors under a restricted sandbox.

## Current state

Two units exist, both in `mods/fracturedsteel/rules/fracturedsteel.yaml` and both rendered
from our own Blender models (kept in `~/Desktop/FracturedSteel-assets/`, outside this repo).

`fs_sentinel` ("E-Ship") is a hovering scout from `worker.blend`. **Caveat:** the saved
`worker.blend` is the original pre-thruster state — it has no `Pivot` or `RCam` and no
thruster geometry, because those were added in a live Blender session that was never
saved. The committed sprites are fine, but re-rendering the ship means rebuilding that rig
first (see `docs/asset-pipeline.md` for the camera values).

`fs_tank` ("Tank") is a tracked vehicle from `tank.blend`, with the turret mounted at the
rear over a front engine deck, Merkava/TAM style, and a pintle-mounted FM MAG on the turret
roof. It is slower and heavier than the ship and does not hover. It trails exhaust smoke
from two rear outlets while moving, via two `LeavesTrails` traits.

Its movement comes from the **`^tracked`** template, which every tracked vehicle should
inherit so they all handle alike: pivot in place before setting off
(`TurnsWhileMoving: false`), never arc between cells (`AlwaysTurnInPlace: true`, which the
engine recommends for actors with few sprite facings), a slow turn rate, and reversing out
of short moves rather than three-point turning. The hovering ship deliberately does the
opposite. Tracked units use the `fstracked` locomotor, kept separate from the hover
`fsvehicle` so terrain handling and crushing can diverge later. `tank.blend` was made by
opening `worker.blend` and saving under a new name, so it inherits identical lights, world
and render settings — which is why both units share a look and a pixel scale.

`fs_hq` ("HQ") is an 8×8 round compound from `hq.blend`: a central drum with a front
double door, circular skylight and roof antennas, surrounded by a lower ring of
annexes joined by corridors and fortified with stacked sandbags and barbed wire.

The ship currently has:

- 8-facing rotation via `WithFacingSpriteBody`, driven by `sequences/assets/eship.png`.
- Movement (`Mobile` + `fsvehicle` locomotor + `PathFinder`, both wired up in
  `rules/world.yaml`), turning while moving so orders feel responsive.
- Rear thrusters that light up with blue exhaust only while moving (`WithMoveAnimation`
  swapping to the `move` sequence).
- A subtle idle hover bob (`Hovers`), disabled while moving via
  `GrantConditionOnMovement`.
- A green ground selection ring drawn *beneath* the unit by our custom
  `WithSelectionRing` trait.
- A scanner cone projected from the cabin while deployed, combining a
  `WithIdleOverlay` sprite with a real terrain light from our custom
  `ConditionalTerrainLightSource` trait. Deploying (right-click the selected
  unit) is a **placeholder trigger** standing in for the real
  worker-builds-buildings mechanic, which does not exist yet.

The stock SDK `example` actor and its assets still exist and are inherited from; they are
template leftovers, not final design.

### Not built yet

The Frame assembly concept, economy and base building, tech tree, weapons, and AI are all
still unimplemented. There is no design document yet.

### Gotcha: there is no vision system, and fog silently eats effects

No actor has `RevealsShroud` and the world has no `ShroudRenderer`, so nothing ever grants
vision and fog is never drawn. But the player's `Shroud` trait defaults fog to **on**, and
`Shroud.IsVisible` only reports a cell visible if some source revealed it. The upshot is
*invisible* fog that covers the whole map.

Actors are unaffected because they all carry `AlwaysVisible`. Anything rendered as an
`IEffect` is not: `SpriteEffect.Render()` returns nothing when `world.FogObscures(pos)`, so
smoke, explosions, muzzle flashes and projectile trails all spawn correctly and then draw
nothing. This cost real debugging time once already.

Fog is therefore turned off and locked in `rules/player.yaml`. **If you ever re-enable it,
add `RevealsShroud` to units and a `ShroudRenderer` first**, or every effect in the game
will silently disappear. `VisibleThroughFog: true` is the per-effect escape hatch.

## Conventions

- **MiniYaml is indented with TABS, never spaces.** See `.cursor/rules/miniyaml.mdc`.
- Prefer an existing engine trait over new C#. Search `engine/OpenRA.Mods.Common/Traits/`
  first — the engine has far more built in than is obvious, and stock traits need no
  rebuild. `Hovers` and `GrantConditionOnMovement` were both found this way instead of
  being written from scratch.
- Only write custom C# when no stock trait can do the job. See
  `.cursor/rules/custom-traits.mdc`.
- Keep commits scoped to one feature.

## Further reading

- `docs/asset-pipeline.md` — how sprites are produced in Blender and packed into sheets,
  including the isometric facing math. Read this before touching any unit sprite.
