"""Checks the generated place file and runs VillageAutoBuild against the Roblox API mock.

Verified here: the place file is well-formed XML, every script sits in the expected service with its
full source; the greybox blocks have the planned bounding boxes; with templates the real builder is
used.  NOT verified: that Roblox Studio opens the file.
"""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

from lupa import LuaRuntime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from test_roblox_builder import HELPERS, expected_bounds, read  # noqa: E402


def check_place():
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_place.py")], check=True, stdout=subprocess.DEVNULL)
    place_path = os.path.join(ROOT, "exports", "roblox", "ArcaneVillage.rbxlx")
    with open(place_path, "rb") as fh:
        # Roblox Open Cloud rejects the upload if anything follows </roblox>.
        assert fh.read().endswith(b"</roblox>"), "place file must end exactly with </roblox>"
    tree = ET.parse(place_path)
    root = tree.getroot()
    assert root.tag == "roblox" and root.get("version") == "4"

    def children(node):
        return {c.find("Properties/string[@name='Name']").text: c for c in node.findall("Item")}

    def source(node):
        return node.find("Properties/ProtectedString[@name='Source']").text

    services = children(root)
    for s in ("Workspace", "ReplicatedStorage", "ServerStorage", "ServerScriptService", "StarterPlayer"):
        assert s in services, s
    shared = children(children(services["ReplicatedStorage"])["ArcaneShared"])
    server = children(children(services["ServerScriptService"])["ArcaneServer"])
    client = children(children(children(services["StarterPlayer"])["StarterPlayerScripts"])["ArcaneClient"])
    village = children(children(services["ServerStorage"])["VillageWorld"])
    assert server["Bootstrap"].get("class") == "Script" and client["Bootstrap"].get("class") == "LocalScript"
    assert children(services["ServerScriptService"])["VillageAutoBuild"].get("class") == "Script"
    for name in ("Items", "Recipes", "Machines", "Protocol"):
        assert shared[name].get("class") == "ModuleScript"
    assert source(shared["Recipes"]) == read("roblox", "gameplay", "shared", "Recipes.lua")
    assert source(village["WorldLayout"]) == read("roblox", "WorldLayout.lua")
    assert source(server["Actions"]) == read("roblox", "gameplay", "server", "Actions.lua")
    n = len(list(root.iter("Item")))
    refs = [i.get("referent") for i in root.iter("Item")]
    assert len(set(refs)) == n
    print(f"  ok  place file: well-formed, {n} instances, {len(shared)} shared / {len(server)} server / {len(client)} client scripts")


def check_autobuild():
    layout = json.loads(read("world", "world_layout.json"))
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(read("tests", "roblox_mock.lua"))
    loader = lua.eval('function(src, name) local fn, err = load(src, "=" .. name) if not fn then error(err) end return fn() end')
    g = lua.globals()
    g.Layout = loader(read("roblox", "WorldLayout.lua"), "WorldLayout")
    g.Heightmap = loader(read("roblox", "WorldHeightmap.lua"), "WorldHeightmap")
    g.Builder = loader(read("roblox", "VillageWorldBuilder.lua"), "VillageWorldBuilder")
    g.TerrainBuilder = loader(read("roblox", "VillageTerrainBuilder.lua"), "VillageTerrainBuilder")
    g.Auto = loader(read("roblox", "VillageAutoBuild.lua"), "VillageAutoBuild")
    lua.execute(HELPERS)

    # 1) no meshes: greybox blocks + voxel terrain
    rep = lua.eval("Auto.run({ layout = Layout, heightmap = Heightmap, builder = Builder, terrainBuilder = TerrainBuilder })")
    wanted = [i for i in layout["instances"] if layout["assets"][i["asset"]]["category"] in ("houses", "landmarks")
              or i["asset"] in ("bridge_stone", "fountain", "well", "gate_arch", "dock")]
    assert rep.mode == "greybox" and rep.placed == len(wanted), (rep.mode, rep.placed, len(wanted))
    assert rep.terrainCells == 192 * 192
    rows = lua.eval("""(function()
        local out = {}
        for _, p in ipairs(workspace.Village.greybox:GetChildren()) do
            local lo, hi = Builder._worldBounds({ p })
            out[#out + 1] = { p:GetAttribute("AssetId"), p.Name, lo.X, lo.Y, lo.Z, hi.X, hi.Y, hi.Z }
        end
        return out
    end)()""")
    by_asset = {}
    for i in wanted:
        by_asset.setdefault(i["asset"], []).append(i)
    worst = 0.0
    for row in rows.values():
        r = list(row.values())
        inst = by_asset[r[0]].pop(0) if len(by_asset[r[0]]) == 1 else None
        if inst is None:                      # several instances of one asset (gates): match by position
            cands = by_asset[r[0]]
            inst = min(cands, key=lambda c: abs(expected_bounds(c, layout["assets"][c["asset"]])[0] - r[2]))
            cands.remove(inst)
        exp = expected_bounds(inst, layout["assets"][inst["asset"]])
        err = max(abs(a - b) for a, b in zip(exp, r[2:8]))
        assert err < 0.01, (inst["id"], err)
        worst = max(worst, err)
        assert r[1] == inst.get("name", inst["asset"])
    print(f"  ok  greybox: {len(rows)} blocks match the planned bounding boxes (max error {worst:.4f} studs), "
          f"{rep.terrainCells} terrain cells")

    # 2) meshes without terrain chunks: real builder, mesh terrain skipped, voxel terrain used
    rep = lua.eval("""(function()
        local t = makeTemplates()
        for _, d in ipairs(t:GetDescendants()) do
            if string.sub(d.Name, 1, 9) == "terrain_r" then d:Destroy() end
        end
        return Auto.run({ layout = Layout, heightmap = Heightmap, builder = Builder, terrainBuilder = TerrainBuilder, templates = t })
    end)()""")
    n_rest = sum(1 for i in layout["instances"] if i["group"] not in ("terrain", "water"))
    assert rep.mode == "meshes" and not rep.meshTerrain and rep.placed == n_rest and rep.terrainCells == 192 * 192
    assert lua.eval("workspace.Village:FindFirstChild('greybox')") is None

    # 3) full import: everything placed as meshes, no voxel terrain
    rep = lua.eval("Auto.run({ layout = Layout, heightmap = Heightmap, builder = Builder, terrainBuilder = TerrainBuilder, templates = makeTemplates() })")
    assert rep.mode == "meshes" and rep.meshTerrain and rep.placed == len(layout["instances"]) and rep.terrainCells == 0
    print(f"  ok  with meshes: {n_rest} objects on voxel terrain, or all {len(layout['instances'])} with mesh terrain")


if __name__ == "__main__":
    try:
        check_place()
        check_autobuild()
    except AssertionError as exc:
        print("FAILED:", exc)
        sys.exit(1)
    print("PLACE FILE AND AUTO BUILD TESTS PASSED")
