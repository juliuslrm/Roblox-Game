-- Where and how the model of a workshop part sits: used by the server to build the part and by the
-- build preview to show the white hologram in exactly the same place (one rule for both).
local Config = require(script.Parent.Config)
local Grid = require(script.Parent.GridMath)
local Pose = {}

-- Centre of the footprint at the part's nominal middle height, and that height.
-- cellCenter(floor, x, z) -> Vector3: floor-level centre of a grid cell.
function Pose.base(def, e, cellCenter)
	local w, d = Grid.size(def, e.rot)
	local cs = Config.cellSize
	local height = (def.category == "transport") and 0.8 or (def.kind == "shelf") and 6 or 4
	if def.layer == "pipe" then height = 0.5 end
	local base = cellCenter(e.floor, e.gx, e.gz)
		+ Vector3.new((w - 1) * cs / 2, height / 2 + (def.layer == "pipe" and 0.05 or 0), (d - 1) * cs / 2)
	return base, height
end

-- Sizes and turns `body`, a clone of `template`, for entity e (base and height from Pose.base).
-- Models: WorkshopModels (bounds of single uploaded models).  Returns the light specs of the model
-- and the offset of the model centre from its ground pivot (both only for single models).
function Pose.place(body, template, def, e, base, height, Models)
	local cs = Config.cellSize
	local turn = CFrame.Angles(0, math.rad(90 * e.rot), 0)
	if template:GetAttribute("PublishedMachineLibrary") then
		-- undo whatever scale the importer applied: the mesh was designed to fill its footprint
		local k = math.max(template.Size.X, template.Size.Z) / (math.max(def.w, def.d) * cs)
		body.Size = (k > 1.05 or k < 0.6) and template.Size / k or template.Size
		-- keep the template's own rotation (the asset loader corrects the import orientation there)
		-- and stand the mesh on the floor: a MeshPart's CFrame is the centre of its bounding box
		local floorY = base.Y - height / 2
		body.CFrame = CFrame.new(base.X, floorY + body.Size.Y / 2, base.Z) * turn * (template.CFrame - template.CFrame.Position)
		return nil
	end
	local pivot = CFrame.new(base - Vector3.new(0, height / 2, 0)) * turn
	local mesh = Models[def.modelAssetId]
	if mesh then
		-- imported MeshParts are centred on the geometry bounds: recover the grid-centred,
		-- ground-level pivot before turning
		local offset = Vector3.new(table.unpack(mesh.center))
		body.Size = Vector3.new(table.unpack(mesh.size))
		body.CFrame = pivot * CFrame.new(offset)
		return mesh.lights, offset
	end
	body.CFrame = pivot
	return nil
end

return Pose
