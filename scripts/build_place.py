#!/usr/bin/env python3
"""Writes exports/roblox/ArcaneVillage.rbxlx - a Roblox place file (XML) that contains every script
of this repository in the right service.  Open it in Roblox Studio and press Play.

Meshes cannot be stored in a place file (they are cloud assets), so the place starts in
"greybox" mode until the .glb libraries have been imported (docs/ROBLOX_IMPORT.md).

UNVERIFIED_IN_STUDIO: the file is well-formed XML in the documented rbxlx layout, but it has
never been opened in Roblox Studio.
"""
import os
import sys
from xml.sax.saxutils import escape

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "exports", "roblox", "ArcaneVillage.rbxlx")
_ref = [0]


def ref():
    _ref[0] += 1
    return f"RBX{_ref[0]:06d}"


def item(cls, name, children="", props=""):
    return (f'<Item class="{cls}" referent="{ref()}"><Properties><string name="Name">{escape(name)}</string>'
            f'{props}</Properties>{children}</Item>\n')


def script(cls, name, rel):
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    if len(src) >= 200000:
        raise SystemExit(f"{rel}: {len(src)} characters exceed the Roblox script limit")
    src = src.replace("]]>", "]]]]><![CDATA[>")
    return item(cls, name, props=f'<ProtectedString name="Source"><![CDATA[{src}]]></ProtectedString>')


def folder_of(rel_dir, name):
    """Folder with one script per .lua file (X.server.lua -> Script, X.client.lua -> LocalScript)."""
    out = ""
    for fn in sorted(os.listdir(os.path.join(ROOT, rel_dir))):
        if not fn.endswith(".lua"):
            continue
        rel = f"{rel_dir}/{fn}"
        if fn.endswith(".server.lua"):
            out += script("Script", fn[:-11], rel)
        elif fn.endswith(".client.lua"):
            out += script("LocalScript", fn[:-11], rel)
        else:
            out += script("ModuleScript", fn[:-4], rel)
    return item("Folder", name, out)


def main():
    village = "".join(script("ModuleScript", n, f"roblox/{n}.lua") for n in
                      ("VillageWorldBuilder", "VillageTerrainBuilder", "VillageAutoBuild", "WorldLayout", "WorldHeightmap"))
    readme = ("-- Arcane Village: press Play.\n"
              "-- Without imported meshes the village appears as placeholder blocks on voxel terrain.\n"
              "-- To get the real models import exports/library/village_assets.glb and village_terrain.glb into\n"
              "-- ServerStorage.VillageAssets and exports/library/arcane_machines.glb into ServerStorage.ArcaneAssets.\n"
              "return {}\n")
    body = ""
    body += item("Workspace", "Workspace", props='<bool name="StreamingEnabled">false</bool>')
    body += item("Lighting", "Lighting", props='<float name="ClockTime">15.2</float><float name="Brightness">2.6</float>')
    body += item("ReplicatedStorage", "ReplicatedStorage", folder_of("roblox/gameplay/shared", "ArcaneShared"))
    body += item("ServerStorage", "ServerStorage",
                 item("Folder", "VillageWorld", village)
                 + item("ModuleScript", "README", props=f'<ProtectedString name="Source"><![CDATA[{readme}]]></ProtectedString>'))
    body += item("ServerScriptService", "ServerScriptService",
                 script("Script", "VillageAutoBuild", "roblox/VillageAutoBuild.server.lua")
                 + folder_of("roblox/gameplay/server", "ArcaneServer"))
    body += item("StarterPlayer", "StarterPlayer",
                 item("StarterPlayerScripts", "StarterPlayerScripts", folder_of("roblox/gameplay/client", "ArcaneClient")))
    xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
           '<External>null</External>\n<External>nil</External>\n' + body + '</roblox>\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(xml)
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(xml) / 1e6:.2f} MB, {_ref[0]} instances")


if __name__ == "__main__":
    main()
