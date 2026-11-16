-- Market NPCs run the five existing stalls. Prices and bundle sizes are server-owned.
local Market = { order = { "selma", "nyra", "lio", "aron", "esme" }, radius = 12 }
Market.merchants = {
	selma = {
		name = "Selma Wurzelbund", trade = "Kräuter und Saat", color = "4F8A55",
		line = "Frische Kräuter für den Kessel. Die Saat ist fürs eigene Beet.",
		stall = "market_stall_fruit", occurrence = 1,
		offers = {
			{ item = "herb_mint", amount = 2, coins = 26 },
			{ item = "herb_sunleaf", amount = 2, coins = 32 },
			{ item = "berry_red", amount = 2, coins = 48, unlock = { research = "craftsman" } },
			{ item = "seed_mint", amount = 1, coins = 24, unlock = { research = "farming" } },
			{ item = "seed_sunleaf", amount = 1, coins = 29, unlock = { research = "farming" } },
		},
	},
	nyra = {
		name = "Nyra Dämmerhut", trade = "Nachtflora und Rohkristalle", color = "6F4E7C",
		line = "Dämmerpilze vertragen keinen Mittag. Bei den Kristallen ist das anders.",
		stall = "market_stall_cloth", occurrence = 1,
		offers = {
			{ item = "mushroom_gloom", amount = 1, coins = 32 },
			{ item = "crystal_raw", amount = 1, coins = 58, unlock = { research = "rune_study" } },
			{ item = "herb_moonleaf", amount = 2, coins = 44, unlock = { research = "moonbotany" } },
		},
	},
	lio = {
		name = "Lio Glasfunke", trade = "Glassand und Phiolen", color = "3D6FA5",
		line = "Sand für den Ofen. Phiolen, wenn die Abfüllung schon wartet.",
		stall = "market_stall_cloth", occurrence = 2,
		offers = {
			{ item = "sand", amount = 4, coins = 20, unlock = { research = "craftsman" } },
			{ item = "vial", amount = 4, coins = 32, unlock = { research = "glassworks" } },
		},
	},
	aron = {
		name = "Aron Glutbart", trade = "Erz und Brennstoff", color = "B5482F",
		line = "Kohle für die Glut. Kupfer und Eisen kommen vom Wachturm.",
		stall = "market_stall_bread", occurrence = 1,
		offers = {
			{ item = "fuel_charcoal", amount = 4, coins = 24, unlock = { research = "craftsman" } },
			{ item = "ore_copper", amount = 2, coins = 34, unlock = { quest = "q11" } },
			{ item = "ore_iron", amount = 2, coins = 42, unlock = { quest = "q11" } },
		},
	},
	esme = {
		name = "Esme Eichenmaß", trade = "Holz und Stein", color = "3F7F7A",
		line = "Gerades Holz für die Säge, sauberer Stein fürs Stampfwerk.",
		stall = "market_stall_fruit", occurrence = 2,
		offers = {
			{ item = "wood_log", amount = 2, coins = 18, unlock = { research = "craftsman" } },
			{ item = "stone", amount = 4, coins = 20, unlock = { research = "craftsman" } },
		},
	},
}

function Market.anchors(layout)
	local anchors, counts, byStall = {}, {}, {}
	if not layout then return anchors end
	for _, id in ipairs(Market.order) do
		local def = Market.merchants[id]
		byStall[def.stall .. "#" .. def.occurrence] = id
	end
	for index, row in ipairs(layout.instances) do
		if layout.groupNames[row[7]] == "market" then
			local name = layout.assetNames[row[1]]
			counts[name] = (counts[name] or 0) + 1
			local id = byStall[name .. "#" .. counts[name]]
			if id then
				local yaw = math.rad(row[5])
				local fx, fz = math.sin(yaw), math.cos(yaw)
				anchors[id] = { x = row[2], y = row[3], z = row[4], yaw = row[5], index = index,
					approachX = row[2] + fx * 4.4, approachZ = row[4] + fz * 4.4 }
			end
		end
	end
	return anchors
end

function Market.near(anchor, playerPosition)
	if not anchor or not playerPosition then return false end
	local dx, dz = anchor.approachX - playerPosition.x, anchor.approachZ - playerPosition.z
	return dx * dx + dz * dz <= Market.radius * Market.radius
end

return Market
