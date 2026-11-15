-- Paste into the Roblox Studio command bar (View > Command Bar) after
--   1. importing the meshes into ServerStorage.VillageAssets and
--   2. placing the ModuleScripts into ServerStorage.VillageWorld
-- (see docs/ROBLOX_IMPORT.md).  Running it again rebuilds the village.

local ServerStorage = game:GetService("ServerStorage")
local scripts = ServerStorage:WaitForChild("VillageWorld")
local Builder = require(scripts.VillageWorldBuilder)
local layout = require(scripts.WorldLayout)

local found, missing = Builder.checkTemplates(ServerStorage.VillageAssets, layout)
print(string.format("templates found: %d, missing: %d", #found, #missing))
if #missing > 0 then
	warn("missing templates: " .. table.concat(missing, ", "))
end

local report = Builder.build({
	templates = ServerStorage.VillageAssets,
	layout = layout,
	origin = CFrame.new(0, 0, 0),      -- move / rotate the whole village here
	applyLighting = false,            -- true = also copy the suggested Lighting settings
	createSpawn = false,
})
print("village folder:", report.folder:GetFullName())
