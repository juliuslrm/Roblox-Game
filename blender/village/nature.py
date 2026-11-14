"""Nature assets: trees, bushes, rocks, flowers, small ground cover.

Origin = point on the ground; trunks and rocks reach a little below z = 0 so
they stay planted on gentle slopes.
"""
import math

from .meshkit import T, R, lerp


# ---------------------------------------------------------------- helpers
def trunk(mb, h, r0, r1, color="bark", segs=6, bend=(0.0, 0.0), roots=True, sink=1.2):
    """Tapered, slightly bent trunk. Returns the top centre."""
    rings = []
    n = 3
    for i in range(n + 1):
        f = i / n
        z = lerp(-sink, h, f)
        r = lerp(r0, r1, f) * (1.25 if i == 0 else 1.0)
        ox = bend[0] * math.sin(f * math.pi * 0.5) * h * 0.2
        oy = bend[1] * math.sin(f * math.pi * 0.5) * h * 0.2
        rings.append([(ox + r * math.cos(2 * math.pi * k / segs), oy + r * math.sin(2 * math.pi * k / segs), z)
                      for k in range(segs)])
    mb.loft(rings, color, smooth=True, grad=(0.3, 0.62))
    mb.collider_cyl((0, 0, h / 2), max(r0 * 0.9, 0.8), h + 2.0)      # walk under the crown
    mb.collision = "proxy"
    if roots:
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.4
            mb.beam((r0 * 0.5 * math.cos(a), r0 * 0.5 * math.sin(a), 1.3),
                    (r0 * 2.0 * math.cos(a), r0 * 2.0 * math.sin(a), -0.6), r0 * 0.6, r0 * 0.6, color,
                    tone=-0.04)
    return (bend[0] * h * 0.2, bend[1] * h * 0.2, h)


def canopy(mb, blobs, colors, zr, level=1, noise=0.17):
    """blobs: list of (x, y, z, r, color_index, (sx, sy, sz))."""
    for b in blobs:
        x, y, z, r, ci = b[:5]
        sc = b[5] if len(b) > 5 else (1, 1, 0.85)
        mb.blob(r, colors[ci], pos=(x, y, z), scale=sc, level=level, noise=noise, zr=zr,
                grad=(0.16, 0.9))


def octa(mb, r, h, color, pos=(0, 0, 0), **kw):
    mb.lathe([(0.0, 0.0), (r, h * 0.5), (0.0, h)], color, segs=4, pos=pos, smooth=False, **kw)


# ---------------------------------------------------------------- trees
def tree_oak_a(mb):
    top = trunk(mb, 9.5, 1.5, 0.9, bend=(0.5, 0.2))
    mb.beam((top[0], top[1], 7.0), (4.2, 1.0, 11.5), 0.7, 0.7, "bark")
    mb.beam((top[0], top[1], 7.5), (-3.6, -1.6, 11.8), 0.7, 0.7, "bark")
    canopy(mb, [(0.8, 0.3, 16.5, 6.6, 0), (5.6, 1.6, 13.6, 4.2, 1), (-4.8, -2.0, 13.8, 4.4, 1),
                (-1.0, 4.8, 14.0, 4.0, 0), (1.6, -4.6, 14.6, 3.9, 0), (0.5, 0.0, 21.0, 3.6, 2)],
           ("leaf_green", "leaf_dark", "leaf_lime"), zr=(9.5, 24.5))


def tree_oak_b(mb):
    top = trunk(mb, 12.0, 1.7, 1.0, bend=(-0.6, 0.3))
    mb.beam((top[0], top[1], 8.5), (5.0, -1.0, 13.5), 0.8, 0.8, "bark")
    canopy(mb, [(-2.6, 0.6, 19.0, 6.4, 0), (4.8, -1.2, 16.4, 5.2, 0), (-6.6, -1.5, 15.2, 3.8, 1),
                (0.5, 5.2, 16.2, 4.2, 1), (-1.0, -5.0, 16.0, 4.0, 0), (-2.0, 1.0, 23.6, 3.8, 2),
                (6.5, 0.5, 20.0, 3.0, 2)],
           ("leaf_dark", "leaf_teal", "leaf_green"), zr=(11.5, 27.0))


def tree_round(mb):
    """Small ornamental tree with one tidy round crown."""
    trunk(mb, 7.0, 0.85, 0.6, bend=(0.2, -0.1), roots=False)
    canopy(mb, [(0.2, 0.0, 10.6, 4.6, 0, (1, 1, 0.95)), (2.4, 0.8, 9.4, 2.6, 1), (-2.2, -1.0, 9.6, 2.5, 1),
                (0.2, 0.2, 13.6, 2.4, 0)],
           ("leaf_lime", "leaf_green"), zr=(6.5, 15.5))


def tree_poplar(mb):
    """Tall, narrow tree that punctuates the skyline."""
    trunk(mb, 6.0, 1.0, 0.7, roots=False)
    canopy(mb, [(0, 0, 11.0, 3.6, 0, (1, 1, 1.9)), (0.4, 0.2, 19.5, 3.0, 0, (1, 1, 2.0)),
                (-0.3, 0.1, 26.5, 2.1, 1, (1, 1, 2.0)), (1.6, -0.8, 13.0, 2.2, 1, (1, 1, 1.6)),
                (-1.5, 1.0, 16.0, 2.2, 0, (1, 1, 1.6))],
           ("leaf_teal", "leaf_green"), zr=(5.0, 30.0))


def _pine(mb, h, r, tiers, color, trunk_h, tr):
    trunk(mb, trunk_h + h * 0.4, tr, tr * 0.5, color="bark", roots=False)
    z = trunk_h
    for i in range(tiers):
        f = i / tiers
        rr = r * (1 - f * 0.72)
        th = h / tiers * 1.55
        mb.lathe([(rr * 0.28, 0.0), (rr, 0.25), (rr * 0.55, th * 0.5), (0.0, th)] if i == tiers - 1 else
                 [(rr * 0.28, 0.0), (rr, 0.25), (rr * 0.42, th * 0.82)],
                 color, segs=7, pos=(mb.jitter(0.25), mb.jitter(0.25), z), phase=i * 0.5, smooth=False,
                 zr=(trunk_h, trunk_h + h * 1.05), grad=(0.14, 0.86), tone=mb.jitter(0.03))
        z += h / tiers


def tree_pine_a(mb):
    _pine(mb, 24.0, 6.4, 5, "pine", 4.0, 1.1)


def tree_pine_b(mb):
    _pine(mb, 15.0, 4.6, 4, "leaf_dark", 3.0, 0.8)


def tree_pine_c(mb):
    _pine(mb, 31.0, 7.2, 6, "pine", 6.0, 1.3)


def tree_birch(mb):
    top = trunk(mb, 15.0, 0.75, 0.4, color="bark_birch", bend=(0.5, -0.3), roots=False)
    for z in (2.0, 4.6, 6.4, 9.0, 11.4):
        a = z * 2.1
        mb.box(0.55, 0.3, 0.3, "iron", pos=(0.55 * math.cos(a) + top[0] * z / 15, 0.55 * math.sin(a) + top[1] * z / 15, z),
               anchor="c")
    canopy(mb, [(top[0], top[1], 17.5, 4.2, 0), (top[0] + 2.8, top[1] + 0.5, 14.2, 3.0, 1),
                (top[0] - 2.6, top[1] - 1.0, 15.0, 2.9, 0), (top[0], top[1] + 0.5, 21.0, 2.6, 1)],
           ("leaf_lime", "leaf_green"), zr=(11.5, 23.5), noise=0.22)


def tree_apple(mb):
    top = trunk(mb, 6.0, 1.2, 0.8, bend=(0.4, 0.4))
    mb.beam((top[0], top[1], 5.0), (3.6, -1.0, 8.0), 0.6, 0.6, "bark")
    mb.beam((top[0], top[1], 5.0), (-3.0, 1.6, 8.2), 0.6, 0.6, "bark")
    blobs = [(0.6, 0.6, 11.0, 5.2, 0), (4.4, -1.2, 9.4, 3.4, 1), (-3.8, 1.8, 9.6, 3.5, 1),
             (0.0, -3.6, 9.8, 3.0, 0), (0.6, 0.6, 14.2, 2.8, 0)]
    canopy(mb, blobs, ("leaf_green", "leaf_dark"), zr=(6.5, 16.5))
    for i in range(11):
        a = i * 2.39996
        r = 3.6 + (i % 3) * 0.9
        mb.blob(0.45, "flower_red", pos=(0.6 + r * math.cos(a), 0.6 + r * math.sin(a), 8.0 + (i * 1.7) % 4.6),
                level=0, noise=0.05, grad=(0.4, 0.75))


def tree_blossom(mb):
    """Flowering tree: the pink accent of the village green."""
    top = trunk(mb, 7.0, 1.0, 0.7, bend=(-0.4, 0.3))
    mb.beam((top[0], top[1], 5.6), (3.4, 1.4, 9.0), 0.5, 0.5, "bark")
    canopy(mb, [(-0.6, 0.4, 12.0, 4.8, 0), (3.6, 1.6, 10.6, 3.2, 1), (-4.0, -1.0, 10.4, 3.2, 0),
                (0.4, -3.4, 10.8, 2.8, 1), (-0.4, 0.6, 15.2, 2.6, 1)],
           ("leaf_pink", "flower_white"), zr=(7.0, 17.5))


def tree_autumn(mb):
    top = trunk(mb, 10.0, 1.4, 0.85, bend=(0.3, -0.5))
    mb.beam((top[0], top[1], 7.5), (-4.0, 1.0, 12.0), 0.65, 0.65, "bark")
    canopy(mb, [(0.4, -0.8, 17.0, 6.0, 0), (-5.0, 1.0, 14.2, 4.0, 1), (4.6, 0.6, 14.4, 4.0, 0),
                (0.6, -5.2, 14.6, 3.6, 1), (0.6, -1.0, 21.2, 3.2, 2)],
           ("leaf_autumn", "roof_orange", "flower_yellow"), zr=(10.0, 24.5))


def tree_stump(mb):
    mb.collision = "mesh"
    mb.lathe([(1.9, -1.0), (1.6, 0.4), (1.35, 2.0)], "bark", segs=7, smooth=True)
    mb.cyl(1.25, 1.25, 0.08, "wood_pale", pos=(0, 0, 2.0), segs=7)
    mb.cyl(0.6, 0.6, 0.04, "wood_light", pos=(0.1, 0.05, 2.08), segs=7)
    for k in range(3):
        a = 2 * math.pi * k / 3
        mb.beam((0.8 * math.cos(a), 0.8 * math.sin(a), 1.0), (2.8 * math.cos(a), 2.8 * math.sin(a), -0.5),
                0.8, 0.8, "bark", tone=-0.04)
    mb.blob(0.5, "flower_red", pos=(1.9, 0.6, 0.6), level=0, noise=0.05, scale=(1, 1, 0.6))
    mb.cyl(0.14, 0.18, 0.5, "plaster_white", pos=(1.9, 0.6, 0.0), segs=5)


def log_pile(mb):
    """Fallen log with a mossy patch."""
    mb.collision = "mesh"
    with mb.at(R("Z", 14), T(0, 0, 1.2), R("Y", 90)):
        mb.cyl(1.25, 1.1, 9.0, "bark", pos=(0, 0, -4.5), segs=7)
        mb.cyl(0.95, 0.95, 0.06, "wood_pale", pos=(0, 0, 4.5), segs=7)
        mb.cyl(1.05, 1.05, 0.06, "wood_pale", pos=(0, 0, -4.56), segs=7)
    mb.blob(1.3, "leaf_dark", pos=(-0.6, 0.2, 2.2), scale=(1.6, 0.9, 0.35), level=0, noise=0.2)
    mb.beam((1.5, -0.3, 1.6), (2.4, -1.8, 3.0), 0.35, 0.35, "bark")


# ---------------------------------------------------------------- bushes
def bush_a(mb):
    canopy(mb, [(0, 0, 1.5, 2.4, 0, (1, 1, 0.8)), (1.9, 0.6, 1.1, 1.6, 1, (1, 1, 0.8)),
                (-1.7, -0.6, 1.2, 1.7, 1, (1, 1, 0.8))], ("leaf_green", "leaf_dark"), zr=(0, 3.6), level=1)


def bush_b(mb):
    canopy(mb, [(0, 0, 1.9, 2.9, 0, (1.1, 1, 0.8)), (2.2, -0.8, 1.2, 1.8, 0, (1, 1, 0.8)),
                (-2.1, 0.9, 1.4, 2.0, 1, (1, 1, 0.8))], ("leaf_dark", "leaf_teal"), zr=(0, 4.4), level=1)
    for i in range(9):
        a = i * 2.39996
        r = 1.2 + (i % 3) * 0.75
        octa(mb, 0.3, 0.5, ("flower_white", "flower_purple")[i % 2],
             pos=(r * math.cos(a), r * math.sin(a), 2.5 + 1.2 * math.cos(r * 0.6) - 0.3 * (i % 2)))


def bush_berry(mb):
    canopy(mb, [(0, 0, 1.3, 2.0, 0, (1, 1, 0.8)), (1.4, 1.0, 0.9, 1.4, 1, (1, 1, 0.8))],
           ("leaf_lime", "leaf_green"), zr=(0, 3.0), level=1)
    for i in range(8):
        a = i * 2.39996
        r = 1.0 + (i % 2) * 0.7
        octa(mb, 0.24, 0.42, "flower_red", pos=(r * math.cos(a), r * math.sin(a), 1.9 + 0.5 * math.cos(i)))


def hedge(mb):
    """Clipped hedge segment, 8 studs long along X."""
    mb.collider_box((0, 0, 1.7), (8.0, 2.4, 3.6))
    mb.collision = "proxy"
    for i in range(3):
        x = -2.7 + i * 2.7
        mb.blob(1.9, "leaf_dark", pos=(x, mb.jitter(0.15), 1.7), scale=(1.0, 0.72, 1.05), level=1,
                noise=0.12, zr=(0, 3.8), grad=(0.18, 0.86))


# ---------------------------------------------------------------- rocks
def _rock(mb, r, pos=(0, 0, 0), scale=(1, 1, 0.7), color="rock", level=1, noise=0.26):
    mb.collision = "mesh"
    mb.blob(r, color, pos=pos, scale=scale, level=level, noise=noise, grad=(0.24, 0.78))


def rock_a(mb):
    _rock(mb, 1.9, pos=(0, 0, 0.5), scale=(1.2, 0.95, 0.72))


def rock_b(mb):
    _rock(mb, 2.3, pos=(0, 0, 0.7), scale=(1.1, 1.0, 0.75))
    _rock(mb, 1.3, pos=(2.5, 0.8, 0.3), scale=(1, 1, 0.7), color="rock_dark", level=0)
    _rock(mb, 1.0, pos=(-2.0, -1.3, 0.2), scale=(1.2, 1, 0.6), level=0)


def rock_c(mb):
    """Flat mossy slab."""
    _rock(mb, 3.0, pos=(0, 0, 0.2), scale=(1.25, 0.9, 0.36), color="rock_dark")
    mb.blob(1.5, "stone_moss", pos=(-0.5, 0.2, 1.0), scale=(1.4, 1.0, 0.22), level=0, noise=0.2)


def rock_large(mb):
    """Boulder group, a small landmark in the meadows."""
    _rock(mb, 4.6, pos=(0, 0, 1.6), scale=(1.1, 0.9, 0.95), noise=0.22)
    _rock(mb, 3.0, pos=(4.4, 1.6, 0.8), scale=(1, 1.1, 0.8), color="rock_dark")
    _rock(mb, 2.0, pos=(-3.8, -2.4, 0.4), scale=(1.2, 1, 0.7), level=0)
    mb.blob(2.0, "stone_moss", pos=(0.4, -0.4, 5.3), scale=(1.5, 1.2, 0.25), level=0, noise=0.2)
    mb.blob(1.5, "leaf_dark", pos=(3.0, -2.6, 0.8), scale=(1, 1, 0.75), level=0, noise=0.2, grad=(0.2, 0.8))


def rock_cliff(mb):
    """Tall outcrop for the hills at the edge of the map."""
    _rock(mb, 7.0, pos=(0, 0, 4.5), scale=(1.0, 0.8, 1.45), noise=0.2)
    _rock(mb, 5.4, pos=(6.2, 1.5, 2.6), scale=(1.0, 0.9, 1.2), color="rock_dark", noise=0.22)
    _rock(mb, 4.2, pos=(-5.6, -1.0, 1.6), scale=(1.1, 0.9, 1.0), noise=0.24)
    _rock(mb, 2.6, pos=(2.0, -5.0, 0.6), scale=(1.2, 1, 0.7), color="rock_dark", level=0)
    mb.blob(2.6, "stone_moss", pos=(-0.5, 0.0, 14.2), scale=(1.5, 1.1, 0.25), level=0, noise=0.2)


# ---------------------------------------------------------------- ground cover
def _flower_patch(mb, colors, n=8, spread=2.6, leaf="leaf_green"):
    for i in range(3):
        a = i * 2.2
        mb.blob(0.9, leaf, pos=(1.2 * math.cos(a), 1.2 * math.sin(a), 0.25), scale=(1.2, 1.0, 0.45), level=0,
                noise=0.25, grad=(0.25, 0.8))
    for i in range(n):
        a = i * 2.39996
        r = spread * math.sqrt((i + 0.5) / n)
        x, y = r * math.cos(a), r * math.sin(a)
        h = 1.1 + (i * 0.37) % 0.9
        mb.lathe([(0.09, 0.0), (0.07, h)], leaf, segs=3, pos=(x, y, 0), smooth=False, tone=-0.1)
        octa(mb, 0.36, 0.62, colors[i % len(colors)], pos=(x, y, h - 0.15), tone=mb.jitter(0.05),
             grad=(0.45, 0.8))


def flowers_red(mb):
    _flower_patch(mb, ("flower_red", "flower_red", "flower_yellow"))


def flowers_yellow(mb):
    _flower_patch(mb, ("flower_yellow", "flower_white"))


def flowers_blue(mb):
    _flower_patch(mb, ("flower_blue", "flower_purple", "flower_white"))


def flowers_white(mb):
    _flower_patch(mb, ("flower_white", "leaf_pink"), n=9, spread=3.0)


def grass_tuft(mb):
    for i in range(7):
        a = i * 2.39996
        r = 0.25 + 0.6 * (i / 7)
        h = 1.3 + (i * 0.53) % 1.2
        x, y = r * math.cos(a), r * math.sin(a)
        with mb.at(T(x, y, -0.1), R("Z", math.degrees(a)), R("Y", 14 + 5 * (i % 3))):
            mb.lathe([(0.2, 0.0), (0.12, h * 0.55), (0.0, h)], "grass_dark" if i % 2 else "grass", segs=3,
                     smooth=False, grad=(0.25, 0.85))


def mushrooms(mb):
    for x, y, s in ((0, 0, 1.0), (1.1, 0.5, 0.7), (-0.7, 0.9, 0.55)):
        mb.cyl(0.22 * s, 0.16 * s, 0.9 * s, "plaster_white", pos=(x, y, -0.1), segs=5)
        mb.lathe([(0.75 * s, 0.75 * s), (0.6 * s, 1.05 * s), (0.0, 1.3 * s)], "flower_red", segs=6, pos=(x, y, 0),
                 smooth=False, grad=(0.4, 0.75))
        mb.cyl(0.74 * s, 0.74 * s, 0.03, "plaster_cream", pos=(x, y, 0.73 * s), segs=6)


def reeds(mb):
    for i in range(8):
        a = i * 2.39996
        r = 0.3 + 1.1 * (i / 8)
        x, y = r * math.cos(a), r * math.sin(a)
        h = 3.2 + (i * 0.71) % 1.8
        with mb.at(T(x, y, -0.6), R("Z", math.degrees(a)), R("Y", 4 + 3 * (i % 3))):
            mb.lathe([(0.1, 0.0), (0.07, h)], "leaf_green", segs=3, smooth=False, grad=(0.25, 0.75))
            if i % 2 == 0:
                mb.lathe([(0.0, h - 0.2), (0.2, h), (0.2, h + 0.9), (0.0, h + 1.1)], "wood_dark", segs=4,
                         smooth=False)
            else:
                mb.lathe([(0.26, h * 0.3), (0.0, h * 0.3 + 2.2)], "leaf_lime", segs=3, smooth=False)


def lily_pads(mb):
    for i, (x, y, r) in enumerate(((0, 0, 1.2), (2.2, 0.8, 0.9), (-1.4, 1.8, 0.8), (0.9, -2.0, 1.0))):
        mb.cyl(r, r * 0.9, 0.08, "leaf_green" if i % 2 else "leaf_lime", pos=(x, y, 0.02), segs=7,
               phase=i * 0.7)
    octa(mb, 0.4, 0.55, "leaf_pink", pos=(0.1, 0.1, 0.1))
    octa(mb, 0.32, 0.45, "flower_white", pos=(2.2, 0.7, 0.1))


def wheat_patch(mb):
    """8 x 8 studs of ripe grain."""
    for ix in range(4):
        for iy in range(4):
            x = -3.0 + ix * 2.0 + mb.jitter(0.3)
            y = -3.0 + iy * 2.0 + mb.jitter(0.3)
            h = 3.2 + mb.jitter(0.4)
            mb.lathe([(0.75, -0.3), (1.05, h * 0.62), (0.0, h + 0.5)], "thatch", segs=5, pos=(x, y, 0),
                     phase=mb.jitter(1.0), smooth=False, grad=(0.22, 0.88), tone=mb.jitter(0.05))


def pumpkin_patch(mb):
    for x, y, r in ((0, 0, 1.2), (2.4, 0.9, 0.9), (-1.6, 1.8, 1.0), (0.8, -2.2, 0.8)):
        mb.blob(r, "roof_orange", pos=(x, y, r * 0.62), scale=(1, 1, 0.72), level=1, noise=0.06,
                grad=(0.3, 0.75))
        mb.cyl(0.12, 0.08, 0.5, "leaf_dark", pos=(x, y, r * 1.25), segs=4)
    for i in range(4):
        a = i * 1.7
        mb.blob(0.9, "leaf_green", pos=(1.8 * math.cos(a), 1.8 * math.sin(a) + 0.3, 0.2), scale=(1.3, 1, 0.3),
                level=0, noise=0.25, grad=(0.25, 0.8))


def garden_bed(mb):
    """Vegetable bed 9 x 5 studs with a low plank border."""
    mb.box(9.0, 5.0, 0.9, "dirt_dark", pos=(0, 0, -0.5), taper=0.96)
    for sy in (-1, 1):
        mb.box(9.3, 0.3, 1.0, "wood_mid", pos=(0, sy * 2.6, -0.4))
    for sx in (-1, 1):
        mb.box(0.3, 5.2, 1.0, "wood_mid", pos=(sx * 4.6, 0, -0.4))
    for row in range(3):
        y = -1.5 + row * 1.5
        mb.box(8.2, 0.8, 0.25, "dirt", pos=(0, y, 0.35))
        for i in range(6):
            x = -3.6 + i * 1.44
            if row == 0:
                mb.blob(0.52, "leaf_lime", pos=(x, y, 0.85), level=0, noise=0.15, scale=(1, 1, 0.8),
                        grad=(0.3, 0.8))
            elif row == 1:
                octa(mb, 0.3, 1.3, "leaf_green", pos=(x, y, 0.5))
                octa(mb, 0.2, 0.5, "roof_orange", pos=(x, y, 0.35))
            else:
                mb.blob(0.42, "leaf_dark", pos=(x, y, 0.8), level=0, noise=0.2, grad=(0.3, 0.8))
                octa(mb, 0.2, 0.36, "flower_red", pos=(x + 0.25, y - 0.2, 0.9))


NATURE = {
    "tree_oak_a": tree_oak_a, "tree_oak_b": tree_oak_b, "tree_round": tree_round,
    "tree_poplar": tree_poplar, "tree_pine_a": tree_pine_a, "tree_pine_b": tree_pine_b,
    "tree_pine_c": tree_pine_c, "tree_birch": tree_birch, "tree_apple": tree_apple,
    "tree_blossom": tree_blossom, "tree_autumn": tree_autumn, "tree_stump": tree_stump,
    "log_pile": log_pile, "bush_a": bush_a, "bush_b": bush_b, "bush_berry": bush_berry, "hedge": hedge,
    "rock_a": rock_a, "rock_b": rock_b, "rock_c": rock_c, "rock_large": rock_large,
    "rock_cliff": rock_cliff, "flowers_red": flowers_red, "flowers_yellow": flowers_yellow,
    "flowers_blue": flowers_blue, "flowers_white": flowers_white, "grass_tuft": grass_tuft,
    "mushrooms": mushrooms, "reeds": reeds, "lily_pads": lily_pads, "wheat_patch": wheat_patch,
    "pumpkin_patch": pumpkin_patch, "garden_bed": garden_bed,
}
