-- ROBLOX CLIENT: plays the idle loops of the market traders.
-- A trader is a folder "Figure" of seven anchored MeshParts that the server placed in the rest
-- pose.  MarketMotion holds, per part, the joint frame for every sample of the loop; a part moves
-- with  pivot * frame(t) * CFrame.new(-joint) * restLocal.  Only this client sees the motion, the
-- server never moves the parts, so nothing has to be replicated.
local RunService = game:GetService("RunService")
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("ArcaneShared")
local Motion = require(Shared.MarketMotion)

local RANGE = 130                      -- studs: figures further away stand still
local PHASE = { selma = 0, nyra = 1.7, lio = 3.1, aron = 4.6, esme = 2.4 }   -- so they do not move in step

-- joint frames as CFrames, already combined with the joint offset
local tracks = {}
for role, data in pairs(Motion.roles) do
	tracks[role] = { duration = data.duration, parts = {} }
	for part, rows in pairs(data.parts) do
		local joint = data.joints[part]
		local back = CFrame.new(-joint[1], -joint[2], -joint[3])
		local frames = table.create(#rows)
		for i, r in ipairs(rows) do
			frames[i] = CFrame.new(r[1], r[2], r[3], r[4], r[5], r[6], r[7]) * back
		end
		tracks[role].parts[part] = frames
	end
end

local figures = {}                     -- Folder -> { pivot, track, parts = { { part, frames, restLocal } }, phase }

local function register(figure)
	if figures[figure] then return end
	local role = figure:GetAttribute("MerchantRole")
	local pivot = figure:GetAttribute("MerchantPivot")
	local track = role and tracks[role]
	if not track or typeof(pivot) ~= "CFrame" then return end
	local parts, missing = {}, false
	for name, frames in pairs(track.parts) do
		local part = figure:FindFirstChild(name)
		if part and part:IsA("BasePart") then
			-- still in the rest pose here: the server never moves the parts
			parts[#parts + 1] = { part = part, frames = frames, restLocal = pivot:ToObjectSpace(part.CFrame) }
		else
			missing = true
		end
	end
	if missing then return end          -- not everything has arrived yet, try again later
	figures[figure] = { pivot = pivot, track = track, parts = parts, phase = PHASE[role] or 0,
		centre = pivot.Position + Vector3.new(0, 3, 0) }
end

local function scan()
	local market = workspace:FindFirstChild("ArcaneMarket")
	if not market then return end
	for _, d in ipairs(market:GetDescendants()) do
		if d:IsA("Folder") and d.Name == "Figure" then register(d) end
	end
end
task.spawn(function()
	while true do
		scan()
		for figure in pairs(figures) do
			if not figure:IsDescendantOf(workspace) then figures[figure] = nil end
		end
		task.wait(2)
	end
end)

RunService.RenderStepped:Connect(function()
	local camera = workspace.CurrentCamera
	if not camera or not next(figures) then return end
	local eye = camera.CFrame.Position
	local now = workspace:GetServerTimeNow()
	for _, f in pairs(figures) do
		if (eye - f.centre).Magnitude <= RANGE then
			for _, entry in ipairs(f.parts) do
				local count = #entry.frames
				local at = ((now + f.phase) % f.track.duration) / f.track.duration * count
				local i = math.floor(at)
				local a, b = entry.frames[i % count + 1], entry.frames[(i + 1) % count + 1]
				entry.part.CFrame = f.pivot * a:Lerp(b, at - i) * entry.restLocal
			end
		end
	end
end)
