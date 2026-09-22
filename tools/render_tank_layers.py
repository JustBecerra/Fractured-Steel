"""Render hull and turret layers from tank.blend. Does not save the .blend.

Run:

    /home/justo/Desktop/blender-5.2.1-linux-x64/blender --background \\
        /home/justo/Desktop/FracturedSteel-assets/tank.blend \\
        --python tools/render_tank_layers.py

Hull keeps the existing camera and 60px frame. Turret meshes are shifted in
XY so the ring sits on the pivot (frame centre); Turreted.Offset then places
that centred sprite on the rear deck.
"""
from math import atan2, cos, pi, sin
from pathlib import Path

import bpy
from mathutils import Vector

FRAME = 60
FACINGS = 32
OUT = Path(__file__).resolve().parents[1] / "art/placeholders/tank"
OUT.mkdir(parents=True, exist_ok=True)

# Turret basket, gun, and pintle MG. Everything else is hull.
TURRET = {
    "Turret", "Cupola", "Mantlet",
    "Barrel", "BarrelRing_1", "BarrelRing_2", "BarrelRing_3",
    "BoreEvac", "BoreEvacFlange_F", "BoreEvacFlange_R", "MuzzleBrake",
    "MG_AmmoBox", "MG_Barrel", "MG_FlashHider", "MG_Pintle", "MG_Receiver",
}


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
    sc.render.resolution_x = FRAME
    sc.render.resolution_y = FRAME
    # Keep the authored ortho so WPP matches the shipping tank sheet.

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    turret_objs = [o for o in meshes if o.name in TURRET]
    missing = TURRET - {o.name for o in turret_objs}
    if missing:
        raise SystemExit(f"missing turret meshes: {sorted(missing)}")

    pivot = sc.objects.get("Pivot")
    if pivot is None:
        raise SystemExit("Pivot empty missing")

    bpy.context.view_layer.update()
    turret = sc.objects["Turret"]
    ring_world = turret.matrix_world.translation.copy()
    pivot_world = pivot.matrix_world.translation.copy()
    print("turret_ring_world", [round(v, 3) for v in ring_world])
    print("pivot_world", [round(v, 3) for v in pivot_world])
    print("offset_blender_xy", [round(ring_world.x - pivot_world.x, 3),
                                round(ring_world.y - pivot_world.y, 3)])

    # Spin the turret around its own ring. Parent-inverse on the hull Pivot
    # means child.location == world, so we reparent onto a dedicated empty.
    spin = bpy.data.objects.new("TurretSpin", None)
    sc.collection.objects.link(spin)
    spin.location = ring_world
    for o in turret_objs:
        mw = o.matrix_world.copy()
        o.parent = spin
        o.matrix_world = mw
    bpy.context.view_layer.update()
    # Centre the ring on the camera look-at (the hull pivot) so the turret
    # sheet is frame-centred. Height stays; Offset in YAML is XY only.
    spin.location.x = pivot_world.x
    spin.location.y = pivot_world.y

    yaws = facing_yaws(cam, FACINGS)
    print("yaws_deg", [round(y * 180 / pi, 1) for y in yaws])

    def render_layer(name, hide_turret, spinner):
        for o in meshes:
            o.hide_render = (o.name in TURRET) if hide_turret else (o.name not in TURRET)
        for i, yaw in enumerate(yaws):
            spinner.rotation_euler = (0.0, 0.0, yaw)
            bpy.context.view_layer.update()
            dest = OUT / f"{name}_{i:02d}.png"
            sc.render.filepath = str(dest)
            bpy.ops.render.render(write_still=True)
        spinner.rotation_euler = (0.0, 0.0, 0.0)
        print("layer", name, "done")

    render_layer("hull", hide_turret=True, spinner=pivot)
    render_layer("turret", hide_turret=False, spinner=spin)


if __name__ == "__main__":
    main()
