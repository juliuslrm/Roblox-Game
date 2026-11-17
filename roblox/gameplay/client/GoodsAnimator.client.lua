-- ROBLOX CLIENT: draws the goods gliding over the conveyors.
-- The server publishes per conveyor part which item lies on it and since when (attributes Goods*,
-- see WorkshopWorld:syncGoods); GoodsMotion turns that into smooth positions; this script only
-- keeps one model per moving item and sets its CFrame every frame.  Nothing here is replicated.
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("ArcaneShared")
local Config = require(Shared.Config)
local GoodsMotion = require(Shared.GoodsMotion)
local ItemArt = require(Shared.ItemArt)
local Icons = require(Shared.ItemIcons)

local RANGE = 160                                   -- studs: conveyors further away are not animated
local motion = GoodsMotion.new(Config.cellSize)
local bodies = {}                                   -- conveyor part -> true
local models = {}                                   -- visual serial -> { item, part }
local holder = Instance.new("Folder")
holder.Name = "ArcaneGoods"
holder.Parent = workspace
local templates = ReplicatedStorage:WaitForChild("ArcaneItemModels", 20)

local function readStatic(body)
	local cell, surface = body:GetAttribute("GoodsCell"), body:GetAttribute("GoodsSurface")
	if typeof(cell) ~= "Vector3" or typeof(surface) ~= "Vector3" then return nil end
	local c = { room = body:GetAttribute("GoodsRoom"), floor = cell.Y, gx = cell.X, gz = cell.Z,
		x = surface.X, y = surface.Y, z = surface.Z, out = body:GetAttribute("GoodsOut") or -1,
		period = body:GetAttribute("GoodsPeriod") or 2, rise = body:GetAttribute("GoodsRise") }
	local nextCell, warp = body:GetAttribute("GoodsNext"), body:GetAttribute("GoodsWarp")
	if typeof(nextCell) == "Vector3" then c.next = { gx = nextCell.X, floor = nextCell.Y, gz = nextCell.Z } end
	if typeof(warp) == "Vector3" then c.warp = { x = warp.X, y = warp.Y, z = warp.Z, out = body:GetAttribute("GoodsWarpOut") or 0 } end
	return c
end
local function readState(body)
	motion:setState(body, body:GetAttribute("GoodsItem"), body:GetAttribute("GoodsAt"), body:GetAttribute("GoodsIn"),
		workspace:GetServerTimeNow())
end
local function add(body)
	if bodies[body] or not body:IsA("BasePart") or body:GetAttribute("GoodsOut") == nil then return end
	local c = readStatic(body)
	if not c then return end
	bodies[body] = true
	motion:setCarrier(body, c)
	readState(body)
	for _, name in ipairs({ "GoodsItem", "GoodsAt", "GoodsIn" }) do
		body:GetAttributeChangedSignal(name):Connect(function() readState(body) end)
	end
end
local function remove(body)
	if bodies[body] then
		bodies[body] = nil
		motion:removeCarrier(body)
	end
end
local function scan()
	local root = workspace:FindFirstChild("ArcaneWorkshops")
	if not root then return end
	for _, d in ipairs(root:GetDescendants()) do add(d) end
end
workspace.DescendantAdded:Connect(function(d)
	if d:IsA("BasePart") then task.defer(add, d) end
end)
workspace.DescendantRemoving:Connect(remove)
task.spawn(function()
	while true do
		scan()
		task.wait(3)
	end
end)

-- one model per moving item: the item's Blender model, or a coloured ball without the library
local function newModel(item)
	local name = "item_" .. item
	local template = templates and templates:FindFirstChild(name, true)
	local shape = ItemArt[name]
	local part, offset, base
	if template and shape and template:IsA("BasePart") then
		part = template:Clone()
		part.Size = Vector3.new(table.unpack(shape.size))
		-- keep the template's rotation: the asset loader stores the import correction there
		offset = CFrame.new(table.unpack(shape.center)) * (template.CFrame - template.CFrame.Position)
		base = part.Size
	else
		local icon = Icons.item(item)
		part = Instance.new("Part")
		part.Shape, part.Size = Enum.PartType.Ball, Vector3.new(0.9, 0.9, 0.9)
		part.Color = Color3.fromRGB(icon.color[1], icon.color[2], icon.color[3])
		offset, base = CFrame.new(0, 0.45, 0), part.Size
	end
	part.Name = name
	part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch, part.CastShadow = true, false, false, false, false
	part.Parent = holder
	return { item = item, part = part, offset = offset, base = base, scale = 1 }
end

-- every item gets its own fixed turn, so a row of equal goods does not look stamped
local function turnOf(item)
	local sum = 0
	for i = 1, #item do sum = (sum * 31 + string.byte(item, i)) % 360 end
	return math.rad(sum)
end

RunService.RenderStepped:Connect(function(dt)
	local camera = workspace.CurrentCamera
	if not camera then return end
	motion:step(workspace:GetServerTimeNow(), dt)
	local eye = camera.CFrame.Position
	local alive = {}
	for serial, v in pairs(motion.visuals) do
		local near = (Vector3.new(v.x, v.y, v.z) - eye).Magnitude <= RANGE
		if near then
			local m = models[serial]
			if m and m.item ~= v.item then m.part:Destroy() m = nil end
			if not m then
				m = newModel(v.item)
				models[serial] = m
			end
			local scale = math.max(v.scale, 0.02)
			if math.abs(m.scale - scale) > 0.005 then
				m.scale = scale
				m.part.Size = m.base * scale
			end
			m.part.Transparency = (v.scale < 0.05) and 1 or 0
			m.part.CFrame = CFrame.new(v.x, v.y, v.z) * CFrame.Angles(0, v.yaw + turnOf(v.item) + (v.spin or 0), 0)
				* CFrame.new(m.offset.Position * scale) * (m.offset - m.offset.Position)
			alive[serial] = true
		end
	end
	for serial, m in pairs(models) do
		if not alive[serial] then
			m.part:Destroy()
			models[serial] = nil
		end
	end
end)
