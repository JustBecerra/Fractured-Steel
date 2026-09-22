"""Render layered Frame sprites from tank.blend's camera and lights.

Does not save the .blend. Run:

    /home/justo/Desktop/blender-5.2.1-linux-x64/blender --background \\
        /home/justo/Desktop/FracturedSteel-assets/tank.blend \\
        --python tools/render_frame.py
"""
from math import atan2, cos, pi, sin
from pathlib import Path

import bpy
from mathutils import Vector

WPP_PACKED = 6.304 / 60.0  # tank ortho / tank frame px
FRAME = 96
FACINGS = 32
OUT = Path(__file__).resolve().parents[1] / "art/placeholders/frame"
OUT.mkdir(parents=True, exist_ok=True)

LAYERS = ("legs", "torso", "sword", "shield")


def mat(name, fallback="Material"):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    for m in bpy.data.materials:
        if m.users:
            return m
    return bpy.data.materials[0]


def place(col, obj):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def box(col, name, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(location=loc, scale=scale)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    place(col, o)
    return o


def cyl(col, name, loc, r, depth, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    place(col, o)
    return o


def build_frame(col, steel, dark, blade, shield_mat):
    # Forward is +X. Legs.
    for y, n in ((-0.35, "L"), (0.35, "R")):
        cyl(col, "thigh" + n, (0.05, y, 0.85), 0.16, 0.9, steel)
        cyl(col, "shin" + n, (0.12, y, 0.35), 0.13, 0.7, dark)
        box(col, "foot" + n, (0.25, y, 0.06), (0.35, 0.16, 0.06), dark)
        box(col, "hip" + n, (0.0, y, 1.25), (0.22, 0.18, 0.12), steel)

    # Assault torso.
    box(col, "torso", (0.0, 0.0, 1.7), (0.55, 0.45, 0.5), steel)
    box(col, "chest", (0.25, 0.0, 1.75), (0.2, 0.4, 0.35), dark)
    box(col, "head", (0.15, 0.0, 2.25), (0.22, 0.22, 0.18), dark)
    box(col, "visor", (0.35, 0.0, 2.28), (0.06, 0.18, 0.08), blade)

    # Sword in the left hand (−Y).
    box(col, "grip", (0.15, -0.7, 1.55), (0.06, 0.06, 0.18), dark)
    box(col, "blade", (0.55, -0.7, 1.55), (0.55, 0.04, 0.08), blade)
    box(col, "guard", (0.22, -0.7, 1.55), (0.04, 0.16, 0.16), steel)

    # Shield in the right hand (+Y).
    box(col, "shield", (0.2, 0.75, 1.6), (0.12, 0.45, 0.55), shield_mat)
    box(col, "boss", (0.34, 0.75, 1.6), (0.04, 0.12, 0.12), steel)

    for o in col.objects:
        if o.name.startswith(("thigh", "shin", "foot", "hip")):
            o["layer"] = "legs"
        elif o.name in ("torso", "chest", "head", "visor"):
            o["layer"] = "torso"
        elif o.name in ("grip", "blade", "guard"):
            o["layer"] = "sword"
        else:
            o["layer"] = "shield"


def facing_yaws(cam, count):
    bpy.context.view_layer.update()
    r = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
    u = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))

    def screen_angle(yaw):
        v = Vector((cos(yaw), sin(yaw), 0.0))
        return atan2(v.dot(r), v.dot(u)) % (2 * pi)

    yaws = []
    for i in range(count):
        target = (i * 2 * pi / count) % (2 * pi)
        best, best_err = 0.0, 99.0
        for s in range(720):
            yaw = s * 2 * pi / 720
            err = abs((screen_angle(yaw) - target + pi) % (2 * pi) - pi)
            if err < best_err:
                best, best_err = yaw, err
        yaws.append(best)
    return yaws


def main():
    sc = bpy.context.scene
    cam = sc.objects.get("RCam") or sc.camera
    sc.camera = cam
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    cam.data.ortho_scale = FRAME * WPP_PACKED
    sc.render.resolution_x = FRAME
    sc.render.resolution_y = FRAME

    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = True

    col = bpy.data.collections.new("FSFrame")
    sc.collection.children.link(col)

    steel = mat("Gray")
    dark = mat("DarkMetal")
    blade = mat("White")
    shield_mat = mat("Door")
    build_frame(col, steel, dark, blade, shield_mat)

    pivot = bpy.data.objects.new("FramePivot", None)
    sc.collection.objects.link(pivot)
    pivot.scale = (3.2, 3.2, 3.2)
    for o in col.objects:
        o.parent = pivot

    yaws = facing_yaws(cam, FACINGS)
    print("yaws_deg", [round(y * 180 / pi, 1) for y in yaws])

    for layer in LAYERS:
        for o in col.objects:
            o.hide_render = o.get("layer") != layer
        for i, yaw in enumerate(yaws):
            pivot.rotation_euler = (0.0, 0.0, yaw)
            bpy.context.view_layer.update()
            dest = OUT / f"{layer}_{i:02d}.png"
            sc.render.filepath = str(dest)
            bpy.ops.render.render(write_still=True)
        print("layer", layer, "done")


if __name__ == "__main__":
    main()
