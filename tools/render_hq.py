"""Render the HQ's three flag frames plus team-colour masks. Does not save.

Run:

    /home/justo/Desktop/blender-5.2.1-linux-x64/blender --background \\
        /home/justo/Desktop/FracturedSteel-assets/hq.blend \\
        --python tools/render_hq.py

Then pack with tools/pack_hq.py. Renders go to art/placeholders/hq/ at the
file's saved resolution through RCam, the same framing as the shipped sheet.

The flag cloth is rebuilt per frame from the formula that made it. The saved
cloth is frame 0, so the script checks it matches before trusting the rest.
"""
from math import pi, sin
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parents[1] / "art/placeholders/hq"
OUT.mkdir(parents=True, exist_ok=True)

POLE = Vector((-2.407, -4.277, 5.09))
POLE_H = 2.7
FLAG_W = 2.25
FLAG_H = 1.28
NU, NV = 9, 5
N_FRAMES = 3

# Painted in the player's colour: the drum roof, its wall ribs and the belt
# joining them, the door lintel and the ring of low roofs.
TEAM_PREFIXES = ("RoofSlab", "Rib_", "Belt", "Lintel", "OuterRoof_", "CorridorRoof_")


def flag_axes(cam):
    r = (cam.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
    u = (cam.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
    # Flag streams toward 3 o'clock on screen (camera right).
    along = r.copy()
    up = Vector((0.0, 0.0, 1.0))
    up = (up - along * along.dot(up)).normalized()
    normal = along.cross(up).normalized()
    return along, up, normal


def cloth_verts(phase, along, up, normal):
    pole_top = Vector((POLE.x, POLE.y, POLE.z + POLE_H))
    verts = []
    for j in range(NV):
        for i in range(NU):
            u = i / (NU - 1)
            v = j / (NV - 1)
            billow = sin(u * 1.55 * pi + phase) * 0.32 * (u ** 1.1)
            billow += sin(u * 2.7 * pi + phase * 1.35) * 0.08 * u
            lift = sin(u * pi + phase * 0.9) * 0.20 * u
            h = FLAG_H * (1.0 - 0.10 * u)
            p = pole_top + along * (u * FLAG_W)
            p += up * ((v - 0.5) * h + lift - 0.08)
            p += normal * billow
            verts.append(p)
    return verts


def emission_material(name, rgb):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1.0)
    em.inputs["Strength"].default_value = 1.0
    mat.node_tree.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def assign(obj, mat):
    if not obj.material_slots:
        obj.data.materials.append(mat)
    for slot in obj.material_slots:
        slot.link = "OBJECT"
        slot.material = mat


def main():
    sc = bpy.context.scene
    cam = sc.objects["RCam"]
    sc.camera = cam
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    bpy.context.view_layer.update()

    cloth = bpy.data.objects["FlagCloth"]
    along, up, normal = flag_axes(cam)
    saved = [cloth.matrix_world @ v.co for v in cloth.data.vertices]
    expected = cloth_verts(0.0, along, up, normal)
    err = max((a - b).length for a, b in zip(saved, expected))
    if len(saved) != len(expected) or err > 1e-3:
        raise SystemExit(f"FlagCloth no longer matches the frame-0 formula (err {err:.4f})")

    world_to_local = cloth.matrix_world.inverted()

    def pose_flag(phase):
        for v, p in zip(cloth.data.vertices, cloth_verts(phase, along, up, normal)):
            v.co = world_to_local @ p
        cloth.data.update()

    def render_frames(prefix):
        for i in range(N_FRAMES):
            pose_flag(i * 2.0 * pi / N_FRAMES)
            sc.render.filepath = str(OUT / f"{prefix}{i}.png")
            bpy.ops.render.render(write_still=True)
        print("pass", prefix, "done")

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    team = [o for o in meshes if o.name.startswith(TEAM_PREFIXES)]
    print("team parts", sorted(o.name for o in team))

    render_frames("idle")

    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    on = emission_material("TeamMaskOn", (1.0, 1.0, 1.0))
    off = emission_material("TeamMaskOff", (0.0, 0.0, 0.0))
    for o in meshes:
        assign(o, on if o in team else off)
    render_frames("mask")


if __name__ == "__main__":
    main()
