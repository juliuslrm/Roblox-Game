"""Character QA sheets: the views of the character brief (§16.2) for one or all traders.

    python blender/render_character_qa.py -- --out previews/characters/before [--only lio] [--tile 512]

Per trader, neutral grey light, plain background, fixed cameras (so a before and an after sheet can be
put side by side):
    <out>/<role>_views.png      front, side, back, three-quarter; head front, head three-quarter, eyes,
                                hand right, hand left, clothing (torso), held item in use, atmospheric light
    <out>/<role>_motion.png     the idle loop at 8 moments, three-quarter view, whole figure
The characters are rendered from their mesh pieces with vertex colours (the colour that is baked into the
textures, without the texture detail), so geometry, proportions and shading are judged, not the bake.
"""
import argparse
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE)]

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import validate_grips as VG  # noqa: E402
from village import characters as C  # noqa: E402
from village import export  # noqa: E402
from village import scene as sc  # noqa: E402


def neutral_light(scene):
    sc.setup_light(scene, sun_az=235.0, sun_el=38.0, sun_strength=2.6, sky=(0.82, 0.83, 0.86), sky_strength=0.9)


def warm_light(scene):
    sc.setup_light(scene, sun_az=200.0, sun_el=18.0, sun_strength=4.2, sky=(0.42, 0.5, 0.75), sky_strength=0.5)


def joint(ch, rots, bone):
    mats = ch.body.bone_matrices(rots) if rots else None
    p = ch.heads[bone]
    return (mats[bone] @ np.r_[p, 1])[:3] if mats else p


def views(ch, out, tile):
    scene = bpy.context.scene
    cam = scene.camera
    cam.data.clip_start = 0.02
    duration = C.LOOPS[ch.role]["duration"]
    rest = C.local_rotations(ch.role, 0.0)
    objs = VG.show_character(ch, rest, VG.material())
    V = np.vstack([VG.posed(ch, p.weights, p.verts, rest) for p in ch.pieces])
    lo, hi = V.min(axis=0), V.max(axis=0)
    tiles = []
    tmp = str(ROOT / f"world/_qa_{ch.role}_%d.png")

    def shot():
        tiles.append(VG.render_tile(tmp % len(tiles)))
    for az in (-90, 180, 90, -55):                         # front, figure's right side, back, 3/4
        sc.frame_bounds(cam, lo, hi, az=az, el=6, aspect=1.0, lens=50, margin=0.78)
        shot()
    mats = ch.body.bone_matrices(rest)
    eye = {k: (mats["head"] @ np.r_[ch.body.landmarks["eye." + k], 1])[:3] for k in ("L", "R")}
    eyes = (eye["L"] + eye["R"]) / 2
    face = eyes + np.array((0.0, 0.0, -0.12))
    cam.data.lens = 50
    for az, dist in ((-90, 1.05), (-50, 1.1)):
        sc.orbit(cam, tuple(face), az, 2, dist)
        shot()
    sc.orbit(cam, tuple(eyes), -90, 0, 0.42)
    shot()
    for side in ("R", "L"):
        M = mats["wrist." + side]
        w = (M @ np.r_[ch.heads["wrist." + side], 1])[:3]
        hand = M[:3, :3] @ ch.body.hand_geometry[side]["hand"]
        c = w + hand * 0.22
        sx = 1 if side == "L" else -1
        sc.orbit(cam, tuple(c), -90 + sx * 55, 12, 0.95)
        shot()
    chest = joint(ch, rest, "spine03")
    sc.orbit(cam, tuple(chest + np.array((0, 0, -0.4))), -70, 8, 3.2)
    shot()
    VG.clear(objs)
    # held item in use: the loop moment with the right hand highest
    best_t, best_z = 0.0, -1e9
    for k in range(int(duration * 8)):
        t = k / 8
        z = joint(ch, C.local_rotations(ch.role, t), "wrist.R")[2]
        if z > best_z:
            best_t, best_z = t, z
    rots = C.local_rotations(ch.role, best_t)
    objs = VG.show_character(ch, rots, VG.material())
    w = joint(ch, rots, "wrist.R")
    sc.orbit(cam, tuple(w + np.array((0.0, -0.1, -0.1))), -120, 12, 1.6)
    shot()
    VG.clear(objs)
    # atmospheric light, three-quarter whole figure
    warm_light(scene)
    objs = VG.show_character(ch, rest, VG.material())
    sc.frame_bounds(cam, lo, hi, az=-60, el=8, aspect=1.0, lens=50, margin=0.8)
    shot()
    VG.clear(objs)
    neutral_light(scene)
    VG.sheet(tiles, str(Path(out) / f"{ch.role}_views.png"))


def _show_posed(ch, rots, moves, mat):
    mats = ch.body.bone_matrices(rots, moves)
    objs = []
    for p in ch.pieces:
        vh = np.c_[p.verts, np.ones(len(p.verts))]
        V = np.zeros_like(p.verts)
        for j, b in enumerate(ch.bones):
            w = p.weights[:, j]
            nz = w > 0
            if nz.any():
                V[nz] += w[nz, None] * (vh[nz] @ mats[b].T)[:, :3]
        objs.append(VG.add_mesh(p.name, V, p.faces, p.colors, mat, p.smooth))
    return objs, mats


def faces(ch, out):
    """Neutral face and every expression of the face rig (C.FACE_POSES), front and three-quarter."""
    scene = bpy.context.scene
    cam = scene.camera
    cam.data.clip_start = 0.02
    base = C.local_rotations(ch.role, 0.0)
    base = {b: R for b, R in base.items() if b not in ("neck01", "head")}      # face straight ahead
    tiles = []
    tmp = str(ROOT / f"world/_qaf_{ch.role}_%d.png")
    for name in ["neutral"] + list(C.FACE_POSES):
        rots, moves = ({}, {}) if name == "neutral" else C.face_pose(name)
        objs, mats = _show_posed(ch, {**base, **rots}, moves, VG.material())
        eye = [(mats["head"] @ np.r_[ch.body.landmarks["eye." + k], 1])[:3] for k in ("L", "R")]
        c = (eye[0] + eye[1]) / 2 + np.array((0.0, 0.0, -0.1))
        for az in (-90, -55):
            sc.orbit(cam, tuple(c), az, 3, 0.85)
            tiles.append(VG.render_tile(tmp % len(tiles)))
        VG.clear(objs)
    VG.sheet(tiles, str(Path(out) / f"{ch.role}_face.png"))


def motion(ch, out):
    scene = bpy.context.scene
    cam = scene.camera
    duration = C.LOOPS[ch.role]["duration"]
    tiles = []
    tmp = str(ROOT / f"world/_qam_{ch.role}_%d.png")
    rest = C.local_rotations(ch.role, 0.0)
    V = np.vstack([VG.posed(ch, p.weights, p.verts, rest) for p in ch.pieces])
    lo, hi = V.min(axis=0) - 0.3, V.max(axis=0) + 0.3
    for k in range(8):
        rots = C.local_rotations(ch.role, duration * k / 8)
        objs = VG.show_character(ch, rots, VG.material())
        sc.frame_bounds(cam, lo, hi, az=-62, el=6, aspect=1.0, lens=50, margin=0.78)
        tiles.append(VG.render_tile(tmp % len(tiles)))
        VG.clear(objs)
    VG.sheet(tiles, str(Path(out) / f"{ch.role}_motion.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="previews/characters/after")
    ap.add_argument("--only")
    ap.add_argument("--tile", type=int, default=512)
    ap.add_argument("--faces-only", action="store_true")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    VG.TILE = args.tile
    scene = export.new_scene()
    sc.setup_render(scene, res=(args.tile, args.tile), samples=24)
    neutral_light(scene)
    sc.add_camera(scene)
    for role in ([args.only] if args.only else C.ROLES):
        ch = C.build(role)
        faces(ch, out)
        if not args.faces_only:
            views(ch, out, args.tile)
            motion(ch, out)
        print(f"[qa] {role}: {out}/{role}_views.png, {role}_motion.png", flush=True)


if __name__ == "__main__":
    main()
