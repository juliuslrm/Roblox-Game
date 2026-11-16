"""The five market traders as jointed figures in the style of the village.

Each trader consists of seven rigid parts that turn in ball joints (no skinning):

    lower   legs, boots, skirt of the coat            fixed
    torso   chest, apron, belt, neck                   turns at the waist
    head    face, hair, hat                            turns at the neck
    upper_l / upper_r   upper arm with shoulder ball   turns at the shoulder
    fore_l / fore_r     forearm, hand, tool            turns at the elbow

"l" is the figure's left arm (Blender +X; the figure faces -Y), "r" its right arm.
All parts are modelled in the rest pose (arms hanging) in the figure's own space: origin at the
ground between the feet, 1 unit = 1 stud.  `pose_frames` gives the joint frame of every part for a
moment of the idle loop; a part's vertices move with  frame(t) * frame_rest^-1.

The loops are plain forward kinematics from a few keyed joint angles, eased and closed, so they
play identically in Blender (preview renders) and in Roblox (sampled into MerchantMotion.lua).
"""
import math

from mathutils import Matrix, Vector

from .meshkit import R, S, T

PARTS = ("lower", "torso", "head", "upper_l", "fore_l", "upper_r", "fore_r")
ROLES = ("selma", "nyra", "lio", "aron", "esme")

# joint positions in the rest pose
WAIST = Vector((0.0, 0.0, 2.72))
NECK = Vector((0.0, 0.0, 4.62))
SHOULDER_X, SHOULDER_Z = 0.93, 4.1
UPPER_LEN, FORE_LEN = 1.02, 0.92


def joints(role):
    w = LOOK[role]["width"]
    sx = SHOULDER_X * w
    out = {"lower": Vector((0, 0, 0)), "torso": WAIST.copy(), "head": NECK.copy()}
    for side, tag in ((1, "l"), (-1, "r")):
        out["upper_" + tag] = Vector((side * sx, 0.0, SHOULDER_Z))
        out["fore_" + tag] = Vector((side * sx, 0.0, SHOULDER_Z - UPPER_LEN))
    return out


LOOK = {
    #          coat            trim          apron          skin             hair         width  robe
    "selma": dict(coat="cloth_green", trim="pine", apron="plaster_cream", skin="plaster_peach", hair="roof_orange",
                  width=1.0, robe=True, boots="wood_dark"),
    "nyra": dict(coat="roof_purple", trim="roof_slate", apron=None, skin="plaster_rose", hair="plaster_white",
                 width=0.96, robe=True, boots="iron"),
    "lio": dict(coat="cloth_blue", trim="roof_teal", apron="wood_mid", skin="wood_pale", hair="wood_dark",
                width=0.98, robe=False, boots="wood_dark"),
    "aron": dict(coat="roof_red", trim="iron", apron="wood_red", skin="plaster_peach", hair="wood_dark",
                 width=1.16, robe=False, boots="iron"),
    "esme": dict(coat="roof_teal", trim="leaf_dark", apron=None, skin="plaster_peach", hair="brick",
                 width=1.0, robe=False, boots="wood_red"),
}


# ---------------------------------------------------------------- small helpers
def _ring(rx, ry, z, n=10, cx=0.0, cy=0.0):
    return [(cx + rx * math.cos(TAU * i / n), cy + ry * math.sin(TAU * i / n), z) for i in range(n)]


TAU = 2 * math.pi


def _body(mb, sections, color, n=10, **kw):
    """Smooth body from elliptical sections [(z, rx, ry[, cy])]."""
    rings = [_ring(s[1], s[2], s[0], n, cy=(s[3] if len(s) > 3 else 0.0)) for s in sections]
    mb.loft(rings, color, smooth=True, **kw)


def _ball(mb, r, pos, color, scale=(1, 1, 1), **kw):
    mb.blob(r, color, pos=pos, scale=scale, level=1, noise=0.0, smooth=True, **kw)


# ---------------------------------------------------------------- lower body
def _legs(mb, role):
    look = LOOK[role]
    w = look["width"]
    pants = "roof_slate" if role in ("aron", "lio") else look["trim"]
    for side in (-1, 1):
        with mb.at(T(side * 0.34 * w, 0, 0)):
            _body(mb, [(0.42, 0.29, 0.3), (1.4, 0.31, 0.32), (2.3, 0.37, 0.37), (2.8, 0.38, 0.36)], pants, n=8, grad=(0.3, 0.7))
            # boot: shaft, rounded toe cap pointing forward (-Y), sole
            _body(mb, [(0.1, 0.33, 0.36), (0.55, 0.34, 0.35), (0.98, 0.36, 0.36)], look["boots"], n=8, grad=(0.3, 0.75))
            _ball(mb, 0.36, (0, -0.3, 0.27), look["boots"], scale=(0.95, 1.25, 0.72), grad=(0.3, 0.75))
            mb.box(0.72, 1.12, 0.1, "wood_dark", pos=(0, -0.2, 0.0))
            mb.box(0.74, 0.1, 0.14, "brass" if role != "nyra" else "glass_light", pos=(0, -0.34, 0.86))   # cuff strap


def build_lower(mb, role):
    look = LOOK[role]
    w = look["width"]
    _legs(mb, role)
    if look["robe"]:                                             # long skirt of the coat, open over the boots
        _body(mb, [(0.62, 1.0 * w, 0.82), (1.5, 0.9 * w, 0.72), (2.4, 0.76 * w, 0.58), (2.86, 0.74 * w, 0.55)],
              look["coat"], n=12, grad=(0.28, 0.72))
        mb.loft([_ring(1.02 * w, 0.84, 0.56, 12), _ring(1.02 * w, 0.84, 0.74, 12)], look["trim"], smooth=True)
    else:                                                        # short coat tail
        _body(mb, [(1.95, 0.84 * w, 0.62), (2.4, 0.78 * w, 0.58), (2.86, 0.74 * w, 0.55)], look["coat"], n=12,
              grad=(0.3, 0.72))
        mb.loft([_ring(0.86 * w, 0.64, 1.9, 12), _ring(0.86 * w, 0.64, 2.04, 12)], look["trim"], smooth=True)
    if look["apron"]:                                            # lower half of the apron
        z0 = 0.95 if look["robe"] else 1.55
        mb.loft([[(-0.5 * w, -0.86, z0), (0.5 * w, -0.86, z0), (0.56 * w, -0.5, z0), (-0.56 * w, -0.5, z0)],
                 [(-0.46 * w, -0.6, 2.84), (0.46 * w, -0.6, 2.84), (0.5 * w, -0.4, 2.84), (-0.5 * w, -0.4, 2.84)]],
                look["apron"], grad=(0.35, 0.8))


# ---------------------------------------------------------------- torso
def build_torso(mb, role):
    look = LOOK[role]
    w = look["width"]
    _body(mb, [(2.6, 0.72 * w, 0.54), (3.1, 0.74 * w, 0.55), (3.75, 0.84 * w, 0.58), (4.12, 0.8 * w, 0.54),
               (4.38, 0.5 * w, 0.4), (4.52, 0.27, 0.27)], look["coat"], n=12, grad=(0.3, 0.78))
    _body(mb, [(4.44, 0.24, 0.24), (4.84, 0.23, 0.23)], look["skin"], n=8)                       # neck
    mb.loft([_ring(0.31, 0.3, 4.4, 10), _ring(0.4, 0.38, 4.56, 10)], look["trim"], smooth=True)      # collar
    mb.loft([_ring(0.76 * w, 0.58, 2.74, 12), _ring(0.76 * w, 0.58, 2.98, 12)], "wood_dark", smooth=True)   # belt
    mb.box(0.3, 0.1, 0.3, "brass", pos=(0, -0.6, 2.71))                                              # buckle
    if look["apron"]:                                                                                # bib of the apron
        mb.loft([[(-0.46 * w, -0.62, 2.84), (0.46 * w, -0.62, 2.84), (0.5 * w, -0.42, 2.84), (-0.5 * w, -0.42, 2.84)],
                 [(-0.4 * w, -0.66, 3.95), (0.4 * w, -0.66, 3.95), (0.44 * w, -0.46, 3.95), (-0.44 * w, -0.46, 3.95)]],
                look["apron"], grad=(0.35, 0.8))
        for side in (-1, 1):                                                                         # straps
            mb.beam((side * 0.36 * w, -0.6, 3.9), (side * 0.3 * w, -0.1, 4.42), 0.14, 0.08, look["apron"])
    else:
        for i in range(3):                                                                           # coat buttons
            mb.blob(0.08, "brass", pos=(0, -0.59, 3.2 + i * 0.36), level=0, noise=0.0)
    if role == "selma":                                                                              # seed pouch on the belt
        _ball(mb, 0.26, (0.55, -0.42, 2.6), "wood_mid", scale=(1, 0.7, 1.1))
        mb.box(0.36, 0.1, 0.16, "wood_dark", pos=(0.55, -0.56, 2.74))
    elif role == "nyra":                                                                             # moon brooch, cloak clasp
        mb.cyl(0.17, 0.17, 0.06, "glass_light", pos=(0, -0.44, 4.28), segs=8, grad=(0.6, 1.0))
        with mb.at(T(0, -0.42, 4.28), R("X", 90)):
            mb.cyl(0.17, 0.17, 0.07, "glass_light", segs=8, grad=(0.6, 1.0))
            mb.cyl(0.13, 0.13, 0.08, "roof_purple", pos=(0.07, 0.03, 0.0), segs=8)
    elif role == "lio":                                                                              # vials in the apron pocket
        mb.box(0.72, 0.12, 0.36, "wood_dark", pos=(0, -0.7, 3.05))
        for i in range(3):
            mb.cyl(0.07, 0.07, 0.34, ("glass_light", "glass_blue", "glass_lit")[i], pos=(-0.22 + i * 0.22, -0.72, 3.3), segs=6)
    elif role == "aron":                                                                             # rivets on the leather apron
        for sx in (-1, 1):
            mb.blob(0.07, "brass", pos=(sx * 0.34 * w, -0.68, 3.82), level=0, noise=0.0)
    elif role == "esme":                                                                             # shoulder cape and strap
        _body(mb, [(3.86, 0.9, 0.62), (4.2, 0.84, 0.58), (4.42, 0.5, 0.42)], look["trim"], n=12, grad=(0.3, 0.75))
        mb.beam((-0.62, -0.5, 4.2), (0.6, -0.56, 2.95), 0.16, 0.07, "wood_mid")


# ---------------------------------------------------------------- head and face
HEAD_C = Vector((0.0, 0.0, 5.52))
HEAD_R = (0.7, 0.68, 0.78)          # half extents of the skull


def _face_y(x, z):
    """Front surface (-Y) of the head ellipsoid at x, z."""
    u = 1.0 - (x / HEAD_R[0]) ** 2 - ((z - HEAD_C.z) / HEAD_R[2]) ** 2
    return HEAD_C.y - HEAD_R[1] * math.sqrt(max(u, 0.02))


def _on_face(mb, x, z, lift=0.0):
    """Transform whose local XZ plane is tangent to the face at x, z; local -Y points outwards."""
    y = _face_y(x, z) - lift
    nx = x / HEAD_R[0] ** 2
    nz = (z - HEAD_C.z) / HEAD_R[2] ** 2
    ny = (y - HEAD_C.y) / HEAD_R[1] ** 2
    yaw = math.degrees(math.atan2(nx, -ny))
    pitch = math.degrees(math.atan2(nz, math.hypot(nx, ny)))
    return mb.at(T(x, y, z), R("Z", yaw), R("X", -pitch))


FACE = {
    # eye size, eye spread, brow tilt (deg, + = friendly), brow height, mouth width, smile, nose size, cheeks
    "selma": dict(eye=0.135, spread=0.27, brow=8, brow_z=0.21, mouth=0.2, smile=1.0, nose=0.1, cheeks="plaster_rose",
                  iris="leaf_dark", lips="roof_red"),
    "nyra": dict(eye=0.125, spread=0.26, brow=-6, brow_z=0.2, mouth=0.15, smile=0.35, nose=0.085, cheeks=None,
                 iris="roof_purple", lips="roof_purple"),
    "lio": dict(eye=0.14, spread=0.28, brow=12, brow_z=0.23, mouth=0.21, smile=1.2, nose=0.105, cheeks="plaster_peach",
                iris="roof_teal", lips="brick"),
    "aron": dict(eye=0.12, spread=0.29, brow=-12, brow_z=0.19, mouth=0.17, smile=0.5, nose=0.14, cheeks="plaster_rose",
                 iris="wood_dark", lips="brick"),
    "esme": dict(eye=0.13, spread=0.27, brow=2, brow_z=0.22, mouth=0.18, smile=0.8, nose=0.095, cheeks=None,
                 iris="leaf_dark", lips="brick"),
}


def _face(mb, role):
    look, f = LOOK[role], FACE[role]
    ez = HEAD_C.z + 0.06
    for side in (-1, 1):
        x = side * f["spread"]
        with _on_face(mb, x, ez, 0.0):                           # eye: white, iris, pupil, highlight, upper lid
            mb.blob(f["eye"], "plaster_white", scale=(1.0, 0.34, 1.18), level=1, noise=0.0, smooth=True, grad=(0.75, 1.0))
            mb.blob(f["eye"] * 0.62, f["iris"], pos=(side * -0.012, -0.03, -0.012), scale=(1, 0.3, 1), level=1, noise=0.0,
                    smooth=True)
            mb.blob(f["eye"] * 0.34, "iron", pos=(side * -0.012, -0.042, -0.012), scale=(1, 0.3, 1), level=0, noise=0.0,
                    grad=(0.0, 0.2))
            mb.blob(f["eye"] * 0.16, "plaster_white", pos=(side * -0.012 + 0.03, -0.052, 0.03), scale=(1, 0.3, 1), level=0,
                    noise=0.0, grad=(0.95, 1.0))
            mb.box(f["eye"] * 2.3, 0.05, 0.035, look["hair"], pos=(0, -0.035, f["eye"] * 1.02), tone=-0.2)
        with _on_face(mb, x, ez + f["brow_z"], 0.0):             # eyebrow
            with mb.at(R("Y", side * f["brow"])):
                mb.box(0.25, 0.06, 0.06, look["hair"], pos=(0, -0.02, 0.0), anchor="c", tone=-0.12)
        _ball(mb, 0.15, (side * (HEAD_R[0] - 0.02), 0.05, HEAD_C.z + 0.0), look["skin"], scale=(0.5, 0.8, 1.15), tone=-0.04)  # ear
    with _on_face(mb, 0.0, HEAD_C.z - 0.12, 0.0):                # nose
        mb.blob(f["nose"], look["skin"], pos=(0, -0.05, 0.0), scale=(0.85, 1.25, 1.0), level=1, noise=0.0, smooth=True,
                tone=-0.05)
    mz = HEAD_C.z - 0.37                                          # mouth: short curved line, corners lifted by `smile`
    n = 3
    for i in range(n):
        u = i - 1
        x = u * f["mouth"] * 0.62
        z = mz + f["smile"] * 0.035 * abs(u)
        with _on_face(mb, x, z, 0.0):
            with mb.at(R("Y", -u * 20 * f["smile"])):
                mb.box(f["mouth"] * 0.7, 0.04, 0.034, f["lips"], pos=(0, -0.008, 0.0), anchor="c", tone=-0.22)
    with _on_face(mb, 0.0, mz - 0.075, 0.0):                      # lower lip: a soft shadow under the line
        mb.blob(0.07, look["skin"], scale=(1.5, 0.3, 0.55), level=0, noise=0.0, smooth=True, tone=-0.07)


def build_head(mb, role):
    look = LOOK[role]
    c = HEAD_C
    _ball(mb, 1.0, tuple(c), look["skin"], scale=HEAD_R, grad=(0.42, 0.74))
    _ball(mb, 0.36, (0, -0.14, c.z - 0.5), look["skin"], scale=(1.1, 0.95, 0.55), grad=(0.42, 0.74))  # chin and jaw
    _face(mb, role)
    hair = look["hair"]
    if role == "selma":
        _ball(mb, 1.0, (0, 0.08, c.z + 0.12), hair, scale=(0.75, 0.72, 0.76))                       # hair cap
        for side in (-1, 1):
            _ball(mb, 0.3, (side * 0.6, -0.12, c.z - 0.05), hair, scale=(0.5, 0.75, 1.5))           # strands at the temples
        for i in range(5):                                                                           # braid over the shoulder
            _ball(mb, 0.2 - i * 0.012, (0.62 + i * 0.03, 0.2 - i * 0.07, c.z - 0.5 - i * 0.27), hair, scale=(1, 1, 1.05))
        mb.blob(0.11, "cloth_green", pos=(0.76, -0.1, c.z - 1.82), level=0, noise=0.0)
        # witch hat: wide brim, bent point, band with a sprig
        with mb.at(T(0, 0.05, c.z + 0.5), R("X", -6)):
            mb.lathe([(1.35, -0.03), (1.38, 0.05), (0.66, 0.16), (0.6, 0.1)], "cloth_green", segs=14, smooth=True, grad=(0.3, 0.75))
            _body(mb, [(0.1, 0.66, 0.66), (0.55, 0.5, 0.5), (0.95, 0.32, 0.32, 0.06), (1.3, 0.16, 0.16, 0.2), (1.52, 0.03, 0.03, 0.4)],
                  "cloth_green", n=10, grad=(0.3, 0.78))
            mb.loft([_ring(0.67, 0.67, 0.14, 12), _ring(0.6, 0.6, 0.34, 12)], "wood_red", smooth=True)
            mb.box(0.2, 0.08, 0.2, "brass", pos=(0, -0.66, 0.14))
            mb.blob(0.14, "leaf_lime", pos=(0.3, -0.62, 0.34), scale=(0.7, 0.4, 1.3), level=0, noise=0.1)
    elif role == "nyra":
        _ball(mb, 1.0, (0, 0.06, c.z + 0.1), hair, scale=(0.74, 0.71, 0.75))                         # silver hair
        for i in range(5):                                                                           # fringe in strands
            _ball(mb, 0.2, (-0.44 + i * 0.22, -0.56 + 0.05 * abs(i - 2), c.z + 0.5 - 0.03 * abs(i - 2)), hair, scale=(0.75, 0.6, 1.0))
        for side in (-1, 1):
            _ball(mb, 0.24, (side * 0.6, -0.2, c.z - 0.3), hair, scale=(0.5, 0.7, 2.0))
        coat = LOOK[role]["coat"]
        # hood: a cap over the back of the head and a rim that frames the face without covering it
        _ball(mb, 1.0, (0, 0.34, c.z + 0.08), coat, scale=(0.86, 0.66, 0.92), grad=(0.26, 0.72))
        rim = []                                                                                     # rolled rim round the face
        for k in range(14):
            a = TAU * k / 14
            cx, cz = 0.8 * math.cos(a), 0.86 * math.sin(a)
            rim.append([(cx + 0.13 * math.cos(b) * math.cos(a), -0.12 + 0.2 * math.sin(b), c.z + 0.06 + cz + 0.13 * math.cos(b) * math.sin(a))
                        for b in (TAU * q / 6 for q in range(6))])
        mb.ring_loft(rim, coat, smooth=True, grad=(0.26, 0.72))
        _body(mb, [(4.5, 0.6, 0.5, 0.2), (4.85, 0.8, 0.6, 0.3)], coat, n=10, grad=(0.26, 0.7))                     # hood falls on the shoulders
        mb.cyl(0.1, 0.1, 0.05, "glass_light", pos=(0, -0.3, c.z + 0.98), segs=6, grad=(0.7, 1.0))  # star at the hood seam
    elif role == "lio":
        _ball(mb, 1.0, (0, 0.06, c.z + 0.14), hair, scale=(0.74, 0.72, 0.74))
        for i in range(5):                                                                           # tousled tufts
            a = -0.9 + i * 0.45
            _ball(mb, 0.24, (0.5 * math.sin(a), -0.38 - 0.1 * math.cos(a * 2), c.z + 0.74 + 0.08 * math.cos(a * 3)), hair,
                  scale=(1, 1, 0.8))
        # brass goggles pushed up on the forehead
        mb.loft([_ring(0.73, 0.71, c.z + 0.34, 12), _ring(0.73, 0.71, c.z + 0.5, 12)], "wood_dark", smooth=True)
        for side in (-1, 1):
            with mb.at(T(side * 0.27, -0.66, c.z + 0.43), R("X", 78)):
                mb.cyl(0.2, 0.18, 0.2, "brass", segs=10)
                mb.cyl(0.14, 0.14, 0.03, "glass_light", pos=(0, 0, 0.2), segs=10, grad=(0.6, 1.0))
        mb.box(0.16, 0.08, 0.08, "brass", pos=(0, -0.74, c.z + 0.39))
    elif role == "aron":
        _ball(mb, 1.0, (0, 0.1, c.z + 0.1), hair, scale=(0.73, 0.7, 0.72))                           # short hair
        # full beard with moustache
        _ball(mb, 0.62, (0, -0.3, c.z - 0.62), hair, scale=(1.05, 0.8, 0.85), grad=(0.3, 0.7))
        for side in (-1, 1):
            _ball(mb, 0.3, (side * 0.5, -0.22, c.z - 0.36), hair, scale=(0.7, 0.8, 1.2))
            _ball(mb, 0.17, (side * 0.17, -0.7, c.z - 0.27), hair, scale=(1.25, 0.6, 0.6))
        mb.blob(0.1, "brass", pos=(0, -0.62, c.z - 1.02), level=0, noise=0.0)                        # beard clasp
        # flat leather cap with a short peak
        _ball(mb, 1.0, (0, 0.04, c.z + 0.56), "wood_red", scale=(0.78, 0.78, 0.3), grad=(0.3, 0.7))
        mb.box(0.9, 0.5, 0.08, "wood_red", pos=(0, -0.72, c.z + 0.44), taper=(0.8, 0.9))
        mb.loft([_ring(0.74, 0.72, c.z + 0.4, 12), _ring(0.76, 0.74, c.z + 0.52, 12)], "iron", smooth=True)
    else:  # esme
        _ball(mb, 1.0, (0, 0.08, c.z + 0.1), hair, scale=(0.75, 0.72, 0.76))
        _ball(mb, 0.34, (0, 0.62, c.z - 0.1), hair, scale=(0.9, 0.9, 1.1))                           # bun at the back
        for side in (-1, 1):
            _ball(mb, 0.24, (side * 0.6, -0.2, c.z - 0.02), hair, scale=(0.5, 0.7, 1.4))
        # hunter's hat with a feather
        with mb.at(T(0, 0.03, c.z + 0.52), R("X", -4), R("Y", 6)):
            mb.lathe([(1.02, 0.0), (1.05, 0.08), (0.64, 0.18), (0.6, 0.1)], "wood_mid", segs=14, smooth=True, grad=(0.3, 0.75))
            _body(mb, [(0.1, 0.64, 0.64), (0.4, 0.58, 0.58), (0.62, 0.42, 0.48), (0.7, 0.08, 0.3)], "wood_mid", n=10,
                  grad=(0.3, 0.78))
            mb.loft([_ring(0.65, 0.65, 0.14, 12), _ring(0.61, 0.61, 0.3, 12)], "roof_teal", smooth=True)
            with mb.at(T(-0.6, 0.1, 0.24), R("Y", -28), R("X", 12)):
                mb.lathe([(0.0, 0.0), (0.13, 0.3), (0.1, 0.9), (0.0, 1.25)], "plaster_white", segs=5, smooth=False, grad=(0.6, 1.0))
                mb.box(0.03, 0.03, 1.2, "wood_pale")


# ---------------------------------------------------------------- arms and hands
def build_upper(mb, role, side):
    look = LOOK[role]
    j = joints(role)["upper_l" if side > 0 else "upper_r"]
    r = 0.27 * (1.08 if role == "aron" else 1.0)
    with mb.at(T(*j)):
        # sleeve with a rounded shoulder cap (one closed shape, so nothing intersects at the joint)
        _body(mb, [(-UPPER_LEN, r * 0.92, r * 0.92), (-0.5, r, r), (0.0, r * 1.08, r * 1.08), (0.17, r * 0.92, r * 0.92),
                   (0.28, r * 0.5, r * 0.5)], look["coat"], n=8, grad=(0.3, 0.75))
        if role == "esme":
            mb.loft([_ring(r * 1.12, r * 1.12, -0.6, 8), _ring(r * 1.12, r * 1.12, -0.46, 8)], look["trim"], smooth=True)


def _hand_open(mb, skin, side):
    """Relaxed hand: palm, four slightly curled fingers, thumb.  Hangs along -Z, palm towards the body."""
    mb.blob(0.21, skin, pos=(0, 0, -0.17), scale=(0.62, 0.95, 1.0), level=1, noise=0.0, smooth=True)
    for i in range(4):
        y = -0.135 + i * 0.09
        ln = (0.2, 0.24, 0.23, 0.18)[i]
        with mb.at(T(0, y, -0.33), R("Y", side * 14)):
            mb.box(0.085, 0.08, ln, skin, pos=(0, 0, -ln), tone=-0.03 * (i % 2))
            with mb.at(T(0, 0, -ln), R("Y", side * 30)):
                mb.box(0.08, 0.075, ln * 0.6, skin, pos=(0, 0, -ln * 0.6), taper=0.8)
    with mb.at(T(side * -0.05, -0.2, -0.16), R("X", 38), R("Y", side * 20)):                        # thumb, to the front
        mb.box(0.1, 0.09, 0.22, skin, pos=(0, 0, -0.22), taper=0.8)


def _hand_grip(mb, skin, side):
    """Fist closed around a handle that runs along Y through the grip point: back of the hand, four
    fingers folded over the handle, thumb across them."""
    mb.blob(0.21, skin, pos=(side * 0.05, 0, GRIP_Z + 0.06), scale=(0.72, 1.02, 0.86), level=1, noise=0.0, smooth=True)
    for i in range(4):                                           # fingers: two short segments each, curled round the handle
        y = -0.15 + i * 0.1
        with mb.at(T(side * -0.13, y, GRIP_Z - 0.02)):
            mb.box(0.11, 0.088, 0.24, skin, pos=(0, 0, -0.13), tone=-0.035 * (i % 2))
        with mb.at(T(side * -0.03, y, GRIP_Z - 0.16)):
            mb.box(0.2, 0.086, 0.1, skin, pos=(0, 0, -0.05), tone=-0.035 * (i % 2))
    with mb.at(T(side * -0.12, -0.04, GRIP_Z + 0.14), R("Z", side * 12)):                          # thumb over the fingers
        mb.box(0.11, 0.3, 0.1, skin, pos=(0, 0, -0.05), taper=(1.0, 0.85))


GRIP_Z = -0.3           # centre of the fist below the wrist
HAND_SCALE = 1.22


def build_fore(mb, role, side):
    look = LOOK[role]
    tag = "fore_l" if side > 0 else "fore_r"
    j = joints(role)[tag]
    r = 0.24 * (1.08 if role == "aron" else 1.0)
    held = HELD[role][tag]
    bare = role == "aron"                                        # rolled-up sleeves
    with mb.at(T(*j)):
        _ball(mb, r * 1.16, (0, 0, 0), look["coat"], grad=(0.35, 0.78))                              # elbow ball
        if bare:
            _body(mb, [(-0.34, r, r), (-0.02, r * 1.04, r * 1.04)], look["coat"], n=8, grad=(0.3, 0.75))
            mb.loft([_ring(r * 1.12, r * 1.12, -0.42, 8), _ring(r * 1.12, r * 1.12, -0.3, 8)], look["coat"], smooth=True, tone=0.08)
            _body(mb, [(-FORE_LEN, r * 0.74, r * 0.74), (-0.36, r * 0.92, r * 0.92)], look["skin"], n=8, grad=(0.4, 0.72))
        else:
            _body(mb, [(-FORE_LEN + 0.1, r * 0.86, r * 0.86), (-0.4, r * 0.95, r * 0.95), (-0.02, r * 1.04, r * 1.04)],
                  look["coat"], n=8, grad=(0.3, 0.75))
            mb.loft([_ring(r * 1.02, r * 1.02, -FORE_LEN + 0.04, 8), _ring(r * 1.02, r * 1.02, -FORE_LEN + 0.2, 8)],
                    look["trim"], smooth=True)                                                       # cuff
            _body(mb, [(-FORE_LEN - 0.02, r * 0.62, r * 0.62), (-FORE_LEN + 0.08, r * 0.7, r * 0.7)], look["skin"], n=8)  # wrist
        with mb.at(T(0, 0, -FORE_LEN), S(HAND_SCALE)):
            if held:
                _hand_grip(mb, look["skin"], side)
                with mb.at(T(0, 0, GRIP_Z)):
                    held(mb, side)
            else:
                _hand_open(mb, look["skin"], side)


# ---------------------------------------------------------------- things in the hands
# Each tool is modelled around the grip point; the handle runs along Y (front - back in the rest
# pose).  With the forearm raised forwards the handle stands upright: +Y of the rest pose is "up".
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
        "upper_r": [(0, (-34, 12, 0)), (1.6, (-64, 8, 24)), (3.4, (-64, 8, 24)), (5.2, (-34, 4, 46)), (6.4, (-34, 4, 46)), (8, (-34, 12, 0))],
        "fore_r": [(0, (-70, 0, 0)), (1.6, (-116, 0, 0)), (3.4, (-112, 0, 0)), (5.2, (-58, 0, 0)), (6.4, (-54, 0, 0)), (8, (-70, 0, 0))],
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
        "upper_l": [(0, (-44, -4, -30)), (0.5, (-50, -2, -34)), (1.0, (-42, -6, -28)), (1.5, (-50, -2, -34)), (2.0, (-42, -6, -28)), (3.4, (-24, -10, -6)), (5.4, (-24, -10, -6)), (6.5, (-44, -4, -30))],
        "fore_l": [(0, (-92, 0, 0)), (0.5, (-100, 0, 0)), (1.0, (-88, 0, 0)), (1.5, (-100, 0, 0)), (2.0, (-88, 0, 0)), (3.4, (-66, 0, 0)), (5.4, (-66, 0, 0)), (6.5, (-92, 0, 0))],
        "upper_r": [(0, (-40, 2, 30)), (2.0, (-40, 2, 30)), (3.6, (-118, 34, -8)), (5.2, (-118, 34, -8)), (6.5, (-40, 2, 30))],
        "fore_r": [(0, (-90, 0, 0)), (2.0, (-90, 0, 0)), (3.6, (-42, 0, 26)), (4.4, (-42, 0, -26)), (5.2, (-42, 0, 26)), (6.5, (-90, 0, 0))],
        "head": [(0, (14, 0, 0)), (2.0, (14, 0, 0)), (3.6, (-14, 6, -22)), (5.2, (-14, 6, -22)), (6.5, (14, 0, 0))],
        "torso": [(0, (4, 0, 0)), (3.6, (-2, 0, -6)), (5.2, (-2, 0, -6)), (6.5, (4, 0, 0))],
    }),
    # Aron weighs the ore in his hand and taps it twice with the hammer.
    "aron": dict(duration=6.0, keys={
        "upper_l": [(0, (-34, -6, -18)), (3.0, (-36, -6, -18)), (4.4, (-50, -8, -8)), (6, (-34, -6, -18))],
        "fore_l": [(0, (-84, 0, 0)), (1.5, (-80, 0, 0)), (1.7, (-76, 0, 0)), (2.1, (-80, 0, 0)), (2.3, (-76, 0, 0)), (3.0, (-84, 0, 0)), (4.4, (-98, 0, 0)), (6, (-84, 0, 0))],
        "upper_r": [(0, (-26, 14, 6)), (1.1, (-66, 10, 20)), (1.5, (-36, 4, 30)), (1.9, (-60, 8, 22)), (2.1, (-36, 4, 30)), (3.0, (-26, 16, 6)), (6, (-26, 14, 6))],
        "fore_r": [(0, (-66, 0, 0)), (1.1, (-104, 0, 0)), (1.5, (-52, 0, 0)), (1.9, (-98, 0, 0)), (2.1, (-52, 0, 0)), (3.0, (-70, 0, 0)), (6, (-66, 0, 0))],
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
    """Adds one part to the builder: in the rest pose (t = None) or posed at loop time t."""
    if t is None:
        BUILDERS[part](mb, role)
        return
    frame = pose_frames(role, t)[part] @ pose_frames(role)[part].inverted()
    with mb.at(frame):
        BUILDERS[part](mb, role)


def build_figure(mb, role, t=0.0):
    """Whole trader as one mesh, posed at loop time t (preview renders)."""
    for part in PARTS:
        build_part(mb, role, part, t)
