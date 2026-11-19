"""Realistic human bodies from the MakeHuman base mesh (CC0 assets, see assets/thirdparty/makehuman).

Only the data is used (base mesh, macro targets, default skeleton and its skin weights); the loader,
the macro mixing, the skeleton simplification and the posing below are our own code.

Coordinates: the MakeHuman mesh is Y-up and faces +Z in decimetres.  Everything here returns the
figure space of the village pipeline instead: Z up, the figure faces -Y, its left side is +X, the
origin lies on the ground between the feet, 1 unit = 1 stud.

    body = Body.build(params, height)      shaped mesh, skeleton (reduced) and skin weights
    body.pose(rotations) -> posed vertices and bone matrices (linear blend skinning)
"""
import gzip
import json
import math
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "assets/thirdparty/makehuman"
SOURCE = "https://raw.githubusercontent.com/makehumancommunity/makehuman/master/makehuman/data/"

# MakeHuman (x, y, z) -> figure (x, -z, y)
MH_TO_FIGURE = np.array(((1.0, 0, 0), (0, 0, -1.0), (0, 1.0, 0)))

# ---------------------------------------------------------------- data files
_cache = {}


def _target_path(name):
    return DATA / "targets" / (name.replace("/", "__") + ".target.gz")


def fetch_target(name):
    """Macro targets are kept gzip-compressed in the repository; a missing one is fetched once."""
    path = _target_path(name)
    if not path.exists():
        with urllib.request.urlopen(SOURCE + "targets/" + name + ".target", timeout=120) as res:
            raw = res.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(raw, 9))
    return path


def load_target(name):
    """-> (indices, offsets in MakeHuman units).  An empty target gives empty arrays."""
    if name in _cache:
        return _cache[name]
    idx, off = [], []
    with gzip.open(fetch_target(name), "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line[0] == "#":
                continue
            p = line.split()
            idx.append(int(p[0]))
            off.append((float(p[1]), float(p[2]), float(p[3])))
    out = (np.array(idx, dtype=np.int64), np.array(off, dtype=np.float64).reshape(-1, 3))
    _cache[name] = out
    return out


def load_obj():
    """Base mesh: vertices (MH units), uvs, faces as vertex / uv index tuples, group name per face."""
    if "obj" in _cache:
        return _cache["obj"]
    verts, uvs, faces, fuv, groups = [], [], [], [], []
    group = None
    with open(DATA / "3dobjs/base.obj", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                verts.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("vt "):
                uvs.append([float(x) for x in line.split()[1:3]])
            elif line.startswith("g "):
                group = line.split()[1]
            elif line.startswith("f "):
                vi, ti = [], []
                for tok in line.split()[1:]:
                    parts = tok.split("/")
                    vi.append(int(parts[0]) - 1)
                    ti.append(int(parts[1]) - 1 if len(parts) > 1 and parts[1] else -1)
                faces.append(tuple(vi))
                fuv.append(tuple(ti))
                groups.append(group)
    out = dict(verts=np.array(verts), uvs=np.array(uvs), faces=faces, fuv=fuv, groups=groups)
    _cache["obj"] = out
    return out


def load_skeleton():
    if "skel" not in _cache:
        _cache["skel"] = json.loads((DATA / "rigs/default.mhskel").read_text(encoding="utf-8"))
    return _cache["skel"]


def load_weights():
    if "weights" not in _cache:
        _cache["weights"] = json.loads((DATA / "rigs/default_weights.mhw").read_text(encoding="utf-8"))["weights"]
    return _cache["weights"]


# ---------------------------------------------------------------- macro modelling
def _split(value, names):
    """Weights of the low / average / high variants of a slider in [0, 1] (0.5 = average)."""
    if value < 0.5:
        return {names[0]: 1 - value / 0.5, names[1]: value / 0.5}
    return {names[1]: 1 - (value - 0.5) / 0.5, names[2]: (value - 0.5) / 0.5}


def macro_targets(p):
    """Target names and weights for the macro parameters (MakeHuman 1.1 macro model):
    gender 0 = female .. 1 = male; age 0.5 = 25 years .. 1 = 90 years; muscle, weight, height
    0.5 = average; race = {caucasian, african, asian} shares."""
    gender = {"female": 1 - p["gender"], "male": p["gender"]}
    a = max(0.5, p["age"])
    age = {"young": 1 - (a - 0.5) / 0.5, "old": (a - 0.5) / 0.5}
    muscle = _split(p["muscle"], ("minmuscle", "averagemuscle", "maxmuscle"))
    weight = _split(p["weight"], ("minweight", "averageweight", "maxweight"))
    hv = p.get("height", 0.5)
    height = {"minheight": max(0.0, (0.5 - hv) * 2), "maxheight": max(0.0, (hv - 0.5) * 2)}
    out = {}

    def put(name, w):
        if w > 1e-4:
            out[name] = out.get(name, 0.0) + w
    for race, share in p.get("race", {"caucasian": 1.0}).items():
        for g, gw in gender.items():
            for ag, aw in age.items():
                put(f"macrodetails/{race}-{g}-{ag}", share * gw * aw)
    for g, gw in gender.items():
        for ag, aw in age.items():
            for m, mw in muscle.items():
                for wt, ww in weight.items():
                    base = gw * aw * mw * ww
                    put(f"macrodetails/universal-{g}-{ag}-{m}-{wt}", base)
                    for h, hw in height.items():
                        put(f"macrodetails/height/{g}-{ag}-{m}-{wt}-{h}", base * hw)
    return out


def shaped_vertices(params):
    obj = load_obj()
    v = obj["verts"].copy()
    for name, w in macro_targets(params).items():
        idx, off = load_target(name)
        if len(idx):
            v[idx] += w * off
    for name, w in params.get("details", {}).items():           # face and body detail targets
        idx, off = load_target(name)
        if len(idx):
            v[idx] += w * off
    return v


# ---------------------------------------------------------------- skeleton reduction
# Bones that stay in the exported rig, with the parent they keep.  Every other MakeHuman bone hands
# its skin weights to its nearest kept ancestor (twist bones, toes, the face bones, the fingers: the
# fingers are posed once around the held tool and then belong to the hand).
KEEP = {
    "root": None,
    "spine05": "root", "spine04": "spine05", "spine03": "spine04", "spine02": "spine03", "spine01": "spine02",
    "neck01": "spine01", "neck02": "neck01", "head": "neck02",
    "clavicle.L": "spine01", "upperarm01.L": "clavicle.L", "upperarm02.L": "upperarm01.L",
    "lowerarm01.L": "upperarm02.L", "lowerarm02.L": "lowerarm01.L", "wrist.L": "lowerarm02.L",
    "clavicle.R": "spine01", "upperarm01.R": "clavicle.R", "upperarm02.R": "upperarm01.R",
    "lowerarm01.R": "upperarm02.R", "lowerarm02.R": "lowerarm01.R", "wrist.R": "lowerarm02.R",
    "pelvis.L": "root", "upperleg01.L": "pelvis.L", "lowerleg01.L": "upperleg01.L", "foot.L": "lowerleg01.L",
    "pelvis.R": "root", "upperleg01.R": "pelvis.R", "lowerleg01.R": "upperleg01.R", "foot.R": "lowerleg01.R",
}
# face bones of the MakeHuman skeleton that stay as an animatable face rig (bone based, so it works in
# Roblox, which plays skinned bones but not shape keys): eyes, upper and lower lids, brows, lip corners
# (upper and lower), upper and lower lip, cheeks, jaw.  Each keeps its own MakeHuman skin weights and
# hangs from its nearest kept ancestor (head or jaw).
FACE = ("jaw", "eye.L", "eye.R", "orbicularis03.L", "orbicularis03.R", "orbicularis04.L", "orbicularis04.R",
        "oculi01.L", "oculi01.R", "oris03.L", "oris03.R", "oris07.L", "oris07.R", "oris05", "oris01",
        "risorius03.L", "risorius03.R")
# twist bones (upperarm02, lowerarm02) and finger bones keep their own weights while the rest pose
# and the grip are baked (they spread the forearm twist and close the hand); then they are merged
FINGERS = [f"finger{i}-{j}" for i in range(1, 6) for j in range(1, 4)]
SHOULDER_TO_UPPER = {"shoulder01.L": "upperarm01.L", "shoulder01.R": "upperarm01.R"}


class Body:
    """A shaped MakeHuman body in figure space with a reduced skeleton and skin weights."""

    def __init__(self, verts, bones, parents, weights, faces, fuv, uvs, groups):
        self.verts = verts            # (N, 3) rest positions
        self.bones = bones            # name -> (head, tail) rest
        self.parents = parents        # name -> parent name or None (topological order in .order)
        self.weights = weights        # name -> (indices, weights)
        self.faces, self.fuv, self.uvs, self.groups = faces, fuv, uvs, groups
        self.order = _topo(parents)

    # ---------------------------------------------------------------- build
    @classmethod
    def build(cls, params, height):
        obj = load_obj()
        mh = shaped_vertices(params)
        skel = load_skeleton()
        joints = {name: mh[np.array(ids)].mean(axis=0) for name, ids in skel["joints"].items()}
        body_ids = sorted({i for f, g in zip(obj["faces"], obj["groups"]) if g == "body" for i in f})
        ground = mh[body_ids, 1].min()
        top = mh[body_ids, 1].max()
        k = height / (top - ground)

        def fig(p):
            q = (np.asarray(p) - np.array((0.0, ground, 0.0))) * k
            return q @ MH_TO_FIGURE.T
        verts = fig(mh)
        heads = {b: fig(joints[d["head"]]) for b, d in skel["bones"].items()}
        tails = {b: fig(joints[d["tail"]]) for b, d in skel["bones"].items()}
        full_parent = {b: d["parent"] for b, d in skel["bones"].items()}
        keep = dict(KEEP)
        for side in ("L", "R"):
            for f in FINGERS:
                name = f"{f}.{side}"
                p = full_parent[name]
                keep[name] = "wrist." + side if p.startswith("metacarpal") else p
        for name in FACE:
            p = full_parent[name]
            while p not in keep and p not in FACE:
                p = full_parent[p]
            keep[name] = p
        # weights: every bone gives its weights to the nearest kept ancestor
        raw = load_weights()
        n = len(verts)
        acc = {b: np.zeros(n) for b in keep}
        for b, pairs in raw.items():
            target = SHOULDER_TO_UPPER.get(b, b)
            while target not in keep:
                target = full_parent[target]
            arr = np.array(pairs, dtype=np.float64).reshape(-1, 2)
            np.add.at(acc[target], arr[:, 0].astype(np.int64), arr[:, 1])
        weights = {b: (np.nonzero(w)[0], w[np.nonzero(w)[0]]) for b, w in acc.items() if w.any()}
        bones = {b: (heads[b], tails[b]) for b in keep}
        groups = obj["groups"]
        body = cls(verts, bones, keep, weights, obj["faces"], obj["fuv"], obj["uvs"], groups)
        # rest positions of all MakeHuman bones (face landmarks: lips, jaw, eyes, brows)
        body.landmarks = {b: heads[b] for b in heads}
        return body

    # ---------------------------------------------------------------- helpers
    def face_ids(self, group="body"):
        return [i for i, g in enumerate(self.groups) if g == group]

    def dense_weights(self):
        n = len(self.verts)
        names = self.order
        W = np.zeros((n, len(names)))
        for j, b in enumerate(names):
            if b in self.weights:
                idx, w = self.weights[b]
                W[idx, j] = w
        s = W.sum(axis=1, keepdims=True)
        s[s == 0] = 1
        return names, W / s

    def merge_bones(self, names):
        """Gives the weights of `names` to their parents and drops them from the skeleton."""
        for b in names:
            p = self.parents[b]
            if b in self.weights:
                idx, w = self.weights.pop(b)
                if p in self.weights:
                    pi, pw = self.weights[p]
                    acc = {}
                    for i, x in zip(pi, pw):
                        acc[i] = acc.get(i, 0.0) + x
                    for i, x in zip(idx, w):
                        acc[i] = acc.get(i, 0.0) + x
                    ks = np.array(sorted(acc))
                    self.weights[p] = (ks, np.array([acc[i] for i in ks]))
                else:
                    self.weights[p] = (idx, w)
            for c, cp in list(self.parents.items()):
                if cp == b:
                    self.parents[c] = p
            del self.parents[b]
            del self.bones[b]
        self.order = _topo(self.parents)

    # ---------------------------------------------------------------- posing
    def bone_matrices(self, local_rot, local_move=None):
        """local_rot: bone -> 3x3 rotation in figure axes about the bone head, relative to the parent;
        local_move: bone -> translation in figure axes (parent space; the face rig slides lip corners and
        brows).  -> bone -> 4x4 world transform (posed = M @ rest)."""
        out = {}
        local_move = local_move or {}
        for b in self.order:
            head = self.bones[b][0]
            R = local_rot.get(b, np.eye(3))
            L = np.eye(4)
            L[:3, :3] = R
            L[:3, 3] = head - R @ head + np.asarray(local_move.get(b, (0.0, 0.0, 0.0)))
            p = self.parents[b]
            out[b] = out[p] @ L if p else L
        return out

    def skin(self, mats, verts=None):
        """Linear blend skinning of the rest vertices (or `verts`, same order)."""
        names, W = self.dense_weights()
        v = self.verts if verts is None else verts
        vh = np.c_[v, np.ones(len(v))]
        out = np.zeros_like(v)
        for j, b in enumerate(names):
            w = W[:, j]
            nz = w > 0
            if nz.any():
                out[nz] += w[nz, None] * (vh[nz] @ mats[b].T)[:, :3]
        return out

    def apply_pose(self, local_rot):
        """Bakes a pose as the new rest pose (mesh and skeleton)."""
        mats = self.bone_matrices(local_rot)
        self.verts = self.skin(mats)
        for b, (h, t) in list(self.bones.items()):
            M = mats[b]
            self.bones[b] = ((M @ np.r_[h, 1])[:3], (M @ np.r_[t, 1])[:3])
        return mats


def _topo(parents):
    order, seen = [], set()

    def visit(b):
        if b in seen:
            return
        p = parents[b]
        if p:
            visit(p)
        seen.add(b)
        order.append(b)
    for b in sorted(parents):
        visit(b)
    return order


def rot(axis, deg):
    """3x3 rotation about a unit axis (numpy), degrees."""
    a = np.asarray(axis, dtype=np.float64)
    a = a / np.linalg.norm(a)
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    x, y, z = a
    return np.array(((c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s),
                     (y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s),
                     (z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c))))


def rotation_between(a, b):
    """Shortest rotation turning direction a into direction b."""
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    axis = np.cross(a, b)
    s = np.linalg.norm(axis)
    if s < 1e-9:
        return np.eye(3)
    return rot(axis / s, math.degrees(math.atan2(s, float(np.dot(a, b)))))
