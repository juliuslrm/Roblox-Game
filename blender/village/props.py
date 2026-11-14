"""Props and decorations: street furniture, fences, market goods, bridge.

Origin = point on the ground.  Segment props (fences, walls, hedge) run along
the X axis from -4 to +4 studs so they can be chained every 8 studs.
"""
import math

from .building import gable_roof, lean_to_roof, w_beam
from .landmarks import flag
from .meshkit import T, R, lerp
from .nature import octa

SEG = 8.0   # length of chainable segments


# ---------------------------------------------------------------- helpers
def barrel_at(mb, x, y, z, s=1.0, color="wood_mid"):
    mb.lathe([(0.95 * s, 0), (1.2 * s, 1.5 * s), (0.95 * s, 3.0 * s)], color, segs=8, pos=(x, y, z),
             grad=(0.36, 0.62), tone=mb.jitter(0.04))
    for zz in (0.5, 2.3):
        mb.lathe([(1.12 * s, zz * s), (1.12 * s, (zz + 0.25) * s)], "iron", segs=8, pos=(x, y, z))
    mb.cyl(0.85 * s, 0.85 * s, 0.05, "wood_light", pos=(x, y, z + 3.0 * s - 0.02), segs=8)


def crate_at(mb, x, y, z, s=2.2, rot=0.0, color="wood_light"):
    with mb.at(T(x, y, z), R("Z", rot)):
        mb.box(s, s, s, color, tone=mb.jitter(0.05))
        e = 0.22
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box(e, e, s + 0.06, "wood_mid", pos=(sx * (s / 2 - e / 2 + 0.03), sy * (s / 2 - e / 2 + 0.03), -0.03))
        for zz in (0.0, s - e):
            for sy in (-1, 1):
                mb.box(s + 0.06, e, e, "wood_mid", pos=(0, sy * (s / 2 - e / 2 + 0.03), zz))
            for sx in (-1, 1):
                mb.box(e, s + 0.06, e, "wood_mid", pos=(sx * (s / 2 - e / 2 + 0.03), 0, zz))


def sack_at(mb, x, y, z, s=1.0, color="cloth_white"):
    mb.blob(1.0 * s, color, pos=(x, y, z + 0.8 * s), scale=(1.0, 0.8, 0.95), level=0, noise=0.12,
            grad=(0.3, 0.7))
    octa(mb, 0.3 * s, 0.6 * s, color, pos=(x, y, z + 1.55 * s))


def lantern_head(mb, x, y, z, s=1.0, light=True):
    """Hanging / standing lantern body, top at z."""
    mb.lathe([(0.75 * s, 0), (0.2 * s, 0.5 * s), (0.0, 0.7 * s)], "iron", segs=4, pos=(x, y, z - 0.6 * s),
             phase=math.pi / 4, smooth=False)
    mb.box(0.8 * s, 0.8 * s, 1.2 * s, "glass_lit", pos=(x, y, z - 1.8 * s), taper=1.25, grad=(0.6, 0.9))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.beam((x + sx * 0.4 * s, y + sy * 0.4 * s, z - 1.8 * s), (x + sx * 0.5 * s, y + sy * 0.5 * s, z - 0.6 * s),
                    0.1 * s, 0.1 * s, "iron")
    mb.box(0.95 * s, 0.95 * s, 0.16 * s, "iron", pos=(x, y, z - 1.96 * s))
    if light:
        mb.light((x, y, z - 1.2 * s), brightness=1.0, range_=28)


# ---------------------------------------------------------------- water
def well(mb):
    seg = 10
    mb.collider_cyl((0, 0, 1.6), 3.6, 4.2)
    mb.collision = "proxy"
    mb.lathe([(4.6, -1.0), (4.6, 0.25), (4.0, 0.25)], "cobble", segs=seg, smooth=False)
    mb.lathe([(3.3, -1.0), (3.3, 3.0), (3.5, 3.0), (3.5, 3.5), (2.5, 3.5), (2.5, 1.8)], "stone_grey", segs=seg,
             smooth=False, grad=(0.34, 0.62))
    mb.cyl(2.5, 2.5, 0.1, "water_deep", pos=(0, 0, 1.75), segs=seg, smooth=False)
    for sx in (-1, 1):
        mb.box(0.6, 0.6, 7.2, "wood_dark", pos=(sx * 3.1, 0, 2.6))
        mb.beam((sx * 3.1, 0, 8.0), (sx * 1.6, 0, 9.6), 0.4, 0.4, "wood_dark")
    with mb.at(T(0, 0, 9.6)):
        gable_roof(mb, 5.0, 7.4, 2.9, "roof_red", oe=1.0, og=0.6, th=0.35, courses=3, sag=0.1, lip=0.18, K=2,
                   trim="wood_dark", gable=None)
    mb.beam((-3.5, 0, 7.4), (4.4, 0, 7.4), 0.4, 0.4, "wood_mid")
    mb.beam((4.4, 0, 7.4), (4.4, 0, 6.3), 0.18, 0.18, "iron")
    mb.beam((4.2, 0, 6.3), (5.2, 0, 6.3), 0.18, 0.18, "iron")
    mb.beam((0.6, 0, 7.3), (0.6, 0, 5.0), 0.1, 0.1, "wood_pale")
    mb.lathe([(0.55, 0), (0.7, 1.1)], "wood_mid", segs=7, pos=(0.6, 0, 3.9))
    mb.lathe([(0.72, 0.8), (0.72, 1.0)], "iron", segs=7, pos=(0.6, 0, 3.9))


def fountain(mb):
    """Centrepiece of the village square."""
    seg = 12
    mb.collider_cyl((0, 0, -0.25), 11.0, 1.5)
    mb.collider_cyl((0, 0, 1.8), 9.1, 3.6)
    mb.collider_cyl((0, 0, 7.0), 2.4, 14.0)
    mb.collision = "proxy"
    mb.lathe([(11.0, -1.5), (11.0, 0.5), (10.0, 0.5), (10.0, 1.0), (9.0, 1.0)], "cobble", segs=seg, smooth=False,
             grad=(0.36, 0.6))
    mb.lathe([(8.6, 0.0), (8.6, 3.0), (9.1, 3.0), (9.1, 3.6), (7.5, 3.6), (7.5, 2.2)], "stone_light", segs=seg,
             smooth=False, grad=(0.36, 0.64))
    mb.cyl(7.5, 7.5, 0.1, "water", pos=(0, 0, 2.6), segs=seg, smooth=False)
    mb.lathe([(2.2, 1.0), (1.8, 3.4), (1.2, 4.0), (1.1, 7.0), (1.6, 7.6)], "stone_grey", segs=8, smooth=False,
             grad=(0.34, 0.62))
    mb.lathe([(1.5, 7.4), (4.2, 8.6), (4.5, 9.3), (3.6, 9.3), (3.4, 8.9)], "stone_light", segs=8, smooth=False)
    mb.cyl(3.5, 3.5, 0.1, "water", pos=(0, 0, 9.05), segs=8, smooth=False)
    mb.lathe([(0.9, 8.6), (0.7, 11.2), (1.1, 11.6)], "stone_grey", segs=8, smooth=False)
    mb.lathe([(1.0, 11.4), (2.3, 12.2), (2.5, 12.7), (1.9, 12.7), (1.8, 12.4)], "stone_light", segs=8, smooth=False)
    mb.cyl(1.85, 1.85, 0.08, "water", pos=(0, 0, 12.52), segs=8, smooth=False)
    mb.lathe([(0.5, 12.2), (0.35, 13.6), (0.0, 14.3)], "brass", segs=6, smooth=False)
    for k in range(4):                                         # falling water
        a = math.pi / 2 * k + math.pi / 4
        c, s = math.cos(a), math.sin(a)
        mb.beam((4.2 * c, 4.2 * s, 9.1), (5.4 * c, 5.4 * s, 2.7), 0.7, 0.25, "glass_light", tone=0.12)
        mb.beam((2.3 * c, 2.3 * s, 12.5), (3.1 * c, 3.1 * s, 9.1), 0.5, 0.2, "glass_light", tone=0.12)
    for k in range(seg):
        a = 2 * math.pi * (k + 0.5) / seg
        if k % 3 == 0:
            mb.box(1.6, 0.9, 0.5, "stone_grey", pos=(8.9 * math.cos(a), 8.9 * math.sin(a), 3.6))
    mb.light((0, 0, 6.0), color=(0.75, 0.9, 1.0), brightness=0.6, range_=30)


def trough(mb):
    mb.box(6.4, 2.6, 2.0, "wood_mid", pos=(0, 0, 0.5), taper=1.08)
    mb.box(5.8, 2.0, 0.1, "water", pos=(0, 0, 2.25))
    for sx in (-1, 1):
        mb.box(0.6, 3.0, 1.2, "wood_dark", pos=(sx * 2.4, 0, -0.5))
    for sx in (-1, 1):
        mb.box(0.2, 2.86, 2.1, "iron", pos=(sx * 2.9, 0, 0.5))


# ---------------------------------------------------------------- light
def lantern_post(mb):
    mb.collider_cyl((0, 0, 5.0), 0.7, 11.5)
    mb.collision = "proxy"
    mb.box(1.6, 1.6, 1.5, "stone_grey", pos=(0, 0, -0.6), taper=0.8)
    mb.cyl(0.34, 0.22, 10.0, "iron", pos=(0, 0, 0.9), segs=6)
    mb.cyl(0.5, 0.5, 0.3, "iron", pos=(0, 0, 3.0), segs=6)
    mb.beam((0, 0, 10.6), (0, -2.3, 11.4), 0.22, 0.22, "iron")
    mb.beam((0, 0, 9.2), (0, -1.4, 10.9), 0.16, 0.16, "iron")
    mb.beam((0, -2.3, 11.4), (0, -2.3, 10.9), 0.1, 0.1, "iron")
    lantern_head(mb, 0, -2.3, 10.9)


def lantern_post_double(mb):
    mb.collider_cyl((0, 0, 6.0), 0.8, 13.5)
    mb.collision = "proxy"
    mb.box(2.0, 2.0, 1.7, "stone_grey", pos=(0, 0, -0.6), taper=0.8)
    mb.cyl(0.42, 0.28, 11.5, "iron", pos=(0, 0, 1.1), segs=6)
    mb.cyl(0.6, 0.6, 0.35, "iron", pos=(0, 0, 3.4), segs=6)
    mb.blob(0.4, "brass", pos=(0, 0, 12.9), level=0, noise=0.0)
    for sx in (-1, 1):
        mb.beam((0, 0, 11.6), (sx * 2.5, 0, 12.2), 0.22, 0.22, "iron")
        mb.beam((0, 0, 10.0), (sx * 1.5, 0, 11.8), 0.16, 0.16, "iron")
        lantern_head(mb, sx * 2.5, 0, 12.0)


# ---------------------------------------------------------------- fences
def fence_post(mb):
    mb.box(0.75, 0.75, 4.6, "wood_mid", pos=(0, 0, -1.0), taper=0.86, tone=mb.jitter(0.04))


def fence_wood(mb):
    """Rustic two-rail fence, post at x = -4."""
    mb.collider_box((0, 0, 1.3), (SEG, 0.8, 4.6))
    mb.collision = "proxy"
    with mb.at(T(-SEG / 2, 0, 0)):
        fence_post(mb)
    mb.beam((-SEG / 2, 0, 2.7 + mb.jitter(0.12)), (SEG / 2, 0, 2.7 + mb.jitter(0.12)), 0.3, 0.55, "wood_light",
            tone=mb.jitter(0.05))
    mb.beam((-SEG / 2, 0, 1.3 + mb.jitter(0.12)), (SEG / 2, 0, 1.3 + mb.jitter(0.12)), 0.3, 0.55, "wood_light",
            tone=mb.jitter(0.05))


def fence_picket(mb):
    """Garden picket fence, post at x = -4."""
    mb.collider_box((0, 0, 1.2), (SEG, 0.8, 4.4))
    mb.collision = "proxy"
    with mb.at(T(-SEG / 2, 0, 0)):
        mb.box(0.7, 0.7, 4.4, "plaster_white", pos=(0, 0, -1.0))
        octa(mb, 0.5, 0.8, "plaster_white", pos=(0, 0, 3.2))
    for z in (0.9, 2.3):
        mb.beam((-SEG / 2, 0.06, z), (SEG / 2, 0.06, z), 0.2, 0.4, "plaster_white", tone=-0.05)
    n = 7
    for i in range(n):
        x = -SEG / 2 + SEG * (i + 1) / (n + 1)
        h = 2.9 + mb.jitter(0.12)
        mb.prism([(x - 0.3, 0.2), (x + 0.3, 0.2), (x + 0.3, h), (x, h + 0.45), (x - 0.3, h)], -0.2, -0.04,
                 "plaster_white", tone=mb.jitter(0.03))


def stone_wall(mb):
    """Dry stone wall segment (8 x 1.7 x 3.2)."""
    mb.collider_box((0, 0, 1.2), (SEG, 1.7, 4.6))
    mb.collision = "proxy"
    mb.box(SEG, 1.7, 4.0, "stone_grey", pos=(0, 0, -1.0), taper=(1.0, 0.78), grad=(0.32, 0.62))
    rng = mb.rng
    x = -SEG / 2
    while x < SEG / 2 - 0.3:
        w = min(rng.uniform(1.2, 2.2), SEG / 2 - x)
        mb.box(w - 0.08, 1.7, rng.uniform(0.45, 0.75), rng.choice(("stone_light", "stone_dark", "stone_warm")),
               pos=(x + w / 2, 0, 2.95), taper=(0.92, 0.85), tone=rng.uniform(-0.05, 0.05))
        x += w
    for sy in (-1, 1):
        for _ in range(5):
            w, h = rng.uniform(0.9, 1.7), rng.uniform(0.5, 0.9)
            xx = rng.uniform(-SEG / 2 + w / 2 + 0.1, SEG / 2 - w / 2 - 0.1)
            z = rng.uniform(0.1, 2.0)
            k = lerp(1.0, 0.78, (z + 1.0) / 4.0)
            mb.box(w, 0.22, h, rng.choice(("stone_light", "stone_dark", "stone_warm")),
                   pos=(xx, sy * 0.85 * k, z), tone=rng.uniform(-0.05, 0.05))


def gate_arch(mb):
    """Village gate: two stone piers, a timber lintel roof and a name board.
    The road passes through along Y; clear width 16 studs."""
    half = 10.0
    mb.collision = "proxy"
    mb.collider_box((0, 0, 15.2), (2 * half + 6.0, 5.0, 4.0))
    for sx in (-1, 1):
        mb.collider_box((sx * half, 0, 5.5), (4.2, 4.2, 15.0))
        with mb.at(T(sx * half, 0, 0)):
            mb.box(4.4, 4.4, 2.6, "stone_dark", pos=(0, 0, -1.6), taper=0.9)
            mb.box(3.4, 3.4, 12.0, "stone_grey", pos=(0, 0, 1.0), taper=0.9, grad=(0.34, 0.62))
            mb.box(3.9, 3.9, 0.7, "stone_light", pos=(0, 0, 13.0))
            rng = mb.rng
            for _ in range(8):
                f = rng.choice([(0, -1), (0, 1), (1, 0), (-1, 0)])
                z = rng.uniform(2.0, 11.5)
                k = lerp(1.0, 0.9, (z - 1) / 12) * 1.7
                if f[0] == 0:
                    mb.box(rng.uniform(1.0, 1.8), 0.25, rng.uniform(0.6, 1.0), "stone_light",
                           pos=(rng.uniform(-0.6, 0.6), f[1] * k, z), tone=rng.uniform(-0.08, 0.04))
                else:
                    mb.box(0.25, rng.uniform(1.0, 1.8), rng.uniform(0.6, 1.0), "stone_light",
                           pos=(f[0] * k, rng.uniform(-0.6, 0.6), z), tone=rng.uniform(-0.08, 0.04))
            lantern_head(mb, -sx * 2.4, -0.2, 10.2)
            mb.beam((-sx * 1.4, -0.2, 10.4), (-sx * 2.4, -0.2, 10.4), 0.18, 0.18, "iron")
    mb.beam((-half - 2.6, 0, 14.3), (half + 2.6, 0, 14.3), 1.3, 1.3, "wood_dark")
    for sx in (-1, 1):
        mb.beam((sx * (half - 1.6), 0, 10.4), (sx * (half - 5.2), 0, 13.7), 0.8, 0.8, "wood_dark")
    with mb.at(T(0, 0, 15.0), R("Z", 90)):
        gable_roof(mb, 4.4, 2 * half + 5.0, 2.6, "roof_red", oe=1.0, og=0.8, th=0.4, courses=3, sag=0.25, lip=0.2,
                   K=4, trim="wood_dark", gable=None)
    mb.box(9.0, 0.4, 2.6, "wood_light", pos=(0, 0, 10.6), grad=(0.42, 0.62))
    mb.box(9.5, 0.55, 0.35, "wood_dark", pos=(0, 0, 10.4))
    mb.box(9.5, 0.55, 0.35, "wood_dark", pos=(0, 0, 13.1))
    for sx in (-1, 1):
        mb.box(0.14, 0.14, 0.9, "iron", pos=(sx * 3.6, 0, 13.4))
        for sy in (-1, 1):
            mb.blob(0.55, "cloth_yellow", pos=(sx * 2.4, sy * 0.25, 11.9), scale=(1, 0.3, 1), level=0, noise=0.0)
    for sy in (-1, 1):
        mb.box(2.4, 0.2, 1.0, "cloth_red", pos=(0, sy * 0.24, 11.4))


# ---------------------------------------------------------------- seating / signs
def bench(mb):
    for sx in (-1, 1):
        mb.box(0.5, 2.2, 1.9, "stone_grey", pos=(sx * 2.6, 0, -0.3), taper=(1, 0.8))
    for y in (-0.6, 0.0, 0.6):
        mb.box(6.4, 0.5, 0.26, "wood_light", pos=(0, y, 1.6), tone=mb.jitter(0.05))
    for z in (2.6, 3.4):
        mb.box(6.4, 0.24, 0.55, "wood_light", pos=(0, 0.95, z), tone=mb.jitter(0.05))
    for sx in (-1, 1):
        mb.beam((sx * 2.6, 0.8, 1.6), (sx * 2.6, 1.05, 4.1), 0.3, 0.3, "wood_dark")


def signpost(mb):
    mb.collider_cyl((0, 0, 3.5), 0.6, 9.0)
    mb.collision = "proxy"
    mb.box(0.6, 0.6, 9.4, "wood_dark", pos=(0, 0, -1.0), taper=0.85)
    for i, (ang, z, col) in enumerate(((10, 7.0, "wood_light"), (-150, 5.8, "wood_pale"), (95, 4.6, "wood_light"))):
        with mb.at(T(0, 0, z), R("Z", ang)):
            mb.prism([(0.2, 0), (3.3, 0), (4.0, 0.45), (3.3, 0.9), (0.2, 0.9)], -0.42, -0.26, col,
                     tone=mb.jitter(0.04))
            mb.box(1.6, 0.05, 0.16, "wood_dark", pos=(1.8, -0.45, 0.38))
    octa(mb, 0.45, 0.8, "wood_dark", pos=(0, 0, 8.3))


def notice_board(mb):
    mb.collider_box((0, 0, 3.0), (6.2, 0.8, 8.0))
    mb.collision = "proxy"
    for sx in (-1, 1):
        mb.box(0.55, 0.55, 8.0, "wood_dark", pos=(sx * 2.8, 0, -1.0))
    mb.box(5.4, 0.3, 3.8, "wood_light", pos=(0, 0, 2.6), grad=(0.42, 0.62))
    with mb.at(T(-3.4, 0, 6.8)):
        lean_to_roof(mb, 0, 6.8, 1.3, 0.9, "roof_brown", z=0, og=0.2, oe=0.4, courses=2)
    with mb.at(T(-3.4, 0, 6.8), R("Z", 180), T(-6.8, 0, 0)):
        lean_to_roof(mb, 0, 6.8, 1.3, 0.9, "roof_brown", z=0, og=0.2, oe=0.4, courses=2)
    for x, z, w, h, c, r in ((-1.6, 4.4, 1.5, 1.8, "plaster_white", 4), (0.3, 4.0, 1.3, 1.6, "plaster_cream", -5),
                             (1.7, 4.8, 1.2, 1.4, "plaster_yellow", 3), (-0.4, 2.9, 1.6, 1.0, "plaster_white", -2)):
        with mb.at(T(x, -0.17, z), R("Y", r)):
            mb.box(w, 0.04, h, c, anchor="c")
            mb.box(0.16, 0.08, 0.16, "cloth_red", pos=(0, -0.02, h / 2 - 0.2), anchor="c")


# ---------------------------------------------------------------- market
def _stall(mb, cloth, goods):
    w, d = 9.0, 5.0
    mb.collider_box((0, 0, 1.6), (w, d, 4.4))
    mb.collision = "proxy"
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = 8.6 if sy > 0 else 7.0
            mb.box(0.42, 0.42, h + 0.6, "wood_dark", pos=(sx * (w / 2 - 0.3), sy * (d / 2 - 0.3), -0.6))
    mb.box(w, d - 0.4, 0.35, "wood_light", pos=(0, 0, 3.0))
    mb.box(w - 0.6, 0.3, 2.2, "wood_mid", pos=(0, -d / 2 + 0.5, 0.8))
    for sx in (-1, 1):
        mb.box(0.3, d - 1.0, 2.2, "wood_mid", pos=(sx * (w / 2 - 0.5), 0, 0.8))
    n = 8
    sw = (w + 1.4) / n
    for i in range(n):
        x = -(w + 1.4) / 2 + sw * (i + 0.5)
        col = cloth[i % 2]
        mb.beam((x, d / 2 + 0.3, 8.9), (x, -d / 2 - 1.5, 6.9), sw, 0.14, col, grad=(0.4, 0.66))
        mb.box(sw, 0.12, 0.6 if i % 2 else 0.85, col, pos=(x, -d / 2 - 1.5, 6.9 - (0.55 if i % 2 else 0.8)),
               tone=-0.05)
    goods(mb)


def _tray(mb, x, y, colors, n=6, r=0.42, z=3.35):
    mb.box(2.4, 1.9, 0.5, "wood_mid", pos=(x, y, z), taper=1.12)
    for i in range(n):
        gx = x - 0.75 + 0.75 * (i % 3) + mb.jitter(0.08)
        gy = y - 0.4 + 0.8 * (i // 3) + mb.jitter(0.08)
        mb.blob(r, colors[i % len(colors)], pos=(gx, gy, z + 0.62), level=0, noise=0.08, grad=(0.35, 0.75))


def market_stall_fruit(mb):
    def goods(mb):
        _tray(mb, -2.9, -0.5, ("flower_red", "flower_red", "leaf_lime"))
        _tray(mb, 0.0, -0.5, ("roof_orange", "flower_yellow"))
        _tray(mb, 2.9, -0.5, ("leaf_green", "leaf_lime"), r=0.5)
        crate_at(mb, 5.8, -1.6, 0, s=2.0, rot=12)
        barrel_at(mb, -6.0, 0.6, 0, s=0.9)
    _stall(mb, ("cloth_red", "cloth_white"), goods)


def market_stall_bread(mb):
    def goods(mb):
        for i in range(5):
            mb.blob(0.6, "plaster_yellow", pos=(-3.2 + i * 0.9, -0.8, 3.75), scale=(0.75, 1.5, 0.6), level=0,
                    noise=0.08, grad=(0.25, 0.6), tone=-0.12)
        for i in range(4):
            mb.cyl(0.75, 0.6, 0.6, "thatch", pos=(1.6 + (i % 2) * 1.7, -1.1 + (i // 2) * 1.5, 3.35), segs=7)
        mb.box(3.0, 1.4, 0.2, "cloth_white", pos=(-1.4, 0.9, 3.35))
        for i in range(3):
            mb.blob(0.45, "wood_pale", pos=(-2.3 + i * 0.9, 0.9, 3.85), level=0, noise=0.1)
        sack_at(mb, 5.9, -0.8, 0, s=1.1)
        sack_at(mb, 6.3, 1.0, 0, s=0.9, color="plaster_cream")
    _stall(mb, ("cloth_yellow", "cloth_white"), goods)


def market_stall_cloth(mb):
    def goods(mb):
        cols = ("cloth_blue", "cloth_red", "cloth_green", "cloth_yellow", "flower_purple", "cloth_white")
        for i, c in enumerate(cols):
            with mb.at(T(-3.4 + i * 1.35, -0.3, 3.75), R("X", 90)):
                mb.cyl(0.42, 0.42, 3.2, c, pos=(0, 0, -1.6), segs=6)
        mb.beam((-4.2, 2.2, 7.8), (4.2, 2.2, 7.8), 0.2, 0.2, "wood_dark")
        for i, c in enumerate(("cloth_blue", "cloth_red", "cloth_green")):
            mb.box(1.9, 0.1, 3.0, c, pos=(-2.6 + i * 2.6, 2.2, 4.8), grad=(0.35, 0.65))
        crate_at(mb, -6.0, -1.0, 0, s=2.0, rot=-8)
    _stall(mb, ("cloth_blue", "cloth_white"), goods)


# ---------------------------------------------------------------- storage
def barrel(mb):
    barrel_at(mb, 0, 0, 0)


def barrel_stack(mb):
    barrel_at(mb, -1.25, 0, 0)
    barrel_at(mb, 1.25, 0.2, 0)
    barrel_at(mb, 0.0, 2.2, 0, s=0.95)
    barrel_at(mb, 0.0, 0.7, 3.0, s=0.9)


def crate(mb):
    crate_at(mb, 0, 0, 0)


def crate_stack(mb):
    crate_at(mb, -1.2, 0, 0, s=2.4, rot=4)
    crate_at(mb, 1.4, 0.3, 0, s=2.0, rot=-9)
    crate_at(mb, -0.9, 0.1, 2.4, s=1.8, rot=17)
    sack_at(mb, 1.6, -1.9, 0, s=0.85)


def sack_pile(mb):
    sack_at(mb, -1.0, 0, 0)
    sack_at(mb, 1.0, 0.3, 0, s=0.95, color="plaster_cream")
    sack_at(mb, 0.1, -0.3, 1.3, s=0.9)


def woodpile(mb):
    mb.collider_box((0, 0, 2.2), (7.2, 2.8, 5.6))
    mb.collision = "proxy"
    for sx in (-1, 1):
        mb.box(0.45, 0.45, 5.4, "wood_dark", pos=(sx * 3.2, 0, -0.6))
    with mb.at(T(-3.9, 0.9, 4.6)):
        lean_to_roof(mb, 0, 7.8, 2.6, 1.0, "roof_brown", og=0.2, oe=0.3, courses=2)
    rows = 4
    for r in range(rows):
        n = 6 - (r % 2)
        for i in range(n):
            x = -2.5 + (5.0 / (6 - 1)) * (i + 0.5 * (r % 2))
            with mb.at(T(x, 0, 0.45 + r * 0.85), R("X", 90)):
                mb.cyl(0.45, 0.45, 2.6, "bark", pos=(0, 0, -1.3), segs=6, tone=mb.jitter(0.05))
                mb.cyl(0.36, 0.36, 0.04, "wood_pale", pos=(0, 0, 1.3), segs=6, tone=mb.jitter(0.06))


def hay_bale(mb):
    with mb.at(T(0, 0, 1.6), R("Y", 90)):
        mb.cyl(1.6, 1.6, 3.0, "thatch", pos=(0, 0, -1.5), segs=10, grad=(0.3, 0.7))
        for z in (-0.8, 0.8):
            mb.lathe([(1.64, z - 0.08), (1.64, z + 0.08)], "thatch_dark", segs=10)


def haystack(mb):
    mb.lathe([(3.6, -0.5), (3.9, 1.5), (3.0, 4.6), (1.2, 6.8), (0.0, 7.4)], "thatch", segs=9, smooth=False,
             grad=(0.26, 0.82))
    mb.cyl(0.16, 0.12, 2.4, "wood_dark", pos=(0, 0, 6.6), segs=5)
    mb.beam((2.6, -2.6, 0.0), (0.9, -0.9, 6.0), 0.2, 0.2, "wood_mid")           # pitchfork
    for dx in (-0.3, 0.0, 0.3):
        mb.beam((0.9 + dx, -0.9 - dx, 6.0), (0.6 + dx, -0.6 - dx, 7.1), 0.08, 0.08, "iron")


def cart(mb):
    """Two-wheeled hand cart loaded with hay."""
    mb.box(7.0, 4.0, 0.35, "wood_light", pos=(0, 0, 2.4))
    for sy in (-1, 1):
        mb.box(7.0, 0.25, 1.5, "wood_mid", pos=(0, sy * 2.0, 2.6))
        for x in (-3.2, -1.1, 1.1, 3.2):
            mb.box(0.3, 0.3, 1.9, "wood_dark", pos=(x, sy * 2.1, 2.5))
        with mb.at(T(-0.6, sy * 2.6, 2.1), R("X", 90)):
            mb.lathe([(2.1, -0.18), (2.1, 0.18)], "wood_dark", segs=12, smooth=False)
            mb.cyl(0.5, 0.5, 0.6, "iron", pos=(0, 0, -0.3), segs=6)
            for k in range(4):
                a = math.pi / 4 * k
                mb.beam((-1.9 * math.cos(a), -1.9 * math.sin(a), 0), (1.9 * math.cos(a), 1.9 * math.sin(a), 0),
                        0.22, 0.22, "wood_mid", up=(0, 0, 1))
        mb.beam((3.4, sy * 1.5, 2.5), (7.4, sy * 1.5, 1.0), 0.3, 0.3, "wood_mid")
    mb.box(0.3, 4.0, 1.5, "wood_mid", pos=(-3.4, 0, 2.6))
    mb.box(0.4, 0.4, 2.4, "wood_dark", pos=(3.0, 0, 0.0))
    mb.blob(2.4, "thatch", pos=(-0.2, 0, 3.6), scale=(1.35, 0.8, 0.6), level=1, noise=0.15, grad=(0.3, 0.8))


def planter(mb):
    """Half barrel full of flowers."""
    mb.lathe([(1.5, 0), (1.75, 1.6)], "wood_mid", segs=8, grad=(0.36, 0.6))
    mb.lathe([(1.68, 0.4), (1.72, 0.65)], "iron", segs=8)
    mb.cyl(1.6, 1.6, 0.1, "dirt_dark", pos=(0, 0, 1.45), segs=8)
    for i in range(3):
        a = i * 2.1
        mb.blob(0.8, "leaf_green", pos=(0.7 * math.cos(a), 0.7 * math.sin(a), 1.9), level=0, noise=0.2,
                scale=(1, 1, 0.7), grad=(0.3, 0.8))
    for i in range(6):
        a = i * 2.39996
        r = 0.5 + 0.7 * (i % 2)
        octa(mb, 0.32, 0.55, ("flower_red", "flower_yellow", "flower_purple")[i % 3],
             pos=(r * math.cos(a), r * math.sin(a), 2.2 + 0.25 * (i % 3)))


def beehives(mb):
    mb.collider_box((0, 0, 1.8), (6.0, 2.4, 4.8))
    mb.collision = "proxy"
    mb.box(6.0, 2.4, 0.3, "wood_light", pos=(0, 0, 1.6))
    for sx in (-1, 1):
        mb.box(0.4, 2.0, 2.2, "wood_dark", pos=(sx * 2.4, 0, -0.6))
    for x in (-1.6, 1.6):
        mb.lathe([(1.2, 0), (1.3, 0.5), (1.15, 1.0), (1.2, 1.5), (0.95, 2.0), (0.5, 2.5), (0.0, 2.7)], "thatch",
                 segs=8, pos=(x, 0, 1.9), smooth=False, grad=(0.3, 0.78))
        mb.box(0.5, 0.1, 0.3, "iron", pos=(x, -1.2, 2.0))


def scarecrow(mb):
    mb.collider_cyl((0, 0, 4.0), 0.7, 9.0)
    mb.collision = "proxy"
    mb.box(0.4, 0.4, 8.6, "wood_dark", pos=(0, 0, -1.0))
    mb.beam((-3.2, 0, 5.6), (3.2, 0, 5.6), 0.35, 0.35, "wood_dark")
    mb.box(2.6, 1.0, 3.2, "cloth_blue", pos=(0, 0, 3.2), taper=(0.8, 0.9), grad=(0.35, 0.65))
    for sx in (-1, 1):
        mb.beam((sx * 1.0, 0, 5.6), (sx * 3.0, 0, 5.5), 0.8, 0.8, "cloth_blue")
        mb.blob(0.5, "thatch", pos=(sx * 3.3, 0, 5.5), level=0, noise=0.3)
    mb.blob(1.05, "cloth_white", pos=(0, 0, 7.2), level=1, noise=0.06, grad=(0.35, 0.7))
    mb.lathe([(1.9, 7.8), (1.0, 8.2), (0.8, 9.2), (0.0, 9.5)], "thatch_dark", segs=7, smooth=False)
    octa(mb, 0.16, 0.3, "roof_orange", pos=(0, -1.0, 7.1))
    mb.blob(0.6, "thatch", pos=(0, 0, 3.0), scale=(1.6, 0.8, 0.5), level=0, noise=0.3)


def clothesline(mb):
    mb.collision = "proxy"
    for sx in (-1, 1):
        mb.collider_cyl((sx * 6.0, 0, 3.0), 0.5, 8.0)
        mb.box(0.4, 0.4, 8.0, "wood_dark", pos=(sx * 6.0, 0, -1.0))
        mb.beam((sx * 6.0 - 0.9, 0, 6.6), (sx * 6.0 + 0.9, 0, 6.6), 0.3, 0.3, "wood_dark")
    mb.beam((-6.0, 0, 6.5), (6.0, 0, 6.5), 0.08, 0.08, "wood_pale")
    for x, w, h, c in ((-4.2, 1.8, 2.6, "cloth_white"), (-1.9, 2.2, 2.0, "cloth_red"), (0.8, 1.6, 3.0, "cloth_blue"),
                       (3.2, 2.4, 2.2, "cloth_yellow")):
        with mb.at(T(x, 0, 6.5), R("X", mb.jitter(7))):
            mb.box(w, 0.07, h, c, pos=(0, 0, -h), grad=(0.32, 0.66))


def banner_pole(mb):
    mb.collider_cyl((0, 0, 7.5), 0.7, 16.0)
    mb.collision = "proxy"
    mb.box(1.3, 1.3, 1.2, "stone_grey", pos=(0, 0, -0.5), taper=0.8)
    flag(mb, 0, 0, 0.5, h=15.0, color="cloth_red", length=5.6)
    mb.box(0.12, 2.6, 5.0, "cloth_yellow", pos=(0, 1.5, 7.6), grad=(0.36, 0.66))
    mb.beam((0, 0, 12.7), (0, 2.9, 12.7), 0.16, 0.16, "wood_dark")


# ---------------------------------------------------------------- water side
def bridge_stone(mb):
    """Humpback stone bridge. Road runs along X (28 studs), deck 12 wide,
    road level z = 0 at both ends, water expected around z = -4."""
    L, half_w, hump = 28.0, 6.0, 2.6
    mb.collision = "mesh_precise"      # curved deck: needs PreciseConvexDecomposition in Roblox

    def top(x):
        return hump * (1 - (x / (L / 2)) ** 2)

    n = 10
    xs = [-L / 2 + L * i / n for i in range(n + 1)]
    span, zs, rise = 8.0, -4.2, 4.4
    arc = [(span * math.cos(math.pi * i / 8), zs + rise * math.sin(math.pi * i / 8)) for i in range(9)]
    poly = [(x, top(x) - 0.3) for x in xs] + [(L / 2, -9.0), (span, -9.0)] + arc[1:-1] + [(-span, -9.0), (-L / 2, -9.0)]
    mb.prism(poly, -half_w, half_w, "stone_grey", grad=(0.3, 0.64))
    rings = [[(x, -half_w + 0.9, top(x) - 0.3), (x, half_w - 0.9, top(x) - 0.3), (x, half_w - 0.9, top(x) + 0.02),
              (x, -half_w + 0.9, top(x) + 0.02)] for x in xs]
    mb.loft(rings, "cobble", grad=(0.45, 0.58))
    for sy in (-1, 1):
        y0, y1 = sy * (half_w - 0.95), sy * (half_w + 0.25)
        rings = [[(x, min(y0, y1), top(x) - 0.4), (x, max(y0, y1), top(x) - 0.4), (x, max(y0, y1), top(x) + 2.9),
                  (x, min(y0, y1), top(x) + 2.9)] for x in xs]
        mb.loft(rings, "stone_warm", grad=(0.4, 0.62))
        for i in range(n):
            xm = (xs[i] + xs[i + 1]) / 2
            mb.box((L / n) - 0.25, 1.5, 0.55, ("stone_light", "stone_dark")[i % 2],
                   pos=(xm, sy * (half_w - 0.35), top(xm) + 2.8), tone=mb.jitter(0.04))
        for x in (-L / 2 + 0.6, L / 2 - 0.6):
            mb.box(1.9, 1.9, 5.2, "stone_dark", pos=(x, sy * (half_w - 0.35), top(x) - 1.0), taper=0.9)
            octa(mb, 0.9, 1.3, "stone_light", pos=(x, sy * (half_w - 0.35), top(x) + 4.2))
        k = (span + 0.5) / span
        with mb.at(T(0, sy * (half_w + 0.02), 0), R("Z", 0 if sy < 0 else 180)):
            for a, b in zip(arc[:-1], arc[1:]):
                w_beam(mb, a[0] * k, zs + (a[1] - zs) * k, b[0] * k, zs + (b[1] - zs) * k,
                       "stone_light", w=1.0, t=0.3, tone=mb.jitter(0.05))
            mb.box(1.5, 0.5, 1.6, "stone_light", pos=(0, -0.15, zs + rise - 0.1))


def dock(mb):
    """Wooden jetty reaching 20 studs out along -Y; deck at z = 0."""
    mb.collider_box((0, -10.1, -0.4), (6.6, 20.6, 0.8))
    mb.collision = "proxy"
    n = 11
    for i in range(n):
        y = -1.0 - i * 1.8
        mb.box(6.4 + mb.jitter(0.25), 1.6, 0.35, "wood_light", pos=(mb.jitter(0.1), y, -0.35), tone=mb.jitter(0.07))
    for sx in (-1, 1):
        mb.beam((sx * 2.6, 0.2, -0.55), (sx * 2.6, -20.4, -0.55), 0.5, 0.5, "wood_mid")
        for y in (-1.5, -10.0, -19.6):
            h = 2.0 if y < -15 else 0.4
            mb.cyl(0.45, 0.4, 7.0 + h, "wood_dark", pos=(sx * 3.1, y, -7.0), segs=6)
    mb.beam((3.1, -19.6, 1.6), (-3.1, -19.6, 1.6), 0.25, 0.25, "wood_pale")
    barrel_at(mb, -1.9, -3.0, 0, s=0.8)
    lantern_head(mb, 3.1, -19.6, 3.9, s=0.8)
    mb.cyl(0.1, 0.1, 0.5, "iron", pos=(3.1, -19.6, 1.9), segs=4)


def rowboat(mb):
    """Small boat; waterline at z = 0, bow towards +X."""
    stations = ((-4.6, 0.9, 1.2), (-3.2, 1.9, 1.0), (0.0, 2.3, 0.9), (3.0, 1.7, 1.05), (5.2, 0.15, 1.5))
    rings = []
    for x, hw, top in stations:
        rings.append([(x, -hw, top), (x, -hw * 0.75, -0.2), (x, 0.0, -0.75), (x, hw * 0.75, -0.2), (x, hw, top)])
    mb.loft(rings, "wood_mid", grad=(0.3, 0.62))
    inner = [(x, hw * 0.82, top - 0.12) for x, hw, top in stations]
    pts = inner + [(x, -y, z) for x, y, z in reversed(inner)]
    mb.poly(pts, "wood_dark", facing=(0, 0, 1), tone=-0.1)
    for x, hw in ((-2.4, 1.7), (1.0, 2.1)):
        mb.box(1.0, hw * 2, 0.25, "wood_light", pos=(x, 0, 0.85))
    for sy in (-1, 1):
        mb.beam((0.6, sy * 2.2, 1.0), (-3.0, sy * 4.8, -0.2), 0.16, 0.16, "wood_pale")
        mb.box(1.4, 0.5, 0.1, "wood_pale", pos=(-3.4, sy * 5.05, -0.3))


PROPS = {
    "well": well, "fountain": fountain, "trough": trough,
    "lantern_post": lantern_post, "lantern_post_double": lantern_post_double,
    "fence_post": fence_post, "fence_wood": fence_wood, "fence_picket": fence_picket,
    "stone_wall": stone_wall, "gate_arch": gate_arch,
    "bench": bench, "signpost": signpost, "notice_board": notice_board,
    "market_stall_fruit": market_stall_fruit, "market_stall_bread": market_stall_bread,
    "market_stall_cloth": market_stall_cloth,
    "barrel": barrel, "barrel_stack": barrel_stack, "crate": crate, "crate_stack": crate_stack,
    "sack_pile": sack_pile, "woodpile": woodpile, "hay_bale": hay_bale, "haystack": haystack,
    "cart": cart, "planter": planter, "beehives": beehives, "scarecrow": scarecrow,
    "clothesline": clothesline, "banner_pole": banner_pole,
    "bridge_stone": bridge_stone, "dock": dock, "rowboat": rowboat,
}
