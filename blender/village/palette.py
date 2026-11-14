"""Shared colour palette for every asset of the village.

All assets use ONE material and ONE small texture. Every palette colour owns a
vertical strip in that texture: the strip is a gradient from a cool shadow tone
(v = 0) over the base colour (v = 0.5) to a warm highlight (v = 1).  Geometry
picks a colour by its U coordinate and a tone by its V coordinate, which gives
hand-painted looking gradients without any per-asset textures.  This is cheap
on mobile (one 1024x64 texture for the whole world) and survives the Roblox
importer, which supports exactly one texture per MeshPart.
"""
import os
import struct
import zlib

# name -> sRGB hex. Order defines the column index; append only, never reorder,
# otherwise already exported assets would point to wrong columns.
COLORS = [
    # plaster / walls
    ("plaster_cream", "EBDDBE"), ("plaster_white", "F1EBDD"), ("plaster_yellow", "E8C97A"),
    ("plaster_rose", "DDA98F"), ("plaster_sage", "B9C4A0"), ("plaster_blue", "A9BFCB"),
    ("plaster_peach", "E9B98A"),
    # timber
    ("wood_dark", "5B3A26"), ("wood_mid", "86573A"), ("wood_light", "B58556"),
    ("wood_pale", "D2AE7C"), ("wood_red", "7A3B2A"), ("wood_grey", "8A7F73"),
    # stone / masonry
    ("stone_grey", "9A968C"), ("stone_dark", "6E6A66"), ("stone_warm", "B4A58C"),
    ("stone_light", "C9C2B2"), ("stone_moss", "7F8B6A"), ("brick", "A6573F"),
    # roofs
    ("roof_red", "B5482F"), ("roof_orange", "CE7A3B"), ("roof_brown", "7B4A33"),
    ("roof_slate", "56637A"), ("roof_teal", "3F7F7A"), ("roof_purple", "6F4E7C"),
    ("roof_green", "5E7F4A"), ("thatch", "C9A85A"), ("thatch_dark", "A6843F"),
    # metal / glass
    ("iron", "3E4046"), ("brass", "C99A3C"), ("glass_blue", "35506B"),
    ("glass_lit", "FFD27A"), ("glass_light", "7FB2C9"),
    # fabric
    ("cloth_red", "C1433B"), ("cloth_blue", "3D6FA5"), ("cloth_yellow", "E8B93C"),
    ("cloth_white", "EFE9DC"), ("cloth_green", "4F8A55"),
    # foliage / ground
    ("leaf_green", "5FA343"), ("leaf_dark", "3F7D3A"), ("leaf_lime", "8DBB45"),
    ("leaf_teal", "3F8A6A"), ("leaf_autumn", "D98A2B"), ("leaf_pink", "E9A1B5"),
    ("pine", "2F6B4F"), ("bark", "6B4A35"), ("bark_birch", "E3DED2"),
    ("grass", "7DB551"), ("grass_dark", "5E9A45"), ("grass_dry", "A9B85A"),
    ("dirt", "9A7650"), ("dirt_dark", "7A5A3C"), ("sand", "D9C48E"),
    ("cobble", "A39A8C"), ("cobble_dark", "857C70"), ("rock", "8E8F92"),
    ("rock_dark", "6B6D73"), ("water", "4FA3C7"), ("water_deep", "2F7FA8"),
    # flowers / misc
    ("flower_red", "D9443F"), ("flower_yellow", "F2C83A"), ("flower_white", "F4F1E8"),
    ("flower_purple", "9A62C4"), ("flower_blue", "5A8FDD"),
]

N_COLUMNS = 64          # fixed grid; unused columns stay black
COLUMN_PX = 16
TEX_W = N_COLUMNS * COLUMN_PX   # 1024
TEX_H = 64
TEXTURE_NAME = "village_palette.png"
MATERIAL_NAME = "VillagePalette"

assert len(COLORS) <= N_COLUMNS, "palette is full"
INDEX = {name: i for i, (name, _) in enumerate(COLORS)}


def _hex_to_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


RGB = {name: _hex_to_rgb(h) for name, h in COLORS}


def tone(rgb, t):
    """Tone curve of one palette column. t in [0,1]; 0.5 returns rgb itself."""
    if t < 0.5:
        k = t / 0.5
        dark = (rgb[0] * 0.46, rgb[1] * 0.47, rgb[2] * 0.62)   # cool shadow
        return tuple(d + (c - d) * k for c, d in zip(rgb, dark))
    k = (t - 0.5) / 0.5
    light = (rgb[0] + (1 - rgb[0]) * 0.42, rgb[1] + (1 - rgb[1]) * 0.36,
             rgb[2] + (1 - rgb[2]) * 0.16)                      # warm highlight
    return tuple(c + (l - c) * k for c, l in zip(rgb, light))


def uv(color, shade=0.5):
    """UV for a palette colour. shade 0 = shadow, 0.5 = base, 1 = highlight."""
    try:
        col = INDEX[color]
    except KeyError:
        raise KeyError(f"unknown palette colour '{color}'") from None
    return ((col + 0.5) / N_COLUMNS, min(0.97, max(0.03, shade)))


def write_texture(path):
    """Write the palette PNG (pure Python, no Pillow needed)."""
    rows = []
    for y in range(TEX_H):                     # PNG row 0 = top = highlight
        t = 1.0 - (y + 0.5) / TEX_H
        row = bytearray([0])                   # filter type 0
        for col in range(N_COLUMNS):
            if col < len(COLORS):
                r, g, b = tone(RGB[COLORS[col][0]], t)
            else:
                r = g = b = 0.0
            px = bytes((round(r * 255), round(g * 255), round(b * 255)))
            row += px * COLUMN_PX
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", TEX_W, TEX_H, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(png)
    return path


def get_material(texture_path):
    """Return the single shared Blender material (created on first use)."""
    import bpy
    mat = bpy.data.materials.get(MATERIAL_NAME)
    if mat is not None:
        return mat
    img = bpy.data.images.load(texture_path, check_existing=True)
    img.name = TEXTURE_NAME
    mat = bpy.data.materials.new(MATERIAL_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    tex.location = (-320, 300)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat
