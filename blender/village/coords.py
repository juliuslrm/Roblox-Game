"""Blender <-> Roblox coordinate conversion.

Blender: right-handed, Z up.   Roblox: right-handed, Y up.
The glTF exporter (+Y up) maps a Blender point (x, y, z) to (x, z, -y); the
Roblox importer keeps glTF axes.  This mapping is a pure rotation, so a
rotation of angle a around Blender's Z axis is a rotation of the same angle a
around Roblox's Y axis.  1 Blender unit = 1 stud.
"""


def to_roblox(p):
    return [round(p[0], 4), round(p[2], 4), round(-p[1], 4)]


def size_to_roblox(s):
    return [round(abs(s[0]), 4), round(abs(s[2]), 4), round(abs(s[1]), 4)]


def bounds_to_roblox(bmin, bmax):
    """Blender AABB -> Roblox AABB (min, max, size, center)."""
    rmin = [bmin[0], bmin[2], -bmax[1]]
    rmax = [bmax[0], bmax[2], -bmin[1]]
    return {
        "min": [round(v, 4) for v in rmin],
        "max": [round(v, 4) for v in rmax],
        "size": [round(b - a, 4) for a, b in zip(rmin, rmax)],
        "center": [round((a + b) / 2, 4) for a, b in zip(rmin, rmax)],
    }
