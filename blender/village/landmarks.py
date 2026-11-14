"""Landmark buildings: the orientation points of the village.

Same conventions as houses.py (front = -Y, origin on the ground, studs).
"""
import math

from .building import (Wing, win, door, finish, window, porch, hanging_sign, balcony, spire, steps,
                       wall_lantern, chimney, arch_span, w_beam, hip_roof, door_leaf)
from .houses import wins
from .meshkit import T, R, lerp


def clock_face(mb, cx, cz, r=2.6):
    """Clock in the wall frame."""
    n = 12
    pts = [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    mb.poly([(x, -0.18, z) for x, z in pts], "plaster_white", facing=(0, -1, 0), grad=(0.5, 0.62))
    k = (r + 0.2) / r
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        w_beam(mb, cx + (a[0] - cx) * k, cz + (a[1] - cz) * k, cx + (b[0] - cx) * k, cz + (b[1] - cz) * k,
               "brass", w=0.45, t=0.34, tone=0.0)
    for i in range(4):
        a = math.pi / 2 * i
        mb.box(0.3, 0.1, 0.3, "iron", pos=(cx + (r - 0.55) * math.cos(a), -0.22, cz + (r - 0.55) * math.sin(a)),
               anchor="c")
    w_beam(mb, cx, cz, cx + r * 0.42, cz + r * 0.42, "iron", w=0.26, t=0.3, tone=0.0)
    w_beam(mb, cx, cz, cx - r * 0.1, cz + r * 0.78, "iron", w=0.2, t=0.32, tone=0.0)


def flag(mb, x, y, z, h=7.0, color="cloth_red", length=4.2, rot=0.0):
    """Pole with a pennant; pole base at (x, y, z)."""
    with mb.at(T(x, y, z), R("Z", rot)):
        mb.cyl(0.14, 0.1, h, "wood_dark", segs=5)
        mb.blob(0.26, "brass", pos=(0, 0, h + 0.15), level=0, noise=0.0)
        z1, z0 = h - 0.3, h - 2.5
        mb.poly([(0.1, 0, z0), (length, 0.35, (z0 + z1) / 2), (0.1, 0, z1)], color, double=True,
                grad=(0.4, 0.66))


# ---------------------------------------------------------------------
def lm_chapel(mb):
    """Stone chapel with a bell tower and a tall slate spire."""
    stones = ("stone_grey", "stone_warm", "stone_dark")
    nave = Wing(mb, 20, 34, cy=7.0, found=1.6, found_color="stone_dark")
    aw = dict(arch=True, w=2.8, h=7.4, z=3.8, muntins=(1, 2), glass="glass_light", sill="stone_grey")
    nave.storey(15.0, style="stone", color="stone_light", stone_colors=stones, openings={
        "left": wins(3, **aw), "right": wins(3, **aw),
        "back": [win(0.5, arch=True, w=4.4, h=8.4, z=3.6, muntins=(2, 2), lit=True, sill="stone_grey")]})
    for side in ("left", "right"):
        with nave.wall(side):
            for x in (1.0, 11.4, 22.6, 33.0):
                mb.box(1.8, 2.4, 12.5, "stone_grey", pos=(x, -1.1, -1.6), taper=(1.0, 0.45))
                mb.box(2.1, 2.7, 0.5, "stone_dark", pos=(x, -1.2, -1.6))
    nave.gable("roof_slate", ridge="y", pitch=58, gable="stone", gable_color="stone_light",
               gable_win="round", trim="stone_dark", og=1.2, oe=1.6, sag=0.3)
    tower = Wing(mb, 13, 13, cy=-14.0, found=1.6, found_color="stone_dark")
    tower.storey(15.0, style="stone", color="stone_light", stone_colors=stones, openings={
        "front": [door(0.5, arch=True, double=True, w=5.4, h=9.2, color="wood_dark", fw=0.8,
                       frame="stone_grey")],
        "left": [win(0.5, arch=True, w=1.8, h=4.6, z=5.0, sill="stone_grey")],
        "right": [win(0.5, arch=True, w=1.8, h=4.6, z=5.0, sill="stone_grey")]})
    with tower.wall("front"):
        wall_lantern(mb, 6.5 - 4.6, 6.0)
        wall_lantern(mb, 6.5 + 4.6, 6.0)
    tower.storey(11.0, style="stone", color="stone_light", stone_colors=stones, band="stone_grey", openings={
        "front": [win(0.5, round_=True, w=4.0, z=3.4, frame="stone_grey", glass="glass_light")],
        "left": [win(0.5, arch=True, w=1.8, h=4.6, z=3.0, sill="stone_grey")],
        "right": [win(0.5, arch=True, w=1.8, h=4.6, z=3.0, sill="stone_grey")]})
    belfry = dict(arch=True, w=3.6, h=5.6, z=2.0, glass="iron", muntins=(0, 0), sill="stone_grey",
                  frame="stone_grey")
    tower.storey(9.5, style="stone", color="stone_light", stone_colors=stones, band="stone_grey",
                 openings={s: [win(0.5, **belfry)] for s in ("front", "left", "right", "back")})
    for s in ("front", "left", "right", "back"):
        with tower.wall(s):
            mb.lathe([(0.0, 5.6), (0.5, 5.4), (0.75, 4.3), (1.15, 3.4), (1.2, 3.2)], "brass", segs=6,
                     pos=(6.5, -0.45, 0.2), smooth=False)
    with mb.at(T(0, -14.0, tower.z)):
        mb.box(14.2, 14.2, 0.7, "stone_grey", pos=(0, 0, -0.3))
        spire(mb, 6.5, 24.0, "roof_slate", segs=4, courses=9, o=1.5, flare=0.72, finial=None)
        top = 24.0 - 0.7
        mb.box(0.3, 0.3, 3.6, "brass", pos=(0, 0, top))
        mb.box(1.9, 0.3, 0.3, "brass", pos=(0, 0, top + 2.3))
    finish(mb, tower.z + 24.0, taper=0.02)


def lm_windmill(mb):
    """Octagonal tower mill with gallery, cap and four cloth sails."""
    seg, ph = 8, math.pi / 8
    r0, r1, h = 9.4, 5.9, 38.0
    mb.collider_cyl((0, 0, 20.0), 9.6, 48.0)
    mb.collision = "proxy"

    def rad(z):
        return lerp(r0, r1, z / h)

    mb.lathe([(r0 + 0.9, -4.0), (r0 + 0.9, 2.0), (r0 + 0.3, 6.0)], "stone_grey", segs=seg, phase=ph,
             smooth=False, grad=(0.3, 0.6))
    mb.lathe([(rad(5.5), 5.5), (rad(h), h)], "plaster_white", segs=seg, phase=ph, smooth=False,
             grad=(0.38, 0.66))
    for z in (5.6, 15.0, 26.5, h - 0.7):
        mb.lathe([(rad(z) + 0.25, z), (rad(z + 0.7) + 0.25, z + 0.7)], "wood_dark", segs=seg, phase=ph,
                 smooth=False)
    tilt = -math.degrees(math.atan((r0 - r1) / h))

    def face(ang, z):
        ap = rad(z) * math.cos(math.pi / seg)
        return mb.at(T(0, 0, z), R("Z", ang), T(0, -ap - 0.05, 0), R("X", tilt))

    for k in range(seg):                                     # corner timbers
        a = ph + 2 * math.pi * k / seg
        mb.beam((rad(6.3) * math.cos(a), rad(6.3) * math.sin(a), 6.3),
                (rad(h - 0.7) * math.cos(a), rad(h - 0.7) * math.sin(a), h - 0.7), 0.7, 0.7, "wood_dark")
    with face(0, 0):
        with mb.at(R("X", -tilt)):
            door_leaf(mb, 0, 1.8, w=4.0, h=7.2, arch=True, color="wood_mid")
            wall_lantern(mb, 3.6, 6.8)
        with mb.at(R("X", -tilt), T(0, -0.4, 1.8)):
            steps(mb, 0, 1.8, w=5.6)
    for ang, z, lit in ((0, 18.0, True), (90, 9.5, False), (-90, 19.5, False), (180, 10.5, False),
                        (45, 28.5, False), (-135, 29.0, True), (0, 30.0, False)):
        with face(ang, z):
            window(mb, 0, 0, w=2.2, h=3.4, arch=True, muntins=(1, 1), lit=lit, sill="wood_light",
                   shutters="cloth_blue" if z < 25 else None)
    # gallery
    gz = 15.6
    gr = rad(gz) + 3.6
    mb.cyl(gr, gr, 0.4, "wood_light", pos=(0, 0, gz), segs=seg, phase=ph, smooth=False)
    for k in range(seg):
        a0 = ph + 2 * math.pi * k / seg
        a1 = ph + 2 * math.pi * (k + 1) / seg
        p0 = ((gr - 0.3) * math.cos(a0), (gr - 0.3) * math.sin(a0))
        p1 = ((gr - 0.3) * math.cos(a1), (gr - 0.3) * math.sin(a1))
        mb.box(0.36, 0.36, 2.9, "wood_dark", pos=(p0[0], p0[1], gz + 0.4))
        mb.beam((p0[0], p0[1], gz + 3.2), (p1[0], p1[1], gz + 3.2), 0.36, 0.3, "wood_dark")
        mb.beam((p0[0], p0[1], gz + 1.8), (p1[0], p1[1], gz + 1.8), 0.22, 0.22, "wood_dark")
        mb.beam((rad(gz - 4) * math.cos(a0), rad(gz - 4) * math.sin(a0), gz - 4.0),
                ((gr - 0.6) * math.cos(a0), (gr - 0.6) * math.sin(a0), gz), 0.45, 0.45, "wood_dark")
    # cap
    with mb.at(T(0, 0, h)):
        mb.lathe([(r1 + 0.9, -0.3), (r1 + 1.0, 0.5), (r1 + 0.2, 3.2), (r1 - 1.6, 5.8), (2.2, 7.6),
                  (0.0, 8.3)], "roof_red", segs=seg, phase=ph, smooth=False, grad=(0.32, 0.7))
        mb.blob(0.5, "brass", pos=(0, 0, 8.6), level=0, noise=0.0)
        mb.beam((0, 5.0, 3.6), (0, 11.5, 0.5), 0.5, 0.5, "wood_dark")           # tail pole
    # sails
    hub = (0.0, -r1 - 3.2, h + 3.0)
    mb.beam((0, 0, h + 3.4), hub, 1.0, 1.0, "wood_dark", ext=0.4)
    L = 23.0
    with mb.at(T(*hub), R("X", 6), R("Y", 24)):
        mb.box(1.5, 1.2, 1.5, "wood_dark", anchor="c")
        for k in range(4):
            with mb.at(R("Y", 90 * k)):
                mb.box(0.5, 0.4, L, "wood_dark", pos=(0, 0, 0))
                mb.beam((3.9, 0, 4.5), (3.9, 0, L - 0.3), 0.3, 0.28, "wood_mid")
                for i in range(7):
                    z = 4.5 + (L - 5.0) * i / 6
                    mb.beam((0, 0, z), (4.05, 0, z), 0.26, 0.26, "wood_mid")
                mb.poly([(0.3, 0.08, 4.8), (3.75, 0.08, 4.8), (3.75, 0.08, L - 0.7), (0.3, 0.08, L - 0.7)],
                        "cloth_white", double=True, grad=(0.4, 0.62))
    finish(mb, h, taper=0.0)


def lm_town_hall(mb):
    """Town hall with an arcaded loggia, timbered council floor and clock tower."""
    W, D = 38, 22
    wg = Wing(mb, W, D, found=2.2, found_color="stone_dark")
    aw = dict(arch=True, h=5.2, z=3.2, muntins=(1, 1), sill="stone_light")
    wg.storey(12.0, style="stone", color="stone_warm", stone_colors=("stone_light", "stone_grey"),
              stone_density=0.45, openings={
        "front": [door(0.5, arch=True, double=True, w=5.6, h=9.0, color="wood_dark", fw=0.8, no_steps=True),
                  win(0.14, **aw), win(0.86, **aw)],
        "left": wins(2, **aw), "right": wins(2, **aw), "back": wins(4, **aw)})
    with wg.wall("front"):                                      # loggia
        dep, zs, zt = 6.0, 6.2, 11.2
        n = 5
        bay = W / n
        mb.collider_box((W / 2, -dep / 2 - 0.3, -3.1), (W, dep + 0.6, 6.2))        # podium
        mb.collider_box((W / 2, -dep / 2 - 0.2, zt + 1.4), (W + 1.2, dep + 1.6, 3.6))  # deck
        mb.collider_box((W / 2, -dep - 3.6, -3.4), (14.0, 5.0, 5.0))               # stairs (coarse)
        for i in range(n + 1):
            x = clamp_(bay * i, 1.0, W - 1.0)
            mb.collider_box((x, -dep, 4.0), (2.2, 2.2, 8.4))
            mb.box(2.0, 2.0, zs + 2.2, "stone_light", pos=(x, -dep, -2.2), tone=mb.jitter(0.03))
            mb.box(2.5, 2.5, 0.6, "stone_grey", pos=(x, -dep, zs - 0.6))
            mb.box(2.5, 2.5, 0.7, "stone_grey", pos=(x, -dep, -2.2 + 2.0))
        for i in range(n):
            x0 = clamp_(bay * i, 1.0, W - 1.0) + 1.0
            x1 = clamp_(bay * (i + 1), 1.0, W - 1.0) - 1.0
            arch_span(mb, x0, x1, zs, zt, -dep - 0.8, -dep + 0.8, "stone_warm", rise=(x1 - x0) * 0.42,
                      grad=(0.42, 0.6))
        for x in (1.0, W - 1.0):
            mb.box(1.6, dep - 1.0, zt - zs, "stone_warm", pos=(x, -dep / 2 + 0.2, zs))
        mb.box(W + 1.2, dep + 1.6, 0.8, "stone_light", pos=(W / 2, -dep / 2 - 0.2, zt))     # deck
        mb.box(W, dep + 0.6, 2.2, "stone_grey", pos=(W / 2, -dep / 2 - 0.3, -2.2), tone=-0.05)  # podium
        with mb.at(T(0, -dep - 0.6, 0)):
            steps(mb, W / 2, 2.2, w=14.0)
        k = 11                                                   # balustrade
        for i in range(k + 1):
            x = lerp(0.2, W - 0.2, i / k)
            mb.box(0.5, 0.5, 2.0, "stone_light", pos=(x, -dep - 0.5, zt + 0.8), taper=0.8)
        mb.box(W + 0.8, 0.8, 0.4, "stone_grey", pos=(W / 2, -dep - 0.5, zt + 2.8))
        for x in (bay, W - bay):                                 # banners
            mb.box(2.6, 0.12, 6.4, "cloth_red", pos=(x, -dep - 1.0, zt - 6.4), grad=(0.35, 0.62))
            mb.box(1.2, 0.16, 1.2, "cloth_yellow", pos=(x, -dep - 1.02, zt - 3.6))
            mb.box(3.0, 0.3, 0.3, "wood_dark", pos=(x, -dep - 0.95, zt - 0.1))
    wg.storey(11.0, style="timber", color="plaster_cream", pattern="x", openings={
        "front": wins(5, arch=True, h=5.0, z=2.8, w=3.0, lit=True),
        "left": wins(2, z=2.8, h=4.6), "right": wins(2, z=2.8, h=4.6), "back": wins(4, z=2.8, h=4.6)})
    wg.gable("roof_teal", ridge="x", pitch=50, gable_win="arch", K=5, sag=0.5)
    for x in (-12.0, 12.0):
        wg.dormer(x, side=-1, roof="roof_teal", lit=True)
    wg.chimney(-15.0, 2.5, color="stone_warm")
    wg.chimney(15.0, 2.5, color="stone_warm")
    # clock tower rising from the centre of the roof
    tz = wg.z + 1.0
    tw, th = 10.0, 15.0
    with mb.at(T(0, -3.0, tz)):
        mb.collider_box((0, 0, th / 2 + 4.0), (tw, tw, th + 8.0))
        mb.box(tw, tw, th, "plaster_cream", pos=(0, 0, 0), grad=(0.42, 0.62))
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box(0.95, 0.95, th, "wood_dark", pos=(sx * (tw / 2 - 0.2), sy * (tw / 2 - 0.2), 0))
        for z in (0.0, 7.6, th - 0.8):
            mb.box(tw + 0.6, tw + 0.6, 0.8, "wood_dark", pos=(0, 0, z))
        for ang in (0, 90, 180, 270):
            with mb.at(R("Z", ang), T(0, -tw / 2, 0)):
                clock_face(mb, 0, 11.3, r=2.5)
                window(mb, 0, 2.6, w=2.4, h=3.6, arch=True, muntins=(1, 0), sill=None, lit=(ang == 0))
        with mb.at(T(0, 0, th)):
            spire(mb, tw / 2, 17.0, "roof_teal", segs=4, courses=8, o=1.6, flare=0.68, finial="brass")
    flag(mb, 0, -3.0, tz + th + 17.0 - 0.9, h=6.0, color="cloth_red")
    finish(mb, tz + th + 17.0, taper=0.02)


def clamp_(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def lm_tavern(mb):
    """The village inn: big L-shaped house, balcony, sign and outdoor tables."""
    a = Wing(mb, 34, 20, found=1.4)
    a.storey(11.0, style="stone", stone_density=0.55, openings={
        "front": [door(0.68, double=True, arch=True, w=5.2, h=8.2, color="wood_mid", hood="roof_brown"),
                  win(0.9, lit=True, w=3.2, shutters="cloth_green")],
        "right": wins(2, lit=True), "back": wins(4), "left": [win(0.75)]})
    with a.wall("front"):
        wall_lantern(mb, 0.68 * 34 - 4.4, 5.6)
        wall_lantern(mb, 0.68 * 34 + 4.4, 5.6)
        hanging_sign(mb, 32.6, 10.4, emblem="cloth_yellow", reach=3.2)
        for i, (bx, by) in enumerate(((28.6, -1.6), (30.6, -1.5), (29.6, -1.6))):   # barrels
            z = -1.4 if i < 2 else 1.5
            mb.lathe([(0.75, 0), (0.95, 1.4), (0.75, 2.8)], "wood_mid", segs=8, pos=(bx, by, z))
            mb.lathe([(0.98, 1.2), (0.98, 1.6)], "iron", segs=8, pos=(bx, by, z))
    a.storey(9.5, style="timber", color="plaster_peach", pattern="brace", jetty=1.0, openings={
        "front": [win(0.9, z=2.8, lit=True), door(0.66, w=3.2, h=6.8, color="wood_mid")],
        "right": wins(2, z=2.8, shutters="cloth_green"), "back": wins(4, z=2.8), "left": [win(0.75, z=2.8)]})
    with a.wall("front"):
        balcony(mb, 0.66 * 34, 0.0, 9.0, depth=3.2)
    a.gable("roof_brown", ridge="x", pitch=50, gable_win="lit", K=5, sag=0.6)
    b = Wing(mb, 16, 24, cx=-9.0, cy=-12.0, found=1.4)
    b.storey(11.0, style="stone", stone_density=0.55, openings={
        "front": [win(0.5, w=4.6, h=4.6, z=3.0, muntins=(2, 1), lit=True, shutters="cloth_green",
                      flowerbox="flower_red")],
        "left": wins(2, lo=0.0, hi=0.6), "right": [win(0.25, lit=True)]})
    b.storey(9.5, style="timber", color="plaster_peach", pattern="brace", jetty=1.2, openings={
        "front": wins(2, z=2.8, shutters="cloth_green"),
        "left": wins(2, lo=0.0, hi=0.6, z=2.8), "right": [win(0.25, z=2.8)]})
    b.gable("roof_brown", ridge="y", pitch=53, gable_win="shutter", gables=(True, False), og=(1.8, -1.2))
    a.chimney(13.5, 1.5, w=3.8, d=3.2, pots=2, color="brick", extra=3.6)
    a.chimney(-3.0, 3.0)
    a.dormer(9.0, side=-1, roof="roof_brown", lit=True)
    # outdoor seating in the yard in front of the main wing
    for tx, ty in ((6.0, -16.5), (13.5, -19.5)):
        with mb.at(T(tx, ty, 0), R("Z", 12 if tx < 10 else -8)):
            mb.collider_box((0, 0, 1.4), (5.0, 5.2, 2.8))
            mb.box(5.0, 2.4, 0.3, "wood_light", pos=(0, 0, 2.4))
            for sx in (-1, 1):
                mb.box(0.4, 2.0, 2.4, "wood_dark", pos=(sx * 1.9, 0, 0))
                mb.box(5.0, 0.9, 0.25, "wood_mid", pos=(0, sx * 2.1, 1.4))
                for lx in (-1.9, 1.9):
                    mb.box(0.35, 0.7, 1.4, "wood_dark", pos=(lx, sx * 2.1, 0))
            mb.cyl(0.28, 0.24, 0.6, "brass", pos=(1.0, 0.3, 2.7), segs=6)
            mb.cyl(0.28, 0.24, 0.6, "brass", pos=(-1.2, -0.4, 2.7), segs=6)
    finish(mb, a.z + a.roof_h)


def lm_smithy(mb):
    """Blacksmith: squat stone workshop with an open forge under a lean-to."""
    wg = Wing(mb, 22, 17, found=1.0, found_color="stone_dark")
    wg.storey(10.0, style="stone", color="stone_grey", stone_colors=("stone_dark", "stone_warm", "stone_light"),
              openings={"front": [door(0.3, w=4.4, color="wood_dark", lantern=-1), win(0.75, w=3.2, lit=True)],
                        "left": [win(0.5)], "back": wins(2)})
    with wg.wall("front"):
        hanging_sign(mb, 21.0, 9.4, emblem="iron", shape="box", board="wood_pale")
    wg.gable("roof_slate", ridge="x", pitch=46, gable="stone", gable_win="round", trim="wood_dark")
    with wg.wall("right"):                                      # open forge
        Wd = 17
        mb.box(Wd, 9.5, 1.0, "cobble_dark", pos=(Wd / 2, -4.75, -1.0), tone=-0.05)
        mb.collider_box((Wd / 2, -4.75, -2.5), (Wd, 9.5, 5.0))
        mb.collider_box((11.5, -1.9, 1.6), (5.0, 3.6, 3.2))
        mb.collider_box((5.6, -5.2, 1.6), (2.4, 2.2, 3.2))
        for px in (1.05, 8.5, 15.95):
            mb.collider_box((px, -9.05, 4.0), (0.8, 0.8, 8.4))
        porch(mb, 0.6, Wd - 1.2, 9.5, 8.2, 2.6, "roof_slate", post="wood_dark", n_posts=3)
        # hearth
        mb.box(5.0, 3.6, 3.0, "stone_dark", pos=(11.5, -1.9, 0), taper=0.94)
        mb.box(3.8, 2.6, 0.5, "roof_orange", pos=(11.5, -1.9, 2.8), tone=0.25)
        mb.blob(0.9, "glass_lit", pos=(11.5, -1.9, 3.3), level=0, noise=0.3, scale=(1.6, 1.1, 0.6),
                grad=(0.6, 0.9))
        mb.light((11.5, -1.9, 4.2), color=(1.0, 0.55, 0.2), brightness=1.6, range_=26)
        mb.box(4.4, 3.2, 3.6, "stone_dark", pos=(11.5, -1.7, 6.2), taper=(0.6, 0.6))      # hood
        # anvil on a stump
        mb.cyl(1.0, 1.1, 1.8, "wood_mid", pos=(5.6, -5.2, 0), segs=7)
        mb.box(1.2, 0.8, 0.5, "iron", pos=(5.6, -5.2, 1.8))
        mb.box(0.7, 0.6, 0.5, "iron", pos=(5.6, -5.2, 2.3))
        mb.box(2.3, 0.9, 0.55, "iron", pos=(5.6, -5.2, 2.8))
        mb.beam((6.75, -5.2, 3.08), (7.9, -5.2, 3.2), 0.5, 0.4, "iron")
        # quench trough, tools, coal
        mb.box(3.4, 1.6, 1.5, "wood_dark", pos=(3.2, -8.2, 0), taper=1.08)
        mb.box(3.0, 1.2, 0.1, "water", pos=(3.2, -8.2, 1.35))
        for i in range(4):
            mb.blob(0.6, "iron", pos=(14.6 + mb.jitter(0.6), -6.6 + mb.jitter(0.6), 0.3 + i * 0.12), level=0,
                    noise=0.3, scale=(1, 1, 0.7))
        mb.beam((1.2, -0.3, 6.6), (7.6, -0.3, 6.6), 0.3, 0.3, "wood_dark")
        for i in range(4):
            mb.box(0.16, 0.16, 2.0 + 0.3 * (i % 2), "iron", pos=(2.2 + i * 1.5, -0.45, 4.3))
            mb.box(0.6, 0.3, 0.4, "iron", pos=(2.2 + i * 1.5, -0.45, 4.1))
    with mb.at(wg.m):
        chimney(mb, 11.0 + 1.6, -8.5 + 11.5, wg.z - 3.0, 17.0, w=3.4, d=3.4, color="stone_dark", pots=1)
    finish(mb, wg.z + wg.roof_h, taper=0.03)


def lm_watchtower(mb):
    """Round stone watchtower with a timber gallery and a conical roof."""
    seg = 10
    ph = math.pi / seg
    r0, r1, h = 7.6, 6.3, 40.0
    mb.collider_cyl((0, 0, 22.0), 8.2, 52.0)
    mb.collision = "proxy"

    def rad(z):
        return lerp(r0, r1, clamp_(z / h, 0, 1))

    mb.lathe([(r0 + 1.2, -4.0), (r0 + 1.2, 1.4), (r0 + 0.4, 3.4)], "stone_dark", segs=seg, phase=ph,
             smooth=False, grad=(0.3, 0.58))
    mb.lathe([(rad(3.0), 3.0), (rad(h), h)], "stone_grey", segs=seg, phase=ph, smooth=False,
             grad=(0.36, 0.64))
    mb.lathe([(rad(21) + 0.3, 21.0), (rad(21.8) + 0.3, 21.8)], "stone_dark", segs=seg, phase=ph, smooth=False)
    tilt = -math.degrees(math.atan((r0 - r1) / h))
    rng = mb.rng

    def face(k, z):
        ap = rad(z) * math.cos(math.pi / seg)
        return mb.at(T(0, 0, z), R("Z", 360.0 / seg * k), T(0, -ap - 0.03, 0), R("X", tilt))

    for _ in range(46):
        k = rng.randrange(seg)
        z = rng.uniform(4.0, h - 2.5)
        if k == 0 and z < 13:
            continue
        with face(k, z):
            fw = 2 * rad(z) * math.sin(math.pi / seg)
            sw = rng.uniform(1.0, 1.8)
            mb.box(sw, rng.uniform(0.15, 0.3), rng.uniform(0.6, 1.0),
                   rng.choice(("stone_light", "stone_dark", "stone_warm")),
                   pos=(rng.uniform(-fw / 2 + sw / 2 + 0.2, fw / 2 - sw / 2 - 0.2), -0.05, 0), taper=0.9,
                   skip=("+y",))
    with face(0, 0):
        with mb.at(R("X", -tilt)):
            door_leaf(mb, 0, 1.6, w=3.4, h=7.0, arch=True, color="wood_dark", frame="stone_light", fw=0.7)
            wall_lantern(mb, 3.0, 6.4)
        with mb.at(R("X", -tilt), T(0, -0.3, 1.6)):
            steps(mb, 0, 1.6, w=4.8)
    for k, z in ((0, 16.0), (3, 12.0), (5, 24.0), (7, 14.0), (2, 28.0), (8, 30.0), (0, 31.0)):
        with face(k, z):                                         # arrow slits
            mb.box(0.7, 0.2, 3.6, "iron", pos=(0, -0.02, 0), skip=("+y",))
            w_beam(mb, -0.6, -0.2, -0.6, 3.8, "stone_light", w=0.5, t=0.25)
            w_beam(mb, 0.6, -0.2, 0.6, 3.8, "stone_light", w=0.5, t=0.25)
            w_beam(mb, -0.85, 4.0, 0.85, 4.0, "stone_light", w=0.5, t=0.25)
    # timber gallery
    gr = r1 + 2.8
    mb.cyl(gr, gr, 0.6, "wood_mid", pos=(0, 0, h), segs=seg, phase=ph, smooth=False)
    mb.cyl(r1 - 0.4, r1 - 0.4, 7.4, "wood_light", pos=(0, 0, h + 0.6), segs=seg, phase=ph, smooth=False,
           grad=(0.38, 0.6))
    for k in range(seg):
        a0 = ph + 2 * math.pi * k / seg
        a1 = ph + 2 * math.pi * (k + 1) / seg
        c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
        mb.beam((rad(h - 4.5) * c0, rad(h - 4.5) * s0, h - 4.5), ((gr - 0.5) * c0, (gr - 0.5) * s0, h),
                0.5, 0.5, "wood_dark")
        mb.box(0.5, 0.5, 7.4, "wood_dark", pos=((gr - 0.4) * c0, (gr - 0.4) * s0, h + 0.6))
        mb.beam(((gr - 0.4) * c0, (gr - 0.4) * s0, h + 3.2), ((gr - 0.4) * c1, (gr - 0.4) * s1, h + 3.2),
                0.35, 0.3, "wood_dark")
        mb.beam(((gr - 0.4) * c0, (gr - 0.4) * s0, h + 7.7), ((gr - 0.4) * c1, (gr - 0.4) * s1, h + 7.7),
                0.5, 0.5, "wood_dark")
        am = (a0 + a1) / 2
        mb.box(0.25, 0.25, 2.6, "wood_dark", pos=((gr - 0.5) * math.cos(am) * 0.98, (gr - 0.5) * math.sin(am) * 0.98,
                                                 h + 0.6))
    with mb.at(T(0, 0, h + 8.0)):
        spire(mb, (gr - 0.2) * math.cos(math.pi / seg), 13.0, "roof_red", segs=seg, courses=6, o=1.6,
              flare=0.8, finial=None)
    flag(mb, 0, 0, h + 8.0 + 13.0 - 1.0, h=7.5, color="cloth_blue", length=5.0)
    mb.light((0, 0, h + 4.5), brightness=1.2, range_=36)
    finish(mb, h, taper=0.0)


def lm_market_hall(mb):
    """Open timber market hall on stone footings under a big hipped roof."""
    W, D, ph = 30.0, 18.0, 10.0
    mb.box(W + 3, D + 3, 4.8, "cobble", pos=(0, 0, -4.0), taper=0.98, grad=(0.3, 0.56))
    mb.collision = "proxy"
    mb.collider_box((0, 0, -1.6), (W + 3, D + 3, 4.8))
    mb.collider_box((0, 0, 16.0), (W + 4, D + 4, 9.0))
    xs = [lerp(-W / 2 + 0.8, W / 2 - 0.8, i / 3) for i in range(4)]
    ys = [-D / 2 + 0.8, D / 2 - 0.8]
    for x in xs:
        for y in ys:
            mb.collider_box((x, y, 5.5), (1.7, 1.7, 9.5))
            mb.box(1.7, 1.7, 1.8, "stone_grey", pos=(x, y, 0.8), taper=0.85)
            mb.box(0.95, 0.95, ph - 1.6, "wood_dark", pos=(x, y, 2.4), tone=mb.jitter(0.04))
            for sx in (-1, 1):
                if -W / 2 < x + sx * 2.4 < W / 2:
                    mb.beam((x, y, ph - 1.9), (x + sx * 2.4, y, ph + 0.6), 0.5, 0.5, "wood_dark")
            sy = 1 if y < 0 else -1
            mb.beam((x, y, ph - 1.9), (x, y + sy * 2.4, ph + 0.6), 0.5, 0.5, "wood_dark")
    for y in ys:
        mb.beam((-W / 2, y, ph + 0.9), (W / 2, y, ph + 0.9), 0.9, 0.9, "wood_dark")
    for x in xs:
        mb.beam((x, -D / 2, ph + 0.9), (x, D / 2, ph + 0.9), 0.8, 0.8, "wood_dark")
    with mb.at(T(0, 0, ph + 1.3), R("Z", 90)):
        hip_roof(mb, D, W, 9.5, "roof_orange", o=2.4, courses=6)
    with mb.at(T(0, 0, ph + 1.3 + 9.2)):                         # roof lantern
        mb.box(4.4, 3.2, 2.4, "plaster_cream", pos=(0, 0, 0))
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box(0.5, 0.5, 2.4, "wood_dark", pos=(sx * 2.0, sy * 1.4, 0))
        with mb.at(T(0, 0, 2.4), R("Z", 90)):
            hip_roof(mb, 3.2, 4.4, 2.8, "roof_orange", o=0.9, courses=2, th=0.3, lip=0.15)
    for x in (xs[0], xs[-1]):
        mb.box(0.8, 0.8, 0.14, "iron", pos=(x, ys[0] - 0.9, 7.6))
        mb.box(0.6, 0.6, 0.9, "glass_lit", pos=(x, ys[0] - 0.9, 6.7), grad=(0.6, 0.85))
        mb.beam((x, ys[0], 7.9), (x, ys[0] - 1.1, 7.9), 0.16, 0.16, "iron")
        mb.light((x, ys[0] - 0.9, 7.0), brightness=1.0, range_=24)
    mb.light((0, 0, 8.5), brightness=0.8, range_=30)


LANDMARKS = {
    "lm_chapel": lm_chapel,
    "lm_windmill": lm_windmill,
    "lm_town_hall": lm_town_hall,
    "lm_tavern": lm_tavern,
    "lm_smithy": lm_smithy,
    "lm_watchtower": lm_watchtower,
    "lm_market_hall": lm_market_hall,
}
