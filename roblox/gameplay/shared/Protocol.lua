-- Network contract. Payload field types: "int", "num", "str", "bool", "id" (short string), "ids" (array of ids).
-- A field name ending in "?" is optional.
local P = {}
P.remoteName = "ArcaneRequest"
P.eventName = "ArcaneEvent"
P.actions = {
	BuyMarketOffer = { merchant = "id", item = "id" },
	GatherNode = { node = "id" },
	EnterWorkshop = { ["owner?"] = "int" },
	LeaveWorkshop = {},
	PlaceMachine = { machine = "id", gx = "int", gz = "int", floor = "int", rot = "int" },
	RemoveMachine = { uid = "id" },
	RotateMachine = { uid = "id" },
	SetRecipe = { uid = "id", ["recipe?"] = "id" },
	StartManualCraft = { uid = "id", recipe = "id" },
	TransferStack = { from = "id", to = "id", item = "id", amount = "int", ["slot?"] = "id" },
	SetFilter = { uid = "id", ["items?"] = "ids", ["link?"] = "id" },
	ToggleMachine = { uid = "id" },
	BuyUpgrade = { kind = "id" },
	UnlockResearch = { research = "id" },
	StockShelf = { uid = "id", item = "id", amount = "int" },
	ClaimOrder = { kind = "id", id = "id" },
	DonateProject = { amount = "int" },
	InviteCoOp = { user = "int", role = "id" },
	SetCoOpPermission = { user = "int", role = "id" },
	SaveBlueprint = { slot = "int", name = "str", uids = "ids" },
	PlaceBlueprint = { slot = "int", gx = "int", gz = "int", floor = "int" },
	Experiment = { uid = "id" },
	RequestSnapshot = {},
}
P.codes = { OK = "OK", BAD_REQUEST = "BAD_REQUEST", RATE_LIMITED = "RATE_LIMITED", DUPLICATE = "DUPLICATE",
	NOT_FOUND = "NOT_FOUND", FORBIDDEN = "FORBIDDEN", TOO_FAR = "TOO_FAR", LOCKED = "LOCKED",
	NO_FUNDS = "NO_FUNDS", NO_ITEMS = "NO_ITEMS", NO_SPACE = "NO_SPACE", BLOCKED = "BLOCKED",
	BUSY = "BUSY", LIMIT = "LIMIT", NOT_READY = "NOT_READY", SAFE_MODE = "SAFE_MODE" }
-- German feedback texts for result codes (UI falls back to the code).
P.messages = {
	BAD_REQUEST = "Ungültige Anfrage.", RATE_LIMITED = "Zu schnell – kurz warten.", DUPLICATE = "Bereits verarbeitet.",
	NOT_FOUND = "Nicht gefunden.", FORBIDDEN = "Dafür fehlt dir die Berechtigung.", TOO_FAR = "Du bist zu weit entfernt.",
	LOCKED = "Noch nicht freigeschaltet.", NO_FUNDS = "Nicht genug Münzen oder Wissen.", NO_ITEMS = "Es fehlen Zutaten.",
	NO_SPACE = "Kein Platz im Ziel.", BLOCKED = "Dort ist kein Platz frei.", BUSY = "Die Maschine arbeitet gerade.",
	LIMIT = "Limit erreicht.", NOT_READY = "Noch nicht erfüllt.", SAFE_MODE = "Spielstand konnte nicht geladen werden – nur Ansehen möglich.",
}
return P
