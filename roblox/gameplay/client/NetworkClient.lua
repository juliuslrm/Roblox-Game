-- ROBLOX CLIENT (UNVERIFIED_IN_STUDIO): thin wrapper around the two remotes. All state shown in
-- the UI comes from server snapshots; the client never computes money, items or unlocks itself.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("ArcaneShared")
local Protocol = require(Shared.Protocol)
local Net = { snapshot = nil, listeners = {}, handlers = {}, seq = 0 }
local request = ReplicatedStorage:WaitForChild(Protocol.remoteName, 30)
local event = ReplicatedStorage:WaitForChild(Protocol.eventName, 30)

function Net.onSnapshot(fn) Net.listeners[#Net.listeners + 1] = fn end
function Net.on(name, fn) Net.handlers[name] = fn end
local function publish(snap)
	if not snap then return end
	Net.snapshot = snap
	for _, fn in ipairs(Net.listeners) do task.spawn(fn, snap) end
end
-- Returns the server result table ({ ok, code, payload }).
function Net.send(action, payload)
	if not request then return { ok = false, code = "NOT_READY" } end
	payload = payload or {}
	Net.seq = Net.seq + 1
	payload.actionId = "c" .. Net.seq .. "_" .. math.floor(os.clock() * 1000) % 100000
	local ok, result = pcall(function() return request:InvokeServer(action, payload) end)
	if not ok or type(result) ~= "table" then return { ok = false, code = "NOT_READY" } end
	publish(result.snapshot)
	return result
end
function Net.message(result)
	if result.ok then return nil end
	return Protocol.messages[result.code] or result.code
end
if event then
	event.OnClientEvent:Connect(function(name, data)
		if name == "Snapshot" then publish(data)
		elseif Net.handlers[name] then Net.handlers[name](data) end
	end)
end
return Net
