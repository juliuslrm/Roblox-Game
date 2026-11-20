-- ROBLOX CLIENT: brings the market traders to life.
-- A trader is a skinned rig (Model "Figure") that the server placed in the rest pose.  Per figure this
-- client plays:
--   body     the idle clips of MarketMotion ("idle" and "idle2" start in the same pose; at the end of a
--            loop the next one is picked at random and blended in over 0.4 s), evaluated exactly like
--            Blender by MarketPose (keys, monotone cubic interpolation, breathing);
--   greet    an additive nod, bow and smile when the figure's GreetAt attribute changes (the server sets
--            it when someone opens the trade) or when this player walks up to the stall;
--   look     head and neck turn towards this player while he is close and in front (limited, smoothed,
--            with pauses so the trader does not stare), otherwise the eyes wander a little;
--   face     blinking at random intervals, the expressions of the clips (smile, focus, ...), the eyes
--            leading the head.
-- A bone's Transform is  restRot^-1 * figureRot * (CFrame(p) * q) * figureRot^-1 * restRot  with q, p in
-- the Roblox frame of the figure (see MarketMotion.lua).  Nothing is replicated: every client animates
-- locally.  Detail drops with distance (face < 40 studs, body < 130 studs, beyond: rest pose).
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("ArcaneShared")
local Motion = require(Shared.MarketMotion)
local Pose = require(Shared.MarketPose)

local RANGE, FACE_RANGE, LOOK_RANGE, GREET_RANGE = 130, 40, 16, 9
local BLEND = 0.4
local LOOK_YAW, LOOK_PITCH = math.rad(38), math.rad(16)
local EYE_YAW, EYE_PITCH = math.rad(22), math.rad(14)
Pose.BREATH = Motion.breath or Pose.BREATH

local prepared = {}
for role, data in pairs(Motion.roles) do
	prepared[role] = Pose.prepare(data)
end

local rng = Random.new()
local figures = {}

local function quatCF(q, p)
	if p then
		return CFrame.new(p[1], p[2], p[3], q[1], q[2], q[3], q[4])
	end
	return CFrame.new(0, 0, 0, q[1], q[2], q[3], q[4])
end

local function register(figure)
	if figures[figure] then return end
	local role = figure:GetAttribute("MerchantRole")
	local pivot = figure:GetAttribute("MerchantPivot")
	local data = role and Motion.roles[role]
	if not data or typeof(pivot) ~= "CFrame" then return end
	local found = {}
	for _, d in ipairs(figure:GetDescendants()) do
		if d:IsA("Bone") then found[d.Name] = d end
	end
	local figureRot = pivot - pivot.Position
	local bones = {}
	local function entry(name)
		if bones[name] then return bones[name] end
		local bone = found[name]
		if not bone then return nil end
		local rest = bone.WorldCFrame - bone.WorldCFrame.Position
		local e = { bone = bone, pre = rest:Inverse() * figureRot, post = figureRot:Inverse() * rest, rest = rest }
		bones[name] = e
		return e
	end
	local channels = Pose.channelsOf(Motion, role)
	local rig = Pose.rigOf(Motion, role)
	for _, list in pairs(channels) do
		for _, b in ipairs(list) do
			if not entry(b[1]) then return end      -- not everything has arrived yet, try again later
		end
	end
	local faceBones, eyes = {}, {}
	for _, pose in pairs(data.poses) do
		for name in pairs(pose) do
			if entry(name) then faceBones[name] = true end
		end
	end
	for _, name in ipairs(rig.eyes) do
		eyes[name] = true
		-- roles with their own rig list the eyes explicitly; the others turn them only if a face pose uses them
		if data.rig and entry(name) then faceBones[name] = true end
	end
	local now = workspace:GetServerTimeNow()
	figures[figure] = {
		role = role, data = data, prep = prepared[role], bones = bones, faceBones = faceBones,
		channels = channels, rig = rig, eyes = eyes,
		figureRot = figureRot, centre = pivot.Position + Vector3.new(0, 5.6, 0),
		clip = "idle", clipStart = now - rng:NextNumber(0, data.clips.idle.duration),
		prevClip = nil, prevStart = 0, blendStart = -10,
		greetStart = nil, lastGreetAt = figure:GetAttribute("GreetAt"), wasNear = false, lastNearGreet = -100,
		lookYaw = 0, lookPitch = 0, eyeYaw = 0, eyePitch = 0,
		attention = 0, attentionUntil = now, saccade = Vector2.zero, nextSaccade = now + 1,
		nextBlink = now + rng:NextNumber(1, 4), blinkStart = -10, doubleBlink = false,
		frame = 0,
	}
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

-- body pose of the current clip (with the blend from the previous one and the greeting on top)
local function bodyPose(f, now)
	local clip = f.data.clips[f.clip]
	local t = now - f.clipStart
	if t >= clip.duration then                       -- loop end: pick the next idle
		f.prevClip, f.prevStart, f.blendStart = f.clip, f.clipStart, now
		f.clip = (f.data.clips.idle2 and rng:NextNumber() < 0.4) and "idle2" or "idle"
		f.clipStart = f.clipStart + clip.duration
		t = now - f.clipStart
	end
	local greetT = nil
	if f.greetStart then
		greetT = now - f.greetStart
		if greetT > f.data.clips.greet.duration then
			f.greetStart, greetT = nil, nil
		end
	end
	local pose = Pose.evaluate(f.channels, f.prep, f.clip, t, greetT, f.rig.breath)
	local blend = (now - f.blendStart) / BLEND
	if f.prevClip and blend < 1 then
		local old = Pose.evaluate(f.channels, f.prep, f.prevClip, now - f.prevStart, greetT, f.rig.breath)
		local u = blend * blend * (3 - 2 * blend)
		for bone, q in pairs(pose) do
			local o = old[bone]
			if o then
				local a = quatCF(o):Lerp(quatCF(q), u)
				local x, y, z, w = a:ToQuaternion()
				pose[bone] = { x, y, z, w }
			end
		end
	end
	local weights = Pose.faceWeights(f.prep, f.clip, t)
	if greetT then
		for name, w in pairs(Pose.faceWeights(f.prep, "greet", greetT)) do
			weights[name] = math.max(weights[name] or 0, w)
		end
	end
	return pose, weights
end

local function approach(current, target, dt, tau)
	return current + (target - current) * (1 - math.exp(-dt / tau))
end

-- head turn and eye direction towards the local player's head (or a wandering point)
local function attention(f, now, dt)
	local character = Players.LocalPlayer.Character
	local head = character and character:FindFirstChild("Head")
	local yaw, pitch = 0, 0
	local near = false
	if head then
		local d = f.figureRot:VectorToObjectSpace(head.Position - f.centre)
		local dist = d.Magnitude
		local inFront = d.Z > -2
		near = dist < LOOK_RANGE and inFront
		if near then
			yaw = math.atan2(d.X, d.Z)
			pitch = -math.atan2(d.Y, math.sqrt(d.X * d.X + d.Z * d.Z))
		end
		-- greet a player who walks up to the stall (once in a while)
		if dist < GREET_RANGE and inFront and not f.wasNear and now - f.lastNearGreet > 25 then
			f.greetStart, f.lastNearGreet = now, now
		end
		f.wasNear = dist < GREET_RANGE + 2
	end
	-- attention: look at the player for a few seconds, then glance away, then back
	if now > f.attentionUntil then
		if f.attention == 1 then
			f.attention, f.attentionUntil = 0, now + rng:NextNumber(1.2, 3)
		else
			f.attention, f.attentionUntil = 1, now + rng:NextNumber(2.5, 6)
		end
	end
	local watching = near and (f.attention == 1 or f.greetStart ~= nil)
	local ty = watching and math.clamp(yaw, -LOOK_YAW, LOOK_YAW) or 0
	local tp = watching and math.clamp(pitch, -LOOK_PITCH, LOOK_PITCH) or 0
	f.lookYaw = approach(f.lookYaw, ty, dt, 0.45)
	f.lookPitch = approach(f.lookPitch, tp, dt, 0.45)
	-- eyes: towards the remaining angle when watching, small saccades otherwise
	if now > f.nextSaccade then
		f.saccade = Vector2.new(rng:NextNumber(-0.12, 0.12), rng:NextNumber(-0.07, 0.07))
		f.nextSaccade = now + rng:NextNumber(0.7, 2.6)
	end
	local ey, ep = f.saccade.X, f.saccade.Y
	if watching then
		ey = math.clamp(yaw - f.lookYaw, -EYE_YAW, EYE_YAW)
		ep = math.clamp(pitch - f.lookPitch, -EYE_PITCH, EYE_PITCH)
	end
	if math.abs(ty - f.lookYaw) > 0.35 and now - f.blinkStart > 1 then
		f.nextBlink = now                            -- people blink when the head turns a lot
	end
	f.eyeYaw = approach(f.eyeYaw, ey, dt, 0.06)
	f.eyePitch = approach(f.eyePitch, ep, dt, 0.06)
end

local function blinkWeight(f, now)
	if now >= f.nextBlink then
		f.blinkStart = now
		f.doubleBlink = rng:NextNumber() < 0.15
		f.nextBlink = now + rng:NextNumber(2.2, 6.0)
	end
	local u = now - f.blinkStart
	local w = 0
	if u < 0.07 then
		w = u / 0.07
	elseif u < 0.19 then
		w = 1 - (u - 0.07) / 0.12
	elseif f.doubleBlink and u < 0.45 and u > 0.26 then
		local v = u - 0.26
		w = v < 0.06 and v / 0.06 or math.max(0, 1 - (v - 0.06) / 0.12)
	end
	return w
end

local function apply(f, now, dt, withFace)
	local pose, weights = bodyPose(f, now)
	local look = CFrame.Angles(0, f.lookYaw, 0) * CFrame.Angles(f.lookPitch, 0, 0)
	local transforms = {}
	for name, q in pairs(pose) do
		transforms[name] = quatCF(q)
	end
	-- the look turn is shared by neck (40 %) and head (60 %), on top of the clip
	local neckName, headName = f.rig.neck, f.rig.head
	local neck, head = transforms[neckName], transforms[headName]
	if neck then transforms[neckName] = CFrame.new():Lerp(look, 0.4) * neck end
	if head then transforms[headName] = CFrame.new():Lerp(look, 0.6) * head end
	if withFace then
		weights.blink = math.max(weights.blink or 0, blinkWeight(f, now))
		local face = {}
		for poseName, w in pairs(weights) do
			local spec = f.data.poses[poseName]
			if spec and w > 0.001 then
				for bone, e in pairs(spec) do
					local cur = face[bone] or { rot = CFrame.new(), move = Vector3.zero }
					cur.rot = CFrame.new():Lerp(quatCF(e.q), w) * cur.rot
					if e.p then
						cur.move = cur.move + Vector3.new(e.p[1], e.p[2], e.p[3]) * w
					end
					face[bone] = cur
				end
			end
		end
		for bone in pairs(f.faceBones) do
			local cur = face[bone]
			local cf = cur and (CFrame.new(cur.move) * cur.rot) or CFrame.new()
			if f.eyes[bone] then
				cf = cf * CFrame.Angles(0, f.eyeYaw, 0) * CFrame.Angles(f.eyePitch, 0, 0)
			end
			transforms[bone] = cf
		end
	end
	for name, cf in pairs(transforms) do
		local e = f.bones[name]
		if e then
			e.bone.Transform = e.pre * cf * e.post
		end
	end
end

local function rest(f)
	for _, e in pairs(f.bones) do
		e.bone.Transform = CFrame.new()
	end
	f.resting = true
end

RunService.RenderStepped:Connect(function(dt)
	local camera = workspace.CurrentCamera
	if not camera or not next(figures) then return end
	local eye = camera.CFrame.Position
	local now = workspace:GetServerTimeNow()
	for figure, f in pairs(figures) do
		local greetAt = figure:GetAttribute("GreetAt")
		if greetAt and greetAt ~= f.lastGreetAt then
			f.lastGreetAt = greetAt
			f.greetStart = now
		end
		local dist = (eye - f.centre).Magnitude
		if dist <= RANGE then
			f.frame = f.frame + 1
			-- far away: the body moves at a lower update rate, without face and look
			if dist < FACE_RANGE or f.frame % 3 == 0 then
				local near = dist < FACE_RANGE
				if near then attention(f, now, dt) end
				apply(f, now, near and dt or dt * 3, near)
				f.resting = false
			end
		elseif not f.resting then
			rest(f)
		end
	end
end)
