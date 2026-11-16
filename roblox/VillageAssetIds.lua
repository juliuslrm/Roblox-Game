-- Roblox asset ids of the uploaded model libraries (exports/library/*.fbx, uploaded through the
-- Open Cloud Assets API).  The ids only load in experiences of the account that owns the assets.
-- Set a value to nil to skip it; with no ids the village falls back to placeholder blocks.
return {
	-- target folder in ServerStorage -> list of Model asset ids
	folders = {
		VillageAssets = { 121417351385239, 115718062572873 }, -- village_assets.fbx, village_terrain.fbx
		ArcaneAssets = { 89059240299616 },                    -- arcane_machines.fbx
	},
	-- Measured in the place (2026-11-16): Roblox imports the FBX libraries turned 180 degrees about
	-- the vertical axis compared with the level plan (plan x,z arrives as -x,-z).  The loader
	-- turns the templates back by this angle.
	importYaw = 180,
	paletteDecal = 124079534405265,                           -- exports/textures/village_palette.png
}
