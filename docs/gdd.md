# Fractured Steel — Game Design Document

Vertical slice for the `fracturedsteel` OpenRA mod. One faction versus the built-in skirmish AI. Fiction and lore are out of scope.

## Faction

| | |
| --- | --- |
| Working name | Ferro Union |
| Internal id | `example` (existing map/faction id; display name is Ferro Union) |
| Economy | Alloy salvaged from junkyards by the tracked dozer, processed at the Processing Plant |
| Signature unit | **Frame** — a war-mech assembled from torso, legs, and two arms |

## Win condition

Destroy the enemy base in a skirmish vs the built-in AI on **Steel Arena**.

## Tech tree

Build order (arrows are prerequisites). `+` means those buildings unlock together from the same parent.

```
HQ
 └─ Reactor
     └─ Processing Plant
         ├─ Vehicle Foundry
         ├─ Defense Turret
         └─ Crew Academy
             └─ Mech Foundry
                 └─ Mech Assembly
                     └─ Tech Lab
```

| Building | Size | Cost | Time (sec) | Power | Role |
| --- | --- | --- | --- | --- | --- |
| HQ | 8×8 | — (starts placed) | — | 0 | Base, building/defense queues, build radius |
| Reactor | 3×3 | 500 | 8 | **+80** | Power |
| Processing Plant | 4×3 | 1500 | 16 | −30 | Alloy drop-off; spawns one dozer |
| Vehicle Foundry | 4×4 | 2000 | 20 | −40 | Paladin |
| Defense Turret | 2×2 | 600 | 10 | −15 | Fixed gun |
| Crew Academy | 5×4 | 1000 | 14 | −20 | Prerequisite for Mech Foundry |
| Mech Foundry | 4×4 | 2500 | 24 | −50 | Prerequisite for Mech Assembly |
| Mech Assembly | 5×5 | 3000 | 28 | −50 | Produces Frames; loadout UI |
| Tech Lab | 3×3 | 2000 | 20 | −30 | End of this slice's tree |

Starting cash: **5000**. Each junkyard dump: **30000** Alloy (1 cell × density 60 × 500 credits). Processing Plant storage: **20000**.

## Units

| Unit | Produced at | Cost | Time (sec) | HP | Speed | Role |
| --- | --- | --- | --- | --- | --- | --- |
| Tracked dozer | Processing Plant (free on place) | — | — | 500 | 64 | Harvest Alloy from junkyards |
| Paladin | Vehicle Foundry | 900 | 12 | 900 | 64 | Tracked gun vehicle |
| Frame | Mech Assembly | 2200 | 24 | 1200* | 48* | Modular mech |

\*Frame HP/speed after Assault torso + Bipedal legs. See part catalog.

Starting force: HQ. Extra dozers come from extra Processing Plants, not the Vehicle Foundry.

## Frame part catalog (initial)

Four slots. This slice ships one option per slot. Later parts hook in as extra conditions on the same `fs_frame` actor.

### Torso

| Part | Condition | Effect |
| --- | --- | --- |
| **Assault** | `torso-assault` | Armor type Heavy. Incoming damage **100%** (baseline). Production cost modifier **100%**. |

### Legs

| Part | Condition | Effect |
| --- | --- | --- |
| **Bipedal** | `legs-bipedal` | Speed **48**. All-terrain (Clear + Alloy). Speed multiplier **100%**. |

### Arms

| Part | Slot | Condition | Effect |
| --- | --- | --- | --- |
| **Sword** | Left | `arm-sword` | Melee, range 1.5 cells, 4000 damage, reload 30 ticks |
| **Shield** | Right | `arm-shield` | Incoming damage **80%** (DamageMultiplier 80). No weapon |

Default loadout (hard-coded until the player changes it at Mech Assembly): Assault + Bipedal + Sword + Shield.

## Combat notes

- Paladin and Defense Turret use an instant-hit cannon (range 6 cells, 2500 damage, reload 25 ticks).
- Sword is melee (`InstantHit`, short range). Shield is defensive only.
- Torso durability is `Armor` + conditional `DamageMultiplier` (OpenRA has no max-HP swap).

## AI

One ModularBot ("Ferro Union AI") that builds the tech tree, harvests Alloy, trains Paladins and Frames, and attacks on Steel Arena.
