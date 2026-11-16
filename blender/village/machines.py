"""Gameplay assets: machines, storage and logistics parts of the workshop.

These are the centrepiece of the game, so they carry far more detail than the
village assets: individual planks and stones, rivets, iron bands, gears, pipes
with flanges, valves, gauges and tools.  Every machine also shows where things
go in and out (same positions as the ports in roblox/gameplay/shared/Machines.lua):

    solid input   back  (+Y)  wooden funnel with brass rim
    solid output  front (-Y)  chute with a tray
    liquid input  left  (-X)  pipe stub with a blue ring
    liquid output right (+X)  pipe stub with an orange ring

Separate from the 91 village assets (own registry, own build script).  Ids match
`modelAssetId` in Machines.lua.  Studs, origin = centre of the footprint on the
floor, front = -Y (Roblox +Z).  Footprint = grid cells x 2 studs.
"""
import math

from mathutils import Matrix, Vector

from .meshkit import T, R, S

TAU = 2 * math.pi


# ====================================================================== detail kit
def tube(mb, p0, p1, r, color, segs=6, flanges=False, **kw):
    """Round pipe between two points, optionally with a flange ring at both ends."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    length = axis.length
    if length < 1e-4:
        return
    z = axis / length
    x = Vector((0, 0, 1)).cross(z)
    if x.length < 1e-3:
        x = Vector((1, 0, 0))
    x.normalize()
    y = z.cross(x)
    m = Matrix(((x.x, y.x, z.x, p0.x), (x.y, y.y, z.y, p0.y), (x.z, y.z, z.z, p0.z), (0, 0, 0, 1)))
    with mb.at(m):
        mb.cyl(r, r, length, color, segs=segs, **kw)
        if flanges:
            mb.cyl(r * 1.45, r * 1.45, 0.14, "iron", pos=(0, 0, 0.02), segs=segs, smooth=False)
            mb.cyl(r * 1.45, r * 1.45, 0.14, "iron", pos=(0, 0, length - 0.16), segs=segs, smooth=False)


def pipe_run(mb, pts, r, color="brass", segs=6):
    """Pipe through several points with ball joints at the bends."""
    for a, b in zip(pts[:-1], pts[1:]):
        tube(mb, a, b, r, color, segs=segs)
    for p in pts[1:-1]:
        mb.blob(r * 1.35, color, pos=p, level=0, noise=0.0)


def rivets(mb, r, z, n, color="iron", size=0.11, phase=0.0, pos=(0, 0)):
    for k in range(n):
        a = phase + TAU * k / n
        mb.box(size, size, size, color, pos=(pos[0] + r * math.cos(a), pos[1] + r * math.sin(a), z), anchor="c")


def band(mb, r, z, h=0.22, color="iron", segs=10, pos=(0, 0, 0), bolts=0):
    mb.lathe([(r, z), (r, z + h)], color, segs=segs, smooth=False, pos=pos)
    if bolts:
        rivets(mb, r + 0.03, z + h / 2, bolts, "brass", 0.1, pos=(pos[0], pos[1]))


def gear(mb, r, thick, color="brass", teeth=8, hub="iron"):
    """Gear lying in the local XY plane, centred at the origin."""
    mb.cyl(r * 0.82, r * 0.82, thick, color, pos=(0, 0, -thick / 2), segs=teeth * 2, smooth=False)
    for k in range(teeth):
        with mb.at(R("Z", 360.0 * k / teeth)):
            mb.box(r * 0.3, r * 0.26, thick * 0.9, color, pos=(r * 0.9, 0, -thick * 0.45), taper=(0.7, 0.8))
    mb.cyl(r * 0.28, r * 0.28, thick * 1.5, hub, pos=(0, 0, -thick * 0.75), segs=6, smooth=False)


def valve(mb, r=0.42, color="cloth_red"):
    """Hand wheel in the local XY plane."""
    n = 8
    for k in range(n):
        a0, a1 = TAU * k / n, TAU * (k + 1) / n
        mb.beam((r * math.cos(a0), r * math.sin(a0), 0), (r * math.cos(a1), r * math.sin(a1), 0), 0.1, 0.1, color, up=(0, 0, 1))
    for k in range(4):
        a = TAU * k / 4
        mb.beam((0, 0, 0), (r * math.cos(a), r * math.sin(a), 0), 0.08, 0.08, color, up=(0, 0, 1))
    mb.cyl(0.1, 0.1, 0.3, "iron", pos=(0, 0, -0.25), segs=5)


def gauge(mb, r=0.36):
    """Pressure gauge facing local -Y, centred at the origin."""
    with mb.at(R("X", 90)):
        mb.cyl(r, r, 0.14, "brass", pos=(0, 0, -0.02), segs=10, smooth=False)
        mb.cyl(r * 0.78, r * 0.78, 0.04, "plaster_white", pos=(0, 0, 0.12), segs=10, smooth=False, grad=(0.55, 0.7))
        mb.beam((0, 0, 0.17), (r * 0.45, r * 0.5, 0.17), 0.06, 0.03, "cloth_red", up=(0, 0, 1))


def bottle(mb, x, y, z, color="glass_blue", s=1.0, cork=True):
    mb.lathe([(0.0, 0.0), (0.3 * s, 0.08 * s), (0.32 * s, 0.6 * s), (0.13 * s, 0.82 * s), (0.13 * s, 1.05 * s)], color, segs=6,
             pos=(x, y, z), smooth=False, grad=(0.35, 0.9))
    if cork:
        mb.cyl(0.11 * s, 0.09 * s, 0.16 * s, "wood_pale", pos=(x, y, z + 1.03 * s), segs=5)


def flask(mb, x, y, z, color="glass_light", s=1.0, liquid=None):
    mb.lathe([(0.0, 0.0), (0.55 * s, 0.15 * s), (0.6 * s, 0.55 * s), (0.18 * s, 1.15 * s), (0.18 * s, 1.6 * s), (0.24 * s, 1.66 * s)],
             color, segs=8, pos=(x, y, z), smooth=False, grad=(0.35, 0.92))
    if liquid:
        mb.lathe([(0.0, 0.03 * s), (0.5 * s, 0.16 * s), (0.54 * s, 0.5 * s), (0.0, 0.52 * s)], liquid, segs=8, pos=(x, y, z + 0.01),
                 smooth=False, grad=(0.45, 0.85))


def planks(mb, w, d, z, color="wood_light", n=None, thick=0.3, gap=0.05):
    """Table top / deck made of single boards running along X."""
    n = n or max(2, round(d / 0.9))
    pw = d / n
    for i in range(n):
        y = -d / 2 + pw * (i + 0.5)
        mb.box(w + mb.jitter(0.08), pw - gap, thick, color, pos=(mb.jitter(0.03), y, z), tone=mb.jitter(0.07))


def stone_plinth(mb, w, d, h=0.5, color="stone_grey"):
    """Paved base: a slab with a ring of individual edge stones."""
    mb.box(w - 0.5, d - 0.5, h, "stone_dark", tone=-0.05)
    nx, ny = max(2, round(w / 1.3)), max(2, round(d / 1.3))
    sx, sy = (w - 0.2) / nx, (d - 0.2) / ny
    for i in range(nx):
        for j in range(ny):
            if i in (0, nx - 1) or j in (0, ny - 1) or (i + j) % 2 == 0:
                mb.box(sx - 0.1, sy - 0.1, h + 0.06 + mb.jitter(0.03), ("stone_grey", "stone_light", "stone_warm")[(i * 3 + j) % 3] if color == "stone_grey" else color,
                       pos=(-w / 2 + 0.1 + sx * (i + 0.5), -d / 2 + 0.1 + sy * (j + 0.5), 0), taper=0.93, tone=mb.jitter(0.06))


def wood_frame(mb, w, d, h, color="wood_dark", inset=0.45, post=0.5, braces=True):
    """Four posts with stretchers and diagonal braces. Returns the top height."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (w / 2 - inset), sy * (d / 2 - inset)
            mb.box(post, post, h, color, pos=(x, y, 0), tone=mb.jitter(0.04))
            mb.box(post + 0.2, post + 0.2, 0.25, color, pos=(x, y, 0), tone=-0.08)
    for sy in (-1, 1):
        y = sy * (d / 2 - inset)
        mb.beam((-(w / 2 - inset), y, h * 0.3), (w / 2 - inset, y, h * 0.3), 0.3, 0.3, color)
        if braces:
            mb.beam((-(w / 2 - inset), y, h * 0.3), (-(w / 2 - inset) + h * 0.5, y, h - 0.1), 0.24, 0.24, color)
            mb.beam((w / 2 - inset, y, h * 0.3), (w / 2 - inset - h * 0.5, y, h - 0.1), 0.24, 0.24, color)
    for sx in (-1, 1):
        x = sx * (w / 2 - inset)
        mb.beam((x, -(d / 2 - inset), h * 0.3), (x, d / 2 - inset, h * 0.3), 0.3, 0.3, color)
    return h


def workbench(mb, w, d, h=2.5, top="wood_light"):
    wood_frame(mb, w - 0.3, d - 0.3, h)
    mb.box(w - 0.5, d - 0.5, 0.22, "wood_dark", pos=(0, 0, h - 0.1))
    planks(mb, w - 0.2, d - 0.2, h + 0.1, top)
    for sx in (-1, 1):                                       # iron corner straps
        for sy in (-1, 1):
            mb.box(0.5, 0.5, 0.06, "iron", pos=(sx * (w / 2 - 0.4), sy * (d / 2 - 0.4), h + 0.4))
    return h + 0.4


def funnel_in(mb, x, y, z=1.2, s=1.0):
    """Solid input: funnel that leans out towards the back (+Y)."""
    with mb.at(T(x, y, z), R("X", 22)):
        mb.lathe([(0.3 * s, 0.0), (0.72 * s, 0.75 * s), (0.78 * s, 0.82 * s), (0.62 * s, 0.82 * s), (0.22 * s, 0.1 * s)], "wood_light",
                 segs=4, phase=math.pi / 4, smooth=False)
        mb.lathe([(0.8 * s, 0.78 * s), (0.8 * s, 0.9 * s)], "brass", segs=4, phase=math.pi / 4, smooth=False)


def chute_out(mb, x, y, z=1.0, s=1.0):
    """Solid output: sloped chute with side boards and a small tray, pointing to the front (-Y)."""
    with mb.at(T(x, y, 0)):
        mb.beam((0, 0.5 * s, z + 0.35 * s), (0, -0.25 * s, z - 0.15 * s), 0.9 * s, 0.1, "wood_light")
        for sx in (-1, 1):
            mb.beam((sx * 0.45 * s, 0.5 * s, z + 0.45 * s), (sx * 0.45 * s, -0.25 * s, z - 0.05 * s), 0.1, 0.3 * s, "wood_dark")
        mb.box(1.0 * s, 0.14, 0.3, "brass", pos=(0, -0.3 * s, z - 0.3))


def fluid_stub(mb, side, y, z=1.3, ring="flower_blue", x=None, w=4):
    """Pipe stub at the left (-1) or right (+1) edge."""
    x1 = side * (w / 2 - 0.08) if x is None else x
    x0 = x1 - side * 0.8
    tube(mb, (x0, y, z), (x1, y, z), 0.3, "brass", segs=8)
    with mb.at(T(x1 - side * 0.12, y, z), R("Y", 90)):
        mb.cyl(0.45, 0.45, 0.12, "iron", pos=(0, 0, -0.06), segs=8, smooth=False)
        mb.cyl(0.38, 0.38, 0.16, ring, pos=(0, 0, -0.08 - side * 0.02), segs=8, smooth=False, grad=(0.5, 0.8))


def port_x(w, cells):
    """X of the solid ports (cell column floor((cells-1)/2))."""
    return (math.floor((cells - 1) / 2) + 0.5) * 2 - w / 2


def fire_bed(mb, x, y, z, r=0.8):
    for k in range(4):
        with mb.at(T(x, y, z), R("Z", 45 * k + 10)):
            mb.box(r * 1.9, 0.26, 0.22, "bark", pos=(0, 0, k * 0.07), tone=-0.1)
    mb.blob(r * 0.55, "roof_orange", pos=(x, y, z + 0.35), level=0, noise=0.35, scale=(1.2, 1.2, 0.9), grad=(0.5, 0.95))
    mb.blob(r * 0.32, "glass_lit", pos=(x, y, z + 0.6), level=0, noise=0.35, scale=(1, 1, 1.3), grad=(0.6, 0.98))


def crystal(mb, x, y, z, h=1.2, r=0.4, color="glass_light", segs=5):
    mb.lathe([(0.0, 0.0), (r, h * 0.3), (r * 0.8, h * 0.72), (0.0, h)], color, segs=segs, pos=(x, y, z), smooth=False, grad=(0.3, 0.98))


def rune_plate(mb, x, y, z, color="glass_light", s=0.4, rot=0):
    with mb.at(T(x, y, z), R("Z", rot)):
        mb.box(s, s * 0.28, 0.06, color, grad=(0.6, 0.95))
        mb.box(s * 0.28, s, 0.06, color, grad=(0.6, 0.95))


def tool_rack(mb, x, y, z, n=3, w=2.0):
    """Wall-less rack: a rail with hanging tools, facing -Y."""
    mb.beam((x - w / 2, y, z), (x + w / 2, y, z), 0.14, 0.14, "wood_dark")
    for i in range(n):
        tx = x - w / 2 + w * (i + 0.5) / n
        mb.box(0.1, 0.1, 0.9 + 0.2 * (i % 2), "wood_light", pos=(tx, y - 0.08, z - 1.0 - 0.2 * (i % 2)))
        if i % 2 == 0:
            mb.box(0.45, 0.2, 0.3, "iron", pos=(tx, y - 0.08, z - 1.3))
        else:
            mb.lathe([(0.0, 0.0), (0.2, 0.25), (0.06, 0.4)], "iron", segs=4, pos=(tx, y - 0.08, z - 1.6), smooth=False)


# ====================================================================== machines
def kettle(mb):
    stone_plinth(mb, 4, 4)
    mb.lathe([(1.5, 0.5), (1.6, 0.8), (1.3, 0.8), (1.25, 0.56)], "stone_dark", segs=10, smooth=False)       # fire ring
    fire_bed(mb, 0, 0, 0.56)
    for k in range(3):                                                                                       # tripod
        a = TAU * k / 3 + 0.5
        mb.beam((1.6 * math.cos(a), 1.6 * math.sin(a), 0.5), (0.25 * math.cos(a), 0.25 * math.sin(a), 5.2), 0.2, 0.2, "iron")
    mb.blob(0.26, "iron", pos=(0, 0, 5.25), level=0, noise=0.0)
    for k in range(3):                                                                                       # chains
        a = TAU * k / 3 + 1.55
        for i in range(4):
            f = i / 4
            mb.box(0.1, 0.1, 0.34, "iron", pos=(1.25 * math.cos(a) * (1 - f) * 0.9, 1.25 * math.sin(a) * (1 - f) * 0.9, 3.75 + f * 1.4),
                   tone=0.05 * (i % 2))
    mb.lathe([(0.7, 1.35), (1.3, 1.6), (1.55, 2.3), (1.5, 3.1), (1.3, 3.55), (1.45, 3.75), (1.2, 3.75), (1.15, 3.3)], "iron", segs=12,
             smooth=False, grad=(0.3, 0.7))
    band(mb, 1.57, 2.35, 0.16, "brass", 12, bolts=12)
    rivets(mb, 1.36, 3.5, 12, "brass")
    for side in (-1, 1):
        pipe_run(mb, [(side * 1.34, -0.38, 2.95), (side * 1.73, -0.33, 2.89),
                      (side * 1.73, 0.32, 2.89), (side * 1.34, 0.36, 2.95)], 0.085, "brass")
    mb.cyl(1.15, 1.15, 0.1, "leaf_lime", pos=(0, 0, 3.3), segs=12, smooth=False, grad=(0.6, 0.85))
    for bx, by, r in ((0.4, 0.3, 0.2), (-0.5, -0.2, 0.15), (0.1, -0.6, 0.12)):
        mb.blob(r, "leaf_lime", pos=(bx, by, 3.42), level=0, noise=0.0, scale=(1, 1, 0.6), grad=(0.7, 0.98))
    tube(mb, (0.5, 0.4, 3.2), (1.5, 1.2, 4.9), 0.07, "wood_light", segs=5)                                    # ladle
    mb.blob(0.2, "wood_light", pos=(0.5, 0.4, 3.25), level=0, noise=0.0)
    funnel_in(mb, port_x(4, 2), 1.45, 0.75, 0.75)
    chute_out(mb, port_x(4, 2), -1.55, 0.95, 0.8)
    fluid_stub(mb, -1, 1.0, 1.1)
    for i, c in enumerate(("glass_blue", "flower_red", "leaf_lime")):
        bottle(mb, 1.45, -1.3 + i * 0.5, 0.56, c, 0.75)
    mb.light((0, 0, 3.7), color=(0.6, 1.0, 0.5), brightness=0.7, range_=10)
    mb.light((0, 0, 0.9), color=(1.0, 0.6, 0.25), brightness=0.7, range_=8)


def grinder(mb):
    stone_plinth(mb, 4, 4)
    wood_frame(mb, 3.2, 3.2, 1.3, inset=0.35, post=0.4, braces=False)
    mb.cyl(1.55, 1.6, 0.75, "stone_dark", pos=(0, 0, 1.3), segs=12, smooth=False)                             # bed stone
    for k in range(6):
        with mb.at(R("Z", 30 * k)):
            mb.box(3.0, 0.08, 0.03, "stone_grey", pos=(0, 0, 2.05), tone=-0.15)
    mb.cyl(1.4, 1.4, 0.7, "stone_light", pos=(0, 0, 2.15), segs=12, smooth=False)                             # runner stone
    band(mb, 1.42, 2.3, 0.14, "iron", 12, bolts=6)
    mb.lathe([(0.3, 2.85), (1.0, 3.9), (1.08, 4.0), (0.9, 4.0), (0.25, 2.95)], "wood_light", segs=8, smooth=False)   # hopper
    band(mb, 1.06, 3.9, 0.12, "brass", 8)
    for i in range(5):
        mb.blob(0.2, "leaf_green", pos=(0.45 * math.cos(i * 1.3), 0.45 * math.sin(i * 1.3), 3.85 + 0.05 * i), level=0, noise=0.2)
    mb.beam((0, 0, 2.5), (1.95, 0, 2.5), 0.2, 0.2, "wood_dark")                                               # crank arm
    mb.box(0.3, 0.3, 1.0, "wood_dark", pos=(1.82, 0, 2.5))
    mb.cyl(0.22, 0.22, 0.5, "wood_light", pos=(1.82, 0, 3.4), segs=6)
    with mb.at(T(-1.4, -1.5, 1.9), R("X", 90)):
        gear(mb, 0.55, 0.16, teeth=8)
    with mb.at(T(-0.55, -1.5, 2.2), R("X", 90), R("Z", 22)):
        gear(mb, 0.4, 0.16, "iron", teeth=6, hub="brass")
    funnel_in(mb, port_x(4, 2), 1.5, 1.4, 0.8)
    chute_out(mb, port_x(4, 2), -1.5, 1.35, 0.8)
    mb.box(0.9, 0.9, 0.5, "wood_mid", pos=(1.35, -1.4, 0.56), taper=1.1)                                      # powder bowl
    mb.blob(0.42, "leaf_lime", pos=(1.35, -1.4, 1.0), level=0, noise=0.1, scale=(1, 1, 0.4), grad=(0.5, 0.8))


def saw(mb):
    top = workbench(mb, 6, 4, 2.4)
    with mb.at(T(0.9, 0.1, top + 0.05), R("X", 90)):                                                          # blade
        mb.cyl(1.25, 1.25, 0.08, "stone_light", pos=(0, 0, -0.04), segs=16, smooth=False)
        for k in range(16):
            with mb.at(R("Z", 22.5 * k)):
                mb.box(0.24, 0.22, 0.07, "stone_light", pos=(1.3, 0, -0.035), taper=(0.3, 1.0))
        mb.cyl(0.3, 0.3, 0.3, "brass", pos=(0, 0, -0.15), segs=6, smooth=False)
    mb.box(1.5, 0.5, 1.5, "wood_dark", pos=(0.9, 0.75, top))                                                  # blade guard
    mb.box(1.7, 0.6, 0.2, "iron", pos=(0.9, 0.75, top + 1.5))
    mb.box(5.4, 0.25, 0.4, "wood_mid", pos=(0, -1.2, top))                                                    # fence
    for x in (-2.2, -1.4):                                                                                    # logs waiting
        with mb.at(T(x, 0.3, top + 0.4), R("X", 90)):
            mb.cyl(0.38, 0.36, 2.6, "bark", pos=(0, 0, -1.3), segs=7)
            mb.cyl(0.3, 0.3, 0.04, "wood_pale", pos=(0, 0, 1.3), segs=7, smooth=False)
            mb.cyl(0.3, 0.3, 0.04, "wood_pale", pos=(0, 0, -1.34), segs=7, smooth=False)
    for i in range(3):                                                                                        # finished boards
        mb.box(1.6, 0.9, 0.14, "wood_pale", pos=(2.1, -0.4, top + 0.02 + i * 0.16), tone=mb.jitter(0.06))
    with mb.at(T(-2.75, 1.0, 1.5), R("Y", 90)):                                                               # treadle wheel
        gear(mb, 0.75, 0.18, "wood_mid", teeth=10, hub="iron")
    mb.beam((-2.6, 1.0, 1.5), (0.9, 0.9, top - 0.3), 0.12, 0.12, "iron")
    mb.box(1.6, 0.6, 0.14, "wood_dark", pos=(-1.2, -1.6, 0.35))                                              # pedal
    for i in range(6):
        mb.blob(0.2, "wood_pale", pos=(0.4 + mb.jitter(0.9), -1.45 + mb.jitter(0.2), 0.1), level=0, noise=0.3, scale=(1.3, 1, 0.4))
    funnel_in(mb, port_x(6, 3), 1.55, top - 0.1, 0.75)
    chute_out(mb, port_x(6, 3), -1.6, top - 0.75, 0.85)
    tool_rack(mb, -1.6, 1.75, 2.1, 3, 1.8)


def crusher(mb):
    stone_plinth(mb, 4, 4)
    mb.box(2.5, 2.5, 1.3, "stone_dark", pos=(0, 0, 0.5), taper=0.9)                                           # mortar block
    mb.lathe([(1.0, 1.8), (1.15, 2.05), (0.8, 2.05), (0.6, 1.85)], "stone_light", segs=8, smooth=False)
    for sx in (-1, 1):
        mb.box(0.5, 0.6, 5.3, "wood_dark", pos=(sx * 1.55, 0.3, 0.5), tone=mb.jitter(0.04))
        mb.beam((sx * 1.55, 0.3, 1.0), (sx * 1.55, -1.3, 0.55), 0.3, 0.3, "wood_dark")
        mb.box(0.62, 0.72, 0.2, "iron", pos=(sx * 1.55, 0.3, 3.3))
    mb.box(3.8, 0.7, 0.55, "wood_dark", pos=(0, 0.3, 5.8))
    mb.box(1.3, 1.3, 0.9, "iron", pos=(0, 0.1, 2.5), taper=0.85)                                              # stamp head
    rivets(mb, 0.7, 3.2, 4, "brass", 0.14, math.pi / 4, (0, 0.1))
    mb.box(0.45, 0.45, 2.4, "wood_mid", pos=(0, 0.1, 3.4))
    mb.box(0.9, 0.3, 0.3, "iron", pos=(0, 0.1, 4.6))
    with mb.at(T(0, 0.75, 4.75), R("Y", 90)):                                                                 # cam shaft
        mb.cyl(0.2, 0.2, 3.7, "wood_mid", pos=(0, 0, -1.85), segs=6)
        mb.box(0.3, 0.7, 0.5, "iron", pos=(0.25, 0, -0.25))
    with mb.at(T(1.78, 0.75, 4.75), R("Y", 90)):
        gear(mb, 0.7, 0.16, teeth=9)
    mb.beam((1.86, 0.75, 4.75), (1.86, -0.2, 4.2), 0.12, 0.12, "wood_dark")                                   # crank
    mb.cyl(0.1, 0.1, 0.5, "wood_light", pos=(1.86, -0.2, 3.9), segs=5)
    for i in range(4):
        mb.blob(0.3, ("rock", "stone_light")[i % 2], pos=(-1.3 + i * 0.35, -1.45, 0.72 + 0.05 * (i % 2)), level=0, noise=0.3)
    funnel_in(mb, port_x(4, 2), 1.5, 1.7, 0.75)
    chute_out(mb, port_x(4, 2), -1.5, 1.25, 0.8)


def furnace(mb):
    stone_plinth(mb, 6, 4, color="stone_dark")
    rng = mb.rng
    mb.box(4.3, 3.2, 3.3, "brick", pos=(-0.6, 0.1, 0.5), taper=(0.94, 0.94), grad=(0.3, 0.6))                 # body
    for row in range(5):                                                                                      # single bricks
        for i in range(5):
            x = -2.45 + i * 0.9 + (0.45 if row % 2 else 0)
            if abs(x + 0.6) > 0.9 or row > 2:
                mb.box(0.78, 0.14, 0.42, ("brick", "roof_brown", "roof_red")[(i + row) % 3], pos=(min(x, 1.2), -1.5 + 0.02 * row, 0.7 + row * 0.56),
                       tone=rng.uniform(-0.08, 0.08))
    mb.lathe([(1.9, 3.8), (1.5, 4.5), (0.9, 4.9)], "brick", segs=4, phase=math.pi / 4, pos=(-0.6, 0.1, 0), smooth=False)      # dome
    mb.box(1.5, 0.3, 1.5, "iron", pos=(-0.6, -1.52, 0.75))                                                    # door
    mb.box(1.1, 0.1, 0.9, "glass_lit", pos=(-0.6, -1.7, 1.0), grad=(0.6, 0.95))
    for z in (0.95, 1.3, 1.65):
        mb.box(1.2, 0.12, 0.08, "iron", pos=(-0.6, -1.74, z))
    mb.box(0.16, 0.2, 1.3, "brass", pos=(-1.45, -1.6, 0.85))                                                  # hinge / latch
    mb.box(0.4, 0.3, 0.14, "brass", pos=(0.25, -1.65, 1.4))
    mb.box(1.3, 1.3, 2.9, "stone_grey", pos=(0.4, 0.8, 3.7), taper=0.86)                                      # chimney
    for z in (4.3, 5.2, 6.0):
        mb.box(1.45 - (z - 4) * 0.05, 1.45 - (z - 4) * 0.05, 0.16, "stone_dark", pos=(0.4, 0.8, z))
    mb.box(1.5, 1.5, 0.3, "stone_dark", pos=(0.4, 0.8, 6.6))
    mb.cyl(0.4, 0.34, 0.6, "roof_orange", pos=(0.4, 0.8, 6.9), segs=6)
    with mb.at(T(-2.2, -1.98, 0.95), R("X", -90), S(0.55)):                                                   # bellows
        mb.lathe([(0.0, 0.0), (0.7, 0.3), (0.75, 1.2), (0.2, 1.7)], "wood_mid", segs=4, phase=math.pi / 4, smooth=False)
        for z in (0.5, 0.8, 1.1):
            mb.lathe([(0.8, z), (0.8, z + 0.1)], "cloth_red", segs=4, phase=math.pi / 4, smooth=False)
    mb.box(1.5, 2.6, 1.3, "wood_dark", pos=(2.15, 0.2, 0.5))                                                  # coal bin
    for sy in (-1, 1):
        mb.box(1.6, 0.14, 0.2, "iron", pos=(2.15, 0.2 + sy * 1.25, 1.2))
    for i in range(7):
        mb.blob(0.34, "iron", pos=(2.15 + mb.jitter(0.45), 0.2 + mb.jitter(0.9), 1.85 + mb.jitter(0.1)), level=0, noise=0.35, scale=(1, 1, 0.7))
    tube(mb, (2.3, -1.2, 0.5), (2.9, -1.75, 2.6), 0.07, "wood_light", segs=5)                                 # shovel
    mb.box(0.5, 0.1, 0.6, "iron", pos=(2.2, -1.1, 0.4))
    with mb.at(T(-0.6, -1.55, 3.2)):
        gauge(mb, 0.34)
    funnel_in(mb, port_x(6, 3), 1.6, 2.4, 0.8)
    mb.box(1.3, 0.5, 0.14, "iron", pos=(port_x(6, 3) + 1.6, -1.7, 0.6))                                       # output shelf with ingot mould
    mb.box(0.8, 0.35, 0.2, "brass", pos=(port_x(6, 3) + 1.6, -1.7, 0.74), taper=0.8)
    mb.light((-0.6, -2.0, 1.4), color=(1.0, 0.6, 0.25), brightness=1.1, range_=12)


def glassbench(mb):
    top = workbench(mb, 4, 4, 2.4)
    mb.box(1.3, 1.3, 0.9, "stone_dark", pos=(-1.1, 1.0, top), taper=0.9)                                      # glory hole
    mb.box(0.7, 0.2, 0.5, "glass_lit", pos=(-1.1, 0.36, top + 0.2), grad=(0.6, 0.95))
    mb.cyl(0.3, 0.26, 0.9, "stone_grey", pos=(-1.1, 1.2, top + 0.9), segs=6)
    tube(mb, (-1.7, -0.9, top + 0.45), (1.3, -0.5, top + 0.75), 0.07, "iron", segs=6)                         # blowpipe
    mb.blob(0.36, "glass_lit", pos=(1.45, -0.48, top + 0.77), level=1, noise=0.05, scale=(1.2, 1, 1), grad=(0.5, 0.98))
    for sx in (-1.5, -0.7):                                                                                   # pipe rests
        mb.box(0.12, 0.3, 0.5, "iron", pos=(sx, -0.8 + (sx + 1.5) * 0.14, top))
    flask(mb, 0.5, 0.9, top, "glass_light", 0.7)
    flask(mb, 1.3, 1.1, top, "glass_blue", 0.55)
    for i in range(4):
        bottle(mb, 0.1 + i * 0.45, 0.2, top, ("glass_light", "glass_blue")[i % 2], 0.6, cork=False)
    mb.box(1.0, 0.7, 0.12, "stone_light", pos=(1.2, -1.3, top))                                               # marver
    with mb.at(T(-0.3, -1.3, top + 0.06), R("Z", 25)):                                                        # jacks / shears
        mb.box(1.1, 0.1, 0.08, "iron")
        mb.box(1.1, 0.1, 0.08, "iron", pos=(0, 0.18, 0))
    mb.box(1.4, 1.0, 0.9, "wood_mid", pos=(1.1, 1.0, 0.3), taper=1.05)                                        # sand crate under the bench
    mb.blob(0.6, "sand", pos=(1.1, 1.0, 1.15), level=0, noise=0.15, scale=(1.1, 0.8, 0.35))
    funnel_in(mb, port_x(4, 2), 1.55, top - 0.05, 0.7)
    chute_out(mb, port_x(4, 2), -1.6, top - 0.75, 0.8)
    mb.light((-1.1, 0.2, top + 0.5), color=(1.0, 0.65, 0.3), brightness=0.8, range_=9)


def extractor(mb):
    stone_plinth(mb, 6, 4)
    # copper still
    mb.lathe([(1.2, 0.5), (1.5, 0.9), (1.55, 2.6), (1.25, 3.3), (0.55, 3.9), (0.4, 4.5), (0.5, 4.7)], "brass", segs=12, pos=(-1.2, 0.1, 0),
             smooth=False, grad=(0.3, 0.8))
    band(mb, 1.58, 1.2, 0.18, "iron", 12, pos=(-1.2, 0.1, 0), bolts=0)
    band(mb, 1.58, 2.4, 0.18, "iron", 12, pos=(-1.2, 0.1, 0))
    rivets(mb, 1.6, 1.29, 12, "brass", 0.11, 0, (-1.2, 0.1))
    rivets(mb, 1.6, 2.49, 12, "brass", 0.11, 0.26, (-1.2, 0.1))
    mb.box(0.7, 0.14, 0.9, "glass_light", pos=(-1.2, -1.5, 1.3), grad=(0.3, 0.9))                              # sight glass
    mb.box(0.86, 0.1, 1.06, "iron", pos=(-1.2, -1.46, 1.22))
    with mb.at(T(-1.2, -1.58, 2.9)):
        gauge(mb, 0.36)
    pipe_run(mb, [(-1.2, 0.1, 4.7), (-1.2, 0.1, 5.3), (0.9, 0.1, 5.0), (1.6, 0.1, 4.3)], 0.2)                # swan neck
    # condenser coil around a glass column
    mb.lathe([(0.55, 0.9), (0.6, 3.9), (0.4, 4.3)], "glass_light", segs=8, pos=(1.6, 0.1, 0), smooth=False, grad=(0.35, 0.9))
    n = 22
    pts = [(1.6 + 0.78 * math.cos(i * 0.9), 0.1 + 0.78 * math.sin(i * 0.9), 4.0 - i * 0.135) for i in range(n)]
    for a, b in zip(pts[:-1], pts[1:]):
        tube(mb, a, b, 0.09, "roof_orange", segs=4)
    mb.cyl(0.85, 0.95, 0.5, "wood_mid", pos=(1.6, 0.1, 0.5), segs=8, smooth=False)
    band(mb, 0.97, 0.6, 0.12, "iron", 8, pos=(1.6, 0.1, 0))
    with mb.at(T(0.3, 0.1, 5.35)):
        valve(mb, 0.36)
    flask(mb, 1.6, -1.35, 0.56, "glass_light", 0.8, liquid="leaf_lime")                                       # catch flask
    tube(mb, (1.6, -0.6, 1.3), (1.6, -1.35, 1.75), 0.08, "brass", segs=5)
    fluid_stub(mb, -1, 1.0, 1.3, w=6)
    fluid_stub(mb, 1, 1.0, 1.3, "roof_orange", w=6)
    funnel_in(mb, port_x(6, 3), 1.55, 1.5, 0.75)
    tube(mb, (port_x(6, 3), 1.2, 1.6), (-0.6, 0.6, 2.2), 0.14, "brass", segs=6)
    mb.light((-1.2, -1.7, 1.6), color=(0.6, 1.0, 0.6), brightness=0.6, range_=9)


def bottler(mb):
    top = workbench(mb, 4, 4, 2.2)
    mb.lathe([(0.5, 1.9), (0.95, 2.2), (1.0, 3.6), (0.7, 4.0), (0.3, 4.1)], "glass_light", segs=10, pos=(0, 0.6, top), smooth=False,
             grad=(0.35, 0.92))                                                                               # reservoir
    mb.lathe([(0.0, 2.0), (0.86, 2.26), (0.9, 3.0), (0.0, 3.02)], "leaf_lime", segs=10, pos=(0, 0.6, top + 0.01), smooth=False, grad=(0.45, 0.85))
    for sx in (-1, 1):
        mb.box(0.3, 0.3, 4.3, "wood_dark", pos=(sx * 1.25, 0.6, top))
        mb.beam((sx * 1.25, 0.6, top + 1.9), (sx * 0.9, 0.6, top + 2.2), 0.2, 0.2, "iron")
    mb.box(2.9, 0.4, 0.3, "wood_dark", pos=(0, 0.6, top + 4.2))
    band(mb, 1.02, 2.3, 0.14, "brass", 10, pos=(0, 0.6, top), bolts=5)
    tube(mb, (0, 0.6, top + 1.9), (0, -0.5, top + 1.5), 0.13, "brass", segs=6, flanges=True)                  # filling arm
    tube(mb, (0, -0.5, top + 1.5), (0, -0.5, top + 1.05), 0.09, "brass", segs=6)
    with mb.at(T(0.45, 0.05, top + 1.75), R("Y", 90)):
        valve(mb, 0.3)
    mb.cyl(1.25, 1.25, 0.14, "wood_mid", pos=(0, -0.6, top), segs=10, smooth=False)                           # turntable
    for k in range(5):
        a = TAU * k / 5 - math.pi / 2
        bottle(mb, 0.9 * math.cos(a), -0.6 + 0.9 * math.sin(a), top + 0.14, "leaf_lime" if k < 2 else "glass_light", 0.7, cork=(k < 2))
    mb.box(0.9, 0.7, 0.4, "wood_mid", pos=(-1.35, -1.2, top), taper=1.1)                                      # cork box
    for i in range(4):
        mb.cyl(0.1, 0.09, 0.16, "wood_pale", pos=(-1.55 + (i % 2) * 0.35, -1.35 + (i // 2) * 0.3, top + 0.4), segs=5)
    mb.box(0.9, 0.5, 0.3, "plaster_cream", pos=(1.35, -1.25, top))                                            # labels
    with mb.at(T(1.35, 0.3, top + 2.6)):
        gauge(mb, 0.3)
    fluid_stub(mb, -1, 1.0, 1.3)
    tube(mb, (-1.2, 1.0, 1.3), (-0.4, 0.8, top + 2.0), 0.12, "brass", segs=5)
    funnel_in(mb, port_x(4, 2), 1.55, top - 0.05, 0.7)
    chute_out(mb, port_x(4, 2), -1.6, top - 0.75, 0.8)


def mixer(mb):
    stone_plinth(mb, 4, 4)
    n = 12                                                                                                    # stave vat
    for k in range(n):
        with mb.at(R("Z", 360.0 * k / n)):
            mb.box(0.22, 0.86, 2.9, "wood_mid", pos=(1.52, 0, 0.5), tone=mb.jitter(0.08), taper=(1.0, 1.06))
    mb.cyl(1.5, 1.5, 0.3, "wood_dark", pos=(0, 0, 0.5), segs=n, smooth=False)
    for z in (0.95, 2.0, 3.0):
        band(mb, 1.68, z, 0.2, "iron", n, bolts=4)
    mb.cyl(1.42, 1.42, 0.1, "flower_purple", pos=(0, 0, 2.9), segs=n, smooth=False, grad=(0.5, 0.85))
    for bx, by in ((0.5, 0.4), (-0.6, 0.1), (0.1, -0.7)):
        mb.blob(0.18, "leaf_pink", pos=(bx, by, 3.0), level=0, noise=0.0, scale=(1, 1, 0.5))
    for sx in (-1, 1):                                                                                        # gantry
        mb.box(0.36, 0.36, 5.2, "wood_dark", pos=(sx * 1.72, 0.9, 0.5))
    mb.box(3.9, 0.45, 0.4, "wood_dark", pos=(0, 0.9, 5.5))
    mb.beam((0, 0.9, 5.7), (0, 0, 5.7), 0.4, 0.3, "wood_dark")
    mb.cyl(0.13, 0.13, 3.2, "iron", pos=(0, 0, 2.4), segs=6)                                                  # paddle shaft
    for a in (0, 90):
        with mb.at(T(0, 0, 2.5), R("Z", a + 20)):
            mb.box(2.0, 0.1, 0.5, "wood_light", pos=(0, 0, 0))
    with mb.at(T(0, 0, 5.4)):
        gear(mb, 0.6, 0.18, teeth=10)
    with mb.at(T(0.95, 0, 5.4), R("Z", 18)):
        gear(mb, 0.4, 0.18, "iron", teeth=7, hub="brass")
    mb.beam((0.95, 0, 5.5), (0.95, 0, 6.1), 0.12, 0.12, "iron")
    mb.beam((0.95, 0, 6.1), (1.6, -0.5, 6.1), 0.12, 0.12, "wood_dark")
    mb.cyl(0.12, 0.12, 0.45, "wood_light", pos=(1.6, -0.5, 6.1), segs=5)
    tube(mb, (0, -1.55, 0.95), (0, -1.9, 0.95), 0.16, "brass", segs=6, flanges=True)                          # tap
    fluid_stub(mb, -1, 1.0, 1.3)
    fluid_stub(mb, 1, 1.0, 1.3, "roof_orange")
    funnel_in(mb, port_x(4, 2), 1.5, 3.0, 0.7)
    chute_out(mb, port_x(4, 2), -1.55, 0.95, 0.75)


def runetable(mb):
    stone_plinth(mb, 6, 6, 0.4, "stone_dark")
    mb.cyl(2.2, 2.45, 0.5, "stone_dark", pos=(0, 0, 0.4), segs=8, smooth=False)
    for k in range(8):                                                                                        # carved pillar stones
        with mb.at(R("Z", 45 * k)):
            mb.box(0.5, 1.55, 1.7, ("stone_grey", "stone_light")[k % 2], pos=(1.95, 0, 0.9), taper=(0.9, 0.96), tone=mb.jitter(0.05))
            mb.box(0.1, 0.5, 0.9, "glass_light", pos=(2.2, 0, 1.3), grad=(0.5, 0.95))
    mb.cyl(1.9, 1.9, 1.7, "stone_dark", pos=(0, 0, 0.9), segs=8, smooth=False)
    mb.cyl(2.75, 2.75, 0.4, "stone_light", pos=(0, 0, 2.6), segs=8, smooth=False)                             # slab
    mb.cyl(2.2, 2.2, 0.06, "stone_grey", pos=(0, 0, 3.0), segs=16, smooth=False)
    for k in range(16):                                                                                       # rune circle
        a = TAU * k / 16
        rune_plate(mb, 1.9 * math.cos(a), 1.9 * math.sin(a), 3.06, ("glass_light", "flower_blue")[k % 2], 0.34, math.degrees(a))
    for k in range(6):
        a = TAU * k / 6 + 0.3
        tube(mb, (1.1 * math.cos(a), 1.1 * math.sin(a), 3.08), (1.1 * math.cos(a + TAU / 3), 1.1 * math.sin(a + TAU / 3), 3.08), 0.04,
             "glass_light", segs=3)
    crystal(mb, 0, 0, 3.6, 1.5, 0.5, "flower_blue", 6)                                                        # focus crystal
    for k in range(3):
        a = TAU * k / 3
        tube(mb, (0.8 * math.cos(a), 0.8 * math.sin(a), 3.06), (0.25 * math.cos(a), 0.25 * math.sin(a), 3.75), 0.07, "brass", segs=5)
    mb.box(0.9, 0.6, 0.2, "stone_warm", pos=(-1.9, -1.2, 3.0))                                                # blank on the table
    for i, (cx, cy) in enumerate(((2.3, -2.3), (-2.3, 2.3))):                                                 # candles
        mb.cyl(0.14, 0.12, 0.7 + 0.2 * i, "plaster_cream", pos=(cx, cy, 0.46), segs=6)
        mb.blob(0.12, "glass_lit", pos=(cx, cy, 1.3 + 0.2 * i), level=0, noise=0.0, scale=(0.8, 0.8, 1.5))
    mb.box(0.6, 0.2, 0.9, "wood_mid", pos=(2.2, -1.4, 3.0))                                                   # chisel block
    tube(mb, (2.2, -1.4, 3.9), (2.5, -1.0, 4.6), 0.06, "iron", segs=4)
    funnel_in(mb, port_x(6, 3), 2.5, 2.3, 0.85)
    chute_out(mb, port_x(6, 3), -2.55, 2.3, 0.9)
    mb.light((0, 0, 4.3), color=(0.5, 0.7, 1.0), brightness=0.9, range_=12)


def forge(mb):
    stone_plinth(mb, 6, 6, color="stone_dark")
    rng = mb.rng
    mb.box(3.6, 3.0, 2.3, "stone_grey", pos=(-0.9, 1.2, 0.5), taper=0.95)                                     # hearth
    for _ in range(14):
        sw = rng.uniform(0.7, 1.2)
        mb.box(sw, 0.16, rng.uniform(0.4, 0.6), rng.choice(("stone_light", "stone_dark", "stone_warm")),
               pos=(rng.uniform(-2.4, 0.6), -0.3, rng.uniform(0.7, 2.3)), tone=rng.uniform(-0.05, 0.05))
    mb.box(3.0, 2.4, 0.3, "stone_dark", pos=(-0.9, 1.2, 2.8))
    for i in range(9):
        mb.blob(0.3, "iron", pos=(-0.9 + mb.jitter(1.1), 1.2 + mb.jitter(0.8), 3.15), level=0, noise=0.35, scale=(1, 1, 0.6))
    for i in range(4):
        mb.blob(0.26, "roof_orange", pos=(-0.9 + mb.jitter(0.6), 1.2 + mb.jitter(0.5), 3.3), level=0, noise=0.3, grad=(0.55, 0.98))
    mb.blob(0.3, "glass_lit", pos=(-0.9, 1.2, 3.45), level=0, noise=0.3, scale=(1, 1, 1.4), grad=(0.6, 0.98))
    mb.lathe([(2.1, 4.6), (1.2, 5.9), (0.6, 6.3), (0.6, 7.6)], "stone_dark", segs=4, phase=math.pi / 4, pos=(-0.9, 1.2, 0), smooth=False)  # hood
    for sx in (-1, 1):
        mb.box(0.3, 0.3, 1.9, "iron", pos=(-0.9 + sx * 1.6, 0.0, 2.8))
        mb.box(0.3, 0.3, 1.9, "iron", pos=(-0.9 + sx * 1.6, 2.5, 2.8))
    with mb.at(T(1.7, 1.6, 2.6), R("Y", 90), S(0.55)):                                                        # big bellows
        mb.lathe([(0.0, 0.0), (0.85, 0.3), (0.95, 1.5), (0.25, 2.2)], "wood_mid", segs=4, phase=math.pi / 4, smooth=False)
        for z in (0.5, 0.85, 1.2):
            mb.lathe([(1.0, z), (1.0, z + 0.12)], "cloth_red", segs=4, phase=math.pi / 4, smooth=False)
    mb.beam((2.3, 1.6, 3.1), (2.7, 0.4, 4.4), 0.14, 0.14, "wood_dark")
    mb.cyl(0.85, 0.95, 1.5, "wood_mid", pos=(1.5, -1.5, 0.5), segs=8)                                         # anvil on a stump
    band(mb, 0.92, 1.4, 0.16, "iron", 8, pos=(1.5, -1.5, 0))
    mb.box(1.1, 0.7, 0.4, "iron", pos=(1.5, -1.5, 2.0))
    mb.box(0.7, 0.5, 0.45, "iron", pos=(1.5, -1.5, 2.4))
    mb.box(1.9, 0.8, 0.5, "iron", pos=(1.5, -1.5, 2.85))
    mb.beam((2.45, -1.5, 3.1), (3.0, -1.5, 3.2), 0.4, 0.3, "iron")                                            # horn
    with mb.at(T(1.4, -1.5, 3.4), R("Z", 35)):                                                                # hammer
        mb.box(0.16, 1.3, 0.14, "wood_light")
        mb.box(0.5, 0.36, 0.34, "iron", pos=(0, 0.6, -0.1))
    mb.box(1.5, 1.0, 1.1, "wood_dark", pos=(-2.2, -2.2, 0.5), taper=1.06)                                     # quench tub
    mb.box(1.3, 0.8, 0.08, "water", pos=(-2.2, -2.2, 1.5))
    tool_rack(mb, -0.2, -2.7, 3.3, 4, 2.4)
    for sx in (-1.4, 1.0):
        mb.box(0.2, 0.2, 3.4, "wood_dark", pos=(-0.2 + sx, -2.7, 0.5))
    funnel_in(mb, port_x(6, 3), 2.55, 2.9, 0.8)
    mb.box(1.2, 0.5, 0.16, "iron", pos=(port_x(6, 3), -2.7, 0.6))
    mb.light((-0.9, 1.0, 3.8), color=(1.0, 0.55, 0.2), brightness=1.3, range_=14)


def enchanter(mb):
    stone_plinth(mb, 6, 6, 0.4, "stone_dark")
    mb.cyl(2.4, 2.4, 0.08, "roof_purple", pos=(0, 0, 0.46), segs=16, smooth=False, grad=(0.4, 0.6))           # carpet
    mb.cyl(2.0, 2.0, 0.04, "brass", pos=(0, 0, 0.54), segs=16, smooth=False)
    mb.cyl(1.9, 1.9, 0.05, "roof_purple", pos=(0, 0, 0.56), segs=16, smooth=False, grad=(0.45, 0.6))
    mb.box(2.2, 1.6, 2.6, "wood_dark", pos=(0, 0.5, 0.5), taper=(0.75, 0.8))                                  # lectern foot
    for z in (0.9, 2.6):
        mb.box(2.0 - (z - 0.9) * 0.25, 1.5 - (z - 0.9) * 0.2, 0.16, "brass", pos=(0, 0.5, z))
    with mb.at(T(0, 0.3, 3.2), R("X", -20)):                                                                  # desk + open book
        mb.box(3.2, 2.2, 0.3, "wood_mid")
        mb.box(3.3, 0.3, 0.45, "wood_dark", pos=(0, -1.05, 0.1))
        for sx in (-1, 1):
            with mb.at(T(sx * 0.72, 0, 0.3), R("Y", -sx * 6)):
                mb.box(1.35, 1.7, 0.2, "plaster_cream", tone=0.05)
                for i in range(5):
                    mb.box(0.95, 0.06, 0.02, "iron", pos=(0, 0.55 - i * 0.26, 0.2), tone=0.2)
        mb.box(0.12, 1.75, 0.3, "cloth_red", pos=(0, 0, 0.3))
        mb.box(0.12, 0.6, 0.04, "cloth_red", pos=(0.3, -1.1, 0.42))
    for sx in (-1, 1):                                                                                        # crystal pylons
        x, y = sx * 2.2, 1.9
        mb.lathe([(0.5, 0.4), (0.3, 0.9), (0.22, 3.8), (0.4, 4.1)], "brass", segs=6, pos=(x, y, 0), smooth=False)
        crystal(mb, x, y, 4.3, 1.3, 0.42, "flower_purple", 5)
        for k in range(3):
            a = TAU * k / 3
            tube(mb, (x + 0.4 * math.cos(a), y + 0.4 * math.sin(a), 4.1), (x + 0.3 * math.cos(a), y + 0.3 * math.sin(a), 4.8), 0.05, "brass", segs=4)
    for k in range(5):                                                                                        # floating runes
        a = TAU * k / 5
        with mb.at(T(1.5 * math.cos(a), 0.3 + 1.2 * math.sin(a), 5.3 + 0.2 * (k % 2)), R("X", 90)):
            rune_plate(mb, 0, 0, 0, "glass_light", 0.4, 36 * k)
    mb.cyl(0.5, 0.55, 0.9, "stone_grey", pos=(-2.2, -1.9, 0.4), segs=6, smooth=False)                         # ink stand
    mb.cyl(0.3, 0.3, 0.3, "iron", pos=(-2.2, -1.9, 1.3), segs=6)
    tube(mb, (-2.2, -1.9, 1.5), (-1.9, -1.5, 2.6), 0.04, "plaster_white", segs=4)
    fluid_stub(mb, -1, 1.0, 1.3, w=6)
    funnel_in(mb, port_x(6, 3), 2.55, 1.6, 0.8)
    chute_out(mb, port_x(6, 3), -2.6, 0.9, 0.85)
    mb.light((0, 0.4, 4.8), color=(0.75, 0.5, 1.0), brightness=1.0, range_=14)


def infuser(mb):
    stone_plinth(mb, 6, 6)
    wood_frame(mb, 5.0, 3.4, 2.0, inset=0.4, post=0.45)
    planks(mb, 5.2, 3.6, 2.0, "wood_mid")
    cols = ("roof_orange", "flower_blue")
    for i, sx in enumerate((-1, 1)):                                                                          # two retorts
        x = sx * 1.55
        mb.cyl(0.5, 0.6, 0.5, "iron", pos=(x, 0.6, 2.3), segs=8, smooth=False)
        fire_bed(mb, x, 0.6, 2.3, 0.35)
        mb.lathe([(0.3, 3.0), (0.95, 3.4), (1.05, 4.3), (0.7, 5.0), (0.25, 5.3), (0.25, 5.9)], "glass_light", segs=10, pos=(x, 0.6, 0),
                 smooth=False, grad=(0.35, 0.92))
        mb.lathe([(0.0, 3.05), (0.9, 3.42), (0.98, 4.0), (0.0, 4.02)], cols[i], segs=10, pos=(x, 0.6, 0.01), smooth=False, grad=(0.45, 0.9))
        for k in range(3):
            a = TAU * k / 3
            tube(mb, (x + 0.7 * math.cos(a), 0.6 + 0.7 * math.sin(a), 2.3), (x + 0.5 * math.cos(a), 0.6 + 0.5 * math.sin(a), 3.2), 0.07, "iron", segs=4)
        pipe_run(mb, [(x, 0.6, 5.9), (x, 0.6, 6.4), (x * 0.3, 0.2, 6.5), (0, -0.2, 5.6)], 0.12, "brass")
    mb.lathe([(0.3, 2.3), (0.9, 2.6), (1.0, 3.4), (0.75, 4.2), (0.45, 4.4), (0.5, 5.6)], "brass", segs=10, pos=(0, -0.5, 0), smooth=False,
             grad=(0.3, 0.8))                                                                                 # fusion vessel
    band(mb, 1.03, 3.3, 0.16, "iron", 10, pos=(0, -0.5, 0), bolts=5)
    mb.box(0.5, 0.12, 0.7, "glass_lit", pos=(0, -1.48, 2.9), grad=(0.6, 0.95))
    with mb.at(T(0.75, -1.35, 4.1)):
        gauge(mb, 0.3)
    with mb.at(T(-0.6, -0.2, 6.0)):
        valve(mb, 0.32)
    tube(mb, (0, -1.3, 2.6), (0, -1.75, 2.45), 0.14, "brass", segs=6, flanges=True)
    for i in range(3):
        bottle(mb, -2.1 + i * 0.45, -1.4, 2.3, ("flower_purple", "glass_light")[i % 2], 0.7)
    funnel_in(mb, port_x(6, 3), 2.5, 2.0, 0.85)
    chute_out(mb, port_x(6, 3), -2.55, 1.9, 0.9)
    mb.light((0, -0.5, 4.6), color=(0.9, 0.6, 1.0), brightness=0.9, range_=12)


def crystal_refiner(mb):
    stone_plinth(mb, 6, 6, color="stone_dark")
    wood_frame(mb, 4.4, 4.4, 2.0, inset=0.4, post=0.5)
    planks(mb, 4.6, 4.6, 2.0, "wood_mid")
    with mb.at(T(0, 0, 2.5)):                                                                                 # grinding wheel (horizontal)
        mb.cyl(1.7, 1.7, 0.4, "stone_light", segs=16, smooth=False)
        for k in range(8):
            with mb.at(R("Z", 45 * k)):
                mb.box(1.5, 0.06, 0.03, "stone_grey", pos=(0.85, 0, 0.4), tone=-0.12)
        mb.cyl(0.3, 0.3, 0.7, "brass", pos=(0, 0, 0.3), segs=6, smooth=False)
    band(mb, 1.72, 2.6, 0.14, "iron", 16)
    for k in range(3):                                                                                        # brass arms holding the crystal
        a = TAU * k / 3 + 0.5
        pipe_run(mb, [(2.1 * math.cos(a), 2.1 * math.sin(a), 2.3), (2.0 * math.cos(a), 2.0 * math.sin(a), 4.6),
                      (0.7 * math.cos(a), 0.7 * math.sin(a), 5.1)], 0.11, "brass", segs=5)
        mb.box(0.3, 0.3, 0.3, "iron", pos=(0.6 * math.cos(a), 0.6 * math.sin(a), 4.95))
    crystal(mb, 0, 0, 3.6, 2.4, 0.75, "glass_light", 6)
    for k in range(4):
        a = TAU * k / 4 + 0.3
        crystal(mb, 1.2 * math.cos(a), 1.2 * math.sin(a), 2.9, 0.5, 0.16, "flower_blue", 4)
    with mb.at(T(-2.35, 0.6, 1.4), R("Y", 90)):                                                               # drive wheel + belt
        gear(mb, 0.95, 0.2, "wood_mid", teeth=12, hub="iron")
    with mb.at(T(-1.2, 0.6, 2.2), R("Y", 90)):
        gear(mb, 0.45, 0.2, "brass", teeth=7)
    mb.beam((-2.5, 0.6, 1.4), (-2.5, -0.5, 1.9), 0.14, 0.14, "iron")
    mb.cyl(0.14, 0.14, 0.5, "wood_light", pos=(-2.5, -0.5, 1.9), segs=5)
    mb.box(0.9, 0.9, 0.7, "wood_dark", pos=(2.2, -2.2, 0.5))                                                  # water drip bucket
    mb.box(0.75, 0.75, 0.06, "water", pos=(2.2, -2.2, 1.2))
    for i in range(5):
        crystal(mb, 2.0 + mb.jitter(0.3), 2.1 + mb.jitter(0.3), 0.5, 0.5 + 0.1 * i, 0.18, ("glass_light", "flower_blue")[i % 2], 4)
    mb.lathe([(0.4, 0.0), (0.5, 1.0), (0.3, 1.1)], "glass_light", segs=6, pos=(-1.7, -1.9, 2.3), smooth=False)        # loupe stand
    funnel_in(mb, port_x(6, 3), 2.5, 2.0, 0.85)
    chute_out(mb, port_x(6, 3), -2.55, 1.9, 0.9)
    mb.light((0, 0, 4.8), color=(0.6, 0.9, 1.0), brightness=1.1, range_=14)


def advanced_cauldron(mb):
    stone_plinth(mb, 8, 8, 0.6, "stone_dark")
    for k in range(12):                                                                                       # ring wall
        with mb.at(R("Z", 30 * k)):
            mb.box(0.9, 1.65, 1.0, ("stone_grey", "stone_light", "stone_warm")[k % 3], pos=(2.95, 0, 0.6), taper=0.92, tone=mb.jitter(0.05))
            if k % 3 == 0:
                mb.box(0.08, 0.5, 0.5, "flower_purple", pos=(3.42, 0, 0.85), grad=(0.5, 0.95))
    fire_bed(mb, 0, 0, 0.66, 1.4)
    mb.lathe([(1.4, 1.5), (2.5, 2.1), (2.95, 3.6), (2.6, 4.9), (2.85, 5.25), (2.5, 5.25), (2.35, 4.7)], "iron", segs=14, smooth=False,
             grad=(0.28, 0.7))
    band(mb, 2.98, 3.5, 0.24, "brass", 14, bolts=14)
    rivets(mb, 2.7, 5.0, 14, "brass", 0.14)
    for k in range(3):                                                                                        # clawed feet
        a = TAU * k / 3 + 0.4
        mb.beam((2.3 * math.cos(a), 2.3 * math.sin(a), 0.6), (1.7 * math.cos(a), 1.7 * math.sin(a), 1.9), 0.5, 0.5, "iron")
    mb.cyl(2.35, 2.35, 0.12, "flower_purple", pos=(0, 0, 4.7), segs=14, smooth=False, grad=(0.5, 0.88))
    for bx, by, r in ((0.9, 0.5, 0.34), (-0.8, -0.3, 0.26), (0.1, -1.1, 0.2), (-0.3, 1.0, 0.3)):
        mb.blob(r, "leaf_pink", pos=(bx, by, 4.84), level=0, noise=0.0, scale=(1, 1, 0.55), grad=(0.6, 0.98))
    for k in range(4):                                                                                        # four pylons with crystals and arcs
        a = math.pi / 2 * k + math.pi / 4
        x, y = 3.35 * math.cos(a), 3.35 * math.sin(a)
        mb.lathe([(0.55, 0.6), (0.34, 1.2), (0.26, 6.6), (0.5, 7.0)], "brass", segs=6, pos=(x, y, 0), smooth=False, grad=(0.3, 0.8))
        band(mb, 0.36, 3.0, 0.18, "iron", 6, pos=(x, y, 0))
        crystal(mb, x, y, 7.2, 1.5, 0.48, ("glass_light", "flower_purple")[k % 2], 5)
        pipe_run(mb, [(x, y, 6.4), (x * 0.75, y * 0.75, 7.3), (x * 0.3, y * 0.3, 7.6)], 0.09, "brass", segs=4)
    mb.lathe([(0.0, 7.4), (0.55, 7.9), (0.4, 8.6), (0.0, 9.2)], "flower_purple", segs=6, smooth=False, grad=(0.3, 0.98))     # heart crystal
    for k in range(8):
        a = TAU * k / 8
        with mb.at(T(1.5 * math.cos(a), 1.5 * math.sin(a), 6.2 + 0.25 * (k % 2)), R("Z", math.degrees(a)), R("Y", 90)):
            rune_plate(mb, 0, 0, 0, "glass_light", 0.42)
    with mb.at(T(0, -3.06, 3.0)):
        gauge(mb, 0.42)
    with mb.at(T(-3.1, 1.0, 2.2), R("Y", 90)):
        valve(mb, 0.45)
    fluid_stub(mb, -1, 1.0, 1.5, w=8)
    tube(mb, (-3.2, 1.0, 1.5), (-2.4, 0.8, 2.6), 0.2, "brass", segs=6)
    funnel_in(mb, port_x(8, 4), 3.5, 2.0, 0.95)
    tube(mb, (port_x(8, 4), 3.2, 2.3), (-0.7, 2.3, 4.6), 0.2, "wood_light", segs=5)
    chute_out(mb, port_x(8, 4), -3.55, 1.1, 1.0)
    mb.light((0, 0, 6.2), color=(0.8, 0.5, 1.0), brightness=1.5, range_=18)
    mb.light((0, 0, 1.2), color=(1.0, 0.6, 0.25), brightness=0.8, range_=10)


def herb_grower(mb):
    for i, (x, y, w, d) in enumerate(((0, -2.75, 5.8, 0.3), (0, 2.75, 5.8, 0.3), (-2.75, 0, 0.3, 5.2), (2.75, 0, 0.3, 5.2))):   # raised bed
        mb.box(w, d, 1.1, "wood_mid", pos=(x, y, 0), tone=mb.jitter(0.05))
        mb.box(w, d, 0.16, "wood_dark", pos=(x, y, 1.1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(0.45, 0.45, 1.5, "wood_dark", pos=(sx * 2.7, sy * 2.7, 0))
            mb.lathe([(0.0, 1.5), (0.25, 1.65), (0.0, 1.9)], "brass", segs=4, pos=(sx * 2.7, sy * 2.7, 0), smooth=False)
    mb.box(5.2, 5.2, 0.9, "dirt_dark", pos=(0, 0, 0.1))
    for iy in range(3):                                                                                       # furrows + plants
        y = -1.6 + iy * 1.6
        mb.box(4.8, 0.9, 0.2, "dirt", pos=(0, y, 0.95), tone=mb.jitter(0.04))
        for ix in range(4):
            x = -1.8 + ix * 1.2 + mb.jitter(0.12)
            h = 0.9 + mb.jitter(0.25)
            mb.lathe([(0.07, 0.0), (0.05, h)], "leaf_dark", segs=3, pos=(x, y, 1.1), smooth=False)
            for k in range(4):
                a = TAU * k / 4 + ix + iy
                mb.blob(0.3, ("leaf_green", "leaf_lime")[(ix + iy + k) % 2], pos=(x + 0.28 * math.cos(a), y + 0.28 * math.sin(a), 1.25 + h * (0.4 + 0.18 * k)),
                        level=0, noise=0.2, scale=(1.1, 1.1, 0.5), grad=(0.3, 0.9))
            if (ix + iy) % 3 == 0:
                mb.blob(0.13, "flower_white", pos=(x, y, 1.2 + h), level=0, noise=0.0)
    for sx in (-1, 1):                                                                                        # trellis with glass roof
        mb.box(0.24, 0.24, 4.6, "wood_dark", pos=(sx * 2.6, 2.6, 1.3))
        mb.beam((sx * 2.6, 2.6, 5.7), (sx * 2.6, -0.4, 4.6), 0.2, 0.2, "wood_dark")
    mb.beam((-2.6, 2.6, 5.8), (2.6, 2.6, 5.8), 0.26, 0.26, "wood_dark")
    for i in range(4):
        x = -1.95 + i * 1.3
        mb.beam((x, 2.6, 5.75), (x, -0.4, 4.65), 1.1, 0.06, "glass_light", grad=(0.4, 0.9))
    pipe_run(mb, [(-2.85, 1.0, 1.3), (-2.3, 1.0, 1.9), (-2.3, 1.0, 4.9), (2.2, 1.0, 4.9)], 0.11, "brass", segs=5)          # sprinkler
    for i in range(4):
        mb.cyl(0.1, 0.16, 0.25, "brass", pos=(-1.6 + i * 1.2, 1.0, 4.55), segs=5)
    fluid_stub(mb, -1, 1.0, 1.3, w=6)
    mb.box(0.9, 0.9, 0.6, "wood_light", pos=(port_x(6, 3) + 1.9, 2.3, 1.26), taper=1.15)                     # seed tray (input)
    funnel_in(mb, port_x(6, 3), 2.6, 1.3, 0.7)
    chute_out(mb, port_x(6, 3), -2.62, 1.25, 0.9)
    mb.box(1.0, 0.7, 0.7, "thatch", pos=(port_x(6, 3) - 1.7, -2.3, 1.26), taper=1.1)                          # harvest basket
    mb.blob(0.4, "leaf_green", pos=(port_x(6, 3) - 1.7, -2.3, 2.05), level=0, noise=0.2, scale=(1.2, 0.8, 0.5))


def quarry_drill(mb):
    stone_plinth(mb, 6, 6, color="stone_dark")
    mb.lathe([(1.3, 0.5), (1.5, 0.8), (1.0, 0.8), (0.8, 0.52)], "rock_dark", segs=8, smooth=False)            # bore hole rim
    legs = []
    for k in range(4):                                                                                        # derrick
        a = math.pi / 2 * k + math.pi / 4
        p0 = (2.5 * math.cos(a), 2.5 * math.sin(a), 0.5)
        p1 = (0.5 * math.cos(a), 0.5 * math.sin(a), 7.4)
        legs.append((p0, p1))
        mb.beam(p0, p1, 0.4, 0.4, "wood_dark")
        mb.box(0.8, 0.8, 0.25, "iron", pos=(p0[0], p0[1], 0.5))
    for f in (0.3, 0.6):
        ring = [tuple(a + (b - a) * f for a, b in zip(p0, p1)) for p0, p1 in legs]
        for i in range(4):
            mb.beam(ring[i], ring[(i + 1) % 4], 0.22, 0.22, "wood_mid")
    for i in range(4):
        a, b = legs[i], legs[(i + 1) % 4]
        mb.beam(tuple(x + (y - x) * 0.3 for x, y in zip(a[0], a[1])), tuple(x + (y - x) * 0.6 for x, y in zip(b[0], b[1])), 0.16, 0.16, "wood_mid")
    mb.box(1.6, 1.6, 0.4, "wood_dark", pos=(0, 0, 7.3))
    mb.cyl(0.75, 0.75, 1.3, "iron", pos=(0, 0, 5.6), segs=8, smooth=False)                                    # drive head
    band(mb, 0.78, 5.8, 0.16, "brass", 8, bolts=8)
    with mb.at(T(0, 0, 7.0)):
        gear(mb, 0.9, 0.22, teeth=12)
    with mb.at(T(1.2, 0, 7.0), R("Z", 15)):
        gear(mb, 0.5, 0.22, "iron", teeth=7, hub="brass")
    mb.lathe([(0.3, 1.9), (0.3, 5.6)], "iron", segs=6)                                                        # drill string
    for i in range(7):                                                                                        # spiral bit
        with mb.at(T(0, 0, 1.9 + i * 0.5), R("Z", 60 * i)):
            mb.box(1.0, 0.16, 0.14, "stone_light", pos=(0, 0, 0))
    mb.lathe([(0.0, 0.6), (0.55, 1.5), (0.3, 1.9)], "stone_light", segs=6, smooth=False)
    mb.box(1.1, 1.0, 1.5, "brick", pos=(2.2, 1.9, 0.5), taper=0.9)                                            # firebox
    mb.box(0.6, 0.12, 0.5, "glass_lit", pos=(2.2, 1.36, 0.9), grad=(0.6, 0.95))
    mb.cyl(0.22, 0.2, 2.2, "iron", pos=(2.2, 2.1, 2.0), segs=6)
    tube(mb, (2.2, 1.9, 1.8), (0.7, 0.4, 6.0), 0.12, "brass", segs=5, flanges=True)
    for i in range(5):
        mb.blob(0.45 + 0.08 * (i % 2), ("rock", "rock_dark", "roof_orange")[i % 3], pos=(-1.9 + mb.jitter(0.5), -2.0 + mb.jitter(0.4), 0.8 + 0.1 * i),
                level=0, noise=0.3, scale=(1.1, 1, 0.75))
    mb.box(1.6, 1.1, 0.8, "wood_mid", pos=(-2.0, 2.0, 0.5), taper=1.08)                                       # ore cart
    for sx in (-1, 1):
        with mb.at(T(-2.0 + sx * 0.6, 2.62, 0.75), R("X", 90)):
            mb.cyl(0.32, 0.32, 0.12, "iron", pos=(0, 0, -0.06), segs=8, smooth=False)
    chute_out(mb, port_x(6, 3), -2.6, 0.95, 0.9)
    mb.light((2.2, 1.2, 1.2), color=(1.0, 0.6, 0.25), brightness=0.7, range_=8)


def well_pump(mb):
    n = 10
    for k in range(n):                                                                                        # stone ring
        with mb.at(R("Z", 36 * k)):
            mb.box(0.5, 1.1, 0.85, ("stone_grey", "stone_light", "stone_warm")[k % 3], pos=(1.5, 0, 0), taper=0.92, tone=mb.jitter(0.05))
            mb.box(0.5, 1.05, 0.8, ("stone_light", "stone_grey")[k % 2], pos=(1.5, 0, 0.85), taper=0.92, tone=mb.jitter(0.05))
    mb.cyl(1.3, 1.3, 0.1, "water", pos=(0, 0, 1.0), segs=n, smooth=False, grad=(0.4, 0.8))
    mb.cyl(0.4, 0.34, 3.6, "iron", pos=(0, 0.8, 0.9), segs=8)                                                 # pump column
    band(mb, 0.42, 1.8, 0.14, "brass", 8, pos=(0, 0.8, 0), bolts=4)
    mb.lathe([(0.34, 4.5), (0.5, 4.7), (0.3, 5.0)], "iron", segs=8, pos=(0, 0.8, 0), smooth=False)
    mb.beam((0, 0.8, 4.6), (0, -1.1, 5.5), 0.18, 0.26, "iron")                                                # handle
    mb.beam((-0.35, -1.1, 5.5), (0.35, -1.1, 5.5), 0.16, 0.16, "wood_light")
    mb.beam((0, 0.3, 4.75), (0, 0.3, 3.9), 0.1, 0.1, "iron")
    pipe_run(mb, [(0, 0.8, 3.6), (1.0, 0.8, 3.6), (1.0, 0.8, 1.3), (1.9, 1.0, 1.3)], 0.2, "brass")            # outlet to the right edge
    with mb.at(T(1.0, 0.45, 2.5), R("X", 90)):
        valve(mb, 0.34)
    with mb.at(T(-0.45, 0.45, 3.0)):
        gauge(mb, 0.3)
    fluid_stub(mb, 1, 1.0, 1.3, "roof_orange")
    mb.lathe([(0.45, 0.0), (0.55, 0.9)], "wood_mid", segs=7, pos=(-1.3, -1.35, 0), smooth=False)              # bucket
    band(mb, 0.56, 0.6, 0.1, "iron", 7, pos=(-1.3, -1.35, 0))


# ====================================================================== logistics
def _belt_frame(mb):
    for sx in (-1, 1):
        mb.box(0.2, 2.0, 0.55, "wood_dark", pos=(sx * 0.8, 0, 0))
        for y in (-0.7, 0.7):
            mb.box(0.3, 0.26, 0.12, "iron", pos=(sx * 0.8, y, 0.55))


def wooden_belt(mb):
    _belt_frame(mb)
    for i in range(6):                                                                                        # slats
        mb.box(1.36, 0.28, 0.1, "wood_light", pos=(0, -0.83 + i * 0.333, 0.52), tone=mb.jitter(0.08))
    for y in (-0.78, 0.78):                                                                                   # end rollers
        with mb.at(T(0, y, 0.36), R("Y", 90)):
            mb.cyl(0.2, 0.2, 1.4, "wood_mid", pos=(0, 0, -0.7), segs=6)
    for sx in (-1, 1):
        mb.box(0.1, 1.9, 0.08, "iron", pos=(sx * 0.5, 0, 0.44))
    mb.lathe([(0.0, 0.0), (0.26, 0.03), (0.0, 0.06)], "brass", segs=3, pos=(0, -0.2, 0.63), phase=-math.pi / 2, smooth=False)


def belt_turn(mb):
    mb.box(1.9, 1.9, 0.5, "wood_dark")
    for i in range(5):                                                                                        # fanned slats: back (+Y) to left (-X)
        a = math.radians(i * 22.5)
        with mb.at(T(-0.78, 0.78, 0.5), R("Z", -90 + i * 22.5)):
            mb.box(1.35, 0.3, 0.1, "wood_light", pos=(0.9, 0, 0.02), tone=mb.jitter(0.08), taper=(1.0, 1.0))
    mb.cyl(0.14, 0.14, 0.5, "iron", pos=(-0.78, 0.78, 0.4), segs=6, smooth=False)
    for k in range(4):                                                                                        # outer guide rail
        a0, a1 = math.radians(-90 + k * 22.5), math.radians(-90 + (k + 1) * 22.5)
        mb.beam((-0.8 + 1.62 * math.cos(a0), 0.8 + 1.62 * math.sin(a0), 0.75), (-0.8 + 1.62 * math.cos(a1), 0.8 + 1.62 * math.sin(a1), 0.75),
                0.12, 0.3, "wood_mid")
    with mb.at(T(-0.35, 0.3, 0.63), R("Z", 90)):
        mb.lathe([(0.0, 0.0), (0.24, 0.03), (0.0, 0.06)], "brass", segs=3, phase=-math.pi / 2, smooth=False)


def input_hopper(mb):
    wood_frame(mb, 1.7, 1.7, 0.9, inset=0.18, post=0.24, braces=False)
    mb.lathe([(0.3, 0.7), (0.86, 1.7), (0.92, 1.8), (0.76, 1.8), (0.22, 0.8)], "wood_light", segs=4, phase=math.pi / 4, smooth=False)
    mb.lathe([(0.94, 1.76), (0.94, 1.88)], "brass", segs=4, phase=math.pi / 4, smooth=False)
    for k in range(4):
        with mb.at(R("Z", 90 * k)):
            mb.box(0.1, 0.9, 0.06, "iron", pos=(0.6, 0, 1.3))
    mb.beam((0, 0, 0.75), (0, -0.9, 0.5), 0.8, 0.1, "wood_mid")                                               # outlet to the front
    for sx in (-1, 1):
        mb.beam((sx * 0.4, 0, 0.85), (sx * 0.4, -0.9, 0.6), 0.08, 0.26, "wood_dark")
    with mb.at(T(0.86, 0, 0.75), R("Y", 90)):
        gear(mb, 0.3, 0.1, teeth=6)
    mb.box(0.5, 0.12, 0.3, "brass", pos=(0, -0.92, 0.3))


def _hub(mb, color="brass"):
    mb.box(1.9, 1.9, 0.5, "wood_dark")
    mb.box(1.7, 1.7, 0.16, "wood_mid", pos=(0, 0, 0.5))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(0.3, 0.3, 0.14, "iron", pos=(sx * 0.75, sy * 0.75, 0.6))


def splitter(mb):
    _hub(mb)
    mb.cyl(0.55, 0.6, 0.5, "iron", pos=(0, 0, 0.66), segs=8, smooth=False)
    with mb.at(T(0, 0, 1.25)):
        gear(mb, 0.55, 0.16, teeth=8)
    mb.beam((0, 0, 1.3), (0.0, -0.6, 1.55), 0.3, 0.1, "wood_light")                                           # deflector paddle
    for a in (0, -90, 90):                                                                                    # three exits: front, right, left
        with mb.at(R("Z", a)):
            mb.box(0.8, 0.5, 0.1, "wood_light", pos=(0, -0.7, 0.66))
            mb.lathe([(0.0, 0.0), (0.2, 0.03), (0.0, 0.06)], "brass", segs=3, pos=(0, -0.75, 0.77), phase=-math.pi / 2, smooth=False)
    mb.box(0.7, 0.3, 0.3, "wood_mid", pos=(0, 0.8, 0.66))


def merger(mb):
    _hub(mb)
    mb.lathe([(0.85, 0.66), (0.4, 1.3), (0.4, 1.5), (0.3, 1.5), (0.3, 1.3), (0.7, 0.7)], "iron", segs=8, smooth=False)
    band(mb, 0.87, 0.66, 0.12, "brass", 8, bolts=4)
    for a in (180, -90, 90):                                                                                  # three entries: back, right, left
        with mb.at(R("Z", a)):
            mb.beam((0, -0.95, 1.2), (0, -0.4, 0.9), 0.7, 0.08, "wood_light")
    mb.box(0.8, 0.5, 0.1, "wood_light", pos=(0, -0.7, 0.66))
    mb.lathe([(0.0, 0.0), (0.22, 0.03), (0.0, 0.06)], "brass", segs=3, pos=(0, -0.75, 0.77), phase=-math.pi / 2, smooth=False)


def filter_sorter(mb):
    _hub(mb)
    mb.box(1.3, 1.3, 1.0, "plaster_cream", pos=(0, 0, 0.66), taper=0.85)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.beam((sx * 0.65, sy * 0.65, 0.66), (sx * 0.55, sy * 0.55, 1.66), 0.14, 0.14, "wood_dark")
    mb.box(1.25, 1.25, 0.14, "wood_dark", pos=(0, 0, 1.66))
    mb.lathe([(0.0, 1.9), (0.4, 2.25), (0.3, 2.7), (0.0, 3.0)], "flower_blue", segs=5, smooth=False, grad=(0.3, 0.98))        # sorting eye
    for k in range(3):
        a = TAU * k / 3
        tube(mb, (0.5 * math.cos(a), 0.5 * math.sin(a), 1.8), (0.25 * math.cos(a), 0.25 * math.sin(a), 2.3), 0.05, "brass", segs=4)
    mb.box(0.7, 0.1, 0.5, "glass_light", pos=(0, -0.62, 0.95), grad=(0.4, 0.9))                               # whitelist plate
    mb.box(0.3, 0.06, 0.3, "flower_blue", pos=(0, -0.68, 1.05))
    mb.box(0.8, 0.5, 0.1, "wood_light", pos=(0, -0.72, 0.5))                                                  # front = accepted
    with mb.at(R("Z", -90)):
        mb.box(0.8, 0.5, 0.1, "wood_mid", pos=(0, -0.72, 0.5))                                                # left = everything else
    mb.light((0, 0, 2.4), color=(0.5, 0.7, 1.0), brightness=0.5, range_=7)


def vertical_lift(mb):
    mb.box(1.9, 1.9, 0.5, "wood_dark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(0.24, 0.24, 11.4, "wood_dark", pos=(sx * 0.78, sy * 0.78, 0.5), tone=mb.jitter(0.04))
            mb.box(0.36, 0.36, 0.2, "iron", pos=(sx * 0.78, sy * 0.78, 0.5))
    for i, z in enumerate((2.6, 5.0, 7.4, 9.8)):                                                              # cross bracing on three sides
        for a in (0, 90, 180):
            with mb.at(R("Z", a)):
                mb.beam((-0.78, 0.78, z - 1.0), (0.78, 0.78, z + 1.0) if i % 2 else (0.78, 0.78, z - 1.0), 0.12, 0.12, "wood_mid")
    mb.box(1.9, 1.9, 0.3, "wood_mid", pos=(0, 0, 11.7))
    with mb.at(T(0, 0.3, 11.2), R("Y", 90)):                                                                  # pulley
        gear(mb, 0.5, 0.16, "iron", teeth=8, hub="brass")
    mb.box(0.08, 0.08, 8.6, "wood_pale", pos=(0, 0.3, 2.7))                                                   # rope
    mb.box(1.3, 1.3, 0.16, "wood_light", pos=(0, 0, 2.4))                                                     # platform
    for sx in (-1, 1):
        mb.box(0.1, 1.3, 0.4, "wood_dark", pos=(sx * 0.6, 0, 2.56))
    mb.box(0.6, 0.5, 0.5, "wood_light", pos=(0, 0, 2.56), tone=0.06)                                          # crate on the platform
    mb.box(0.7, 0.7, 1.2, "iron", pos=(0, 0.3, 0.5))                                                          # counterweight
    mb.beam((0, -0.86, 12.0), (0, -0.92, 11.6), 0.9, 0.1, "wood_light")                                        # upper exit lip (front)
    with mb.at(T(0.9, -0.4, 1.4), R("Y", 90)):
        gear(mb, 0.36, 0.1, teeth=6)


def magical_gate(mb):
    mb.box(1.9, 1.9, 0.4, "stone_dark")
    for k in range(4):
        with mb.at(R("Z", 90 * k)):
            mb.box(0.5, 0.5, 0.2, "stone_light", pos=(0.7, 0.7, 0.4), taper=0.8)
    arch = []
    n = 8
    for i in range(n + 1):
        a = math.pi * i / n
        arch.append((0.72 * math.cos(a), 0.0, 1.5 + 1.35 * math.sin(a)))
    for sx in (-1, 1):                                                                                        # pillars of stacked stones
        for i in range(3):
            mb.box(0.42, 0.55, 0.38, ("stone_light", "stone_grey", "stone_warm")[i], pos=(sx * 0.72, 0, 0.4 + i * 0.38), tone=mb.jitter(0.05))
    for a, b in zip(arch[:-1], arch[1:]):                                                                     # voussoirs
        mb.beam(a, b, 0.55, 0.4, "stone_light", up=(0, 1, 0), tone=mb.jitter(0.07))
    mb.box(0.4, 0.6, 0.45, "brass", pos=(0, 0, 2.75), taper=0.7)                                              # keystone
    crystal(mb, 0, 0, 3.15, 0.6, 0.2, "flower_purple", 4)
    pts = [(0.52 * math.cos(math.pi * i / n), 1.5 + 1.1 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    poly = [(-0.52, 0.45), (0.52, 0.45)] + pts
    mb.prism(poly, -0.05, 0.05, "flower_purple", grad=(0.25, 0.98))                                           # portal film
    for k in range(5):
        with mb.at(T(0.3 * math.cos(k * 1.9), -0.09, 1.0 + k * 0.33), R("X", 90)):
            rune_plate(mb, 0, 0, 0, "glass_light", 0.22, 40 * k)
    for sx in (-1, 1):
        mb.box(0.12, 0.12, 0.5, "glass_light", pos=(sx * 0.72, -0.3, 1.0), grad=(0.5, 0.95))
    mb.light((0, 0, 1.9), color=(0.75, 0.5, 1.0), brightness=0.9, range_=10)


def _pipe_node(mb, arms):
    """Pipe piece with a hub and arms towards the given directions (dx, dy)."""
    for dx, dy in arms:
        tube(mb, (0, 0, 0.42), (dx * 1.0, dy * 1.0, 0.42), 0.26, "brass", segs=8)
        with mb.at(T(dx * 0.88, dy * 0.88, 0.42), R("Y", 90) if dx else R("X", 90)):
            mb.cyl(0.38, 0.38, 0.16, "iron", pos=(0, 0, -0.08), segs=8, smooth=False)
            rivets(mb, 0.32, 0.0, 4, "brass", 0.08, math.pi / 4)
    mb.blob(0.36, "brass", pos=(0, 0, 0.42), level=1, noise=0.0)
    mb.box(0.5, 0.5, 0.16, "stone_dark", pos=(0, 0, 0))                                                       # support
    mb.box(0.16, 0.16, 0.2, "iron", pos=(0, 0, 0.14))


def pipe_straight(mb):
    _pipe_node(mb, ((0, 1), (0, -1), (1, 0), (-1, 0)))


def pipe_bend(mb):
    _pipe_node(mb, ((0, 1), (0, -1), (1, 0), (-1, 0)))
    with mb.at(T(0, 0, 0.95)):
        valve(mb, 0.3)


def fluid_tank(mb):
    stone_plinth(mb, 4, 4)
    for k in range(4):                                                                                        # cradle
        a = math.pi / 2 * k + math.pi / 4
        mb.beam((1.6 * math.cos(a), 1.6 * math.sin(a), 0.5), (1.2 * math.cos(a), 1.2 * math.sin(a), 1.4), 0.3, 0.3, "wood_dark")
    mb.lathe([(0.9, 0.9), (1.5, 1.3), (1.62, 2.0), (1.62, 4.2), (1.3, 4.9), (0.5, 5.2), (0.5, 5.5)], "brass", segs=12, smooth=False,
             grad=(0.3, 0.8))
    for z in (1.6, 2.9, 4.1):
        band(mb, 1.65, z, 0.2, "iron", 12, bolts=12)
    mb.box(0.5, 0.14, 2.3, "glass_light", pos=(0, -1.66, 1.75), grad=(0.3, 0.95))                             # level glass
    mb.box(0.36, 0.1, 1.2, "water", pos=(0, -1.72, 1.8), grad=(0.4, 0.8))
    mb.box(0.66, 0.1, 0.16, "iron", pos=(0, -1.68, 1.68))
    mb.box(0.66, 0.1, 0.16, "iron", pos=(0, -1.68, 4.0))
    mb.cyl(0.62, 0.62, 0.16, "iron", pos=(0, 0, 5.5), segs=8, smooth=False)                                   # lid
    rivets(mb, 0.5, 5.7, 8, "brass", 0.1)
    with mb.at(T(0, 0, 5.95)):
        valve(mb, 0.4)
    with mb.at(T(0.9, -1.45, 3.4)):
        gauge(mb, 0.34)
    for side, ring in ((-1, "flower_blue"), (1, "roof_orange")):
        fluid_stub(mb, side, 0.0, 1.2, ring)
    for sy in (-1, 1):
        tube(mb, (0, sy * 1.1, 1.2), (0, sy * 1.92, 1.2), 0.3, "brass", segs=8, flanges=True)
    tube(mb, (1.2, -1.3, 0.9), (1.5, -1.75, 0.75), 0.12, "brass", segs=5)                                     # drain tap
    mb.box(0.3, 0.1, 0.1, "cloth_red", pos=(1.35, -1.55, 1.05))


def storage_crate(mb):
    mb.box(3.3, 3.3, 0.2, "wood_dark")
    for side in range(4):                                                                                     # plank walls
        with mb.at(R("Z", 90 * side)):
            for i in range(4):
                mb.box(0.78, 0.2, 2.7, "wood_light", pos=(-1.2 + i * 0.8, -1.6, 0.2), tone=mb.jitter(0.09))
            mb.beam((-1.6, -1.72, 0.4), (1.6, -1.72, 2.7), 0.3, 0.12, "wood_mid", up=(0, 1, 0))
            mb.box(3.5, 0.14, 0.3, "wood_mid", pos=(0, -1.72, 0.2))
            mb.box(3.5, 0.14, 0.3, "wood_mid", pos=(0, -1.72, 2.6))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(0.36, 0.36, 2.9, "wood_dark", pos=(sx * 1.66, sy * 1.66, 0.1))
            mb.box(0.46, 0.46, 0.12, "iron", pos=(sx * 1.66, sy * 1.66, 2.95))
            mb.box(0.46, 0.46, 0.12, "iron", pos=(sx * 1.66, sy * 1.66, 0.08))
    with mb.at(T(0, -0.25, 2.9), R("X", -14)):                                                                # lid, slightly open
        for i in range(4):
            mb.box(0.8, 3.4, 0.2, "wood_light", pos=(-1.2 + i * 0.8, 0, 0), tone=mb.jitter(0.09))
        for y in (-1.2, 1.2):
            mb.box(3.4, 0.3, 0.1, "iron", pos=(0, y, 0.2))
    mb.box(0.5, 0.14, 0.6, "iron", pos=(0, -1.8, 2.1))                                                        # lock plate
    mb.box(0.2, 0.1, 0.24, "brass", pos=(0, -1.88, 2.25))
    for sx in (-1, 1):
        mb.box(0.12, 0.7, 0.12, "wood_pale", pos=(sx * 1.84, 0, 1.9))                                         # rope handles
    mb.blob(0.7, "leaf_green", pos=(0.5, 0.9, 2.75), level=0, noise=0.25, scale=(1.4, 1, 0.4))                # contents peeking out
    mb.blob(0.35, "flower_red", pos=(-0.6, 1.1, 2.85), level=0, noise=0.1)
    mb.box(0.9, 0.06, 0.6, "plaster_cream", pos=(-0.9, -1.74, 1.1))                                           # label


def shop_shelf(mb):
    for sx in (-1, 1):                                                                                        # side panels with cut-out look
        mb.box(0.3, 1.7, 6.0, "wood_dark", pos=(sx * 2.75, 0, 0), tone=mb.jitter(0.04))
        mb.box(0.36, 1.8, 0.3, "wood_mid", pos=(sx * 2.75, 0, 0))
        mb.lathe([(0.0, 6.0), (0.26, 6.2), (0.0, 6.6)], "brass", segs=4, pos=(sx * 2.75, 0, 0), smooth=False)
    for i in range(6):                                                                                        # back boards
        mb.box(0.9, 0.14, 5.8, "wood_mid", pos=(-2.25 + i * 0.9, 0.78, 0.1), tone=mb.jitter(0.08))
    shelves = (0.35, 2.15, 3.95)
    for z in shelves:
        mb.box(5.4, 1.6, 0.22, "wood_light", pos=(0, 0, z), tone=mb.jitter(0.04))
        mb.box(5.4, 0.12, 0.3, "wood_dark", pos=(0, -0.78, z + 0.1))
        for sx in (-1, 1):
            if z > 1:
                mb.beam((sx * 2.5, 0.6, z - 0.6), (sx * 2.0, -0.4, z), 0.14, 0.14, "iron")
    cols = ("glass_blue", "flower_red", "leaf_lime", "flower_purple", "glass_lit", "roof_orange")
    for row, z in enumerate(shelves):                                                                         # wares
        for i in range(7):
            x = -2.25 + i * 0.75
            kind = (i + row * 2) % 4
            if kind == 0:
                flask(mb, x, 0.05, z + 0.22, "glass_light", 0.5, liquid=cols[(i + row) % 6])
            elif kind == 3 and row == 0:
                mb.box(0.5, 0.5, 0.5, "wood_mid", pos=(x, 0.1, z + 0.22))
                mb.box(0.3, 0.3, 0.1, cols[(i + row) % 6], pos=(x, 0.1, z + 0.72))
            else:
                bottle(mb, x, -0.1 + 0.2 * (i % 2), z + 0.22, cols[(i + row) % 6], 0.62 + 0.1 * (kind % 2))
        for i in range(3):
            mb.box(0.36, 0.04, 0.22, "plaster_cream", pos=(-1.9 + i * 1.9, -0.85, z + 0.02))                  # price tags
    mb.box(5.9, 1.9, 0.2, "wood_dark", pos=(0, 0, 5.85))                                                      # cornice + sign
    mb.box(3.0, 0.2, 0.95, "wood_light", pos=(0, -0.8, 6.05))
    mb.box(3.2, 0.24, 0.14, "brass", pos=(0, -0.8, 6.0))
    mb.box(3.2, 0.24, 0.14, "brass", pos=(0, -0.8, 6.95))
    mb.blob(0.3, "cloth_yellow", pos=(0, -0.92, 6.52), level=0, noise=0.0, scale=(1, 0.3, 1))
    n = 7
    for i in range(n):
        x = -2.7 + 5.4 * (i + 0.5) / n
        mb.beam((x, 0.6, 7.1), (x, -0.98, 6.75), 5.4 / n, 0.08, ("cloth_red", "cloth_white")[i % 2], grad=(0.4, 0.66))
    mb.cyl(0.35, 0.3, 0.45, "brass", pos=(2.3, -0.3, 0.57), segs=8)                                           # coin bowl
    for i in range(3):
        mb.cyl(0.12, 0.12, 0.04, "cloth_yellow", pos=(2.3 + 0.08 * i, -0.3 - 0.05 * i, 1.02 + 0.04 * i), segs=6)
    mb.light((0, -0.9, 5.4), brightness=0.6, range_=10)


MACHINES = {
    "mach_kettle": kettle, "mach_grinder": grinder, "mach_saw": saw, "mach_crusher": crusher, "mach_furnace": furnace,
    "mach_glassbench": glassbench, "mach_extractor": extractor, "mach_bottler": bottler, "mach_mixer": mixer,
    "mach_runetable": runetable, "mach_forge": forge, "mach_enchanter": enchanter, "mach_infuser": infuser,
    "mach_crystal_refiner": crystal_refiner, "mach_advanced_cauldron": advanced_cauldron, "mach_herb_grower": herb_grower,
    "mach_quarry_drill": quarry_drill, "mach_well_pump": well_pump,
    "logi_wooden_belt": wooden_belt, "logi_belt_turn": belt_turn, "logi_input_hopper": input_hopper,
    "logi_splitter": splitter, "logi_merger": merger, "logi_filter_sorter": filter_sorter,
    "logi_vertical_lift": vertical_lift, "logi_magical_gate": magical_gate, "logi_pipe_straight": pipe_straight,
    "logi_pipe_bend": pipe_bend, "logi_fluid_tank": fluid_tank, "logi_storage_crate": storage_crate,
    "logi_shop_shelf": shop_shelf,
}
