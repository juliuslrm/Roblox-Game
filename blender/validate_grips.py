"""Grip test scenes: measures every held prop of every trader and renders a contact sheet per grip.

    python blender/validate_grips.py -- --out previews/grips/after [--only lio] [--no-render]

Per grip (role, hand): the measurements of village/gripcheck.py, the prop's distance to the body
during the idle loop, and one sheet (16 views, same light, neutral background, fixed cameras):
    row 1   whole figure front, side, three-quarter (loop moment with the hand highest), hand close-up
    row 2-3 hand and prop alone in the rest pose from six directions (front, outside, back, inside,
            above, below)
    row 4   the hand during the loop, four moments
Writes <out>/<role>_<hand>_<prop>.png, <out>/grip_validation.json and, for --out .../after, the
report docs/GRIP_VALIDATION_REPORT.md (visual verdicts come from docs/grip_reviews.json, written
after looking at the sheets).
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE)]

import bpy  # noqa: E402
import numpy as np  # noqa: E402

from village import characters as C  # noqa: E402
from village import export  # noqa: E402
from village import gripcheck as GC  # noqa: E402
from village import grips as G  # noqa: E402
from village import scene as sc  # noqa: E402

TILE = 360


def lin(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def material():
    m = bpy.data.materials.new("vertex_colour")
    m.use_nodes = True
    nt = m.node_tree
    a = nt.nodes.new("ShaderNodeVertexColor")
    a.layer_name = "Col"
    nt.links.new(a.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    return m


def add_mesh(name, V, F, cols, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    if smooth:
        me.shade_smooth()
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    L = lin(cols)
    ca.data.foreach_set("color", np.c_[L, np.ones(len(L))].ravel())
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def posed(ch, W, V, rots):
    return GC._posed(ch, W, V, rots)


def show_character(ch, rots, mat, keep=None):
    """Posed copies of all pieces (keep(piece) -> face mask or None for all)."""
    objs = []
    for p in ch.pieces:
        V = posed(ch, p.weights, p.verts, rots) if rots else p.verts
        F = p.faces
        if keep is not None:
            m = keep(p)
            if m is None:
                continue
            F = [f for f in F if m[list(f)].all()]
            if not F:
                continue
        objs.append(add_mesh(p.name, V, F, p.colors, mat, p.smooth))
    return objs


def clear(objs):
    for o in objs:
        me = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(me)


def render_tile(path):
    sc.render(bpy.context.scene, path)
    return path


def sheet(tiles, out, cols=4):
    rows = math.ceil(len(tiles) / cols)
    W, H = TILE * cols, TILE * rows
    img = np.zeros((H, W, 4), dtype=np.float32)
    for k, path in enumerate(tiles):
        im = bpy.data.images.load(path)
        px = np.array(im.pixels[:], dtype=np.float32).reshape(TILE, TILE, 4)
        r, c = k // cols, k % cols
        img[H - (r + 1) * TILE:H - r * TILE, c * TILE:(c + 1) * TILE] = px
        bpy.data.images.remove(im)
        os.remove(path)
    out_img = bpy.data.images.new("sheet", W, H)
    out_img.pixels.foreach_set(img.ravel())
    out_img.filepath_raw = out
    out_img.file_format = "PNG"
    out_img.save()
    bpy.data.images.remove(out_img)


def render_grip(ch, side, out_dir, mat):
    scene = bpy.context.scene
    cam = scene.camera
    role = ch.role
    pid = ch.held[side][0]
    sx = 1.0 if side == "L" else -1.0
    duration = C.LOOPS[role]["duration"]
    count = int(round(duration * GC.FPS))
    wb = "wrist." + side
    # loop moment with the hand highest: the prop is held up and can be seen
    best_k, best_z, hand_pos = 0, -1e9, {}
    for k in range(count):
        mats = ch.body.bone_matrices(C.local_rotations(role, duration * k / count))
        p = (mats[wb] @ np.r_[ch.heads[wb], 1])[:3]
        hand_pos[k] = (mats[wb] @ np.r_[ch.heads[wb] + np.array((0, 0, -0.25)), 1])[:3]
        if p[2] > best_z:
            best_k, best_z = k, p[2]
    tiles = []
    tmp = str(ROOT / f"world/_grip_{role}_{side}_%d.png")
    rots = C.local_rotations(role, duration * best_k / count)
    objs = show_character(ch, rots, mat)
    V = np.vstack([posed(ch, p.weights, p.verts, rots) for p in ch.pieces])
    lo, hi = V.min(axis=0), V.max(axis=0)
    for az in (-90, 0 if sx > 0 else 180, -90 + sx * 35):
        sc.frame_bounds(cam, lo, hi, az=az, el=8, aspect=1.0, lens=50, margin=0.8)
        tiles.append(render_tile(tmp % len(tiles)))
    c = hand_pos[best_k]
    sc.orbit(cam, tuple(c), -90 + sx * 40, 12, 1.25)
    cam.data.lens = 50
    tiles.append(render_tile(tmp % len(tiles)))
    clear(objs)
    # hand and prop alone, rest pose
    names = ch.bones
    wi = names.index(wb)

    def keep(p):
        if p.name == "prop_" + side:
            return np.ones(len(p.verts), dtype=bool)
        if p.name == "skin":
            return p.weights[:, wi] > 0.5
        return None
    objs = show_character(ch, None, mat, keep)
    c = ch.heads[wb] + np.array((0, 0, -0.3))
    for az, el in ((-90, 5), (0 if sx > 0 else 180, 5), (90, 5), (180 if sx > 0 else 0, 5), (-60, 80), (-60, -80)):
        sc.orbit(cam, tuple(c), az, el, 1.5)
        tiles.append(render_tile(tmp % len(tiles)))
    clear(objs)
    # the hand during the loop
    for k in [int(count * f) for f in (0.0, 0.25, 0.5, 0.75)]:
        rots = C.local_rotations(role, duration * k / count)
        objs = show_character(ch, rots, mat)
        sc.orbit(cam, tuple(hand_pos[k]), -90 + sx * 40, 12, 1.4)
        tiles.append(render_tile(tmp % len(tiles)))
        clear(objs)
    path = str(Path(out_dir) / f"{role}_{side}_{pid}.png")
    sheet(tiles, path)
    return path


def tool_use(ch):
    """Aron's hammer taps the ore: smallest distance hammer head <-> ore over the loop, and the times
    of the closest approach (a tap has to reach the ore without passing into it)."""
    if ch.role != "aron":
        return None
    R = next(p for p in ch.pieces if p.name == "prop_R")
    L = next(p for p in ch.pieces if p.name == "prop_L")
    frame = ch.held["R"][2]
    inv = np.linalg.inv(frame)
    local = (np.c_[R.verts, np.ones(len(R.verts))] @ inv.T)[:, :3]
    head = local[:, 1] < -0.6                                    # the hammer head (prop space)
    duration = C.LOOPS["aron"]["duration"]
    rows = []
    for k in range(int(duration * GC.FPS * 4)):
        t = k / (GC.FPS * 4)
        rots = C.local_rotations("aron", t)
        H = posed(ch, R.weights[head], R.verts[head], rots)
        O = posed(ch, L.weights, L.verts, rots)
        bvh = GC._bvh(O, L.faces)
        d = GC._signed(bvh, H[::3]).min()
        rows.append((t, float(d)))
    d = np.array([r[1] for r in rows])
    taps = [rows[i] for i in range(1, len(rows) - 1) if d[i] <= d[i - 1] and d[i] <= d[i + 1] and d[i] < 0.15]
    return {"closest": round(float(d.min()), 4), "taps": [(round(t, 2), round(v, 4)) for t, v in taps]}


def report_markdown(results, reviews):
    lines = ["# Griff-Validierung", "",
             "Erzeugt von `blender/validate_grips.py`. Automatische Werte aus `blender/village/gripcheck.py`; die",
             "visuelle Wertung stammt aus `docs/grip_reviews.json` und wurde nach Ansicht der Bogen in",
             "`previews/grips/after/` eingetragen. Status:",
             "",
             "- **PASS_AUTOMATED**: alle Messungen ohne Pflichtverletzung, automatische Punkte ≥ 76/85.",
             "- **PASS_VISUAL**: zusätzlich angesehen und ≥ 90/100 gesamt.",
             "- **FAIL**: Pflichtverletzung oder zu wenig Punkte.",
             "- **UNVERIFIED_IN_STUDIO**: gilt für alle: Hautverformung und Darstellung in Roblox sind nicht gesehen.",
             "",
             "| Händler | Hand | Gegenstand | Lage | Finger | Arm | Halt | Bewegung | Visuell | Summe | Status |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in results:
        s = r["scores"]
        v = reviews.get(f"{r['role']}_{r['side']}", {})
        vis = v.get("score")
        auto = sum(s.values())
        total = auto + (vis or 0)
        if r["mandatory"] or auto < 76:
            status = "FAIL"
        elif vis is not None and total >= 90:
            status = "PASS_AUTOMATED, PASS_VISUAL"
        else:
            status = "PASS_AUTOMATED"
        r["status"] = status
        lines.append(f"| {r['role']} | {r['side']} | {r['profile']} | {s['position']} | {s['fingers']} | {s['wrist_arm']} | "
                     f"{s['stability']} | {s['motion']} | {vis if vis is not None else '–'} | {total:.0f} | {status} |")
    lines += ["", "## Einzelheiten", ""]
    for r in results:
        v = reviews.get(f"{r['role']}_{r['side']}", {})
        lines += [f"### {r['role']} – {r['side']} – {r['profile']}", "",
                  f"- Aufgabe: {G.PROFILES[r['profile']]['task']}",
                  f"- Fingerdicke {r['finger_thickness']} Studs, Handlänge {r['hand_length']} Studs",
                  f"- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): "
                  f"{[r['fingers'][i]['touching'] for i in (1, 2, 3, 4, 5)]}, Handfläche {r['palm_gap']} Studs",
                  f"- Tiefste Durchdringung {r['deepest']} Studs; Kontakt auf dem Griffbereich: {r['region_share']:.0%} "
                  f"(Kontakt bei y {r['contact_y']})",
                  f"- Handgelenk {r['wrist_bend']}°, Ellbogen {r['elbow_flexion'][0]}–{r['elbow_flexion'][1]}°, "
                  f"Oberarm max. {r['arm_lift_max']}° gehoben",
                  f"- Verrutschen in der Schleife: {r['slide']} Studs; größter Handschritt {r['hand_step_max']} Studs, "
                  f"Drehung {r['hand_turn_max_deg']}°, Naht {r['seam_step']}",
                  f"- Abstand Gegenstand ↔ Körper in der Schleife: {r['body_clearance']} Studs",
                  f"- Probleme: {r['problems'] or 'keine'}; Pflichtverletzungen: {r['mandatory'] or 'keine'}",
                  f"- Visuelle Prüfung: {v.get('notes', 'noch nicht angesehen')}",
                  f"- Bogen: `previews/grips/after/{r['role']}_{r['side']}_{r['profile']}.png`", ""]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="previews/grips/after")
    ap.add_argument("--only")
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    scene = export.new_scene()
    sc.setup_render(scene, res=(TILE, TILE), samples=16)
    sc.setup_light(scene)
    sc.add_camera(scene)
    mat = material()
    results, extras = [], {}
    for role in ([args.only] if args.only else C.ROLES):
        ch = C.build(role)
        clearance = GC.prop_body_clearance(ch, posed)
        use = tool_use(ch)
        if use:
            extras[role] = {"hammer_to_ore": use}
        for side in ("L", "R"):
            r = GC.check_grip(ch, side)
            r.update(role=role, side=side, body_clearance=round(clearance[side][0], 4),
                     body_clearance_time=clearance[side][1])
            if clearance[side][0] < -0.5 * r["finger_thickness"]:
                r["mandatory"].append(f"the {r['profile']} passes {-clearance[side][0]:.3f} studs into the body at "
                                      f"t={clearance[side][1]} s")
            if not args.no_render:
                r["sheet"] = render_grip(ch, side, out_dir, mat)
            results.append(r)
            print(f"[grips] {role} {side} {r['profile']}: scores {r['scores']}, problems {r['problems']}, "
                  f"mandatory {r['mandatory']}", flush=True)
        if use:
            print(f"[grips] {role} hammer -> ore: {use}", flush=True)
    data = {"results": results, "extras": extras}
    (out_dir / "grip_validation.json").write_text(json.dumps(data, indent=1, default=float), encoding="utf-8")
    if args.out.rstrip("/").endswith("after") and not args.only:
        rv = ROOT / "docs/grip_reviews.json"
        reviews = json.loads(rv.read_text(encoding="utf-8")) if rv.exists() else {}
        (ROOT / "docs/GRIP_VALIDATION_REPORT.md").write_text(report_markdown(results, reviews), encoding="utf-8")
    failed = [r for r in results if r["mandatory"]]
    print(f"grip validation: {len(results)} grips, {len(failed)} with mandatory failures")


if __name__ == "__main__":
    main()
