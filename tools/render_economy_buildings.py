"""Render original economy-building sprites from academy.blend's camera and lights.

Does not save the .blend. Run:

    /home/justo/Desktop/blender-5.2.1-linux-x64/blender --background \\
        /home/justo/Desktop/FracturedSteel-assets/academy.blend \\
        --python tools/render_economy_buildings.py
"""
from math import ceil
from pathlib import Path

import bpy
from mathutils import Vector

# Packed WPP matches academy (ortho 16.8117 → 160px) and HQ (33.623 → 320px).
WPP = 16.811738967895508 / 160.0
OUT = Path(__file__).resolve().parents[1] / "art/placeholders/buildings"
OUT.mkdir(parents=True, exist_ok=True)

# Pixel frame per building. Ortho is frame * WPP so they share HQ/academy scale.
BUILDINGS = {
    "reactor": 128,
    "plant": 160,
    "vfoundry": 160,
    "turret": 96,
    "mfoundry": 160,
    "assembly": 192,
    "techlab": 128,
}


def mat(name):
    return bpy.data.materials[name]


def link(obj, collection):
    collection.objects.link(obj)
    if obj.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)


def box(col, name, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(location=loc, scale=scale)
    o = bpy.context.active_object
    o.name = name
    if o.data.materials:
        o.data.materials[0] = material
    else:
        o.data.materials.append(material)
    # ops dumps into the scene collection; move into ours.
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def cyl(col, name, loc, r, depth, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    if o.data.materials:
        o.data.materials[0] = material
    else:
        o.data.materials.append(material)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def cone(col, name, loc, r1, depth, material):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    if o.data.materials:
        o.data.materials[0] = material
    else:
        o.data.materials.append(material)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def clear_built(col):
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def build_reactor(col, gray, metal, white):
    box(col, "hall", (0, 0, 0.7), (1.6, 1.2, 0.7), gray)
    box(col, "hallroof", (0, 0, 1.45), (1.7, 1.3, 0.08), metal)
    for y, n in ((-1.6, "towa"), (1.6, "towb")):
        cyl(col, n, (0.2, y, 1.4), 0.85, 2.8, white)
        cone(col, n + "cap", (0.2, y, 3.0), 0.7, 0.5, metal)
    box(col, "pipe", (1.4, 0, 0.9), (0.18, 1.6, 0.18), metal)


def build_plant(col, gray, metal, door, dark):
    box(col, "shed", (0.2, 0, 1.1), (2.2, 1.6, 1.1), gray)
    box(col, "roof", (0.2, 0, 2.28), (2.4, 1.75, 0.1), metal)
    box(col, "door", (2.35, 0, 0.7), (0.08, 0.7, 0.7), door)
    box(col, "hopper", (-1.6, 0.8, 1.4), (0.7, 0.7, 1.4), dark)
    box(col, "belt", (-0.4, 0.8, 0.35), (1.4, 0.25, 0.12), metal)
    cyl(col, "silo", (-1.8, -1.1, 1.2), 0.55, 2.4, metal)


def build_vfoundry(col, gray, metal, door, white):
    box(col, "bay", (0, 0, 1.3), (2.4, 2.0, 1.3), gray)
    box(col, "roof", (0, 0, 2.7), (2.6, 2.2, 0.12), metal)
    box(col, "door", (2.45, 0, 1.0), (0.1, 1.4, 1.0), door)
    box(col, "clerestory", (0, 0, 3.1), (1.8, 0.4, 0.35), white)
    box(col, "stack", (-1.8, 1.5, 3.2), (0.2, 0.2, 0.9), metal)


def build_turret(col, gray, metal, dark):
    box(col, "pad", (0, 0, 0.15), (1.1, 1.1, 0.15), gray)
    box(col, "bags", (0, 0, 0.4), (1.2, 1.2, 0.2), dark)
    cyl(col, "pintle", (0, 0, 0.85), 0.22, 0.7, metal)
    box(col, "gun", (0.7, 0, 1.15), (0.9, 0.12, 0.12), metal)
    box(col, "shield", (0.15, 0, 1.25), (0.08, 0.55, 0.35), gray)


def build_mfoundry(col, gray, metal, door, white):
    box(col, "shop", (0, 0, 1.5), (2.3, 2.1, 1.5), gray)
    box(col, "roof", (0, 0, 3.1), (2.5, 2.3, 0.12), metal)
    box(col, "door", (2.35, 0, 1.1), (0.1, 1.2, 1.1), door)
    # Overhead crane rail
    box(col, "rail", (0, 0, 2.7), (2.2, 0.12, 0.12), metal)
    box(col, "trolley", (0.4, 0, 2.45), (0.4, 0.4, 0.2), white)
    box(col, "hook", (0.4, 0, 1.9), (0.08, 0.08, 0.4), metal)


def build_assembly(col, gray, metal, white, dark):
    box(col, "pad", (0, 0, 0.12), (2.6, 2.6, 0.12), gray)
    # Gantry legs
    for x, y, n in ((-2.2, -2.2, "a"), (2.2, -2.2, "b"), (-2.2, 2.2, "c"), (2.2, 2.2, "d")):
        box(col, "leg" + n, (x, y, 1.6), (0.18, 0.18, 1.6), metal)
    box(col, "beamx", (0, 0, 3.2), (2.5, 0.16, 0.16), metal)
    box(col, "beamy", (0, 0, 3.4), (0.16, 2.5, 0.16), metal)
    box(col, "cabin", (0, 1.6, 1.1), (1.2, 0.7, 1.1), gray)
    box(col, "jig", (0, 0, 0.5), (0.8, 0.8, 0.4), dark)
    box(col, "light", (0, 0, 3.7), (0.2, 0.2, 0.15), white)


def build_techlab(col, gray, metal, white, door):
    box(col, "lab", (0, 0, 1.0), (1.7, 1.5, 1.0), gray)
    box(col, "roof", (0, 0, 2.08), (1.85, 1.65, 0.1), metal)
    box(col, "door", (1.75, 0, 0.55), (0.08, 0.45, 0.55), door)
    cyl(col, "disharm", (0, -1.2, 2.5), 0.08, 1.0, metal)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, location=(0, -1.2, 3.1))
    dish = bpy.context.active_object
    dish.name = "dish"
    dish.scale = (1.0, 0.25, 1.0)
    dish.data.materials.append(white)
    for c in list(dish.users_collection):
        c.objects.unlink(dish)
    col.objects.link(dish)
    box(col, "antenna", (1.2, 1.1, 2.7), (0.06, 0.06, 0.7), metal)


BUILDERS = {
    "reactor": lambda c: build_reactor(c, mat("Gray"), mat("DarkMetal"), mat("White")),
    "plant": lambda c: build_plant(c, mat("Gray"), mat("DarkMetal"), mat("Door"), mat("DarkMetal")),
    "vfoundry": lambda c: build_vfoundry(c, mat("Gray"), mat("DarkMetal"), mat("Door"), mat("White")),
    "turret": lambda c: build_turret(c, mat("Gray"), mat("DarkMetal"), mat("Door")),
    "mfoundry": lambda c: build_mfoundry(c, mat("Gray"), mat("DarkMetal"), mat("Door"), mat("White")),
    "assembly": lambda c: build_assembly(c, mat("Gray"), mat("DarkMetal"), mat("White"), mat("Door")),
    "techlab": lambda c: build_techlab(c, mat("Gray"), mat("DarkMetal"), mat("White"), mat("Door")),
}


def main():
    sc = bpy.context.scene
    cam = sc.objects["RCam"]
    sc.camera = cam
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"

    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = True

    col = bpy.data.collections.new("FSBuild")
    sc.collection.children.link(col)

    for name, px in BUILDINGS.items():
        clear_built(col)
        BUILDERS[name](col)
        bpy.context.view_layer.update()
        cam.data.ortho_scale = px * WPP
        sc.render.resolution_x = px
        sc.render.resolution_y = px
        dest = OUT / f"{name}.png"
        sc.render.filepath = str(dest)
        bpy.ops.render.render(write_still=True)
        print("wrote", dest)


if __name__ == "__main__":
    main()
