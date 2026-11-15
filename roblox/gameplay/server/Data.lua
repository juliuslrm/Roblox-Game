-- Loads the shared data tables once for all server modules.
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("ArcaneShared")
return {
	Config = require(Shared.Config), Items = require(Shared.Items), Recipes = require(Shared.Recipes),
	Machines = require(Shared.Machines), Research = require(Shared.Research), Quests = require(Shared.Quests),
	Locations = require(Shared.Locations), Protocol = require(Shared.Protocol), GridMath = require(Shared.GridMath),
	Util = require(Shared.Util), Validator = require(Shared.Validator),
}
