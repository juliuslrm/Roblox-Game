-- Runs VillageAutoBuild once when the server starts (UNVERIFIED_IN_STUDIO).
-- Characters are held back until the ground exists, so nobody falls into the void.
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local folder = ServerStorage:WaitForChild("VillageWorld")

Players.CharacterAutoLoads = false
local ok, err = pcall(function()
	local Auto = require(folder:WaitForChild("VillageAutoBuild"))
	local origin = workspace:GetAttribute("VillageOrigin")
	if typeof(origin) ~= "CFrame" then origin = CFrame.new() end
	local report = Auto.run({
		layout = require(folder:WaitForChild("WorldLayout")),
		heightmap = require(folder:WaitForChild("WorldHeightmap")),
		builder = require(folder:WaitForChild("VillageWorldBuilder")),
		terrainBuilder = require(folder:WaitForChild("VillageTerrainBuilder")),
		templates = ServerStorage:FindFirstChild("VillageAssets"),
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
