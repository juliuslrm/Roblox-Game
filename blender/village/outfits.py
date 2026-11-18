"""What each trader wears.  OUTFITS[role](anat) -> (pieces, covered): covered marks the body vertices
hidden under clothes (their skin is not exported).

Garment edges are zero lines of smooth fields (see wardrobe.fitted): height, position along an arm or
leg, distance from the middle of the chest, summed skin weights of a body part.
"""
import math

import numpy as np

from . import wardrobe as Wd
from .wardrobe import rgb

TAU = 2 * math.pi

COLORS = {
    "selma": dict(skin="E2B497", dress="4E7A4C", trim="2F4D33", apron="E8DEC8", boots="4A3426", hair="9A4A22", hat="3E6B44",
                  band="7A5A2E", belt="5A3E26", lips="B86A60", iris="5B7A3E"),
    "nyra": dict(skin="E6C2AE", robe="5B3E6E", trim="3A3550", cloak="3C4258", boots="2E2E33", hair="D9D6D0", belt="2E2A38",
                 lips="9E6872", iris="6C5A8A"),
    "lio": dict(skin="8D5A3B", shirt="4A6A95", vest="6B4428", trousers="4A4F5A", boots="3B2A20", belt="2E2018",
                brass="B08D3C", hair="1E1612", lips="6E4034", iris="3A2A1E", lens="8FB9C8"),
    "aron": dict(skin="D9A988", shirt="9E3B2E", apron="6A3E26", trousers="4C4A48", boots="2A2522", hair="4A3022",
                 beard="5A3A28", cap="3D3A36", lips="A8665A", iris="4A6070", belt="3A2618", brass="A78A44"),
    "esme": dict(skin="E8BC9A", tunic="2F7A74", vest="7A5235", trousers="3F5E3A", boots="7A3E2A", hair="8E3A1E",
                 hat="6A4A2C", feather="D8C8A8", belt="4A3020", lips="B26458", iris="4E7048", lace="D9C9A0", brass="B08D3C"),
}


def C(role, key):
    return rgb(COLORS[role][key])


class Fields:
    """Smooth scalar fields over the body vertices."""

    def __init__(self, anat):
        self.a = anat
        V = anat.V
        self.x, self.y, self.z = V[:, 0], V[:, 1], V[:, 2]
        self.w_arm = anat.weight(("upperarm", "lowerarm"))
        self.w_hand = anat.weight(("wrist",))
        self.w_head = anat.weight(("head", "neck02"))
        self.w_shin = anat.weight(("lowerleg",))
        self.w_foot = anat.weight(("foot",))
        self.w_thigh = anat.weight(("upperleg", "pelvis"))
        self.arm_t = anat.arm_t()
        self.leg_t = anat.leg_t()
        self.arm_angle = anat.limb_angle("arm")
        self.leg_angle = anat.limb_angle("leg")
        self.phi = np.arctan2(self.x, -self.y)                 # around the body, 0 at the front

    def fill(self, amount):
        """Offset that lets cloth span the hollows of the torso (see wardrobe.hull_fill)."""
        if not hasattr(self, "_fill"):
            torso = self.a.in_body & (self.w_arm + self.w_hand + self.w_head < 0.3) & (self.z > self.a.hip_z - 0.3)
            self._fill = Wd.hull_fill(self.a, torso)
        return self._fill * amount

    def sleeve(self, cuff):
        return np.where(self.w_arm + self.w_hand > 0.3, cuff - self.arm_t, 1.0)

    def leg(self, end):
        return np.where(self.w_thigh + self.w_shin + self.w_foot > 0.3, end - self.leg_t, 1.0)


def _min(*fields):
    out = fields[0]
    for f in fields[1:]:
        out = np.minimum(out, f)
    return out


# ---------------------------------------------------------------- garment builders
def shirt(anat, F, name, color, cuff, bottom_z, neck=0.05, scoop=0.0, vneck=0.0, ease=0.022, sleeve_ease=0.035,
          flare=0.0, fold=0.014, kind="cloth", trim=None):
    a = anat
    def field(m):
        f = _min(F.z - (bottom_z + m), (a.neck_z + neck - m) - F.z, 0.45 - F.w_hand - F.w_head,
                 F.sleeve(cuff - m * 0.4))
        if scoop:                     # rounded neckline at the front
            d = np.hypot(F.x / scoop, np.maximum(0, F.z - (a.neck_z - scoop * 0.8)) / (scoop * 0.8))
            front = F.y < -0.02
            f = np.where(front & (F.z > a.neck_z - scoop * 0.8), np.minimum(f, d - 1 - m), f)
        if vneck:
            top = a.neck_z + 0.02
            depth = vneck
            w = 0.11 * np.clip((F.z - (top - depth)) / depth, 0, 1)
            front = (F.y < -0.02) & (F.z > top - depth)
            f = np.where(front, np.minimum(f, np.abs(F.x) - w - m), f)
        return f
    off = np.full(len(a.V), ease)
    arm = F.w_arm > 0.3
    t = F.arm_t
    off[arm] = (ease + sleeve_ease * t + flare * np.clip((t - 0.6) / 0.4, 0, 1) ** 2
                + Wd.folds(F.arm_angle, t, 6, fold, (0.5, cuff - 0.07), 0.07))[arm]
    env = np.clip((a.neck_z - 0.55 - F.z) / 0.5, 0, 1) * np.clip((F.z - bottom_z) / 0.25, 0, 1)
    off[~arm] += (fold * env * (0.5 + 0.5 * np.sin(9 * F.phi + 2 * F.z)))[~arm]
    off += F.fill(0.9)
    cols = None
    if trim is not None:              # darker band at cuffs
        cols = np.tile(color, (len(a.V), 1))
        cols[arm & (t > cuff - 0.05)] = trim
    piece = Wd.fitted(a, name, field(0.0), off, color, kind, colors=cols, relax=8, relax_mask=~arm)
    return piece, field(0.035) > 0


def trousers(anat, F, name, color, top_z, end_t, ease=0.03, fold=0.016):
    a = anat
    def field(m):
        return _min((top_z - m) - F.z, F.leg(end_t - m * 0.5), 0.4 - F.w_arm - F.w_hand)
    off = np.full(len(a.V), ease)
    legs = (F.w_thigh + F.w_shin) > 0.3
    t = F.leg_t
    off[legs] = (ease + 0.025 * np.clip(1 - np.abs(t - 0.35) / 0.35, 0, 1)
                 + Wd.folds(F.leg_angle, t, 5, fold, (0.5, end_t - 0.05), 0.08))[legs]
    return Wd.fitted(a, name, field(0.0), off, color, "cloth"), field(0.035) > 0


def boots(anat, F, name, color, top_t, sole="2A211B", ease=0.03):
    """Boots: for every horizontal slice of the foot and lower leg the convex outline plus ease, so the
    toe box, instep and shaft come out smooth like a real boot on its last; a welt and a sole at the
    bottom.  The trousers end inside the shaft."""
    a = anat
    pieces = []
    seg = 64
    th = np.linspace(0, TAU, seg, endpoint=False)
    U = np.stack((np.sin(th), -np.cos(th)), axis=1)
    top_z = float(np.median(a.V[np.abs(F.leg_t - top_t) < 0.01, 2]))
    for side, sx in (("L", 1.0), ("R", -1.0)):
        leg = a.in_body & ((F.w_shin + F.w_foot + F.w_thigh) > 0.3) & ((F.x > 0) == (sx > 0))
        P = a.V[leg]
        floor = P[:, 2].min()
        ankle = float(np.asarray(a.body.bones["foot." + side][0])[2])
        foot = leg & (F.z < ankle + 0.06)
        Pf = a.V[foot]
        sole_h = 0.05
        # foot: cross-sections along the foot (perpendicular to Y), convex outline in X-Z plus ease
        y_heel, y_toe = Pf[:, 1].max(), Pf[:, 1].min()
        ys = np.linspace(y_heel - 0.02, y_toe + 0.02, 18)
        ang = np.linspace(0, TAU, 48, endpoint=False)
        Ux = np.stack((np.cos(ang), np.sin(ang)), axis=1)
        rings = []
        for k, y in enumerate(ys):
            pts = Wd.slice_points(a, foot, y, pad=0.02, axis=1)
            if len(pts) < 3:
                continue
            c = np.array((pts[:, 0].mean(), (pts[:, 2].min() + pts[:, 2].max()) / 2))
            r = ((pts[:, [0, 2]] - c) @ Ux.T).max(axis=0) + ease + 0.008
            ring = np.stack((c[0] + r * np.cos(ang), np.full_like(ang, y), c[1] + r * np.sin(ang)), axis=1)
            ring[:, 2] = np.maximum(ring[:, 2], floor + sole_h - 0.005)
            rings.append(ring)
        # rounded heel and toe caps
        for end, ref, step in ((0, rings[0], 0.035), (len(rings), rings[-1], -0.035)):
            c = ref.mean(axis=0)
            for frac, dy in ((0.75, step * 0.55), (0.4, step * 0.9), (0.04, step * 1.05)):
                cap = c + (ref - c) * frac + np.array((0.0, dy, 0.0))
                cap[:, 2] = np.maximum(cap[:, 2], floor + sole_h - 0.005)
                rings.insert(end, cap) if end == 0 else rings.append(cap)
        outer = np.array(rings)
        ctr = outer.mean(axis=1, keepdims=True)
        verts, faces = Wd.grid_solid(outer, ctr + (outer - ctr) * 0.85, True)
        W = Wd.fixed_weights(a, len(verts), "foot." + side)
        pieces.append(Wd.Piece(name, verts, faces, W, np.tile(color, (len(verts), 1)), "leather").orient_outwards())
        # shaft: horizontal outlines from below the ankle up to the boot top
        zs = np.linspace(ankle - 0.1, top_z, 20)
        outer = []
        for z in zs:
            band = Wd.slice_points(a, leg, z, pad=0.03)
            c = band[:, :2].mean(axis=0)
            u = (z - zs[0]) / max(0.01, top_z - zs[0])
            r = ((band[:, :2] - c) @ U.T).max(axis=0) + ease + 0.035 * min(1.0, u * 3) + 0.02 * u ** 2
            if z < ankle + 0.1:                         # the lower end stays inside the foot part
                r = r - 0.03 * (1 - (z - zs[0]) / (ankle + 0.1 - zs[0]))
            outer.append(np.stack((c[0] + r * np.sin(th), c[1] - r * np.cos(th), np.full_like(th, z)), axis=1))
        outer = np.array(outer)
        ctr = outer.mean(axis=1, keepdims=True)
        verts, faces = Wd.grid_solid(outer, ctr + (outer - ctr) * 0.9, True)
        W = Wd.nearest_weights(a, verts, leg)
        pieces.append(Wd.Piece(name, verts, faces, W, np.tile(color, (len(verts), 1)), "leather").orient_outwards())
        # sole: footprint outline, extruded
        low = Pf[Pf[:, 2] < floor + 0.1]
        c = low[:, :2].mean(axis=0)
        r = ((low[:, :2] - c) @ U.T).max(axis=0) + ease - 0.004
        sole_rings = [np.stack((c[0] + r * f * np.sin(th), c[1] - r * f * np.cos(th), np.full_like(th, z)), axis=1)
                      for f, z in ((0.97, floor), (1.0, floor + 0.012), (1.0, floor + sole_h))]
        verts, faces = cap_solid(sole_rings)
        W = Wd.fixed_weights(a, len(verts), "foot." + side)
        pieces.append(Wd.Piece(name + "_sole", verts, faces, W, np.tile(rgb(sole), (len(verts), 1)), "leather")
                      .orient_outwards())
    def field(m):
        return np.where((F.w_shin + F.w_foot) > 0.3, (top_z - m) - F.z, -1.0)
    return Wd.merge(name, pieces), field(0.04) > 0


def cap_solid(rings):
    """Closed prism through stacked rings (each (n, 3)), flat caps."""
    n = len(rings[0])
    verts = np.vstack(rings)
    faces = []
    for r in range(len(rings) - 1):
        for c in range(n):
            a, b = r * n + c, r * n + (c + 1) % n
            faces.append((a, b, b + n, a + n))
    faces.append(tuple(reversed(range(n))))
    top = (len(rings) - 1) * n
    faces.append(tuple(range(top, top + n)))
    return verts, faces


def band(anat, name, z, height, color, kind="leather", ease=0.035, thickness=0.02, bone="spine05", buckle=None):
    """Belt or waist band: a ring around the body at height z."""
    mask = anat.group(("spine", "root", "pelvis", "upperleg"))
    zs = np.linspace(z - height / 2, z + height / 2, 4)
    th, rings = Wd.support_rings(anat, zs, mask, 64)
    r = np.max([rr for _, rr in rings], axis=0) + ease
    c = rings[1][0]
    outer = np.array([np.stack((c[0] + r * np.sin(th), c[1] - r * np.cos(th), np.full_like(th, zz)), axis=1) for zz in zs])
    inner = np.array([np.stack((c[0] + (r - thickness) * np.sin(th), c[1] - (r - thickness) * np.cos(th),
                                np.full_like(th, zz)), axis=1) for zz in zs])
    verts, faces = Wd.grid_solid(outer, inner, True)
    pieces = [Wd.Piece(name, verts, faces, Wd.fixed_weights(anat, len(verts), bone), np.tile(color, (len(verts), 1)), kind)
              .orient_outwards()]
    if buckle is not None:
        front = np.array((c[0], c[1] - r[0] - 0.008, z))
        bw, bh, bd = height * 1.1, height * 1.15, 0.022
        frame = []
        for (x0, x1, z0, z1) in ((-bw / 2, bw / 2, bh / 2 - 0.016, bh / 2), (-bw / 2, bw / 2, -bh / 2, -bh / 2 + 0.016),
                                 (-bw / 2, -bw / 2 + 0.016, -bh / 2, bh / 2), (bw / 2 - 0.016, bw / 2, -bh / 2, bh / 2)):
            frame.append(box(front + np.array(((x0 + x1) / 2, 0, (z0 + z1) / 2)), (x1 - x0, bd, z1 - z0)))
        bv = np.vstack([v for v, _ in frame])
        bf, off = [], 0
        for v, f in frame:
            bf += [tuple(i + off for i in fc) for fc in f]
            off += len(v)
        pieces.append(Wd.Piece(name + "_buckle", bv, bf, Wd.fixed_weights(anat, len(bv), bone),
                               np.tile(buckle, (len(bv), 1)), "metal"))
    return Wd.merge(name, pieces)


def box(centre, size):
    cx, cy, cz = centre
    hx, hy, hz = (s / 2 for s in size)
    v = np.array([(cx + sx * hx, cy + sy * hy, cz + sz * hz) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)])
    f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return v, f


def bib(anat, F, name, color, z0, z1, half_width, offset, kind="cloth"):
    """Front panel on the chest (apron bib): between heights z0..z1, |x| < half_width, front only."""
    field = _min(F.z - z0, z1 - F.z, half_width - np.abs(F.x), -F.y - 0.02, 0.4 - F.w_arm - F.w_hand - F.w_head)
    return Wd.fitted(anat, name, field, np.full(len(anat.V), offset) + F.fill(1.0), color, kind, relax=14)


def legs_under(anat, F, z_hem, z_top):
    """Body vertices hidden under a skirt from z_top down to z_hem."""
    return (F.z > z_hem + 0.06) & (F.z < z_top) & ((F.w_thigh + F.w_shin + anat.weight(("spine05", "root"))) > 0.5)


def cloak(anat, name, z_top, z_hem, color, theta=(1.25, TAU - 1.25), ease=0.07, flare=0.25):
    """A cape hanging from the shoulders down the back."""
    a = anat
    rows, seg = 22, 48
    zs = np.linspace(z_top, z_hem, rows)
    mask = a.group(("spine", "clavicle", "upperarm", "lowerarm", "root", "pelvis", "upperleg", "lowerleg", "neck01"))
    th_full, rings = Wd.support_rings(a, zs, mask, 96, centre=np.array((0.0, 0.0)))
    th = np.linspace(theta[0], theta[1], seg)
    outer, inner, prev = [], [], None
    for k, (z, (c, r)) in enumerate(zip(zs, rings)):
        u = k / (rows - 1)
        rr = np.interp(th % TAU, th_full, r, period=TAU)
        if prev is not None:
            rr = np.maximum(rr, prev)
        prev = rr
        rad = rr + ease + flare * u ** 1.5 + 0.03 * u * np.sin(9 * th)
        outer.append(np.stack((rad * np.sin(th), -rad * np.cos(th), np.full_like(th, z)), axis=1))
        inner.append(np.stack(((rad - 0.022) * np.sin(th), -(rad - 0.022) * np.cos(th), np.full_like(th, z)), axis=1))
    verts, faces = Wd.grid_solid(np.array(outer), np.array(inner), False)
    torso = a.group(("spine01", "spine02", "clavicle", "neck01"))
    near = Wd.nearest_weights(a, verts, torso)
    low = Wd.fixed_weights(a, len(verts), "spine05")
    u = np.clip((z_top - verts[:, 2]) / max(0.01, (z_top - z_hem)) * 2.2, 0, 1)[:, None]
    W = near * (1 - u) + low * u
    return Wd.Piece(name, verts, faces, W, np.tile(color, (len(verts), 1)), "cloth").orient_outwards()


# ---------------------------------------------------------------- per trader
def selma(anat):
    F, a, role = Fields(anat), anat, "selma"
    out, cov = [], np.zeros(len(anat.V), dtype=bool)
    p, c = shirt(a, F, "dress", C(role, "dress"), cuff=0.95, bottom_z=a.waist_z - 0.2, scoop=0.16, trim=C(role, "trim"))
    out.append(p)
    cov |= c
    hem = 0.16
    out.append(Wd.skirt(a, "skirt", a.waist_z - 0.12, hem, C(role, "dress"), ease_top=0.03, flare=0.42, fold_amp=0.035))
    cov |= legs_under(a, F, hem, a.waist_z)
    out.append(Wd.skirt(a, "apron", a.waist_z - 0.1, 0.62, C(role, "apron"), ease_top=0.06, flare=0.4, fold_amp=0.02,
                        theta_range=(-1.15, 1.15), thickness=0.012, extra=0.0, fold_count=7))
    out.append(bib(a, F, "apron_bib", C(role, "apron"), a.waist_z - 0.12, a.neck_z - 0.42, 0.2, 0.05))
    out.append(band(a, "apron_tie", a.waist_z - 0.06, 0.07, C(role, "apron"), kind="cloth", ease=0.07))
    p, c = boots(a, F, "boots", C(role, "boots"), top_t=0.86)
    out.append(p)
    cov |= c
    return out, cov


def nyra(anat):
    F, a, role = Fields(anat), anat, "nyra"
    out, cov = [], np.zeros(len(anat.V), dtype=bool)
    p, c = shirt(a, F, "robe", C(role, "robe"), cuff=0.9, bottom_z=a.waist_z - 0.2, neck=0.1, flare=0.12,
                 trim=C(role, "trim"))
    out.append(p)
    cov |= c
    hem = 0.05
    out.append(Wd.skirt(a, "skirt", a.waist_z - 0.12, hem, C(role, "robe"), ease_top=0.035, flare=0.5, fold_amp=0.04))
    cov |= legs_under(a, F, hem, a.waist_z)
    out.append(band(a, "sash", a.waist_z - 0.04, 0.11, C(role, "belt"), kind="cloth", ease=0.06))
    out.append(cloak(a, "cloak", a.shoulder_z + 0.12, 0.7, C(role, "cloak"), flare=0.62))
    p, c = boots(a, F, "boots", C(role, "boots"), top_t=0.9)
    out.append(p)
    cov |= c
    return out, cov


def lio(anat):
    F, a, role = Fields(anat), anat, "lio"
    out, cov = [], np.zeros(len(anat.V), dtype=bool)
    p, c = shirt(a, F, "shirt", C(role, "shirt"), cuff=0.94, bottom_z=a.waist_z - 0.42, vneck=0.32)
    out.append(p)
    cov |= c
    p, c = trousers(a, F, "trousers", C(role, "trousers"), top_z=a.waist_z - 0.08, end_t=0.9)
    out.append(p)
    cov |= c
    p, c = boots(a, F, "boots", C(role, "boots"), top_t=0.74)
    out.append(p)
    cov |= c
    vest = _min(0.35 - F.w_arm - F.w_hand - F.w_head, F.z - (a.waist_z - 0.3), (a.neck_z - 0.02) - F.z,
                np.where(F.y < 0, np.abs(F.x) - 0.08, 1.0))
    out.append(Wd.fitted(a, "vest", vest, np.full(len(a.V), 0.05) + F.fill(1.0), C(role, "vest"), "leather", relax=14))
    out.append(band(a, "belt", a.waist_z - 0.14, 0.085, C(role, "belt"), ease=0.05, buckle=C(role, "brass")))
    return out, cov


def aron(anat):
    F, a, role = Fields(anat), anat, "aron"
    out, cov = [], np.zeros(len(anat.V), dtype=bool)
    p, c = shirt(a, F, "shirt", C(role, "shirt"), cuff=0.5, bottom_z=a.waist_z - 0.42, vneck=0.22)
    out.append(p)
    cov |= c
    # rolled-up sleeves: a thick roll at the sleeve end
    roll = _min(F.sleeve(0.53), F.arm_t - 0.44, F.w_arm - 0.3)
    out.append(Wd.fitted(a, "sleeve_roll", roll, np.full(len(a.V), 0.06), C(role, "shirt") * 0.92, "cloth"))
    p, c = trousers(a, F, "trousers", C(role, "trousers"), top_z=a.waist_z - 0.08, end_t=0.9)
    out.append(p)
    cov |= c
    p, c = boots(a, F, "boots", C(role, "boots"), top_t=0.76)
    out.append(p)
    cov |= c
    out.append(Wd.skirt(a, "apron", a.waist_z - 0.06, a.knee_z - 0.35, C(role, "apron"), kind="leather", ease_top=0.07,
                        flare=0.12, fold_amp=0.012, theta_range=(-1.25, 1.25), thickness=0.02, fold_count=5))
    out.append(bib(a, F, "apron_bib", C(role, "apron"), a.waist_z - 0.1, a.neck_z - 0.3, 0.26, 0.055, kind="leather"))
    out.append(band(a, "belt", a.waist_z - 0.1, 0.09, C(role, "belt"), ease=0.08, buckle=C(role, "brass")))
    return out, cov


def esme(anat):
    F, a, role = Fields(anat), anat, "esme"
    out, cov = [], np.zeros(len(anat.V), dtype=bool)
    p, c = shirt(a, F, "tunic", C(role, "tunic"), cuff=0.93, bottom_z=a.waist_z - 0.2, vneck=0.2, trim=C(role, "vest"))
    out.append(p)
    cov |= c
    out.append(Wd.skirt(a, "tunic_skirt", a.waist_z - 0.12, a.knee_z + 0.45, C(role, "tunic"), ease_top=0.07, flare=0.2,
                        fold_amp=0.025))
    p, c = trousers(a, F, "trousers", C(role, "trousers"), top_z=a.waist_z - 0.05, end_t=0.85)
    out.append(p)
    cov |= c
    p, c = boots(a, F, "boots", C(role, "boots"), top_t=0.52)
    out.append(p)
    cov |= c
    vest = _min(0.35 - F.w_arm - F.w_hand - F.w_head, F.z - (a.waist_z - 0.22), (a.neck_z - 0.1) - F.z,
                np.where(F.y < 0, np.abs(F.x) - 0.05, 1.0))
    out.append(Wd.fitted(a, "vest", vest, np.full(len(a.V), 0.045) + F.fill(1.0), C(role, "vest"), "leather", relax=14))
    out.append(band(a, "belt", a.waist_z - 0.1, 0.075, C(role, "belt"), ease=0.1, buckle=C(role, "brass")))
    return out, cov


OUTFITS = {"selma": selma, "nyra": nyra, "lio": lio, "aron": aron, "esme": esme}
