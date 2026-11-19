"""The Reom character of the CharMorph database (CC-BY, see docs/CREDITS.md), loaded as data only.

The database lives in assets/thirdparty/charmorph-db (scripts/fetch_charmorph_db.sh).  Nothing of the
CharMorph add-on is executed: the mesh and its shader node groups come from char.blend, morphs and
vertex groups from .npz / .npy arrays, textures from the texture folders.  Units: metres, the figure
faces -Y, Z is up.

    obj = load()                         # mesh object with materials and textures
    apply_morphs(obj, {"Race_Blackman": 0.9, ...})
    set_skin(obj, melanin=0.9)
"""
import os
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DB = Path(os.environ.get("CHARMORPH_DB", ROOT / "assets/thirdparty/charmorph-db"))
CHAR = DB / "characters/reom"
# material slots of the mesh, in the order of the character's config.yaml
MATERIALS = ["Sclera_Cornea", "Iris", "Pupil", "Face", "Torso", "Arms", "Legs", "Mouth", "Tongue", "Gums", "Teeth"]
NONCOLOR = ("ChannelPack", "Height", "Mask", "Opacity")


def _texdir(path):
    out = {}
    if path.is_dir():
        for f in sorted(path.iterdir()):
            if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
                out.setdefault(f.stem, f)
    return out


def _link_textures(obj, texture_set="4K"):
    """An image node named or labelled tex_<name> gets the texture <name> (as CharMorph assigns them):
    the character's texture set first, then the character folder, then the shared folder."""
    texmap = _texdir(DB / "textures")
    texmap.update(_texdir(CHAR / "textures"))
    texmap.update(_texdir(CHAR / "textures" / texture_set))
    seen, missing = set(), set()

    def scan(nodes):
        for node in nodes:
            if node.type == "GROUP" and node.node_tree and node.node_tree.name not in seen:
                seen.add(node.node_tree.name)
                scan(node.node_tree.nodes)
            if node.type != "TEX_IMAGE":
                continue
            for name in (node.name, node.label):
                if name.startswith("tex_"):
                    f = texmap.get(name[4:])
                    if f is None:
                        missing.add(name)
                        break
                    img = bpy.data.images.load(str(f), check_existing=True)
                    if any(k in name for k in NONCOLOR):
                        img.colorspace_settings.name = "Non-Color"
                    node.image = img
                    break
    for m in obj.data.materials:
        if m and m.node_tree:
            scan(m.node_tree.nodes)
    return missing


def load(name="Lio"):
    if not (CHAR / "char.blend").exists():
        raise FileNotFoundError(f"{CHAR}/char.blend missing - run scripts/fetch_charmorph_db.sh")
    with bpy.data.libraries.load(str(CHAR / "char.blend"), link=False) as (src, dst):
        dst.objects = ["cm_reom"]
        dst.materials = [m for m in src.materials if m in MATERIALS]
    obj = bpy.data.objects["cm_reom"]
    obj.name = name
    bpy.context.scene.collection.objects.link(obj)
    for i, m in enumerate(MATERIALS):
        obj.data.materials[i] = bpy.data.materials[m]
    missing = _link_textures(obj)
    if missing:
        raise RuntimeError(f"Reom textures not found: {sorted(missing)}")
    obj.data.shade_smooth()
    return obj


def morph(name):
    """(indices or None for all vertices, deltas) of a level-2 morph."""
    base = CHAR / "morphs/L2" / name
    if base.with_suffix(".npz").exists():
        z = np.load(base.with_suffix(".npz"), allow_pickle=False)
        return z["idx"], z["delta"].astype(np.float64)
    return None, np.load(base.with_suffix(".npy"), allow_pickle=False).astype(np.float64)


def expression(name):
    """(indices, deltas) of a level-3 morph: the 52 ARKit face shapes (eyeBlinkLeft, jawOpen, ...)."""
    z = np.load(CHAR / "morphs/L3" / f"{name}.npz", allow_pickle=False)
    return z["idx"], z["delta"].astype(np.float64)


def apply_morphs(obj, values):
    me = obj.data
    V = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    for name, w in values.items():
        idx, d = morph(name)
        if idx is None:
            V += w * d
        else:
            V[idx] += w * d
    me.vertices.foreach_set("co", V.ravel())
    me.update()


def set_skin(obj, melanin=None, tone=None, age=None, melanin_blend=None, melanin_fraction=None,
             hemoglobin=None, lip_strength=None, stubble=None, scalp_tan_lines=None):
    """Skin shader settings: melanin mixes the light and the dark skin maps (CharMorphSettings);
    melanin_blend / melanin_fraction drive the skin look-up table of the face, torso, arm and leg
    shaders (defaults 0 / 0.2 = light skin); hemoglobin = redness (default 0.125), lip_strength = lip
    tint (1), stubble = five o'clock shadow of the face (0)."""
    g = bpy.data.node_groups.get("CharMorphSettings")
    for key, val in (("Melanin", melanin), ("Tone", tone), ("Age", age)):
        if val is not None and g is not None and key in g.nodes:
            g.nodes[key].outputs[0].default_value = val
    for m in obj.data.materials:
        if not m or not m.node_tree:
            continue
        for n in m.node_tree.nodes:
            if n.type == "GROUP" and n.node_tree and n.node_tree.name.endswith("Shader"):
                for key, val in (("Melanin Blend", melanin_blend), ("Melanin Fraction", melanin_fraction),
                                 ("Hemoglobin Fraction", hemoglobin), ("Lip Strength", lip_strength),
                                 ("Five O Clock Shadow", stubble), ("ScalpTanLines", scalp_tan_lines)):
                    if val is not None and key in n.inputs and not n.inputs[key].is_linked:
                        n.inputs[key].default_value = val


def refresh_normals(obj, subdivide=1):
    """Drops the stored custom normals of the base shape (they no longer fit after morphing) and adds
    a subdivision modifier for close renders (levels: render)."""
    me = obj.data
    if "custom_normal" in me.attributes:
        me.attributes.remove(me.attributes["custom_normal"])
    me.shade_smooth()
    if subdivide:
        mod = obj.modifiers.new("Subdivision", "SUBSURF")
        mod.levels, mod.render_levels = subdivide, subdivide


def vertex_groups(kind="rigify"):
    """{group name: (indices, weights)} of the Rigify deform bones (weights/<kind>.npz)."""
    z = np.load(CHAR / "weights" / f"{kind}.npz", allow_pickle=False)
    names = [n.decode("utf-8") for n in bytes(z["names"]).split(b"\0")]
    out, i = {}, 0
    for name, cnt in zip(names, z["cnt"]):
        out[name] = (z["idx"][i:i + int(cnt)], z["weights"][i:i + int(cnt)])
        i += int(cnt)
    return out


def tint_lips(color=(0.62, 0.45, 0.45), strength=0.85):
    """The skin maps give every skin tone the same light pink lips.  Multiplies the face base colour by
    `color` inside Reom's lip mask (tex_ReomLipMask), so darker skin gets darker lips."""
    g = bpy.data.node_groups.get("FaceShader")
    if g is None or "LipTint" in g.nodes:
        return
    bsdf = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED")
    src = bsdf.inputs["Base Color"].links[0].from_socket
    mask = g.nodes["tex_ReomLipMask"]
    fac = g.nodes.new("ShaderNodeMath")
    fac.operation, fac.inputs[1].default_value = "MULTIPLY", strength
    mix = g.nodes.new("ShaderNodeMix")
    mix.name, mix.data_type, mix.blend_type = "LipTint", "RGBA", "MULTIPLY"
    mix.inputs["B"].default_value = (*color, 1.0)
    g.links.new(mask.outputs["Color"], fac.inputs[0])
    g.links.new(fac.outputs[0], mix.inputs["Factor"])
    g.links.new(src, mix.inputs["A"])
    g.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
