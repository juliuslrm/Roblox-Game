"""Market stands of the five alchemy traders, facing Blender -Y.

The traders themselves are built in merchants.py.  STYLES: awning cloth, sign colour (the other
entries of a row were used by the first figure generator and are kept for the stall colours only).
"""
from .machines import bottle
from .meshkit import R, T

STYLES = {
    "selma": ("cloth_green", "pine", "wood_pale", "plaster_peach", "wood_red", 1.0, 1.0),
    "nyra": ("roof_purple", "roof_slate", "glass_light", "plaster_rose", "wood_grey", 0.93, 1.02),
    "lio": ("cloth_blue", "roof_teal", "wood_mid", "wood_light", "wood_dark", 0.94, 0.98),
    "aron": ("roof_red", "iron", "wood_red", "plaster_peach", "wood_dark", 1.23, 0.95),
    "esme": ("roof_teal", "leaf_dark", "wood_mid", "sand", "wood_red", 0.98, 1.07),
}


def sprig(mb, x, y, z, scale=1, color="leaf_green"):
    mb.beam((x, y, z), (x + 0.07 * scale, y, z + 0.9 * scale), 0.055 * scale, 0.055 * scale, "leaf_dark")
    for i in range(4):
        sign = 1 if i % 2 else -1
        with mb.at(T(x + sign * 0.15 * scale, y, z + (i + 1) * 0.19 * scale), R("Y", sign * 31)):
            mb.blob(0.23 * scale, color, scale=(0.65, 0.36, 1.22), level=0, noise=0.07,
                    grad=(0.38, 0.73))


def mushroom(mb, x, y, z, scale=1):
    mb.cyl(0.13 * scale, 0.11 * scale, 0.45 * scale, "plaster_cream", (x, y, z), segs=6, smooth=False)
    mb.lathe([(0.18 * scale, 0.34 * scale), (0.41 * scale, 0.40 * scale),
              (0.34 * scale, 0.62 * scale), (0.13 * scale, 0.73 * scale)],
             "roof_purple", segs=8, pos=(x, y, z), smooth=False)
    for dx, dy, dz in ((-0.16, -0.16, 0.59), (0.18, -0.12, 0.60), (0.0, 0.14, 0.67)):
        mb.blob(0.06 * scale, "flower_purple", (x + dx * scale, y + dy * scale, z + dz * scale),
                scale=(1, 1, 0.58), level=0, noise=0)


def crystal(mb, x, y, z, scale=1, color="glass_light"):
    with mb.at(T(x, y, z), R("Y", -12)):
        mb.lathe([(0.21 * scale, 0), (0.29 * scale, 0.3 * scale), (0.19 * scale, 0.82 * scale),
                  (0.04 * scale, 1.05 * scale)], color, segs=5, smooth=False, grad=(0.34, 0.86))


def flask_case(mb, x, y, z, scale=1):
    mb.box(0.8 * scale, 0.6 * scale, 0.10 * scale, "brass", (x, y, z))
    mb.box(0.59 * scale, 0.43 * scale, 0.58 * scale, "glass_lit", (x, y, z + 0.09 * scale))
    mb.box(0.8 * scale, 0.6 * scale, 0.12 * scale, "iron", (x, y, z + 0.62 * scale))
    for dx in (-0.32, 0.32):
        for dy in (-0.22, 0.22):
            mb.box(0.07 * scale, 0.07 * scale, 0.6 * scale, "iron",
                   (x + dx * scale, y + dy * scale, z + 0.09 * scale))


def goods(mb, role, z=3):
    for x in (-2.55, 0, 2.55):
        mb.box(2.11, 1.45, 0.21, "wood_mid", (x, -0.6, z), taper=1.08)
    if role == "selma":
        for i in range(8):
            sprig(mb, -3.3 + i * 0.49, -0.73 + i % 2 * 0.38, z + 0.21,
                  0.75 + i % 3 * 0.17, "leaf_lime" if i < 4 else "leaf_teal")
        for i in range(5):
            mb.blob(0.20, "flower_red", (1.78 + i * 0.35, -0.63, z + 0.35), level=0, noise=0.04)
        for i in range(2):
            mb.lathe([(0.27, 0), (0.31, 0.26), (0.18, 0.54), (0.20, 0.58)], "cloth_white",
                     segs=7, pos=(2.2 + i * 0.58, -0.18, z + 0.20), smooth=False)
    elif role == "nyra":
        for i in range(5):
            mushroom(mb, -3.30 + i * 0.46, -0.69 + i % 2 * 0.37, z + 0.2, 0.83 + i % 3 * 0.28)
        for i in range(5):
            crystal(mb, 1.8 + i * 0.36, -0.70 + i % 2 * 0.35, z + 0.2,
                    0.67 + i % 3 * 0.25, "flower_purple" if i % 2 else "glass_light")
        for i in range(3):
            sprig(mb, -0.49 + i * 0.43, -0.65, z + 0.21, 0.69, "glass_light")
    elif role == "lio":
        for i in range(9):
            bottle(mb, -0.71 + i % 3 * 0.61 + (2.55 if i > 4 else 0), -1.01 + i // 3 * 0.42,
                   z + 0.22, "glass_light", 0.81 + i % 3 * 0.25)
        mb.blob(0.77, "sand", (-2.56, -0.55, z + 0.23), scale=(1, 0.61, 0.47), level=1, noise=0.07)
    elif role == "aron":
        for i, color in enumerate(("iron", "brick", "stone_grey")):
            for j in range(5):
                mb.blob(0.37 + 0.08 * (j % 2), color,
                        (2.55 * (i - 1) + (j % 3 - 1) * 0.55, -0.93 + 0.59 * (j // 3), z + 0.38),
                        scale=(1, 0.83, 0.79), level=0, noise=0.26)
        mb.box(1.13, 0.49, 0.23, "brass", (0.10, -0.22, z + 0.3), taper=0.74)
    else:
        for i in range(5):
            with mb.at(T(-3.2 + 0.57 * (i % 3), -0.45, z + 0.4 + 0.36 * (i // 3)), R("X", 90)):
                mb.cyl(0.26, 0.25, 1.21, "bark", segs=7, smooth=False)
                mb.cyl(0.217, 0.217, 0.03, "wood_pale", (0, 0, 1.21), segs=7, smooth=False)
        for i in range(6):
            mb.blob(0.41, "stone_warm" if i % 2 else "stone_grey",
                    (1.93 + 0.53 * (i % 3), -1.03 + 0.52 * (i // 3), z + 0.35),
                    scale=(1.1, 0.85, 0.73), level=0, noise=0.19)
        mb.box(1.54, 0.36, 0.22, "wood_light", (0, -0.73, z + 0.22), taper=0.86)


def stall(mb, role):
    cloth, trim, *_ = STYLES[role]
    mb.box(7.8, 2.03, 2.78, "wood_mid", (0, -0.45, 0))
    mb.box(8.2, 2.25, 0.25, "wood_light", (0, -0.45, 2.75))
    for i in range(10):
        mb.box(0.734, 0.075, 2.30, "wood_dark" if i % 3 == 0 else "wood_mid",
               ((i - 4.5) * 0.758, -1.50, 0.2), tone=mb.jitter(0.055))
    mb.box(7.9, 0.16, 0.38, "wood_dark", (0, -1.55, 0.19))
    for sign in (-1, 1):
        for y, top in ((-2.06, 8.16), (2.05, 8.96)):
            mb.box(0.38, 0.38, top, "wood_dark", (sign * 4.15, y, 0))
            mb.beam((sign * 4.15, y, top - 1.47), (sign * 2.52, y, top - 0.17),
                    0.19, 0.22, "wood_mid")
    for i in range(8):
        x = (i - 3.5) * 1.12
        color = cloth if i % 2 else "cloth_white"
        mb.beam((x, 2.55, 9.05), (x, -2.94, 8.14), 1.12, 0.18, color)
        mb.box(1.095, 0.13, 0.51 + (i % 2) * 0.12, color, (x, -2.91, 7.52 + (i % 2) * 0.06))
    mb.box(1.75, 0.14, 1.02, trim, (0, -1.67, 1.22))
    mb.box(1.93, 0.065, 0.11, "brass", (0, -1.75, 1.16))
    mb.box(1.93, 0.065, 0.11, "brass", (0, -1.75, 2.24))
    with mb.at(T(0, -1.82, 1.35)):
        if role == "selma":
            sprig(mb, -0.1, 0, 0, 0.87, "leaf_lime")
        elif role == "nyra":
            crystal(mb, 0.08, 0, 0, 0.7)
        elif role == "lio":
            bottle(mb, 0, 0, 0, "glass_light", 0.83)
        elif role == "aron":
            mb.beam((-0.24, 0, 0.08), (0.19, 0, 0.68), 0.11, 0.10, "wood_light")
            mb.box(0.66, 0.16, 0.29, "brass", (0.11, 0, 0.56))
        else:
            for side in (-1, 1):
                mb.beam((side * 0.35, 0, 0.12), (-side * 0.30, 0, 0.73), 0.18, 0.14, "wood_pale")
    goods(mb, role)
