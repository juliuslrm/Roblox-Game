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
    assert source(village["WorkshopFacade"]) == read("roblox", "WorkshopFacade.lua")
    for module in ("WorkshopArchitecture", "WorkshopModels", "MarketCatalog", "MarketIdle", "MarketMotion"):
        assert source(shared[module]) == read("roblox", "gameplay", "shared", module + ".lua")
    assert source(village["VillageAutoBuild"]) == read("roblox", "VillageAutoBuild.lua")
    assert source(children(services["ServerScriptService"])["VillageAutoBuild"]) == read(
        "roblox", "VillageAutoBuild.server.lua"
    )
    for module in ("Actions", "MarketArt", "MarketWorld"):
        assert source(server[module]) == read("roblox", "gameplay", "server", module + ".lua")
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
    g.WorkshopFacade = loader(read("roblox", "WorkshopFacade.lua"), "WorkshopFacade")
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

    # A partial import can contain the first tile, but must keep the complete voxel ground.
    rep = lua.eval("""(function()
        local t = makeTemplates("terrain_r1_c1", "house_01_timber_cottage")
        t:FindFirstChild("terrain_r1_c2", true):Destroy()
        local emptyTile = Instance.new("Model", t)
        emptyTile.Name = "terrain_r1_c2"
        assert(t:FindFirstChild("terrain_r0_c0", true))
        return Auto.run({ layout = Layout, heightmap = Heightmap, builder = Builder, terrainBuilder = TerrainBuilder, templates = t })
    end)()""")
    assert not rep.meshTerrain and rep.placed == n_rest and rep.terrainCells == 192 * 192
    assert list(rep.missingTerrain.values()) == ["terrain_r1_c1", "terrain_r1_c2"]
    assert lua.eval("workspace.Village:FindFirstChild('terrain')") is None
    assert lua.eval("workspace.Village:FindFirstChild('water')") is None
    assert any("house_01_timber_cottage: proportions differ" in message for message in rep.warnings.values())

    # 3) full import: everything placed as meshes, no voxel terrain
    rep = lua.eval("Auto.run({ layout = Layout, heightmap = Heightmap, builder = Builder, terrainBuilder = TerrainBuilder, templates = makeTemplates() })")
    assert rep.mode == "meshes" and rep.meshTerrain and rep.placed == len(layout["instances"]) and rep.terrainCells == 0
    print(f"  ok  with meshes: {n_rest} objects on voxel terrain for missing or partial ground, "
          f"or all {len(layout['instances'])} with complete ground")

    # An imported facade keeps the cottage's asset ID and transform but uses its own bounds.
    bounds = lua.eval("""(function()
        local t = makeTemplates("house_01_timber_cottage")
        local part = Instance.new("MeshPart", t)
        part.Name = "workshop_facade"
        part.Size = Vector3.new(table.unpack(WorkshopFacade.size)) * 2
        part.CFrame = CFrame.new(90, 35, 400)
        local built = Builder.build({ templates = t, layout = Layout, workshopFacade = WorkshopFacade,
            includeGroups = { buildings = true }, verbose = false })
        assert(built.missing.house_01_timber_cottage == nil)
        for _, row in ipairs(collect(built)) do
            if row[2] == "house_01_timber_cottage" then return row end
        end
    end)()""")
    facade = next(i for i in layout["instances"] if i["asset"] == "house_01_timber_cottage")
    center = list(g.WorkshopFacade.center.values())
    size = list(g.WorkshopFacade.size.values())
    x, y, z = (c - s / 2 for c, s in zip(center, size))
    w, h, d = size
    render_asset = {"bounds_blender": {"min": [x, -z - d, y], "max": [x + w, -z, y + h]}}
    actual = [bounds[i] for i in range(4, 10)]
    expected = expected_bounds(facade, render_asset)
    assert max(abs(a - b) for a, b in zip(expected, actual)) < 0.01, (actual, expected)
    print("  ok  optional workshop facade keeps the cottage placement and uses its own scale")

    # 4) asset loader: libraries become template folders, lost textures are replaced, failures reported
    g.Loader = loader(read("roblox", "VillageAssetLoader.lua"), "VillageAssetLoader")
    g.Ids = loader(read("roblox", "VillageAssetIds.lua"), "VillageAssetIds")
    res = lua.eval("""(function()
        local storage = Instance.new("Folder")
        local insert = {}
        function insert:LoadAsset(id)
            if id == 136001329353977 then error("HTTP 403") end
            local model = Instance.new("Model")
            if id == Ids.paletteDecal then
                local decal = Instance.new("Decal", model)
                decal.Texture = "rbxassetid://42"
                return model
            end
            local a = Instance.new("MeshPart", model); a.Name = "house_" .. id; a.TextureID = ""
            local b = Instance.new("MeshPart", model); b.Name = "kept_" .. id; b.TextureID = "rbxassetid://7"
            local c = Instance.new("MeshPart", model); c.Name = "dup"; c.TextureID = "rbxassetid://" .. id
            return model
        end
        local rep = Loader.load({ ids = Ids, insertService = insert, parent = storage })
        local again = Loader.load({ ids = Ids, insertService = insert, parent = storage })
        return { rep.loaded, #rep.failed, rep.meshParts, rep.retextured, again.loaded,
            storage.VillageAssets:FindFirstChild("house_121417351385239", true).TextureID,
            storage.VillageAssets:FindFirstChild("kept_121417351385239", true).TextureID,
            storage.ArcaneAssets:FindFirstChild("house_89059240299616", true):GetAttribute("PublishedMachineLibrary"),
            storage.ArcaneMarketAssets ~= nil,
            storage.VillageAssets:FindFirstChild("dup", true).TextureID }
    end)()""")
    # 6 ids, one fails; per folder only the first "dup" survives (3 folders), 2 unique parts per asset
    assert list(res.values()) == [5, 1, 13, 5, 0, "rbxassetid://42", "rbxassetid://7", True, True,
                                  "rbxassetid://72420451763699"], list(res.values())
    print("  ok  asset loader: 5 of 6 assets loaded, failure reported, missing textures replaced, "
          "first template of a name wins, no reload")


def check_market_world():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(read("tests", "roblox_mock.lua"))
    g = lua.globals()
    g.Layout = lua.execute(read("roblox", "WorldLayout.lua"))
    g.Market = lua.execute(read("roblox", "gameplay", "shared", "MarketCatalog.lua"))
    g.Art = lua.execute(read("roblox", "gameplay", "server", "MarketArt.lua"))
    g.Motion = lua.execute(read("roblox", "gameplay", "shared", "MarketMotion.lua"))
    g.Idle = lua.eval("""function(source)
        local env = setmetatable({
            script = { Parent = { MarketMotion = Motion } },
            require = function(value) return value end,
        }, { __index = _G })
        return assert(load(source, "@MarketIdle.lua", "t", env))()
    end""")(read("roblox", "gameplay", "shared", "MarketIdle.lua"))
    g.MarketWorld = lua.eval("""function(source)
        local env = setmetatable({
            script = { Parent = { Data = { Market = Market }, MarketArt = Art } },
            require = function(value) return value end,
        }, { __index = _G })
        return assert(load(source, "@MarketWorld.lua", "t", env))()
    end""")(read("roblox", "gameplay", "server", "MarketWorld.lua"))
    lua.execute("""
        Color3.fromHex = function(hex)
            return Color3.fromRGB(tonumber(hex:sub(1, 2), 16), tonumber(hex:sub(3, 4), 16), tonumber(hex:sub(5, 6), 16))
        end
        local new = Instance.new
        Instance.new = function(class, parent)
            local obj = new(class, parent)
            if class == "ProximityPrompt" then
                obj.Triggered = { Connect = function(_, fn) obj.OnTrigger = fn end }
            end
            return obj
        end

        local anchors = Market.anchors(Layout)
        local origin = CFrame.new(55, 4, -17) * CFrame.Angles(0, math.rad(32), 0)
        local village = Instance.new("Folder", workspace)
        village.Name = "Village"
        local stalls = Instance.new("Folder", village)
        stalls.Name = "market"
        for _, a in pairs(anchors) do
            local old = Instance.new("Model", stalls)
            old:SetAttribute("LayoutIndex", a.index)
        end
        local extra = Instance.new("Model", stalls)
        local function ground(a) return origin * Vector3.new(a.x, a.y + 0.34, a.z) end
        local called
        local function open(player, id) called = player .. id end
        local templates = Instance.new("Folder")
        local model = Instance.new("Model", templates)
        model.Name = "merchant_nyra"
        local mesh = Instance.new("MeshPart", model)
        mesh.Archivable = true
        local stand = Instance.new("MeshPart", templates)
        stand.Name = "stall_nyra"
        stand.Archivable = true
        local esme = Instance.new("MeshPart", templates)
        esme.Name, esme.Archivable = "merchant_esme", true
        local bone = Instance.new("Bone", esme)
        bone.Name, bone.Archivable = "root", true
        local market = MarketWorld.build(workspace, anchors, origin, templates, ground, open)
        assert(#market:GetChildren() == 5 and #stalls:GetChildren() == 1 and extra.Parent == stalls)
        assert(market.selma:FindFirstChild("Coat") and not market.nyra:FindFirstChild("Coat"))
        assert(market.selma.Head.SpecialMesh.MeshType == Enum.MeshType.Sphere)
        assert(market.selma.Head.SpecialMesh.Scale.Y < 1 and market.selma.Head.CFrame.Y > 5)
        local actor = market.nyra:FindFirstChild("MeshPart")
        assert(actor and actor.Size.Y == Art.merchant_nyra.size[2] and actor.CanCollide == false)
        local pivot = origin * CFrame.new(anchors.nyra.x, anchors.nyra.y + 0.34, anchors.nyra.z)
            * CFrame.Angles(0, math.rad(anchors.nyra.yaw), 0) * CFrame.new(0, 0, -1.6)
        assert((actor.CFrame.Position - (pivot * Vector3.new(table.unpack(Art.merchant_nyra.center)))).Magnitude < 0.001)
        assert(market.nyra.CounterCollision.CanCollide)
        market.nyra.TradePrompt.ProximityPrompt.OnTrigger("Player-")
        local rig = market.esme:FindFirstChild("merchant_esme")
        assert(rig and rig.root:IsA("Bone") and rig:GetAttribute("MarketRigRole") == "esme")
        assert(not actor:GetAttribute("MarketRigRole"))
        local count = 0
        for _, tracks in pairs(Motion.bones) do
            count = count + 1
            local moved = 0
            for _, track in pairs(tracks) do
                assert(#track == 49)
                local x, y, z, w = Idle.sample(track, 2.3)
                assert(math.abs(x*x + y*y + z*z + w*w - 1) < 1e-6)
                moved = moved + x*x + y*y + z*z
                for _, t in ipairs({0, Motion.duration}) do
                    local qx, qy, qz, qw = Idle.sample(track, t)
                    assert(qx*qx + qy*qy + qz*qz < 1e-6 and math.abs(qw - 1) < 1e-6)
                end
            end
            assert(moved > 0.0001)
        end
        assert(count == 5)
        assert(called == "Player-nyra")
    """)
    print("  ok  market: five shops, scaled imported NPC, fallback, prompt and targeted stall replacement")


def check_workshop_plots():
    """Level, empty plots in the plan and the open workshop geometry that stands on them."""
    layout = json.loads(read("world", "world_layout.json"))
    hm = json.loads(read("world", "heightmap.json"))
    plots, half = layout["workshop_plots"]["plots"], layout["workshop_plots"]["half"]
    assert len(plots) == 4 and half >= 42          # Config.maxPlayers, largest tier 80 studs + yard
    cell, org = hm["cell"], hm["origin_blender"]
    worst = 0.0
    for a in plots:
        x, y, z = a["blender"]
        hs = [hm["heights"][round((y + dy - org[1]) / cell)][round((x + dx - org[0]) / cell)]
              for dx in range(-40, 41, 4) for dy in range(-40, 41, 4)]
        worst = max(worst, max(hs) - min(hs))
        assert max(hs) - min(hs) < 1.0, (a, min(hs), max(hs))
        assert abs(z - sum(hs) / len(hs)) < 0.6
        for inst in layout["instances"]:
            if inst["group"] in ("terrain", "water", "roads"):
                continue
            ix, iy, _ = inst["blender"]["location"]
            assert not (abs(ix - x) < half and abs(iy - y) < half), (inst["id"], a)
        for b in plots:
            assert a is b or max(abs(a["blender"][0] - b["blender"][0]), abs(a["blender"][1] - b["blender"][1])) >= 2 * half + 20
    lua_layout = read("roblox", "WorldLayout.lua")
    for a in plots:
        r = a["roblox"]
        assert "{%g, %g, %g}" % tuple(r) in lua_layout, r

    lua = LuaRuntime(unpack_returned_tuples=True)
    arch = lua.execute(read("roblox", "gameplay", "shared", "WorkshopArchitecture.lua"))
    for size in (32, 48, 64, 80):
        for floors in (1, 2, 3):
            parts = list(arch.build(size, floors, 12, True)[0].values())
            names = {q.name for q in parts}
            assert "ExitDoor" not in names and "AmberWindow" not in names
            h = size / 2
            for q in parts:
                if not q.collides or q.position[2] > 3:
                    continue
                px, pz, sx, sz = q.position[1], q.position[3], q.size[1], q.size[3]
                if q.name.endswith("Wall"):
                    # ground floor walls are low and leave the middle 12 studs of every side open
                    assert q.size[2] <= 2.4
                    on_x_side = abs(abs(px) - h - 0.5) < 0.01 and sx == 1
                    lo, hi = (pz - sz / 2, pz + sz / 2) if on_x_side else (px - sx / 2, px + sx / 2)
                    assert hi <= -6 + 1e-6 or lo >= 6 - 1e-6, (size, q.name, lo, hi)
    print(f"  ok  workshop plots: 4 level plots (ground varies {worst:.2f} studs), empty, apart; "
          "open workshop has low walls with an opening on every side for all 12 sizes")


if __name__ == "__main__":
    try:
        check_place()
        check_autobuild()
        check_workshop_plots()
        check_market_world()
    except AssertionError as exc:
        print("FAILED:", exc)
        sys.exit(1)
    print("PLACE FILE AND AUTO BUILD TESTS PASSED")
