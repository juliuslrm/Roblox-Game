"""Clothes for the realistic traders (see characters.py).

Two kinds of garment:

  * fitted garments (shirts, bodices, sleeves, trousers, boots) are the body surface itself, pushed
    out along the vertex normals by the cloth thickness plus folds, with a thick hem along every cut
    edge.  They keep the body's skin weights, so they bend exactly like the body under them.
  * loose garments (skirts, aprons, cloaks, hoods) are lofts whose rings follow the measured outline
    of the body (support function of a horizontal slice) plus ease and folds.  Their skin weights
    come from the nearest body vertex.

Skin that a garment covers completely is removed from the body.
Fitted garments are open shells (the body fills them); loose garments are closed solids.
All geometry is in figure space (Z up, figure faces -Y, left = +X, 1 unit = 1 stud).
"""
import math

import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

from .human import FACE

TAU = 2 * math.pi


def rgb(hexcode):
    return np.array([int(hexcode[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


class Piece:
    """A mesh of the finished character: vertices, polygons, dense skin weights over the final bone
    list, a colour per vertex and a surface kind (drives the baked texture detail)."""

    def __init__(self, name, verts, faces, weights, colors, kind, smooth=True):
        self.name = name
        self.verts = np.asarray(verts, dtype=np.float64)
        self.faces = [tuple(int(i) for i in f) for f in faces]
        self.weights = np.asarray(weights, dtype=np.float64)
        self.colors = np.asarray(colors, dtype=np.float64)
        self.kind = kind
        self.smooth = smooth

    def triangles(self):
        return sum(len(f) - 2 for f in self.faces)

    def orient_outwards(self):
        """Closed solids: flip all faces if the signed volume is negative."""
        V = self.verts
        vol = 0.0
        for f in self.faces:
            a = V[f[0]]
            for k in range(1, len(f) - 1):
                vol += float(np.dot(a, np.cross(V[f[k]], V[f[k + 1]])))
        if vol < 0:
            self.faces = [tuple(reversed(f)) for f in self.faces]
        return self


def merge(name, pieces, kind=None):
    verts, faces, W, C = [], [], [], []
    off = 0
    for p in pieces:
        verts.append(p.verts)
        W.append(p.weights)
        C.append(p.colors)
        faces += [tuple(i + off for i in f) for f in p.faces]
        off += len(p.verts)
    return Piece(name, np.vstack(verts), faces, np.vstack(W), np.vstack(C), kind or pieces[0].kind)


# ---------------------------------------------------------------- body analysis
FACE_BONES = set(FACE)    # the face rig counts as head for garment and hair fields


class Anatomy:
    """Per-vertex facts about the body used to cut and fold garments."""

    def __init__(self, body):
        self.body = body
        self.names, self.W = body.dense_weights()
        self.bone = {b: i for i, b in enumerate(self.names)}
        V = body.verts
        self.V = V
        self.faces = [body.faces[i] for i in body.face_ids("body")]
        self.face_index = body.face_ids("body")
        self.normals = _vertex_normals(V, self.faces)
        self.dom = np.array([self.names[i] for i in np.argmax(self.W, axis=1)])
        self.in_body = np.zeros(len(V), dtype=bool)
        for f in self.faces:
            self.in_body[list(f)] = True
        head = lambda b: np.asarray(body.bones[b][0])
        self.arm, self.leg = {}, {}
        for side in ("L", "R"):
            self.arm[side] = _chain_param(V, [head("upperarm01." + side), head("lowerarm01." + side), head("wrist." + side)])
            self.leg[side] = _chain_param(V, [head("upperleg01." + side), head("lowerleg01." + side), head("foot." + side)])
        self.lm = body.landmarks
        self.neck_z = float(head("neck01")[2])
        self.waist_z = float(head("spine03")[2])
        self.hip_z = float(head("upperleg01.L")[2])
        self.knee_z = float(head("lowerleg01.L")[2])
        self.ankle_z = float(head("foot.L")[2])
        self.shoulder_z = float(head("upperarm01.L")[2])
        self.head_c = np.asarray(self.lm["head"]) + np.array((0.0, -0.02, 0.28)) * (self.neck_z / 5.5)

    def group(self, names):
        """Vertices whose dominant bone is one of `names` (prefix match: 'upperarm' matches both)."""
        names = tuple(names) + (("finger",) if "wrist" in names else ())
        return np.array([d.startswith(names) or ("head" in names and d in FACE_BONES) for d in self.dom])

    def weight(self, prefixes):
        """Summed skin weight of the bones whose names start with one of `prefixes` (continuous
        region membership, unlike the dominant bone)."""
        prefixes = tuple(prefixes) + (("finger",) if "wrist" in prefixes else ())      # the fingers are hand
        cols = [i for i, b in enumerate(self.names)
                if b.startswith(prefixes) or ("head" in prefixes and b in FACE_BONES)]
        return self.W[:, cols].sum(axis=1)

    def side_of(self):
        return np.where(self.V[:, 0] >= 0, "L", "R")

    def arm_t(self):
        """Position along the arm (0 shoulder .. 1 wrist) of every vertex, using its own side."""
        L, R = self.arm["L"][0], self.arm["R"][0]
        return np.where(self.V[:, 0] >= 0, L, R)

    def leg_t(self):
        L, R = self.leg["L"][0], self.leg["R"][0]
        return np.where(self.V[:, 0] >= 0, L, R)

    def limb_angle(self, which):
        chains = self.arm if which == "arm" else self.leg
        return np.where(self.V[:, 0] >= 0, chains["L"][1], chains["R"][1])

    def faces_where(self, mask, strict=True):
        """Body faces (vertex index tuples) whose vertices are all (strict) / mostly in `mask`."""
        out = []
        for f in self.faces:
            m = mask[list(f)]
            if m.all() or (not strict and m.sum() >= 3):
                out.append(f)
        return out


def _vertex_normals(V, faces):
    N = np.zeros_like(V)
    for f in faces:
        p = V[list(f)]
        n = np.zeros(3)
        for k in range(len(f)):
            n += np.cross(p[k], p[(k + 1) % len(f)])
        for i in f:
            N[i] += n
    ln = np.linalg.norm(N, axis=1)
    ln[ln == 0] = 1
    return N / ln[:, None]


def _chain_param(V, pts):
    """Arc-length parameter (0..1) of the projection of every vertex onto a polyline, and the angle
    of the vertex around the polyline (0 at the front, -Y)."""
    pts = [np.asarray(p, dtype=np.float64) for p in pts]
    lens = [np.linalg.norm(b - a) for a, b in zip(pts, pts[1:])]
    total = sum(lens)
    best_d = np.full(len(V), np.inf)
    t = np.zeros(len(V))
    ang = np.zeros(len(V))
    acc = 0.0
    for (a, b), ln in zip(zip(pts, pts[1:]), lens):
        d = (b - a) / ln
        s = np.clip((V - a) @ d, 0, ln)
        foot = a + s[:, None] * d
        dist = np.linalg.norm(V - foot, axis=1)
        better = dist < best_d
        best_d[better] = dist[better]
        t[better] = (acc + s[better]) / total
        ref = np.array((0.0, -1.0, 0.0))
        e1 = ref - np.dot(ref, d) * d
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(d, e1)
        q = V - foot
        ang[better] = np.arctan2(q[better] @ e2, q[better] @ e1)
        acc += ln
    return t, ang


# ---------------------------------------------------------------- fitted garments
def fitted(anat, name, field, offset, color, kind, colors=None, inner_gap=0.004, relax=4, relax_mask=None):
    """Garment from the body where `field` > 0 (one value per body vertex; the garment edge is its
    zero line).  Body faces partly inside are kept and their outside corners slide along the face
    edges onto the zero line, so every cut is a smooth line instead of following the mesh.  Each
    vertex is pushed out along the body normal by `offset`; every edge gets a thick hem."""
    f = np.asarray(field, dtype=np.float64)
    offset = np.asarray(offset, dtype=np.float64)
    # every body face with a corner inside is clipped exactly at the zero line of the field (one shared
    # vertex per cut edge, interpolated linearly), so the garment edge is a smooth curve that does not
    # follow the quads of the body mesh
    inside = f > 0
    keep = [fc for fc in anat.faces if inside[list(fc)].any()]
    rows = {}                                          # key -> new index; key = vertex or (a, b) edge cut
    src = []                                           # (a, b, t): new vertex = a + (b - a) * t

    def vid(key, a, b, t):
        if key not in rows:
            rows[key] = len(src)
            src.append((a, b, t))
        return rows[key]
    faces, cut = [], set()
    for fc in keep:
        n = len(fc)
        poly = []
        for k in range(n):
            a, b = fc[k], fc[(k + 1) % n]
            if inside[a]:
                poly.append(vid(a, a, a, 0.0))
            if inside[a] != inside[b]:
                key = (min(a, b), max(a, b))
                t = f[a] / (f[a] - f[b])
                i = vid(key, a, b, t)
                cut.add(i)
                poly.append(i)
        if len(poly) >= 3:
            faces.append(tuple(poly))
    ia = np.array([r[0] for r in src])
    ib = np.array([r[1] for r in src])
    tt = np.array([r[2] for r in src])[:, None]

    def lerp(X):
        X = np.asarray(X)
        return X[ia] * (1 - tt) + X[ib] * tt
    P = lerp(anat.V)
    N = lerp(anat.normals)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    O = lerp(offset[:, None])[:, 0]
    W = lerp(anat.W)
    W /= np.maximum(W.sum(axis=1, keepdims=True), 1e-9)
    col = np.tile(color, (len(src), 1)) if colors is None else lerp(colors)
    V = P + N * O[:, None]
    F = [tuple(fc) for fc in faces]
    on_cut = np.zeros(len(V), dtype=bool)
    on_cut[list(cut)] = True
    if relax:
        # cloth and leather smooth out the body's small forms: Laplacian relaxation, then every
        # vertex is pushed back to at least 60 % of its offset above the skin
        nbs = [set() for _ in range(len(V))]
        for fc in F:
            for a2, b2 in zip(fc, fc[1:] + fc[:1]):
                nbs[a2].add(b2)
                nbs[b2].add(a2)
        nb_idx = [np.array(sorted(n)) for n in nbs]
        movable = ~on_cut                                 # edge vertices stay on the cut line
        if relax_mask is not None:
            movable &= lerp(np.asarray(relax_mask, dtype=np.float64)[:, None])[:, 0] > 0.5
        for _ in range(relax):
            avg = np.array([V[n].mean(axis=0) if len(n) else V[k] for k, n in enumerate(nb_idx)])
            V = np.where(movable[:, None], V + 0.5 * (avg - V), V)
            d = np.einsum("ij,ij->i", V - P, N)
            low = d < 0.6 * O
            V[low] += N[low] * (0.6 * O[low] - d[low])[:, None]
    edges = set()
    for fc in F:
        for a2, b2 in zip(fc, fc[1:] + fc[:1]):
            edges.add((a2, b2))
    boundary = [(a2, b2) for (a2, b2) in edges if (b2, a2) not in edges]
    inner = {}
    newV, newW, newC = [V], [W], [col]
    n = len(V)
    for a2, b2 in boundary:
        for v in (a2, b2):
            if v not in inner:
                inner[v] = n
                n += 1
                newV.append((P[v] + N[v] * min(inner_gap, O[v] * 0.3))[None])
                newW.append(W[v][None])
                newC.append(col[v][None] * 0.75)
        F.append((b2, a2, inner[a2], inner[b2]))
    return Piece(name, np.vstack(newV), F, np.vstack(newW), np.vstack(newC), kind)


def hull_fill(anat, mask, step=0.03, segments=128, drop=0.35):
    """Cloth bridges hollows: for every vertex in `mask`, how far it lies inside the convex outline of
    its horizontal body slice (0 on the outline).  Added to a garment's offset it spans the cleavage,
    the small of the back and the dips between muscles like real fabric."""
    V = anat.V
    out = np.zeros(len(V))
    idx = np.nonzero(mask)[0]
    if len(idx) == 0:
        return out
    z0, z1 = V[idx, 2].min(), V[idx, 2].max()
    zs = np.arange(z0, z1 + step, step)
    th, rings = support_rings(anat, zs, mask, segments)
    # fabric falls from the widest point instead of following the body back in underneath it
    R = np.array([r for _, r in rings])
    fall = R.copy()
    for j in range(1, 9):
        fall[:-j] = np.maximum(fall[:-j], R[j:] - drop * j * step)
    rings = [(c, fall[k]) for k, (c, _r) in enumerate(rings)]
    for i in idx:
        k = int(round((V[i, 2] - z0) / step))
        k = min(max(k, 0), len(zs) - 1)
        c, r = rings[k]
        d = V[i, :2] - c
        ang = math.atan2(d[0], -d[1]) % TAU
        rh = np.interp(ang, th, r, period=TAU)
        out[i] = max(0.0, rh - float(np.linalg.norm(d)))
    return out


def folds(angle, t, count, amp, centres, width):
    """Cloth folds: ridges around a limb (angle) concentrated at parameters `centres` along it."""
    env = np.zeros_like(t)
    for c in centres:
        env = np.maximum(env, np.exp(-((t - c) / width) ** 2))
    return amp * env * (0.5 + 0.5 * np.sin(count * angle + 7.0 * t))


# ---------------------------------------------------------------- loose garments (lofts)
def slice_points(anat, mask, z, pad=0.0, axis=2):
    """Points where the body surface (edges between vertices in mask) crosses the plane at height z,
    plus the vertices within `pad` of it: an exact outline even where the mesh is coarse."""
    key = id(mask)
    cache = getattr(anat, "_edge_cache", {})
    if key not in cache:
        E = set()
        for f in anat.faces:
            for a, b in zip(f, f[1:] + f[:1]):
                if mask[a] and mask[b]:
                    E.add((min(a, b), max(a, b)))
        cache[key] = (np.array(sorted(E)), mask)
        anat._edge_cache = cache
    E = cache[key][0]
    if len(E) == 0:
        return np.zeros((0, 3))
    A, B = anat.V[E[:, 0]], anat.V[E[:, 1]]
    za, zb = A[:, axis] - z, B[:, axis] - z
    cross = (za * zb) <= 0
    cross &= np.abs(za - zb) > 1e-9
    t = (za[cross] / (za[cross] - zb[cross]))[:, None]
    pts = A[cross] + (B[cross] - A[cross]) * t
    if pad:
        V = anat.V[mask]
        pts = np.vstack((pts, V[np.abs(V[:, axis] - z) < pad]))
    return pts


def support_rings(anat, zs, mask, segments=72, centre=None):
    """Outline of the body at heights zs: support function r(theta) of the vertices in `mask` within a
    thin band around each height; theta = 0 at the front (-Y), increasing towards +X (the left)."""
    th = np.linspace(0, TAU, segments, endpoint=False)
    U = np.stack((np.sin(th), -np.cos(th)), axis=1)
    out = []
    for z in zs:
        band = slice_points(anat, mask, z, pad=0.04)
        c = centre if centre is not None else (band[:, :2].mean(axis=0) if len(band) else np.zeros(2))
        if len(band) == 0:
            out.append((c, np.full(segments, 0.05)))
            continue
        r = ((band[:, :2] - c) @ U.T).max(axis=0)
        out.append((np.asarray(c, float), r))
    return th, out


def grid_solid(outer, inner, closed_u):
    """Closed solid between two grids (rows x cols x 3).  Returns verts, faces (outer facing out
    after Piece.orient_outwards)."""
    m, n, _ = outer.shape
    verts = np.vstack((outer.reshape(-1, 3), inner.reshape(-1, 3)))
    off = m * n
    faces = []
    cols = n if closed_u else n - 1

    def i(r, c, layer):
        return layer * off + r * n + (c % n)
    for r in range(m - 1):
        for c in range(cols):
            faces.append((i(r, c, 0), i(r, c + 1, 0), i(r + 1, c + 1, 0), i(r + 1, c, 0)))
            faces.append((i(r + 1, c, 1), i(r + 1, c + 1, 1), i(r, c + 1, 1), i(r, c, 1)))
    for c in range(cols):                                     # top and bottom rims
        faces.append((i(0, c + 1, 0), i(0, c, 0), i(0, c, 1), i(0, c + 1, 1)))
        faces.append((i(m - 1, c, 0), i(m - 1, c + 1, 0), i(m - 1, c + 1, 1), i(m - 1, c, 1)))
    if not closed_u:                                          # side edges
        for r in range(m - 1):
            faces.append((i(r, 0, 0), i(r + 1, 0, 0), i(r + 1, 0, 1), i(r, 0, 1)))
            faces.append((i(r + 1, n - 1, 0), i(r, n - 1, 0), i(r, n - 1, 1), i(r + 1, n - 1, 1)))
    return verts, faces


def nearest_weights(anat, pts, mask=None, k=6):
    """Skin weights for loose cloth: inverse-distance blend of the k nearest body vertices."""
    idx = np.nonzero(anat.in_body if mask is None else (mask & anat.in_body))[0]
    tree = KDTree(len(idx))
    for j, i in enumerate(idx):
        tree.insert(Vector(anat.V[i]), j)
    tree.balance()
    W = np.zeros((len(pts), anat.W.shape[1]))
    for r, p in enumerate(pts):
        hits = tree.find_n(Vector(p), k)
        ws = np.array([1.0 / (h[2] + 1e-3) for h in hits])
        ws /= ws.sum()
        for (co, j, d), w in zip(hits, ws):
            W[r] += w * anat.W[idx[j]]
    return W / W.sum(axis=1, keepdims=True)


def fixed_weights(anat, n, bone):
    W = np.zeros((n, anat.W.shape[1]))
    W[:, anat.bone[bone]] = 1.0
    return W


def skirt(anat, name, z_top, z_hem, color, kind="cloth", ease_top=0.02, flare=0.22, fold_amp=0.03, fold_count=11,
          thickness=0.02, theta_range=None, extra=0.0, rows=26, segments=72, colors=None):
    """Skirt / robe / apron / cloak body: rings from z_top down to z_hem around the hips and legs.
    theta_range = (a0, a1) in radians (0 = front, + towards the figure's left) for an open garment."""
    zs = np.linspace(z_top, z_hem, rows)
    legs = anat.group(("spine05", "root", "pelvis", "upperleg", "lowerleg", "spine04"))
    th, rings = support_rings(anat, zs, legs, segments)
    if theta_range:
        th = np.linspace(theta_range[0], theta_range[1], segments)
    outer, inner = [], []
    prev = None
    centre = rings[0][0]
    for k, (z, (_c, r)) in enumerate(zip(zs, rings)):
        u = k / (rows - 1)
        rr = np.interp(th % TAU, np.linspace(0, TAU, len(r), endpoint=False), r, period=TAU)
        if prev is not None:
            rr = np.maximum(rr, prev)                          # a skirt never tucks back in under the hips
        prev = rr
        rad = rr + ease_top + extra + flare * u ** 1.6
        rad = rad + fold_amp * (u ** 0.8) * np.sin(fold_count * th + 1.3 * np.sin(3 * th))
        cc = centre
        pts = np.stack((cc[0] + rad * np.sin(th), cc[1] - rad * np.cos(th), np.full_like(th, z)), axis=1)
        ptsi = np.stack((cc[0] + (rad - thickness) * np.sin(th), cc[1] - (rad - thickness) * np.cos(th), np.full_like(th, z)), axis=1)
        outer.append(pts)
        inner.append(ptsi)
    verts, faces = grid_solid(np.array(outer), np.array(inner), closed_u=theta_range is None)
    W = fixed_weights(anat, len(verts), "spine05")
    col = np.tile(color, (len(verts), 1)) if colors is None else colors(verts)
    return Piece(name, verts, faces, W, col, kind).orient_outwards()
