"""Eyes, lashes, brows, hair, beards and headwear of the realistic traders.

Hair is real geometry: a thin cap over the scalp (so no skin shows between strands) and a few hundred
tapered strands grown from it.  A strand is a flat ribbon with thickness; it grows step by step
along its style's flow and is pushed out of the head wherever it would sink in, so it lies on the
head like real hair.
"""
import math
import random

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import wardrobe as Wd
from .wardrobe import rgb

TAU = 2 * math.pi


class Head:
    """Measurements of the head of a body (figure space)."""

    def __init__(self, anat):
        self.a = anat
        b = anat.body
        eyes = {}
        for side in ("l", "r"):
            ids = sorted({v for i in b.face_ids(f"helper-{side}-eye") for v in b.faces[i]})
            P = b.verts[ids]
            c = P.mean(axis=0)
            eyes[side.upper()] = (c, float(np.linalg.norm(P - c, axis=1).mean()))
        self.eyes = eyes
        self.eye_z = float((eyes["L"][0][2] + eyes["R"][0][2]) / 2)
        self.eye_r = (eyes["L"][1] + eyes["R"][1]) / 2
        hm = anat.weight(("head", "neck02")) > 0.5
        self.mask = hm & anat.in_body
        H = anat.V[self.mask]
        self.top = float(H[:, 2].max())
        self.chin = float(H[:, 2].min())
        self.centre = np.array((0.0, float(H[:, 1].mean()) + 0.02, (self.top + self.eye_z) / 2))
        self.front_y = float(H[:, 1].min())
        self.back_y = float(H[:, 1].max())
        self.half_w = float(H[:, 0].max())
        self.mouth = np.asarray(b.landmarks.get("oris01", (0, self.front_y, self.eye_z - 0.3)))
        # BVH of the head skin (with ears) for hair collisions
        faces = [f for f in anat.faces if self.mask[list(f)].sum() >= 3]
        self.bvh = BVHTree.FromPolygons([Vector(v) for v in anat.V], [list(f) for f in faces], all_triangles=False)

    def angle(self, V):
        """Angle around the vertical head axis, 0 at the face, + towards the figure's left."""
        return np.arctan2(V[:, 0] - self.centre[0], -(V[:, 1] - self.centre[1]))

    def push_out(self, p, dist):
        """Move a point out of the head so it is at least `dist` from the skin."""
        hit = self.bvh.find_nearest(Vector(p))
        if hit[0] is None:
            return p
        q = Vector(p) - hit[0]
        inside = q.dot(hit[1]) < 0
        if inside or q.length < dist:
            return np.array(hit[0] + hit[1] * dist)
        return p


def _sphere(centre, radius, axis, rings, segs):
    """UV sphere whose pole points along `axis`; rings = list of polar angles (degrees) from the pole."""
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    ref = np.array((0.0, 0.0, 1.0)) if abs(axis[2]) < 0.9 else np.array((1.0, 0.0, 0.0))
    e1 = np.cross(axis, ref)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    verts = [centre + axis * radius]
    for th in rings[1:-1]:
        t = math.radians(th)
        for k in range(segs):
            a = TAU * k / segs
            verts.append(centre + radius * (axis * math.cos(t) + math.sin(t) * (e1 * math.cos(a) + e2 * math.sin(a))))
    verts.append(centre - axis * radius)
    faces = []
    n = len(rings) - 2
    for k in range(segs):
        faces.append((0, 1 + (k + 1) % segs, 1 + k))
    for r in range(n - 1):
        for k in range(segs):
            a = 1 + r * segs + k
            b = 1 + r * segs + (k + 1) % segs
            faces.append((a, b, b + segs, a + segs))
    last = len(verts) - 1
    base = 1 + (n - 1) * segs
    for k in range(segs):
        faces.append((base + k, base + (k + 1) % segs, last))
    return np.array(verts), faces


def eyes(head, iris_hex, name="eyes"):
    """Eyeballs in the sockets of the base mesh: sclera, iris with a darker rim, pupil, all as
    vertex colours on rings placed at the colour borders."""
    a = head.a
    rings = [0, 6, 9.5, 11, 18, 25, 28.5, 31, 45, 70, 100, 140, 180]
    iris = rgb(iris_hex)
    pieces = []
    for side, (c, r) in head.eyes.items():
        sx = 1 if side == "L" else -1
        gaze = np.array((sx * 0.06, -1.0, -0.02))
        V, F = _sphere(c, r * 1.0, gaze, rings, 28)
        d = V - c
        ang = np.degrees(np.arccos(np.clip(d @ (gaze / np.linalg.norm(gaze)) / r, -1, 1)))
        col = np.empty((len(V), 3))
        col[:] = rgb("EDE6DC")
        col[ang < 40] = rgb("F2ECE4")
        col[ang < 29.5] = iris * 0.55                                 # limbal ring
        col[ang < 26] = iris
        col[ang < 15] = iris * 1.18
        col[ang < 9.6] = rgb("0E0B0A")                                # pupil
        col[ang > 70] = rgb("D8C8C0")                                 # pinkish towards the back
        W = Wd.fixed_weights(a, len(V), "head")
        pieces.append(Wd.Piece(name, V, F, W, col, "eye").orient_outwards())
    return Wd.merge(name, pieces)


def lashes(head, color_hex):
    """Eyelashes from the helper strips of the base mesh, made double-sided with a little thickness."""
    a, b = head.a, head.a.body
    pieces = []
    for side in ("l", "r"):
        for k in (1, 2):
            fids = b.face_ids(f"helper-{side}-eyelashes-{k}")
            used = sorted({v for i in fids for v in b.faces[i]})
            rm = {v: j for j, v in enumerate(used)}
            P = b.verts[used]
            F = [tuple(rm[v] for v in b.faces[i]) for i in fids]
            N = Wd._vertex_normals(P, F)
            V = np.vstack((P + N * 0.0015, P - N * 0.0015))
            n = len(P)
            faces = F + [tuple(reversed([i + n for i in f])) for f in F]
            W = a.W[used]
            pieces.append(Wd.Piece("lashes", V, faces, np.vstack((W, W)), np.tile(rgb(color_hex), (len(V), 1)), "hair"))
    return Wd.merge("lashes", pieces)


# ---------------------------------------------------------------- strands
def _ribbon(points, width, thickness, twist_ref=None):
    """Closed flat strand along points; width / thickness taper to the tip."""
    pts = [np.asarray(p, float) for p in points]
    n = len(pts)
    verts, faces = [], []
    ref = np.array((0.0, 0.0, 1.0)) if twist_ref is None else twist_ref
    for i, p in enumerate(pts):
        d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        d /= max(1e-9, np.linalg.norm(d))
        side = np.cross(d, ref)
        if np.linalg.norm(side) < 1e-6:
            side = np.cross(d, np.array((1.0, 0.0, 0.0)))
        side /= np.linalg.norm(side)
        up = np.cross(side, d)
        t = i / (n - 1)
        w = width * (1 - 0.85 * t ** 1.4)
        h = thickness * (1 - 0.7 * t)
        for sx, sy in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            verts.append(p + side * sx * w / 2 + up * sy * h / 2)
    for i in range(n - 1):
        for k in range(4):
            a, b = i * 4 + k, i * 4 + (k + 1) % 4
            faces.append((a, b, b + 4, a + 4))
    faces.append((3, 2, 1, 0))
    last = (n - 1) * 4
    faces.append((last, last + 1, last + 2, last + 3))
    return np.array(verts), faces


def grow(head, root, normal, direction_fn, length, steps, lift, rng, curl=0.0):
    """Strand path from root: each step follows direction_fn(p, t) and stays `lift(t)` above the skin."""
    p = np.asarray(root, float) + normal * lift(0.0)
    pts = [p]
    seg = length / steps
    phase = rng.uniform(0, TAU)
    for i in range(1, steps + 1):
        t = i / steps
        d = direction_fn(p, t)
        d = d / max(1e-9, np.linalg.norm(d))
        if curl:
            side = np.cross(d, np.array((0.0, 0.0, 1.0)))
            if np.linalg.norm(side) > 1e-6:
                side /= np.linalg.norm(side)
                up = np.cross(side, d)
                d = d + curl * (side * math.cos(phase + 2.4 * i) + up * math.sin(phase + 2.4 * i))
                d /= np.linalg.norm(d)
        p = p + d * seg
        p = head.push_out(p, lift(t))
        pts.append(p)
    return pts


def scalp_field(head, front, side_drop, nape):
    """Field over the body vertices that is positive on the scalp: the hairline sits `front` above
    the eyes at the forehead, drops by `side_drop` at the temples and reaches `nape` (height) behind."""
    a = head.a
    V = a.V
    phi = head.angle(V)
    u = np.abs(phi) / math.pi                                  # 0 front .. 1 back
    line_front = head.eye_z + front
    line = line_front - side_drop * np.sin(np.clip(u * 2, 0, 1) * math.pi / 2) ** 2
    back = np.clip((u - 0.55) / 0.45, 0, 1)
    line = line * (1 - back) + nape * back
    # keep the ears free
    ear = np.exp(-((np.abs(phi) - math.pi / 2) / 0.32) ** 2) * np.exp(-((V[:, 2] - (head.eye_z - 0.04)) / 0.12) ** 2)
    f = (V[:, 2] - line) - 0.2 * ear
    return np.where(head.mask | (a.weight(("neck",)) > 0.3), f, -1.0)


def hair_cap(head, name, field, color, thickness=0.014):
    a = head.a
    return Wd.fitted(a, name, field, np.full(len(a.V), thickness), color, "hair", inner_gap=0.002)


def _roots(piece, count, rng, keep=None):
    """Area-weighted random points (with normals) on the outer faces of a piece."""
    V = piece.verts
    tris = []
    for f in piece.faces:
        for k in range(1, len(f) - 1):
            tris.append((f[0], f[k], f[k + 1]))
    T = np.array(tris)
    A = V[T[:, 0]]
    B = V[T[:, 1]]
    Cc = V[T[:, 2]]
    nrm = np.cross(B - A, Cc - A)
    area = np.linalg.norm(nrm, axis=1)
    ok = area > 1e-9
    if keep is not None:
        ok &= keep((A + B + Cc) / 3)
    prob = np.where(ok, area, 0)
    prob /= prob.sum()
    out = []
    for i in rng.choices(range(len(T)), weights=prob, k=count):
        u, v = rng.random(), rng.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v
        p = A[i] + u * (B[i] - A[i]) + v * (Cc[i] - A[i])
        out.append((p, nrm[i] / area[i]))
    return out


def strands(head, name, roots, direction_fn, length_fn, color, rng, width=0.03, thickness=0.009, steps=8,
            lift=lambda t: 0.012 + 0.01 * t, curl=0.0, bone_fn=None, jitter=0.12):
    """Strands from root points; colours vary a little per strand (lighter tips)."""
    a = head.a
    pieces = []
    base = rgb(color) if isinstance(color, str) else color
    for k, (p, n) in enumerate(roots):
        pts = grow(head, p, n, direction_fn, length_fn(p, rng), steps, lift, rng, curl)
        V, F = _ribbon(pts, width * rng.uniform(0.75, 1.25), thickness)
        tone = base * rng.uniform(1 - jitter, 1 + jitter)
        col = np.empty((len(V), 3))
        for i in range(len(V)):
            t = (i // 4) / (len(pts) - 1)
            col[i] = np.clip(tone * (0.8 + 0.35 * t), 0, 1)
        W = Wd.nearest_weights(a, V[:1], head.mask) if bone_fn is None else bone_fn(V)
        if W.shape[0] == 1:
            W = np.repeat(W, len(V), axis=0)
        pieces.append(Wd.Piece(name, V, F, W, col, "hair"))
    return Wd.merge(name, pieces)


def head_bone(head, n):
    return Wd.fixed_weights(head.a, n, "head")


def brows(head, color_hex, rng, thick=1.0):
    """Eyebrows: short hairs lying on the brow ridge, pointing outwards and slightly up."""
    pieces = []
    for side, (c, r) in head.eyes.items():
        sx = 1 if side == "L" else -1
        roots = []
        for i in range(34):
            u = i / 33                                                   # 0 inner end .. 1 outer end
            x = c[0] + sx * (-1.25 * r + 2.9 * r * u)
            z = c[2] + r * (1.55 + 0.35 * math.sin(math.pi * min(1, u * 1.2)) - 0.25 * u)
            p = np.array((x, c[1] - 2 * r, z + rng.uniform(-0.15, 0.15) * r * thick))
            hit = head.bvh.ray_cast(Vector(p), Vector((0, 1, 0)))
            if hit[0] is None:
                continue
            roots.append((np.array(hit[0]), np.array(hit[1]), u))
        for p, n, u in roots:
            d = np.array((sx * 1.0, 0.0, 0.55 - 0.7 * u))
            d = d - np.dot(d, n) * n
            pts = [p + n * 0.003 + d / np.linalg.norm(d) * 0.013 * k * thick for k in range(4)]
            V, F = _ribbon(pts, 0.009 * thick, 0.0035)
            pieces.append(Wd.Piece("brows", V, F, head_bone(head, len(V)), np.tile(rgb(color_hex), (len(V), 1)), "hair"))
    return Wd.merge("brows", pieces)


# ---------------------------------------------------------------- headwear
def lathe_piece(head, name, profile, centre, color, kind, segs=40, tilt=None, scale=(1.0, 1.0)):
    """Solid of revolution around a vertical axis through centre: profile = [(r, z), ...]."""
    verts, rows = [], []
    for r, z in profile:
        row = []
        if r < 1e-6:
            verts.append(np.array((0.0, 0.0, z)))
            row = [len(verts) - 1]
        else:
            for k in range(segs):
                t = TAU * k / segs
                verts.append(np.array((r * math.sin(t) * scale[0], -r * math.cos(t) * scale[1], z)))
                row.append(len(verts) - 1)
        rows.append(row)
    faces = []
    for a_, b_ in zip(rows, rows[1:]):
        for k in range(segs):
            if len(a_) == 1 and len(b_) == 1:
                continue
            if len(a_) == 1:
                faces.append((a_[0], b_[(k + 1) % segs], b_[k]))
            elif len(b_) == 1:
                faces.append((a_[k], a_[(k + 1) % segs], b_[0]))
            else:
                faces.append((a_[k], a_[(k + 1) % segs], b_[(k + 1) % segs], b_[k]))
    if len(rows[0]) > 1:
        faces.append(tuple(reversed(rows[0])))
    if len(rows[-1]) > 1:
        faces.append(tuple(rows[-1]))
    V = np.array(verts)
    if tilt is not None:
        V = V @ tilt.T
    V = V + centre
    return Wd.Piece(name, V, faces, head_bone(head, len(V)), np.tile(color, (len(V), 1)), kind).orient_outwards()


def head_ring(head, z):
    """Radius of the head outline at height z (support function, 64 directions)."""
    th, rings = Wd.support_rings(head.a, [z], head.mask, 64, centre=head.centre[:2])
    return th, rings[0][1]
