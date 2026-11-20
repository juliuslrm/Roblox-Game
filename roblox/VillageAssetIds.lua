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
			100548175724336, -- arcane_machines.fbx (new conveyors, 2026-11-17)
		},
		ArcaneMarketAssets = {
			112405603844665, -- trader_selma.fbx: skinned rig, face rig, fingers, PBR maps (2026-11-19)
			108051845917119, -- trader_nyra.fbx
			131339803075041, -- trader_lio.fbx: Reom base (CC-BY), Rigify rig with fingers, cloth-simulated outfit (2026-11-20)
			97062981895864, -- trader_aron.fbx
			84388846974618, -- trader_esme.fbx
			122869519424675, -- arcane_market.fbx: the five stalls
		},
		ArcaneResourceAssets = { 119763588026096 }, -- arcane_resources.fbx: one model per raw item
		ArcaneItemAssets = { 104749246484046 }, -- arcane_items.fbx: one small model per item (goods on the belts)
	},
	-- Measured in the place (2026-11-16): Roblox imports the FBX and GLB files turned 180 degrees about
	-- the vertical axis compared with the level plan (plan x,z arrives as -x,-z).  The loader
	-- turns the templates back by this angle.
	importYaw = 180,
	paletteDecal = 124079534405265,                           -- exports/textures/village_palette.png
}
