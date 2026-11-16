"""Generate the Arcane Village workshop and validate its preview layout.

Blender: blender -b --python-exit-code 1 -P blender/build_workshop.py -- [--no-render]
Python:  python blender/build_workshop.py [--no-render]
Uses the existing village exports and a Lua runtime (lupa).
"""
import argparse
import json
import math
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE), str(ROOT / "roblox/gameplay/tests")]

from harness import lua_list, new_runtime
from village import coords, export, luadata, palette, registry, scene, workshop
from village.building import gable_roof
from village.machines import MACHINES, _pipe_node, valve
from village.meshkit import MeshBuilder, R, T

ASSET = "house_01_timber_cottage"
ART = ROOT / "assets/workshop"
EXPORT = ROOT / "exports/glb/workshop"
PREVIEW = ROOT / "previews/workshop"

# id, machine, cell x/z, rotation, recipe (when relevant)
FACTORY = (
    ("hopper", "input_hopper", 11, 5, 0, None),
    ("feed", "wooden_belt", 11, 6, 0, None),
    ("mill", "grinder", 11, 7, 0, "r06"),
    ("powder_a", "wooden_belt", 11, 9, 0, None),
    ("powder_b", "wooden_belt", 11, 10, 0, None),
    ("extractor", "extractor", 10, 11, 0, "r10"),
    ("essence", "pipe_straight", 13, 11, 0, None),
    ("filler", "bottler", 14, 11, 0, "r12"),
    ("tonics", "wooden_belt", 14, 13, 0, None),
    ("finished", "storage_crate", 14, 14, 0, None),
    ("pump", "well_pump", 10, 14, 2, None),
    ("water_a", "pipe_bend", 9, 15, 0, None),
    ("water_b", "pipe_straight", 9, 14, 0, None),
    ("water_c", "pipe_straight", 9, 13, 0, None),
    ("water_d", "pipe_straight", 9, 12, 0, None),
    ("water_e", "pipe_bend", 9, 11, 0, None),
)


def validate_layout():
    lua = new_runtime()
    load = lua.globals().loadModule
    data = load("server/Data")
    architecture = load("shared/WorkshopArchitecture")
    place = load("server/PlacementService")
    sim = load("server/WorkshopSimulation")
    profile = load("server/ProfileService").new(1)
    starter = lua_list(profile.workshop.layout)
    assert data.Config.cellSize == 2 and place.cells(profile) == 16
    for _, definition in data.Machines.items():
        profile.research[definition.research] = True
    uids = {}
    for name, machine, x, z, rotation, recipe in FACTORY:
        entity = place.place(profile, machine, x, z, 1, rotation, True)
        assert entity is not None and not isinstance(entity, tuple), (name, entity)
        entity.recipe = recipe
        uids[name] = entity.uid
    expanded = lua_list(profile.workshop.layout)
    for entity in expanded:
        definition = data.Machines[entity.machine]
        for x, _z in (lua_list(cell) for cell in data.GridMath.cells(definition, entity.gx, entity.gz, entity.rot).values()):
            assert not 6 <= x <= 8, (entity.machine, "occupies the 6-stud central aisle")

    crate = next(e for e in starter if e.machine == "storage_crate")
    buffers = profile.workshop.buffers
    buffers[crate.uid].inv.herb_mint = 8
    buffers[uids["filler"]].inv.vial = 4
    runtime = sim.newRuntime()
    for _ in range(480):
        sim.step(profile, runtime, 0.25)
    count = buffers[uids["finished"]].inv.tonic_bottled
    assert count == 4, (count, "the displayed factory must make four real tonics")

    for size in (32, 48, 64, 80):
        for floors in (1, 2, 3):
            parts, _ = architecture.build(size, floors, data.Config.floorHeight)
            slabs = [part for part in parts.values() if part.floor is not None]
            assert len(slabs) == 1 + 2 * (floors - 1)
            assert sum(part.name == "ExitDoor" for part in parts.values()) == 1
            for part in slabs:
                if part.floor > 1:
                    x, _y, z = lua_list(part.position)
                    w, _h, d = lua_list(part.size)
                    assert x - w / 2 >= -size / 2 + 6 or z + d / 2 <= size / 2 - 8
    print(f"[workshop] validated 12 room sizes/floor counts and {count} bottled tonics in 120 simulated seconds")
    parts, lights = architecture.build(32, 1, data.Config.floorHeight)
    return data, starter, expanded[len(starter):], lua_list(parts), lua_list(lights)


def point(v):
    """Roblox (x, up, z) to Blender (x, -z, up)."""
    return v[0], -v[2], v[1]


def collection(target, name):
    group = bpy.data.collections.new(name)
    target.collection.children.link(group)
    return group


def light(target, name, location, energy, size, color):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.shadow_soft_size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    target.collection.objects.link(obj)
    obj.location = location


def facade_metadata(mesh):
    entry = export.describe(mesh, "houses", "", "")
    bounds = entry["bounds_roblox"]
    data = {
        "size": bounds["size"], "center": bounds["center"], "category": "houses",
        "collision": entry["collision"], "castShadow": entry["cast_shadow"],
        "colliders": entry["colliders"], "lights": entry["lights"],
    }
    (ROOT / "roblox/WorkshopFacade.lua").write_text(
        "-- Generated by blender/build_workshop.py.\nreturn " + luadata.to_lua(data, inline_depth=2) + "\n",
        encoding="utf-8",
    )
    return data


def machine_metadata(kettle):
    manifest = json.loads((ROOT / "world/gameplay_asset_manifest.json").read_text(encoding="utf-8"))
    machines = {name: {key: value["bounds_roblox"][key] for key in ("size", "center")}
                for name, value in manifest["assets"].items()}
    entry = export.describe(kettle, "machines", "", "")
    machines["mach_kettle"] = {key: entry["bounds_roblox"][key] for key in ("size", "center")}
    machines["mach_kettle"]["lights"] = entry["lights"]
    (ROOT / "roblox/gameplay/shared/WorkshopModels.lua").write_text(
        "-- Generated by blender/build_workshop.py.\nreturn " + luadata.to_lua(machines, inline_depth=2) + "\n",
        encoding="utf-8",
    )


def read_glb(path):
    content = path.read_bytes()
    signature, version, length, json_size, json_type = struct.unpack_from("<4s4I", content)
    assert (signature, version, length, json_type) == (b"glTF", 2, len(content), 0x4E4F534A), path
    data = json.loads(content[20:20 + json_size])
    assert len(data["materials"]) == len(data["images"]) == 1 and "bufferView" in data["images"][0], path
    triangles = 0
    for mesh in data["meshes"]:
        for primitive in mesh["primitives"]:
            assert primitive.get("mode", 4) == 4
            assert {"POSITION", "TEXCOORD_0", "NORMAL"} <= set(primitive["attributes"])
            count = data["accessors"][primitive["indices"]]["count"]
            assert count % 3 == 0
            triangles += count // 3
    assert max(
        sum(data["accessors"][primitive["indices"]]["count"] // 3 for primitive in mesh["primitives"])
        for mesh in data["meshes"]
    ) < 10_000, path
    return data, triangles


def road_context(target, layout, placement, facade_max_depth):
    inverse = (T(*placement["location"]) @ R("Z", placement["rotation_z_deg"])).inverted()
    group = collection(target, "Dorfumgebung")
    prototypes = {}
    for instance in layout["instances"]:
        name, kind = instance["asset"], instance["group"]
        if name == ASSET:
            continue
        pose = instance["blender"]
        position = pose["location"]
        distance = (Vector(position) - Vector(placement["location"])).xy.length
        if kind not in ("terrain", "roads") and (distance > 64 or name not in registry.ASSETS):
            continue
        if kind == "terrain" and distance > 135:
            continue
        if kind == "roads" and name not in ("road_south_road", "plaza_paving"):
            continue
        if name not in prototypes:
            if name in registry.ASSETS:
                prototypes[name] = registry.build(name).to_mesh(name, scene.TEXTURE_PATH)
            else:
                bpy.ops.import_scene.gltf(filepath=str(ROOT / layout["assets"][name]["glb"]))
                imported, = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
                prototypes[name] = imported.data.copy()
                prototypes[name].transform(imported.matrix_world)
                bpy.data.objects.remove(imported, do_unlink=True)
        scale = pose["scale"]
        obj = bpy.data.objects.new(instance.get("name", name), prototypes[name])
        group.objects.link(obj)
        obj.matrix_world = inverse @ T(*position) @ R("Z", pose["rotation_z_deg"])
        obj.scale = (scale,) * 3

    # Work in the asset's local coordinates to compare facade, portal and real road.
    old = layout["assets"][ASSET]["bounds_blender"]
    portal = Vector((0, old["min"][1] - 5, 0))
    road = next(r for r in layout["roads"] if r["id"] == "south_road")
    points = [inverse @ Vector(point(p)) for p in road["points_roblox"]]
    nearest = None
    for a, b in zip(points, points[1:]):
        ab = b - a
        t = max(0, min(1, (portal - a).xy.dot(ab.xy) / ab.xy.length_squared))
        candidate = a.lerp(b, t)
        if nearest is None or (portal - candidate).xy.length < (portal - nearest).xy.length:
            nearest = candidate
    assert portal.y < facade_max_depth < 0 and nearest.y < facade_max_depth
    assert (portal - nearest).xy.length < 18, (portal, nearest)
    print(f"[workshop] portal clear of facade, {((portal - nearest).xy.length):.1f} studs to road centre")
    return nearest


def interior(target, boxes, lamps):
    builders = {key: MeshBuilder(seed=47) for key in ("Boden", "Wände", "Frontwand", "Balken", "Tür", "Einrichtung")}
    for spec in boxes:
        name = spec.name
        if name.startswith("Floor"):
            group = "Boden"
        elif name.startswith("FrontWall") or name == "Lintel":
            group = "Frontwand"
        elif name.endswith(("Wall", "StoneSkirt")):
            group = "Wände"
        elif name.endswith(("Beam", "Post")) or name == "Rafter":
            group = "Balken"
        elif name.startswith(("ExitDoor", "Door")):
            group = "Tür"
        else:
            group = "Einrichtung"
        x, y, z = lua_list(spec.size)
        builder = builders[group]
        with builder.at(T(*point(lua_list(spec.position))), R("Y", -(spec.roll or 0))):
            builder.box(x, z, y, spec.color, anchor="c", tone=builder.jitter(0.035))
    # A visual floor overlay within the floor's physical box footprint.
    floor = builders["Boden"]
    for i in range(16):
        for j in range(4):
            floor.box(1.94, 7.94, 0.022, ("wood_pale", "wood_light", "wood_pale")[(i + j) % 3],
                      (-15 + 2 * i, -12 + 8 * j, -0.01), tone=floor.jitter(0.04))
    shell = collection(target, "Innenraum")
    objects = [builder.to_object(f"workshop_{name}", scene.TEXTURE_PATH, shell) for name, builder in builders.items()]
    roof_builder = MeshBuilder(seed=8)
    with roof_builder.at(T(0, 0, 12)):
        gable_roof(roof_builder, 34, 34, 10.5, "roof_purple", sag=1.0,
                   oe=1.2, og=1.2, courses=7, gable_win=None)
    roof = roof_builder.to_object("workshop_roof", scene.TEXTURE_PATH, collection(target, "Ausblendbares Dach"))
    for i, spec in enumerate(lamps):
        light(target, f"Warmlicht {i + 1}", point(lua_list(spec.position)), spec.strength * 570, 1.35, (1, 0.75, 0.47))
    return objects, roof


def entities(target, data, entries, name):
    # Arms follow the exact adjacent cells in the simulated factory. The game
    # uses the same nodes with all four ports visible for free construction.
    preview_arms = {
        (13, 11): ((1, 0), (-1, 0)),
        (9, 15): ((1, 0), (0, 1)),
        (9, 11): ((1, 0), (0, -1)),
    }
    group = collection(target, name)
    for entity in entries:
        definition = data.Machines[entity.machine]
        w, d = data.GridMath.size(definition, entity.rot)
        builder = MeshBuilder(seed=registry.stable_seed(definition.modelAssetId))
        if definition.kind == "pipe":
            _pipe_node(builder, preview_arms.get((entity.gx, entity.gz), ((0, 1), (0, -1))))
            if entity.machine == "pipe_bend":
                with builder.at(T(0, 0, 0.95)):
                    valve(builder, 0.3)
        else:
            MACHINES[definition.modelAssetId](builder)
        obj = builder.to_object(definition.modelAssetId + "_" + entity.uid, scene.TEXTURE_PATH, group)
        obj.location = (2 * entity.gx - 16 + w, 16 - 2 * entity.gz - d, 0)
        obj.rotation_euler.z = math.radians(-90 * entity.rot)
        if entity.machine == "kettle":
            light(target, "Kesselglut", obj.location + Vector((0, -0.6, 1.1)), 120, 0.65, (1, 0.48, 0.22))
            light(target, "Trankglühen", obj.location + Vector((0, 0, 3.7)), 84, 0.62, (0.55, 1, 0.4))
    return group


def configure(target, resolution):
    scene.setup_render(target, resolution, samples=48)
    target.cycles.use_denoising = False  # also render on CPU-only Blender builds without OIDN
    target.view_settings.view_transform = "AgX"
    target.render.threads_mode = "FIXED"
    target.render.threads = 8


def save_project(exterior, starter, cutaway):
    for image in bpy.data.images:
        if image.source == "FILE" and image.packed_file is None:
            image.pack()
    bpy.context.window.scene = exterior
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
    ART.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(ART / "ArcaneVillage_Workshop.blend"), compress=True)
    print(f"[workshop] Blender scenes: {', '.join(item.name for item in (exterior, starter, cutaway))}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-render", action="store_true")
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    elif Path(sys.argv[0]).resolve() == Path(__file__).resolve():
        argv = sys.argv[1:]
    else:
        argv = []
    args = parser.parse_args(argv)
    data, starter_entities, factory_entities, boxes, lamps = validate_layout()
    layout = json.loads((ROOT / "world/world_layout.json").read_text(encoding="utf-8"))
    pose = next(row["blender"] for row in layout["instances"] if row["asset"] == ASSET)
    exterior = export.new_scene()
    exterior.name = "01 - Dorfweg"
    facade = MeshBuilder(seed=registry.stable_seed("workshop_facade"))
    workshop.facade(facade)
    obj = facade.to_object("workshop_facade", scene.TEXTURE_PATH, collection(exterior, "Werkstattfassade"))
    facade_metadata(facade)
    ext_path = EXPORT / "workshop_facade.glb"
    export.export_glb([obj], str(ext_path))
    ext_doc, ext_tris = read_glb(ext_path)
    assert ext_doc["nodes"][0]["name"] == obj.name
    nearest = road_context(exterior, layout, pose, facade.bounds()[0][1])
    configure(exterior, (1440, 1100))
    scene.setup_light(exterior, sun_az=265, sun_el=34, sun_strength=3.1, sky_strength=0.7)
    cam = scene.add_camera(exterior, "Dorfweg")
    cam.data.lens = 29
    eye = (nearest.x + 20, nearest.y - 21, nearest.z + 11.4)
    scene.aim(cam, eye, (-0.4, -0.9, 17.2))

    starter = bpy.data.scenes.new("02 - Starterwerkstatt")
    bpy.context.window.scene = starter
    models, roof = interior(starter, boxes, lamps)
    int_path = EXPORT / "workshop_interior_32.glb"
    export.export_glb([*models, roof], str(int_path))
    int_doc, int_tris = read_glb(int_path)
    kettle_builder = MeshBuilder(seed=registry.stable_seed("mach_kettle"))
    MACHINES["mach_kettle"](kettle_builder)
    machine_metadata(kettle_builder)
    kettle = kettle_builder.to_object("mach_kettle", scene.TEXTURE_PATH)
    kettle_path = EXPORT / "mach_kettle.glb"
    export.export_glb([kettle], str(kettle_path))
    kettle_doc, _ = read_glb(kettle_path)
    assert kettle_doc["nodes"][0]["name"] == "mach_kettle"
    bpy.data.objects.remove(kettle, do_unlink=True)
    assert len(int_doc["meshes"]) == len(models) + 1
    entities(starter, data, starter_entities, "Startergeräte")
    configure(starter, (1440, 1000))
    starter.cycles.samples = 72
    for model in models:
        if model.name.startswith(("workshop_Frontwand", "workshop_Tür")):
            model.visible_camera = False
    threshold = MeshBuilder(seed=32)
    for i in range(16):
        threshold.box(1.94, 6, 0.18, "wood_pale", (-15 + 2 * i, 19, -0.17), tone=threshold.jitter(0.05))
    threshold.to_object("Kamera-Vorraum", scene.TEXTURE_PATH, collection(starter, "Renderkulisse"))
    light(starter, "Fensterlicht", (10, 10, 7), 750, 3.0, (1, 0.76, 0.45))
    light(starter, "Eingangsfülllicht", (0, 12, 8.5), 900, 4.0, (0.72, 0.82, 1))
    cam = scene.add_camera(starter, "Blick vom Eingang")
    cam.data.lens = 17.3
    scene.aim(cam, (2.5, 24.5, 7.4), (0.8, -0.6, 4.25))

    cutaway = bpy.data.scenes.new("03 - Fabrikausbau")
    bpy.context.window.scene = cutaway
    models, cut_roof = interior(cutaway, boxes, lamps)
    cut_roof.hide_render = True
    cut_roof.hide_set(True)
    for model in models:
        if not model.name.startswith(("workshop_Boden", "workshop_Tür")):
            model.hide_render = True
            model.hide_set(True)
    border = MeshBuilder(seed=53)
    for x, y, w, d in ((0, -16.3, 33, 0.65), (-16.3, 0, 0.65, 32), (16.3, 0, 0.65, 32), (0, 16.3, 33, 0.65)):
        border.box(w, d, 0.55, "wood_dark", (x, y, 0.0))
    border.to_object("Schnittkante", scene.TEXTURE_PATH)
    entities(cutaway, data, starter_entities, "Startergeräte")
    entities(cutaway, data, factory_entities, "Fertigungslinie")
    configure(cutaway, (1440, 1220))
    scene.setup_light(cutaway, sun_az=125, sun_el=66, sun_strength=2.3, sky_strength=0.72)
    ground = scene.ground_plane(cutaway, size=180, color="stone_light", z=-1.06)
    ground.name = "Schnittmodell-Untergrund"
    cam = scene.add_camera(cutaway, "Fabrikplan")
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 49
    scene.aim(cam, (4, 20, 55), (0, 0, 1.0))

    save_project(exterior, starter, cutaway)
    print(f"[workshop] GLB facade {ext_tris} triangles, interior {int_tris} triangles across {len(int_doc['meshes'])} meshes")
    if not args.no_render:
        for view, filename in ((exterior, "01-dorfweg.png"), (starter, "02-starterwerkstatt.png"), (cutaway, "03-fabrikausbau.png")):
            bpy.context.window.scene = view
            scene.render(view, str(PREVIEW / filename))


if __name__ == "__main__":
    main()
