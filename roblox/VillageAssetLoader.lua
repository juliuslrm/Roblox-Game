--[[
	VillageAssetLoader  (UNVERIFIED_IN_STUDIO)

	Loads the uploaded model libraries with InsertService:LoadAsset at server start and stores
	them as template folders in ServerStorage, where VillageWorldBuilder (VillageAssets) and
	WorkshopWorld (ArcaneAssets) look for meshes by name.

	The importer turns the libraries about the vertical axis (ids.importYaw); the loader turns
	every part back so the templates match the level plan.

	Every mesh uses the one palette texture.  If the import lost the texture (MeshPart.TextureID
	empty and no SurfaceAppearance), the loader assigns the uploaded palette image instead.

	Loader.load{ ids = <VillageAssetIds>, insertService = InsertService, parent = ServerStorage }
	  -> report { folders = {name = Folder}, loaded, failed = {..}, meshParts, retextured, texture }
	Existing folders (e.g. imported by hand in Studio) are kept and not loaded again.
]]
local Loader = {}

local function paletteTexture(insertService, decalId, report)
	if not decalId then return nil end
	local ok, result = pcall(function() return insertService:LoadAsset(decalId) end)
	if not ok then
		report.failed[#report.failed + 1] = "palette " .. tostring(decalId) .. ": " .. tostring(result)
		return nil
	end
	local texture
	for _, d in ipairs(result:GetDescendants()) do
		if d:IsA("Decal") and d.Texture ~= "" then texture = d.Texture break end
	end
	result:Destroy()
	return texture
end

local function hasSurfaceAppearance(part)
	for _, child in ipairs(part:GetChildren()) do
		if child:IsA("SurfaceAppearance") then return true end
	end
	return false
end

function Loader.load(opts)
	local ids, insertService, parent = opts.ids, opts.insertService, opts.parent
	local report = { folders = {}, loaded = 0, failed = {}, meshParts = 0, retextured = 0 }
	local texture -- resolved lazily, only when something was actually loaded
	local textureResolved = false

	for folderName, assetIds in pairs(ids.folders or {}) do
		local existing = parent:FindFirstChild(folderName)
		if existing then
			report.folders[folderName] = existing
		else
			local folder = Instance.new("Folder")
			folder.Name = folderName
			local any = false
			for _, assetId in ipairs(assetIds) do
				local ok, result = pcall(function() return insertService:LoadAsset(assetId) end)
				if ok and result then
					result.Name = "Asset_" .. tostring(assetId)
					result.Parent = folder
					report.loaded = report.loaded + 1
					any = true
				else
					report.failed[#report.failed + 1] = tostring(assetId) .. ": " .. tostring(result)
				end
			end
			if any then
				if not textureResolved then
					texture = paletteTexture(insertService, ids.paletteDecal, report)
					textureResolved = true
				end
				local undo = CFrame.Angles(0, math.rad(-(ids.importYaw or 0)), 0)
				for _, d in ipairs(folder:GetDescendants()) do
					if d:IsA("BasePart") and (ids.importYaw or 0) ~= 0 then
						d.CFrame = undo * d.CFrame -- undo the import rotation about the world origin
					end
					if d:IsA("MeshPart") then
						report.meshParts = report.meshParts + 1
						d.Anchored = true
						if folderName == "ArcaneAssets" then d:SetAttribute("PublishedMachineLibrary", true) end
						if texture and d.TextureID == "" and not hasSurfaceAppearance(d) then
							d.TextureID = texture
							report.retextured = report.retextured + 1
						end
					end
				end
				folder.Parent = parent
				report.folders[folderName] = folder
			else
				folder:Destroy()
			end
		end
	end
	report.texture = texture
	return report
end

return Loader
