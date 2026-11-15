"""Architectural building blocks: foundations, storeys, timber framing, roofs,
windows, doors, chimneys, dormers.

Wall details are always modelled in a *wall frame*: x runs left -> right when
looking at the wall from outside, z is up, and the outside is towards -y.
Wing.storey() places that frame on each of the four walls.
"""
import math

from .meshkit import T, R, S, lerp, clamp

BW = 0.85      # timber beam width
BT = 0.28      # timber protrusion from the plaster


# =====================================================================
# opening descriptors
# =====================================================================
def win(u, **kw):
    """Window at fraction u (0..1) along the wall."""
    d = {"t": "win", "u": u, "w": 3.0, "h": 4.2, "z": 3.3}
    d.update(kw)
    return d


def door(u, **kw):
    d = {"t": "door", "u": u, "w": 4.0, "h": 7.4, "z": 0.0}
    d.update(kw)
    return d


# =====================================================================
# wall-frame details
# =====================================================================
def w_beam(mb, x0, z0, x1, z1, color, w=BW, t=BT, tone=None):
    """Timber lying on the wall plane between two points."""
    length = math.hypot(x1 - x0, z1 - z0)
    if length < 1e-3:
        return
    ux, uz = (x1 - x0) / length, (z1 - z0) / length
    px, pz = -uz * w / 2, ux * w / 2
    poly = [(x0 - px, z0 - pz), (x1 - px, z1 - pz), (x1 + px, z1 + pz), (x0 + px, z0 + pz)]
    mb.prism(poly, -t, 0.04, color, hide1=True, grad=(0.45, 0.57),
             tone=mb.jitter(0.05) if tone is None else tone)


def _arc(cx, zs, half_w, rise, segs=6):
    """Arc points from the right spring point to the left one."""
    return [(cx + half_w * math.cos(math.pi * i / segs), zs + rise * math.sin(math.pi * i / segs))
            for i in range(segs + 1)]


def window(mb, cx, z0, w=3.0, h=4.2, frame="wood_dark", glass="glass_blue", arch=False,
           muntins=(1, 1), shutters=None, flowerbox=None, sill="stone_light", lit=False,
           fw=0.42, round_=False, **_):
    """Window sitting on the wall plane. (cx, z0) = bottom centre of the glass."""
    gcol = "glass_lit" if lit else glass
    ggrad = (0.55, 0.8) if lit else (0.3, 0.78)
    x0, x1, z1 = cx - w / 2, cx + w / 2, z0 + h
    if round_:
        r = w / 2
        cz = z0 + r
        pts = [(cx + r * math.cos(2 * math.pi * i / 8 + math.pi / 8),
                cz + r * math.sin(2 * math.pi * i / 8 + math.pi / 8)) for i in range(8)]
        mb.poly([(x, -0.07, z) for x, z in pts], gcol, facing=(0, -1, 0), grad=ggrad)
        for i in range(8):
            a, b = pts[i], pts[(i + 1) % 8]
            k = (r + fw / 2) / r
            w_beam(mb, cx + (a[0] - cx) * k, cz + (a[1] - cz) * k,
                   cx + (b[0] - cx) * k, cz + (b[1] - cz) * k, frame, w=fw, t=0.3)
        w_beam(mb, cx, cz - r, cx, cz + r, frame, w=0.16, t=0.16)
        w_beam(mb, cx - r, cz, cx + r, cz, frame, w=0.16, t=0.16)
        return
    if arch:
        rise = w * 0.42
        zs = z1 - rise
        arc = _arc(cx, zs, w / 2, rise)
        pts = [(x0, z0), (x1, z0)] + arc
        mb.poly([(x, -0.07, z) for x, z in pts], gcol, facing=(0, -1, 0), grad=ggrad)
        k = (w / 2 + fw / 2) / (w / 2)
        kz = (rise + fw / 2) / rise
        for a, b in zip(arc[:-1], arc[1:]):
            w_beam(mb, cx + (a[0] - cx) * k, zs + (a[1] - zs) * kz,
                   cx + (b[0] - cx) * k, zs + (b[1] - zs) * kz, frame, w=fw, t=0.3)
        w_beam(mb, x0 - fw / 2, z0 - fw, x0 - fw / 2, zs, frame, w=fw, t=0.3)
        w_beam(mb, x1 + fw / 2, z0 - fw, x1 + fw / 2, zs, frame, w=fw, t=0.3)
        mtop = zs
    else:
        mb.quad((x0, -0.07, z0), (x1, -0.07, z0), (x1, -0.07, z1), (x0, -0.07, z1), gcol,
                facing=(0, -1, 0), grad=ggrad)
        w_beam(mb, x0 - fw / 2, z0 - fw, x0 - fw / 2, z1 + fw, frame, w=fw, t=0.3)
        w_beam(mb, x1 + fw / 2, z0 - fw, x1 + fw / 2, z1 + fw, frame, w=fw, t=0.3)
        w_beam(mb, x0, z1 + fw / 2, x1, z1 + fw / 2, frame, w=fw, t=0.3)
        mtop = z1
    w_beam(mb, x0, z0 - fw / 2, x1, z0 - fw / 2, frame, w=fw, t=0.3)
    nv, nh = muntins
    for i in range(nv):
        x = lerp(x0, x1, (i + 1) / (nv + 1))
        top = z1 if not arch else zs + rise * math.sqrt(max(0.0, 1 - ((x - cx) / (w / 2)) ** 2))
        w_beam(mb, x, z0, x, top, frame, w=0.16, t=0.16)
    for i in range(nh):
        z = lerp(z0, mtop, (i + 1) / (nh + 1))
        w_beam(mb, x0, z, x1, z, frame, w=0.16, t=0.16)
    if sill:
        mb.box(w + 2 * fw + 0.5, 0.75, 0.3, sill, pos=(cx, -0.3, z0 - fw - 0.3), skip=("+y",))
    if shutters:
        sw, sh = w / 2 + 0.12, h + 0.3
        for side in (-1, 1):
            hinge = cx + side * (w / 2 + fw)
            with mb.at(T(hinge, -0.14, z0 - 0.15), R("Z", -side * 11)):
                mb.box(sw, 0.16, sh, shutters, pos=(side * sw / 2, 0, 0), tone=mb.jitter(0.04))
                for zz in (sh * 0.2, sh * 0.72):
                    mb.box(sw * 0.94, 0.1, 0.24, shutters, pos=(side * sw / 2, -0.1, zz),
                           tone=-0.16, skip=("+y",))
    if flowerbox:
        bz = z0 - fw - 0.95
        mb.box(w + 0.7, 0.95, 0.7, "wood_mid", pos=(cx, -0.55, bz), taper=1.06, skip=("+y",))
        n = 3
        for i in range(n):
            fx = lerp(x0 + 0.3, x1 - 0.3, i / (n - 1)) + mb.jitter(0.12)
            mb.blob(0.5, "leaf_green", pos=(fx, -0.58, bz + 0.85), level=0, noise=0.2,
                    scale=(1, 0.8, 0.75), grad=(0.3, 0.75))
            mb.blob(0.24, flowerbox, pos=(fx + mb.jitter(0.25), -0.85, bz + 1.15 + mb.jitter(0.1)),
                    level=0, noise=0.1, grad=(0.45, 0.75))


def door_leaf(mb, cx, z0, w=4.0, h=7.4, color="wood_mid", frame="wood_dark", arch=False,
              double=False, bands=True, fw=0.6, peek=False, **_):
    """Door on the wall plane. Returns the z of the top of its frame."""
    x0, x1 = cx - w / 2, cx + w / 2
    if arch:
        rise = w * 0.4
        zs = z0 + h - rise
        arc = _arc(cx, zs, w / 2, rise)
        poly = [(x0, z0), (x1, z0)] + arc
    else:
        zs = z0 + h
        poly = [(x0, z0), (x1, z0), (x1, zs), (x0, zs)]
    mb.prism(poly, -0.2, 0.04, color, hide1=True, grad=(0.38, 0.6))
    # plank grooves
    n = max(3, round(w / 1.0))
    for i in range(1, n):
        x = lerp(x0, x1, i / n)
        top = zs if not arch else zs + rise * math.sqrt(max(0.0, 1 - ((x - cx) / (w / 2)) ** 2))
        wide = 0.14 if (double and i == n // 2) else 0.07
        mb.box(wide, 0.06, top - z0 - 0.1, color, pos=(x, -0.22, z0 + 0.05), tone=-0.22,
               skip=("+y", "-z"))
    if bands:
        for zz in (z0 + h * 0.2, z0 + h * 0.66):
            mb.box(w * 0.92, 0.08, 0.32, "iron", pos=(cx, -0.24, zz), skip=("+y",))
    knobs = [cx - 0.35, cx + 0.35] if double else [cx + w * 0.32]
    for kx in knobs:
        mb.box(0.3, 0.3, 0.3, "brass", pos=(kx, -0.32, z0 + h * 0.44), anchor="c")
    if peek:   # small window in the door
        mb.quad((cx - 0.5, -0.215, z0 + h * 0.6), (cx + 0.5, -0.215, z0 + h * 0.6),
                (cx + 0.5, -0.215, z0 + h * 0.6 + 1.0), (cx - 0.5, -0.215, z0 + h * 0.6 + 1.0),
                "glass_lit", facing=(0, -1, 0), grad=(0.55, 0.75))
    # frame
    w_beam(mb, x0 - fw / 2, z0, x0 - fw / 2, zs, frame, w=fw, t=0.42)
    w_beam(mb, x1 + fw / 2, z0, x1 + fw / 2, zs, frame, w=fw, t=0.42)
    if arch:
        k = (w / 2 + fw / 2) / (w / 2)
        kz = (rise + fw / 2) / rise
        for a, b in zip(arc[:-1], arc[1:]):
            w_beam(mb, cx + (a[0] - cx) * k, zs + (a[1] - zs) * kz,
                   cx + (b[0] - cx) * k, zs + (b[1] - zs) * kz, frame, w=fw, t=0.42)
    else:
        w_beam(mb, x0 - fw, zs + fw / 2, x1 + fw, zs + fw / 2, frame, w=fw, t=0.42)
    return z0 + h + fw


def door_hood(mb, cx, z, w, color, depth=2.8, bracket="wood_dark"):
    """Small lean-to roof on two brackets above a door."""
    half = w / 2 + 1.0
    mb.beam((cx, 0.0, z + 1.5), (cx, -depth, z + 0.25), 2 * half, 0.34, color, grad=(0.4, 0.62))
    mb.beam((cx, 0.0, z + 1.68), (cx, -depth * 0.5, z + 1.08), 2 * half + 0.2, 0.3, color, tone=0.07)
    for sx in (-1, 1):
        x = cx + sx * (half - 0.45)
        mb.beam((x, -0.05, z - 1.3), (x, -depth * 0.82, z + 0.45), 0.4, 0.4, bracket)
        mb.beam((x, -0.05, z + 0.55), (x, -depth * 0.86, z + 0.55), 0.4, 0.4, bracket)


def wall_lantern(mb, x, z, color="iron"):
    """Lantern on a bracket; registers a light anchor."""
    mb.beam((x, 0, z + 0.9), (x, -1.2, z + 0.9), 0.18, 0.18, color)
    mb.beam((x, 0, z + 0.2), (x, -1.0, z + 0.9), 0.14, 0.14, color)
    mb.box(0.75, 0.75, 0.12, color, pos=(x, -1.2, z + 0.65))
    mb.box(0.55, 0.55, 0.8, "glass_lit", pos=(x, -1.2, z - 0.15), grad=(0.6, 0.85))
    mb.box(0.75, 0.75, 0.12, color, pos=(x, -1.2, z - 0.27))
    mb.light((x, -1.2, z + 0.25), brightness=0.9, range_=22)


def steps(mb, cx, fh, w=5.2, color="stone_light", deep=0.6):
    """Stairs from the ground (z = -fh) up to the door sill (z = 0)."""
    n = max(1, round(fh / 0.8))
    rise = fh / n
    for i in range(n):
        depth = 1.7 + i * 1.15
        top = -i * rise
        mb.box(w + i * 0.25, depth, (fh + deep) + top, color,
               pos=(cx, -depth / 2 + 0.02, -fh - deep), tone=mb.jitter(0.04) - i * 0.015,
               skip=("-z",))


def lean_to_roof(mb, x0, W, depth, H, color, z=0.0, og=0.8, oe=1.0, th=0.4, courses=4, lip=0.2):
    """Single-slope roof in the wall frame: touches the wall at height z + H
    and falls to z at y = -depth. Covers x0 .. x0 + W."""
    length = math.hypot(depth, H)
    dy, dz = -depth / length, -H / length
    ny, nz = -H / length, depth / length
    total = depth + oe
    for i in range(courses):
        ta, tb = i / courses, (i + 1) / courses
        a = (-total * ta, z + H - H * (total / depth) * ta)
        b = (-total * tb + dy * 0.15, z + H - H * (total / depth) * tb + dz * 0.15)
        lp = lip * (1.3 if i == courses - 1 else 1.0)
        sec = [(a[0] - ny * th, a[1] - nz * th), (b[0] - ny * th, b[1] - nz * th),
               (b[0] + ny * lp, b[1] + nz * lp), (a[0] + ny * 0.02, a[1] + nz * 0.02)]
        rings = [[(x0 - og, y, zz) for y, zz in sec], [(x0 + W + og, y, zz) for y, zz in sec]]
        mb.loft(rings, color, zr=(z - 1, z + H + 0.5), grad=(0.36, 0.64),
                tone=(0.03 if i % 2 else -0.02) + mb.jitter(0.03))


def porch(mb, x0, W, depth, post_h, roof_h, roof_color, post="wood_dark", z=0.0, n_posts=2,
          rail=False):
    """Open porch in the wall frame: posts, plate beam, lean-to roof."""
    yf = -depth + 0.45
    xs = [lerp(x0 + 0.45, x0 + W - 0.45, i / (n_posts - 1)) for i in range(n_posts)]
    for x in xs:
        mb.box(0.6, 0.6, post_h, post, pos=(x, yf, z), tone=mb.jitter(0.04))
        mb.box(0.9, 0.9, 0.35, post, pos=(x, yf, z), tone=-0.05)
        for sx in (-1, 1):
            if x0 + 0.3 < x + sx * 1.3 < x0 + W - 0.3:
                mb.beam((x, yf, z + post_h - 1.5), (x + sx * 1.3, yf, z + post_h - 0.1), 0.35, 0.35, post)
    mb.beam((x0 - 0.2, yf, z + post_h + 0.25), (x0 + W + 0.2, yf, z + post_h + 0.25), 0.55, 0.5, post)
    for x in (x0 + 0.3, x0 + W - 0.3):
        mb.beam((x, yf, z + post_h + 0.25), (x, 0.0, z + post_h + 0.25), 0.45, 0.45, post)
    if rail:
        for a, b in zip(xs[:-1], xs[1:]):
            mb.beam((a, yf, z + 2.4), (b, yf, z + 2.4), 0.3, 0.3, post)
            k = max(2, round((b - a) / 1.4))
            for i in range(1, k):
                mb.box(0.2, 0.2, 2.3, post, pos=(lerp(a, b, i / k), yf, z + 0.1), tone=0.05)
    lean_to_roof(mb, x0, W, depth, roof_h, roof_color, z=z + post_h + 0.5)


def awning(mb, cx, z, w, depth=3.4, rise=1.5, colors=("cloth_red", "cloth_white")):
    """Striped fabric awning with a scalloped valance."""
    n = max(4, round(w / 1.15))
    sw = w / n
    for i in range(n):
        x = cx - w / 2 + sw * (i + 0.5)
        col = colors[i % 2]
        mb.beam((x, 0.0, z + rise), (x, -depth, z), sw, 0.14, col, grad=(0.4, 0.66))
        mb.box(sw, 0.12, 0.55 if i % 2 else 0.75, col, pos=(x, -depth, z - (0.5 if i % 2 else 0.7)),
               tone=-0.05)
    for sx in (-1, 1):
        x = cx + sx * (w / 2 - 0.1)
        mb.beam((x, -0.05, z - 1.6), (x, -depth + 0.1, z - 0.1), 0.14, 0.14, "iron")


def hanging_sign(mb, x, z, board="wood_light", emblem="cloth_yellow", reach=2.8, shape="round"):
    """Shop sign hanging from an iron bracket, perpendicular to the wall."""
    mb.beam((x, 0.0, z), (x, -reach, z), 0.18, 0.18, "iron")
    mb.beam((x, 0.0, z - 1.3), (x, -reach * 0.7, z - 0.1), 0.14, 0.14, "iron")
    yc = -reach * 0.62
    for dy in (-0.55, 0.55):
        mb.box(0.08, 0.08, 0.5, "iron", pos=(x, yc + dy, z - 0.55))
    mb.box(0.22, 2.1, 1.7, board, pos=(x, yc, z - 2.25), grad=(0.42, 0.62))
    mb.box(0.3, 2.3, 0.2, "wood_dark", pos=(x, yc, z - 0.6))
    mb.box(0.3, 2.3, 0.2, "wood_dark", pos=(x, yc, z - 2.4))
    if shape == "round":
        mb.blob(0.52, emblem, pos=(x, yc, z - 1.4), scale=(0.42, 1, 1), level=0, noise=0.0)
    else:
        mb.box(0.34, 1.2, 0.8, emblem, pos=(x, yc, z - 1.8))


def balcony(mb, cx, z, w, depth=3.0, wood="wood_dark", floor="wood_light"):
    mb.box(w, depth, 0.32, floor, pos=(cx, -depth / 2, z - 0.32))
    for sx in (-1, 1):
        x = cx + sx * (w / 2 - 0.5)
        mb.beam((x, -0.05, z - 2.2), (x, -depth + 0.4, z - 0.3), 0.4, 0.4, wood)
    yf = -depth + 0.15
    n = max(3, round(w / 1.1))
    for i in range(n + 1):
        x = cx - w / 2 + 0.15 + (w - 0.3) * i / n
        mb.box(0.22, 0.22, 2.3, wood, pos=(x, yf, z), tone=mb.jitter(0.04))
    for sx in (-1, 1):
        x = cx + sx * (w / 2 - 0.15)
        for y in (-depth * 0.5,):
            mb.box(0.22, 0.22, 2.3, wood, pos=(x, y, z))
        mb.beam((x, 0.0, z + 2.4), (x, yf, z + 2.4), 0.32, 0.26, wood)
    mb.beam((cx - w / 2, yf, z + 2.4), (cx + w / 2, yf, z + 2.4), 0.32, 0.26, wood)


def ext_stairs(mb, x_start, x_end, rise_total, width=3.4, wood="wood_mid", dark="wood_dark",
               landing=4.4, z_ground=0.0):
    """Wooden stairs along a wall (wall frame). Climbs from x_start at
    z_ground to a landing ending at x_end, rise_total above z_ground."""
    sgn = 1 if x_end > x_start else -1
    run_total = abs(x_end - x_start) - landing
    n = max(3, round(rise_total / 0.85))
    run, rise = run_total / n, rise_total / n
    yc = -width / 2
    for i in range(n):
        x = x_start + sgn * run * (i + 0.5)
        mb.box(run + 0.15, width, 0.3, wood, pos=(x, yc, z_ground + rise * (i + 1) - 0.3),
               tone=mb.jitter(0.05))
    xl0 = x_start + sgn * run_total
    top = z_ground + rise_total
    mb.box(landing, width, 0.35, wood, pos=((xl0 + x_end) / 2, yc, top - 0.35))
    for y in (-0.2, -width + 0.2):
        mb.beam((x_start, y, z_ground + 0.1), (xl0, y, top - 0.35), 0.3, 0.7, dark)
    for x in (xl0 + sgn * 0.3, x_end - sgn * 0.3):
        mb.box(0.5, 0.5, rise_total + 0.6, dark, pos=(x, -width + 0.3, z_ground - 0.6))
    # railing on the outer side
    yo = -width + 0.15
    mb.beam((x_start, yo, z_ground + 3.0), (xl0, yo, top + 2.6), 0.26, 0.3, dark)
    mb.beam((xl0, yo, top + 2.6), (x_end, yo, top + 2.6), 0.26, 0.3, dark)
    k = max(2, round(n / 2))
    for i in range(k + 1):
        f = i / k
        mb.box(0.22, 0.22, 2.9, dark, pos=(lerp(x_start, xl0, f), yo, z_ground + rise_total * f + 0.1))
    mb.box(0.22, 0.22, 2.6, dark, pos=(x_end - sgn * 0.15, yo, top))
    mb.beam((x_end - sgn * 0.15, yo, top + 2.6), (x_end - sgn * 0.15, 0.0, top + 2.6), 0.26, 0.3, dark)


def bay_window(mb, cx, z, w=6.0, h=6.0, depth=1.8, color="plaster_cream", frame="wood_dark",
               roof="roof_red", lit=False):
    """Oriel: a small box bay on brackets with its own roof."""
    mb.box(w, depth, h, color, pos=(cx, -depth / 2, z))
    mb.box(w + 0.4, depth + 0.2, 0.45, frame, pos=(cx, -depth / 2 - 0.1, z - 0.3))
    mb.box(w + 0.4, depth + 0.2, 0.4, frame, pos=(cx, -depth / 2 - 0.1, z + h - 0.2))
    for sx in (-1, 1):
        mb.box(0.5, 0.5, h, frame, pos=(cx + sx * (w / 2 - 0.2), -depth + 0.2, z))
        mb.beam((cx + sx * (w / 2 - 0.5), -0.05, z - 2.0), (cx + sx * (w / 2 - 0.5), -depth, z - 0.2),
                0.4, 0.4, frame)
    with mb.at(T(0, -depth, 0)):
        nw = 2 if w > 5 else 1
        ww = (w - 1.6) / nw - 0.4
        for i in range(nw):
            wx = cx - w / 2 + 0.8 + (w - 1.6) * (i + 0.5) / nw
            window(mb, wx, z + 1.5, w=ww, h=h - 3.0, frame=frame, lit=lit, sill=None, muntins=(1, 1))
    lean_to_roof(mb, cx - w / 2, w, depth, 1.6, roof, z=z + h + 0.2, og=0.5, oe=0.6, courses=2)


def arch_span(mb, x0, x1, z_spring, z_top, y0, y1, color, rise=None, segs=6, **kw):
    """Masonry above an arched opening: rectangle minus the arc below it."""
    half = (x1 - x0) / 2
    rise = half if rise is None else rise
    cx = (x0 + x1) / 2
    arc = _arc(cx, z_spring, half, rise, segs)       # right -> left
    poly = [(x0, z_top), (x0, z_spring)] + list(reversed(arc))[1:-1] + [(x1, z_spring), (x1, z_top)]
    mb.prism(poly, y0, y1, color, **kw)


# ---------------------------------------------------------------- wall styles
def _op_rects(ops, W):
    rects = []
    for o in ops:
        cx = o["u"] * W
        rects.append((cx - o["w"] / 2, cx + o["w"] / 2, o["z"], o["z"] + o["h"], o))
    return rects


def timber_wall(mb, W, H, ops, color="wood_dark", pattern="brace", corner_posts=True):
    rects = _op_rects(ops, W)
    bw = BW
    w_beam(mb, 0, bw / 2, W, bw / 2, color)
    w_beam(mb, 0, H - bw / 2, W, H - bw / 2, color)
    xs = [bw / 2, W - bw / 2]
    for x0, x1, _z0, _z1, o in rects:
        pad = 0.75 if o["t"] == "win" else 0.95
        for x in (x0 - pad, x1 + pad):
            if bw * 1.5 < x < W - bw * 1.5:
                xs.append(x)
    xs.sort()
    merged = [xs[0]]
    for x in xs[1:]:
        if x - merged[-1] > bw * 1.6:
            merged.append(x)
        elif x == xs[-1]:
            merged[-1] = x
    xs = merged

    def blocked(a, b):
        return [r for r in rects if r[0] < b and r[1] > a]

    filled = [xs[0]]
    for a, b in zip(xs[:-1], xs[1:]):
        if not blocked(a, b) and b - a > 7.0:
            k = math.ceil((b - a) / 5.5)
            filled += [lerp(a, b, i / k) for i in range(1, k)]
        filled.append(b)
    xs = filled
    for x in xs[1:-1]:
        w_beam(mb, x, bw, x, H - bw, color)
    if not corner_posts:
        w_beam(mb, xs[0], bw, xs[0], H - bw, color)
        w_beam(mb, xs[-1], bw, xs[-1], H - bw, color)
    n_panels = len(xs) - 1
    for i, (a, b) in enumerate(zip(xs[:-1], xs[1:])):
        a2, b2 = a + bw / 2, b - bw / 2
        hit = blocked(a, b)
        if hit:
            for x0, x1, z0, z1, o in hit:
                if o["t"] == "win":
                    if z0 - 0.9 > bw * 1.6:
                        w_beam(mb, a2, z0 - 0.95, b2, z0 - 0.95, color, w=bw * 0.8)
                    if z1 + 1.1 < H - bw * 1.6:
                        w_beam(mb, a2, z1 + 0.95, b2, z1 + 0.95, color, w=bw * 0.8)
            continue
        if b2 - a2 < 1.2:
            continue
        lo, hi = bw, H - bw
        if pattern == "brace":
            if i == 0:
                w_beam(mb, a2, hi, b2, lo, color, w=bw * 0.8)
            elif i == n_panels - 1:
                w_beam(mb, a2, lo, b2, hi, color, w=bw * 0.8)
            else:
                w_beam(mb, a2, H * 0.5, b2, H * 0.5, color, w=bw * 0.8)
        elif pattern == "x":
            mid = H * 0.52
            w_beam(mb, a2, mid, b2, mid, color, w=bw * 0.8)
            w_beam(mb, a2, lo, b2, mid - bw * 0.4, color, w=bw * 0.7)
            w_beam(mb, a2, mid - bw * 0.4, b2, lo, color, w=bw * 0.7)
        elif pattern == "herring":
            if i % 2:
                w_beam(mb, a2, lo, b2, hi, color, w=bw * 0.8)
            else:
                w_beam(mb, a2, hi, b2, lo, color, w=bw * 0.8)
        elif pattern == "grid":
            w_beam(mb, a2, H * 0.5, b2, H * 0.5, color, w=bw * 0.8)
        elif pattern == "k":
            mid = H * 0.5
            w_beam(mb, a2, mid, b2, mid, color, w=bw * 0.8)
            if i == 0:
                w_beam(mb, a2, mid + bw * 0.4, b2, hi, color, w=bw * 0.7)
                w_beam(mb, a2, mid - bw * 0.4, b2, lo, color, w=bw * 0.7)
            elif i == n_panels - 1:
                w_beam(mb, a2, hi, b2, mid + bw * 0.4, color, w=bw * 0.7)
                w_beam(mb, a2, lo, b2, mid - bw * 0.4, color, w=bw * 0.7)


def stone_wall(mb, W, H, ops, colors=("stone_dark", "stone_light", "stone_warm"),
               density=1.0, size=(1.3, 2.6, 0.8, 1.3), margin=0.6):
    """Scatter protruding stones over a wall, avoiding openings."""
    rects = _op_rects(ops, W)
    rng = mb.rng
    n = int(W * H / 15 * density)
    placed = []
    tries = 0
    while len(placed) < n and tries < n * 12:
        tries += 1
        sw = rng.uniform(size[0], size[1])
        sh = rng.uniform(size[2], size[3])
        x = rng.uniform(margin + sw / 2, W - margin - sw / 2)
        z = rng.uniform(0.3 + sh / 2, H - 0.4 - sh / 2)
        box = (x - sw / 2 - 0.25, x + sw / 2 + 0.25, z - sh / 2 - 0.2, z + sh / 2 + 0.2)
        if any(box[0] < r[1] + 0.9 and box[1] > r[0] - 0.9 and box[2] < r[3] + 0.9 and box[3] > r[2] - 0.9
               for r in rects):
            continue
        if any(box[0] < p[1] and box[1] > p[0] and box[2] < p[3] and box[3] > p[2] for p in placed):
            continue
        placed.append(box)
        mb.box(sw, rng.uniform(0.12, 0.24), sh, rng.choice(colors), pos=(x, -0.06, z - sh / 2),
               taper=0.9, tone=rng.uniform(-0.06, 0.06), skip=("+y",))


def plank_wall(mb, W, H, ops, color="wood_mid", spacing=1.7):
    """Board-and-batten cladding."""
    rects = _op_rects(ops, W)
    n = max(2, round(W / spacing))
    for i in range(n + 1):
        x = clamp(W * i / n, 0.2, W - 0.2)
        spans = [(0.0, H)]
        for x0, x1, z0, z1, _o in rects:
            if x0 - 0.7 < x < x1 + 0.7:
                new = []
                for a, b in spans:
                    if z0 - 0.8 > a:
                        new.append((a, min(b, z0 - 0.8)))
                    if z1 + 0.8 < b:
                        new.append((max(a, z1 + 0.8), b))
                spans = new
        for a, b in spans:
            if b - a > 0.5:
                mb.box(0.36, 0.14, b - a, color, pos=(x, -0.05, a), tone=mb.jitter(0.07) - 0.08,
                       skip=("+y",))
    mb.box(W, 0.2, 0.5, color, pos=(W / 2, -0.08, 0), tone=-0.12, skip=("+y",))


def plaster_wall(mb, W, H, ops, colors=("brick", "stone_warm")):
    """Mostly clean plaster with a few exposed bricks near the base corners."""
    rng = mb.rng
    for side in (0, 1):
        for _ in range(rng.randint(2, 4)):
            sw, sh = rng.uniform(1.0, 1.7), rng.uniform(0.5, 0.75)
            x = rng.uniform(0.8, 3.6)
            x = x if side == 0 else W - x
            z = rng.uniform(0.3, 2.6)
            if any(r[0] - 1 < x < r[1] + 1 and z < r[3] for r in _op_rects(ops, W)):
                continue
            mb.box(sw, 0.14, sh, rng.choice(colors), pos=(x, -0.05, z), tone=rng.uniform(-0.05, 0.05),
                   skip=("+y",))


# =====================================================================
# roofs
# =====================================================================
def _shape_fn(shape):
    if callable(shape):
        return shape
    if shape == "gambrel":
        return lambda t: 0.27 * (t / 0.5) if t < 0.5 else 0.27 + 0.73 * ((t - 0.5) / 0.5)
    return lambda t: t ** shape


class _RoofSide:
    """Cross-section of one roof slope. t = 0 at the ridge, 1 at the eave."""

    def __init__(self, sgn, ridge_x, halfw, oe, H, th, shape):
        self.sgn, self.ridge_x, self.total, self.H, self.th = sgn, ridge_x, halfw + oe, H, th
        self.g = _shape_fn(shape)
        self.tw = halfw / self.total
        self.gw = self.g(self.tw)

    LIFT = 0.25   # keeps the roof skin clear of corner posts and wall plates

    def p(self, t):
        return (self.ridge_x + self.sgn * self.total * t,
                self.H * (1 - self.g(t) / self.gw) + self.th + self.LIFT)

    def frame(self, t0, t1):
        """Unit slope direction and upward normal of the chord t0 -> t1."""
        a, b = self.p(t0), self.p(t1)
        dx, dz = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dz)
        dx, dz = dx / length, dz / length
        nx, nz = (-dz, dx) if dx > 0 else (dz, -dx)
        return (dx, dz), (nx, nz)

    def t_at(self, x):
        return clamp(abs(x - self.ridge_x) / self.total)


def gable_roof(mb, W, L, H, color, oe=2.0, og=1.6, th=0.55, courses=7, shape=0.85, sag=0.45,
               lip=0.26, K=5, trim="wood_dark", gable="timber", gable_color="plaster_cream",
               gable_frame="wood_dark", gable_win=None, asym=0.0, alt=None, ridge_color=None,
               gables=(True, True)):
    """Gable roof. Local frame: ridge along Y through the origin, wall top at
    z = 0, slopes fall towards +-X.  gable: 'timber' | 'plank' | 'plain' | 'stone'.
    Returns a function h(x) = height of the gable wall top at x."""
    rng = mb.rng
    og0, og1 = (og, og) if isinstance(og, (int, float)) else og   # overhang at the -Y / +Y end
    Lt = L + og0 + og1
    y_lo = -L / 2 - og0
    sides = [_RoofSide(s, asym, W / 2 - s * asym, oe, H, th, shape) for s in (1, -1)]
    ys = [y_lo + Lt * k / K for k in range(K + 1)]

    def sagz(y, t):
        s = (y - y_lo) / Lt
        return -sag * (1 - (2 * s - 1) ** 2) * (1 - 0.85 * t)

    zr = (-th * 3, H + th)
    for side in sides:
        for i in range(courses):
            ta, tb = i / courses, (i + 1) / courses
            a, b = side.p(ta), side.p(tb)
            (dx, dz), (nx, nz) = side.frame(ta, tb)
            ext = 0.2
            lp = lip * (1.35 if i == courses - 1 else 1.0)
            rings = []
            for y in ys:
                wob = rng.uniform(-0.05, 0.05)
                s0, s1 = sagz(y, ta), sagz(y, tb)
                bx, bz = b[0] + dx * ext, b[1] + dz * ext
                rings.append([
                    (a[0] - nx * th, y, a[1] - nz * th + s0),
                    (bx - nx * th, y, bz - nz * th + s1),
                    (bx + nx * (lp + wob), y, bz + nz * (lp + wob) + s1),
                    (a[0] + nx * 0.02, y, a[1] + nz * 0.02 + s0),
                ])
            ftone = []
            for _k in range(K):
                tt = rng.uniform(-0.07, 0.07)
                ftone += [tt, tt, tt, tt]
            ftone += [0, 0]
            col = color if not alt or i % 2 == 0 else alt
            mb.loft(rings, col, zr=zr, grad=(0.34, 0.66), tone=(0.025 if i % 2 else -0.02),
                    ftone=ftone)
    # ridge cap
    rc = ridge_color or color
    rings = []
    for y in ys:
        s0 = sagz(y, 0)
        z = H + th + s0
        rings.append([(asym - 0.62, y, z - 0.45), (asym + 0.62, y, z - 0.45), (asym + 0.62, y, z + 0.12),
                      (asym, y, z + 0.5), (asym - 0.62, y, z + 0.12)])
    rings[0] = [(x, y - 0.25, z) for x, y, z in rings[0]]
    rings[-1] = [(x, y + 0.25, z) for x, y, z in rings[-1]]
    mb.loft(rings, rc, tone=-0.12, grad=(0.45, 0.6))
    # barge boards
    if trim:
        for e in (-1, 1):
            if not gables[0 if e < 0 else 1]:
                continue
            ye = (y_lo + 0.02) if e < 0 else (y_lo + Lt - 0.02)
            for side in sides:
                rings = []
                steps_n = 6
                for j in range(steps_n + 1):
                    t = j / steps_n
                    p = side.p(t)
                    _d, (nx, nz) = side.frame(max(0.0, t - 0.08), min(1.0, t + 0.08))
                    up, dn = lip + 0.12, th + 0.5
                    rings.append([(p[0] + nx * up, ye - 0.22, p[1] + nz * up),
                                  (p[0] + nx * up, ye + 0.22, p[1] + nz * up),
                                  (p[0] - nx * dn, ye + 0.22, p[1] - nz * dn),
                                  (p[0] - nx * dn, ye - 0.22, p[1] - nz * dn)])
                mb.loft(rings, trim, grad=(0.42, 0.6))

    # gable walls
    def gable_h(x, y=L / 2):
        side = sides[0] if x >= asym else sides[1]
        t = side.t_at(x)
        return max(0.0, side.p(t)[1] - 1.25 * th + sagz(y, t))

    if gable:
        n = 6
        xs = [lerp(W / 2, asym, j / n) for j in range(n)] + [lerp(asym, -W / 2, j / n) for j in range(n + 1)]
        poly = [(-W / 2, 0.0), (W / 2, 0.0)] + [(x, gable_h(x)) for x in xs]
        # drop consecutive duplicates (zero height corners)
        clean = []
        for p in poly:
            if not clean or math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-4:
                clean.append(p)
        if math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) < 1e-4:
            clean.pop()
        wall_col = {"plank": "wood_mid", "stone": "stone_grey"}.get(gable, gable_color)
        if gable in ("plank", "stone") and gable_color not in ("plaster_cream",):
            wall_col = gable_color
        for e, mat in ((-1, T(-W / 2, -L / 2, 0)), (1, T(W / 2, L / 2, 0) @ R("Z", 180))):
            if not gables[0 if e < 0 else 1]:
                continue
            mb.prism(clean, e * (L / 2 - 0.7), e * L / 2, wall_col, zr=(0, H), grad=(0.47, 0.6))
            with mb.at(mat):
                # wall frame: x in [0, W]; frame x = model x + W/2 (front) / W/2 - x (back)
                gh = (lambda fx: gable_h(fx - W / 2)) if e < 0 else (lambda fx: gable_h(W / 2 - fx))
                cxf = W / 2 + (asym if e < 0 else -asym)
                _gable_detail(mb, W, gh, cxf, gable, gable_frame, gable_win, wall_col)
    return gable_h


def _gable_detail(mb, W, gh, cx, style, frame, gwin, wall_col):
    top = gh(cx)
    if style == "timber":
        w_beam(mb, 0, BW / 2, W, BW / 2, frame)
        if not gwin:
            w_beam(mb, cx, BW, cx, top - 0.4, frame)
        else:
            w_beam(mb, cx - 2.4, BW, cx - 2.4, gh(cx - 2.4) - 0.3, frame)
            w_beam(mb, cx + 2.4, BW, cx + 2.4, gh(cx + 2.4) - 0.3, frame)
            # collar beam: only where the gable is still wide enough to contain it
            zc = min(7.0, gh(cx - 2.4) - 0.7, gh(cx + 2.4) - 0.7)
            if zc > 5.6 and top - zc > 1.6:
                w_beam(mb, cx - 2.4, zc, cx + 2.4, zc, frame, w=BW * 0.8)
                w_beam(mb, cx, zc, cx, top - 0.4, frame, w=BW * 0.8)
        for s in (-1, 1):
            x = cx + s * W * 0.3
            if abs(x - cx) > 3.2 and gh(x) > 2.2:
                w_beam(mb, x, BW, x, gh(x) - 0.3, frame)
                xo = cx + s * (W / 2 - 1.0)
                if gh(xo) < 1.5:
                    w_beam(mb, x - s * BW / 2, gh(x) - 1.0, xo, BW, frame, w=BW * 0.7)
    elif style == "plank":
        n = max(2, round(W / 1.6))
        for i in range(1, n):
            x = W * i / n
            if gwin and abs(x - cx) < 1.9:
                continue
            h = gh(x) - 0.25
            if h > 0.6:
                mb.box(0.36, 0.14, h, wall_col, pos=(x, -0.05, 0), tone=mb.jitter(0.06) - 0.1,
                       skip=("+y",))
        w_beam(mb, 0, 0.3, W, 0.3, frame, w=0.6)
    elif style == "stone":
        rng = mb.rng
        for _ in range(int(W * top / 40)):
            x = rng.uniform(1.5, W - 1.5)
            z = rng.uniform(0.4, max(0.5, gh(x) - 1.6))
            if gwin and abs(x - cx) < 2.4:
                continue
            mb.box(rng.uniform(1.2, 2.2), 0.18, rng.uniform(0.7, 1.1),
                   rng.choice(("stone_dark", "stone_light", "stone_warm")), pos=(x, -0.06, z),
                   taper=0.9, skip=("+y",))
    if gwin == "round":
        window(mb, cx, min(3.0, top * 0.3), w=2.6, round_=True, frame=frame, sill=None)
    elif gwin == "small":
        window(mb, cx, 2.6, w=2.2, h=2.8, frame=frame, muntins=(1, 1), sill="wood_light")
    elif gwin == "arch":
        window(mb, cx, 2.4, w=2.4, h=3.8, frame=frame, arch=True, muntins=(1, 0), sill="wood_light")
    elif gwin == "lit":
        window(mb, cx, 2.6, w=2.2, h=2.8, frame=frame, muntins=(1, 1), sill="wood_light", lit=True)
    elif gwin == "shutter":
        window(mb, cx, 2.6, w=2.2, h=2.8, frame=frame, sill="wood_light", shutters="wood_red")
    elif gwin == "hatch":   # loading hatch with hoist beam
        door_leaf(mb, cx, 1.6, w=2.6, h=3.6, color="wood_light", frame=frame, bands=False)
        mb.beam((cx, 0, top - 1.2), (cx, -2.8, top - 1.2), 0.5, 0.5, frame)
        mb.beam((cx, -2.4, top - 1.2), (cx, -2.4, top - 2.6), 0.1, 0.1, "iron")
        mb.box(0.4, 0.4, 0.4, "iron", pos=(cx, -2.4, top - 3.0))


def hip_roof(mb, W, L, H, color, o=1.8, th=0.55, courses=6, shape=0.85, lip=0.26, alt=None):
    """Hipped roof, L >= W, ridge along Y, wall top at z = 0."""
    assert L >= W - 1e-6
    rng = mb.rng
    side = _RoofSide(1, 0.0, W / 2, o, H, th, shape)
    extra = (L - W) / 2
    zr = (-th * 3, H + th)

    def rect(x, z, nx, nz, k):
        hx = max(x + nx * k, 0.03)          # never let a ring fold through the ridge line
        hy = extra + hx
        zz = z + nz * k
        return [(hx, -hy, zz), (hx, hy, zz), (-hx, hy, zz), (-hx, -hy, zz)]

    t0 = 0.035
    for i in range(courses):
        ta = max(t0, i / courses)
        tb = (i + 1) / courses
        a, b = side.p(ta), side.p(tb)
        (dx, dz), (nx, nz) = side.frame(ta, tb)
        bx, bz = b[0] + dx * 0.2, b[1] + dz * 0.2
        lp = lip * (1.35 if i == courses - 1 else 1.0)
        rings = [rect(a[0], a[1], nx, nz, 0.02), rect(bx, bz, nx, nz, lp),
                 rect(bx, bz, nx, nz, -th), rect(a[0], a[1], nx, nz, -th)]
        ftone = [rng.uniform(-0.05, 0.05) for _ in range(16)]
        col = color if not alt or i % 2 == 0 else alt
        mb.ring_loft(rings, col, zr=zr, grad=(0.34, 0.66), tone=(0.025 if i % 2 else -0.02),
                     ftone=ftone)
    top = side.p(t0)
    zt = top[1]
    mb.beam((0, -extra - 0.5, zt), (0, extra + 0.5, zt), 1.3, 0.9, color, tone=-0.12)
    eave = side.p(1.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.beam((sx * (eave[0] + 0.1), sy * (extra + eave[0] + 0.1), eave[1] + lip),
                    (0, sy * extra, zt + 0.25), 0.75, 0.5, color, tone=-0.1)


def spire(mb, r, H, color, segs=4, courses=6, flare=0.8, lip=0.22, o=1.4, finial="brass"):
    """Pyramid / cone roof built as a stepped lathe. r = wall half-width
    (apothem). Wall top at z = 0."""
    k = 1 / math.cos(math.pi / segs)          # apothem -> corner radius
    rt = r + o
    prof = [((rt + 0.05) * k, -o * 0.45 - 0.3)]
    for i in range(courses):
        ta, tb = i / courses, (i + 1) / courses   # eave -> tip
        ra = rt * (1 - ta) ** (1 / flare) if flare != 1 else rt * (1 - ta)
        rb = rt * (1 - tb) ** (1 / flare) if flare != 1 else rt * (1 - tb)
        za, zb = H * ta - o * 0.45, H * tb - o * 0.45
        prof.append(((ra + lip) * k, za))
        if rb > 0.05:
            prof.append(((rb + lip * 0.4) * k, zb))
            prof.append((rb * k, zb - 0.02))
    prof.append((0.0, H - o * 0.45 + 0.3))
    # remove the non-monotonic artefacts of the last course
    mb.lathe(prof, color, segs=segs, phase=math.pi / segs, smooth=False, grad=(0.34, 0.68))
    if finial:
        zt = H - o * 0.45
        mb.cyl(0.14, 0.1, 1.6, finial, pos=(0, 0, zt), segs=5)
        mb.blob(0.38, finial, pos=(0, 0, zt + 1.7), level=0, noise=0.0)


def chimney(mb, x, y, z0, h, w=2.6, d=2.2, color="stone_grey", pots=1, cap="stone_dark"):
    rng = mb.rng
    with mb.at(T(x, y, z0)):
        mb.box(w, d, h, color, taper=0.86, grad=(0.36, 0.62))
        mb.box(w * 0.86 + 0.7, d * 0.86 + 0.7, 0.55, cap, pos=(0, 0, h), taper=0.92)
        for _ in range(5):
            f = rng.choice([(0, -1), (0, 1), (1, 0), (-1, 0)])
            z = rng.uniform(h * 0.3, h * 0.9)
            k = lerp(1, 0.86, z / h)
            sw, sh = rng.uniform(0.7, 1.2), rng.uniform(0.45, 0.7)
            if f[0] == 0:
                mb.box(sw, 0.2, sh, "stone_light", pos=(rng.uniform(-0.5, 0.5), f[1] * d * k / 2, z),
                       tone=rng.uniform(-0.1, 0.05))
            else:
                mb.box(0.2, sw, sh, "stone_light", pos=(f[0] * w * k / 2, rng.uniform(-0.4, 0.4), z),
                       tone=rng.uniform(-0.1, 0.05))
        for i in range(pots):
            px = 0 if pots == 1 else (i - (pots - 1) / 2) * 1.0
            mb.cyl(0.42, 0.34, 1.1, "roof_orange", pos=(px, 0, h + 0.55), segs=6)
            mb.cyl(0.26, 0.26, 0.05, "iron", pos=(px, 0, h + 1.62), segs=6)


def dormer(mb, x, y, z, rot=0, w=4.4, h=3.4, depth=5.0, roof="roof_red", wall="plaster_cream",
           frame="wood_dark", lit=False, shutters=None):
    """Gabled dormer. (x, y, z) = bottom centre of its front face, front = -Y
    before rotation."""
    with mb.at(T(x, y, z), R("Z", rot)):
        mb.box(w, depth, h, wall, pos=(0, depth / 2, 0), grad=(0.45, 0.6))
        with mb.at(T(-w / 2, 0, 0)):
            window(mb, w / 2, 0.85, w=2.1, h=2.2, frame=frame, lit=lit, sill="wood_light",
                   shutters=shutters)
            w_beam(mb, 0.2, 0, 0.2, h, frame, w=0.4)
            w_beam(mb, w - 0.2, 0, w - 0.2, h, frame, w=0.4)
        with mb.at(T(0, depth / 2, h)):
            gable_roof(mb, w, depth, w * 0.55, roof, oe=0.7, og=0.6, th=0.35, courses=3, sag=0.0,
                       lip=0.16, K=1, trim=frame, gable="plain", gable_color=wall,
                       gables=(True, False))


# =====================================================================
# wing
# =====================================================================
SIDES = ("front", "right", "back", "left")


class Wing:
    """A rectangular building volume that is stacked storey by storey."""

    def __init__(self, mb, w, d, cx=0.0, cy=0.0, rot=0.0, found=1.4, found_color="stone_grey",
                 found_deep=4.0, found_out=0.45):
        self.mb, self.w, self.d = mb, w, d
        self.m = T(cx, cy, 0) @ R("Z", rot)
        self.z = found
        self.found = found
        self.cw, self.cd = w, d          # current storey size
        self.oy = 0.0                    # current storey centre offset (jetties)
        self.ox = 0.0
        self.roof_h = 0.0
        mb.wings.append(self)
        with mb.at(self.m):
            mb.box(w + 2 * found_out, d + 2 * found_out, found + found_deep, found_color,
                   pos=(0, 0, -found_deep), taper=((w + found_out) / (w + 2 * found_out),
                                                   (d + found_out) / (d + 2 * found_out)),
                   grad=(0.3, 0.58), skip=("-z",))
            for side in SIDES:
                W = w if side in ("front", "back") else d
                with mb.at(self._wall_m(side, w + found_out * 1.4, d + found_out * 1.4, 0, 0, 0.0)):
                    stone_wall(mb, W + found_out * 1.4, found, [], density=1.6,
                               size=(1.2, 2.2, 0.5, max(0.55, found * 0.6)), margin=0.2)

    def _wall_m(self, side, w, d, ox, oy, z):
        if side == "front":
            return T(ox - w / 2, oy - d / 2, z)
        if side == "right":
            return T(ox + w / 2, oy - d / 2, z) @ R("Z", 90)
        if side == "back":
            return T(ox + w / 2, oy + d / 2, z) @ R("Z", 180)
        return T(ox - w / 2, oy + d / 2, z) @ R("Z", 270)

    def wall(self, side):
        """Context manager: wall frame of the *last built* storey."""
        z = self.z - self._last_h
        return self.mb.at(self.m, self._wall_m(side, self.cw, self.cd, self.ox, self.oy, z))

    def wall_width(self, side):
        return self.cw if side in ("front", "back") else self.cd

    def storey(self, h, style="timber", color="plaster_cream", frame="wood_dark", pattern="brace",
               jetty=0.0, openings=None, stone_colors=("stone_dark", "stone_light", "stone_warm"),
               band=None, steps_color="stone_light", stone_density=1.0):
        """Add one storey. jetty: overhang (number = front only, or dict per side).
        openings: {side: [win(...), door(...), ...]}"""
        mb = self.mb
        openings = openings or {}
        if isinstance(jetty, (int, float)):
            jetty = {"front": jetty} if jetty else {}
        jf, jb = jetty.get("front", 0), jetty.get("back", 0)
        jl, jr = jetty.get("left", 0), jetty.get("right", 0)
        self.cw += jl + jr
        self.cd += jf + jb
        self.ox += (jr - jl) / 2
        self.oy += (jb - jf) / 2
        w, d, z0 = self.cw, self.cd, self.z
        with mb.at(self.m):
            body_col = {"stone": "stone_grey", "plank": "wood_mid", "brick": "brick"}.get(style, color)
            if style in ("stone", "plank", "brick") and color != "plaster_cream":
                body_col = color
            mb.box(w, d, h, body_col, pos=(self.ox, self.oy, z0), grad=(0.42, 0.62))
            # jetty brackets + bressummer
            for side, j in (("front", jf), ("back", jb), ("left", jl), ("right", jr)):
                if j <= 0:
                    continue
                W = w if side in ("front", "back") else d
                with mb.at(self._wall_m(side, w, d, self.ox, self.oy, z0)):
                    n = max(2, round(W / 4.5))
                    for i in range(n + 1):
                        x = clamp(W * i / n, 0.5, W - 0.5)
                        mb.beam((x, j + 0.05, -1.7), (x, -0.1, 0.0), 0.5, 0.5, frame)
                    mb.box(W + 0.3, 0.5, 0.5, frame, pos=(W / 2, -0.05, -0.25), tone=-0.04)
            if band:
                mb.box(w + 0.5, d + 0.5, 0.45, band, pos=(self.ox, self.oy, z0 - 0.1))
            if style == "timber":
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        mb.box(BW + 0.1, BW + 0.1, h, frame,
                               pos=(self.ox + sx * (w / 2 - BW / 2 + BT), self.oy + sy * (d / 2 - BW / 2 + BT), z0),
                               tone=mb.jitter(0.04), grad=(0.45, 0.57))
            elif style in ("stone", "brick"):
                # quoins
                qcol = "stone_light" if style == "stone" else "stone_warm"
                nq = int(h / 1.5)
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        for q in range(nq):
                            lx, ly = (2.0, 1.2) if q % 2 else (1.2, 2.0)
                            mb.box(lx, ly, 1.1, qcol,
                                   pos=(self.ox + sx * (w / 2 - lx / 2 + 0.16), self.oy + sy * (d / 2 - ly / 2 + 0.16),
                                        z0 + 0.2 + q * 1.5), tone=mb.jitter(0.05))
            for side in SIDES:
                W = w if side in ("front", "back") else d
                ops = openings.get(side, [])
                with mb.at(self._wall_m(side, w, d, self.ox, self.oy, z0)):
                    if style == "timber":
                        timber_wall(mb, W, h, ops, frame, pattern)
                    elif style == "stone":
                        stone_wall(mb, W, h, ops, stone_colors, density=stone_density)
                    elif style == "brick":
                        stone_wall(mb, W, h, ops, ("brick", "roof_brown", "stone_warm"), density=1.5,
                                   size=(1.0, 1.6, 0.45, 0.6))
                    elif style == "plank":
                        plank_wall(mb, W, h, ops, body_col)
                    else:
                        plaster_wall(mb, W, h, ops)
                    for o in ops:
                        cx = o["u"] * W
                        if o["t"] == "win":
                            kw = {k: v for k, v in o.items() if k not in ("t", "u", "z", "w", "h")}
                            kw.setdefault("frame", frame)
                            if style in ("stone", "brick"):
                                kw.setdefault("sill", "stone_light")
                            window(mb, cx, o["z"], o["w"], o["h"], **kw)
                        else:
                            kw = {k: v for k, v in o.items() if k not in ("t", "u", "z", "w", "h")}
                            kw.setdefault("frame", frame)
                            top = door_leaf(mb, cx, o["z"], o["w"], o["h"], **kw)
                            if z0 <= self.found + 1e-6 and not o.get("no_steps"):
                                steps(mb, cx, self.found, w=o["w"] + 1.4, color=steps_color)
                            if o.get("hood"):
                                door_hood(mb, cx, top, o["w"], o["hood"], bracket=frame)
                            if o.get("lantern"):
                                wall_lantern(mb, cx + o["lantern"] * (o["w"] / 2 + 1.5), o["z"] + 5.2)
        self.z += h
        self._last_h = h
        return self

    def roof_frame(self, ridge="x"):
        """Transform to the roof frame (ridge along local Y) on top of the walls.
        Returns (context manager, W, L)."""
        mb = self.mb
        if ridge == "y":
            return mb.at(self.m, T(self.ox, self.oy, self.z)), self.cw, self.cd
        return mb.at(self.m, T(self.ox, self.oy, self.z), R("Z", 90)), self.cd, self.cw

    def gable(self, color, ridge="x", H=None, pitch=52, **kw):
        ctx, W, L = self.roof_frame(ridge)
        if H is None:
            H = (W / 2) * math.tan(math.radians(pitch))
        with ctx:
            gable_roof(self.mb, W, L, H, color, **kw)
        self.roof_h = H
        self.ridge = ridge
        self._roof = {k: kw[k] for k in ("th", "shape", "oe") if k in kw}
        return self

    def hip(self, color, H=None, pitch=48, **kw):
        long_x = self.cw >= self.cd
        ctx, W, L = self.roof_frame("x" if long_x else "y")
        if H is None:
            H = (W / 2) * math.tan(math.radians(pitch))
        with ctx:
            hip_roof(self.mb, W, L, H, color, **kw)
        self.roof_h = H
        self.ridge = "x" if long_x else "y"
        return self

    def roof_z(self, dist_from_ridge):
        """Approximate roof surface height at a horizontal distance from the
        ridge (for placing chimneys and dormers)."""
        W = self.cd if getattr(self, "ridge", "x") == "x" else self.cw
        rp = getattr(self, "_roof", {})
        side = _RoofSide(1, 0.0, W / 2, rp.get("oe", 2.0), self.roof_h, rp.get("th", 0.55),
                         rp.get("shape", 0.85))
        return self.z + side.p(side.t_at(dist_from_ridge))[1]


def wing_chimney(wg, along, dist, extra=2.6, sink=2.0, **kw):
    """Chimney through the roof of a wing. along = position along the ridge,
    dist = signed horizontal distance from the ridge."""
    z0 = wg.roof_z(abs(dist)) - sink
    top = wg.z + wg.roof_h + extra
    x, y = (along, wg.oy + dist) if wg.ridge == "x" else (wg.ox + dist, along)
    with wg.mb.at(wg.m):
        chimney(wg.mb, x, y, z0, top - z0, **kw)


def wing_dormer(wg, along, side=-1, inset=3.0, **kw):
    """Dormer on a roof slope. side -1 = front / left slope, +1 = back / right."""
    W = wg.cd if wg.ridge == "x" else wg.cw
    face = W / 2 - inset
    z = wg.roof_z(face) - 0.15
    if wg.ridge == "x":
        x, y, rot = along, wg.oy + side * face, (0 if side < 0 else 180)
    else:
        x, y, rot = wg.ox + side * face, along, (90 if side > 0 else 270)
    with wg.mb.at(wg.m):
        dormer(wg.mb, x, y, z, rot=rot, **kw)


def finish(mb, height, taper=0.035, lean=(0.0, 0.0)):
    """Global 'hand-built' deformation: walls widen slightly towards the base
    and the whole building may lean a little."""
    def fn(v):
        if v.z <= 0:
            k = 1 + taper
        else:
            k = 1 + taper * max(0.0, 1 - v.z / height)
        zz = max(v.z, 0.0)
        return (v.x * k + lean[0] * zz, v.y * k + lean[1] * zz, v.z)
    mb.deform(fn)
    # light anchors follow the same deformation
    for lt in mb.lights:
        lt["position"] = tuple(fn(type(mb.verts[0])(lt["position"])))
    # one collision box per wing: walls plus the lower part of the roof
    for wg in mb.wings:
        top = wg.z + wg.roof_h * 0.45
        with mb.at(wg.m):
            mb.collider_box((wg.ox, wg.oy, (top - 4.0) / 2), (wg.cw + 0.6, wg.cd + 0.6, top + 4.0))
    if mb.colliders and mb.collision is None:
        mb.collision = "proxy"


Wing.chimney = wing_chimney
Wing.dormer = wing_dormer
