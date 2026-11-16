"""One small model per item: what travels over the conveyor belts and what the UI shows as icon.

Every model is named ``item_<item id>`` (ids from roblox/gameplay/shared/Items.lua).  Conventions as
for all assets (1 unit = 1 stud, origin at the bottom centre, one mesh, shared palette texture).
A belt is 2 studs wide, so the models stay inside a 1.5 stud square and below 1.7 studs.

Readability comes first: every family has its own silhouette (bundles of leaves, bowls of powder,
ingots, flasks ...) and inside a family colour and shape tell the members apart - no two flasks
share both.
"""
import math

from .meshkit import T, R, S

TAU = 2 * math.pi


# ---------------------------------------------------------------- shared shapes
def _ring(r, z, n=8, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(TAU * i / n), cy + r * math.sin(TAU * i / n), z) for i in range(n)]


def _torus(mb, R0, r, color, n=12, m=6, **kw):
    """Ring lying in the XY plane around the origin."""
    rings = []
    for k in range(n):
        a = TAU * k / n
        rings.append([((R0 + r * math.cos(b)) * math.cos(a), (R0 + r * math.cos(b)) * math.sin(a), r * math.sin(b))
                      for b in (TAU * q / m for q in range(m))])
    mb.ring_loft(rings, color, smooth=True, **kw)


def _flask(mb, liquid, lower, upper, glass="glass_light", cork="wood_pale", segs=8, smooth=True, label=None):
    """Stoppered glass vessel.  `lower` is the profile of the filled part, `upper` of the empty part
    above it ([(r, z), ...], the two meet at the same radius); the liquid is shown as the lower part."""
    mb.lathe([(0.0, lower[0][1])] + lower + [(0.0, lower[-1][1])], liquid, segs=segs, smooth=smooth, grad=(0.45, 1.0))
    mb.lathe([(0.0, upper[0][1])] + upper + [(0.0, upper[-1][1])], glass, segs=segs, smooth=smooth, grad=(0.5, 1.0))
    top_r, top_z = upper[-1]
    mb.cyl(top_r * 0.95, top_r * 0.75, 0.16, cork, pos=(0, 0, top_z - 0.04), segs=6)
    if label:
        r = max(p[0] for p in lower) * 1.02
        z = (lower[0][1] + lower[-1][1]) / 2
        mb.box(r * 1.0, 0.05, 0.26, label, pos=(0, -r * 0.94, z - 0.13))


def _bundle(mb, leaf, leaf2, tie="wood_pale", n=6, flower=None, h=1.15, wide=1.0):
    """Bunch of herbs standing on its cut stems, tied in the middle."""
    for i in range(5):
        a = TAU * i / 5
        mb.beam((0.07 * math.cos(a), 0.07 * math.sin(a), 0.0), (0.12 * math.cos(a), 0.12 * math.sin(a), 0.62), 0.06, 0.06, "leaf_dark")
    mb.cyl(0.17, 0.17, 0.1, tie, pos=(0, 0, 0.3), segs=8)
    for i in range(n):
        a = TAU * i / n + 0.3
        r = 0.2 + 0.1 * (i % 2)
        z = 0.62 + (h - 0.62) * ((i * 0.61) % 1.0)
        with mb.at(T(r * wide * math.cos(a), r * wide * math.sin(a), z), R("Z", math.degrees(a)), R("Y", 38)):
            mb.blob(0.26, (leaf, leaf2)[i % 2], scale=(0.5 * wide, 1.0 * wide, 1.25), level=0, noise=0.12, grad=(0.3, 0.95))
    mb.blob(0.24, leaf, pos=(0, 0, h), scale=(0.8, 0.8, 1.1), level=0, noise=0.12, grad=(0.35, 0.95))
    if flower:
        for i in range(3):
            a = TAU * i / 3 + 0.7
            mb.blob(0.11, flower, pos=(0.24 * math.cos(a), 0.24 * math.sin(a), h - 0.1 + 0.12 * (i % 2)), level=0, noise=0.0,
                    grad=(0.5, 1.0))


def _bowl(mb, powder, bowl="wood_mid", speck=None):
    """Turned wooden bowl with a heap of powder."""
    mb.lathe([(0.0, 0.0), (0.34, 0.0), (0.4, 0.06), (0.62, 0.38), (0.56, 0.4), (0.36, 0.12), (0.0, 0.1)], bowl, segs=10, smooth=True,
             grad=(0.3, 0.8))
    mb.lathe([(0.56, 0.34), (0.4, 0.5), (0.18, 0.66), (0.0, 0.72)], powder, segs=9, smooth=False, grad=(0.4, 1.0))
    if speck:
        for i in range(5):
            a = i * 2.39996
            mb.blob(0.05, speck, pos=(0.3 * ((i * 0.6) % 1.0) * math.cos(a), 0.3 * ((i * 0.6) % 1.0) * math.sin(a), 0.6), level=0, noise=0.0)


def _ingot(mb, color, stamp="brass", count=1):
    for k in range(count):
        with mb.at(T(0, 0.0, k * 0.3), R("Z", 12 * k)):
            mb.box(1.1, 0.56, 0.28, color, taper=(0.82, 0.72), grad=(0.3, 0.95))
    mb.box(0.26, 0.16, 0.03, stamp, pos=(0, 0, 0.28 + (count - 1) * 0.3))


def _rock(mb, r, pos, color, scale=(1, 1, 0.8), level=1):
    mb.blob(r, color, pos=pos, scale=scale, level=level, noise=0.22, grad=(0.25, 0.8))


def _pouch(mb, cloth, tag, seed):
    """Small tied seed bag with a coloured tag and a few seeds in front of it."""
    mb.lathe([(0.0, 0.0), (0.4, 0.04), (0.5, 0.36), (0.38, 0.64), (0.16, 0.76), (0.2, 0.94), (0.0, 0.98)], cloth, segs=9, smooth=True,
             grad=(0.35, 0.85))
    mb.cyl(0.19, 0.19, 0.07, "wood_dark", pos=(0, 0, 0.72), segs=8)
    mb.box(0.3, 0.05, 0.26, tag, pos=(0.0, -0.5, 0.3))
    for i in range(4):
        mb.blob(0.07, seed, pos=(-0.3 + i * 0.2, -0.62 - 0.05 * (i % 2), 0.05), scale=(1.3, 0.8, 0.7), level=0, noise=0.0)


def _amulet(mb, gem, gem2, frame="brass", shape="round"):
    """Pendant standing upright on its chain, gem in the middle."""
    with mb.at(T(0, 0, 0.62), R("X", 90)):
        segs = 10 if shape == "round" else (6 if shape == "hex" else 4)
        mb.cyl(0.46, 0.46, 0.12, frame, pos=(0, 0, -0.06), segs=segs, smooth=(shape == "round"))
        mb.cyl(0.3, 0.26, 0.1, gem, pos=(0, 0, 0.04), segs=segs, smooth=False, grad=(0.4, 1.0))
        mb.cyl(0.14, 0.05, 0.08, gem2, pos=(0, 0, 0.13), segs=segs, smooth=False, grad=(0.5, 1.0))
    with mb.at(T(0, 0, 1.14), R("X", 90)):
        _torus(mb, 0.1, 0.035, frame, n=8, m=5)
    for i in range(7):                                           # chain lying around the foot
        a = TAU * i / 7
        mb.blob(0.07, frame, pos=(0.34 * math.cos(a), 0.3 * math.sin(a) + 0.08, 0.06), level=0, noise=0.0)
    mb.box(0.22, 0.2, 0.16, frame, pos=(0, 0, 0.0))


# ---------------------------------------------------------------- raw materials
def herb_mint(mb):
    _bundle(mb, "leaf_lime", "leaf_green", flower="flower_white")


def herb_sunleaf(mb):
    _bundle(mb, "leaf_green", "leaf_lime", tie="cloth_yellow", n=5, h=1.05)
    with mb.at(T(0, -0.05, 1.18), R("X", -24)):                   # one open yellow bloom on top
        for k in range(8):
            a = TAU * k / 8
            mb.blob(0.17, "flower_yellow", pos=(0.27 * math.cos(a), 0.27 * math.sin(a), 0.0), scale=(1.4, 1.4, 0.3), level=0, noise=0.08,
                    grad=(0.5, 1.0))
        mb.lathe([(0.18, -0.04), (0.19, 0.05), (0.0, 0.12)], "roof_orange", segs=7, smooth=False)


def herb_moonleaf(mb):
    _bundle(mb, "leaf_teal", "plaster_blue", tie="glass_light", n=6, h=1.2, wide=0.8)
    for i in range(3):
        a = TAU * i / 3
        mb.blob(0.09, "glass_light", pos=(0.2 * math.cos(a), 0.2 * math.sin(a), 1.28), level=0, noise=0.0, grad=(0.7, 1.0))


def mushroom_gloom(mb):
    for x, y, s in ((0.0, 0.0, 1.0), (0.42, -0.2, 0.55), (-0.38, 0.22, 0.45)):
        mb.cyl(0.15 * s, 0.11 * s, 0.6 * s, "plaster_blue", pos=(x, y, 0.0), segs=6)
        z = 0.56 * s
        mb.lathe([(0.52 * s, z), (0.46 * s, z + 0.22 * s), (0.2 * s, z + 0.42 * s), (0.0, z + 0.48 * s)], "roof_purple", segs=8, smooth=False,
                 pos=(x, y, 0), grad=(0.3, 0.9))
        mb.cyl(0.5 * s, 0.5 * s, 0.03, "glass_light", pos=(x, y, z - 0.03), segs=8, grad=(0.6, 1.0))
        for k in range(3):
            a = TAU * k / 3 + s
            mb.blob(0.055 * s, "glass_light", pos=(x + 0.24 * s * math.cos(a), y + 0.24 * s * math.sin(a), z + 0.3 * s), level=0, noise=0.0)


def berry_red(mb):
    mb.beam((0, 0.3, 0.1), (0, -0.25, 0.75), 0.06, 0.06, "bark")
    for i, (x, y, z) in enumerate(((0.0, -0.3, 0.2), (0.24, -0.12, 0.24), (-0.24, -0.1, 0.22), (0.1, 0.12, 0.2), (-0.12, 0.2, 0.2),
                                   (0.0, -0.1, 0.5), (0.2, 0.08, 0.52), (-0.18, 0.02, 0.5))):
        mb.blob(0.2, "flower_red", pos=(x, y, z), level=0, noise=0.03, smooth=True, grad=(0.35, 1.0))
        mb.blob(0.04, "wood_dark", pos=(x, y - 0.02, z + 0.19), level=0, noise=0.0)
    with mb.at(T(0.05, -0.28, 0.8), R("Y", 30), R("Z", 20)):
        mb.blob(0.26, "leaf_green", scale=(1.3, 0.8, 0.25), level=0, noise=0.1, grad=(0.3, 0.9))
    with mb.at(T(-0.2, -0.2, 0.74), R("Y", -34), R("Z", -30)):
        mb.blob(0.22, "leaf_dark", scale=(1.3, 0.8, 0.25), level=0, noise=0.1, grad=(0.3, 0.9))


def wood_log(mb):
    with mb.at(T(0, 0, 0.36), R("Z", 12), R("Y", 90)):
        mb.cyl(0.36, 0.34, 1.3, "bark", pos=(0, 0, -0.65), segs=8)
        mb.cyl(0.3, 0.3, 0.04, "wood_pale", pos=(0, 0, 0.65), segs=8)
        mb.cyl(0.3, 0.3, 0.04, "wood_pale", pos=(0, 0, -0.69), segs=8)
        mb.cyl(0.14, 0.14, 0.05, "wood_light", pos=(0, 0, 0.67), segs=6)
        mb.cyl(0.14, 0.14, 0.05, "wood_light", pos=(0, 0, -0.72), segs=6)
    mb.cyl(0.1, 0.08, 0.3, "bark", pos=(0.2, 0.0, 0.62), segs=5)       # branch stub
    mb.blob(0.14, "leaf_green", pos=(0.22, 0.0, 0.98), scale=(1.2, 0.9, 0.5), level=0, noise=0.1)


def stone(mb):
    _rock(mb, 0.52, (-0.05, 0.0, 0.36), "stone_grey", scale=(1.1, 0.95, 0.75))
    _rock(mb, 0.3, (0.48, -0.2, 0.2), "stone_light", level=0)
    _rock(mb, 0.24, (-0.4, -0.36, 0.16), "stone_dark", level=0)
    mb.blob(0.16, "stone_moss", pos=(-0.1, 0.1, 0.72), scale=(1.4, 1.1, 0.3), level=0, noise=0.15)


def sand(mb):
    # open sack, sand spilling over the rim
    mb.lathe([(0.0, 0.0), (0.44, 0.04), (0.56, 0.36), (0.5, 0.7), (0.46, 0.82), (0.4, 0.82), (0.36, 0.2), (0.0, 0.16)], "thatch", segs=9,
             smooth=True, grad=(0.3, 0.8))
    mb.lathe([(0.44, 0.74), (0.3, 0.92), (0.0, 1.0)], "sand", segs=9, smooth=False, grad=(0.5, 1.0))
    mb.lathe([(0.3, 0.0), (0.16, 0.14), (0.0, 0.2)], "sand", segs=7, smooth=False, pos=(0.34, -0.3, 0), grad=(0.5, 1.0))
    mb.box(0.3, 0.05, 0.2, "cloth_white", pos=(0, -0.56, 0.36))


def _ore(mb, vein, vein2):
    _rock(mb, 0.56, (0.0, 0.0, 0.42), "rock_dark", scale=(1.1, 0.95, 0.8))
    for i in range(9):
        a = i * 2.39996
        u = 0.2 + 0.65 * ((i * 0.618) % 1.0)
        r = 0.54 * math.sqrt(max(0.05, 1 - (u - 0.45) ** 2 * 2.6))
        mb.blob(0.13 + 0.04 * (i % 3), (vein, vein2)[i % 2], pos=(r * 1.1 * math.cos(a), r * 0.95 * math.sin(a), 0.12 + u * 0.72), level=0,
                noise=0.3, grad=(0.35, 1.0))


def ore_copper(mb):
    _ore(mb, "roof_orange", "brass")


def ore_iron(mb):
    _ore(mb, "roof_slate", "brick")


def crystal_raw(mb):
    _rock(mb, 0.42, (0.0, 0.0, 0.14), "rock_dark", scale=(1.2, 1.1, 0.45))
    for x, y, h, r, tilt, yaw, c in ((0.0, 0.0, 1.3, 0.22, 0, 0, "glass_light"), (0.28, 0.1, 0.9, 0.17, 20, 30, "glass_blue"),
                                     (-0.26, 0.12, 0.95, 0.18, 22, 160, "flower_purple"), (0.06, -0.3, 0.7, 0.15, 26, 270, "glass_light")):
        with mb.at(T(x, y, 0.16), R("Z", yaw), R("Y", tilt)):
            mb.lathe([(r * 0.7, 0.0), (r, h * 0.35), (r * 0.8, h * 0.8), (0.0, h)], c, segs=5, smooth=False, grad=(0.3, 1.0))


def water(mb):
    # wooden pail, full to the brim
    mb.lathe([(0.0, 0.0), (0.4, 0.0), (0.54, 0.78), (0.47, 0.78), (0.36, 0.08), (0.0, 0.08)], "wood_mid", segs=10, smooth=False, grad=(0.3, 0.85))
    mb.lathe([(0.43, 0.2), (0.46, 0.2), (0.48, 0.3), (0.45, 0.3)], "iron", segs=10, smooth=False)
    mb.lathe([(0.5, 0.56), (0.53, 0.56), (0.545, 0.66), (0.515, 0.66)], "iron", segs=10, smooth=False)
    mb.cyl(0.47, 0.47, 0.04, "water", pos=(0, 0, 0.68), segs=10, grad=(0.55, 1.0))
    mb.blob(0.1, "glass_light", pos=(0.12, -0.1, 0.72), scale=(1.5, 1.0, 0.2), level=0, noise=0.0, grad=(0.8, 1.0))
    for k in range(6):                                            # handle bow
        a0, a1 = math.pi * k / 6, math.pi * (k + 1) / 6
        mb.beam((0.52 * math.cos(a0), 0, 0.74 + 0.5 * math.sin(a0)), (0.52 * math.cos(a1), 0, 0.74 + 0.5 * math.sin(a1)), 0.05, 0.05, "iron")


def seed_mint(mb):
    _pouch(mb, "cloth_white", "leaf_lime", "leaf_dark")


def seed_sunleaf(mb):
    _pouch(mb, "thatch", "flower_yellow", "wood_dark")


def fuel_charcoal(mb):
    for i, (x, y, z, r, yaw) in enumerate(((0.0, 0.0, 0.22, 0.34, 0), (0.42, 0.14, 0.18, 0.26, 40), (-0.4, -0.1, 0.18, 0.27, 110),
                                           (0.1, -0.4, 0.16, 0.24, 200), (0.05, 0.1, 0.58, 0.26, 70))):
        with mb.at(T(x, y, z), R("Z", yaw)):
            mb.blob(r, "iron", scale=(1.25, 0.85, 0.75), level=0, noise=0.3, grad=(0.05, 0.42))
    for x, y, z in ((0.2, -0.16, 0.36), (-0.2, 0.12, 0.34), (0.1, 0.2, 0.74)):                    # embers in the cracks
        mb.blob(0.08, "roof_orange", pos=(x, y, z), level=0, noise=0.2, grad=(0.6, 1.0))


# ---------------------------------------------------------------- intermediates
def mint_powder(mb):
    _bowl(mb, "leaf_lime", speck="leaf_dark")


def sunleaf_powder(mb):
    _bowl(mb, "flower_yellow", bowl="wood_light", speck="roof_orange")


def moon_powder(mb):
    _bowl(mb, "plaster_blue", bowl="stone_dark", speck="glass_light")


def stone_dust(mb):
    _bowl(mb, "stone_light", bowl="wood_dark", speck="stone_dark")


def plank(mb):
    for k, (yaw, c) in enumerate(((0, "wood_light"), (8, "wood_pale"), (-6, "wood_light"))):
        with mb.at(T(0, 0, k * 0.17), R("Z", yaw)):
            mb.box(1.4, 0.44, 0.15, c, tone=mb.jitter(0.04))
            mb.box(0.05, 0.44, 0.155, "wood_mid", pos=(0.4, 0, 0))


def glass(mb):
    for k in range(3):
        with mb.at(T(-0.16 + k * 0.16, 0, 0.04), R("Y", -14)):
            mb.box(0.07, 1.0, 1.05, "glass_light", grad=(0.45, 1.0))
            mb.box(0.075, 0.2, 0.2, "glass_blue", pos=(0, 0.2, 0.62), grad=(0.6, 1.0))
    mb.box(0.9, 1.1, 0.08, "wood_mid")


def vial(mb):
    mb.lathe([(0.0, 0.0), (0.22, 0.02), (0.26, 0.2), (0.26, 0.7), (0.14, 0.88), (0.14, 1.08), (0.18, 1.12), (0.0, 1.12)], "glass_light", segs=8,
             smooth=True, grad=(0.5, 1.0))
    mb.cyl(0.13, 0.1, 0.16, "wood_pale", pos=(0, 0, 1.08), segs=6)
    mb.blob(0.06, "plaster_white", pos=(0.14, -0.2, 0.6), scale=(0.6, 0.3, 2.2), level=0, noise=0.0, grad=(0.9, 1.0))   # glint


def _extract(mb, liquid, glass="glass_light"):
    # laboratory flask: wide cone, long neck
    _flask(mb, liquid, [(0.5, 0.02), (0.52, 0.12), (0.34, 0.46)], [(0.34, 0.46), (0.15, 0.82), (0.13, 1.2), (0.17, 1.24)], glass=glass, segs=9)


def herbal_extract(mb):
    _extract(mb, "leaf_green")


def solar_extract(mb):
    _extract(mb, "flower_yellow")
    mb.blob(0.07, "glass_lit", pos=(0.1, -0.3, 0.3), level=0, noise=0.0, grad=(0.8, 1.0))


def lunar_extract(mb):
    _extract(mb, "plaster_blue", glass="glass_blue")
    mb.blob(0.07, "glass_light", pos=(-0.1, -0.3, 0.26), level=0, noise=0.0, grad=(0.8, 1.0))


def shadow_essence(mb):
    _extract(mb, "roof_purple", glass="roof_slate")
    for i in range(3):
        mb.blob(0.05, "flower_purple", pos=(-0.16 + i * 0.16, -0.36, 0.14 + 0.1 * (i % 2)), level=0, noise=0.0, grad=(0.7, 1.0))


def berry_mash(mb):
    # preserving jar with cloth cover
    mb.lathe([(0.0, 0.0), (0.4, 0.02), (0.46, 0.14), (0.46, 0.58), (0.0, 0.58)], "flower_red", segs=10, smooth=True, grad=(0.35, 0.95))
    mb.lathe([(0.0, 0.58), (0.46, 0.58), (0.46, 0.74), (0.36, 0.84), (0.0, 0.84)], "glass_light", segs=10, smooth=True, grad=(0.5, 1.0))
    mb.lathe([(0.0, 0.82), (0.5, 0.8), (0.52, 0.7), (0.56, 0.68), (0.5, 0.9), (0.0, 0.96)], "cloth_white", segs=10, smooth=False, grad=(0.5, 1.0))
    mb.cyl(0.39, 0.39, 0.05, "wood_dark", pos=(0, 0, 0.8), segs=10)
    for i in range(4):
        a = i * 1.7
        mb.blob(0.07, "roof_red", pos=(0.4 * math.cos(a), 0.4 * math.sin(a), 0.2 + 0.09 * i), level=0, noise=0.0)


def copper_ingot(mb):
    _ingot(mb, "roof_orange", stamp="brass", count=2)


def iron_ingot(mb):
    _ingot(mb, "roof_slate", stamp="iron", count=2)


def rune_blank(mb):
    with mb.at(R("X", -12)):
        mb.box(0.9, 0.22, 1.2, "stone_warm", taper=(0.84, 1.0), grad=(0.3, 0.9))
        mb.box(0.62, 0.04, 0.84, "stone_light", pos=(0, -0.12, 0.16))
        for i in range(3):                                           # faint guide lines, no rune yet
            mb.box(0.4, 0.03, 0.04, "stone_dark", pos=(0, -0.145, 0.34 + i * 0.22))
    mb.box(1.0, 0.5, 0.1, "stone_dark")


def crystal_core(mb):
    with mb.at(T(0, 0, 0.66)):
        mb.lathe([(0.0, -0.56), (0.4, -0.06), (0.4, 0.06), (0.0, 0.56)], "glass_light", segs=6, smooth=False, grad=(0.3, 1.0))
        _torus(mb, 0.45, 0.055, "brass", n=12, m=5)
        for k in range(3):
            a = TAU * k / 3
            mb.beam((0.45 * math.cos(a), 0.45 * math.sin(a), 0.0), (0.22 * math.cos(a), 0.22 * math.sin(a), -0.62), 0.05, 0.05, "brass")
    mb.cyl(0.26, 0.3, 0.08, "brass", pos=(0, 0, 0.0), segs=8)


# ---------------------------------------------------------------- products
def tonic_minor(mb):
    # round little flask, green
    _flask(mb, "leaf_lime", [(0.3, 0.02), (0.46, 0.2), (0.48, 0.42)], [(0.48, 0.42), (0.38, 0.66), (0.15, 0.82), (0.15, 1.0), (0.19, 1.04)], segs=9)


def vitality_draught(mb):
    # tall slim bottle, golden
    _flask(mb, "flower_yellow", [(0.28, 0.02), (0.3, 0.1), (0.3, 0.72)], [(0.3, 0.72), (0.3, 0.9), (0.13, 1.1), (0.13, 1.34), (0.17, 1.38)],
           segs=8, label="cloth_white")


def night_ink(mb):
    # squat ink pot with a quill
    mb.lathe([(0.0, 0.0), (0.42, 0.02), (0.5, 0.2), (0.44, 0.46), (0.22, 0.56), (0.22, 0.66), (0.28, 0.7), (0.0, 0.7)], "roof_slate", segs=8,
             smooth=False, grad=(0.25, 0.8))
    mb.cyl(0.2, 0.2, 0.03, "roof_purple", pos=(0, 0, 0.69), segs=8, grad=(0.3, 0.7))
    mb.box(0.3, 0.05, 0.2, "plaster_cream", pos=(0, -0.5, 0.18))
    with mb.at(T(0.08, 0.0, 0.66), R("Y", 24), R("X", -10)):
        mb.box(0.03, 0.03, 0.9, "plaster_white")
        mb.lathe([(0.0, 0.3), (0.15, 0.5), (0.11, 0.9), (0.0, 1.06)], "plaster_blue", segs=4, smooth=False, grad=(0.5, 1.0))


def tonic_bottled(mb):
    # the minor tonic in a proper labelled bottle with a wax seal
    _flask(mb, "leaf_lime", [(0.34, 0.02), (0.36, 0.1), (0.36, 0.62)], [(0.36, 0.62), (0.36, 0.76), (0.16, 0.98), (0.16, 1.2), (0.2, 1.24)], segs=6,
           smooth=False, cork="roof_red", label="plaster_cream")
    mb.blob(0.07, "roof_red", pos=(0, -0.36, 0.3), scale=(1.2, 0.5, 1.2), level=0, noise=0.0)


def berry_tonic(mb):
    # heart-shaped: two bulbs side by side, red
    for sx in (-1, 1):
        with mb.at(T(sx * 0.2, 0, 0)):
            mb.lathe([(0.0, 0.0), (0.2, 0.04), (0.34, 0.3), (0.3, 0.58), (0.0, 0.66)], "flower_red", segs=8, smooth=True, grad=(0.4, 1.0))
    mb.lathe([(0.0, 0.5), (0.3, 0.56), (0.14, 0.82), (0.13, 1.04), (0.17, 1.08), (0.0, 1.08)], "glass_light", segs=8, smooth=True, grad=(0.5, 1.0))
    mb.cyl(0.125, 0.1, 0.16, "wood_pale", pos=(0, 0, 1.04), segs=6)
    mb.blob(0.1, "leaf_green", pos=(0.12, -0.06, 1.2), scale=(1.4, 0.8, 0.3), level=0, noise=0.1)


def potion_vigor(mb):
    # angular four-sided bottle, orange, with a brass collar
    _flask(mb, "roof_orange", [(0.42, 0.02), (0.46, 0.14), (0.4, 0.6)], [(0.4, 0.6), (0.34, 0.8), (0.16, 0.92), (0.16, 1.16), (0.2, 1.2)], segs=4,
           smooth=False)
    mb.cyl(0.19, 0.19, 0.08, "brass", pos=(0, 0, 0.92), segs=4, smooth=False)
    mb.blob(0.08, "glass_lit", pos=(0, -0.3, 0.3), level=0, noise=0.0, grad=(0.8, 1.0))


def dream_draught(mb):
    # teardrop, violet, with a star on the stopper
    _flask(mb, "flower_purple", [(0.16, 0.02), (0.46, 0.26), (0.5, 0.5)], [(0.5, 0.5), (0.36, 0.82), (0.12, 1.12), (0.12, 1.24), (0.15, 1.28)], segs=10)
    mb.lathe([(0.0, 1.38), (0.12, 1.46), (0.0, 1.58)], "glass_light", segs=4, smooth=False, grad=(0.7, 1.0))
    for i in range(3):
        mb.blob(0.05, "glass_light", pos=(-0.18 + i * 0.18, -0.4, 0.3 + 0.12 * (i % 2)), level=0, noise=0.0, grad=(0.8, 1.0))


def twin_elixir(mb):
    # two joined flasks, teal and gold, one stopper each, tied with a brass band
    for sx, c in ((-1, "roof_teal"), (1, "flower_yellow")):
        with mb.at(T(sx * 0.26, 0, 0)):
            _flask(mb, c, [(0.24, 0.02), (0.3, 0.14), (0.3, 0.6)], [(0.3, 0.6), (0.24, 0.8), (0.11, 0.94), (0.11, 1.14), (0.14, 1.18)], segs=7)
    mb.box(1.16, 0.62, 0.1, "brass", pos=(0, 0, 0.36))


def elixir_master(mb):
    # ornate: faceted body in a brass cage with a crown stopper
    _flask(mb, "glass_lit", [(0.3, 0.1), (0.5, 0.34), (0.5, 0.56)], [(0.5, 0.56), (0.34, 0.86), (0.14, 1.0), (0.14, 1.2), (0.18, 1.24)], segs=6,
           smooth=False, cork="brass")
    mb.cyl(0.36, 0.3, 0.12, "brass", pos=(0, 0, 0.0), segs=6, smooth=False)
    for k in range(6):
        a = TAU * k / 6
        mb.beam((0.3 * math.cos(a), 0.3 * math.sin(a), 0.1), (0.5 * math.cos(a), 0.5 * math.sin(a), 0.46), 0.05, 0.05, "brass")
        mb.beam((0.5 * math.cos(a), 0.5 * math.sin(a), 0.46), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.92), 0.05, 0.05, "brass")
    mb.lathe([(0.0, 1.32), (0.16, 1.4), (0.08, 1.52), (0.0, 1.64)], "brass", segs=6, smooth=False, grad=(0.5, 1.0))


def charm_focus(mb):
    _amulet(mb, "glass_blue", "glass_light", shape="hex")


def charm_luck(mb):
    _amulet(mb, "leaf_green", "leaf_lime", shape="round")
    with mb.at(T(0, -0.16, 0.62), R("X", 90)):                    # four-leaf clover on the gem
        for k in range(4):
            a = TAU * k / 4 + 0.78
            mb.blob(0.1, "leaf_lime", pos=(0.12 * math.cos(a), 0.12 * math.sin(a), 0.0), scale=(1, 1, 0.4), level=0, noise=0.0, grad=(0.6, 1.0))


def ring_warding(mb):
    with mb.at(T(0, 0, 0.56), R("X", 90)):
        _torus(mb, 0.42, 0.09, "brass", n=14, m=6)
    mb.lathe([(0.0, 0.0), (0.2, 0.0), (0.24, 0.14), (0.0, 0.3)], "cloth_blue", segs=6, smooth=False, pos=(0, 0, 1.0), grad=(0.4, 1.0))
    mb.cyl(0.26, 0.22, 0.1, "brass", pos=(0, 0, 0.94), segs=6, smooth=False)
    mb.box(0.5, 0.36, 0.1, "roof_purple", pos=(0, 0, 0.0))            # little cushion
    mb.box(0.42, 0.3, 0.06, "roof_purple", pos=(0, 0, 0.1), tone=0.08)


def twilight_relic(mb):
    # lidded urn with a glowing band
    mb.lathe([(0.0, 0.0), (0.28, 0.0), (0.24, 0.12), (0.46, 0.4), (0.5, 0.66), (0.36, 0.9), (0.26, 0.96), (0.0, 0.96)], "roof_slate", segs=10,
             smooth=True, grad=(0.25, 0.85))
    mb.lathe([(0.5, 0.56), (0.53, 0.58), (0.53, 0.7), (0.5, 0.72)], "flower_purple", segs=10, smooth=False, grad=(0.6, 1.0))
    mb.lathe([(0.0, 0.94), (0.32, 0.94), (0.26, 1.06), (0.08, 1.14), (0.1, 1.24), (0.0, 1.3)], "brass", segs=10, smooth=True, grad=(0.4, 1.0))
    for sx in (-1, 1):
        with mb.at(T(sx * 0.5, 0, 0.7), R("X", 90)):
            _torus(mb, 0.13, 0.04, "brass", n=8, m=5)
    for k in range(4):
        a = TAU * k / 4 + 0.4
        mb.blob(0.05, "glass_light", pos=(0.5 * math.cos(a), 0.5 * math.sin(a), 0.64), level=0, noise=0.0, grad=(0.8, 1.0))


def void_seed(mb):
    # dark kernel in a cracked shell, light breaking out
    mb.blob(0.5, "roof_slate", pos=(0, 0, 0.58), scale=(0.95, 0.95, 1.12), level=1, noise=0.1, grad=(0.1, 0.5))
    for i in range(7):
        a = i * 2.39996
        u = 0.15 + 0.7 * ((i * 0.618) % 1.0)
        r = 0.5 * math.sqrt(max(0.05, 1 - (u - 0.5) ** 2 * 3.4))
        with mb.at(T(r * math.cos(a), r * math.sin(a), 0.08 + u * 1.0), R("Z", math.degrees(a)), R("Y", 90)):
            mb.lathe([(0.0, -0.06), (0.07, 0.0), (0.0, 0.22)], "flower_purple", segs=4, smooth=False, grad=(0.6, 1.0))
    mb.lathe([(0.0, 1.1), (0.1, 1.18), (0.05, 1.36), (0.0, 1.5)], "leaf_teal", segs=4, smooth=False, grad=(0.4, 1.0))    # sprout tip
    mb.lathe([(0.0, 0.0), (0.3, 0.0), (0.36, 0.08), (0.0, 0.14)], "rock_dark", segs=8, smooth=False)


ITEMS = {
    "item_herb_mint": herb_mint, "item_herb_sunleaf": herb_sunleaf, "item_herb_moonleaf": herb_moonleaf,
    "item_mushroom_gloom": mushroom_gloom, "item_berry_red": berry_red, "item_wood_log": wood_log, "item_stone": stone,
    "item_sand": sand, "item_ore_copper": ore_copper, "item_ore_iron": ore_iron, "item_crystal_raw": crystal_raw,
    "item_water": water, "item_seed_mint": seed_mint, "item_seed_sunleaf": seed_sunleaf, "item_fuel_charcoal": fuel_charcoal,
    "item_mint_powder": mint_powder, "item_sunleaf_powder": sunleaf_powder, "item_moon_powder": moon_powder,
    "item_stone_dust": stone_dust, "item_plank": plank, "item_glass": glass, "item_vial": vial,
    "item_herbal_extract": herbal_extract, "item_solar_extract": solar_extract, "item_lunar_extract": lunar_extract,
    "item_shadow_essence": shadow_essence, "item_berry_mash": berry_mash, "item_copper_ingot": copper_ingot,
    "item_iron_ingot": iron_ingot, "item_rune_blank": rune_blank, "item_crystal_core": crystal_core,
    "item_tonic_minor": tonic_minor, "item_vitality_draught": vitality_draught, "item_night_ink": night_ink,
    "item_tonic_bottled": tonic_bottled, "item_berry_tonic": berry_tonic, "item_potion_vigor": potion_vigor,
    "item_dream_draught": dream_draught, "item_twin_elixir": twin_elixir, "item_elixir_master": elixir_master,
    "item_charm_focus": charm_focus, "item_charm_luck": charm_luck, "item_ring_warding": ring_warding,
    "item_twilight_relic": twilight_relic, "item_void_seed": void_seed,
}
