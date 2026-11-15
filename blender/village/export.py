"""Export helpers: glTF binary, FBX and .blend sources."""
import os

import bpy

from . import coords
from . import scene as sc


def _collider_to_roblox(c):
    out = {"shape": c["shape"], "center": coords.to_roblox(c["center"])}
    if c["shape"] == "box":
        out["size"] = coords.size_to_roblox(c["size"])
        out["yaw_deg"] = round(c["rot_z"], 3)
    else:
        out["radius"] = round(c["radius"], 3)
        out["height"] = round(c["height"], 3)
    return out


def describe(mb, category, blend, glb, collision=None):
    """Manifest entry of a built asset (bounds in both coordinate systems,
    collision proxies and light anchors already converted to Roblox space)."""
    bmin, bmax = mb.bounds()
    size = [b - a for a, b in zip(bmin, bmax)]
    small = category == "nature" and max(size) < 6.5
    return {
        "category": category,
        "blend": blend,
        "glb": glb,
        "triangles": mb.tri_count(),
        "vertices": len(mb.verts),
        "collision": collision or mb.collision,
        "cast_shadow": not (small or category == "terrain"),
        "bounds_blender": {"min": [round(v, 4) for v in bmin], "max": [round(v, 4) for v in bmax]},
        "bounds_roblox": coords.bounds_to_roblox(bmin, bmax),
        "colliders": [_collider_to_roblox(c) for c in mb.colliders],
        "lights": [{"position": coords.to_roblox(lt["position"]),
                    "color": [round(v, 3) for v in lt["color"]],
                    "brightness": lt["brightness"], "range": lt["range"]} for lt in mb.lights],
    }


def _select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def export_glb(objs, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    _select_only(objs)
    bpy.ops.export_scene.gltf(
        filepath=filepath, export_format="GLB", use_selection=True, export_yup=True,
        export_apply=True, export_texcoords=True, export_normals=True, export_materials="EXPORT",
        export_cameras=False, export_lights=False, export_animations=False, export_extras=False)


def export_fbx(objs, filepath):
    """FBX for the Roblox importer. Blender writes FBX in centimetres with a
    unit factor of 100, global_scale 0.01 compensates so that 1 unit = 1 stud."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    _select_only(objs)
    bpy.ops.export_scene.fbx(
        filepath=filepath, use_selection=True, object_types={"MESH"}, global_scale=0.01,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
        bake_space_transform=True, mesh_smooth_type="FACE", use_mesh_modifiers=True,
        add_leaf_bones=False, bake_anim=False, path_mode="COPY", embed_textures=True)


def save_blend(filepath):
    """Save the current file; the palette texture stays an external, relative
    reference so that all sources share one texture file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=True, relative_remap=True)
    for img in bpy.data.images:
        if img.filepath and not img.filepath.startswith("//"):
            img.filepath = bpy.path.relpath(img.filepath)
    bpy.ops.wm.save_mainfile(compress=True)
    backup = filepath + "1"
    if os.path.exists(backup):
        os.remove(backup)


def new_scene():
    scene = sc.reset()
    scene.unit_settings.system = "NONE"
    return scene
