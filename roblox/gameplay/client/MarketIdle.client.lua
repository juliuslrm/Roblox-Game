local RunService = game:GetService("RunService")
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("ArcaneShared")
local Motion = require(Shared.MarketMotion)
local Idle = require(Shared.MarketIdle)

local phases = { selma = 0, nyra = 1.8, lio = 3.4, aron = 5.0, esme = 6.6 }
local bones = {}

local function add(bone)
	if not bone:IsA("Bone") then return end
	local mesh = bone:FindFirstAncestorWhichIsA("MeshPart")
	local role = mesh and mesh:GetAttribute("MarketRigRole")
	local tracks = role and Motion.bones[role]
	local track = tracks and tracks[bone.Name]
	if track then
		-- Use the skin's bind axes even if the Studio importer reorients the bones.
		local basis = mesh.CFrame.Rotation:ToObjectSpace(bone.WorldCFrame.Rotation)
		bones[bone] = { mesh = mesh, track = track, basis = basis, inverse = basis:Inverse(), phase = phases[role] }
	end
end

workspace.DescendantAdded:Connect(add)
workspace.DescendantRemoving:Connect(function(instance) bones[instance] = nil end)
local market = workspace:FindFirstChild("ArcaneMarket")
if market then
	for _, instance in ipairs(market:GetDescendants()) do add(instance) end
end

RunService.PreRender:Connect(function()
	local camera = workspace.CurrentCamera
	if not camera or not next(bones) then return end
	local eye = camera.CFrame.Position
	local time = workspace:GetServerTimeNow()
	for bone, info in pairs(bones) do
		if (eye - info.mesh.Position).Magnitude <= 110 then
			local rotation = CFrame.new(0, 0, 0, Idle.sample(info.track, time + info.phase))
			bone.Transform = info.inverse * rotation * info.basis
		end
	end
end)
