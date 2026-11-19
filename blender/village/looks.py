"""Hair, beard and headwear of each trader.  LOOKS[role](anat, rng) -> (pieces, covered)."""
import math

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import heads as Hd
from . import outfits as O
from . import wardrobe as Wd
from .wardrobe import rgb

TAU = 2 * math.pi


class Body:
    """Collision with the whole body (braids and long hair fall over shoulders and chest)."""

    def __init__(self, anat):
        self.bvh = BVHTree.FromPolygons([Vector(v) for v in anat.V], [list(f) for f in anat.faces], all_triangles=False)

    def push_out(self, p, dist):
        hit = self.bvh.find_nearest(Vector(p))
        if hit[0] is None:
            return p
        q = Vector(p) - hit[0]
        if q.dot(hit[1]) < 0 or q.length < dist:
            return np.array(hit[0] + hit[1] * dist)
        return p


def _unit(v):
    v = np.asarray(v, float)
    return v / max(1e-9, np.linalg.norm(v))


def braid(anat, body, name, path, radius, color, rng):
    """Three interwoven strands along a path (list of points), tied at the end."""
    pts = [np.asarray(p, float) for p in path]
    # resample the path densely
    dense = []
    for a, b in zip(pts, pts[1:]):
        n = max(2, int(np.linalg.norm(b - a) / 0.02))
        for k in range(n):
            dense.append(a + (b - a) * k / n)
    dense.append(pts[-1])
    dense = [body.push_out(p, radius * 2.2) for p in dense]
    pieces = []
    total = len(dense)
    for s in range(3):
        strand = []
        for i, p in enumerate(dense):
            d = _unit(dense[min(i + 1, total - 1)] - dense[max(i - 1, 0)])
            side = _unit(np.cross(d, np.array((0.0, 1.0, 0.0))))
            up = np.cross(side, d)
            ph = TAU * s / 3 + i * 0.5
            taper = 1 - 0.35 * (i / total)
            strand.append(p + (side * math.sin(ph) * 1.0 + up * math.sin(2 * ph) * 0.45) * radius * 0.8 * taper)
        V, F = Hd._ribbon(strand, radius * 1.5, radius * 1.1)
        col = np.tile(rgb(color) * rng.uniform(0.92, 1.08), (len(V), 1))
        pieces.append(Wd.Piece(name, V, F, None, col, "hair"))
    # tie and tassel
    end = dense[-1]
    d = _unit(dense[-1] - dense[-3])
    for k in range(9):
        a = TAU * k / 9
        side = _unit(np.cross(d, np.array((0.0, 1.0, 0.0))))
        up = np.cross(side, d)
        root = end + (side * math.cos(a) + up * math.sin(a)) * radius * 0.5
        tip = root + d * 0.12 + (side * math.cos(a) + up * math.sin(a)) * 0.03
        V, F = Hd._ribbon([root, (root + tip) / 2, tip], radius * 0.7, radius * 0.4)
        pieces.append(Wd.Piece(name, V, F, None, np.tile(rgb(color), (len(V), 1)), "hair"))
    tie = []
    for k in range(3):
        tie.append(end - d * (0.025 - 0.02 * k))
    V, F = Hd._ribbon(tie, radius * 2.6, radius * 2.6)
    pieces.append(Wd.Piece(name, V, F, None, np.tile(rgb("6A4A2C"), (len(V), 1)), "leather"))
    for p in pieces:
        p.weights = Wd.nearest_weights(anat, p.verts[:1], anat.group(("spine01", "spine02", "neck", "clavicle")))
        p.weights = np.repeat(p.weights, len(p.verts), axis=0)
    return Wd.merge(name, pieces)


# ---------------------------------------------------------------- hats
def witch_hat(head, color, band_color, rng):
    z = head.eye_z + 0.15
    th, r = Hd.head_ring(head, z)
    c = head.centre
    pieces = []
    # brim: elliptical ring with a soft droop at the edge
    rows = []
    for k, (extra, dz) in enumerate(((0.01, 0.0), (0.12, -0.01), (0.26, -0.035), (0.4, -0.08))):
        rr = r + extra + 0.03 * np.sin(5 * th + 1.0) * (k / 3)
        rows.append(np.stack((c[0] + rr * np.sin(th), c[1] - rr * np.cos(th) + 0.02, np.full_like(th, z + dz)), axis=1))
    outer = np.array(rows)
    inner = outer - np.array((0, 0, 0.022))
    V, F = Wd.grid_solid(outer, inner, True)
    pieces.append(Wd.Piece("hat", V, F, Hd.head_bone(head, len(V)), np.tile(color, (len(V), 1)), "felt").orient_outwards())
    # crown: tapering, bent back at the top
    rows = []
    for k in range(14):
        u = k / 13
        rr = (r + 0.03) * (1 - u) ** 1.15 + 0.012
        zz0 = z - 0.005 + 0.78 * u - 0.12 * u ** 3
        if zz0 < head.top + 0.02:
            rr = np.maximum(rr, Hd.head_ring(head, min(zz0, head.top - 0.005))[1] + 0.035)
        bend = 0.22 * u ** 2.2
        zz = z - 0.005 + 0.78 * u - 0.12 * u ** 3
        dent = 1 - 0.06 * math.sin(u * 7)
        rows.append(np.stack((c[0] + rr * dent * np.sin(th), c[1] - rr * np.cos(th) + 0.02 + bend, np.full_like(th, zz)), axis=1))
    outer = np.array(rows)
    centre_line = outer.mean(axis=1, keepdims=True)
    inner = centre_line + (outer - centre_line) * 0.9
    V, F = Wd.grid_solid(outer, inner, True)
    pieces.append(Wd.Piece("hat", V, F, Hd.head_bone(head, len(V)), np.tile(color, (len(V), 1)), "felt").orient_outwards())
    # band
    rows = [np.stack((c[0] + (r + 0.04) * np.sin(th), c[1] - (r + 0.04) * np.cos(th) + 0.02, np.full_like(th, z + dz)), axis=1)
            for dz in (0.012, 0.075)]
    outer = np.array(rows)
    inner = np.array([np.stack((c[0] + (r + 0.02) * np.sin(th), c[1] - (r + 0.02) * np.cos(th) + 0.02, np.full_like(th, z + dz)),
                               axis=1) for dz in (0.012, 0.075)])
    V, F = Wd.grid_solid(outer, inner, True)
    pieces.append(Wd.Piece("hat", V, F, Hd.head_bone(head, len(V)), np.tile(band_color, (len(V), 1)), "leather").orient_outwards())
    return pieces            # felt, leather band and feather keep their own surface


def brim_hat(head, color, band_color, feather_color, rng):
    """Felt hat with a brim turned up at the sides and a feather in the band."""
    z = head.eye_z + 0.17
    th, r = Hd.head_ring(head, z)
    c = head.centre
    pieces = []
    rows = []
    for k, extra in enumerate((0.01, 0.1, 0.19, 0.26)):
        up = 0.07 * (k / 3) ** 2 * np.abs(np.sin(th)) ** 1.5
        rows.append(np.stack((c[0] + (r + extra) * np.sin(th), c[1] - (r + extra) * np.cos(th) + 0.015,
                              z + up - 0.012 * (k / 3)), axis=1))
    outer = np.array(rows)
    V, F = Wd.grid_solid(outer, outer - np.array((0, 0, 0.02)), True)
    pieces.append(Wd.Piece("hat", V, F, Hd.head_bone(head, len(V)), np.tile(color, (len(V), 1)), "felt").orient_outwards())
    rows = []
    for k in range(12):
        u = k / 11
        rr = (r + 0.03) * (1 - 0.12 * u ** 2) * math.cos(u * math.pi / 2) ** 0.35
        zz = z - 0.005 + 0.28 * math.sin(u * math.pi / 2) - 0.03 * u ** 4 * np.cos(th) ** 2
        zm = float(np.max(zz))
        if zm < head.top + 0.02:
            rr = np.maximum(rr, Hd.head_ring(head, min(zm, head.top - 0.005))[1] + 0.035)
        rows.append(np.stack((c[0] + rr * np.sin(th), c[1] - rr * np.cos(th) + 0.015, zz), axis=1))
    outer = np.array(rows)
    mid = outer.mean(axis=1, keepdims=True)
    V, F = Wd.grid_solid(outer, mid + (outer - mid) * 0.9, True)
    pieces.append(Wd.Piece("hat", V, F, Hd.head_bone(head, len(V)), np.tile(color, (len(V), 1)), "felt").orient_outwards())
    rows = [np.stack((c[0] + (r + 0.036) * np.sin(th), c[1] - (r + 0.036) * np.cos(th) + 0.015, np.full_like(th, z + dz)), axis=1)
            for dz in (0.01, 0.06)]
    inner = [np.stack((c[0] + (r + 0.02) * np.sin(th), c[1] - (r + 0.02) * np.cos(th) + 0.015, np.full_like(th, z + dz)), axis=1)
             for dz in (0.01, 0.06)]
    V, F = Wd.grid_solid(np.array(rows), np.array(inner), True)
    pieces.append(Wd.Piece("hat", V, F, Hd.head_bone(head, len(V)), np.tile(band_color, (len(V), 1)), "leather").orient_outwards())
    # feather on the left side, pointing up and back
    base = np.array((c[0] + r[16] + 0.04, c[1] + 0.05, z + 0.04))
    spine = [base + np.array((0.03 * u, 0.32 * u, 0.42 * u - 0.12 * u * u)) for u in np.linspace(0, 1, 12)]
    V, F = Hd._ribbon(spine, 0.012, 0.008, twist_ref=np.array((1.0, 0.0, 0.0)))
    pieces.append(Wd.Piece("hat", V, F, Hd.head_bone(head, len(V)), np.tile(rgb("6A5A40"), (len(V), 1)), "hair"))
    for i in range(2, 12):
        u = i / 11
        w = 0.07 * math.sin(math.pi * min(1, u * 1.05))
        for sgn in (-1, 1):
            p0 = spine[i]
            d = _unit(spine[min(i + 1, 11)] - spine[i - 1])
            side = _unit(np.cross(d, np.array((1.0, 0.0, 0.0)))) * sgn
            pts = [p0, p0 + side * w * 0.5 + d * 0.02, p0 + side * w + d * 0.05]
            V, F = Hd._ribbon(pts, 0.028, 0.004, twist_ref=np.array((1.0, 0.0, 0.0)))
            tone = feather_color * (0.85 + 0.25 * ((i % 3) / 2))
            pieces.append(Wd.Piece("hat", V, F, Hd.head_bone(head, len(V)), np.tile(np.clip(tone, 0, 1), (len(V), 1)), "hair"))
    return pieces            # felt, leather band and feather keep their own surface


def flat_cap(head, color, rng):
    z = head.eye_z + 0.12
    th, r = Hd.head_ring(head, z)
    c = head.centre
    rows = []
    for k in range(10):
        u = k / 9
        puff = 0.035 + 0.07 * math.sin(math.pi * min(1, u * 1.3)) * (1 - 0.4 * u)
        rr = (r + puff) * math.cos(u * math.pi / 2 * 0.98)
        zz = z + (head.top - z + 0.05) * math.sin(u * math.pi / 2)
        rows.append(np.stack((c[0] + rr * np.sin(th), c[1] - rr * np.cos(th) - 0.04 * u, np.full_like(th, zz)), axis=1))
    outer = np.array(rows)
    mid = outer.mean(axis=1, keepdims=True)
    V, F = Wd.grid_solid(outer, mid + (outer - mid) * 0.92, True)
    pieces = [Wd.Piece("cap", V, F, Hd.head_bone(head, len(V)), np.tile(color, (len(V), 1)), "felt").orient_outwards()]
    # visor
    vt = np.linspace(-1.1, 1.1, 20)
    rows = []
    for k, ext in enumerate((0.0, 0.08, 0.15)):
        rr = np.interp(vt % TAU, th, r, period=TAU) + 0.03 + ext * np.cos(vt * 0.9)
        rows.append(np.stack((c[0] + rr * np.sin(vt), c[1] - rr * np.cos(vt), np.full_like(vt, z + 0.01 - 0.05 * ext / 0.15)), axis=1))
    outer = np.array(rows)
    V, F = Wd.grid_solid(outer, outer - np.array((0, 0, 0.018)), False)
    pieces.append(Wd.Piece("cap", V, F, Hd.head_bone(head, len(V)), np.tile(color * 0.85, (len(V), 1)), "felt").orient_outwards())
    return [Wd.merge("cap", pieces)]


def goggles(head, frame_color, lens_color, strap_color):
    z = head.eye_z + 0.16
    th, r = Hd.head_ring(head, z)
    c = head.centre
    pieces = []
    rows = [np.stack((c[0] + (r + 0.05) * np.sin(th), c[1] - (r + 0.05) * np.cos(th), np.full_like(th, z + dz)), axis=1)
            for dz in (-0.025, 0.025)]
    inner = [np.stack((c[0] + (r + 0.035) * np.sin(th), c[1] - (r + 0.035) * np.cos(th), np.full_like(th, z + dz)), axis=1)
             for dz in (-0.025, 0.025)]
    V, F = Wd.grid_solid(np.array(rows), np.array(inner), True)
    pieces.append(Wd.Piece("goggles", V, F, Hd.head_bone(head, len(V)), np.tile(strap_color, (len(V), 1)), "leather")
                  .orient_outwards())
    for sx in (1, -1):
        ang = sx * 0.42
        rr = float(np.interp(ang % TAU, th, r, period=TAU)) + 0.05
        centre = np.array((c[0] + rr * math.sin(ang), c[1] - rr * math.cos(ang), z))
        axis = _unit(np.array((math.sin(ang), -math.cos(ang), 0.25)))
        tilt = _frame_z(axis)
        prof = [(0.0, 0.0), (0.075, 0.0), (0.082, 0.02), (0.07, 0.065), (0.0, 0.065)]
        p = Hd.lathe_piece(head, "goggles", prof, centre, frame_color, "metal", segs=24, tilt=tilt)
        pieces.append(p)
        lens = Hd.lathe_piece(head, "goggles", [(0.0, 0.066), (0.062, 0.066), (0.06, 0.072), (0.0, 0.075)], centre,
                              lens_color, "glass", segs=24, tilt=tilt)
        pieces.append(lens)
    # separate pieces: strap (leather), frames (metal) and lenses (glass) keep their own surface
    return pieces


def _frame_z(axis):
    """Rotation turning +Z into axis."""
    z = _unit(axis)
    x = _unit(np.cross(np.array((0.0, 0.0, 1.0)), z)) if abs(z[2]) < 0.99 else np.array((1.0, 0.0, 0.0))
    y = np.cross(z, x)
    return np.column_stack((x, y, z))


def hood(anat, F, head, color, rng):
    """Hood with cowl: the head, neck and shoulders pushed out, an oval opening for the face."""
    a = anat
    fc = np.array((0.0, head.front_y, head.eye_z - 0.1))
    d = np.hypot(F.x / 0.24, (F.z - fc[2]) / 0.36)
    field = np.minimum(F.z - (a.shoulder_z - 0.12), 0.3 - F.w_arm - F.w_hand)
    field = np.where(F.y < head.centre[1] - 0.04, np.minimum(field, d - 1), field)
    off = 0.06 + 0.05 * np.clip((F.z - head.eye_z + 0.3) / 0.6, 0, 1) + 0.012 * np.sin(7 * F.phi + 6 * F.z) \
        + 0.03 * np.clip((a.neck_z + 0.1 - F.z) / 0.3, 0, 1)
    return Wd.fitted(a, "hood", field, off, color, "cloth")


# ---------------------------------------------------------------- per trader
def _base(anat, role, rng, brow_thick=1.0):
    head = Hd.Head(anat)
    col = O.COLORS[role]
    pieces = [Hd.eyes(head, col["iris"]), Hd.lashes(head, "2A1D17"),
              Hd.brows(head, col.get("beard", col["hair"]), rng, brow_thick)]
    return head, pieces


def selma(anat, rng):
    head, out = _base(anat, "selma", rng)
    col = O.COLORS["selma"]
    field = Hd.scalp_field(head, 0.11, 0.05, head.eye_z - 0.26)
    out.append(Hd.coily_hair(head, "hair", field, col["hair"], rng, height=0.024, curl=0.012, density=3400,
                             contrast=0.35, relief=0.35))
    body = Body(anat)
    for sx in (1, -1):
        path = [np.array((sx * head.half_w * 0.75, head.centre[1] + 0.12, head.eye_z - 0.16)),
                np.array((sx * 0.2, head.centre[1] + 0.02, anat.neck_z - 0.02)),
                np.array((sx * 0.22, -0.5, anat.shoulder_z - 0.15)),
                np.array((sx * 0.19, -0.6, anat.shoulder_z - 0.62))]
        out.append(braid(anat, body, "braids", path, 0.03, col["hair"], rng))
    out += witch_hat(head, rgb(col["hat"]), rgb(col["band"]), rng)
    return out, field > 0.02


def nyra(anat, rng):
    head, out = _base(anat, "nyra", rng, 0.9)
    col = O.COLORS["nyra"]
    F = O.Fields(anat)
    field = Hd.scalp_field(head, 0.1, 0.04, head.eye_z - 0.3)
    cap = Hd.hair_cap(head, "hair", field, rgb(col["hair"]))
    out.append(Hd.coily_hair(head, "hair", field, col["hair"], rng, height=0.02, curl=0.01, density=3000,
                             contrast=0.35, relief=0.35))
    body = Body(anat)
    # long hair from the sides and the back of the head, the face stays free
    sides = lambda P: (np.abs(head.angle(P)) > 0.95) & (P[:, 2] < head.eye_z + 0.2)
    roots = Hd._roots(cap, 420, rng, keep=sides)

    def fall(p, t):
        hit = head.bvh.find_nearest(Vector(p))
        n = np.array(hit[1]) if hit[0] is not None else np.zeros(3)
        out = np.array((np.sign(p[0]) * 0.22, 0.18, -1.0))          # down and a little back, behind the shoulders
        return out + n * 0.35 * (1 - t)

    def length(p, r):
        return r.uniform(0.8, 1.05)
    hair = Hd.strands(head, "hair", roots, fall, length, col["hair"], rng, width=0.036, thickness=0.028, steps=12,
                      bone_fn=None)
    hair.verts = np.array([body.push_out(v, 0.03) if v[2] < anat.neck_z else v for v in hair.verts])
    hair.weights = Wd.nearest_weights(anat, hair.verts, anat.group(("head", "neck", "spine01", "spine02", "clavicle")))
    out.append(hair)
    out.append(hood(anat, F, head, rgb(col["cloak"]), rng))
    return out, field > 0.02


def lio(anat, rng):
    head, out = _base(anat, "lio", rng, 1.1)
    col = O.COLORS["lio"]
    # short coily hair as a volume (strands of flat ribbons read as torn paper close up)
    field = Hd.scalp_field(head, 0.13, 0.06, head.eye_z - 0.2)
    out.append(Hd.coily_hair(head, "hair", field, col["hair"], rng, height=0.06, curl=0.024))
    out += goggles(head, rgb(col["brass"]), rgb(col["lens"]), rgb("3A2A1E"))
    return out, field > 0.02


def aron(anat, rng):
    head, out = _base(anat, "aron", rng, 1.25)
    col = O.COLORS["aron"]
    field = Hd.scalp_field(head, 0.12, 0.05, head.eye_z - 0.22)
    out.append(Hd.coily_hair(head, "hair", field, col["hair"], rng, height=0.025, curl=0.012, density=3000,
                             contrast=0.6, relief=0.6))
    # beard: jaw, chin, cheeks and upper lip; the lips stay free
    V = anat.V
    m = head.mouth
    phi = head.angle(V)
    lips = np.hypot((V[:, 0] - m[0]) / 0.09, (V[:, 2] - m[2]) / 0.042) - 1
    cheek_line = (head.eye_z - 0.19) - V[:, 2] - 0.1 * np.clip(np.abs(phi) - 0.6, 0, 1)
    beard_field = np.minimum(cheek_line, lips)
    beard_field = np.where(np.abs(phi) < 1.75, beard_field, -1.0)
    beard_field = np.minimum(beard_field, V[:, 2] - (head.chin - 0.12))
    beard_field = np.where(head.mask | (anat.weight(("neck",)) > 0.4), beard_field, -1.0)
    moustache = np.minimum(np.minimum(m[2] + 0.06 - V[:, 2], V[:, 2] - (m[2] + 0.026)), 0.1 - np.abs(V[:, 0] - m[0]))
    moustache = np.where((V[:, 1] < head.centre[1] - 0.1) & head.mask, moustache, -1.0)
    # a full beard as a volume (curly, thicker at the chin, thin at the edges); its skin weights come from
    # the face, so it moves with the jaw and the mouth corners
    out.append(Hd.coily_hair(head, "beard", np.maximum(beard_field, moustache), col["beard"], rng, height=0.012,
                             curl=0.006, density=9000, contrast=0.35, relief=0.35))
    out += flat_cap(head, rgb(col["cap"]), rng)
    return out, field > 0.02


def esme(anat, rng):
    head, out = _base(anat, "esme", rng)
    col = O.COLORS["esme"]
    field = Hd.scalp_field(head, 0.12, 0.05, head.eye_z - 0.24)
    out.append(Hd.coily_hair(head, "hair", field, col["hair"], rng, height=0.022, curl=0.011, density=3600,
                             contrast=0.35, relief=0.35))
    gather = np.array((0.0, head.back_y + 0.03, head.eye_z + 0.02))
    # ponytail
    body = Body(anat)
    tail = []
    for k in range(70):
        a, rr = rng.uniform(0, TAU), 0.035 * math.sqrt(rng.random())
        root = gather + np.array((rr * math.cos(a), 0.01, rr * math.sin(a)))
        pts = [root]
        p = root.copy()
        for i in range(1, 11):
            u = i / 10
            p = p + np.array((0.012 * math.sin(u * 5 + a), 0.06 * (1 - u) + 0.01, -0.075))
            p = body.push_out(p, 0.03)
            pts.append(p)
        V, F = Hd._ribbon(pts, 0.04 * rng.uniform(0.8, 1.2), 0.026)
        c = rgb(col["hair"]) * rng.uniform(0.9, 1.1)
        cols = np.array([np.clip(c * (0.85 + 0.3 * ((i // 4) / 10)), 0, 1) for i in range(len(V))])
        tail.append(Wd.Piece("hair", V, F, None, cols, "hair"))
    for p in tail:
        p.weights = Wd.nearest_weights(anat, p.verts, anat.group(("head", "neck", "spine01", "spine02")))
    out += tail
    ring = Hd.lathe_piece(head, "hair_tie", [(0.03, -0.02), (0.05, -0.02), (0.05, 0.02), (0.03, 0.02)], gather,
                          rgb("4A3020"), "leather", segs=16, tilt=_frame_z(np.array((0.0, 1.0, -0.4))))
    out.append(ring)
    out += brim_hat(head, rgb(col["hat"]), rgb(col["belt"]), rgb(col["feather"]), rng)
    return out, field > 0.02


LOOKS = {"selma": selma, "nyra": nyra, "lio": lio, "aron": aron, "esme": esme}
