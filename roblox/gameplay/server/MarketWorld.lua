-- Places the five merchants at the planned stalls. Art is optional in the base place.
local Market = require(script.Parent.Data).Market
local Art = require(script.Parent.MarketArt)
local World = {}

local WOOD = Color3.fromRGB(133, 87, 58)
local DARK = Color3.fromRGB(83, 57, 42)

local function block(parent, name, frame, size, color, collides, transparency)
	local part = Instance.new("Part")
	part.Name, part.CFrame, part.Size = name, frame, size
	part.Anchored, part.CanCollide = true, collides
	part.CanQuery, part.CanTouch = collides, false
	part.TopSurface, part.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	part.Color, part.Transparency = color, transparency or 0
	part.CastShadow = transparency ~= 1
	part.Parent = parent
	return part
end

local function imported(parent, templates, name, pivot, role)
	local template = templates and templates:FindFirstChild(name, true)
	local shape = Art[name]
	if not template or not shape then return false end
	if not template:IsA("BasePart") then
		local parts = {}
		for _, child in ipairs(template:GetDescendants()) do
			if child:IsA("BasePart") then parts[#parts + 1] = child end
		end
		template = #parts == 1 and parts[1] or nil
	end
	if not template or not template.Archivable then return false end
	local mesh = template:Clone()
	mesh.Size = Vector3.new(table.unpack(shape.size))
	-- keep the template's rotation: the asset loader stores the import correction there
	mesh.CFrame = pivot * CFrame.new(table.unpack(shape.center)) * (template.CFrame - template.CFrame.Position)
	mesh.Anchored, mesh.CanCollide, mesh.CanQuery, mesh.CanTouch = true, false, false, false
	local rootBone = role and mesh:FindFirstChild("root", true)
	if rootBone and rootBone:IsA("Bone") then
		mesh:SetAttribute("MarketRigRole", role)
	end
	mesh.Parent = parent
	return true
end

local function fallbackStall(folder, pivot, accent)
	block(folder, "Counter", pivot * CFrame.new(0, 1.4, 0.45), Vector3.new(7.8, 2.8, 2.05), WOOD, false)
	block(folder, "CounterTop", pivot * CFrame.new(0, 2.86, 0.45), Vector3.new(8.2, 0.28, 2.25), DARK, false)
	for _, x in ipairs({-4.15, 4.15}) do
		block(folder, "Post", pivot * CFrame.new(x, 4.25, 0.4), Vector3.new(0.34, 8.5, 0.34), DARK, false)
	end
	for i = 0, 7 do
		block(folder, "Awning", pivot * CFrame.new((i - 3.5) * 1.11, 8.55, 0.25),
			Vector3.new(1.11, 0.18, 5.6), i % 2 == 0 and accent or Color3.fromRGB(234, 220, 190), false)
	end
end

local function ellipsoid(folder, name, frame, size, color)
	local part = block(folder, name, frame, Vector3.new(1, 1, 1), color, false)
	local mesh = Instance.new("SpecialMesh")
	mesh.MeshType, mesh.Scale = Enum.MeshType.Sphere, size
	mesh.Parent = part
end

local function fallbackMerchant(folder, pivot, accent)
	local skin = Color3.fromRGB(221, 169, 143)
	ellipsoid(folder, "Coat", pivot * CFrame.new(0, 3.62, 0), Vector3.new(1.13, 2.52, 0.70), accent)
	ellipsoid(folder, "Neck", pivot * CFrame.new(0, 4.94, 0), Vector3.new(0.28, 0.58, 0.29), skin)
	ellipsoid(folder, "Head", pivot * CFrame.new(0, 5.56, 0.04), Vector3.new(0.58, 0.85, 0.55), skin)
	ellipsoid(folder, "HatBrim", pivot * CFrame.new(0, 5.93, 0.01), Vector3.new(1.26, 0.11, 0.97), DARK)
	ellipsoid(folder, "HatCrown", pivot * CFrame.new(0.05, 6.08, 0.01), Vector3.new(0.65, 0.48, 0.57), accent)
	for _, side in ipairs({ -1, 1 }) do
		local arm = pivot * CFrame.new(side * 0.64, 3.92, 0.04) * CFrame.Angles(0, 0, side * 0.18)
		ellipsoid(folder, "Sleeve", arm, Vector3.new(0.35, 1.57, 0.39), accent)
		ellipsoid(folder, "Hand", pivot * CFrame.new(side * 0.75, 3.16, 0.11), Vector3.new(0.25, 0.39, 0.27), skin)
		ellipsoid(folder, "Leg", pivot * CFrame.new(side * 0.24, 1.57, 0), Vector3.new(0.44, 2.77, 0.43), DARK)
		ellipsoid(folder, "Boot", pivot * CFrame.new(side * 0.24, 0.24, 0.15), Vector3.new(0.43, 0.47, 0.68), DARK)
	end
end

function World.build(parent, anchors, origin, templates, groundPosition, onOpen)
	local root = Instance.new("Folder")
	root.Name = "ArcaneMarket"
	local village = parent:FindFirstChild("Village")
	local oldStalls = village and village:FindFirstChild("market")
	local oldByIndex = {}
	if oldStalls then
		for _, item in ipairs(oldStalls:GetChildren()) do
			local index = item:GetAttribute("LayoutIndex")
			if index then oldByIndex[index] = item end
		end
	end
	local replaced = {}
	for _, id in ipairs(Market.order) do
		local anchor = anchors[id]
		if anchor then
			local def = Market.merchants[id]
			local accent = Color3.fromHex(def.color)
			local folder = Instance.new("Folder")
			folder.Name, folder.Parent = id, root
			local approach = groundPosition({ x = anchor.approachX, y = anchor.y, z = anchor.approachZ })
			local position = origin * Vector3.new(anchor.x, anchor.y, anchor.z)
			local pivot = CFrame.new(position.X, approach.Y, position.Z)
				* (origin - origin.Position) * CFrame.Angles(0, math.rad(anchor.yaw), 0)
			if not imported(folder, templates, "stall_" .. id, pivot) then fallbackStall(folder, pivot, accent) end
			local npc = pivot * CFrame.new(0, 0, -1.6)
			if not imported(folder, templates, "merchant_" .. id, npc, id) then
				fallbackMerchant(folder, npc, accent)
			end
			block(folder, "CounterCollision", pivot * CFrame.new(0, 1.5, 0.45), Vector3.new(8.2, 3, 2.25), WOOD, true, 1)
			local promptAnchor = block(folder, "TradePrompt", CFrame.new(approach + Vector3.new(0, 2.5, 0)),
				Vector3.new(0.2, 0.2, 0.2), accent, false, 1)
			local prompt = Instance.new("ProximityPrompt")
			prompt.ActionText, prompt.ObjectText = "Handeln", def.name
			prompt.MaxActivationDistance, prompt.RequiresLineOfSight = Market.radius, false
			prompt.HoldDuration = 0.15
			prompt.Triggered:Connect(function(player) onOpen(player, id) end)
			prompt.Parent = promptAnchor
			if oldByIndex[anchor.index] then replaced[#replaced + 1] = oldByIndex[anchor.index] end
		end
	end
	local previous = parent:FindFirstChild(root.Name)
	if previous then previous:Destroy() end
	root.Parent = parent
	for _, item in ipairs(replaced) do item:Destroy() end
	return root
end

return World
