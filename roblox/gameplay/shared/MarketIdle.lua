local Motion = require(script.Parent.MarketMotion)
local Idle = {}

function Idle.sample(track, seconds)
	local offset = seconds % Motion.duration * (#track - 1) / Motion.duration
	local index = math.floor(offset) + 1
	local a, b = track[index], track[math.min(index + 1, #track)]
	local alpha = offset - math.floor(offset)
	local dot = a[1] * b[1] + a[2] * b[2] + a[3] * b[3] + a[4] * b[4]
	local sign = dot < 0 and -1 or 1
	local x = a[1] * (1 - alpha) + b[1] * alpha * sign
	local y = a[2] * (1 - alpha) + b[2] * alpha * sign
	local z = a[3] * (1 - alpha) + b[3] * alpha * sign
	local w = a[4] * (1 - alpha) + b[4] * alpha * sign
	local length = math.sqrt(x*x + y*y + z*z + w*w)
	return x / length, y / length, z / length, w / length
end

return Idle
