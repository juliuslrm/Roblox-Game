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
    for module in ("WorkshopArchitecture", "WorkshopModels", "MarketCatalog", "MarketMotion"):
        assert source(shared[module]) == read("roblox", "gameplay", "shared", module + ".lua")
    assert source(village["VillageAutoBuild"]) == read("roblox", "VillageAutoBuild.lua")
    assert source(children(services["ServerScriptService"])["VillageAutoBuild"]) == read(
        "roblox", "VillageAutoBuild.server.lua"
    )
    for module in ("Actions", "MarketArt", "MarketWorld", "TraderArt"):
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
            storage.ArcaneAssets:FindFirstChild("house_100548175724336", true):GetAttribute("PublishedMachineLibrary"),
            storage.ArcaneMarketAssets ~= nil,
            storage.VillageAssets:FindFirstChild("dup", true).TextureID }
    end)()""")
    # every id loads except one; per folder only the first "dup" survives, 2 unique parts per asset
    n = int(lua.eval("(function() local n = 0 for _, ids in pairs(Ids.folders) do n = n + #ids end return n end)()"))
    folders = int(lua.eval("(function() local n = 0 for _ in pairs(Ids.folders) do n = n + 1 end return n end)()"))
    assert list(res.values()) == [n - 1, 1, 2 * (n - 1) + folders, n - 1, 0, "rbxassetid://42", "rbxassetid://7", True, True,
                                  "rbxassetid://72420451763699"], list(res.values())
    print(f"  ok  asset loader: {n - 1} of {n} assets loaded, failure reported, missing textures replaced, "
          "first template of a name wins, no reload")


def check_market_world():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(read("tests", "roblox_mock.lua"))
    g = lua.globals()
    g.Layout = lua.execute(read("roblox", "WorldLayout.lua"))
    g.Market = lua.execute(read("roblox", "gameplay", "shared", "MarketCatalog.lua"))
    g.Art = lua.execute(read("roblox", "gameplay", "server", "MarketArt.lua"))
    g.Motion = lua.execute(read("roblox", "gameplay", "shared", "MarketMotion.lua"))
    g.Traders = lua.execute(read("roblox", "gameplay", "server", "TraderArt.lua"))
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
        local placed = CFrame.new(9, 0, 0) * CFrame.Angles(0, math.rad(180), 0)   -- as left by the asset loader
        local stall = Instance.new("MeshPart", templates)
        stall.Name, stall.Archivable, stall.Size, stall.CFrame = "stall_nyra", true, Vector3.new(1, 1, 1), placed
        -- a skinned rig as the importer builds it: Model with RootPart (bones) and skinned MeshParts
        local function rig(role, withRoot)
            local model = Instance.new("Model", templates)
            model.Name = "Trader_" .. role
            for _, n in ipairs({ "head", "wear1", "hair1", "prop_L" }) do
                local mesh = Instance.new("MeshPart", model)
                mesh.Name, mesh.Size = "trader_" .. role .. "_" .. n, Vector3.new(1, 2, 1)
                mesh.CFrame = placed * CFrame.new(0, 3, 0)
            end
            if withRoot then
                local root = Instance.new("Part", model)
                root.Name, root.CFrame = "RootPart", placed
                local bone = Instance.new("Bone", root)
                bone.Name = "head"
            end
            local poses = Instance.new("Folder", model)
            poses.Name = "InitialPoses"
            return model
        end
        rig("nyra", true)
        rig("esme", false)                                             -- broken rig without RootPart
        local market = MarketWorld.build(workspace, anchors, origin, templates, ground, open)
        assert(#market:GetChildren() == 5 and #stalls:GetChildren() == 1 and extra.Parent == stalls)
        -- no templates: simple stand-in figure
        assert(market.selma:FindFirstChild("Coat") and not market.nyra:FindFirstChild("Coat"))
        assert(market.selma.Head.SpecialMesh.MeshType == Enum.MeshType.Sphere)
        -- broken rig: stand-in figure, no half figure left behind
        assert(market.esme:FindFirstChild("Coat") and not market.esme:FindFirstChild("Figure"))
        -- complete rig: cloned, moved to the stall, anchored, loader poses dropped
        local figure = market.nyra.Figure
        local pivot = origin * CFrame.new(anchors.nyra.x, anchors.nyra.y + 0.34, anchors.nyra.z)
            * CFrame.Angles(0, math.rad(anchors.nyra.yaw), 0) * CFrame.new(0, 0, -1.6)
        assert(figure:IsA("Model") and figure:GetAttribute("MerchantRole") == "nyra")
        assert((figure:GetAttribute("MerchantPivot").Position - pivot.Position).Magnitude < 0.001)
        assert(not figure:FindFirstChild("InitialPoses") and figure.RootPart:FindFirstChild("head"))
        local count = 0
        for _, d in ipairs(figure:GetDescendants()) do
            if d:IsA("BasePart") then
                count = count + 1
                assert(d.Anchored and d.CanCollide == false)
                local want = d.Name == "RootPart" and (pivot * placed) or (pivot * placed * CFrame.new(0, 3, 0))
                assert((d.CFrame.Position - want.Position).Magnitude < 0.001, d.Name)
            end
        end
        assert(count == 5)
        assert(templates:FindFirstChild("trader_nyra_head", true), "template stays in storage")
        assert(market.nyra.CounterCollision.CanCollide)
        market.nyra.TradePrompt.ProximityPrompt.OnTrigger("Player-")
        assert(called == "Player-nyra")

        -- idle loops: every animated bone, unit rotations, closed, something moves; reference poses exist
        local roles = 0
        for role, data in pairs(Motion.roles) do
            roles = roles + 1
            local samples = math.floor(data.duration * Motion.fps + 0.5)
            local bones = 0
            for _, name in ipairs(Traders.animated) do assert(data.bones[name], role .. " " .. name) end
            for bone, rows in pairs(data.bones) do
                bones = bones + 1
                assert(#rows == samples, role .. " " .. bone)
                local travel = 0
                for i, r in ipairs(rows) do
                    assert(math.abs(r[1]^2 + r[2]^2 + r[3]^2 + r[4]^2 - 1) < 1e-3)
                    local nxt = rows[i % #rows + 1]
                    local dot = math.abs(r[1]*nxt[1] + r[2]*nxt[2] + r[3]*nxt[3] + r[4]*nxt[4])
                    assert(dot > 0.97, role .. " " .. bone .. " jumps")
                    travel = travel + math.abs(r[1]-nxt[1]) + math.abs(r[2]-nxt[2]) + math.abs(r[3]-nxt[3])
                end
                assert(travel > 1e-3, role .. " " .. bone .. " never moves")
            end
            assert(bones >= 8)
            local art = Traders.traders[role]
            assert(art and #art.check >= 3 and art.height > 5.5 and art.height < 8)
            for _, c in ipairs(art.check) do assert(c.sample >= 1 and c.sample <= samples and #c.wristL == 3) end
        end
        assert(roles == 5)
    """)
    print("  ok  market: five shops, skinned trader rigs placed and anchored, stand-in for missing or broken rigs,\n"
          "      prompt, closed bone loops for 5 traders with reference poses")


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


def check_resource_world():
    """Every resource node gets the model of its item, a prompt on that model and an empty state."""
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(read("tests", "roblox_mock.lua"))
    g = lua.globals()
    g.Locations = lua.execute(read("roblox", "gameplay", "shared", "Locations.lua"))
    g.Items = lua.execute(read("roblox", "gameplay", "shared", "Items.lua"))
    g.Art = lua.execute(read("roblox", "gameplay", "server", "ResourceArt.lua"))
    g.ResourceWorld = lua.eval("""function(source)
        local env = setmetatable({
            script = { Parent = { Data = { Locations = Locations, Items = Items }, ResourceArt = Art } },
            require = function(value) return value end,
        }, { __index = _G })
        return assert(load(source, "@ResourceWorld.lua", "t", env))()
    end""")(read("roblox", "gameplay", "server", "ResourceWorld.lua"))
    manifest = json.loads(read("world", "resource_asset_manifest.json"))["assets"]
    items = {n.item for n in g.Locations.nodes.values()}
    assert {"res_" + i for i in items} == set(manifest) == set(g.Art.keys()), "one model per node item"
    res = lua.eval("""(function()
        UDim2 = UDim2 or { new = function(...) return { ... } end }
        local new = Instance.new
        Instance.new = function(class, parent)
            local obj = new(class, parent)
            if class == "ProximityPrompt" then
                obj.Enabled = true
                obj.Triggered = { Connect = function(_, fn) obj.OnTrigger = fn end }
            end
            return obj
        end
        local templates = Instance.new("Folder")
        for name, shape in pairs(Art) do
            if name ~= "res_sand" then                       -- one model missing: fallback object
                local mesh = Instance.new("MeshPart", templates)
                mesh.Name = name
                mesh.Size = Vector3.new(1, 1, 1)
                mesh.CFrame = CFrame.new(40, 0, 0) * CFrame.Angles(0, math.rad(180), 0)   -- as left by the asset loader
            end
        end
        local anchors, count = {}, 0
        for id in pairs(Locations.nodes) do
            count = count + 1
            anchors[id] = { x = count * 10, y = 2, z = -count * 7 }
        end
        local origin = CFrame.new(5, 1, -3)
        local gathered
        local world = ResourceWorld.build(workspace, anchors, origin, templates,
            function(a) return origin * Vector3.new(a.x, a.y, a.z) end, function(player, id) gathered = player .. ":" .. id end)
        local folder = workspace.ArcaneResources
        local meshes, fallbacks, prompts, floating = 0, 0, 0, 0
        for id, node in pairs(Locations.nodes) do
            local body = folder[id].Resource
            if body.ClassName == "MeshPart" then meshes = meshes + 1 else fallbacks = fallbacks + 1 end
            local prompt = body:FindFirstChild("ProximityPrompt")
            if prompt and prompt.ObjectText == Items[node.item].name and prompt.ActionText == "Sammeln" then prompts = prompts + 1 end
            local shape = Art["res_" .. node.item]
            local ground = origin * Vector3.new(anchors[id].x, anchors[id].y, anchors[id].z)
            if body.ClassName == "MeshPart" then
                -- the model's lowest point sits at the ground point (centre.y - size.y / 2 is its design base)
                local base = body.CFrame.Position.Y - body.Size.Y / 2 - ground.Y
                if math.abs(base - (shape.center[2] - shape.size[2] / 2)) > 0.01 then floating = floating + 1 end
                if math.abs(body.Size.X - shape.size[1]) > 0.01 then floating = floating + 1 end
            end
        end
        local mint = folder.n_mint_plaza.Resource
        mint.ProximityPrompt.OnTrigger("p1")
        local nodes = {}
        for id, node in pairs(Locations.nodes) do nodes[id] = { remaining = node.capacity } end
        nodes.n_mint_plaza.remaining = 0
        world:update(nodes)
        local emptyT, emptyE = mint.Transparency, mint.ProximityPrompt.Enabled
        nodes.n_mint_plaza.remaining = 2
        world:update(nodes)
        return { count, meshes, fallbacks, prompts, floating, gathered, emptyT, emptyE, mint.Transparency, mint.ProximityPrompt.Enabled,
            mint.CanCollide }
    end)()""")
    r = list(res.values())
    n = len(list(g.Locations.nodes.keys()))
    sand_nodes = sum(1 for node in g.Locations.nodes.values() if node.item == "sand")
    assert r[0] == n and r[1] == n - sand_nodes and r[2] == sand_nodes and r[3] == n and r[4] == 0, r
    assert r[5] == "p1:n_mint_plaza" and abs(r[6] - 0.7) < 1e-6 and r[7] is False and r[8] == 0 and r[9] is True and r[10] is False, r
    print(f"  ok  resources: {n} nodes get the model of their item ({len(manifest)} models), prompt on the model, "
          "fallback object, used-up state")


def check_item_art():
    """Every item has a model (bounds) and a cell on the icon sheet; nothing is left over."""
    lua = LuaRuntime(unpack_returned_tuples=True)
    items = set(lua.execute(read("roblox", "gameplay", "shared", "Items.lua")).keys())
    art = lua.execute(read("roblox", "gameplay", "shared", "ItemArt.lua"))
    sheet = lua.execute(read("roblox", "gameplay", "shared", "ItemIconSheet.lua"))
    manifest = json.loads(read("world", "item_asset_manifest.json"))["assets"]
    assert {"item_" + i for i in items} == set(art.keys()) == set(manifest), "one model per item"
    assert set(sheet["items"].keys()) == items, "one icon per item"
    cells = set()
    for item in items:
        col, row = sheet["items"][item][1], sheet["items"][item][2]
        assert 0 <= col < sheet.columns and 0 <= row < sheet.rows and (col, row) not in cells
        cells.add((col, row))
        size = [art["item_" + item].size[k] for k in (1, 2, 3)]
        assert max(size[0], size[2]) <= 1.6 and size[1] <= 1.9, (item, size)      # fits on a 2 stud belt
    png = os.path.join(ROOT, "exports", "textures", "item_icons.png")
    with open(png, "rb") as fh:
        head = fh.read(24)
    width, height = int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    assert (width, height) == (sheet.columns * sheet.cell, sheet.rows * sheet.cell), (width, height)
    print(f"  ok  items: {len(items)} models with bounds, {len(items)} icons on a {width} x {height} sheet")


if __name__ == "__main__":
    try:
        check_place()
        check_autobuild()
        check_workshop_plots()
        check_resource_world()
        check_item_art()
        check_market_world()
    except AssertionError as exc:
        print("FAILED:", exc)
        sys.exit(1)
    print("PLACE FILE AND AUTO BUILD TESTS PASSED")
