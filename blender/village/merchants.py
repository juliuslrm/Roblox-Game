"""The five market traders: detailed figures with realistic proportions.

Each trader consists of seven rigid parts that turn in joints (no skinning):

    lower   hips, legs, boots, skirt                   fixed
    torso   chest, clothes, belt, apron, neck          turns at the waist
    head    face, eyes, ears, hair, hat                turns at the neck
    upper_l / upper_r   upper arm with sleeve          turns at the shoulder
    fore_l / fore_r     forearm, hand, tool            turns at the elbow

"l" is the figure's left arm (Blender +X; the figure faces -Y), "r" its right arm.
All parts are modelled in the rest pose (arms hanging, palms towards the body) in the figure's own
space: origin at the ground between the feet, 1 unit = 1 stud.  Every figure is modelled at a
height of about 6.4 studs (7.6 head lengths) and scaled by LOOK[role]["scale"].  `pose_frames`
gives the joint frame of every part for a moment of the idle loop.

Faces, hair and clothes are sculpted from parametric surfaces: the head is a lat-long grid around
the skull whose points are pushed out or in for nose, brows, eye sockets, cheekbones, lips and chin;
hair, beards, hoods and aprons are closed shells laid over the body surface.
"""
import math

from mathutils import Matrix, Vector

from .meshkit import R, S, T

TAU = 2 * math.pi
PARTS = ("lower", "torso", "head", "upper_l", "fore_l", "upper_r", "fore_r")
ROLES = ("selma", "nyra", "lio", "aron", "esme")

# ---- proportions (nominal figure, scale 1) ----------------------------------------------------------
WAIST_Z = 3.86
NECK_Z = 5.46
SHOULDER_Z = 5.2
UPPER_LEN, FORE_LEN = 1.14, 0.9          # shoulder -> elbow, elbow -> wrist
HEAD_Z = 6.0                             # centre of the skull
HX, HY, HZ = 0.255, 0.3, 0.42            # half width, half depth, half height (chin to crown)

LOOK = {
    "selma": dict(scale=0.96, female=True, shoulder=0.6, coat="cloth_green", trim="pine", apron="plaster_cream",
                  skin="plaster_peach", hair="roof_orange", lips="roof_red", iris="leaf_dark", blush="plaster_rose",
                  pants="pine", boots="wood_dark", robe=True),
    "nyra": dict(scale=0.95, female=True, shoulder=0.58, coat="roof_purple", trim="roof_slate", apron=None,
                 skin="plaster_rose", hair="stone_light", lips="flower_purple", iris="roof_purple", blush=None,
                 pants="roof_slate", boots="iron", robe=True),
    "lio": dict(scale=1.0, female=False, shoulder=0.64, coat="cloth_blue", trim="roof_teal", apron=None, vest="wood_mid",
                skin="wood_pale", hair="wood_dark", lips="brick", iris="roof_teal", blush=None,
                pants="roof_slate", boots="wood_dark", robe=False),
    "aron": dict(scale=1.03, female=False, shoulder=0.72, coat="roof_red", trim="iron", apron="wood_red",
                 skin="plaster_peach", hair="wood_dark", lips="brick", iris="wood_dark", blush="plaster_rose",
                 pants="roof_slate", boots="iron", robe=False),
    "esme": dict(scale=0.98, female=True, shoulder=0.6, coat="roof_teal", trim="leaf_dark", apron=None, vest="wood_mid",
                 skin="plaster_peach", hair="brick", lips="brick", iris="leaf_dark", blush=None,
                 pants="leaf_dark", boots="wood_red", robe=False),
}


def joints(role):
    look = LOOK[role]
    k, sx = look["scale"], look["shoulder"]
    out = {"lower": Vector((0, 0, 0)), "torso": Vector((0, 0, WAIST_Z * k)), "head": Vector((0, 0, NECK_Z * k))}
    for side, tag in ((1, "l"), (-1, "r")):
        out["upper_" + tag] = Vector((side * sx * k, 0.0, SHOULDER_Z * k))
        out["fore_" + tag] = Vector((side * sx * k, 0.0, (SHOULDER_Z - UPPER_LEN) * k))
    return out


# ---------------------------------------------------------------- shape helpers
def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def _smooth(t):
    t = _clamp(t)
    return t * t * (3 - 2 * t)


def _gauss(x):
    return math.exp(-x * x)


def _ring(rx, ry, z, n, cx=0.0, cy=0.0, p=2.0, ripple=None):
    """Superellipse ring (p = 2 ellipse, larger = boxier); ripple(a) -> radial factor."""
    pts = []
    for i in range(n):
        a = TAU * i / n
        s, c = math.sin(a), math.cos(a)
        k = ripple(a) if ripple else 1.0
        x = rx * k * math.copysign(abs(s) ** (2 / p), s)
        y = -ry * k * math.copysign(abs(c) ** (2 / p), c)          # a = 0 at the front (-Y)
        pts.append((cx + x, cy + y, z))
    return pts


def _body(mb, sections, color, n=24, p=2.0, ripple=None, **kw):
    """Smooth closed body from sections [(z, rx, ry, cy, cx)] (cy, cx optional)."""
    rings = []
    for s in sections:
        cy = s[3] if len(s) > 3 else 0.0
        cx = s[4] if len(s) > 4 else 0.0
        rings.append(_ring(s[1], s[2], s[0], n, cx=cx, cy=cy, p=p, ripple=(lambda a, z=s[0]: ripple(a, z)) if ripple else None))
    mb.loft(rings, color, smooth=True, **kw)


def _tube(mb, pts, radii, color, n=10, **kw):
    """Smooth tube along a polyline of points with a radius per point (tapered strands, fingers)."""
    rings = []
    for i, p in enumerate(pts):
        p = Vector(p)
        d = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        u = d.cross(up).normalized()
        v = d.cross(u).normalized()
        r = radii[i]
        rings.append([tuple(p + (u * math.cos(TAU * k / n) + v * math.sin(TAU * k / n)) * r) for k in range(n)])
    mb.loft(rings, color, smooth=True, **kw)


def _shell(mb, outer, inner, us, fs, color, smooth=True, fcolor=None, **kw):
    """Closed solid between two parametric surfaces outer(u, f) and inner(u, f) over the grid us x fs
    (a hood, a beard, an apron following the body).  fcolor(u, f) -> colour of an outer face."""
    nu, nf = len(us), len(fs)
    verts = [outer(u, f) for f in fs for u in us] + [inner(u, f) for f in fs for u in us]
    off = nu * nf
    faces, colors = [], []

    def idx(i, j, layer):
        return layer * off + j * nu + i
    for j in range(nf - 1):
        for i in range(nu - 1):
            faces.append((idx(i, j, 0), idx(i + 1, j, 0), idx(i + 1, j + 1, 0), idx(i, j + 1, 0)))
            colors.append(fcolor((us[i] + us[i + 1]) / 2, (fs[j] + fs[j + 1]) / 2) if fcolor else color)
            faces.append((idx(i, j + 1, 1), idx(i + 1, j + 1, 1), idx(i + 1, j, 1), idx(i, j, 1)))
            colors.append(color)
    # side walls, oriented consistently with the outer face (du x df) and the reversed inner face;
    # the closed-solid check of MeshBuilder.add then turns the whole shell outwards if needed
    for j in range(nf - 1):                                         # walls at u = first / last
        for i, rev in ((0, False), (nu - 1, True)):
            f = (idx(i, j, 0), idx(i, j + 1, 0), idx(i, j + 1, 1), idx(i, j, 1))
            faces.append(tuple(reversed(f)) if rev else f)
            colors.append(color)
    for i in range(nu - 1):                                         # walls at f = first / last
        for j, rev in ((0, True), (nf - 1, False)):
            f = (idx(i, j, 0), idx(i + 1, j, 0), idx(i + 1, j, 1), idx(i, j, 1))
            faces.append(tuple(reversed(f)) if rev else f)
            colors.append(color)
    mb.add(verts, faces, color, smooth=smooth, closed=True, fcolor=colors, **kw)


# ---------------------------------------------------------------- head and face
FACE = {
    #       brow ridge, jaw taper, chin, nose length, cheekbones, eye height
    "selma": dict(brow=0.018, jaw=0.3, chin=0.02, nose=1.0, cheek=0.024),
    "nyra": dict(brow=0.016, jaw=0.32, chin=0.018, nose=1.08, cheek=0.03),
    "lio": dict(brow=0.026, jaw=0.24, chin=0.028, nose=1.0, cheek=0.02),
    "aron": dict(brow=0.034, jaw=0.16, chin=0.034, nose=1.18, cheek=0.022),
    "esme": dict(brow=0.02, jaw=0.27, chin=0.022, nose=0.95, cheek=0.026),
}


def _skull(a, v, role, features=True):
    """Point on the skin of the head: a = angle around (0 = front, -Y), v = -1 chin .. +1 crown."""
    f = FACE[role]
    rr = (1 - min(abs(v), 1.0) ** 2.4) ** (1 / 2.4)
    s, c = math.sin(a), math.cos(a)
    jaw = _smooth((-v - 0.12) / 0.88)
    w = (1 - f["jaw"] * jaw * jaw) * (1 + 0.035 * _gauss((v + 0.05) / 0.25))
    if c > 0:                                                       # face: the lower face comes forward a little
        d = 1.0 + 0.05 * _gauss((v + 0.45) / 0.3) * c
    else:                                                           # back: occiput, tucked into the neck below
        d = (1.08 if v > -0.3 else 1.08 - 0.42 * _smooth((-v - 0.3) / 0.7)) * 1.0
        d = 1 + (d - 1) * (-c)
    x = HX * w * rr * s
    y = -HY * d * rr * c
    z = HEAD_Z + HZ * v
    if features and c > 0.05:
        X, V = x, v
        nose = 0.0
        if V > -0.3:
            nose = (0.016 + 0.08 * f["nose"] * _smooth((0.16 - V) / 0.46)) * _gauss(max(0.0, V - 0.16) / 0.05)
        else:
            nose = 0.096 * f["nose"] * _gauss((V + 0.3) / 0.055)
        nose *= _gauss(X / (0.034 + 0.03 * max(0.0, -V - 0.12)))
        nose += 0.03 * _gauss((abs(X) - 0.046) / 0.024) * _gauss((V + 0.31) / 0.045)          # nostril wings
        brow = f["brow"] * _gauss((abs(X) - 0.1) / 0.09) * _gauss((V - 0.22) / 0.06)
        socket = -0.05 * _gauss((abs(X) - 0.105) / 0.05) * _gauss((V - 0.065) / 0.065)
        cheek = f["cheek"] * _gauss((abs(X) - 0.165) / 0.06) * _gauss((V + 0.07) / 0.09)
        lips = 0.026 * _gauss(X / 0.075) * _gauss((V + 0.47) / 0.04) + 0.03 * _gauss(X / 0.068) * _gauss((V + 0.575) / 0.045)
        chin = f["chin"] * _gauss(X / 0.085) * _gauss((V + 0.85) / 0.09)
        disp = (nose + brow + socket + cheek + lips + chin) * _smooth(c * 2.2)
        n = Vector((s, -c, 0.0))
        x, y = x + disp * n.x, y + disp * n.y
    return Vector((x, y, z))


def _skull_at(role, X, V):
    """Surface point at lateral position X (front half) and height V."""
    lo, hi = -math.pi / 2, math.pi / 2
    for _ in range(30):
        mid = (lo + hi) / 2
        if _skull(mid, V, role).x < X:
            lo = mid
        else:
            hi = mid
    return _skull((lo + hi) / 2, V, role), (lo + hi) / 2


def _head_surface(mb, role, look):
    na, nv = 44, 36
    rings = []
    vs = [-1.0 + 2.0 * (k / nv) for k in range(1, nv)]
    for v in vs:
        rings.append([tuple(_skull(TAU * i / na, v, role)) for i in range(na)])
    mb.loft(rings, look["skin"], smooth=True, grad=(0.46, 0.66))
    # lips: an upper lip with a cupid's bow and a fuller lower lip, shaped along the mouth
    def lip(V0, bow, thick, push):
        pts, radii = [], []
        for k in range(11):
            t = -1 + 2 * k / 10
            X = 0.066 * t
            V = V0 + bow * (1 - abs(t)) ** 2 - 0.012 * t * t
            p, a = _skull_at(role, X, V)
            pts.append(p + Vector((math.sin(a), -math.cos(a), 0)) * (push - 0.006 * t * t))
            radii.append(thick * (0.35 + 0.65 * (1 - t * t) ** 0.6))
        _tube(mb, [tuple(q) for q in pts], radii, look["lips"], n=8, grad=(0.4, 0.62))
    lip(-0.495, 0.018, 0.017, 0.004)
    lip(-0.548, -0.012, 0.022, 0.006)
    # mouth line between the lips
    pts = []
    for k in range(9):
        X = -0.062 + 0.124 * k / 8
        p, _ = _skull_at(role, X, -0.522 + 0.012 * (abs(X) / 0.062) ** 2)
        pts.append(p + Vector((0, 0.004, 0)))
    for a, b in zip(pts, pts[1:]):
        mb.beam(tuple(a), tuple(b), 0.012, 0.012, "wood_dark", tone=-0.1)


def _eyes(mb, role, look):
    for side in (-1, 1):
        p, a = _skull_at(role, side * 0.105, 0.065)
        e = p + Vector((math.sin(a), -math.cos(a), 0)) * -0.036                   # centre of the eyeball, in the socket
        mb.blob(0.047, "plaster_white", pos=tuple(e), level=2, noise=0.0, smooth=True, grad=(0.8, 1.0))
        look_dir = Vector((side * -0.08, -1, 0)).normalized()
        front = e + look_dir * 0.044
        with mb.at(Matrix.Translation(front) @ Matrix.Rotation(math.atan2(look_dir.x, -look_dir.y), 4, "Z") @ R("X", 90)):
            mb.cyl(0.023, 0.023, 0.008, look["iris"], segs=12, grad=(0.3, 0.7))
            mb.cyl(0.011, 0.011, 0.012, "iron", segs=10, grad=(0.0, 0.1))
            mb.blob(0.005, "plaster_white", pos=(0.008 * side, 0.01, 0.014), level=0, noise=0.0, grad=(1.0, 1.0))
        # upper and lower lid, lash line
        mb.blob(0.054, look["skin"], pos=tuple(e + Vector((0, -0.004, 0.038))), scale=(1.12, 1.02, 0.5), level=1, noise=0.0,
                smooth=True, grad=(0.5, 0.62))
        mb.blob(0.051, look["skin"], pos=tuple(e + Vector((0, -0.002, -0.046))), scale=(1.08, 1.0, 0.38), level=1, noise=0.0,
                smooth=True, grad=(0.5, 0.62))
        lash = []
        for k in range(5):
            t = -1 + 2 * k / 4
            lash.append(e + Vector((t * 0.046, -0.046 + 0.012 * t * t, 0.021 - 0.012 * t * t)))
        for q0, q1 in zip(lash, lash[1:]):
            mb.beam(tuple(q0), tuple(q1), 0.009, 0.009, "iron", tone=0.1)
        # eyebrow: a tapered strip following the brow ridge
        brow = []
        for k in range(5):
            X = side * (0.04 + 0.13 * k / 4)
            q, qa = _skull_at(role, X, 0.215 + 0.03 * math.sin(math.pi * k / 4) - (0.015 if role == "aron" and k < 2 else 0))
            brow.append(q + Vector((math.sin(qa), -math.cos(qa), 0)) * 0.008)
        for k, (q0, q1) in enumerate(zip(brow, brow[1:])):
            w = 0.032 - 0.005 * k
            mb.beam(tuple(q0), tuple(q1), w, 0.014, look["hair"], tone=-0.12)


def _ears(mb, role, look):
    for side in (-1, 1):
        p = _skull(side * math.pi / 2, -0.07, role, features=False)
        with mb.at(T(p.x + side * 0.012, p.y + 0.03, p.z), R("Z", side * 12), R("Y", side * -8)):
            mb.blob(0.11, look["skin"], scale=(0.28, 0.5, 0.95), level=1, noise=0.0, smooth=True, grad=(0.45, 0.6))
            mb.blob(0.06, look["skin"], pos=(side * 0.018, -0.004, 0.0), scale=(0.25, 0.55, 0.9), level=1, noise=0.0, smooth=True, tone=-0.14)
            mb.blob(0.035, look["skin"], pos=(0, 0.0, -0.1), scale=(0.6, 0.8, 0.9), level=1, noise=0.0, smooth=True)


def _hairline(a, style):
    """Height of the hairline (v) around the head; a = 0 front."""
    t = abs(((a + math.pi) % TAU) - math.pi) / math.pi                       # 0 front .. 1 back
    pts = style.get("line", [(0.0, 0.42), (0.28, 0.26), (0.5, 0.0), (0.62, -0.1), (1.0, -0.5)])
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            k = (t - t0) / max(t1 - t0, 1e-6)
            return v0 + (v1 - v0) * _smooth(k)
    return pts[-1][1]


def _hair_cap(mb, role, look, style):
    """Hair as a shell over the scalp from the hairline to the crown, with volume on top."""
    vol, thick = style.get("volume", 0.06), style.get("thick", 0.035)
    na, nf = 40, 12

    def point(a, f, out):
        v0 = _hairline(a, style)
        v = v0 + (0.985 - v0) * f
        p = _skull(a, v, role, features=False)
        n = (p - Vector((0, 0, HEAD_Z))).normalized()
        lift = (thick + vol * _smooth(f * 1.4) * (0.6 + 0.4 * math.cos(a) ** 2)) if out else 0.004
        # a soft wave along the hairline gives strands
        if out:
            lift += style.get("wave", 0.012) * math.sin(a * style.get("waves", 14)) * (1 - f)
        return p + n * lift
    rings = []
    for k in range(nf, -1, -1):
        rings.append([tuple(point(TAU * i / na, k / nf, True)) for i in range(na)])
    for k in range(0, nf + 1):
        rings.append([tuple(point(TAU * i / na, k / nf, False)) for i in range(na)])
    mb.loft(rings, look["hair"], smooth=True, grad=(0.3, 0.62))


def build_head(mb, role):
    look = LOOK[role]
    _head_surface(mb, role, look)
    _eyes(mb, role, look)
    _ears(mb, role, look)
    hair = look["hair"]
    top = Vector((0, 0, HEAD_Z + HZ))
    if role == "selma":
        _hair_cap(mb, role, look, dict(volume=0.05, wave=0.014))
        for side in (-1, 1):                                                     # strands framing the face
            p = _skull(side * 1.15, -0.1, role, features=False)
            _tube(mb, [tuple(p + Vector((side * 0.02, -0.01, 0.2))), tuple(p + Vector((side * 0.035, -0.01, -0.02))),
                       tuple(p + Vector((side * 0.03, 0.0, -0.25)))], [0.045, 0.04, 0.025], hair, n=8)
        braid = [Vector((0.16, 0.2, HEAD_Z - 0.25))]                             # thick braid over the left shoulder
        for k in range(1, 9):
            braid.append(braid[-1] + Vector((0.035, -0.05 if k < 4 else -0.03, -0.12)))
        for k, q in enumerate(braid):
            mb.blob(0.075 - 0.004 * k, hair, pos=tuple(q + Vector((0.012 * (-1) ** k, 0, 0))), scale=(1.05, 1.0, 1.25), level=1,
                    noise=0.0, smooth=True, tone=-0.04 * (k % 2))
        mb.cyl(0.045, 0.045, 0.06, "cloth_green", pos=tuple(braid[-1] + Vector((0, 0, -0.08))), segs=8)
        # witch hat: wide soft brim, cone bending back, band with a sprig
        with mb.at(T(0, 0.03, HEAD_Z + 0.27), R("X", -8)):
            brim = [(0.62, -0.02), (0.64, 0.02), (0.44, 0.06), (0.3, 0.09), (0.28, 0.04)]
            mb.lathe(brim, look["coat"], segs=24, smooth=True, grad=(0.3, 0.7))
            cone = [(0.0, 0.32, 0.31, 0.0), (0.22, 0.27, 0.27, 0.01), (0.45, 0.2, 0.2, 0.04), (0.65, 0.12, 0.12, 0.1),
                    (0.8, 0.06, 0.06, 0.18), (0.9, 0.015, 0.015, 0.27)]
            _body(mb, [(z, rx, ry, cy) for z, rx, ry, cy in cone], look["coat"], n=18, grad=(0.3, 0.78))
            _body(mb, [(0.02, 0.322, 0.312), (0.12, 0.3, 0.29)], "wood_red", n=24)
            mb.box(0.08, 0.03, 0.08, "brass", pos=(0, -0.3, 0.03))
            for k in range(3):
                with mb.at(T(0.08 + 0.05 * k, -0.28 + 0.02 * k, 0.1), R("Y", -20 + 20 * k)):
                    mb.blob(0.045, ("leaf_lime", "leaf_green", "leaf_lime")[k], scale=(0.6, 0.35, 1.3), level=1, noise=0.05)
    elif role == "nyra":
        _hair_cap(mb, role, look, dict(volume=0.03, wave=0.01))
        for side in (-1, 1):                                                     # long straight silver hair
            for k in range(3):
                a = side * (1.1 + 0.25 * k)
                p = _skull(a, 0.0, role, features=False)
                _tube(mb, [tuple(p + Vector((0, 0, 0.25))), tuple(p + Vector((side * 0.03, 0.02, -0.2))),
                           tuple(p + Vector((side * 0.04, 0.04, -0.7))), tuple(p + Vector((side * 0.03, 0.06, -0.95)))],
                      [0.05, 0.055, 0.045, 0.02], hair, n=8)
        # hood: a cloth shell around the head, open at the face, falling onto the shoulders
        def hood(u, f, out):
            a = u
            v = -0.95 + 1.95 * f
            p = _skull(a, min(v, 0.97), role, features=False)
            n = (p - Vector((0, 0, HEAD_Z))).normalized()
            gap = 0.09 + 0.06 * f + (0.05 if v < -0.6 else 0.0)
            q = p + n * (gap + (0.035 if out else 0.0))
            if v < -0.6:
                q = q + Vector((0, 0.06, 0)) * (-0.6 - v) / 0.35
            return q
        us = [math.radians(d) for d in range(48, 313, 12)]
        fs = [k / 12 for k in range(13)]
        _shell(mb, lambda u, f: hood(u, f, True), lambda u, f: hood(u, f, False), us, fs, look["coat"], grad=(0.28, 0.66))
        for side in (-1, 1):                                                     # rolled rim along the face opening
            rim = [hood(side * math.radians(48), k / 10, True) for k in range(11)]
            _tube(mb, [tuple(q) for q in rim], [0.03] * 11, look["trim"], n=8)
        mb.cyl(0.03, 0.03, 0.02, "glass_light", pos=tuple(hood(0.0001 + math.radians(180), 0.98, True)), segs=6)
    elif role == "lio":
        _hair_cap(mb, role, look, dict(volume=0.07, wave=0.022, waves=11, line=[(0.0, 0.4), (0.3, 0.22), (0.5, -0.02),
                                                                                 (0.62, -0.12), (1.0, -0.42)]))
        for k in range(9):                                                       # tousled tufts on top
            a = -0.9 + 0.22 * k
            p = _skull(a, 0.72 - 0.08 * abs(a), role, features=False)
            n = (p - Vector((0, 0, HEAD_Z))).normalized()
            _tube(mb, [tuple(p + n * 0.05), tuple(p + n * 0.13 + Vector((0.03 * math.sin(3 * k), -0.06, 0.03))),
                       tuple(p + n * 0.16 + Vector((0.05 * math.sin(3 * k), -0.12, -0.02)))], [0.06, 0.045, 0.01], look["hair"], n=7)
        # brass goggles pushed up on the forehead, with a strap
        strap = [tuple(_skull(TAU * i / 32, 0.5, role, features=False)) for i in range(32)]
        for i in range(32):
            p = Vector(strap[i])
            n = (p - Vector((0, 0, HEAD_Z))).normalized()
            strap[i] = tuple(p + n * 0.075)
        for i in range(32):
            mb.beam(strap[i], strap[(i + 1) % 32], 0.045, 0.012, "wood_dark")
        for side in (-1, 1):
            p, a = _skull_at(role, side * 0.11, 0.52)
            with mb.at(T(*(p + Vector((0, -0.085, 0)))), R("Z", math.degrees(-a) * 0.5), R("X", 72)):
                mb.cyl(0.075, 0.07, 0.07, "brass", segs=14)
                mb.cyl(0.06, 0.06, 0.02, "glass_light", pos=(0, 0, 0.07), segs=14, grad=(0.6, 1.0))
                mb.cyl(0.078, 0.078, 0.015, "brass", pos=(0, 0, 0.068), segs=14, tone=0.1)
        mb.beam(tuple(_skull_at(role, -0.04, 0.53)[0] + Vector((0, -0.09, 0))), tuple(_skull_at(role, 0.04, 0.53)[0] + Vector((0, -0.09, 0))),
                0.02, 0.02, "brass")
    elif role == "aron":
        _hair_cap(mb, role, look, dict(volume=0.02, thick=0.025, wave=0.006, line=[(0.0, 0.36), (0.28, 0.24), (0.5, -0.05),
                                                                                    (0.62, -0.18), (1.0, -0.45)]))
        # full beard: a shell over cheeks, jaw and chin, open at the mouth
        def beard(u, f, out):
            a = u
            top = -0.6 + 0.62 * _smooth(abs(a) / 1.45)                       # beard reaches up the cheeks to the sideburns
            v = -1.08 + (top + 1.08) * f
            p = _skull(a, max(v, -1.0), role)
            if v < -1.0:
                p = p + Vector((0, 0.02, (v + 1.0) * HZ))
            n = Vector((math.sin(a), -math.cos(a), -0.3 if v < -0.8 else 0.0)).normalized()
            bulk = 0.07 * (1 - f) ** 0.7 + 0.02
            return p + n * ((bulk + 0.015 * math.sin(a * 17 + f * 6)) if out else 0.004)
        us = [math.radians(d) for d in range(-100, 101, 8)]
        fs = [k / 10 for k in range(11)]
        _shell(mb, lambda u, f: beard(u, f, True), lambda u, f: beard(u, f, False), us, fs, look["hair"], grad=(0.25, 0.6))
        for side in (-1, 1):                                                     # moustache
            p0, _ = _skull_at(role, side * 0.012, -0.37)
            p1, _ = _skull_at(role, side * 0.07, -0.43)
            p2, _ = _skull_at(role, side * 0.1, -0.56)
            _tube(mb, [tuple(p0 + Vector((0, -0.03, 0))), tuple(p1 + Vector((0, -0.035, 0))), tuple(p2 + Vector((side * 0.01, -0.02, 0)))],
                  [0.03, 0.028, 0.012], look["hair"], n=8)
        mb.cyl(0.03, 0.03, 0.035, "brass", pos=tuple(_skull_at(role, 0, -0.98)[0] + Vector((0, -0.07, -0.08))), segs=8)   # beard clasp
        # flat leather cap with a short peak
        cap = [(0.0, 0.0), (0.29, 0.0), (0.33, 0.05), (0.31, 0.12), (0.2, 0.17), (0.0, 0.18)]
        with mb.at(T(0, 0.03, HEAD_Z + 0.22), R("X", -6)):
            mb.lathe(cap, look["apron"], segs=24, smooth=True, grad=(0.3, 0.7))
            _body(mb, [(-0.02, 0.29, 0.31), (0.06, 0.3, 0.32)], "iron", n=24)
            mb.loft([[(-0.2, -0.24, 0.0), (0.2, -0.24, 0.0), (0.16, -0.42, -0.05), (-0.16, -0.42, -0.05)],
                     [(-0.2, -0.24, 0.025), (0.2, -0.24, 0.025), (0.16, -0.42, -0.025), (-0.16, -0.42, -0.025)]],
                    look["apron"], grad=(0.25, 0.5))
    else:  # esme
        _hair_cap(mb, role, look, dict(volume=0.04, wave=0.012))
        p = _skull(math.pi, 0.0, role, features=False)
        mb.blob(0.13, look["hair"], pos=tuple(p + Vector((0, 0.08, 0.02))), scale=(1.0, 0.9, 1.05), level=2, noise=0.04, smooth=True)   # bun
        _tube(mb, [tuple(p + Vector((-0.1, 0.12, 0.12))), tuple(p + Vector((0.05, 0.17, 0.05))), tuple(p + Vector((0.13, 0.13, -0.06)))],
              [0.012, 0.012, 0.012], "wood_pale", n=6)                                                              # hair pin
        for side in (-1, 1):
            q = _skull(side * 1.25, -0.05, role, features=False)
            _tube(mb, [tuple(q + Vector((side * 0.02, 0, 0.18))), tuple(q + Vector((side * 0.035, -0.01, -0.05))),
                       tuple(q + Vector((side * 0.02, 0.0, -0.2)))], [0.035, 0.03, 0.012], look["hair"], n=7)
        # hunter's hat with a feather
        with mb.at(T(0, 0.02, HEAD_Z + 0.27), R("X", -5), R("Y", 6)):
            mb.lathe([(0.48, -0.01), (0.5, 0.03), (0.34, 0.08), (0.3, 0.05)], "wood_mid", segs=24, smooth=True, grad=(0.3, 0.7))
            _body(mb, [(0.03, 0.3, 0.31), (0.2, 0.28, 0.3), (0.3, 0.22, 0.26), (0.34, 0.04, 0.16)], "wood_mid", n=20, grad=(0.3, 0.78))
            _body(mb, [(0.04, 0.305, 0.315), (0.11, 0.3, 0.31)], look["coat"], n=24)
            with mb.at(T(-0.28, 0.06, 0.1), R("Y", -30), R("X", 15)):
                _tube(mb, [(0, 0, 0), (0.02, 0, 0.25), (0.06, 0, 0.5), (0.1, 0, 0.68)], [0.012, 0.012, 0.01, 0.004], "wood_pale", n=6)
                for k in range(7):
                    z = 0.12 + 0.08 * k
                    for sx in (-1, 1):
                        mb.beam((0.01 + 0.013 * k, 0, z), (0.01 + 0.013 * k + sx * 0.06, 0, z + 0.05), 0.025, 0.006, "plaster_white")


# ---------------------------------------------------------------- torso and clothes
def _torso_sections(role):
    look = LOOK[role]
    fem = look["female"]
    wide = look["shoulder"] / 0.64
    # z, half width, half depth, forward offset (-y is forward)
    rows = [(3.62, 0.43, 0.27, 0.0), (3.86, 0.46, 0.3, 0.0), (4.12, 0.46, 0.31, -0.005), (4.42, 0.5, 0.34, -0.02),
            (4.7, 0.55, 0.36, -0.035), (4.95, 0.6, 0.34, -0.03), (5.13, 0.63, 0.3, -0.01), (5.28, 0.52, 0.26, 0.015),
            (5.38, 0.3, 0.22, 0.025)]
    out = []
    for z, x, y, cy in rows:
        if fem:
            x *= 0.94
            if 4.55 < z < 4.85:
                y += 0.035
            if z <= 4.2:
                x *= 0.95
        if z > 4.8:
            x *= wide
        if role == "aron":
            x, y = x * 1.06, y * 1.08
        out.append((z, x, y, cy))
    return out


def _torso_point(role, a, z, lift=0.0):
    """Point on the torso surface at angle a (0 = front) and height z, pushed out by `lift`."""
    rows = _torso_sections(role)
    for (z0, x0, y0, c0), (z1, x1, y1, c1) in zip(rows, rows[1:]):
        if z <= z1 or (z1, x1) == rows[-1][:2]:
            t = _clamp((z - z0) / (z1 - z0))
            x, y, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c0 + (c1 - c0) * t
            break
    s, c = math.sin(a), math.cos(a)
    p = 2.5
    px = (x + lift) * math.copysign(abs(s) ** (2 / p), s)
    py = cy - (y + lift) * math.copysign(abs(c) ** (2 / p), c)
    return Vector((px, py, z))


def build_torso(mb, role):
    look = LOOK[role]
    rows = _torso_sections(role)

    def ripple(a, z):                                                         # gathered cloth above the belt
        return 1 + 0.014 * math.sin(a * 11) * _gauss((z - 4.05) / 0.12)
    rings = []
    for z, x, y, cy in rows:
        ring = []
        for i in range(32):
            a = TAU * i / 32
            p, k = _torso_point(role, a, z), ripple(a, z)
            ring.append((p.x * k, p.y * k, p.z))
        rings.append(ring)
    mb.loft(rings, look["coat"], smooth=True, grad=(0.32, 0.72))
    # neck
    nk = 0.105 if look["female"] else 0.125
    _body(mb, [(5.3, nk * 1.12, nk * 1.05, 0.03), (5.5, nk, nk * 0.95, 0.02), (5.72, nk * 0.95, nk * 0.92, 0.01)], look["skin"], n=16,
          grad=(0.44, 0.6))
    if not look["female"]:
        mb.blob(0.035, look["skin"], pos=(0, -0.1, 5.52), scale=(0.8, 0.7, 1.2), level=1, noise=0.0, smooth=True)    # Adam's apple
    # collar: a standing band and two folded points
    _body(mb, [(5.3, nk * 1.45, nk * 1.35, 0.03), (5.44, nk * 1.38, nk * 1.28, 0.03)], look["trim"], n=20)
    for side in (-1, 1):
        mb.loft([[(side * 0.03, -0.17, 5.43), (side * 0.15, -0.12, 5.44), (side * 0.13, -0.16, 5.3)],
                 [(side * 0.03, -0.15, 5.43), (side * 0.15, -0.1, 5.44), (side * 0.13, -0.14, 5.3)]], look["trim"], grad=(0.4, 0.8))
    # placket with buttons down the front
    for k in range(6):
        z = 4.25 + 0.17 * k
        p = _torso_point(role, 0.0, z, 0.01)
        mb.blob(0.024, "brass", pos=tuple(p + Vector((0, -0.005, 0))), scale=(1, 0.5, 1), level=1, noise=0.0)
    pl = [tuple(_torso_point(role, 0.0, 4.12 + 0.12 * k, 0.004)) for k in range(11)]
    for q0, q1 in zip(pl, pl[1:]):
        mb.beam(q0, q1, 0.06, 0.012, look["trim"])
    # belt: band, holes, buckle, a pouch
    belt = [[tuple(_torso_point(role, TAU * i / 32, z, 0.022)) for i in range(32)] for z in (3.79, 3.93)]
    mb.loft(belt, "wood_dark", smooth=True, grad=(0.3, 0.55))
    b = _torso_point(role, 0.0, 3.86, 0.035)
    mb.box(0.13, 0.025, 0.12, "brass", pos=tuple(b + Vector((0, 0, -0.06))))
    mb.box(0.09, 0.03, 0.08, look["coat"], pos=tuple(b + Vector((0, -0.002, -0.04))))
    mb.box(0.012, 0.035, 0.09, "brass", pos=tuple(b + Vector((0.0, -0.005, -0.045))))
    pq = _torso_point(role, 0.9, 3.8, 0.03)
    with mb.at(T(*pq), R("Z", math.degrees(0.9))):
        mb.box(0.18, 0.08, 0.2, "wood_mid", pos=(0, -0.03, -0.22), tone=-0.05)
        mb.box(0.19, 0.09, 0.07, "wood_mid", pos=(0, -0.035, -0.06), taper=(1.0, 0.9))
        mb.box(0.03, 0.02, 0.03, "brass", pos=(0, -0.08, -0.08))

    # role clothes
    if look["apron"]:
        top = 5.0 if role == "aron" else 4.85

        def bib(u, f, out):
            z = 3.66 + (top - 3.66) * f
            half = 1.05 - 0.45 * _smooth((z - 4.0) / 0.6)
            return _torso_point(role, u * half, z, 0.045 if out else 0.028)
        us = [-1 + 2 * k / 12 for k in range(13)]
        fs = [k / 10 for k in range(11)]
        _shell(mb, lambda u, f: bib(u, f, True), lambda u, f: bib(u, f, False), us, fs, look["apron"], grad=(0.38, 0.75))
        for side in (-1, 1):                                                 # straps over the shoulders
            pts = [bib(side * 0.95, 1.0, True), _torso_point(role, side * 0.55, 5.18, 0.05), _torso_point(role, side * 0.9, 5.33, 0.05),
                   _torso_point(role, side * 2.4, 5.2, 0.04), _torso_point(role, side * 2.9, 4.4, 0.04)]
            for q0, q1 in zip(pts, pts[1:]):
                mb.beam(tuple(q0), tuple(q1), 0.07, 0.02, look["apron"])
        pk = _torso_point(role, 0.0, 4.3, 0.05)                                 # pocket with stitching
        mb.box(0.32, 0.02, 0.22, look["apron"], pos=tuple(pk + Vector((0, -0.01, -0.11))), tone=-0.07)
        for k in range(8):
            mb.box(0.025, 0.01, 0.008, "wood_dark", pos=tuple(pk + Vector((-0.14 + 0.04 * k, -0.022, 0.1))))
        if role == "aron":
            for side in (-1, 1):
                q = bib(side * 0.95, 1.0, True)
                mb.blob(0.025, "brass", pos=tuple(q + Vector((0, -0.01, -0.03))), level=1, noise=0.0)
    if look.get("vest"):
        def vest(u, f, out):
            z = 3.95 + 1.25 * f
            return _torso_point(role, u, z, 0.045 if out else 0.02)
        gap = 0.32 if role == "lio" else 0.22
        us = [gap + (TAU - 2 * gap) * k / 28 for k in range(29)]
        fs = [k / 8 for k in range(9)]
        _shell(mb, lambda u, f: vest(u, f, True), lambda u, f: vest(u, f, False), us, fs, look["vest"], grad=(0.3, 0.7))
        if role == "lio":                                                     # vials in the vest pockets
            for side in (-1, 1):
                q = vest(side * 0.75, 0.25, True)
                mb.box(0.2, 0.04, 0.16, look["vest"], pos=tuple(q + Vector((0, -0.03, 0))), tone=-0.08)
                for k in range(2):
                    mb.cyl(0.026, 0.026, 0.16, ("glass_light", "glass_lit")[k], pos=tuple(q + Vector((-0.04 + 0.08 * k, -0.04, 0.1))), segs=8)
                    mb.cyl(0.02, 0.02, 0.03, "wood_pale", pos=tuple(q + Vector((-0.04 + 0.08 * k, -0.04, 0.26))), segs=6)
        else:                                                                 # Esme: lacing and a shoulder strap
            for k in range(5):
                z = 4.05 + 0.22 * k
                for side in (-1, 1):
                    mb.beam(tuple(vest(side * gap, (z - 3.95) / 1.25, True)), tuple(vest(-side * gap, (z + 0.11 - 3.95) / 1.25, True)),
                            0.014, 0.014, "wood_pale")
            pts = [_torso_point(role, -0.5, 5.25, 0.07), _torso_point(role, 0.35, 4.6, 0.07), _torso_point(role, 0.9, 3.95, 0.07)]
            for q0, q1 in zip(pts, pts[1:]):
                mb.beam(tuple(q0), tuple(q1), 0.07, 0.025, "wood_dark")
    if role == "nyra":                                                        # cloak over the shoulders and back, moon brooch
        def cloak(u, f, out):
            z = 2.3 + 3.05 * f
            flare = 0.05 + 0.25 * (1 - f) ** 1.5
            return _torso_point(role, u, min(z, 5.3), (flare + (0.03 if out else 0.0)) + (0.0 if z <= 5.3 else 0.0)) + Vector(
                (0, 0, max(0.0, z - 5.3)))
        us = [math.radians(d) for d in range(55, 306, 10)]
        fs = [k / 14 for k in range(15)]
        _shell(mb, lambda u, f: cloak(u, f, True), lambda u, f: cloak(u, f, False), us, fs, look["trim"], grad=(0.25, 0.62))
        q = _torso_point(role, 0.0, 5.18, 0.06)
        with mb.at(T(*q), R("X", 90)):
            mb.cyl(0.07, 0.07, 0.025, "glass_light", segs=14, grad=(0.6, 1.0))
            mb.cyl(0.055, 0.055, 0.03, look["coat"], pos=(0.03, 0.0, 0.002), segs=14)


# ---------------------------------------------------------------- lower body
def _boot(mb, look, x, tall):
    top = 1.0 if tall else 0.6
    with mb.at(T(x, 0, 0), R("Z", math.copysign(6, x))):
        _body(mb, [(0.06, 0.15, 0.17, 0.02), (0.3, 0.13, 0.145, 0.01), (top - 0.1, 0.145, 0.155), (top, 0.16, 0.17)],
              look["boots"], n=16, grad=(0.25, 0.6))
        mb.loft([_ring(0.17, 0.18, top - 0.02, 16), _ring(0.175, 0.185, top + 0.08, 16)], look["boots"], smooth=True, tone=0.1)    # cuff
        # foot: heel to toe, then sole and heel block
        sections = [(0.16, 0.12, 0.2), (0.02, 0.14, 0.24), (-0.22, 0.155, 0.19), (-0.42, 0.15, 0.14), (-0.56, 0.11, 0.1), (-0.6, 0.06, 0.07)]
        rings = []
        for y, w, h in sections:
            rings.append([(w * math.cos(TAU * i / 14), y, 0.035 + h * 0.5 + h * 0.5 * math.sin(TAU * i / 14)) for i in range(14)])
        mb.loft(rings, look["boots"], smooth=True, grad=(0.25, 0.6))
        mb.loft([[(-0.15, 0.17, 0.0), (0.15, 0.17, 0.0), (0.16, -0.45, 0.0), (0.08, -0.62, 0.0), (-0.08, -0.62, 0.0), (-0.16, -0.45, 0.0)],
                 [(-0.15, 0.17, 0.045), (0.15, 0.17, 0.045), (0.16, -0.45, 0.045), (0.08, -0.62, 0.045), (-0.08, -0.62, 0.045),
                  (-0.16, -0.45, 0.045)]], "wood_dark", tone=-0.15)
        mb.box(0.26, 0.2, 0.09, "wood_dark", pos=(0, 0.08, 0.0), tone=-0.2)
        if not tall:                                                       # laces
            for k in range(4):
                y = -0.06 - 0.09 * k
                mb.beam((-0.07, y, 0.26 - 0.03 * k), (0.07, y - 0.05, 0.26 - 0.03 * k), 0.012, 0.012, "wood_pale")
                mb.beam((0.07, y, 0.26 - 0.03 * k), (-0.07, y - 0.05, 0.26 - 0.03 * k), 0.012, 0.012, "wood_pale")
        else:                                                              # buckle strap
            mb.loft([_ring(0.152, 0.162, 0.52, 16), _ring(0.152, 0.162, 0.58, 16)], "wood_dark", smooth=True)
            mb.box(0.06, 0.02, 0.07, "brass", pos=(0.0, -0.165, 0.515))


def build_lower(mb, role):
    look = LOOK[role]
    tall = role in ("selma", "nyra", "esme")
    for side in (-1, 1):
        _boot(mb, look, side * 0.19, tall)
    if look["robe"]:
        # long skirt with folds that deepen towards the hem, a band at the hem
        def ripple(a, z):
            depth = 0.075 * _smooth((3.6 - z) / 3.2)
            return 1 + depth * math.sin(a * 9 + 0.6)
        sec = [(3.98, 0.47, 0.32), (3.7, 0.52, 0.37), (3.1, 0.6, 0.45), (2.2, 0.7, 0.55), (1.2, 0.8, 0.64), (0.42, 0.88, 0.72)]
        _body(mb, [s for s in reversed(sec)], look["coat"], n=36, ripple=ripple, grad=(0.25, 0.68))
        _body(mb, [(0.36, 0.9, 0.74), (0.5, 0.91, 0.75)], look["trim"], n=36, ripple=lambda a, z: ripple(a, 0.45))
        for side in (-1, 1):                                               # ankles inside the skirt
            _body(mb, [(0.9, 0.12, 0.13, 0, side * 0.19), (1.4, 0.13, 0.14, 0, side * 0.19)], look["pants"], n=12)
        if look["apron"]:                                                 # long apron over the skirt
            def skirt(z):
                pts = list(reversed(sec))
                for (z0, x0, y0), (z1, x1, y1) in zip(pts, pts[1:]):
                    if z <= z1:
                        t = _clamp((z - z0) / (z1 - z0))
                        return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                return pts[-1][1], pts[-1][2]

            def apron(u, f, out):
                z = 1.3 + (3.9 - 1.3) * f
                r_x, r_y = skirt(z)
                fold = 0.075 * _smooth((3.6 - z) / 3.2)                     # stays clear of the skirt's folds
                a = u * 0.95
                lift = fold * max(r_x, r_y) + (0.05 if out else 0.03)
                return Vector(((r_x + lift) * math.sin(a), -(r_y + lift) * math.cos(a), z))
            us = [-1 + 2 * k / 14 for k in range(15)]
            fs = [k / 12 for k in range(13)]
            _shell(mb, lambda u, f: apron(u, f, True), lambda u, f: apron(u, f, False), us, fs, look["apron"], grad=(0.35, 0.78))
    else:
        # hips and trousers
        _body(mb, [(2.82, 0.44, 0.28), (3.05, 0.48, 0.31), (3.4, 0.5, 0.32), (3.7, 0.49, 0.31), (3.95, 0.47, 0.3)], look["pants"], n=28, grad=(0.3, 0.6))
        for side in (-1, 1):
            x = side * 0.19
            top = 1.0 if role == "esme" else 0.6

            def crease(a, z):
                return 1 + 0.03 * math.sin(a * 5 + side) * _gauss((z - 1.75) / 0.25) + 0.02 * math.sin(a * 7) * _gauss((z - top - 0.15) / 0.12)
            _body(mb, [(top - 0.05, 0.14, 0.15, 0.0, x), (1.25, 0.165, 0.175, 0.02, x), (1.75, 0.17, 0.175, -0.01, x),
                       (2.4, 0.2, 0.21, 0.0, x * 1.05), (3.05, 0.23, 0.24, 0.0, x * 1.1), (3.3, 0.22, 0.23, 0.0, x * 1.05)],
                  look["pants"], n=18, ripple=crease, grad=(0.3, 0.62))
        if role == "esme":                                               # tunic skirt down to mid-thigh, slit at the side
            def ripple(a, z):
                return 1 + 0.04 * math.sin(a * 8) * _smooth((3.6 - z) / 1.1)
            _body(mb, [(2.45, 0.6, 0.42), (2.9, 0.56, 0.38), (3.5, 0.52, 0.34), (3.98, 0.48, 0.32)], look["coat"], n=32, ripple=ripple,
                  grad=(0.3, 0.68))
            _body(mb, [(2.42, 0.62, 0.44), (2.52, 0.62, 0.44)], look["trim"], n=32, ripple=lambda a, z: ripple(a, 2.45))
            with mb.at(T(-0.48, -0.12, 3.2), R("Y", 8)):                    # knife in a sheath
                mb.loft([[(-0.04, -0.02, 0), (0.04, -0.02, 0), (0.04, 0.02, 0), (-0.04, 0.02, 0)],
                         [(-0.02, -0.01, -0.45), (0.02, -0.01, -0.45), (0.02, 0.01, -0.45), (-0.02, 0.01, -0.45)]], "wood_dark")
                mb.box(0.06, 0.05, 0.16, "wood_mid", pos=(0, 0, 0.0))
                mb.box(0.12, 0.05, 0.03, "brass", pos=(0, 0, 0.16))
        if look["apron"]:                                                 # Aron: heavy apron down to the knees
            def apron(u, f, out):
                z = 1.65 + (3.9 - 1.65) * f
                a = u * 1.05
                r_x, r_y = 0.5, 0.33 + 0.08 * (1 - f)
                lift = 0.04 if out else 0.016
                return Vector(((r_x + lift) * math.sin(a), -(r_y + lift) * math.cos(a), z))
            us = [-1 + 2 * k / 14 for k in range(15)]
            fs = [k / 10 for k in range(11)]
            _shell(mb, lambda u, f: apron(u, f, True), lambda u, f: apron(u, f, False), us, fs, look["apron"], grad=(0.3, 0.6))
            for k in range(6):
                for side in (-1, 1):
                    q = apron(side * 0.98, k / 5, True)
                    mb.blob(0.02, "brass", pos=tuple(q), level=1, noise=0.0)


# ---------------------------------------------------------------- arms and hands
def build_upper(mb, role, side):
    look = LOOK[role]
    j = joints(role)["upper_l" if side > 0 else "upper_r"] / look["scale"]
    r = 0.165 * (1.12 if role == "aron" else 1.0) * (0.92 if look["female"] else 1.0)

    def fold(a, z):                                                         # folds above the elbow
        return 1 + 0.05 * math.sin(a * 6 + z * 20) * _gauss((z + UPPER_LEN - 0.12) / 0.12)
    with mb.at(T(*j)):
        # rounded shoulder (deltoid) and sleeve; Aron's sleeve is rolled up above the elbow
        bottom = -0.66 if role == "aron" else -UPPER_LEN - 0.05
        _body(mb, [(bottom, r * 0.9, r * 0.92), (-0.45, r * 1.0, r * 1.0), (-0.25, r * 1.1, r * 1.05),
                   (-0.05, r * 1.14, r * 1.08), (0.08, r * 1.02, r * 0.96), (0.15, r * 0.6, r * 0.6), (0.17, r * 0.1, r * 0.1)],
              look["coat"], n=18, ripple=None if role == "aron" else fold, grad=(0.3, 0.72))
        if role == "aron":
            _body(mb, [(-0.74, r * 1.12, r * 1.12), (-0.58, r * 1.14, r * 1.14)], look["coat"], n=18, tone=0.08)   # the roll
            _body(mb, [(-UPPER_LEN - 0.05, r * 0.78, r * 0.8), (-0.62, r * 0.86, r * 0.88)], look["skin"], n=16, grad=(0.42, 0.6))


# centre of the closed fist (hand space, left hand; mirrored in x for the right): the fingers bend
# 60 / 85 / 70 degrees and close around this point - worked out from the finger lengths below
GRIP = Vector((-0.1, 0.0, -0.34))
TOOL_SCALE = {"_sprig": 0.55, "_basket": 0.72, "_crystal": 0.6, "_lantern": 0.68, "_vial": 0.52, "_cloth": 0.55,
              "_hammer": 0.8, "_ore": 0.55, "_axe": 0.82, "_rule": 0.7}


def _finger(mb, skin, base, lengths, radius, curls, side, nail=True):
    """A finger hanging along -Z from `base`, bending towards the palm by `curls` (degrees per joint)."""
    m = Matrix.Translation(base)
    pts, radii = [Vector(base)], [radius * 1.05]
    r = radius
    for i, (ln, cv) in enumerate(zip(lengths, curls)):
        m = m @ R("Y", side * cv)
        tip = m @ Vector((0, 0, -ln))
        pts.append(tip)
        r *= 0.88
        radii.append(r)
        m = Matrix.Translation(tip) @ m.to_3x3().to_4x4()
    _tube(mb, [tuple(p) for p in pts], radii, skin, n=8, grad=(0.45, 0.6))
    mb.blob(radii[-1] * 1.02, skin, pos=tuple(pts[-1]), level=1, noise=0.0, smooth=True)
    if nail:                                                                 # nail on the back of the last joint
        d = (pts[-1] - pts[-2]).normalized()
        back = m.to_3x3() @ Vector((side, 0, 0))
        q = pts[-1] - d * 0.03 + back * radii[-1] * 0.8
        mb.blob(radii[-1] * 0.75, "plaster_cream", pos=tuple(q), scale=(0.5, 0.8, 1.0), level=0, noise=0.0)


def _hand(mb, look, side, grip):
    """Hand hanging from the wrist (origin) along -Z, palm towards the body (-side * X), thumb to the front (-Y)."""
    skin = look["skin"]
    k = 1.0 if not look["female"] else 0.92
    # palm: a rounded block from the wrist to the knuckles
    _body(mb, [(0.02, 0.055 * k, 0.12 * k, 0.0, 0.0), (-0.1 * k, 0.06 * k, 0.15 * k, 0.0, -side * 0.005),
               (-0.25 * k, 0.058 * k, 0.17 * k, 0.0, -side * 0.01), (-0.34 * k, 0.05 * k, 0.165 * k, 0.0, -side * 0.012)],
          skin, n=12, p=2.6, grad=(0.45, 0.62))
    ys = [-0.12, -0.04, 0.04, 0.12]
    lens = [(0.13, 0.08, 0.07), (0.14, 0.09, 0.075), (0.135, 0.085, 0.07), (0.1, 0.065, 0.06)]
    for i, y in enumerate(ys):
        base = Vector((-side * 0.008, y * k, -0.33 * k))
        mb.blob(0.034 * k, skin, pos=tuple(base + Vector((side * 0.025, 0, 0.0))), level=1, noise=0.0, smooth=True)   # knuckle
        ls = [l * k for l in lens[i]]
        if grip:
            _finger(mb, skin, base, ls, 0.032 * k, (60, 85, 70), side)
        else:
            _finger(mb, skin, base, ls, 0.032 * k, (8 + 3 * i, 14, 10), side)
    # thumb: from the base of the palm, forward and down, towards the palm side
    tb = Vector((-side * 0.02, -0.12 * k, -0.08 * k))
    if grip:
        _finger(mb, skin, tb, [0.12 * k, 0.09 * k, 0.07 * k], 0.04 * k, (35, 40, 30), side)
    else:
        m = Matrix.Translation(tb) @ R("X", -25) @ R("Y", side * 18)
        pts = [m @ Vector((0, 0, 0)), m @ Vector((0, 0, -0.12 * k)), m @ Vector((0.0, -0.02, -0.21 * k)), m @ Vector((0, -0.03, -0.28 * k))]
        _tube(mb, [tuple(p) for p in pts], [0.042 * k, 0.037 * k, 0.032 * k, 0.026 * k], skin, n=8, grad=(0.45, 0.6))
        mb.blob(0.026 * k, skin, pos=tuple(pts[-1]), level=1, noise=0.0, smooth=True)


def build_fore(mb, role, side):
    look = LOOK[role]
    tag = "fore_l" if side > 0 else "fore_r"
    j = joints(role)[tag] / look["scale"]
    r = 0.13 * (1.12 if role == "aron" else 1.0) * (0.9 if look["female"] else 1.0)
    held = HELD[role][tag]
    with mb.at(T(*j)):
        if role == "aron":                                                   # bare forearm
            _body(mb, [(-FORE_LEN - 0.02, r * 0.55, r * 0.62), (-FORE_LEN * 0.6, r * 0.85, r * 0.9), (-0.15, r * 1.02, r * 1.05),
                       (0.06, r * 1.0, r * 1.0)], look["skin"], n=16, grad=(0.42, 0.62))
        else:
            def fold(a, z):
                return 1 + 0.045 * math.sin(a * 5 + z * 14) * _gauss((z + 0.12) / 0.14)
            _body(mb, [(-FORE_LEN + 0.12, r * 0.85, r * 0.88), (-0.45, r * 0.95, r * 0.98), (-0.05, r * 1.05, r * 1.05), (0.08, r * 0.95, r * 0.95)],
                  look["coat"], n=16, ripple=fold, grad=(0.3, 0.72))
            _body(mb, [(-FORE_LEN + 0.05, r * 0.95, r * 0.98), (-FORE_LEN + 0.16, r * 0.96, r * 0.99)], look["trim"], n=16)      # cuff
            _body(mb, [(-FORE_LEN - 0.02, r * 0.5, r * 0.58), (-FORE_LEN + 0.08, r * 0.6, r * 0.68)], look["skin"], n=12)        # wrist
        with mb.at(T(0, 0, -FORE_LEN)):
            _hand(mb, look, side, grip=held is not None)
            if held:
                with mb.at(T(side * GRIP.x, GRIP.y, GRIP.z), S(TOOL_SCALE.get(held.__name__, 0.75))):
                    held(mb, side)


# ---------------------------------------------------------------- things in the hands
# Modelled around the grip point; the handle runs along Y (front - back in the rest pose).  With the
# forearm raised forwards the handle stands upright.
def _sprig(mb, side):
    mb.beam((0, 0.3, 0), (0, -1.0, 0), 0.07, 0.07, "leaf_dark")
    for i in range(6):
        s = 1 if i % 2 else -1
        with mb.at(T(s * 0.12, -0.3 - i * 0.13, 0.04 * s), R("Y", s * 25), R("X", 20)):
            mb.blob(0.17, ("leaf_lime", "leaf_green")[i % 2], scale=(1.2, 1.0, 0.4), level=0, noise=0.1, grad=(0.35, 0.9))
    for i in range(3):
        mb.blob(0.07, "flower_white", pos=(0.05 * (i - 1), -1.02 - 0.05 * i, 0.03 * i), level=0, noise=0.0)


HANG = 76           # degrees: typical forward angle of a forearm that carries something hanging


def _basket(mb, side):
    """Herb basket on a bow.  The fist holds the bow; the basket hangs straight down while the
    forearm points forwards (it is turned by HANG against the forearm)."""
    with mb.at(R("X", HANG)):
        mb.beam((-0.36, 0, 0), (0.36, 0, 0), 0.07, 0.07, "wood_mid")
        for sx in (-1, 1):
            mb.beam((sx * 0.36, 0, 0), (sx * 0.46, 0, -0.5), 0.07, 0.07, "wood_mid")
        with mb.at(T(0, 0, -0.98)):
            mb.lathe([(0.0, 0.0), (0.4, 0.0), (0.54, 0.5), (0.47, 0.5), (0.36, 0.08)], "thatch", segs=10, smooth=False,
                     grad=(0.3, 0.8))
            mb.lathe([(0.5, 0.42), (0.56, 0.44), (0.56, 0.54), (0.5, 0.56)], "thatch_dark", segs=10, smooth=False)
            for i in range(5):
                a = i * 1.26
                mb.blob(0.17, ("leaf_lime", "leaf_green", "leaf_teal")[i % 3], pos=(0.2 * math.cos(a), 0.2 * math.sin(a), 0.56),
                        scale=(1.2, 1.2, 0.6), level=0, noise=0.15, grad=(0.35, 0.9))
            mb.blob(0.09, "flower_red", pos=(0.1, -0.2, 0.66), level=0, noise=0.0)


def _crystal(mb, side):
    with mb.at(R("X", 90)):
        mb.lathe([(0.0, -0.2), (0.11, -0.1), (0.15, 0.4), (0.1, 0.74), (0.0, 0.9)], "glass_light", segs=5, smooth=False,
                 grad=(0.3, 1.0))
        mb.lathe([(0.0, 0.2), (0.07, 0.3), (0.06, 0.52), (0.0, 0.62)], "flower_purple", segs=4, smooth=False, pos=(0.12, 0.02, 0))


def _lantern(mb, side):
    """Lantern on a ring, hangs below the fist (turned by HANG like the basket)."""
    with mb.at(R("X", HANG)):
        mb.beam((-0.26, 0, 0), (0.26, 0, 0), 0.06, 0.06, "iron")
        mb.box(0.05, 0.05, 0.3, "iron", pos=(0, 0, -0.34))
        mb.lathe([(0.0, -0.3), (0.3, -0.42), (0.34, -0.48), (0.0, -0.48)], "iron", segs=6, smooth=False)
        mb.box(0.42, 0.42, 0.52, "glass_lit", pos=(0, 0, -1.0), grad=(0.6, 1.0))
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box(0.06, 0.06, 0.56, "iron", pos=(sx * 0.21, sy * 0.21, -1.02))
        mb.box(0.54, 0.54, 0.08, "iron", pos=(0, 0, -1.08))


def _vial(mb, side):
    with mb.at(R("X", 90)):
        # the lower half is the glowing potion, the upper half clear glass; cork on top
        mb.lathe([(0.0, -0.22), (0.2, -0.2), (0.24, 0.0), (0.23, 0.1), (0.0, 0.1)], "glass_lit", segs=8, smooth=True, grad=(0.55, 1.0))
        mb.lathe([(0.0, 0.1), (0.23, 0.1), (0.2, 0.26), (0.08, 0.4), (0.08, 0.62), (0.11, 0.66), (0.0, 0.66)], "glass_light",
                 segs=8, smooth=True, grad=(0.4, 1.0))
        mb.cyl(0.085, 0.07, 0.14, "wood_pale", pos=(0, 0, 0.64), segs=6)


def _cloth(mb, side):
    mb.blob(0.24, "cloth_white", pos=(0, -0.05, -0.02), scale=(1.0, 1.3, 0.7), level=1, noise=0.12, grad=(0.5, 0.95))
    mb.blob(0.16, "cloth_white", pos=(0.05, -0.3, -0.16), scale=(0.8, 1.0, 1.2), level=0, noise=0.15, grad=(0.5, 0.95))


def _hammer(mb, side):
    mb.beam((0, 0.3, 0), (0, -0.95, 0), 0.1, 0.1, "wood_light")
    mb.box(0.3, 0.36, 0.62, "iron", pos=(0, -1.0, 0), anchor="c", grad=(0.3, 0.7))
    mb.box(0.34, 0.4, 0.1, "brass", pos=(0, -1.0, 0), anchor="c")
    mb.box(0.12, 0.08, 0.12, "iron", pos=(0, 0.32, 0), anchor="c")


def _ore(mb, side):
    # a lump of ore that sticks out of the fist towards the front (up, once the forearm is raised)
    mb.blob(0.34, "rock_dark", pos=(0, -0.32, 0.02), scale=(1.0, 1.1, 0.9), level=1, noise=0.22, grad=(0.25, 0.75))
    for i in range(5):
        a = i * 1.3
        mb.blob(0.11, "roof_orange", pos=(0.24 * math.cos(a), -0.42 - 0.1 * (i % 2), 0.02 + 0.24 * math.sin(a)), level=0, noise=0.3,
                grad=(0.4, 0.95))


def _axe(mb, side):
    mb.beam((0, 0.42, 0), (0, -1.25, 0), 0.1, 0.11, "wood_light")
    with mb.at(T(0, -1.12, 0)):
        mb.loft([[(-0.04, -0.14, -0.06), (0.04, -0.14, -0.06), (0.04, 0.14, -0.06), (-0.04, 0.14, -0.06)],
                 [(-0.02, -0.3, -0.56), (0.02, -0.3, -0.56), (0.02, 0.3, -0.56), (-0.02, 0.3, -0.56)]], "iron", grad=(0.3, 0.85))
        mb.box(0.14, 0.3, 0.16, "iron", pos=(0, 0, 0), anchor="c")


def _rule(mb, side):
    """Folding rule, half opened."""
    mb.beam((0, 0.2, 0), (0, -0.9, 0), 0.05, 0.14, "wood_pale")
    with mb.at(T(0, -0.9, 0), R("X", -62)):
        mb.beam((0, 0, 0), (0, -0.9, 0), 0.05, 0.14, "wood_pale")
        for i in range(4):
            mb.box(0.06, 0.03, 0.15, "wood_dark", pos=(0, -0.15 - i * 0.2, 0), anchor="c")
    for i in range(4):
        mb.box(0.06, 0.03, 0.15, "wood_dark", pos=(0, -0.1 - i * 0.2, 0), anchor="c")
    mb.blob(0.06, "brass", pos=(0, -0.9, 0), level=0, noise=0.0)


HELD = {
    "selma": {"fore_r": _sprig, "fore_l": _basket},
    "nyra": {"fore_r": _crystal, "fore_l": _lantern},
    "lio": {"fore_r": _vial, "fore_l": _cloth},
    "aron": {"fore_r": _hammer, "fore_l": _ore},
    "esme": {"fore_r": _axe, "fore_l": _rule},
}

BUILDERS = {
    "lower": lambda mb, role: build_lower(mb, role),
    "torso": lambda mb, role: build_torso(mb, role),
    "head": lambda mb, role: build_head(mb, role),
    "upper_l": lambda mb, role: build_upper(mb, role, 1),
    "upper_r": lambda mb, role: build_upper(mb, role, -1),
    "fore_l": lambda mb, role: build_fore(mb, role, 1),
    "fore_r": lambda mb, role: build_fore(mb, role, -1),
}


# ---------------------------------------------------------------- idle loops
# Joint angles in degrees (Blender axes, figure faces -Y):
#   torso / head: (rx = nod forwards +, ry = tilt to the figure's left -, rz = turn to the figure's left +)
#   upper arm:    (rx = swing forwards -, ry = lift sideways: left arm -, right arm +,
#                  rz = turn the raised forearm inwards: left arm -, right arm +)
#   forearm:      (rx = bend forwards -, ry, rz = twist)
# Keys are (time in seconds, value); values between keys are eased, the last key equals the first.
REST = dict(torso=(0, 0, 0), head=(0, 0, 0), upper_l=(0, -6, 0), fore_l=(-8, 0, 0), upper_r=(0, 6, 0), fore_r=(-8, 0, 0))

LOOPS = {
    # Selma smells at the sprig, nods, lays it towards the basket and looks up at the customers.
    "selma": dict(duration=8.0, keys={
        "upper_l": [(0, (-18, -10, 0)), (4, (-22, -12, 0)), (6, (-28, -8, -10)), (8, (-18, -10, 0))],
        "fore_l": [(0, (-78, 0, 0)), (4, (-74, 0, 0)), (6, (-82, 0, 0)), (8, (-78, 0, 0))],
        "upper_r": [(0, (-30, 12, 0)), (1.6, (-50, 6, 30)), (3.4, (-50, 6, 30)), (5.2, (-30, 4, 46)), (6.4, (-30, 4, 46)), (8, (-30, 12, 0))],
        "fore_r": [(0, (-66, 0, 0)), (1.6, (-112, 0, 0)), (3.4, (-108, 0, 0)), (5.2, (-58, 0, 0)), (6.4, (-54, 0, 0)), (8, (-66, 0, 0))],
        "head": [(0, (0, 0, 8)), (1.6, (14, 0, -6)), (3.4, (16, 2, -6)), (4.4, (-4, 0, -4)), (5.4, (12, -4, 16)), (6.6, (-2, 0, 18)), (8, (0, 0, 8))],
        "torso": [(0, (0, 0, 2)), (2.4, (4, 0, -3)), (5.4, (2, 0, 6)), (8, (0, 0, 2))],
    }),
    # Nyra lifts the lantern, holds the crystal into its light and turns it.
    "nyra": dict(duration=7.0, keys={
        "upper_l": [(0, (-30, -8, 0)), (2, (-56, -10, -16)), (5, (-56, -10, -16)), (7, (-30, -8, 0))],
        "fore_l": [(0, (-64, 0, 0)), (2, (-72, 0, 0)), (5, (-70, 0, 0)), (7, (-64, 0, 0))],
        "upper_r": [(0, (-26, 10, 0)), (2.2, (-56, 8, 22)), (5.2, (-56, 8, 22)), (7, (-26, 10, 0))],
        "fore_r": [(0, (-76, 0, 0)), (2.2, (-98, 0, -45)), (3.2, (-98, 0, 40)), (4.2, (-98, 0, -45)), (5.2, (-98, 0, 30)), (7, (-76, 0, 0))],
        "head": [(0, (2, 0, -6)), (2.2, (8, -6, 4)), (3.7, (10, 6, 2)), (5.2, (8, -4, 4)), (7, (2, 0, -6))],
        "torso": [(0, (0, 0, 0)), (3.5, (3, 0, 3)), (7, (0, 0, 0))],
    }),
    # Lio rubs the vial with the cloth, then holds it up against the light and looks at it.
    "lio": dict(duration=6.5, keys={
        "upper_l": [(0, (-34, -6, -10)), (0.5, (-40, -4, -14)), (1.0, (-32, -8, -8)), (1.5, (-40, -4, -14)), (2.0, (-32, -8, -8)), (3.4, (-20, -10, -2)), (5.4, (-20, -10, -2)), (6.5, (-34, -6, -10))],
        "fore_l": [(0, (-92, 0, 0)), (0.5, (-100, 0, 0)), (1.0, (-88, 0, 0)), (1.5, (-100, 0, 0)), (2.0, (-88, 0, 0)), (3.4, (-66, 0, 0)), (5.4, (-66, 0, 0)), (6.5, (-92, 0, 0))],
        "upper_r": [(0, (-30, 6, 10)), (2.0, (-30, 6, 10)), (3.6, (-62, 26, 6)), (5.2, (-62, 26, 6)), (6.5, (-30, 6, 10))],
        "fore_r": [(0, (-86, 0, 0)), (2.0, (-86, 0, 0)), (3.6, (-92, 0, 26)), (4.4, (-92, 0, -26)), (5.2, (-92, 0, 26)), (6.5, (-86, 0, 0))],
        "head": [(0, (14, 0, 0)), (2.0, (14, 0, 0)), (3.6, (-14, 6, -22)), (5.2, (-14, 6, -22)), (6.5, (14, 0, 0))],
        "torso": [(0, (4, 0, 0)), (3.6, (-2, 0, -6)), (5.2, (-2, 0, -6)), (6.5, (4, 0, 0))],
    }),
    # Aron weighs the ore in his hand and taps it twice with the hammer.
    "aron": dict(duration=6.0, keys={
        "upper_l": [(0, (-34, -6, -18)), (3.0, (-36, -6, -18)), (4.4, (-50, -8, -8)), (6, (-34, -6, -18))],
        "fore_l": [(0, (-84, 0, 0)), (1.5, (-80, 0, 0)), (1.7, (-76, 0, 0)), (2.1, (-80, 0, 0)), (2.3, (-76, 0, 0)), (3.0, (-84, 0, 0)), (4.4, (-98, 0, 0)), (6, (-84, 0, 0))],
        "upper_r": [(0, (-22, 14, 6)), (1.1, (-36, 10, 26)), (1.5, (-26, 6, 32)), (1.9, (-34, 10, 28)), (2.1, (-26, 6, 32)), (3.0, (-22, 16, 6)), (6, (-22, 14, 6))],
        "fore_r": [(0, (-62, 0, 0)), (1.1, (-96, 0, 0)), (1.5, (-58, 0, 0)), (1.9, (-92, 0, 0)), (2.1, (-58, 0, 0)), (3.0, (-64, 0, 0)), (6, (-62, 0, 0))],
        "head": [(0, (4, 0, 6)), (1.2, (16, 0, -2)), (2.4, (16, 0, -2)), (3.4, (2, 0, 4)), (4.4, (10, -4, 10)), (5.2, (2, 0, 8)), (6, (4, 0, 6))],
        "torso": [(0, (0, 0, 0)), (1.2, (5, 0, -2)), (2.4, (5, 0, -2)), (4.4, (0, 0, 4)), (6, (0, 0, 0))],
    }),
    # Esme rests the axe on her shoulder and sights along the folding rule.
    "esme": dict(duration=8.0, keys={
        "upper_r": [(0, (-14, 18, 0)), (2, (-18, 20, 0)), (4, (-14, 18, 0)), (6, (-20, 20, 0)), (8, (-14, 18, 0))],
        "fore_r": [(0, (-116, 0, 0)), (2, (-110, 0, 0)), (4, (-116, 0, 0)), (6, (-108, 0, 0)), (8, (-116, 0, 0))],
        "upper_l": [(0, (-24, -8, 0)), (2.2, (-74, -22, 14)), (3.4, (-74, -34, 30)), (4.6, (-74, -22, 14)), (5.6, (-74, -22, 14)), (8, (-24, -8, 0))],
        "fore_l": [(0, (-62, 0, 0)), (2.2, (-40, 0, 0)), (3.4, (-30, 0, 0)), (4.6, (-40, 0, 0)), (5.6, (-46, 0, 0)), (8, (-62, 0, 0))],
        "head": [(0, (0, 0, -8)), (2.2, (4, 0, 14)), (3.4, (4, 0, 28)), (4.6, (4, 0, 14)), (5.6, (8, 4, 12)), (6.8, (-2, 0, -4)), (8, (0, 0, -8))],
        "torso": [(0, (0, 0, -2)), (3.4, (2, 0, 6)), (5.6, (2, 0, 4)), (8, (0, 0, -2))],
    }),
}


def _ease(u):
    return u * u * (3 - 2 * u)


def angles(role, part, t):
    """Eased joint angles of a part at time t (seconds)."""
    loop = LOOPS[role]
    keys = loop["keys"].get(part)
    if not keys:
        return REST.get(part, (0, 0, 0))
    t = t % loop["duration"]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = _ease((t - t0) / (t1 - t0)) if t1 > t0 else 0.0
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))
    return keys[-1][1]


def _rot(a):
    return R("Z", a[2]) @ R("Y", a[1]) @ R("X", a[0])


def pose_frames(role, t=None):
    """Joint frame (4x4, figure space) of every part.  t = None gives the rest pose the meshes are built in."""
    j = joints(role)
    if t is None:
        return {p: T(*j[p]) for p in PARTS}
    out = {"lower": T(*j["lower"])}
    breathe = 0.02 * math.sin(TAU * t / 3.2)                    # slow rise of the chest
    out["torso"] = T(*j["torso"]) @ T(0, 0, breathe) @ _rot(angles(role, "torso", t))
    out["head"] = out["torso"] @ T(*(j["head"] - j["torso"])) @ _rot(angles(role, "head", t))
    for tag in ("l", "r"):
        up = out["torso"] @ T(*(j["upper_" + tag] - j["torso"])) @ _rot(angles(role, "upper_" + tag, t))
        out["upper_" + tag] = up
        out["fore_" + tag] = up @ T(*(j["fore_" + tag] - j["upper_" + tag])) @ _rot(angles(role, "fore_" + tag, t))
    return out


def build_part(mb, role, part, t=None):
    """Adds one part to the builder: in the rest pose (t = None) or posed at loop time t.  The parts
    are modelled for the nominal figure and scaled to the trader's height here."""
    scale = S(LOOK[role]["scale"])
    if t is None:
        with mb.at(scale):
            BUILDERS[part](mb, role)
        return
    frame = pose_frames(role, t)[part] @ pose_frames(role)[part].inverted()
    with mb.at(frame, scale):
        BUILDERS[part](mb, role)


def build_figure(mb, role, t=0.0):
    """Whole trader as one mesh, posed at loop time t (preview renders)."""
    for part in PARTS:
        build_part(mb, role, part, t)
