"""Gatherable resources: one model per raw item, placed at the resource nodes of the village.

Every model is named ``res_<item id>`` (item ids from roblox/gameplay/shared/Items.lua) and is what
the player walks up to and harvests.  Conventions as for all assets: 1 unit = 1 stud, origin at the
ground centre, one mesh, shared palette texture.  The models stay inside a 6 x 6 stud footprint and
are readable from a distance by silhouette and colour (herbs low and green, ores as rock with
coloured veins, crystals tall and bright ...).
"""
import math

from .meshkit import T, R

TAU = 2 * math.pi


# ---------------------------------------------------------------- shared pieces
def _bed(mb, r=2.3, color="dirt_dark", h=0.28):
    """Low earth mound the plants grow from."""
    mb.lathe([(r, -0.25), (r * 0.94, h * 0.55), (r * 0.6, h), (0.0, h * 1.08)], color, segs=9, smooth=False,
             grad=(0.3, 0.7))


def _spots(n, r0, r1, phase=0.0):
    """n points on a loose spiral between two radii (deterministic)."""
    out = []
    for i in range(n):
        a = phase + i * 2.39996
        r = r0 + (r1 - r0) * ((i * 0.618) % 1.0)
        out.append((r * math.cos(a), r * math.sin(a), a))
    return out


def _leafy_plant(mb, x, y, h, leaf, leaf2, a0=0.0, leaves=5, spread=0.42, size=0.34):
    mb.lathe([(0.07, 0.0), (0.045, h)], "leaf_dark", segs=3, pos=(x, y, 0.2), smooth=False)
    for k in range(leaves):
        a = a0 + TAU * k / leaves * 1.37
        z = 0.3 + h * (0.25 + 0.7 * k / leaves)
        r = spread * (1.0 - 0.45 * k / leaves)
        mb.blob(size * (1.0 - 0.3 * k / leaves), (leaf, leaf2)[k % 2], pos=(x + r * math.cos(a), y + r * math.sin(a), z),
                level=0, noise=0.18, scale=(1.25, 1.25, 0.42), grad=(0.3, 0.9))


def _stone_chunk(mb, r, pos, color, scale=(1, 1, 0.75), noise=0.24, level=0):
    mb.blob(r, color, pos=pos, scale=scale, level=level, noise=noise, grad=(0.24, 0.8))


def _log(mb, length, r, pos, yaw, bark="bark", end="wood_pale"):
    with mb.at(T(*pos), R("Z", yaw), R("Y", 90)):
        mb.cyl(r, r * 0.94, length, bark, pos=(0, 0, -length / 2), segs=7)
        mb.cyl(r * 0.8, r * 0.8, 0.05, end, pos=(0, 0, length / 2), segs=7)
        mb.cyl(r * 0.84, r * 0.84, 0.05, end, pos=(0, 0, -length / 2 - 0.05), segs=7)


def _sack(mb, x, y, color="cloth_white", fill="thatch", s=1.0, yaw=0.0):
    """Open sack: bulging body, rolled rim, visible filling."""
    with mb.at(T(x, y, 0), R("Z", yaw)):
        mb.lathe([(0.0, 0.0), (0.62 * s, 0.06), (0.82 * s, 0.6 * s), (0.72 * s, 1.15 * s), (0.6 * s, 1.5 * s),
                  (0.0, 1.42 * s)], color, segs=8, smooth=True, grad=(0.35, 0.8))
        mb.lathe([(0.52 * s, 1.46 * s), (0.7 * s, 1.5 * s), (0.7 * s, 1.66 * s), (0.52 * s, 1.7 * s)], color, segs=8,
                 smooth=True, tone=0.06)
        mb.lathe([(0.56 * s, 1.5 * s), (0.4 * s, 1.72 * s), (0.0, 1.8 * s)], fill, segs=8, smooth=False, grad=(0.45, 0.9))


def _sign(mb, x, y, color, yaw=0.0, h=2.3):
    """Small wooden stake with a coloured tag that tells the seed sorts apart."""
    with mb.at(T(x, y, 0), R("Z", yaw)):
        mb.box(0.16, 0.16, h, "wood_dark", pos=(0, 0, -0.2))
        mb.box(0.9, 0.1, 0.62, "wood_pale", pos=(0, -0.1, h - 0.85))
        mb.box(0.56, 0.06, 0.34, color, pos=(0, -0.17, h - 0.71))


# ---------------------------------------------------------------- herbs and plants
def herb_mint(mb):
    _bed(mb, 2.2)
    for i, (x, y, a) in enumerate(_spots(9, 0.25, 1.75)):
        _leafy_plant(mb, x, y, 0.75 + 0.35 * ((i * 0.37) % 1.0), "leaf_lime", "leaf_green", a0=a, leaves=5)
    for i, (x, y, _a) in enumerate(_spots(4, 0.6, 1.5, phase=1.1)):
        mb.blob(0.11, "flower_white", pos=(x, y, 1.35 + 0.2 * (i % 2)), level=0, noise=0.0)


def herb_sunleaf(mb):
    _bed(mb, 2.1)
    for i, (x, y, a) in enumerate(_spots(6, 0.3, 1.55, phase=0.6)):
        h = 1.9 + 0.7 * ((i * 0.41) % 1.0)
        mb.lathe([(0.09, 0.0), (0.06, h)], "leaf_green", segs=4, pos=(x, y, 0.2), smooth=False)
        for k in range(3):                                                    # broad leaves along the stem
            b = a + TAU * k / 3
            mb.blob(0.42, "leaf_green", pos=(x + 0.4 * math.cos(b), y + 0.4 * math.sin(b), 0.5 + h * 0.22 * (k + 1)),
                    level=0, noise=0.15, scale=(1.3, 1.3, 0.3), grad=(0.3, 0.85))
        with mb.at(T(x, y, 0.2 + h), R("Z", math.degrees(a)), R("Y", 28)):    # flower head, tilted to the sun
            for k in range(8):
                b = TAU * k / 8
                mb.blob(0.26, "flower_yellow", pos=(0.42 * math.cos(b), 0.42 * math.sin(b), 0.02), level=0, noise=0.1,
                        scale=(1.5, 1.5, 0.3), grad=(0.45, 0.95))
            mb.lathe([(0.28, -0.06), (0.3, 0.06), (0.0, 0.16)], "roof_orange", segs=7, smooth=False)


def herb_moonleaf(mb):
    _bed(mb, 2.0, color="rock_dark")
    for i, (x, y, a) in enumerate(_spots(6, 0.3, 1.5, phase=2.0)):
        h = 1.2 + 0.5 * ((i * 0.53) % 1.0)
        mb.lathe([(0.06, 0.0), (0.04, h)], "leaf_teal", segs=3, pos=(x, y, 0.2), smooth=False)
        for k in range(4):                                                    # crescent leaves, pale on top
            b = a + TAU * k / 4
            with mb.at(T(x, y, 0.35 + h * 0.2 * (k + 1)), R("Z", math.degrees(b)), R("Y", -24)):
                mb.lathe([(0.0, 0.0), (0.2, 0.3), (0.16, 0.62), (0.0, 0.9)], ("leaf_teal", "plaster_blue")[k % 2], segs=4,
                         smooth=False, grad=(0.3, 0.95))
        mb.blob(0.17, "glass_light", pos=(x, y, 0.32 + h), level=0, noise=0.05, grad=(0.6, 1.0))   # glowing bud
    for x, y, _a in _spots(3, 1.2, 1.8, phase=0.3):
        mb.blob(0.12, "flower_purple", pos=(x, y, 0.42), level=0, noise=0.0)


def mushroom_gloom(mb):
    _log(mb, 3.6, 0.55, (0.0, 0.5, 0.45), 18, bark="bark")
    mb.blob(0.8, "stone_moss", pos=(-0.5, 0.45, 0.95), scale=(1.5, 0.8, 0.28), level=0, noise=0.2)
    caps = ((-1.3, -0.5, 1.0), (-0.3, -0.9, 1.35), (0.7, -0.6, 0.85), (1.4, -0.9, 0.6), (0.2, 1.3, 0.7), (-0.9, 1.2, 0.5),
            (1.1, 0.75, 1.1))
    for i, (x, y, s) in enumerate(caps):
        z0 = 0.95 if abs(y - 0.5) < 0.4 else -0.1
        mb.cyl(0.16 * s, 0.11 * s, 0.9 * s + 0.1, "plaster_blue", pos=(x, y, z0), segs=5)
        zc = z0 + 0.85 * s
        mb.lathe([(0.62 * s, zc), (0.52 * s, zc + 0.26 * s), (0.22 * s, zc + 0.46 * s), (0.0, zc + 0.52 * s)],
                 ("roof_purple", "flower_purple")[i % 2], segs=7, smooth=False, grad=(0.3, 0.85))
        mb.cyl(0.6 * s, 0.6 * s, 0.03, "glass_light", pos=(x, y, zc - 0.03), segs=7, grad=(0.6, 1.0))  # glowing gills
        if i % 3 == 0:
            mb.blob(0.07 * s, "glass_light", pos=(x + 0.2 * s, y - 0.15 * s, zc + 0.36 * s), level=0, noise=0.0)


def berry_red(mb):
    for x, y, z, r in ((0.0, 0.0, 1.35, 1.55), (1.1, 0.5, 1.0, 1.1), (-1.05, -0.4, 1.05, 1.15), (0.1, -0.2, 2.25, 0.95)):
        mb.blob(r, ("leaf_dark", "leaf_green")[int(r * 10) % 2], pos=(x, y, z), scale=(1, 1, 0.82), level=1, noise=0.16,
                grad=(0.25, 0.85))
    for i in range(22):                                                       # berries on the outside of the bush
        a = i * 2.39996
        u = 0.25 + 0.7 * ((i * 0.61) % 1.0)
        r = 1.95 * math.sqrt(max(0.0, 1 - (u - 0.45) ** 2 * 2.2))
        mb.blob(0.17, "flower_red", pos=(r * math.cos(a) * 0.86, r * math.sin(a) * 0.8, 0.5 + u * 2.4), level=0, noise=0.05,
                grad=(0.4, 0.95))
    mb.cyl(0.2, 0.14, 0.9, "bark", pos=(0, 0, -0.2), segs=5)


# ---------------------------------------------------------------- wood, stone, sand
def wood_log(mb):
    for i, (y, z) in enumerate(((-1.1, 0.5), (0.0, 0.5), (1.1, 0.5), (-0.55, 1.42), (0.55, 1.42), (0.0, 2.3))):
        _log(mb, 4.2 + 0.2 * (i % 2), 0.52, (-0.4, y, z), 0, bark=("bark", "wood_dark")[i % 2])
    for sx in (-1, 1):                                                        # stakes that hold the stack
        mb.box(0.24, 0.24, 2.4, "wood_dark", pos=(-0.4 + sx * 1.3, -1.78, -0.2))
        mb.box(0.24, 0.24, 2.4, "wood_dark", pos=(-0.4 + sx * 1.3, 1.78, -0.2))
    mb.cyl(0.7, 0.62, 0.9, "bark", pos=(2.35, -0.9, 0.0), segs=8)             # chopping block with axe
    mb.cyl(0.6, 0.6, 0.04, "wood_pale", pos=(2.35, -0.9, 0.9), segs=8)
    with mb.at(T(2.35, -0.9, 0.9), R("Z", 30), R("Y", -32)):
        mb.box(0.12, 0.12, 1.9, "wood_light", pos=(0, 0, 0.0))
        mb.box(0.62, 0.1, 0.44, "iron", pos=(0.2, 0, -0.12), taper=(0.8, 1.0))
    mb.box(0.5, 0.26, 0.2, "wood_pale", pos=(2.2, 0.7, 0.0), tone=0.05)          # split pieces
    with mb.at(T(2.6, 1.25, 0.0), R("Z", 40)):
        mb.box(0.55, 0.24, 0.2, "wood_light")


def stone(mb):
    chunks = ((0.0, 0.0, 0.75, 1.25, "stone_grey"), (1.3, 0.5, 0.5, 0.95, "stone_light"), (-1.25, 0.35, 0.5, 0.9, "stone_dark"),
              (0.35, -1.25, 0.42, 0.85, "stone_light"), (-0.8, -1.0, 0.4, 0.7, "stone_grey"), (0.7, 1.35, 0.35, 0.65, "stone_dark"),
              (0.25, 0.2, 1.75, 0.8, "stone_light"), (-0.5, 0.55, 1.4, 0.6, "stone_grey"))
    for x, y, z, r, c in chunks:
        _stone_chunk(mb, r, (x, y, z), c, scale=(1.1, 1.0, 0.72))
    for x, y, s in ((2.0, -0.9, 0.5), (-1.9, -0.9, 0.42), (1.7, 1.6, 0.36)):  # squared blocks, ready to take
        with mb.at(T(x, y, 0), R("Z", 25 * s * 10)):
            mb.box(1.5 * s, 1.1 * s, 0.9 * s, "stone_warm", tone=mb.jitter(0.05))


def sand(mb):
    mb.lathe([(2.3, -0.2), (1.9, 0.35), (1.15, 1.0), (0.45, 1.45), (0.0, 1.55)], "sand", segs=10, smooth=False, grad=(0.35, 0.9))
    mb.lathe([(1.0, -0.1), (0.7, 0.3), (0.0, 0.5)], "sand", segs=7, pos=(1.9, 1.2, 0), smooth=False, grad=(0.4, 0.9))
    with mb.at(T(-0.3, -0.5, 1.2), R("Z", -35), R("Y", 24)):                  # shovel stuck in the heap
        mb.box(0.13, 0.13, 2.5, "wood_light", pos=(0, 0, 0.1))
        mb.box(0.5, 0.13, 0.16, "wood_dark", pos=(0, 0, 2.6))
        mb.box(0.62, 0.08, 0.8, "iron", pos=(0, 0, -0.62), taper=(0.75, 1.0))
    with mb.at(T(1.9, -1.4, 0)):                                              # bucket, filled
        mb.lathe([(0.0, 0.0), (0.5, 0.0), (0.62, 0.95), (0.54, 0.95), (0.44, 0.1)], "wood_mid", segs=8, smooth=False)
        mb.lathe([(0.55, 0.3), (0.585, 0.3), (0.6, 0.42), (0.56, 0.42)], "iron", segs=8, smooth=False)
        mb.lathe([(0.54, 0.88), (0.3, 1.1), (0.0, 1.18)], "sand", segs=8, smooth=False, grad=(0.45, 0.95))


def _ore(mb, vein, vein2, glint):
    _stone_chunk(mb, 1.75, (0.0, 0.1, 1.2), "rock_dark", scale=(1.15, 1.0, 0.7), level=1, noise=0.2)
    _stone_chunk(mb, 1.1, (1.5, -0.6, 0.72), "rock", scale=(1.1, 1.0, 0.7))
    _stone_chunk(mb, 0.95, (-1.45, 0.75, 0.62), "rock", scale=(1.0, 1.1, 0.7))
    for i in range(13):                                                       # ore nuggets breaking through the rock
        a = i * 2.39996
        u = 0.18 + 0.7 * ((i * 0.618) % 1.0)
        r = 1.72 * math.sqrt(max(0.05, 1 - (u - 0.35) ** 2 * 1.9))
        mb.blob(0.3 + 0.12 * (i % 3), (vein, vein2)[i % 2], pos=(r * 1.1 * math.cos(a), 0.1 + r * math.sin(a), 0.55 + u * 1.5),
                level=0, noise=0.3, scale=(1, 1, 0.8), grad=(0.3, 0.95))
    for x, y, s in ((1.9, 1.3, 0.34), (-1.0, -1.7, 0.3), (2.3, 0.4, 0.24), (-2.1, -0.5, 0.26)):   # loose pieces
        mb.blob(s, glint, pos=(x, y, s * 0.6), level=0, noise=0.3, grad=(0.35, 0.95))
    with mb.at(T(-1.5, -1.9, 0.14), R("Z", 20), R("Y", 80)):                  # pickaxe lying in front of the rock
        mb.box(0.12, 0.12, 2.3, "wood_light", pos=(0, 0, 0))
        mb.beam((0, -0.75, 2.2), (0, 0.75, 2.2), 0.16, 0.16, "iron")


def ore_copper(mb):
    _ore(mb, "roof_orange", "brass", "roof_orange")


def ore_iron(mb):
    _ore(mb, "roof_slate", "brick", "roof_slate")


def crystal_raw(mb):
    _stone_chunk(mb, 1.5, (0.0, 0.0, 0.5), "rock_dark", scale=(1.3, 1.15, 0.5), level=1, noise=0.2)
    shards = ((0.0, 0.0, 3.4, 0.6, 0, 0, "glass_light"), (0.85, 0.35, 2.3, 0.45, 18, 40, "glass_blue"),
              (-0.8, 0.45, 2.5, 0.48, 20, 150, "flower_purple"), (0.3, -0.85, 1.9, 0.4, 24, 280, "glass_light"),
              (-0.55, -0.7, 1.5, 0.34, 30, 215, "glass_blue"), (1.3, -0.5, 1.2, 0.3, 36, 330, "flower_purple"),
              (-1.35, -0.2, 1.1, 0.28, 38, 185, "glass_light"), (0.5, 1.1, 1.3, 0.32, 32, 75, "flower_purple"))
    for x, y, h, r, tilt, yaw, c in shards:
        with mb.at(T(x, y, 0.65), R("Z", yaw), R("Y", tilt)):
            mb.lathe([(r * 0.7, -0.12), (r, h * 0.35), (r * 0.82, h * 0.78), (0.0, h)], c, segs=5, smooth=False, grad=(0.3, 1.0))
    mb.light((0.0, 0.0, 2.0), color=(0.7, 0.85, 1.0), brightness=0.6, range_=10.0)


def fuel_charcoal(mb):
    # charcoal kiln: earth-covered mound with a vent, next to it the finished coal
    mb.lathe([(1.7, -0.2), (1.6, 0.6), (1.15, 1.6), (0.5, 2.15), (0.0, 2.3)], "dirt_dark", segs=9,
             smooth=False, grad=(0.25, 0.75), pos=(-0.7, 0.4, 0))
    mb.cyl(0.4, 0.33, 0.3, "stone_dark", pos=(-0.7, 0.4, 2.15), segs=8)        # vent with sooty opening
    mb.cyl(0.22, 0.22, 0.03, "iron", pos=(-0.7, 0.4, 2.45), segs=8, grad=(0.05, 0.3))
    for k in range(5):                                                        # turf patches on the mound
        a = 0.5 + k * 1.3
        mb.blob(0.5, "grass_dark", pos=(-0.7 + 1.25 * math.cos(a), 0.4 + 1.25 * math.sin(a), 0.75 + 0.2 * (k % 2)), level=0,
                noise=0.2, scale=(1.2, 1.2, 0.3))
    mb.box(0.7, 0.24, 0.6, "stone_dark", pos=(-0.7, -1.28, 0.0))              # fire hole with embers
    mb.box(0.46, 0.1, 0.36, "roof_orange", pos=(-0.7, -1.4, 0.08), grad=(0.6, 1.0))
    for i in range(12):                                                       # heap of charcoal
        a = i * 2.39996
        r = 0.75 * ((i * 0.618) % 1.0)
        mb.blob(0.3, "iron", pos=(1.75 + r * math.cos(a), -0.6 + r * math.sin(a), 0.2 + 0.6 * (1 - r / 0.75) * 0.9), level=0,
                noise=0.32, scale=(1.2, 0.9, 0.8), grad=(0.1, 0.5))
    with mb.at(T(1.9, 1.3, 0)):                                               # basket of coal
        mb.lathe([(0.0, 0.0), (0.55, 0.0), (0.72, 0.85), (0.62, 0.85), (0.5, 0.1)], "thatch_dark", segs=8, smooth=False)
        mb.lathe([(0.62, 0.78), (0.35, 1.02), (0.0, 1.08)], "iron", segs=8, smooth=False, grad=(0.1, 0.5))


# ---------------------------------------------------------------- water and seeds
def water(mb):
    # hand pump on a stone base with a full tub: the place to fill up water
    mb.lathe([(1.5, -0.2), (1.5, 0.3), (1.35, 0.45), (0.0, 0.45)], "stone_grey", segs=8, smooth=False, pos=(-0.7, 0.3, 0))
    mb.cyl(0.26, 0.22, 2.3, "iron", pos=(-0.7, 0.3, 0.45), segs=8)
    mb.lathe([(0.3, 2.75), (0.34, 2.9), (0.0, 3.05)], "iron", segs=8, smooth=False, pos=(-0.7, 0.3, 0))
    mb.beam((-0.7, 0.3, 2.1), (-0.7, -0.75, 2.0), 0.24, 0.24, "iron")         # spout
    mb.box(0.24, 0.24, 0.3, "iron", pos=(-0.7, -0.75, 1.72))
    with mb.at(T(-0.7, 0.3, 2.7), R("X", -28)):                               # handle
        mb.box(0.12, 1.9, 0.12, "iron", pos=(0, 0.75, 0))
        mb.box(0.2, 0.2, 0.5, "wood_dark", pos=(0, 1.65, -0.2))
    with mb.at(T(-0.7, -1.35, 0)):                                            # tub under the spout
        mb.lathe([(0.0, 0.0), (0.95, 0.0), (1.1, 1.0), (1.0, 1.0), (0.88, 0.12)], "wood_mid", segs=10, smooth=False)
        mb.lathe([(1.03, 0.25), (1.07, 0.25), (1.09, 0.4), (1.05, 0.4)], "iron", segs=10, smooth=False)
        mb.lathe([(1.07, 0.75), (1.11, 0.75), (1.13, 0.9), (1.09, 0.9)], "iron", segs=10, smooth=False)
        mb.cyl(0.99, 0.99, 0.04, "water", pos=(0, 0, 0.84), segs=10, grad=(0.5, 0.95))
    with mb.at(T(1.5, -0.2, 0)):                                              # spare bucket
        mb.lathe([(0.0, 0.0), (0.42, 0.0), (0.54, 0.85), (0.47, 0.85), (0.38, 0.1)], "wood_light", segs=8, smooth=False)
        mb.lathe([(0.49, 0.28), (0.52, 0.28), (0.535, 0.4), (0.505, 0.4)], "iron", segs=8, smooth=False)
        mb.cyl(0.45, 0.45, 0.03, "water", pos=(0, 0, 0.7), segs=8, grad=(0.5, 0.95))


def _seed_stand(mb, tag, sprout, sprout2, seed):
    _sack(mb, -0.75, 0.2, fill=seed, s=1.0, yaw=10)
    _sack(mb, 0.75, 0.55, color="thatch", fill=seed, s=0.8, yaw=-20)
    with mb.at(T(0.3, -1.25, 0), R("Z", 8)):                                  # tray with seedlings
        mb.box(2.3, 1.1, 0.34, "wood_mid")
        mb.box(2.1, 0.9, 0.1, "dirt_dark", pos=(0, 0, 0.3))
        for i in range(8):
            x, y = -0.84 + 0.56 * (i % 4), -0.22 + 0.44 * (i // 4)
            mb.lathe([(0.04, 0.4), (0.03, 0.72)], "leaf_dark", segs=3, pos=(x, y, 0), smooth=False)
            mb.blob(0.15, (sprout, sprout2)[i % 2], pos=(x - 0.1, y, 0.76), level=0, noise=0.1, scale=(1.3, 0.9, 0.4))
            mb.blob(0.15, (sprout, sprout2)[(i + 1) % 2], pos=(x + 0.1, y, 0.8), level=0, noise=0.1, scale=(1.3, 0.9, 0.4))
    _sign(mb, 1.75, -0.2, tag, yaw=-15)


def seed_mint(mb):
    _seed_stand(mb, "leaf_lime", "leaf_lime", "leaf_green", "leaf_dark")


def seed_sunleaf(mb):
    _seed_stand(mb, "flower_yellow", "leaf_green", "flower_yellow", "thatch")


RESOURCES = {
    "res_herb_mint": herb_mint,
    "res_herb_sunleaf": herb_sunleaf,
    "res_herb_moonleaf": herb_moonleaf,
    "res_mushroom_gloom": mushroom_gloom,
    "res_berry_red": berry_red,
    "res_wood_log": wood_log,
    "res_stone": stone,
    "res_sand": sand,
    "res_ore_copper": ore_copper,
    "res_ore_iron": ore_iron,
    "res_crystal_raw": crystal_raw,
    "res_water": water,
    "res_seed_mint": seed_mint,
    "res_seed_sunleaf": seed_sunleaf,
    "res_fuel_charcoal": fuel_charcoal,
}
