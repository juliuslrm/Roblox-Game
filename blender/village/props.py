"""Things the market traders hold, modelled at real size (1 stud = 0.27 m: a 6.4 stud figure is
about 1.73 m tall).

Prop space = the closed hand: origin on the handle axis inside the fist, +Y along the handle from
the thumb / index side to the little finger, -Z the direction the fingers point when the hand is
open (+Z towards the wrist), X = Y x Z.  With the forearm held forwards and the thumb up, -Y points
up and +Y down.  Things carried on a bail (basket, lantern) hang along -Z below the fist: they are
carried with the arm down (a bail held in a raised fist could not hang straight).

Every prop is a closed solid: the grip solver (characters.close_hand) measures the signed distance of
the finger skin to this very geometry.
"""
import math

from mathutils import Vector

from .meshkit import R, T

HANG = 12             # degrees: a basket or lantern carried with the arm down hangs slightly forwards
TAU = 2 * math.pi


def _along_y(mb, profile, color, segs=16, smooth=True, **kw):
    """Lathe whose axis is +Y: profile = [(radius, y), ...]."""
    with mb.at(R("X", -90)):
        mb.lathe(profile, color, segs=segs, smooth=smooth, **kw)


def _tube(mb, pts, radii, color, n=10, cap=True, **kw):
    rings = []
    for i, p in enumerate(pts):
        p = Vector(p)
        d = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        u = d.cross(up).normalized()
        v = d.cross(u).normalized()
        rings.append([tuple(p + (u * math.cos(TAU * k / n) + v * math.sin(TAU * k / n)) * radii[i]) for k in range(n)])
    mb.loft(rings, color, smooth=True, cap0=cap, cap1=cap, **kw)


def _leaf(mb, base, direction, length, width, color, curl=0.25):
    """A leaf as a thin closed lens: midrib from `base` along `direction`, bending down by `curl`."""
    d = Vector(direction).normalized()
    side = d.cross(Vector((0.3, 0.2, 1.0))).normalized()
    up = side.cross(d).normalized()
    rows = []
    n = 7
    for i in range(n + 1):
        t = i / n
        w = width * math.sin(math.pi * min(1.0, t * 1.08)) * (1 - 0.25 * t)
        c = Vector(base) + d * (length * t) - up * (curl * length * t * t)
        th = 0.006 + 0.004 * (1 - t)
        rows.append([tuple(c + side * (w * math.cos(TAU * k / 6)) + up * (th * math.sin(TAU * k / 6))) for k in range(6)])
    mb.loft(rows, color, smooth=True, grad=(0.3, 0.8))


def _bail(half_grip, half_span, drop):
    """Carrying bow in the YZ plane: straight along Y over |y| <= half_grip (held by the fist),
    then curving down to (y = +-half_span, z = -drop)."""
    pts = []
    for i in range(25):
        u = -1 + 2 * i / 24
        if abs(u) <= 0.5:
            pts.append((0.0, half_grip * u / 0.5, 0.0))
        else:
            a = (abs(u) - 0.5) / 0.5 * math.pi / 2
            sy = math.copysign(1, u)
            pts.append((0.0, sy * (half_grip + (half_span - half_grip) * math.sin(a)), -drop * (1 - math.cos(a))))
    return pts


# ---------------------------------------------------------------- Selma
def herb_bundle(mb, side):
    """A bundle of fresh herbs: seven stems bound with twine, leaves and small white flowers on top."""
    for k in range(7):
        a = TAU * k / 7
        r = 0.0 if k == 0 else 0.022
        x0, z0 = r * math.cos(a), r * math.sin(a)
        spread = 1.0 + 0.9 * (k > 0)
        pts = [(x0, 0.17, z0), (x0, 0.0, z0), (x0 * spread, -0.25, z0 * spread), (x0 * spread * 1.6, -0.52, z0 * spread * 1.6)]
        _tube(mb, pts, [0.011, 0.012, 0.011, 0.007], "leaf_dark" if k % 2 else "pine", n=6)
        for j in range(4):
            t = 0.3 + 0.17 * j
            stem = Vector((x0 * (1 + 0.9 * t), -0.25 - 0.27 * (t - 0.3) / 0.7 - 0.05 * j, z0 * (1 + 0.9 * t)))
            out = Vector((math.cos(a + j * 2.1), -0.6, math.sin(a + j * 2.1)))
            _leaf(mb, stem, out, 0.13 + 0.03 * (j % 2), 0.045, ("leaf_green", "leaf_lime", "leaf_dark")[(k + j) % 3])
        tip = Vector(pts[-1])
        for f in range(4):
            q = tip + Vector((0.025 * math.cos(f * 1.7), -0.02 - 0.012 * f, 0.025 * math.sin(f * 1.7)))
            mb.blob(0.018, "flower_white", pos=tuple(q), level=1, noise=0.15, smooth=True)
        mb.blob(0.011, "flower_yellow", pos=tuple(tip + Vector((0, -0.04, 0))), level=1, noise=0.0, smooth=True)
    # twine just in front of the fist
    for i in range(3):
        y = -0.085 - 0.018 * i
        with mb.at(T(0, y, 0)):
            mb.ring_loft([[(math.cos(TAU * j / 14) * (0.044 + 0.006 * math.cos(TAU * k / 6)), 0.006 * math.sin(TAU * k / 6),
                            math.sin(TAU * j / 14) * (0.044 + 0.006 * math.cos(TAU * k / 6))) for k in range(6)] for j in range(14)],
                         "thatch_dark", smooth=True)


def basket(mb, side):
    """Wicker basket on a bent bow.  The fist holds the top of the bow."""
    with mb.at(R("X", HANG)):
        _tube(mb, _bail(0.2, 0.4, 0.6), [0.034] * 25, "wood_light", n=12)
        for sy in (-1, 1):                                                     # bow fixings
            mb.blob(0.05, "wood_mid", pos=(0, sy * 0.4, -0.6), scale=(0.8, 0.6, 1.4), level=1, noise=0.0, smooth=True)
        with mb.at(T(0, 0, -0.62)):
            # wicker body: oval in plan (long along the bow), woven bands
            rows = []
            prof = [(0.43, 0.0), (0.44, -0.04), (0.42, -0.18), (0.39, -0.34), (0.34, -0.48), (0.28, -0.53), (0.0, -0.54)]
            segs = 28
            for r, z in prof:
                rows.append([(r * 0.78 * math.cos(TAU * i / segs), r * math.sin(TAU * i / segs), z) for i in range(segs)])
            for j in range(len(rows) - 1):
                if prof[j + 1][0] == 0.0:
                    continue
                mb.loft([rows[j], rows[j + 1]], "thatch" if j % 2 else "thatch_dark", smooth=True, cap0=False, cap1=False)
            mb.lathe([(0.0, -0.54), (0.28, -0.53), (0.0, -0.5)], "thatch_dark", segs=segs, pos=(0, 0, 0))
            for i in range(segs):                                              # upright willow rods
                a = TAU * (i + 0.5) / segs
                pts = [(r * 0.8 * math.cos(a), r * 1.02 * math.sin(a), z) for r, z in prof[:-1]]
                _tube(mb, pts, [0.012] * len(pts), "wood_pale", n=5)
            mb.ring_loft([[((0.44 + 0.022 * math.cos(TAU * k / 8)) * 0.78 * math.cos(TAU * j / 32),          # rim
                            (0.44 + 0.022 * math.cos(TAU * k / 8)) * math.sin(TAU * j / 32), 0.022 * math.sin(TAU * k / 8))
                           for k in range(8)] for j in range(32)], "wood_light", smooth=True)
            # contents: herbs, a cloth and flowers
            mb.blob(0.3, "cloth_white", pos=(0.02, 0.08, -0.08), scale=(0.95, 1.1, 0.35), level=2, noise=0.12, smooth=True)
            for i in range(9):
                a = i * 2.4
                rr = 0.08 + 0.22 * ((i * 37) % 10) / 10
                _leaf(mb, (rr * 0.7 * math.cos(a), rr * math.sin(a), -0.05), (math.cos(a) * 0.3, math.sin(a) * 0.3, 1.0),
                      0.22, 0.06, ("leaf_green", "leaf_lime", "leaf_teal", "leaf_dark")[i % 4], curl=-0.3)
            for i, c in enumerate(("flower_red", "flower_yellow", "flower_purple")):
                mb.blob(0.045, c, pos=(-0.12 + 0.12 * i, -0.18 + 0.1 * i, 0.06), level=1, noise=0.2, smooth=True)


# ---------------------------------------------------------------- Nyra
def crystal(mb, side):
    """A raw crystal: the fist holds the rough base, the clear point stands out in front."""
    # main crystal: hexagonal prism along -Y with a faceted point
    rings = []
    for y, r in ((0.16, 0.07), (0.1, 0.085), (-0.3, 0.09), (-0.42, 0.06)):
        rings.append([(r * math.cos(TAU * k / 6 + 0.3), y, r * math.sin(TAU * k / 6 + 0.3)) for k in range(6)])
    mb.loft(rings, "glass_light", grad=(0.35, 1.0))
    tip = [(0.06 * math.cos(TAU * k / 6 + 0.3), -0.42, 0.06 * math.sin(TAU * k / 6 + 0.3)) for k in range(6)]
    mb.add(tip + [(0.0, -0.56, 0.0)], [(k, (k + 1) % 6, 6) for k in range(6)] + [tuple(range(5, -1, -1))],
           "flower_purple", closed=True, grad=(0.5, 1.0))
    # rough host rock at the base and two side crystals
    mb.blob(0.1, "rock_dark", pos=(0, 0.17, 0), scale=(1.0, 0.6, 1.0), level=2, noise=0.25, smooth=True)
    for a, ln in ((1.1, 0.2), (3.6, 0.15)):
        d = Vector((0.7 * math.cos(a), -1.0, 0.7 * math.sin(a))).normalized()
        base = Vector((0.04 * math.cos(a), 0.12, 0.04 * math.sin(a)))
        u = d.cross(Vector((1, 0, 0))).normalized()
        v = d.cross(u).normalized()
        ring = lambda c, r: [tuple(c + (u * math.cos(TAU * k / 6) + v * math.sin(TAU * k / 6)) * r) for k in range(6)]
        mb.loft([ring(base, 0.035), ring(base + d * ln, 0.035), ring(base + d * (ln + 0.06), 0.004)], "glass_light", grad=(0.4, 1.0))


def lantern(mb, side):
    """Hand lantern on a ring; it hangs below the fist."""
    with mb.at(T(0, -0.05, 0), R("X", 4)):     # hangs nearly straight; shifted so the index finger clears the bail
        # wire bail: a straight grip for the fist, bent down to the cap on both sides
        _tube(mb, _bail(0.26, 0.3, 0.46), [0.024] * 25, "iron", n=10)
        with mb.at(T(0, 0, -0.46)):
            mb.lathe([(0.0, 0.0), (0.06, -0.02), (0.2, -0.1), (0.24, -0.13), (0.0, -0.13)], "iron", segs=8, phase=TAU / 16,
                     smooth=False, grad=(0.35, 0.75))
            # glass body with four corner posts and a lit candle
            mb.box(0.36, 0.36, 0.5, "glass_lit", pos=(0, 0, -0.66), anchor="b", grad=(0.6, 1.0))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    mb.box(0.045, 0.045, 0.56, "iron", pos=(sx * 0.18, sy * 0.18, -0.69), grad=(0.3, 0.7))
            for z in (-0.16, -0.66):
                mb.box(0.42, 0.42, 0.04, "iron", pos=(0, 0, z - 0.02), grad=(0.3, 0.7))
            mb.box(0.44, 0.44, 0.06, "iron", pos=(0, 0, -0.75))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    mb.blob(0.03, "iron", pos=(sx * 0.17, sy * 0.17, -0.77), level=1, noise=0.0, smooth=True)


# ---------------------------------------------------------------- Lio
def vial(mb, side):
    """Round flask held by the neck: the cork above the thumb, the glowing body below the fist."""
    _along_y(mb, [(0.0, -0.3), (0.05, -0.3), (0.055, -0.26), (0.05, -0.2), (0.0, -0.2)], "wood_pale", segs=12)    # cork
    _along_y(mb, [(0.0, -0.21), (0.058, -0.205), (0.06, -0.18), (0.046, -0.16), (0.044, 0.06), (0.075, 0.12), (0.14, 0.18),
                  (0.172, 0.28), (0.165, 0.37), (0.12, 0.44), (0.0, 0.47)], "glass_light", segs=20, grad=(0.45, 1.0))
    mb.blob(0.15, "glass_lit", pos=(0, 0.3, 0), scale=(1, 0.92, 1), level=2, noise=0.0, smooth=True, grad=(0.55, 1.0))


def cloth(mb, side):
    """A crumpled polishing cloth in the fist, its ends hanging out on both sides."""
    mb.blob(0.075, "cloth_white", pos=(0, 0, 0), scale=(0.85, 1.55, 1.05), level=2, noise=0.18, smooth=True, grad=(0.45, 0.95))
    for sy, ln in ((1, 0.32), (-1, 0.14)):
        rows = []
        for i in range(7):
            t = i / 6
            w = 0.07 + 0.05 * t
            c = Vector((0.0, sy * (0.08 + ln * t), -0.05 * t * t * (1 if sy > 0 else 0)))
            rows.append([tuple(c + Vector((0.35 * w * math.cos(TAU * k / 8) + 0.012 * math.sin(3 * TAU * k / 8 + t * 4), 0.0,
                                           w * math.sin(TAU * k / 8)))) for k in range(8)])
        mb.loft(rows, "cloth_white", smooth=True, grad=(0.45, 0.95))


# ---------------------------------------------------------------- Aron
def hammer(mb, side):
    """Smith's hammer: ash handle with a swelled butt, steel head across the handle (striking face
    forwards = -Z), wedge on top."""
    _along_y(mb, [(0.0, 0.42), (0.05, 0.42), (0.068, 0.38), (0.066, 0.3), (0.058, 0.18), (0.055, 0.0), (0.05, -0.3),
                  (0.046, -0.6), (0.05, -0.72), (0.05, -0.92), (0.0, -0.92)], "wood_light", segs=16, grad=(0.4, 0.75))
    with mb.at(T(0, -0.82, 0)):
        prof = [(-0.25, 0.07), (-0.23, 0.085), (-0.12, 0.085), (0.1, 0.085), (0.22, 0.06), (0.3, 0.02)]
        rows = []
        for z, h in prof:
            hx = 0.085 if z < 0.22 else (0.085 if z < 0.25 else 0.03)
            rows.append([(hx * math.copysign(abs(math.cos(TAU * k / 12)) ** 0.35, math.cos(TAU * k / 12)),
                          h * math.copysign(abs(math.sin(TAU * k / 12)) ** 0.35, math.sin(TAU * k / 12)), z) for k in range(12)])
        mb.loft(rows, "iron", smooth=True, grad=(0.3, 0.8))
        mb.lathe([(0.0, -0.27), (0.07, -0.265), (0.082, -0.25)], "stone_light", segs=16, smooth=True)        # polished face
    mb.box(0.03, 0.07, 0.11, "wood_mid", pos=(0, -0.92, 0), anchor="c")


def ore(mb, side):
    """Lump of copper ore: dark host rock with green-orange veins and bright crystals."""
    mb.blob(0.15, "rock_dark", pos=(0, 0.02, -0.02), scale=(1.05, 1.25, 1.0), level=3, noise=0.14, smooth=True, grad=(0.3, 0.75))
    for i in range(9):
        a, b = i * 2.39, 0.6 + (i % 3) * 0.5
        p = Vector((0.15 * math.cos(a) * math.sin(b) * 1.0, 0.02 + 0.17 * math.cos(b), 0.15 * math.sin(a) * math.sin(b)))
        mb.blob(0.035 + 0.01 * (i % 2), ("roof_orange", "leaf_teal", "brass")[i % 3], pos=tuple(p), level=1, noise=0.25, smooth=True)


# ---------------------------------------------------------------- Esme
def axe(mb, side):
    """Felling axe: long curved hickory handle, forged head with the cutting edge forwards (-Z)."""
    pts, radii = [], []
    for i in range(15):
        t = i / 14
        y = 0.46 - 2.4 * t
        pts.append((0.0, y, 0.06 * math.sin(math.pi * t)))
        radii.append(0.06 + 0.012 * math.exp(-((t - 0.02) / 0.04) ** 2) - 0.008 * t)
    _tube(mb, pts, radii, "wood_light", n=14, grad=(0.4, 0.75))
    with mb.at(T(0, -1.82, 0.0)):
        # eye around the handle, cheeks, and a flaring bit
        rows = []
        for z, hy, hx in ((0.12, 0.09, 0.05), (0.0, 0.1, 0.06), (-0.12, 0.09, 0.045), (-0.3, 0.12, 0.022), (-0.46, 0.2, 0.01),
                          (-0.52, 0.22, 0.004)):
            rows.append([(hx * math.cos(TAU * k / 10), hy * math.sin(TAU * k / 10), z) for k in range(10)])
        mb.loft(rows, "iron", smooth=True, grad=(0.3, 0.85))
        mb.loft([[(0.004 * math.cos(TAU * k / 10), 0.22 * math.sin(TAU * k / 10), z) for k in range(10)] for z in (-0.5, -0.545)],
                "stone_light", smooth=True)


def folding_rule(mb, side):
    """Wooden folding rule, half opened: the first leg in the fist, the second bent away."""
    def leg(color):
        mb.box(0.016, 0.62, 0.07, color, pos=(0, -0.31, 0), anchor="c", grad=(0.45, 0.8))
        for i in range(12):                                                   # scale marks on both faces
            for sx in (-1, 1):
                mb.box(0.003, 0.006, 0.025 if i % 2 else 0.04, "wood_dark", pos=(sx * 0.0095, -0.03 - i * 0.05, 0.02), anchor="c")
    with mb.at(T(0, 0.14, 0)):
        leg("wood_pale")
        with mb.at(T(0, -0.62, 0), R("X", -58)):
            mb.blob(0.022, "brass", pos=(0, 0, 0), scale=(0.6, 1, 1), level=1, noise=0.0, smooth=True)
            leg("wood_pale")
            with mb.at(T(0, -0.62, 0), R("X", 140)):
                leg("wood_pale")


# role -> hand -> (builder, tilt of the handle in degrees, distance of the handle axis from the
# knuckle line towards the wrist: in a power grip the handle lies in the palm, the bent first finger
# links carry it)
PROPS = {
    "selma": {"R": (herb_bundle, 6, 0.08), "L": (basket, 4, 0.085)},
    "nyra": {"R": (crystal, 8, 0.11), "L": (lantern, 4, 0.08)},
    "lio": {"R": (vial, 6, 0.08), "L": (cloth, 4, 0.1)},
    "aron": {"R": (hammer, 14, 0.1), "L": (ore, 0, 0.13)},
    "esme": {"R": (axe, 12, 0.1), "L": (folding_rule, 8, 0.07)},
}
