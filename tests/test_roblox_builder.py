"""Executes the Luau integration scripts against a mock of the Roblox API.

What is verified
  * roblox/*.lua parse and run in a Lua 5.x interpreter (they use the Lua 5.1
    subset of Luau on purpose).
  * VillageWorldBuilder puts every mesh exactly where the Blender level plan
    says: the expected world-space bounding box of every instance is computed
    here from the *Blender* data in world_layout.json (independent maths) and
    compared with the bounding box of the part the Lua code produced.
  * The builder copes with arbitrary import scale / position of the templates
    and with templates wrapped in Models.
  * Collision proxies, light anchors, group filters, missing templates and the
    `origin` option behave as documented.
  * VillageTerrainBuilder decodes the height map correctly.

What is NOT verified: behaviour of the real Roblox engine and importer.

    python tests/test_roblox_builder.py
"""
import json
import math
import os
import sys

from lupa import LuaRuntime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOL = 2e-3


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def new_runtime():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(read("tests", "roblox_mock.lua"))
    loader = lua.eval("""function(src, name)
        local fn, err = load(src, "=" .. name)
        if not fn then error(err) end
        return fn()
    end""")
    mods = {name: loader(read("roblox", name + ".lua"), name)
            for name in ("WorldLayout", "WorldHeightmap", "VillageWorldBuilder", "VillageTerrainBuilder")}
    lua.globals().Layout = mods["WorldLayout"]
    lua.globals().Heightmap = mods["WorldHeightmap"]
    lua.globals().Builder = mods["VillageWorldBuilder"]
    lua.globals().TerrainBuilder = mods["VillageTerrainBuilder"]
    lua.execute(HELPERS)
    return lua


# Lua side helpers: fake "imported" templates and result extraction
HELPERS = r"""
-- Creates templates as if the importer had dropped them at odd scales and places.
function makeTemplates(skip, distort)
    local folder = Instance.new("Folder")
    folder.Name = "VillageAssets"
    local scales = { 1, 0.01, 100, 3.5714, 0.28 }
    for index, name in ipairs(Layout.assetNames) do
        if name ~= skip then
            local def = Layout.assets[name]
            local k = scales[(index % #scales) + 1]
            local size = Vector3.new(def.size[1], def.size[2], def.size[3]) * k
            if name == distort then
                size = Vector3.new(size.X * 1.3, size.Y, size.Z)
            end
            local offset = Vector3.new(index * 37.5, -index * 3.25, 1000 - index * 11)
            local part = Instance.new("MeshPart")
            part.Name = name
            part.Size = size
            part.CFrame = CFrame.new(offset + Vector3.new(def.center[1], def.center[2], def.center[3]) * k)
            if index % 3 == 0 then           -- importer wrapped the mesh in a Model of the same name
                local model = Instance.new("Model")
                model.Name = name
                part.Parent = model
                model.Parent = folder
            elseif index % 3 == 1 then       -- nested inside the library model
                local lib = folder:FindFirstChild("village_assets") or Instance.new("Model", folder)
                lib.Name = "village_assets"
                part.Parent = lib
            else
                part.Parent = folder
            end
        end
    end
    return folder
end

-- Flattens the build result into plain arrays for the Python side.
function collect(report)
    local rows = {}
    for _, group in ipairs(report.folder:GetChildren()) do
        if group:IsA("Folder") then
            for _, model in ipairs(group:GetChildren()) do
                local asset = model:GetAttribute("AssetId")
                local mesh, colliders, lights, collide = nil, 0, 0, false
                for _, d in ipairs(model:GetDescendants()) do
                    if d:IsA("MeshPart") then
                        mesh = d
                        collide = d.CanCollide
                    elseif d.Name == "Collider" then
                        colliders = colliders + 1
                    elseif d:IsA("PointLight") then
                        lights = lights + 1
                    end
                end
                local lo, hi = Builder._worldBounds({ mesh })
                rows[#rows + 1] = { model:GetAttribute("LayoutIndex"), asset, group.Name, lo.X, lo.Y, lo.Z, hi.X, hi.Y,
                    hi.Z, colliders, lights, collide and 1 or 0, model.Name, mesh.Transparency }
            end
        end
    end
    return rows
end
"""


def rot_z(p, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def to_roblox(p):
    return (p[0], p[2], -p[1])


def origin_apply(p, origin):
    """origin = (tx, ty, tz, yaw_deg) in Roblox space; yaw around +Y."""
    if origin is None:
        return p
    tx, ty, tz, yaw = origin
    a = math.radians(yaw)
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c + p[2] * s + tx, p[1] + ty, -p[0] * s + p[2] * c + tz)


def expected_bounds(inst, asset, origin=None):
    """World AABB in Roblox space, derived from the Blender transform."""
    b = asset["bounds_blender"]
    loc, rot, scale = inst["blender"]["location"], inst["blender"]["rotation_z_deg"], inst["blender"]["scale"]
    pts = []
    for x in (b["min"][0], b["max"][0]):
        for y in (b["min"][1], b["max"][1]):
            for z in (b["min"][2], b["max"][2]):
                p = rot_z((x * scale, y * scale, z * scale), rot)
                p = (p[0] + loc[0], p[1] + loc[1], p[2] + loc[2])
                pts.append(origin_apply(to_roblox(p), origin))
    return [min(p[i] for p in pts) for i in range(3)] + [max(p[i] for p in pts) for i in range(3)]


def check_build(lua, layout, origin=None, label=""):
    if origin is None:
        report = lua.eval("Builder.build({ templates = makeTemplates(), layout = Layout, verbose = false })")
    else:
        tx, ty, tz, yaw = origin
        report = lua.eval(f"Builder.build({{ templates = makeTemplates(), layout = Layout, verbose = false, "
                          f"origin = CFrame.new({tx}, {ty}, {tz}) * CFrame.Angles(0, math.rad({yaw}), 0) }})")
    rows = lua.globals().collect(report)
    n_expected = len(layout["instances"])
    assert report.placed == n_expected, (report.placed, n_expected)
    assert len(rows) == n_expected
    assert len(report.warnings) == 0, list(report.warnings.values())[:5]
    worst = 0.0
    seen = set()
    for row in rows.values():
        r = list(row.values())
        index, asset_name, group = int(r[0]), r[1], r[2]
        inst = layout["instances"][index - 1]
        asset = layout["assets"][inst["asset"]]
        assert inst["asset"] == asset_name and inst["group"] == group
        exp = expected_bounds(inst, asset, origin)
        err = max(abs(a - b) for a, b in zip(exp, r[3:9]))
        scale_tol = TOL * max(1.0, max(abs(v) for v in exp) / 200.0)
        assert err < scale_tol, f"{inst['id']}: bounding box off by {err:.4f} studs\n exp {exp}\n got {r[3:9]}"
        worst = max(worst, err)
        proxy = asset["collision"] == "proxy"
        assert int(r[9]) == (len(asset["colliders"]) if proxy else 0), (inst["id"], r[9])
        assert int(r[10]) == len(asset["lights"]), (inst["id"], r[10])
        assert bool(r[11]) == (asset["collision"] in ("mesh", "mesh_precise")), (inst["id"], asset["collision"])
        assert r[12] == inst.get("name", inst["asset"])
        if asset.get("transparency"):
            assert abs(r[13] - asset["transparency"]) < 1e-9
        seen.add(index)
    assert len(seen) == n_expected
    precise = {k for k in report.needsPreciseCollision}
    wanted = {i["asset"] for i in layout["instances"] if layout["assets"][i["asset"]]["collision"] == "mesh_precise"}
    assert precise == wanted, (precise ^ wanted)
    print(f"  ok  build {label:28s} {len(rows)} instances, max bounding-box error {worst:.5f} studs")


def main():
    layout = json.loads(read("world", "world_layout.json"))
    lua = new_runtime()
    print("Lua runtime:", lua.eval("_VERSION"))

    # generated module must mirror the JSON
    L = lua.globals().Layout
    assert len(L.instances) == len(layout["instances"])
    assert len(L.assetNames) == len(layout["assets"])
    for k in (1, len(layout["instances"]) // 2, len(layout["instances"])):
        row = list(L.instances[k].values())
        inst = layout["instances"][k - 1]
        assert L.assetNames[int(row[0])] == inst["asset"]
        assert all(abs(a - b) < 1e-3 for a, b in zip(row[1:4], inst["roblox"]["position"]))
    print("  ok  WorldLayout.lua mirrors world_layout.json")

    check_build(lua, layout, None, "at the origin")
    check_build(lua, layout, (1200.0, 64.0, -850.0, 90.0), "moved + rotated 90 deg")
    check_build(lua, layout, (-333.0, -20.0, 77.0, 33.0), "moved + rotated 33 deg")

    # group filters
    rep = lua.eval("Builder.build({ templates = makeTemplates(), layout = Layout, verbose = false, "
                   "includeGroups = { buildings = true } })")
    n_buildings = sum(1 for i in layout["instances"] if i["group"] == "buildings")
    assert rep.placed == n_buildings and rep.skipped == len(layout["instances"]) - n_buildings
    rep = lua.eval("Builder.build({ templates = makeTemplates(), layout = Layout, verbose = false, "
                   "excludeGroups = { nature = true, terrain = true } })")
    n_rest = sum(1 for i in layout["instances"] if i["group"] not in ("nature", "terrain"))
    assert rep.placed == n_rest
    print(f"  ok  group filters ({n_buildings} buildings / {n_rest} without nature+terrain)")

    # missing and distorted templates are reported, not fatal
    rep = lua.eval('Builder.build({ templates = makeTemplates("tree_oak_a", "lm_chapel"), layout = Layout, '
                   'verbose = false })')
    n_oak = sum(1 for i in layout["instances"] if i["asset"] == "tree_oak_a")
    assert rep.missing["tree_oak_a"] == n_oak and rep.placed == len(layout["instances"]) - n_oak
    warnings = list(rep.warnings.values())
    assert any("tree_oak_a" in w and "not found" in w for w in warnings)
    assert any("lm_chapel" in w and "proportions" in w for w in warnings), warnings
    print(f"  ok  missing template -> {n_oak} instances reported, distorted template -> warning")

    # proxies off: meshes collide themselves
    rep = lua.eval("Builder.build({ templates = makeTemplates(), layout = Layout, verbose = false, "
                   "createColliders = false, createLights = false, includeGroups = { buildings = true } })")
    rows = lua.globals().collect(rep)
    assert all(int(list(r.values())[9]) == 0 and int(list(r.values())[10]) == 0 and int(list(r.values())[11]) == 1
               for r in rows.values())
    print("  ok  createColliders / createLights switches")

    # verbose summary + template check helpers run without errors
    lua.execute("Builder.build({ templates = makeTemplates('bench'), layout = Layout, includeGroups = { props = true } })")
    found_missing = lua.eval("{ Builder.checkTemplates(makeTemplates('bench'), Layout) }")
    assert len(found_missing[2]) == 1 and found_missing[2][1] == "bench"
    print("  ok  checkTemplates")

    # height map decoding + voxel terrain call pattern
    hm = json.loads(read("world", "heightmap.json"))
    flat = [v for row in hm["heights"] for v in row]
    decoded = list(lua.eval("TerrainBuilder.decodeHeights(Heightmap)").values())
    assert len(decoded) == len(flat)
    err = max(abs(a - b) for a, b in zip(flat, decoded))
    assert err <= 0.016, err
    res = lua.eval("TerrainBuilder.build({ heightmap = Heightmap })")
    n = hm["vertices_per_side"] - 1
    fills = lua.globals().MOCK_FILLS
    n_water = sum(1 for f in fills.values() if f.material == "Enum.Material.Water")
    assert res.cells == n * n and len(fills) == n * n + n_water and n_water > 50
    f = fills[1]                       # first cell: south-west corner in Blender = (-X, +Z) in Roblox
    assert abs(f.cframe.X - (-382.0)) < 1e-6 and abs(f.cframe.Z - 382.0) < 1e-6
    top = f.cframe.Y + f.size.Y / 2
    assert abs(top - sum((hm["heights"][0][0], hm["heights"][0][1], hm["heights"][1][0], hm["heights"][1][1])) / 4) < 0.02
    print(f"  ok  height map decode (max error {err:.3f} studs), {n * n} terrain cells + {n_water} water blocks")
    print("ALL ROBLOX SCRIPT TESTS PASSED")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print("FAILED:", exc)
        sys.exit(1)
