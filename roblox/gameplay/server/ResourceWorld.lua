-- ROBLOX ADAPTER: puts a model of the resource at every resource node and lets players harvest it
-- by interacting with that model.  Game rules stay in ResourceService; this module only mirrors
-- the node state (available / used up) into the world.
local D = require(script.Parent.Data)
local Art = require(script.Parent.ResourceArt)
local Locations, Items = D.Locations, D.Items
local World = {}
World.__index = World

local EMPTY_TRANSPARENCY = 0.7

-- Stand-in when the model library is missing (plain test place): a small crate, so there is still
-- an object to interact with.
local function fallback(folder, pivot)
	local part = Instance.new("Part")
	part.Name = "Resource"
	part.Size = Vector3.new(2.4, 1.8, 2.4)
	part.CFrame = pivot * CFrame.new(0, 0.9, 0)
	part.Color, part.Material = Color3.fromRGB(134, 87, 58), Enum.Material.Wood
	part.TopSurface, part.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	part.Parent = folder
	return part
end

local function imported(folder, templates, name, pivot)
	local template = templates and templates:FindFirstChild(name, true)
	local shape = Art[name]
	if not template or not shape or not template:IsA("BasePart") then return nil end
	local mesh = template:Clone()
	mesh.Name = "Resource"
	mesh.Size = Vector3.new(table.unpack(shape.size))
	-- keep the template's rotation: the asset loader stores the import correction there
	mesh.CFrame = pivot * CFrame.new(table.unpack(shape.center)) * (template.CFrame - template.CFrame.Position)
	mesh.Parent = folder
	return mesh
end

-- Fixed, node-specific turn so equal models do not all face the same way.
local function yawOf(id)
	local sum = 0
	for i = 1, #id do sum = (sum * 31 + string.byte(id, i)) % 360 end
	return sum
end

-- nodeAnchors: id -> { x, y, z } in village-local coordinates; groundPosition(anchor) -> world Vector3
-- onGather(player, nodeId) is called when a player uses the prompt of a node.
function World.build(parent, nodeAnchors, origin, templates, groundPosition, onGather)
	local self = setmetatable({ entries = {} }, World)
	local root = Instance.new("Folder")
	root.Name = "ArcaneResources"
	for id, anchor in pairs(nodeAnchors) do
		local node = Locations.nodes[id]
		local folder = Instance.new("Folder")
		folder.Name, folder.Parent = id, root
		local pivot = CFrame.new(groundPosition(anchor)) * (origin - origin.Position) * CFrame.Angles(0, math.rad(yawOf(id)), 0)
		local body = imported(folder, templates, "res_" .. node.item, pivot) or fallback(folder, pivot)
		body.Anchored, body.CanCollide, body.CanTouch = true, false, false
		body:SetAttribute("ArcaneNode", id)
		local prompt = Instance.new("ProximityPrompt")
		prompt.ActionText, prompt.ObjectText = "Sammeln", Items[node.item].name
		prompt.MaxActivationDistance, prompt.RequiresLineOfSight, prompt.HoldDuration = 10, false, 0.15
		prompt.Triggered:Connect(function(player) onGather(player, id) end)
		prompt.Parent = body
		-- small name tag, readable from a few steps away
		local tag = Instance.new("BillboardGui")
		tag.Name, tag.Size, tag.MaxDistance = "Name", UDim2.new(0, 130, 0, 26), 45
		tag.StudsOffsetWorldSpace = Vector3.new(0, body.Size.Y / 2 + 1.4, 0)
		local text = Instance.new("TextLabel")
		text.Size, text.BackgroundTransparency, text.TextScaled = UDim2.new(1, 0, 1, 0), 1, true
		text.Font, text.TextColor3, text.TextStrokeTransparency = Enum.Font.GothamBold, Color3.fromRGB(247, 244, 236), 0.4
		text.Text = Items[node.item].name
		text.Parent = tag
		tag.Parent = body
		self.entries[id] = { body = body, prompt = prompt, empty = false }
	end
	local previous = parent:FindFirstChild(root.Name)
	if previous then previous:Destroy() end
	root.Parent = parent
	self.root = root
	return self
end

-- nodes: world.nodes (id -> { remaining }).  A used-up resource fades and cannot be harvested until
-- it has grown back.
function World:update(nodes)
	for id, entry in pairs(self.entries) do
		local state = nodes[id]
		local empty = state ~= nil and state.remaining <= 0
		if empty ~= entry.empty then
			entry.empty = empty
			entry.body.Transparency = empty and EMPTY_TRANSPARENCY or 0
			entry.prompt.Enabled = not empty
		end
	end
end

return World
