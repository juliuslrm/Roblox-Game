-- Runs VillageAutoBuild once when the server starts (UNVERIFIED_IN_STUDIO).
-- Characters are held back until the ground exists, so nobody falls into the void.
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local folder = ServerStorage:WaitForChild("VillageWorld")

Players.CharacterAutoLoads = false
local ok, err = pcall(function()
	local Auto = require(folder:WaitForChild("VillageAutoBuild"))
	-- Fetch the uploaded model libraries; without them the village is built from placeholder blocks.
	local loadOk, loaded = pcall(function()
		return require(folder:WaitForChild("VillageAssetLoader")).load({
			ids = require(folder:WaitForChild("VillageAssetIds")),
			insertService = game:GetService("InsertService"),
			parent = ServerStorage,
		})
	end)
	if loadOk then
		print(string.format("[Village] assets: %d libraries loaded, %d failed, %d mesh parts, %d retextured",
			loaded.loaded, #loaded.failed, loaded.meshParts, loaded.retextured))
		for _, message in ipairs(loaded.failed) do warn("[Village] asset load failed: " .. message) end
	else
		warn("[Village] asset loader failed: " .. tostring(loaded))
	end
	local origin = workspace:GetAttribute("VillageOrigin")
	if typeof(origin) ~= "CFrame" then origin = CFrame.new() end
	local layout = require(folder:WaitForChild("WorldLayout"))
	local builder = require(folder:WaitForChild("VillageWorldBuilder"))
	-- Use the meshes only if their names match the level plan; otherwise say what arrived and
	-- fall back to placeholder blocks instead of building an empty world.
	local templates = ServerStorage:FindFirstChild("VillageAssets")
	if templates then
		local found, missing = builder.checkTemplates(templates, layout)
		print(string.format("[Village] templates: %d found, %d missing", #found, #missing))
		if #found == 0 then
			local names = {}
			for _, d in ipairs(templates:GetDescendants()) do
				if #names >= 20 then break end
				names[#names + 1] = d.ClassName .. ":" .. d.Name
			end
			warn("[Village] no template name matches the level plan. First instances: " .. table.concat(names, ", "))
			templates = nil
		end
	end
	local report = Auto.run({
		layout = layout,
		heightmap = require(folder:WaitForChild("WorldHeightmap")),
		builder = builder,
		terrainBuilder = require(folder:WaitForChild("VillageTerrainBuilder")),
		templates = templates,
		origin = origin,
	})
	print(string.format("[Village] built in mode '%s': %d objects placed, %d missing, %d terrain cells",
		report.mode, report.placed, report.missing, report.terrainCells))
	if report.mode == "greybox" then
		print("[Village] No meshes in ServerStorage.VillageAssets - showing placeholder blocks. See docs/ROBLOX_IMPORT.md.")
	end
end)
if not ok then warn("[Village] auto build failed: " .. tostring(err)) end
workspace:SetAttribute("VillageReady", true)
Players.CharacterAutoLoads = true
for _, player in ipairs(Players:GetPlayers()) do
	task.spawn(function() player:LoadCharacter() end)
end
Players.PlayerAdded:Connect(function(player)
	if not player.Character then player:LoadCharacter() end
end)
