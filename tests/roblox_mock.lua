--[[
	Minimal stand-in for the parts of the Roblox API that the village scripts
	use (Vector3, CFrame, Color3, Instance, Enum, workspace, game).  It exists
	only so that the placement maths can be executed and checked outside
	Roblox Studio.  It is NOT a faithful engine: it models data, hierarchy and
	transforms, nothing else.
]]

-- ---------------------------------------------------------------- Vector3
local V3 = {}
V3.__index = function(self, key)
	if key == "Magnitude" then
		return math.sqrt(self.X * self.X + self.Y * self.Y + self.Z * self.Z)
	elseif key == "Unit" then
		local m = math.sqrt(self.X * self.X + self.Y * self.Y + self.Z * self.Z)
		return V3.new(self.X / m, self.Y / m, self.Z / m)
	end
	return V3[key]
end
function V3.new(x, y, z)
	return setmetatable({ X = x or 0, Y = y or 0, Z = z or 0 }, V3)
end
V3.__add = function(a, b) return V3.new(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
V3.__sub = function(a, b) return V3.new(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
V3.__unm = function(a) return V3.new(-a.X, -a.Y, -a.Z) end
V3.__mul = function(a, b)
	if type(a) == "number" then return V3.new(a * b.X, a * b.Y, a * b.Z) end
	if type(b) == "number" then return V3.new(a.X * b, a.Y * b, a.Z * b) end
	return V3.new(a.X * b.X, a.Y * b.Y, a.Z * b.Z)
end
V3.__div = function(a, b)
	if type(b) == "number" then return V3.new(a.X / b, a.Y / b, a.Z / b) end
	return V3.new(a.X / b.X, a.Y / b.Y, a.Z / b.Z)
end
function V3.Cross(a, b)
	return V3.new(a.Y * b.Z - a.Z * b.Y, a.Z * b.X - a.X * b.Z, a.X * b.Y - a.Y * b.X)
end
Vector3 = V3

-- ---------------------------------------------------------------- CFrame
-- p = position, m = row-major 3x3 rotation
local CF = {}
local function cf(px, py, pz, m)
	return setmetatable({ px = px, py = py, pz = pz, m = m }, CF)
end
local IDENTITY = { 1, 0, 0, 0, 1, 0, 0, 0, 1 }
local function mmul(a, b)
	local r = {}
	for i = 0, 2 do
		for j = 0, 2 do
			r[i * 3 + j + 1] = a[i * 3 + 1] * b[j + 1] + a[i * 3 + 2] * b[3 + j + 1] + a[i * 3 + 3] * b[6 + j + 1]
		end
	end
	return r
end
local function mvec(m, x, y, z)
	return m[1] * x + m[2] * y + m[3] * z, m[4] * x + m[5] * y + m[6] * z, m[7] * x + m[8] * y + m[9] * z
end
CF.__index = function(self, key)
	if key == "Position" then
		return V3.new(self.px, self.py, self.pz)
	elseif key == "X" then return self.px
	elseif key == "Y" then return self.py
	elseif key == "Z" then return self.pz
	end
	return CF[key]
end
function CF.new(a, b, c)
	if a == nil then
		return cf(0, 0, 0, IDENTITY)
	elseif type(a) == "number" then
		return cf(a, b, c, IDENTITY)
	elseif b == nil then
		return cf(a.X, a.Y, a.Z, IDENTITY)
	end
	-- CFrame.new(position, lookAt): -Z points at the target
	local look = (b - a).Unit
	local right = V3.Cross(look, V3.new(0, 1, 0)).Unit
	local up = V3.Cross(right, look)
	return cf(a.X, a.Y, a.Z, { right.X, up.X, -look.X, right.Y, up.Y, -look.Y, right.Z, up.Z, -look.Z })
end
function CF.Angles(rx, ry, rz)
	local cx, sx = math.cos(rx), math.sin(rx)
	local cy, sy = math.cos(ry), math.sin(ry)
	local cz, sz = math.cos(rz), math.sin(rz)
	local mx = { 1, 0, 0, 0, cx, -sx, 0, sx, cx }
	local my = { cy, 0, sy, 0, 1, 0, -sy, 0, cy }
	local mz = { cz, -sz, 0, sz, cz, 0, 0, 0, 1 }
	return cf(0, 0, 0, mmul(mmul(mx, my), mz))
end
CF.__mul = function(a, b)
	if getmetatable(b) == V3 then
		local x, y, z = mvec(a.m, b.X, b.Y, b.Z)
		return V3.new(x + a.px, y + a.py, z + a.pz)
	end
	local x, y, z = mvec(a.m, b.px, b.py, b.pz)
	return cf(x + a.px, y + a.py, z + a.pz, mmul(a.m, b.m))
end
CF.__add = function(a, v) return cf(a.px + v.X, a.py + v.Y, a.pz + v.Z, a.m) end
CF.__sub = function(a, v) return cf(a.px - v.X, a.py - v.Y, a.pz - v.Z, a.m) end
function CF:Inverse()
	local m = self.m
	local t = { m[1], m[4], m[7], m[2], m[5], m[8], m[3], m[6], m[9] }
	local x, y, z = mvec(t, -self.px, -self.py, -self.pz)
	return cf(x, y, z, t)
end
function CF:ToObjectSpace(other) return self:Inverse() * other end
function CF:VectorToWorldSpace(v)
	local x, y, z = mvec(self.m, v.X, v.Y, v.Z)
	return V3.new(x, y, z)
end
function CF:PointToWorldSpace(v) return self * v end
function CF:components()
	return self.px, self.py, self.pz, self.m[1], self.m[2], self.m[3], self.m[4], self.m[5], self.m[6], self.m[7],
		self.m[8], self.m[9]
end
CFrame = CF

-- ---------------------------------------------------------------- Color3 / Enum
Color3 = {}
function Color3.new(r, g, b) return { R = r, G = g, B = b } end
function Color3.fromRGB(r, g, b) return { R = r / 255, G = g / 255, B = b / 255 } end

local function enumNode(path)
	return setmetatable({ _path = path }, {
		__index = function(_, key) return enumNode(path .. "." .. key) end,
		__tostring = function() return path end,
		__eq = function(a, b) return a._path == b._path end,
	})
end
Enum = enumNode("Enum")

-- ---------------------------------------------------------------- Instance
local PARENT_CLASS = {
	Part = "BasePart", MeshPart = "BasePart", SpawnLocation = "Part", BasePart = "PVInstance",
	Model = "PVInstance", PVInstance = "Instance", Folder = "Instance", PointLight = "Light",
	Light = "Instance", Terrain = "BasePart",
}
-- properties that scripts may not write at run time (mirrors Roblox behaviour)
MOCK_READONLY = { CollisionFidelity = true }
MOCK_WARNINGS = {}

local methods = {}
local META = {}

local function isA(class, wanted)
	while class do
		if class == wanted then return true end
		class = PARENT_CLASS[class]
	end
	return false
end

local function raw(inst) return rawget(inst, "_") end

META.__index = function(self, key)
	local m = methods[key]
	if m then return m end
	local data = raw(self)
	if key == "Parent" then return data.parent end
	if key == "ClassName" then return data.class end
	local value = data.props[key]
	if value ~= nil then return value end
	for _, child in ipairs(data.children) do
		if raw(child).props.Name == key then return child end
	end
	return nil
end
META.__newindex = function(self, key, value)
	local data = raw(self)
	if key == "Parent" then
		if data.parent then
			local siblings = raw(data.parent).children
			for i = #siblings, 1, -1 do
				if siblings[i] == self then table.remove(siblings, i) end
			end
		end
		data.parent = value
		if value then table.insert(raw(value).children, self) end
	elseif MOCK_READONLY[key] then
		error("The current thread cannot write '" .. key .. "' (lacking capability Plugin)")
	else
		data.props[key] = value
	end
end

Instance = {}
function Instance.new(class, parent)
	local inst = setmetatable({ _ = { class = class, props = { Name = class }, children = {}, attrs = {} } }, META)
	local p = raw(inst).props
	if isA(class, "BasePart") then
		p.Size = V3.new(4, 1, 2)
		p.CFrame = CF.new()
		p.Anchored = false
		p.CanCollide = true
		p.Transparency = 0
		p.CastShadow = true
	end
	if parent then inst.Parent = parent end
	return inst
end

function methods:IsA(class) return isA(raw(self).class, class) or class == "Instance" end
function methods:GetChildren()
	local out = {}
	for i, c in ipairs(raw(self).children) do out[i] = c end
	return out
end
function methods:GetDescendants()
	local out = {}
	local function walk(node)
		for _, c in ipairs(raw(node).children) do
			out[#out + 1] = c
			walk(c)
		end
	end
	walk(self)
	return out
end
function methods:FindFirstChild(name, recursive)
	for _, c in ipairs(raw(self).children) do
		if raw(c).props.Name == name then return c end
	end
	if recursive then
		for _, c in ipairs(raw(self).children) do
			local hit = c:FindFirstChild(name, true)
			if hit then return hit end
		end
	end
	return nil
end
methods.WaitForChild = methods.FindFirstChild
function methods:Clone()
	local data = raw(self)
	local copy = Instance.new(data.class)
	local cd = raw(copy)
	for k, v in pairs(data.props) do cd.props[k] = v end
	for k, v in pairs(data.attrs) do cd.attrs[k] = v end
	for _, child in ipairs(data.children) do
		child:Clone().Parent = copy
	end
	return copy
end
function methods:Destroy()
	self.Parent = nil
	raw(self).destroyed = true
end
function methods:SetAttribute(name, value) raw(self).attrs[name] = value end
function methods:GetAttribute(name) return raw(self).attrs[name] end
function methods:GetFullName()
	local data = raw(self)
	if data.parent then return data.parent:GetFullName() .. "." .. data.props.Name end
	return data.props.Name
end

-- ---------------------------------------------------------------- globals
workspace = Instance.new("Folder")
workspace.Name = "Workspace"
MOCK_FILLS = {}
local terrain = Instance.new("Terrain", workspace)
terrain.Name = "Terrain"
methods.FillBlock = function(self, cframe, size, material)
	MOCK_FILLS[#MOCK_FILLS + 1] = { cframe = cframe, size = size, material = tostring(material) }
end

local services = {}
game = {}
function game:GetService(name)
	if not services[name] then
		services[name] = Instance.new("Folder")
		services[name].Name = name
	end
	return services[name]
end

function warn(...)
	local parts = {}
	for i = 1, select("#", ...) do parts[i] = tostring((select(i, ...))) end
	MOCK_WARNINGS[#MOCK_WARNINGS + 1] = table.concat(parts, " ")
end
function typeof(v)
	local mt = getmetatable(v)
	if mt == V3 then return "Vector3" elseif mt == CF then return "CFrame" elseif mt == META then return "Instance" end
	return type(v)
end
