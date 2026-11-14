"""Dwelling houses of the village.

Every function builds one unique house into a MeshBuilder.  Conventions:
origin = centre of the footprint on the ground, the main door looks towards
-Y, units are studs.  Houses are exterior shells (not enterable).
"""
import math

from .building import (Wing, win, door, finish, window, porch, awning, hanging_sign, balcony,
                       ext_stairs, bay_window, spire, steps, wall_lantern, chimney)
from .meshkit import T, R


def wins(n, lo=0.0, hi=1.0, **kw):
    """n evenly spaced windows between the wall fractions lo..hi."""
    return [win(lo + (hi - lo) * (i + 0.5) / n, **kw) for i in range(n)]


# ---------------------------------------------------------------------
def house_01_timber_cottage(mb):
    """Reference house: stone ground floor, jettied half-timbered upper floor."""
    wg = Wing(mb, 24, 18, found=1.6)
    wg.storey(10.5, style="stone", openings={
        "front": [door(0.29, arch=True, hood="roof_red", lantern=1),
                  win(0.72, shutters="cloth_green", flowerbox="flower_red")],
        "right": [win(0.5, w=2.6)],
        "left": [win(0.38)],
        "back": [win(0.28), win(0.72)]})
    wg.storey(9.5, style="timber", color="plaster_cream", jetty={"front": 1.3}, openings={
        "front": [win(0.24, z=2.9, shutters="cloth_green"),
                  win(0.72, z=2.9, shutters="cloth_green", flowerbox="flower_yellow")],
        "right": [win(0.5, z=2.9)],
        "left": [win(0.5, z=2.9, lit=True)],
        "back": [win(0.5, z=2.9)]})
    wg.gable("roof_red", ridge="x", pitch=53, gable_win="round")
    wg.chimney(-6.5, 2.6)
    wg.dormer(5.0, side=-1, roof="roof_red", lit=True)
    finish(mb, wg.z + wg.roof_h)


def house_02_gabled_townhouse(mb):
    """Narrow three-storey town house, gable to the street, double jetty."""
    wg = Wing(mb, 18, 24, found=1.2)
    wg.storey(10.5, style="plaster", color="plaster_rose", band="stone_light", openings={
        "front": [door(0.28, color="wood_dark", lantern=-1),
                  win(0.7, w=3.6, h=4.6, z=3.0, arch=True, muntins=(2, 1))],
        "left": wins(2), "right": wins(2, lit=True), "back": [win(0.5)]})
    wg.storey(9.0, style="timber", color="plaster_white", pattern="x", jetty=1.2, openings={
        "front": wins(2, z=2.8, shutters="cloth_blue"),
        "left": [win(0.3, z=2.8)], "right": [win(0.65, z=2.8)]})
    wg.storey(8.0, style="timber", color="plaster_white", pattern="grid", jetty=1.0, openings={
        "front": [win(0.5, z=2.6, w=4.4, h=3.6, muntins=(2, 1), flowerbox="flower_purple")]})
    wg.gable("roof_slate", ridge="y", pitch=60, gable_win="hatch", og=2.0)
    wg.chimney(6.0, 3.0, color="brick")
    finish(mb, wg.z + wg.roof_h)


def house_03_thatched_cottage(mb):
    """Low whitewashed cottage under a thick thatched roof."""
    wg = Wing(mb, 26, 17, found=0.8, found_color="stone_warm")
    small = dict(w=2.6, h=3.0, z=3.0)
    wg.storey(8.5, style="plaster", color="plaster_white", openings={
        "front": [door(0.5, arch=True, w=3.8, h=6.8, color="wood_light"),
                  win(0.17, shutters="cloth_blue", flowerbox="flower_blue", **small),
                  win(0.83, shutters="cloth_blue", flowerbox="flower_white", **small)],
        "left": [win(0.5, **small)], "right": [win(0.5, **small)],
        "back": wins(2, **small)})
    wg.gable("thatch", ridge="x", pitch=50, th=1.3, courses=4, lip=0.5, shape=0.72, oe=2.8, og=2.2,
             sag=0.7, trim=None, ridge_color="thatch_dark", gable_win="small", K=6)
    wg.chimney(7.5, 0.4, w=3.4, d=2.8, color="stone_warm", sink=3.5)
    finish(mb, wg.z + wg.roof_h, taper=0.05)


def house_04_farmhouse(mb):
    """L-shaped farmhouse with a cross gable towards the street."""
    a = Wing(mb, 28, 17, found=1.5)
    a.storey(10.0, style="stone", openings={
        "front": [win(0.14), win(0.4, shutters="cloth_red")],
        "left": [win(0.5)], "right": [win(0.3)], "back": wins(3)})
    a.storey(9.0, style="timber", color="plaster_yellow", pattern="k", openings={
        "front": [win(0.14, z=2.8), win(0.4, z=2.8, flowerbox="flower_red")],
        "left": [win(0.5, z=2.8)], "right": [win(0.3, z=2.8)], "back": wins(2, z=2.8)})
    a.gable("roof_brown", ridge="x", pitch=50, gable_win="small")
    b = Wing(mb, 14, 20, cx=7.0, cy=-10.0, found=1.5)
    b.storey(10.0, style="stone", openings={
        "front": [door(0.5, arch=True, hood="roof_brown", lantern=1)],
        "left": [win(0.22)], "right": [win(0.3)]})
    b.storey(9.0, style="timber", color="plaster_yellow", jetty=1.0, openings={
        "front": [win(0.5, z=2.8, w=3.8, muntins=(2, 1), shutters="cloth_red", flowerbox="flower_yellow")]})
    b.gable("roof_brown", ridge="y", pitch=52, gable_win="round", gables=(True, False), og=(1.6, -1.2))
    a.chimney(-9.0, 2.4, w=3.0)
    a.dormer(-4.0, side=-1, roof="roof_brown")
    finish(mb, a.z + a.roof_h)


def house_05_bakery(mb):
    """Bakery with a wide shop window, striped awning and a big oven chimney."""
    wg = Wing(mb, 26, 18, found=1.0)
    wg.storey(10.5, style="plaster", color="plaster_peach", band="stone_light", openings={
        "front": [door(0.19, peek=True, color="wood_red", lantern=-1),
                  win(0.63, w=8.0, h=4.6, z=2.8, muntins=(3, 1), sill="wood_light", lit=True)],
        "left": [win(0.5)], "right": [win(0.5)], "back": [win(0.3), door(0.75, no_steps=True)]})
    with wg.wall("front"):
        awning(mb, 0.63 * 26, 8.3, 9.6)
        hanging_sign(mb, 1.3, 9.6, emblem="cloth_yellow")
        mb.box(5.0, 1.6, 2.4, "wood_light", pos=(22.5, -1.2, -1.0))          # display bench
        for i in range(3):
            mb.blob(0.55, "plaster_yellow", pos=(21.2 + i * 1.3, -1.2, 1.75), level=0, noise=0.08,
                    scale=(1, 0.8, 0.6), grad=(0.3, 0.6))                    # bread loaves
    wg.storey(9.0, style="timber", color="plaster_yellow", pattern="herring", jetty=1.0, openings={
        "front": wins(3, z=2.8, shutters="wood_red"),
        "left": [win(0.5, z=2.8)], "right": [win(0.5, z=2.8)], "back": wins(2, z=2.8)})
    wg.gable("roof_orange", ridge="x", pitch=50, gable_win="lit")
    wg.chimney(-9.5, 3.2, w=3.8, d=3.2, pots=2, color="brick", extra=4.0)
    finish(mb, wg.z + wg.roof_h)


def house_06_crooked_tower_house(mb):
    """Tall, narrow and slightly crooked, with a steep witch-hat roof."""
    wg = Wing(mb, 16, 15, found=1.3)
    wg.storey(10.0, style="stone", openings={
        "front": [door(0.5, arch=True, color="wood_red", lantern=1)],
        "left": [win(0.5, w=2.4)], "right": [win(0.5, w=2.4)]})
    wg.storey(8.5, style="timber", color="plaster_sage", pattern="x",
              jetty={"front": 1.1, "left": 0.6, "right": 0.6}, openings={
        "front": [win(0.5, z=2.6, w=3.6, muntins=(2, 1), flowerbox="flower_white")],
        "left": [win(0.5, z=2.6)], "right": [win(0.5, z=2.6, lit=True)]})
    wg.storey(8.0, style="timber", color="plaster_sage", pattern="brace",
              jetty={"front": 1.0, "left": 0.5, "right": 0.5}, openings={
        "front": wins(2, z=2.4, w=2.4, h=3.4, shutters="wood_red"),
        "back": [win(0.5, z=2.4)]})
    wg.gable("roof_teal", ridge="y", pitch=63, shape=0.66, gable_win="shutter", oe=2.4, og=1.8,
             sag=0.6)
    wg.chimney(2.5, -3.2, color="stone_dark", w=2.2, d=2.0)
    finish(mb, wg.z + wg.roof_h, lean=(0.016, -0.006))


def house_07_stone_manor(mb):
    """Well-to-do two-storey stone house with arched windows and a hip roof."""
    wg = Wing(mb, 28, 20, found=1.8, found_color="stone_dark")
    stones = ("stone_light", "stone_grey", "stone_dark")
    aw = dict(arch=True, h=4.8, z=3.0, muntins=(1, 1))
    wg.storey(10.5, style="stone", color="stone_warm", stone_colors=stones, openings={
        "front": [door(0.5, double=True, w=5.0, h=8.0, arch=True, hood="roof_slate", color="wood_dark"),
                  win(0.16, **aw), win(0.84, **aw)],
        "left": wins(2, **aw), "right": wins(2, **aw), "back": wins(3, **aw)})
    with wg.wall("front"):
        wall_lantern(mb, 0.5 * 28 - 4.6, 5.4)
        wall_lantern(mb, 0.5 * 28 + 4.6, 5.4)
    aw2 = dict(arch=True, h=4.4, z=2.6, muntins=(1, 1))
    wg.storey(9.5, style="stone", color="stone_warm", stone_colors=stones, band="stone_light", openings={
        "front": wins(3, shutters="cloth_blue", **aw2),
        "left": wins(2, **aw2), "right": wins(2, **aw2), "back": wins(3, **aw2)})
    wg.hip("roof_slate", pitch=47)
    wg.chimney(-10.5, 0.0, color="stone_warm", w=2.8, d=2.8, sink=4.0)
    wg.chimney(10.5, 0.0, color="stone_warm", w=2.8, d=2.8, sink=4.0)
    finish(mb, wg.z + wg.roof_h, taper=0.025)


def house_08_plank_cabin(mb):
    """Wooden cabin with a gambrel roof and a covered porch."""
    wg = Wing(mb, 24, 16, found=1.6, found_color="stone_warm")
    wg.storey(9.5, style="plank", color="wood_light", openings={
        "front": [door(0.5, color="wood_dark", no_steps=True),
                  win(0.17, shutters="cloth_red"), win(0.83, shutters="cloth_red")],
        "left": [win(0.5)], "right": [win(0.5)], "back": wins(2)})
    with wg.wall("front"):
        W = 24
        mb.box(W - 3, 5.2, 0.4, "wood_pale", pos=(W / 2, -2.6, -0.4))               # deck
        mb.box(W - 3.4, 4.8, 1.8, "stone_warm", pos=(W / 2, -2.5, -2.2), tone=-0.1)
        porch(mb, 1.5, W - 3, 5.2, 7.2, 1.7, "roof_green", post="wood_dark", n_posts=4, rail=False)
        with mb.at(T(0, -5.2, 0)):
            steps(mb, W / 2, 1.6, w=6.0, color="wood_pale")
    wg.gable("roof_green", ridge="x", H=10.5, shape="gambrel", gable="plank", gable_color="wood_light",
             gable_win="small", courses=8, oe=1.6)
    wg.chimney(8.0, 2.0, color="stone_warm")
    finish(mb, wg.z + wg.roof_h, taper=0.02)


def house_09_twin_gable(mb):
    """Wide house with two cross gables facing the street."""
    a = Wing(mb, 32, 17, found=1.4)
    a.storey(10.0, style="plaster", color="plaster_blue", band="stone_light", openings={
        "front": [door(0.5, hood="roof_slate", color="wood_light", lantern=1)],
        "left": [win(0.5)], "right": [win(0.5)], "back": wins(3)})
    a.storey(9.0, style="timber", color="plaster_blue", pattern="grid", openings={
        "front": [win(0.5, z=2.8, lit=True)],
        "left": [win(0.5, z=2.8)], "right": [win(0.5, z=2.8)], "back": wins(3, z=2.8)})
    a.gable("roof_slate", ridge="x", pitch=50, gable_win="small")
    for sx in (-1, 1):
        b = Wing(mb, 10.5, 10.5, cx=sx * 10.0, cy=-5.25, found=1.4)
        b.storey(10.0, style="plaster", color="plaster_blue", band="stone_light", openings={
            "front": [win(0.5, w=3.4, muntins=(2, 1), shutters="cloth_white", flowerbox="flower_red")]})
        b.storey(9.0, style="timber", color="plaster_blue", pattern="brace", jetty=0.8, openings={
            "front": [win(0.5, z=2.8, w=3.2, shutters="cloth_white")]})
        b.gable("roof_slate", ridge="y", pitch=58, gable_win="arch", gables=(True, False), og=(1.5, -1.2),
                oe=1.6)
    a.chimney(0.0, 2.2, color="stone_grey")
    finish(mb, a.z + a.roof_h)


def house_10_saltbox(mb):
    """Asymmetric roof: short steep front slope, long back slope."""
    wg = Wing(mb, 22, 22, found=1.2)
    wg.storey(10.0, style="plaster", color="plaster_peach", openings={
        "front": [door(0.5, color="wood_dark", hood="roof_brown"),
                  win(0.16, shutters="cloth_green"), win(0.84, shutters="cloth_green")],
        "left": wins(2), "right": wins(2), "back": [win(0.3), win(0.7)]})
    wg.storey(6.5, style="timber", color="plaster_peach", pattern="grid", openings={
        "front": wins(3, z=1.6, w=2.6, h=3.4)})
    wg.gable("roof_brown", ridge="x", H=11.0, asym=-4.5, gable_win="small", shape=0.9)
    wg.chimney(0.0, -3.0, w=3.2, d=3.0, color="brick", pots=2)
    finish(mb, wg.z + wg.roof_h)


def house_11_stair_house(mb):
    """Workshop below, dwelling above, reached by an outside staircase."""
    wg = Wing(mb, 22, 18, found=1.4)
    wg.storey(10.0, style="stone", openings={
        "front": [door(0.3, double=True, w=5.4, h=7.6, color="wood_mid"),
                  win(0.76, w=3.4, muntins=(2, 1))],
        "right": [win(0.5)], "back": wins(2)})
    with wg.wall("left"):
        ext_stairs(mb, 17.2, 0.8, 10.0 + 1.4, z_ground=-1.4)
    wg.storey(9.0, style="timber", color="plaster_sage", pattern="brace", openings={
        "front": [win(0.24, z=2.8, shutters="wood_red"), door(0.7, w=3.2, h=6.8, color="wood_red")],
        "left": [door(0.17, w=3.2, h=6.8, color="wood_red"), win(0.66, z=2.8)],
        "right": [win(0.5, z=2.8)], "back": wins(2, z=2.8)})
    with wg.wall("front"):
        balcony(mb, 0.7 * 22, 0.0, 8.0)
    wg.gable("roof_red", ridge="x", pitch=51, gable_win="lit")
    wg.chimney(6.0, 2.5)
    finish(mb, wg.z + wg.roof_h, taper=0.02)


def house_12_turret_house(mb):
    """Corner house with an oriel and a round corner turret."""
    wg = Wing(mb, 22, 18, found=1.5)
    wg.storey(10.5, style="plaster", color="plaster_white", band="stone_light", frame="wood_red", openings={
        "front": [door(0.6, arch=True, color="wood_red", frame="wood_red", lantern=1)],
        "right": wins(2, frame="wood_red"), "back": wins(2, frame="wood_red")})
    wg.storey(9.5, style="timber", color="plaster_white", frame="wood_red", pattern="k", openings={
        "right": wins(2, z=2.8), "back": wins(2, z=2.8), "left": [win(0.35, z=2.8)]})
    with wg.wall("front"):
        bay_window(mb, 0.66 * 22, 1.6, w=6.4, h=6.0, color="plaster_white", frame="wood_red",
                   roof="roof_purple", lit=True)
    wg.gable("roof_purple", ridge="x", pitch=52, gable_win="round", gable_frame="wood_red", trim="wood_red")
    # turret on the front-left corner
    tx, ty, r = -11.0, -9.0, 4.4
    mb.collider_cyl((tx, ty, 14.0), r + 0.3, 36.0)
    ap = r * math.cos(math.pi / 8)
    h = wg.z + 4.0
    mb.cyl(r + 0.5, r + 0.3, 5.5, "stone_grey", pos=(tx, ty, -4.0), segs=8, phase=math.pi / 8, smooth=False)
    mb.cyl(r, r - 0.15, h - 1.5, "plaster_white", pos=(tx, ty, 1.5), segs=8, phase=math.pi / 8,
           smooth=False, grad=(0.42, 0.62))
    for z in (1.5 + 9.5, h - 0.6):
        mb.cyl(r + 0.25, r + 0.25, 0.6, "wood_red", pos=(tx, ty, z), segs=8, phase=math.pi / 8, smooth=False)
    for ang in (0, -45, -90):
        for z in (4.6, 14.0):
            with mb.at(T(tx, ty, z), R("Z", ang), T(0, -ap + 0.1, 0)):
                window(mb, 0, 0, w=1.7, h=3.6, frame="wood_red", arch=True, muntins=(0, 1), sill=None,
                       lit=(z > 10 and ang == -45))
    with mb.at(T(tx, ty, h)):
        spire(mb, ap - 0.1, 12.5, "roof_purple", segs=8, courses=5, o=1.3)
    wg.chimney(6.5, 2.4)
    finish(mb, wg.z + wg.roof_h, taper=0.02)


def house_13_fisher_hut(mb):
    """Small weathered plank hut with a dark thatched roof."""
    wg = Wing(mb, 16, 13, found=2.0, found_color="stone_dark")
    wg.storey(8.0, style="plank", color="wood_grey", openings={
        "front": [door(0.36, w=3.4, h=6.4, color="wood_mid"), win(0.78, w=2.2, h=2.6, z=3.2)],
        "right": [win(0.5, w=2.2, h=2.6, z=3.2)], "left": [win(0.5, w=2.2, h=2.6, z=3.2, lit=True)]})
    with wg.wall("right"):                                       # drying rack with fish
        mb.box(0.3, 0.3, 6.5, "wood_dark", pos=(2.0, -2.6, -2.0))
        mb.box(0.3, 0.3, 6.5, "wood_dark", pos=(11.0, -2.6, -2.0))
        mb.beam((1.6, -2.6, 4.3), (11.4, -2.6, 4.3), 0.25, 0.25, "wood_dark")
        for i in range(5):
            mb.blob(0.42, "glass_light", pos=(3.2 + i * 1.6, -2.6, 3.5), scale=(0.35, 0.3, 1.5), level=0,
                    noise=0.05, grad=(0.3, 0.7))
    wg.gable("thatch_dark", ridge="x", pitch=52, th=1.1, courses=4, lip=0.45, shape=0.75, oe=2.2, og=1.8,
             sag=0.6, trim=None, gable="plank", gable_color="wood_grey", gable_win="round", K=5)
    wg.chimney(-4.0, 1.0, w=2.2, d=2.0, color="stone_dark", sink=3.0)
    finish(mb, wg.z + wg.roof_h, taper=0.04, lean=(-0.01, 0.0))


def house_14_long_weaver_house(mb):
    """Long, low half-timbered house with a row of dormers."""
    wg = Wing(mb, 36, 15, found=1.2)
    wg.storey(10.5, style="timber", color="plaster_cream", pattern="herring", openings={
        "front": [door(0.5, color="wood_mid", hood="roof_red", lantern=-1),
                  win(0.12, shutters="cloth_green"), win(0.3, shutters="cloth_green", flowerbox="flower_red"),
                  win(0.7, shutters="cloth_green", flowerbox="flower_yellow"), win(0.88, shutters="cloth_green")],
        "left": [win(0.5)], "right": [win(0.5)], "back": wins(4)})
    wg.gable("roof_red", ridge="x", pitch=55, gable_win="small", K=7, sag=0.7)
    for x in (-11.0, 0.0, 11.0):
        wg.dormer(x, side=-1, roof="roof_red", lit=(x == 0.0))
    wg.chimney(-14.0, 1.6)
    wg.chimney(13.0, -1.6, color="brick")
    finish(mb, wg.z + wg.roof_h)


def house_15_tower_house(mb):
    """Square three-storey house under a tall pyramid roof."""
    wg = Wing(mb, 17, 17, found=1.6, found_color="stone_dark")
    wg.storey(11.0, style="stone", openings={
        "front": [door(0.5, arch=True, w=4.2, color="wood_dark", lantern=1)],
        "left": [win(0.5, w=2.2, h=3.4)], "right": [win(0.5, w=2.2, h=3.4)]})
    j1 = {"front": 0.8, "back": 0.8, "left": 0.8, "right": 0.8}
    wg.storey(9.0, style="timber", color="plaster_cream", pattern="brace", jetty=j1, openings={
        "front": wins(2, z=2.8, shutters="cloth_red"), "left": [win(0.5, z=2.8)],
        "right": [win(0.5, z=2.8, lit=True)], "back": [win(0.5, z=2.8)]})
    j2 = {"front": 0.6, "back": 0.6, "left": 0.6, "right": 0.6}
    wg.storey(8.0, style="timber", color="plaster_cream", pattern="x", jetty=j2, openings={
        "front": [win(0.5, z=2.4, w=3.6, muntins=(2, 1), flowerbox="flower_red")],
        "left": [win(0.5, z=2.4)], "right": [win(0.5, z=2.4)], "back": [win(0.5, z=2.4)]})
    with mb.at(T(wg.ox, wg.oy, wg.z)):
        spire(mb, wg.cw / 2, 15.0, "roof_orange", segs=4, courses=7, o=2.0, flare=0.85)
    wg.roof_h = 15.0
    finish(mb, wg.z + 15.0, taper=0.03)


def house_16_porch_tower_house(mb):
    """White house with ox-blood timbers and a tall gabled entrance bay."""
    a = Wing(mb, 28, 16, found=1.5)
    f = "wood_red"
    a.storey(10.0, style="timber", color="plaster_white", frame=f, pattern="grid", openings={
        "front": [win(0.14, frame=f, shutters="cloth_green"), win(0.86, frame=f, shutters="cloth_green")],
        "left": [win(0.5)], "right": [win(0.5)], "back": wins(3)})
    a.storey(8.5, style="timber", color="plaster_white", frame=f, pattern="brace", openings={
        "front": [win(0.14, z=2.6), win(0.86, z=2.6)],
        "left": [win(0.5, z=2.6)], "right": [win(0.5, z=2.6)], "back": wins(3, z=2.6)})
    a.gable("roof_teal", ridge="x", pitch=50, gable_win="small", gable_frame=f, trim=f)
    b = Wing(mb, 11, 11, cy=-8.5, found=1.5)
    b.storey(10.0, style="timber", color="plaster_white", frame=f, pattern="grid", openings={
        "front": [door(0.5, arch=True, color="wood_red", hood="roof_teal", lantern=1)]})
    b.storey(8.5, style="timber", color="plaster_white", frame=f, pattern="x", jetty=0.8, openings={
        "front": [win(0.5, z=2.6, w=3.4, muntins=(2, 1), flowerbox="flower_red")],
        "left": [win(0.35, z=2.6, w=2.2)], "right": [win(0.65, z=2.6, w=2.2)]})
    b.storey(7.0, style="timber", color="plaster_white", frame=f, pattern="brace", jetty=0.6, openings={
        "front": [win(0.5, z=2.0, w=2.6, h=3.4, lit=True)]})
    b.gable("roof_teal", ridge="y", pitch=62, gable_win="round", gable_frame=f, trim=f, og=(1.8, 1.0),
            shape=0.75)
    a.chimney(-9.0, 2.2)
    finish(mb, b.z + b.roof_h)


def house_17_red_barn(mb):
    """Big red barn with a gambrel roof and white trim."""
    wg = Wing(mb, 30, 24, found=0.8, found_color="stone_warm")
    tr = "plaster_white"
    wg.storey(11.5, style="plank", color="wood_red", frame=tr, openings={
        "front": [door(0.5, double=True, w=9.0, h=9.6, color="wood_red", frame=tr, fw=0.7)],
        "left": wins(2, w=2.4, h=2.4, z=6.0, frame=tr, sill=None),
        "right": wins(2, w=2.4, h=2.4, z=6.0, frame=tr, sill=None),
        "back": [door(0.5, w=4.0, h=7.4, color="wood_red", frame=tr, no_steps=True)]})
    with wg.wall("front"):                                      # white X bracing on the doors
        for sx in (-1, 1):
            x0, x1 = 15 + sx * 0.4, 15 + sx * 4.3
            mb.beam((x0, -0.3, 0.6), (x1, -0.3, 9.0), 0.4, 0.14, tr, up=(0, 1, 0))
            mb.beam((x0, -0.3, 9.0), (x1, -0.3, 0.6), 0.4, 0.14, tr, up=(0, 1, 0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(0.9, 0.9, 11.5, tr, pos=(sx * 14.9, sy * 11.9, 0.8))
    wg.gable("roof_brown", ridge="y", H=12.5, shape="gambrel", gable="plank", gable_color="wood_red",
             gable_frame=tr, trim=tr, gable_win="hatch", courses=8, oe=1.6, og=2.0, sag=0.5)
    finish(mb, wg.z + wg.roof_h, taper=0.015)


def house_18_tiny_cottage(mb):
    """One-room cottage with an oversized chimney."""
    wg = Wing(mb, 15, 12, found=1.0, found_color="stone_warm")
    wg.storey(8.5, style="plaster", color="plaster_yellow", openings={
        "front": [door(0.34, arch=True, w=3.6, h=6.6, color="wood_dark", lantern=1),
                  win(0.78, w=2.4, h=3.0, z=3.0, shutters="roof_purple", flowerbox="flower_purple")],
        "left": [win(0.5, w=2.4, h=3.0, z=3.0)], "back": [win(0.5, w=2.4, h=3.0, z=3.0)]})
    wg.gable("roof_purple", ridge="x", pitch=56, gable_win="round", sag=0.5, shape=0.78)
    # outside chimney breast on the right gable wall
    with wg.wall("right"):
        mb.box(4.2, 2.0, 9.5, "stone_grey", pos=(6.0, -0.8, -5.0), taper=(0.8, 1.0))
    with mb.at(T(8.2, 0, 4.5)):
        chimney(mb, 0, 0, 0, wg.z + wg.roof_h - 1.0, w=3.0, d=2.4, color="stone_grey")
    finish(mb, wg.z + wg.roof_h, taper=0.04)


HOUSES = {
    "house_01_timber_cottage": house_01_timber_cottage,
    "house_02_gabled_townhouse": house_02_gabled_townhouse,
    "house_03_thatched_cottage": house_03_thatched_cottage,
    "house_04_farmhouse": house_04_farmhouse,
    "house_05_bakery": house_05_bakery,
    "house_06_crooked_tower_house": house_06_crooked_tower_house,
    "house_07_stone_manor": house_07_stone_manor,
    "house_08_plank_cabin": house_08_plank_cabin,
    "house_09_twin_gable": house_09_twin_gable,
    "house_10_saltbox": house_10_saltbox,
    "house_11_stair_house": house_11_stair_house,
    "house_12_turret_house": house_12_turret_house,
    "house_13_fisher_hut": house_13_fisher_hut,
    "house_14_long_weaver_house": house_14_long_weaver_house,
    "house_15_tower_house": house_15_tower_house,
    "house_16_porch_tower_house": house_16_porch_tower_house,
    "house_17_red_barn": house_17_red_barn,
    "house_18_tiny_cottage": house_18_tiny_cottage,
}
