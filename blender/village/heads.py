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
        W = Wd.fixed_weights(a, len(V), "eye." + side)             # the eyeball turns with its eye bone
        pieces.append(Wd.Piece(name, V, F, W, col, "eye").orient_outwards())
    return Wd.merge(name, pieces)


def lashes(head, color_hex, upper=44, lower=12, rng_seed=3):
    """Eyelashes as single tapered hairs along the lid edges.  The helper strips of the base mesh
    (cards made for an alpha texture) only give the lid edge (their row nearest to the eyeball) and the
    direction the lashes grow (towards their far row); as solid geometry the strips themselves read
    as a thick black line around the eye."""
    import random
    rng = random.Random(rng_seed)
    a, b = head.a, head.a.body
    pieces = []
    for side in ("l", "r"):
        c, r = head.eyes[side.upper()]
        for k in (1, 2):
            fids = b.face_ids(f"helper-{side}-eyelashes-{k}")
            used = sorted({v for i in fids for v in b.faces[i]})
            P = b.verts[used]
            top = P[:, 2].mean() > c[2]                      # the strip order is not upper / lower
            count, length, width = (upper, 0.022, 0.002) if top else (lower, 0.01, 0.0016)
            d = np.linalg.norm(P - c, axis=1)
            lo, hi = d.min(), d.max()
            near = P[d < lo + 0.3 * (hi - lo)]
            far = P[d > lo + 0.7 * (hi - lo)]
            if len(near) < 2 or len(far) < 1:
                continue
            # order the lid edge from one corner to the other (largest spread axis)
            ax = np.linalg.svd(near - near.mean(axis=0))[2][0]
            near = near[np.argsort((near - near.mean(axis=0)) @ ax)]
            seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(near, axis=0), axis=1))]
            for j in range(count):
                u = (j + rng.uniform(0.2, 0.8)) / count
                root = np.array([np.interp(u * seg[-1], seg, near[:, q]) for q in range(3)])
                tip_dir = far[np.argmin(np.linalg.norm(far - root, axis=1))] - root
                tip_dir /= max(1e-9, np.linalg.norm(tip_dir))
                out_dir = (root - c) / np.linalg.norm(root - c)
                L = length * (0.55 + 0.45 * math.sin(math.pi * u)) * rng.uniform(0.85, 1.1)
                pts = [root + (tip_dir * 0.75 + out_dir * 0.25) * L * t + out_dir * L * 0.25 * t * t
                       for t in (0.0, 0.33, 0.66, 1.0)]
                V, F = _ribbon(pts, width, 0.0012)
                pieces.append(Wd.Piece("lashes", V, F, np.repeat(a.W[used][np.argmin(d)][None], len(V), axis=0),
                                       np.tile(rgb(color_hex), (len(V), 1)), "hair"))
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
        for i in range(64):
            u = i / 63                                                   # 0 inner end .. 1 outer end
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
            pts = [p + n * 0.003 + d / np.linalg.norm(d) * 0.008 * k * (0.7 + 0.3 * thick) for k in range(4)]
            V, F = _ribbon(pts, 0.006 * thick, 0.0028)
            W = np.repeat(Wd.nearest_weights(head.a, [p], head.mask, k=4), len(V), axis=0)   # brows move with the skin
            pieces.append(Wd.Piece("brows", V, F, W, np.tile(rgb(color_hex), (len(V), 1)), "hair"))
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


# ---------------------------------------------------------------- short coily hair as a volume
def subdivide(piece):
    """Every n-gon -> n quads (face centre, edge midpoints, corner); no smoothing, attributes are
    interpolated linearly.  Shared edge midpoints keep the mesh closed."""
    V, W, Cc = piece.verts, piece.weights, piece.colors
    nv, nw, nc = [V], [W], [Cc]
    n = len(V)
    mid = {}

    def add(pos, w, c):
        nonlocal n
        nv.append(pos[None])
        nw.append(w[None])
        nc.append(c[None])
        n += 1
        return n - 1
    faces = []
    for f in piece.faces:
        k = len(f)
        ci = add(V[list(f)].mean(axis=0), W[list(f)].mean(axis=0), Cc[list(f)].mean(axis=0))
        mids = []
        for i in range(k):
            a, b = f[i], f[(i + 1) % k]
            key = (min(a, b), max(a, b))
            if key not in mid:
                mid[key] = add((V[a] + V[b]) / 2, (W[a] + W[b]) / 2, (Cc[a] + Cc[b]) / 2)
            mids.append(mid[key])
        for i in range(k):
            faces.append((f[i], mids[i], ci, mids[i - 1]))
    return Wd.Piece(piece.name, np.vstack(nv), faces, np.vstack(nw), np.vstack(nc), piece.kind, piece.smooth)


def coily_hair(head, name, field, color, rng, height=0.05, curl=0.022, density=5200, levels=2, contrast=1.0, relief=1.0):
    """Short tightly curled hair: a scalp cap, subdivided, pushed out by `height` (thinning to nothing
    at the hairline) and covered with round curl bumps of radius ~`curl`.  Crevices between the
    curls are darker, curl tops lighter, so the volume reads as hair at every distance."""
    a = head.a
    base = rgb(color) if isinstance(color, str) else np.asarray(color)
    cap = Wd.fitted(a, name, field, np.full(len(a.V), 0.004), base, "hair", inner_gap=0.001, relax=0)
    for k in range(levels):
        cap = subdivide(cap)
    V = cap.verts
    F = cap.faces
    N = Wd._vertex_normals(V, F)
    # graph distance to the open border (the hairline): taper of the volume
    nbs = [[] for _ in range(len(V))]
    edges = {}
    for f in F:
        for x, y in zip(f, f[1:] + f[:1]):
            nbs[x].append(y)
            edges[(x, y)] = edges.get((x, y), 0) + 1
    border = {x for (x, y) in edges if (y, x) not in edges}
    dist = np.full(len(V), np.inf)
    frontier = list(border)
    for b in frontier:
        dist[b] = 0.0
    import heapq
    heap = [(0.0, b) for b in frontier]
    while heap:
        d, x = heapq.heappop(heap)
        if d > dist[x]:
            continue
        for y in nbs[x]:
            nd = d + float(np.linalg.norm(V[x] - V[y]))
            if nd < dist[y]:
                dist[y] = nd
                heapq.heappush(heap, (nd, y))
    taper = np.clip(dist / 0.07, 0, 1)
    taper = taper * taper * (3 - 2 * taper)
    # curl bumps: random centres on the cap, each a rounded dome
    tri_area = []
    for f in F:
        tri_area.append(np.linalg.norm(np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])))
    prob = np.array(tri_area) / np.sum(tri_area)
    picks = rng.choices(range(len(F)), weights=prob, k=density)
    centres = np.array([V[list(F[i])].mean(axis=0) for i in picks])
    radii = np.array([curl * rng.uniform(0.7, 1.3) for _ in picks])
    bump = np.zeros(len(V))
    for s in range(0, len(centres), 400):
        C_ = centres[s:s + 400]
        R_ = radii[s:s + 400]
        d2 = ((V[:, None, :] - C_[None]) ** 2).sum(axis=2)
        h = np.clip(1 - d2 / (R_[None] ** 2), 0, None)
        bump = np.maximum(bump, (np.sqrt(h) * R_[None]).max(axis=1))
    out = height * taper + relief * bump * (0.35 + 0.65 * taper)          # relief < 1: smooth, straight hair
    cap.verts = V + N * out[:, None]
    shade = 1.0 + contrast * (0.75 * np.clip(bump / curl, 0, 1) - 0.45)
    jitter = np.array([rng.uniform(1 - 0.1 * contrast, 1 + 0.1 * contrast) for _ in range(len(V))])
    cap.colors = np.clip(base[None] * (shade * jitter)[:, None], 0, 1)
    return cap
