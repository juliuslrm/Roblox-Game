"""Small procedural modelling kit on top of mathutils.

A MeshBuilder accumulates polygons (with palette colour + tone per corner) in
plain Python lists and converts them to one Blender mesh at the end.  Every
primitive is a closed solid whose winding is verified through its signed
volume, because Roblox culls back faces: an inverted face would be invisible
in game although Cycles previews would still look fine.

Conventions (asset space): Z up, units = Roblox studs, the asset's origin is
the point that touches the ground, the "front" of an asset looks towards -Y.
"""
import math
import random
from contextlib import contextmanager

import bpy  # noqa: F401  (the bpy wheel provides mathutils)
from mathutils import Matrix, Vector

from . import palette


# ---------------------------------------------------------------- transforms
def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def S(x, y=None, z=None):
    if y is None:
        y = z = x
    return Matrix.Diagonal((x, y, z, 1.0))


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


# ---------------------------------------------------------------- icosphere
_ICO_CACHE = {}


def _icosphere(level):
    if level in _ICO_CACHE:
        return _ICO_CACHE[level]
    t = (1 + 5 ** 0.5) / 2
    verts = [Vector(v).normalized() for v in [
        (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t),
        (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9),
             (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2),
             (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
             (8, 6, 7), (9, 8, 1)]
    for _ in range(level):
        mid = {}
        new_faces = []

        def midpoint(a, b):
            key = (min(a, b), max(a, b))
            if key not in mid:
                verts.append(((verts[a] + verts[b]) / 2).normalized())
                mid[key] = len(verts) - 1
            return mid[key]

        for a, b, c in faces:
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            new_faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = new_faces
    _ICO_CACHE[level] = (verts, faces)
    return _ICO_CACHE[level]


# ---------------------------------------------------------------- builder
class MeshBuilder:
    def __init__(self, seed=0):
        self.verts = []      # Vector
        self.faces = []      # tuple of vertex indices
        self.colors = []     # palette colour name per face
        self.smooth = []     # bool per face
        self.shades = []     # tuple of tone values (one per face corner)
        self._mstack = [Matrix.Identity(4)]
        self.rng = random.Random(seed)
        self.lights = []     # optional light anchors: dicts in asset space
        self.colliders = []  # simple collision proxies: dicts in asset space
        self.collision = None  # 'proxy' | 'mesh' | 'mesh_precise' | 'none' (None = category default)
        self.wings = []      # building volumes, used to derive box colliders
        self.winding_fixes = 0
        self.custom_normals = {}   # vertex index -> normal (only where given explicitly)

    # ---- transform stack
    @contextmanager
    def at(self, *mats):
        m = self._mstack[-1]
        for x in mats:
            m = m @ x
        self._mstack.append(m)
        try:
            yield
        finally:
            self._mstack.pop()

    @property
    def matrix(self):
        return self._mstack[-1]

    def world(self, p):
        return self._mstack[-1] @ Vector(p)

    # ---- core
    def add(self, verts, faces, color, smooth=False, grad=(0.42, 0.60), zr=None,
            tone=0.0, ftone=None, fsmooth=None, closed=False, fcolor=None, drop=(), vtone=None,
            normals=None):
        """Add polygons. verts are local to the current transform.

        grad   tone at the lowest / highest point of this part
        zr     optional (z0, z1) in asset space the gradient is measured in
        tone   constant tone offset; ftone = per-face offsets
        closed part is a closed solid -> winding is verified and auto-fixed
        drop   face indices that take part in the winding check but are not
               emitted (faces hidden against other geometry)
        """
        m = self._mstack[-1]
        wv = [m @ Vector(v) for v in verts]
        faces = [tuple(f) for f in faces]
        if closed:
            vol = 0.0
            for f in faces:
                a = wv[f[0]]
                for i in range(1, len(f) - 1):
                    vol += a.dot(wv[f[i]].cross(wv[f[i + 1]]))
            if vol < 0:
                faces = [tuple(reversed(f)) for f in faces]
                self.winding_fixes += 1
        elif m.to_3x3().determinant() < 0:
            faces = [tuple(reversed(f)) for f in faces]
        if zr is None:
            zs = [v.z for v in wv]
            zr = (min(zs), max(zs))
        span = max(zr[1] - zr[0], 1e-6)
        vshade = [lerp(grad[0], grad[1], clamp((v.z - zr[0]) / span)) + tone for v in wv]
        if vtone is not None:
            vshade = [a + b for a, b in zip(vshade, vtone)]
        base = len(self.verts)
        self.verts.extend(wv)
        if normals is not None:                    # explicit vertex normals (terrain chunks)
            self.custom_normals.update({base + i: tuple(nv) for i, nv in enumerate(normals)})
        for i, f in enumerate(faces):
            if i in drop:
                continue
            ft = ftone[i] if ftone else 0.0
            self.faces.append(tuple(base + j for j in f))
            self.colors.append(fcolor[i] if fcolor else color)
            self.smooth.append(fsmooth[i] if fsmooth else smooth)
            self.shades.append(tuple(vshade[j] + ft for j in f))
        return base

    def deform(self, fn, start=0):
        """Apply fn(Vector) -> Vector to all vertices from index `start`."""
        for i in range(start, len(self.verts)):
            self.verts[i] = Vector(fn(self.verts[i]))

    def jitter(self, amount):
        return self.rng.uniform(-amount, amount)

    # ---- primitives
    _BOX_FACES = {"-z": (0, 3, 2, 1), "+z": (4, 5, 6, 7), "-y": (0, 1, 5, 4),
                  "+x": (1, 2, 6, 5), "+y": (2, 3, 7, 6), "-x": (3, 0, 4, 7)}

    def box(self, sx, sy, sz, color, pos=(0, 0, 0), anchor="b", taper=1.0, skip=(), **kw):
        """Box with base centre (anchor 'b') or centre (anchor 'c') at pos.
        taper scales the top face (number or (tx, ty)); skip omits faces
        ('-y', '+z', ...) that are hidden against other geometry."""
        tx, ty = (taper, taper) if isinstance(taper, (int, float)) else taper
        hx, hy = sx / 2, sy / 2
        x, y, z = pos
        z0 = z if anchor == "b" else z - sz / 2
        z1 = z0 + sz
        verts = [(x - hx, y - hy, z0), (x + hx, y - hy, z0), (x + hx, y + hy, z0), (x - hx, y + hy, z0),
                 (x - hx * tx, y - hy * ty, z1), (x + hx * tx, y - hy * ty, z1),
                 (x + hx * tx, y + hy * ty, z1), (x - hx * tx, y + hy * ty, z1)]
        faces = [f for k, f in self._BOX_FACES.items() if k not in skip]
        return self.add(verts, faces, color, closed=not skip, **kw)

    def beam(self, p0, p1, w, d, color, up=(0, 0, 1), ext=0.0, **kw):
        """Box running from p0 to p1, cross-section w (sideways) x d (along up)."""
        p0, p1 = Vector(p0), Vector(p1)
        axis = p1 - p0
        length = axis.length
        if length < 1e-6:
            return None
        zax = axis / length
        upv = Vector(up)
        xax = upv.cross(zax)
        if xax.length < 1e-4:
            xax = Vector((1, 0, 0)).cross(zax)
            if xax.length < 1e-4:
                xax = Vector((0, 1, 0)).cross(zax)
        xax.normalize()
        yax = zax.cross(xax)
        m = Matrix((
            (xax.x, yax.x, zax.x, p0.x),
            (xax.y, yax.y, zax.y, p0.y),
            (xax.z, yax.z, zax.z, p0.z),
            (0, 0, 0, 1)))
        with self.at(m):
            return self.box(w, d, length + 2 * ext, color, pos=(0, 0, -ext), **kw)

    def loft(self, rings, color, cap0=True, cap1=True, closed_ring=True, smooth=False,
             hide0=False, hide1=False, **kw):
        """Connect consecutive rings (lists of points with equal length).
        hide0 / hide1 drop the start / end cap but keep the winding check."""
        n = len(rings[0])
        verts = [p for r in rings for p in r]
        faces, fsmooth = [], []
        count = n if closed_ring else n - 1
        for j in range(len(rings) - 1):
            for i in range(count):
                a = j * n + i
                b = j * n + (i + 1) % n
                faces.append((a, b, b + n, a + n))
                fsmooth.append(smooth)
        drop = set()
        if cap0 and closed_ring:
            if hide0:
                drop.add(len(faces))
            faces.append(tuple(reversed(range(n))))
            fsmooth.append(False)
        if cap1 and closed_ring:
            if hide1:
                drop.add(len(faces))
            base = (len(rings) - 1) * n
            faces.append(tuple(range(base, base + n)))
            fsmooth.append(False)
        closed = closed_ring and cap0 and cap1
        return self.add(verts, faces, color, fsmooth=fsmooth, closed=closed, drop=drop, **kw)

    def ring_loft(self, rings, color, smooth=False, **kw):
        """Torus-like solid: rings are connected cyclically (last -> first)."""
        n = len(rings[0])
        m = len(rings)
        verts = [p for r in rings for p in r]
        faces = []
        for j in range(m):
            jn = (j + 1) % m
            for i in range(n):
                a = j * n + i
                b = j * n + (i + 1) % n
                faces.append((a, b, jn * n + (i + 1) % n, jn * n + i))
        return self.add(verts, faces, color, smooth=smooth, closed=True, **kw)

    def prism(self, poly, y0, y1, color, **kw):
        """Polygon given in the XZ plane, extruded along Y from y0 to y1."""
        rings = [[(x, y0, z) for x, z in poly], [(x, y1, z) for x, z in poly]]
        return self.loft(rings, color, **kw)

    def slab(self, poly, z0, z1, color, **kw):
        """Polygon given in the XY plane, extruded along Z from z0 to z1."""
        rings = [[(x, y, z0) for x, y in poly], [(x, y, z1) for x, y in poly]]
        return self.loft(rings, color, **kw)

    def cyl(self, r0, r1, h, color, pos=(0, 0, 0), segs=8, smooth=True, phase=0.0, **kw):
        x, y, z = pos
        ring = lambda r, zz: [(x + r * math.cos(phase + 2 * math.pi * i / segs),
                               y + r * math.sin(phase + 2 * math.pi * i / segs), zz)
                              for i in range(segs)]
        return self.loft([ring(r0, z), ring(r1, z + h)], color, smooth=smooth, **kw)

    def lathe(self, profile, color, segs=8, pos=(0, 0, 0), smooth=True, phase=0.0, **kw):
        """Revolve profile [(r, z), ...] around Z. Ends with r == 0 become tips."""
        x, y, z = pos
        verts, rows = [], []
        for r, pz in profile:
            if r < 1e-5:
                verts.append((x, y, z + pz))
                rows.append([len(verts) - 1])
            else:
                row = []
                for i in range(segs):
                    a = phase + 2 * math.pi * i / segs
                    verts.append((x + r * math.cos(a), y + r * math.sin(a), z + pz))
                    row.append(len(verts) - 1)
                rows.append(row)
        faces, fsmooth = [], []
        for j in range(len(rows) - 1):
            a, b = rows[j], rows[j + 1]
            for i in range(segs):
                i2 = (i + 1) % segs
                if len(a) == 1 and len(b) == 1:
                    continue
                if len(a) == 1:
                    faces.append((a[0], b[i2], b[i]))
                elif len(b) == 1:
                    faces.append((a[i], a[i2], b[0]))
                else:
                    faces.append((a[i], a[i2], b[i2], b[i]))
                fsmooth.append(smooth)
        if len(rows[0]) > 1:
            faces.append(tuple(reversed(rows[0])))
            fsmooth.append(False)
        if len(rows[-1]) > 1:
            faces.append(tuple(rows[-1]))
            fsmooth.append(False)
        return self.add(verts, faces, color, fsmooth=fsmooth, closed=True, **kw)

    def blob(self, radius, color, pos=(0, 0, 0), scale=(1, 1, 1), level=1, noise=0.18,
             smooth=False, **kw):
        """Displaced icosphere: foliage clumps, rocks, bushes."""
        uverts, ufaces = _icosphere(level)
        rng = self.rng
        x, y, z = pos
        verts = []
        for v in uverts:
            k = radius * (1 + rng.uniform(-noise, noise))
            verts.append((x + v.x * k * scale[0], y + v.y * k * scale[1], z + v.z * k * scale[2]))
        return self.add(verts, ufaces, color, smooth=smooth, closed=True, **kw)

    def sheet(self, rows, color, up=(0, 0, 1), close_u=False, **kw):
        """Open surface from a grid of points (rows of equal length), wound so
        that it faces `up`. Face order: for each row pair, for each column.
        close_u connects the last column back to the first."""
        n = len(rows[0])
        verts = [p for r in rows for p in r]
        faces = []
        cols = n if close_u else n - 1
        for j in range(len(rows) - 1):
            for i in range(cols):
                a, b = j * n + i, j * n + (i + 1) % n
                faces.append((a, b, b + n, a + n))
        nrm = Vector((0, 0, 0))
        for f in faces[:: max(1, len(faces) // 16)]:
            p = [Vector(verts[k]) for k in f]
            nrm += (p[1] - p[0]).cross(p[2] - p[1])
        if nrm.dot(Vector(up)) < 0:
            faces = [tuple(reversed(f)) for f in faces]
        return self.add(verts, faces, color, **kw)

    def quad(self, p0, p1, p2, p3, color, double=False, facing=None, **kw):
        return self.poly([p0, p1, p2, p3], color, double=double, facing=facing, **kw)

    def poly(self, pts, color, double=False, facing=None, **kw):
        """Single planar polygon. `facing` (local direction) fixes the visible
        side; double=True emits both sides."""
        n = len(pts)
        idx = list(range(n))
        p = [Vector(q) for q in pts]
        nrm = Vector((0, 0, 0))
        for i in range(1, n - 1):
            nrm += (p[i] - p[0]).cross(p[i + 1] - p[0])
        if facing is not None and nrm.dot(Vector(facing)) < 0:
            idx.reverse()
            nrm = -nrm
        if not double:
            return self.add(pts, [tuple(idx)], color, **kw)
        # Double sided = a very thin closed solid.  (Two faces on the same
        # vertices would be removed as duplicates by mesh.validate(), and
        # coincident faces would z-fight in engines that do not cull.)
        off = nrm.normalized() * 0.015
        verts = [q + off for q in p] + [q - off for q in p]
        faces = [tuple(idx), tuple(n + i for i in reversed(idx))]
        for k in range(n):
            a, b = idx[k], idx[(k + 1) % n]
            faces.append((a, n + a, n + b, b))
        return self.add(verts, faces, color, closed=True, **kw)

    def merge(self, other, *mats):
        """Append another builder's geometry, transformed by mats."""
        m = self._mstack[-1]
        for x in mats:
            m = m @ x
        flip = m.to_3x3().determinant() < 0
        base = len(self.verts)
        self.verts.extend(m @ v for v in other.verts)
        for f, c, s, sh in zip(other.faces, other.colors, other.smooth, other.shades):
            f2 = tuple(base + i for i in f)
            if flip:
                f2, sh = tuple(reversed(f2)), tuple(reversed(sh))
            self.faces.append(f2)
            self.colors.append(c)
            self.smooth.append(s)
            self.shades.append(sh)
        for lt in other.lights:
            lt2 = dict(lt)
            lt2["position"] = tuple(m @ Vector(lt["position"]))
            self.lights.append(lt2)

    def light(self, pos, color=(1.0, 0.82, 0.55), brightness=1.0, range_=24.0):
        """Register a light anchor (exported to the layout for Roblox PointLights)."""
        self.lights.append({"position": tuple(self.world(pos)), "color": color,
                            "brightness": brightness, "range": range_})

    def collider_box(self, center, size, rot_z=0.0):
        """Axis-aligned (after rot_z around Z) collision box in local space."""
        m = self._mstack[-1]
        c = m @ Vector(center)
        yaw = math.degrees(math.atan2(m[1][0], m[0][0])) + rot_z
        self.colliders.append({"shape": "box", "center": tuple(c), "size": tuple(size), "rot_z": yaw})

    def collider_cyl(self, center, radius, height):
        """Upright collision cylinder; center = middle of the cylinder."""
        c = self._mstack[-1] @ Vector(center)
        self.colliders.append({"shape": "cylinder", "center": tuple(c), "radius": radius, "height": height})

    # ---- queries
    def tri_count(self):
        return sum(len(f) - 2 for f in self.faces)

    def bounds(self):
        xs = [v.x for v in self.verts]
        ys = [v.y for v in self.verts]
        zs = [v.z for v in self.verts]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    # ---- output
    def to_mesh(self, name, texture_path):
        import bpy
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([tuple(v) for v in self.verts], [], self.faces)
        uv_layer = mesh.uv_layers.new(name="UVMap")
        flat = []
        for color, shades in zip(self.colors, self.shades):
            for s in shades:
                flat.extend(palette.uv(color, s))
        uv_layer.data.foreach_set("uv", flat)
        mesh.polygons.foreach_set("use_smooth", self.smooth)
        mesh.materials.append(palette.get_material(texture_path))
        mesh.validate(verbose=False)
        mesh.update()
        if self.custom_normals:
            fallback = [tuple(v.normal) for v in mesh.vertices]
            mesh.normals_split_custom_set_from_vertices(
                [self.custom_normals.get(i, fallback[i]) for i in range(len(mesh.vertices))])
        return mesh

    def to_object(self, name, texture_path, collection=None):
        import bpy
        obj = bpy.data.objects.new(name, self.to_mesh(name, texture_path))
        (collection or bpy.context.scene.collection).objects.link(obj)
        return obj
