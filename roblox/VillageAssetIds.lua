-- Roblox asset ids of the uploaded model libraries (exports/library/*.fbx, uploaded through the
-- Open Cloud Assets API).  The ids only load in experiences of the account that owns the assets.
-- Set a value to nil to skip it; with no ids the village falls back to placeholder blocks.
return {
	-- target folder in ServerStorage -> list of Model asset ids
	-- Within one folder the first template of a name wins, so newer single models go first.
	folders = {
		VillageAssets = {
			72420451763699,  -- workshop_facade.glb
			121417351385239, -- village_assets.fbx
			136001329353977, -- village_terrain.fbx (with workshop plots, 2026-11-16)
		},
		ArcaneAssets = {
			137911422416588, -- mach_kettle.glb (replaces the kettle of the machine library)
			89059240299616,  -- arcane_machines.fbx
		},
		ArcaneMarketAssets = { 108160614549126 }, -- ArcaneMarket.glb: five merchants and stalls
	},
	-- Measured in the place (2026-11-16): Roblox imports the FBX and GLB files turned 180 degrees about
	-- the vertical axis compared with the level plan (plan x,z arrives as -x,-z).  The loader
	-- turns the templates back by this angle.
	importYaw = 180,
	paletteDecal = 124079534405265,                           -- exports/textures/village_palette.png
}
