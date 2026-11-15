"""Automated checks for the generated project (no Blender needed, only numpy).

    python blender/validate.py            # prints a report, writes docs/validation_report.md
                                          # exit code 1 if any check fails

Checks: file formats, glTF structure, triangle budgets, degenerate geometry,
UV / palette usage, scale and origin conventions, manifest <-> export
consistency, the level plan (overlaps, bounds, ground contact, coordinate
conversion) and the Roblox scripts (through tests/test_roblox_builder.py).
"""
import json
import math
import os
import struct
import subprocess
import sys
import zlib

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TRI_LIMIT = 10000
TRI_BUDGET = {"houses": 8000, "landmarks": 10000, "nature": 800, "props": 1200, "terrain": 4500}
# plausible overall size (studs) per category: (min height, max height, max footprint)
SIZE_RULES = {"houses": (18, 60, 48), "landmarks": (20, 75, 60)}
COMPONENT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


class Report:
    def __init__(self):
        self.rows = []          # (status, section, message)

    def ok(self, section, msg):
        self.rows.append(("PASS", section, msg))

    def fail(self, section, msg):
        self.rows.append(("FAIL", section, msg))

    def info(self, section, msg):
        self.rows.append(("INFO", section, msg))

    def check(self, cond, section, msg_ok, msg_fail=None):
        (self.ok if cond else self.fail)(section, msg_ok if cond else (msg_fail or msg_ok))
        return cond

    @property
    def failed(self):
        return [r for r in self.rows if r[0] == "FAIL"]


def path(*p):
    return os.path.join(ROOT, *p)


# ---------------------------------------------------------------- glTF reading
class Glb:
    def __init__(self, filepath):
        data = open(filepath, "rb").read()
        magic, version, length = struct.unpack("<III", data[:12])
        assert magic == 0x46546C67, "not a GLB file"
        assert version == 2, f"glTF version {version}"
        assert length == len(data), "length field does not match the file size"
        off = 12
        self.json, self.bin = None, b""
        while off < len(data):
            clen, ctype = struct.unpack("<II", data[off:off + 8])
            chunk = data[off + 8:off + 8 + clen]
            if ctype == 0x4E4F534A:
                self.json = json.loads(chunk)
            elif ctype == 0x004E4942:
                self.bin = chunk
            off += 8 + clen
        self.size = len(data)

    def accessor(self, index):
        acc = self.json["accessors"][index]
        view = self.json["bufferViews"][acc["bufferView"]]
        fmt, width = COMPONENT[acc["componentType"]]
        ncomp = NCOMP[acc["type"]]
        start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
        stride = view.get("byteStride", 0)
        count = acc["count"]
        if stride and stride != width * ncomp:
            raw = b"".join(self.bin[start + i * stride:start + i * stride + width * ncomp] for i in range(count))
        else:
            raw = self.bin[start:start + count * width * ncomp]
        arr = np.frombuffer(raw, dtype="<" + fmt).reshape(count, ncomp)
        return arr

    def image_png(self, index):
        img = self.json["images"][index]
        view = self.json["bufferViews"][img["bufferView"]]
        start = view.get("byteOffset", 0)
        return self.bin[start:start + view["byteLength"]]


def png_size(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    return struct.unpack(">II", data[16:24])


def png_pixels(data):
    """Decode a non-interlaced 8-bit RGB PNG (as written by palette.py)."""
    w, h = png_size(data)
    off, idat = 8, b""
    while off < len(data):
        n, tag = struct.unpack(">I4s", data[off:off + 8])
        if tag == b"IDAT":
            idat += data[off + 8:off + 8 + n]
        off += 12 + n
    raw = zlib.decompress(idat)
    rows = np.frombuffer(raw, dtype=np.uint8).reshape(h, 1 + w * 3)
    assert (rows[:, 0] == 0).all(), "unexpected PNG filter"
    return rows[:, 1:].reshape(h, w, 3)


# ---------------------------------------------------------------- asset checks
def check_asset(rep, name, a, palette_cols):
    sec = f"asset:{name}"
    problems = []
    cat = a["category"]
    glb_path = path(a["glb"])
    if not os.path.exists(glb_path):
        rep.fail(sec, f"missing export {a['glb']}")
        return None
    try:
        g = Glb(glb_path)
    except AssertionError as exc:
        rep.fail(sec, f"invalid GLB: {exc}")
        return None
    j = g.json
    if len(j.get("meshes", [])) != 1 or len(j["meshes"][0]["primitives"]) != 1:
        problems.append("must contain exactly one mesh with one primitive (one MeshPart, one texture)")
    prim = j["meshes"][0]["primitives"][0]
    for attr in ("POSITION", "NORMAL", "TEXCOORD_0"):
        if attr not in prim["attributes"]:
            problems.append(f"missing attribute {attr}")
    if "COLOR_0" in prim["attributes"]:
        problems.append("vertex colours present (they would be multiplied with the texture in Roblox)")
    mats = j.get("materials", [])
    if len(mats) != 1 or "baseColorTexture" not in mats[0].get("pbrMetallicRoughness", {}):
        problems.append("needs exactly one material with a base colour texture")
    if len(j.get("images", [])) != 1:
        problems.append("palette texture is not embedded exactly once")
    else:
        if png_size(g.image_png(0)) != (1024, 64):
            problems.append("embedded texture is not the 1024x64 palette")
    node = j["nodes"][0]
    if node.get("name") != name:
        problems.append(f"node name '{node.get('name')}' != asset id")
    if any(k in node for k in ("rotation", "scale", "translation", "matrix")):
        problems.append("node carries a transform (must be baked)")

    pos = g.accessor(prim["attributes"]["POSITION"]).astype(np.float64)
    nrm = g.accessor(prim["attributes"]["NORMAL"]).astype(np.float64)
    uv = g.accessor(prim["attributes"]["TEXCOORD_0"]).astype(np.float64)
    idx = g.accessor(prim["indices"]).reshape(-1, 3).astype(np.int64)
    tris = len(idx)
    if not np.isfinite(pos).all() or not np.isfinite(uv).all():
        problems.append("NaN / inf in vertex data")
    if idx.max() >= len(pos):
        problems.append("index out of range")
    if tris != a["triangles"]:
        problems.append(f"triangle count {tris} != manifest {a['triangles']}")
    if tris > TRI_LIMIT:
        problems.append(f"{tris} triangles exceed the hard limit {TRI_LIMIT}")
    if tris > TRI_BUDGET.get(cat, TRI_LIMIT):
        problems.append(f"{tris} triangles exceed the {cat} budget {TRI_BUDGET[cat]}")
    # degenerate triangles
    p0, p1, p2 = pos[idx[:, 0]], pos[idx[:, 1]], pos[idx[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0), axis=1)
    degenerate = int((area < 1e-7).sum())
    if degenerate:
        problems.append(f"{degenerate} zero-area triangles")
    bad_n = int((np.abs(np.linalg.norm(nrm, axis=1) - 1) > 1e-2).sum())
    if bad_n:
        problems.append(f"{bad_n} non-unit normals")
    # normals must agree with the triangle winding (Roblox culls back faces)
    fn = np.cross(p1 - p0, p2 - p0)
    vn = nrm[idx[:, 0]] + nrm[idx[:, 1]] + nrm[idx[:, 2]]
    flipped = int(((fn * vn).sum(axis=1) < -1e-9)[area > 1e-7].sum())
    if flipped:
        problems.append(f"{flipped} triangles wound against their normals")
    # UVs: inside the texture and on the centre line of a used palette column
    if uv.min() < -1e-6 or uv.max() > 1 + 1e-6:
        problems.append("UVs outside 0..1")
    col = uv[:, 0] * 64
    off_centre = np.abs(col - np.floor(col) - 0.5).max()
    if off_centre > 0.02:
        problems.append("UVs are not centred on a palette column")
    if int(np.floor(col).max()) >= palette_cols:
        problems.append("UV points at an unused (black) palette column")
    # bounds must match the manifest (Roblox axes = glTF axes)
    br = a["bounds_roblox"]
    err = max(np.abs(pos.min(axis=0) - br["min"]).max(), np.abs(pos.max(axis=0) - br["max"]).max())
    if err > 2e-3:
        problems.append(f"bounds differ from the manifest by {err:.4f} studs")
    # scale / origin conventions
    size = np.array(br["size"])
    if cat in SIZE_RULES:
        lo, hi, foot = SIZE_RULES[cat]
        top = br["max"][1]
        if not (lo <= top <= hi):
            problems.append(f"height {top:.1f} studs outside the plausible range {lo}..{hi}")
        if max(size[0], size[2]) > foot:
            problems.append(f"footprint {max(size[0], size[2]):.1f} studs too large")
    if cat != "terrain":
        if br["min"][1] > 0.06:
            problems.append(f"lowest point {br['min'][1]:.2f} is above the ground plane (asset would float)")
        if br["min"][1] < -10.0:
            problems.append("asset reaches more than 10 studs below its origin")
        if cat in ("houses", "landmarks") and math.hypot(br["center"][0], br["center"][2]) > 12:
            problems.append("origin is far from the centre of the footprint")
    blend = path(a["blend"])
    if not os.path.exists(blend):
        problems.append(f"missing source {a['blend']}")
    else:
        head = open(blend, "rb").read(8)
        if not (head.startswith(b"BLENDER") or head[:4] == b"\x28\xb5\x2f\xfd"):
            problems.append("source is not a .blend file")
    if problems:
        for p in problems:
            rep.fail(sec, p)
    return {"tris": tris, "size": size, "glb_kb": g.size / 1024, "problems": len(problems)}


def check_fbx(rep, rel):
    p = path(rel)
    if not os.path.exists(p):
        rep.fail("fbx", f"missing {rel}")
        return
    head = open(p, "rb").read(27)
    version = struct.unpack("<I", head[23:27])[0] if len(head) >= 27 else 0
    rep.check(head.startswith(b"Kaydara FBX Binary"), "fbx",
              f"{rel}: binary FBX, version {version}, {os.path.getsize(p) / 1e6:.1f} MB", f"{rel}: not a binary FBX")


def check_library(rep, rel, expected_names):
    p = path(rel)
    if not os.path.exists(p):
        rep.fail("library", f"missing {rel}")
        return
    g = Glb(p)
    names = [n.get("name") for n in g.json["nodes"] if "mesh" in n]
    missing = sorted(set(expected_names) - set(names))
    extra = sorted(set(names) - set(expected_names))
    rep.check(not missing and not extra, "library",
              f"{rel}: {len(names)} named meshes, one per asset ({g.size / 1e6:.1f} MB)",
              f"{rel}: missing {missing[:5]} extra {extra[:5]}")
    rep.check(len(g.json.get("images", [])) == 1, "library", f"{rel}: palette texture embedded once")


# ---------------------------------------------------------------- layout checks
def check_layout(rep, layout, heightmap):
    from village.plan import Footprint
    from village import terrain as tr
    sec = "layout"
    assets, insts = layout["assets"], layout["instances"]
    ids = [i["id"] for i in insts]
    rep.check(len(ids) == len(set(ids)), sec, f"{len(ids)} instance ids are unique")
    unknown = sorted({i["asset"] for i in insts} - set(assets))
    rep.check(not unknown, sec, "every instance references a known asset", f"unknown assets: {unknown}")

    worst = 0.0
    for i in insts:
        x, y, z = i["blender"]["location"]
        rx, ry, rz = i["roblox"]["position"]
        worst = max(worst, abs(rx - x), abs(ry - z), abs(rz + y), abs(i["roblox"]["yaw_deg"] - i["blender"]["rotation_z_deg"]))
    rep.check(worst < 1e-3, sec, "Roblox transforms equal the converted Blender transforms (x, z, -y; same yaw)",
              f"coordinate conversion mismatch {worst}")

    half = layout["meta"]["world_size"] / 2
    outside = [i["id"] for i in insts if abs(i["blender"]["location"][0]) > half or abs(i["blender"]["location"][1]) > half]
    rep.check(not outside, sec, "all instances lie inside the world bounds", f"outside: {outside[:5]}")

    houses = [i for i in insts if assets[i["asset"]]["category"] == "houses"]
    landmarks = [i for i in insts if assets[i["asset"]]["category"] == "landmarks"]
    distinct = len({i["asset"] for i in houses})
    rep.check(15 <= distinct <= 25, sec, f"{distinct} individually modelled houses placed (target 15-25)",
              f"{distinct} distinct houses (target 15-25)")
    rep.check(len(landmarks) >= 3, sec, f"{len(landmarks)} landmark buildings placed")

    H = np.array(heightmap["heights"])
    grid = tr.HeightGrid(H)
    rep.check(H.shape == (tr.N + 1, tr.N + 1), sec, f"height map is {H.shape[0]} x {H.shape[1]} samples, "
              f"{H.min():.1f} .. {H.max():.1f} studs")
    rep.check(H.max() - H.min() > 20, sec, "terrain has real height variation (hills, valley)")

    def fake(i):
        return {"x": i["blender"]["location"][0], "y": i["blender"]["location"][1],
                "rot": i["blender"]["rotation_z_deg"], "scale": i["blender"]["scale"]}

    blds = houses + landmarks
    fps = [(i["id"], Footprint(fake(i), assets[i["asset"]]["bounds_blender"])) for i in blds]
    overlaps = [(a[0], b[0]) for k, a in enumerate(fps) for b in fps[k + 1:] if a[1].overlaps(b[1])]
    rep.check(not overlaps, sec, f"no two of the {len(blds)} buildings overlap", f"overlapping buildings: {overlaps}")

    # roads / water vs buildings
    def dist_to_polyline(px, py, pts):
        best = 1e9
        for (x0, _y0, z0), (x1, _y1, z1) in zip(pts[:-1], pts[1:]):
            ax, ay, bx, by = x0, -z0, x1, -z1                 # roblox (x, y, z) -> blender (x, -z)
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-12)))
            best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
        return best

    blocked = []
    for uid, fp in fps:
        pts = fp.corners() + [(fp.cx, fp.cy)]
        for rd in layout["roads"]:
            if min(dist_to_polyline(px, py, rd["points_roblox"]) for px, py in pts) < rd["half_width"] - 0.5:
                blocked.append((uid, rd["id"]))
    rep.check(not blocked, sec, "no building stands on a road", f"buildings on roads: {blocked}")
    wet = []
    wpts, whw = layout["water"]["points_roblox"], layout["water"]["half_width"]
    for uid, fp in fps:
        for px, py in fp.corners():
            for k in range(len(wpts)):
                if math.hypot(px - wpts[k][0], py + wpts[k][2]) < whw[k] + 1.0:
                    wet.append(uid)
    rep.check(not wet, sec, "no building stands in the water", f"buildings in the water: {sorted(set(wet))}")

    # ground contact: origin height vs terrain height
    floating = []
    free_z = {"bridge_stone", "dock", "rowboat", "lily_pads", "reeds", "fountain"}
    for i in insts:
        a = assets[i["asset"]]
        if a["category"] == "terrain" or i["asset"] in free_z:
            continue
        x, y, z = i["blender"]["location"]
        dz = z - grid.at(x, y)
        if abs(dz) > 2.2:
            floating.append((i["id"], round(dz, 2)))
    rep.check(not floating, sec, "every object sits on the terrain (origin within 2.2 studs of the ground)",
              f"{len(floating)} objects off the ground, e.g. {floating[:6]}")

    # building ground: how uneven is the terrain under each footprint?
    worst_b = ("", 0.0)
    for i in blds:
        fp = Footprint(fake(i), assets[i["asset"]]["bounds_blender"], shrink=0.8)
        hs = [grid.at(px, py) for px, py in fp.corners()]
        z = i["blender"]["location"][2]
        d = max(z - min(hs), max(hs) - z)
        if d > worst_b[1]:
            worst_b = (i["id"], d)
    rep.check(worst_b[1] < 3.6, sec, f"terrain under buildings is level enough (worst {worst_b[1]:.2f} studs at "
              f"{worst_b[0]}; foundations reach 4 studs down)", f"terrain too uneven under {worst_b}")

    chunks = [i for i in insts if i["asset"].startswith("terrain_r")]
    n = tr.N // tr.CHUNK_CELLS
    rep.check(len(chunks) == n * n, sec, f"{len(chunks)} terrain chunks cover the {tr.WORLD:.0f} x {tr.WORLD:.0f} stud world")
    tri_total = sum(assets[i["asset"]]["triangles"] for i in insts)
    rep.info(sec, f"{len(insts)} instances, {len(assets)} unique meshes, {tri_total} triangles in the whole world")
    by_group = {}
    for i in insts:
        g = by_group.setdefault(i["group"], [0, 0])
        g[0] += 1
        g[1] += assets[i["asset"]]["triangles"]
    for gname, (cnt, tri) in sorted(by_group.items()):
        rep.info(sec, f"group {gname}: {cnt} instances, {tri} triangles")
    return tri_total


def main():
    rep = Report()
    # palette
    from village import palette
    tex = path("exports", "textures", palette.TEXTURE_NAME)
    if rep.check(os.path.exists(tex), "palette", "palette texture exists"):
        data = open(tex, "rb").read()
        w, h = png_size(data)
        rep.check((w, h) == (palette.TEX_W, palette.TEX_H), "palette", f"palette is {w} x {h} px")
        px = png_pixels(data)
        ok = all(abs(int(px[h // 2, i * palette.COLUMN_PX + 8, c]) - round(palette.tone(palette.RGB[n], 0.5 - 0.5 / h)[c] * 255)) <= 3
                 for i, (n, _) in enumerate(palette.COLORS) for c in range(3))
        rep.check(ok, "palette", f"{len(palette.COLORS)} colour columns match the palette definition")

    manifest = json.load(open(path("world", "asset_manifest.json")))["assets"]
    layout = json.load(open(path("world", "world_layout.json")))
    heightmap = json.load(open(path("world", "heightmap.json")))
    all_assets = dict(layout["assets"])
    all_assets.update(manifest)

    stats = {}
    for name, a in all_assets.items():
        s = check_asset(rep, name, a, len(palette.COLORS))
        if s:
            stats[name] = (a["category"], s)
    clean = sum(1 for _c, s in stats.values() if s["problems"] == 0)
    rep.check(clean == len(all_assets), "assets", f"{clean}/{len(all_assets)} meshes pass all geometry, UV, scale and format checks")
    for cat in sorted({c for c, _ in stats.values()}):
        tri = [s["tris"] for c, s in stats.values() if c == cat]
        rep.info("assets", f"{cat}: {len(tri)} meshes, {min(tri)}-{max(tri)} triangles each, {sum(tri)} in total "
                 f"(budget {TRI_BUDGET.get(cat)})")

    lib_names = list(manifest)
    check_library(rep, "exports/library/village_assets.glb", lib_names)
    check_library(rep, "exports/library/village_terrain.glb",
                  [n for n, a in layout["assets"].items() if a["category"] == "terrain"])
    check_fbx(rep, "exports/library/village_assets.fbx")
    check_fbx(rep, "exports/library/village_terrain.fbx")
    for rel in ("world/village_world.blend", "assets/village_asset_library.blend"):
        rep.check(os.path.exists(path(rel)), "sources", f"{rel} exists ({os.path.getsize(path(rel)) / 1e6:.1f} MB)"
                  if os.path.exists(path(rel)) else f"{rel} missing")

    check_layout(rep, layout, heightmap)

    # roblox scripts
    for rel in ("roblox/WorldLayout.lua", "roblox/WorldHeightmap.lua", "roblox/VillageWorldBuilder.lua",
                "roblox/VillageTerrainBuilder.lua"):
        size = os.path.getsize(path(rel)) if os.path.exists(path(rel)) else 0
        rep.check(0 < size < 200000, "roblox", f"{rel}: {size} characters (Roblox script limit 200000)",
                  f"{rel}: {size} characters - missing or above the 200000 character script limit")
    try:
        import lupa  # noqa: F401
        res = subprocess.run([sys.executable, path("tests", "test_roblox_builder.py")], capture_output=True, text=True)
        last = (res.stdout.strip().splitlines() or ["no output"])[-1]
        rep.check(res.returncode == 0, "roblox", "Luau scripts executed against the Roblox API mock: " + last,
                  "Luau script test failed: " + last + res.stderr[-300:])
    except ImportError:
        rep.info("roblox", "lupa not installed - Luau script test skipped")

    # back-face audit (written by blender/audit_backfaces.py)
    audit_path = path("world", "backface_audit.json")
    if os.path.exists(audit_path):
        audit = json.load(open(audit_path))["results"]
        missing = sorted(set(all_assets) - set(audit))
        rep.check(not missing, "backfaces", f"back-face audit covers all {len(audit)} meshes",
                  f"meshes without audit: {missing[:6]}")
        # single pixels are ray-tracing noise at shared edges; an inverted part covers far more
        bad = {k: v["backface_pixels"] for k, v in audit.items()
               if v["backface_pixels"] > max(8, v["front_pixels"] * 1e-4)}
        noise = sum(1 for v in audit.values() if 0 < v["backface_pixels"] <= 8)
        rep.check(not bad, "backfaces",
                  f"no mesh shows inside-out faces from outside ({noise} meshes with 1-8 stray pixels out of "
                  f"{audit[next(iter(audit))]['views']}+ views each, treated as sampling noise)",
                  f"visible back faces: {bad}")
    else:
        rep.fail("backfaces", "world/backface_audit.json missing - run blender/audit_backfaces.py")

    previews = [f for f in os.listdir(path("previews", "world"))] if os.path.isdir(path("previews", "world")) else []
    rep.check(len(previews) >= 5, "previews", f"{len(previews)} world preview renders present")

    # ---- output
    lines = ["# Validation report", "",
             "Generated by `python blender/validate.py`. PASS/FAIL lines are hard checks, INFO lines are statistics.",
             "", "| Status | Area | Check |", "|---|---|---|"]
    for status, section, msg in rep.rows:
        if section.startswith("asset:") and status != "FAIL":
            continue
        lines.append(f"| {status} | {section} | {msg} |")
    n_fail = len(rep.failed)
    n_pass = sum(1 for r in rep.rows if r[0] == "PASS")
    lines += ["", f"**Result: {n_pass} checks passed, {n_fail} failed.**", ""]
    os.makedirs(path("docs"), exist_ok=True)
    with open(path("docs", "validation_report.md"), "w") as fh:
        fh.write("\n".join(lines))
    for status, section, msg in rep.rows:
        print(f"{status:4s} [{section}] {msg}")
    print(f"\n{n_pass} passed, {n_fail} failed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
