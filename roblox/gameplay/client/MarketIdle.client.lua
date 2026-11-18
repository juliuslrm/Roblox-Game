-- ROBLOX CLIENT: plays the idle loops of the market traders.
-- A trader is a skinned rig (Model "Figure") that the server placed in the rest pose.  MarketMotion
-- holds, per animated bone, one local rotation q per sample (Roblox frame of the figure, about the
-- bone's joint).  The bone's rest orientation R (world, read once while the rig still rests) and the
-- figure's orientation F turn it into the bone's Transform:  R^-1 * F * q * F^-1 * R.
-- Only this client sees the motion; the server never moves the bones, nothing is replicated.
local RunService = game:GetService("RunService")
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("ArcaneShared")
local Motion = require(Shared.MarketMotion)

local RANGE = 130                      -- studs: traders further away stand still
local PHASE = { selma = 0, nyra = 1.7, lio = 3.1, aron = 4.6, esme = 2.4 }   -- so they do not move in step

local tracks = {}
for role, data in pairs(Motion.roles) do
	local bones = {}
	for bone, rows in pairs(data.bones) do
		local frames = table.create(#rows)
		for i, r in ipairs(rows) do
			frames[i] = CFrame.new(0, 0, 0, r[1], r[2], r[3], r[4])
		end
		bones[bone] = frames
	end
	tracks[role] = { duration = data.duration, bones = bones }
end

local figures = {}                     -- Model -> { track, bones = { { bone, frames, pre, post } }, phase, centre }

local function register(figure)
	if figures[figure] then return end
	local role = figure:GetAttribute("MerchantRole")
	local pivot = figure:GetAttribute("MerchantPivot")
	local track = role and tracks[role]
	if not track or typeof(pivot) ~= "CFrame" then return end
	local found = {}
	for _, d in ipairs(figure:GetDescendants()) do
		if d:IsA("Bone") then found[d.Name] = d end
	end
	local figureRot = pivot - pivot.Position
	local list = {}
	for name, frames in pairs(track.bones) do
		local bone = found[name]
		if not bone then return end   -- not everything has arrived yet, try again later
		local rest = bone.WorldCFrame - bone.WorldCFrame.Position
		list[#list + 1] = { bone = bone, frames = frames, pre = rest:Inverse() * figureRot, post = figureRot:Inverse() * rest }
	end
	figures[figure] = { track = track, bones = list, phase = PHASE[role] or 0,
		centre = pivot.Position + Vector3.new(0, 3, 0) }
end

local function scan()
	local market = workspace:FindFirstChild("ArcaneMarket")
	if not market then return end
	for _, d in ipairs(market:GetDescendants()) do
		if d:IsA("Model") and d.Name == "Figure" then register(d) end
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
			for _, entry in ipairs(f.bones) do
				local count = #entry.frames
				local at = ((now + f.phase) % f.track.duration) / f.track.duration * count
				local i = math.floor(at)
				local a, b = entry.frames[i % count + 1], entry.frames[(i + 1) % count + 1]
				entry.bone.Transform = entry.pre * a:Lerp(b, at - i) * entry.post
			end
		end
	end
end)
