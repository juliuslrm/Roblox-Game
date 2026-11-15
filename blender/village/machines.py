"""Gameplay assets: machines, storage and logistics parts of the workshop.

Separate from the 91 village assets (own registry, own build script).  Ids match
`modelAssetId` in roblox/gameplay/shared/Machines.lua.  Conventions as everywhere:
studs, origin = centre of the footprint on the floor, front = -Y (Roblox +Z).
Footprint = grid cells x 2 studs; meshes stay inside it.
"""
import math

from .meshkit import T, R


def _base(mb, w, d, color="stone_grey", h=0.5):
    mb.box(w - 0.3, d - 0.3, h, color, taper=0.96)


def _legs(mb, w, d, h, color="wood_dark", inset=0.5):
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(0.45, 0.45, h, color, pos=(sx * (w / 2 - inset), sy * (d / 2 - inset), 0))


def _table(mb, w, d, h=2.6, top="wood_light"):
    _legs(mb, w, d, h)
    mb.box(w - 0.3, d - 0.3, 0.4, top, pos=(0, 0, h))
    return h + 0.4


def kettle(mb):
    _base(mb, 4, 4)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        mb.beam((1.2 * math.cos(a), 1.2 * math.sin(a), 0.5), (0.9 * math.cos(a), 0.9 * math.sin(a), 1.4), 0.3, 0.3, "iron")
    mb.blob(0.7, "roof_orange", pos=(0, 0, 0.8), level=0, noise=0.3, scale=(1.3, 1.3, 0.5), grad=(0.5, 0.9))
    mb.lathe([(0.9, 1.3), (1.55, 1.9), (1.7, 2.8), (1.45, 3.5), (1.6, 3.7), (1.3, 3.7), (1.25, 3.3)], "iron", segs=10, smooth=False)
    mb.cyl(1.25, 1.25, 0.1, "leaf_lime", pos=(0, 0, 3.3), segs=10, smooth=False, grad=(0.6, 0.8))
    mb.beam((0.6, 0.3, 3.3), (1.5, 0.9, 4.6), 0.14, 0.14, "wood_light")
    mb.light((0, 0, 3.6), color=(0.6, 1.0, 0.5), brightness=0.6, range_=10)


def grinder(mb):
    _base(mb, 4, 4)
    mb.cyl(1.5, 1.5, 0.9, "stone_dark", pos=(0, 0, 0.5), segs=10, smooth=False)
    mb.cyl(1.35, 1.35, 0.8, "stone_light", pos=(0, 0, 1.5), segs=10, smooth=False)
    mb.lathe([(0.5, 2.3), (1.1, 3.4), (1.2, 3.5), (1.0, 3.5), (0.4, 2.4)], "wood_light", segs=8, smooth=False)
    mb.beam((0, 0, 1.9), (1.9, 0, 2.1), 0.2, 0.2, "wood_dark")
    mb.box(0.3, 0.3, 0.7, "wood_dark", pos=(1.9, 0, 2.0))


def saw(mb):
    top = _table(mb, 6, 4)
    with mb.at(T(0.6, 0, top - 0.2), R("X", 90)):
        mb.cyl(1.25, 1.25, 0.14, "stone_light", pos=(0, 0, -0.07), segs=12, smooth=False)
    mb.box(1.2, 0.6, 1.2, "wood_dark", pos=(0.6, 0.7, top))
    for x in (-1.9, -1.2):
        with mb.at(T(x, 0, top + 0.35), R("X", 90)):
            mb.cyl(0.35, 0.35, 2.6, "bark", pos=(0, 0, -1.3), segs=6)


def crusher(mb):
    _base(mb, 4, 4)
    mb.box(2.6, 2.6, 1.4, "stone_dark", pos=(0, 0, 0.5), taper=0.9)
    for sx in (-1, 1):
        mb.box(0.5, 0.5, 4.6, "wood_dark", pos=(sx * 1.5, 0, 0.5))
    mb.box(3.6, 0.6, 0.5, "wood_dark", pos=(0, 0, 5.0))
    mb.box(1.2, 1.2, 1.6, "iron", pos=(0, 0, 2.6))
    mb.box(0.3, 0.3, 1.0, "wood_light", pos=(0, 0, 4.1))


def furnace(mb):
    _base(mb, 6, 4, "stone_dark")
    mb.box(4.6, 3.2, 3.2, "brick", pos=(-0.4, 0, 0.5), taper=0.92)
    mb.box(1.6, 0.3, 1.4, "iron", pos=(-0.4, -1.55, 0.9))
    mb.box(1.2, 0.2, 0.9, "glass_lit", pos=(-0.4, -1.62, 1.1), grad=(0.6, 0.9))
    mb.box(1.3, 1.3, 2.6, "stone_grey", pos=(1.2, 0.6, 3.5), taper=0.85)
    mb.box(1.5, 1.5, 0.3, "stone_dark", pos=(1.2, 0.6, 6.0))
    mb.box(1.0, 2.4, 1.6, "wood_dark", pos=(2.3, 0, 0.5))
    for i in range(3):
        mb.blob(0.38, "iron", pos=(2.3, -0.7 + i * 0.7, 2.25), level=0, noise=0.3, scale=(1, 1, 0.7))
    mb.light((-0.4, -1.9, 1.5), color=(1.0, 0.6, 0.25), brightness=1.0, range_=12)


def glassbench(mb):
    top = _table(mb, 4, 4)
    mb.lathe([(0.0, 0.0), (0.45, 0.2), (0.5, 0.7), (0.2, 1.0), (0.2, 1.4)], "glass_light", segs=7, pos=(-0.9, 0.5, top), smooth=False)
    mb.lathe([(0.0, 0.0), (0.3, 0.15), (0.32, 0.6), (0.14, 0.8), (0.14, 1.0)], "glass_light", segs=6, pos=(0.2, 0.8, top), smooth=False)
    with mb.at(T(0.4, -0.7, top + 0.25), R("Y", 90)):
        mb.cyl(0.09, 0.09, 2.6, "iron", pos=(0, 0, -1.3), segs=5)
    mb.blob(0.3, "glass_lit", pos=(1.7, -0.7, top + 0.25), level=0, noise=0.1, grad=(0.6, 0.9))
    mb.box(0.9, 0.9, 0.5, "stone_dark", pos=(-1.0, -0.8, top))


def extractor(mb):
    _base(mb, 6, 4)
    mb.lathe([(1.5, 0.5), (1.6, 3.2), (1.0, 4.2), (0.35, 4.6), (0.35, 5.2)], "brass", segs=10, pos=(-0.9, 0, 0), smooth=False, grad=(0.35, 0.75))
    mb.beam((-0.9, 0, 5.2), (1.6, 0, 4.6), 0.3, 0.3, "brass")
    mb.beam((1.6, 0, 4.6), (1.6, 0, 3.4), 0.3, 0.3, "brass")
    mb.lathe([(0.8, 0.5), (0.95, 2.4), (0.5, 3.4)], "glass_light", segs=8, pos=(1.6, 0, 0), smooth=False, grad=(0.4, 0.85))
    mb.cyl(0.4, 0.4, 0.5, "iron", pos=(-2.4, 0, 1.2), segs=6)


def bottler(mb):
    top = _table(mb, 4, 4, h=2.2)
    mb.box(0.5, 0.5, 3.0, "wood_dark", pos=(0, 1.2, top))
    mb.beam((0, 1.2, top + 2.8), (0, -0.4, top + 2.8), 0.4, 0.4, "wood_dark")
    mb.lathe([(0.75, 2.0), (0.8, 3.4), (0.3, 3.9)], "glass_light", segs=8, pos=(0, 0.2, top), smooth=False, grad=(0.4, 0.85))
    mb.cyl(0.12, 0.12, 0.9, "brass", pos=(0, -0.4, top + 1.9), segs=5)
    for i in range(3):
        mb.lathe([(0.0, 0.0), (0.3, 0.1), (0.3, 0.6), (0.12, 0.8), (0.12, 1.0)], "glass_blue", segs=6, pos=(-1.0 + i * 1.0, -0.7, top), smooth=False)


def mixer(mb):
    _base(mb, 4, 4)
    mb.lathe([(1.5, 0.5), (1.7, 1.2), (1.7, 3.0), (1.5, 3.2), (1.35, 3.0), (1.35, 1.4)], "wood_mid", segs=10, smooth=False)
    for z in (1.1, 2.7):
        mb.lathe([(1.74, z), (1.74, z + 0.25)], "iron", segs=10, smooth=False)
    mb.cyl(1.35, 1.35, 0.1, "flower_purple", pos=(0, 0, 2.7), segs=10, smooth=False, grad=(0.5, 0.8))
    mb.cyl(0.14, 0.14, 2.6, "wood_dark", pos=(0.3, 0.2, 2.7), segs=5)
    mb.beam((0.3, 0.2, 5.2), (1.5, 0.2, 5.2), 0.2, 0.2, "wood_dark")


def runetable(mb):
    _base(mb, 6, 6, "stone_dark", 0.4)
    mb.cyl(2.3, 2.5, 2.2, "stone_grey", pos=(0, 0, 0.4), segs=8, smooth=False)
    mb.cyl(2.7, 2.7, 0.4, "stone_light", pos=(0, 0, 2.6), segs=8, smooth=False)
    for k in range(8):
        a = 2 * math.pi * k / 8
        mb.box(0.45, 0.45, 0.12, "glass_light", pos=(1.9 * math.cos(a), 1.9 * math.sin(a), 3.0), grad=(0.6, 0.9))
    mb.lathe([(0.0, 3.3), (0.5, 3.9), (0.0, 4.7)], "flower_blue", segs=4, smooth=False, grad=(0.4, 0.9))
    mb.light((0, 0, 4.2), color=(0.5, 0.7, 1.0), brightness=0.8, range_=12)


def forge(mb):
    _base(mb, 6, 6, "stone_dark")
    mb.box(3.4, 3.0, 2.4, "stone_grey", pos=(-0.8, 0.9, 0.5), taper=0.93)
    mb.box(2.6, 2.2, 0.4, "roof_orange", pos=(-0.8, 0.9, 2.8), tone=0.25)
    mb.box(3.0, 2.6, 2.6, "stone_dark", pos=(-0.8, 1.0, 5.0), taper=(0.5, 0.5))
    mb.cyl(0.8, 0.9, 1.4, "wood_mid", pos=(1.6, -1.2, 0.5), segs=7)
    mb.box(1.8, 0.7, 0.45, "iron", pos=(1.6, -1.2, 2.3))
    mb.box(0.9, 0.55, 0.45, "iron", pos=(1.6, -1.2, 1.9))
    mb.box(2.6, 1.0, 1.0, "wood_dark", pos=(1.4, 1.8, 0.5))
    mb.light((-0.8, 0.9, 3.4), color=(1.0, 0.55, 0.2), brightness=1.2, range_=14)


def enchanter(mb):
    _base(mb, 6, 6, "stone_dark", 0.4)
    mb.box(2.4, 1.8, 2.8, "wood_dark", pos=(0, 0.4, 0.4), taper=0.9)
    with mb.at(T(0, 0.2, 3.2), R("X", -18)):
        mb.box(3.0, 2.2, 0.3, "wood_mid")
        mb.box(2.2, 1.5, 0.12, "plaster_cream", pos=(0, 0, 0.3))
    for sx in (-1, 1):
        mb.cyl(0.28, 0.2, 3.6, "brass", pos=(sx * 2.1, 1.8, 0.4), segs=6)
        mb.lathe([(0.0, 4.0), (0.45, 4.5), (0.0, 5.2)], "flower_purple", segs=4, pos=(sx * 2.1, 1.8, 0), smooth=False, grad=(0.4, 0.9))
    mb.light((0, 0.5, 4.5), color=(0.75, 0.5, 1.0), brightness=0.9, range_=14)


def infuser(mb):
    _base(mb, 6, 6)
    for sx in (-1, 1):
        mb.lathe([(1.0, 0.5), (1.2, 2.8), (0.5, 3.6), (0.25, 4.4)], "glass_light", segs=8, pos=(sx * 1.6, 0.6, 0), smooth=False, grad=(0.4, 0.85))
        mb.beam((sx * 1.6, 0.6, 4.4), (0, 0, 5.0), 0.22, 0.22, "brass")
    mb.cyl(0.22, 0.22, 2.2, "brass", pos=(0, 0, 2.8), segs=6)
    mb.lathe([(0.7, 0.5), (0.95, 1.6), (0.9, 2.8), (0.5, 2.9)], "iron", segs=8, pos=(0, -1.2, 0), smooth=False)
    mb.beam((0, 0, 2.8), (0, -1.2, 2.9), 0.22, 0.22, "brass")


def crystal_refiner(mb):
    _base(mb, 6, 6, "stone_dark")
    mb.box(3.6, 3.6, 1.8, "wood_dark", pos=(0, 0, 0.5), taper=0.92)
    mb.cyl(1.7, 1.7, 0.35, "stone_light", pos=(0, 0, 2.3), segs=12, smooth=False)
    mb.lathe([(0.0, 2.7), (0.8, 3.5), (0.55, 4.6), (0.0, 5.4)], "glass_light", segs=6, smooth=False, grad=(0.35, 0.95))
    for k in range(3):
        a = 2 * math.pi * k / 3
        mb.beam((2.2 * math.cos(a), 2.2 * math.sin(a), 0.5), (1.0 * math.cos(a), 1.0 * math.sin(a), 4.4), 0.25, 0.25, "brass")
    mb.light((0, 0, 4.2), color=(0.6, 0.9, 1.0), brightness=1.0, range_=14)


def advanced_cauldron(mb):
    _base(mb, 8, 8, "stone_dark", 0.6)
    mb.cyl(3.2, 3.4, 0.8, "stone_grey", pos=(0, 0, 0.6), segs=12, smooth=False)
    mb.lathe([(1.8, 1.4), (2.9, 2.2), (3.2, 3.8), (2.8, 5.0), (3.0, 5.3), (2.6, 5.3), (2.5, 4.8)], "iron", segs=12, smooth=False)
    mb.cyl(2.5, 2.5, 0.12, "flower_purple", pos=(0, 0, 4.8), segs=12, smooth=False, grad=(0.5, 0.85))
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        mb.cyl(0.3, 0.22, 6.6, "brass", pos=(3.3 * math.cos(a), 3.3 * math.sin(a), 0.6), segs=6)
        mb.lathe([(0.0, 7.2), (0.5, 7.8), (0.0, 8.6)], "glass_light", segs=4, pos=(3.3 * math.cos(a), 3.3 * math.sin(a), 0), smooth=False, grad=(0.4, 0.95))
    mb.light((0, 0, 6.0), color=(0.8, 0.5, 1.0), brightness=1.4, range_=18)


def herb_grower(mb):
    mb.box(5.6, 5.6, 1.0, "wood_mid", taper=1.03)
    mb.box(5.0, 5.0, 0.2, "dirt_dark", pos=(0, 0, 0.9))
    for ix in range(3):
        for iy in range(3):
            mb.blob(0.6, "leaf_green" if (ix + iy) % 2 else "leaf_lime", pos=(-1.6 + ix * 1.6, -1.6 + iy * 1.6, 1.5), level=0, noise=0.2,
                    scale=(1, 1, 0.85), grad=(0.3, 0.85))
    for sx in (-1, 1):
        mb.box(0.3, 0.3, 3.2, "wood_dark", pos=(sx * 2.6, 2.6, 1.0))
    mb.beam((-2.6, 2.6, 4.1), (2.6, 2.6, 4.1), 0.3, 0.3, "wood_dark")


def quarry_drill(mb):
    _base(mb, 6, 6, "stone_dark")
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        mb.beam((2.4 * math.cos(a), 2.4 * math.sin(a), 0.5), (0.3 * math.cos(a), 0.3 * math.sin(a), 6.2), 0.4, 0.4, "wood_dark")
    mb.cyl(0.7, 0.7, 1.2, "iron", pos=(0, 0, 5.2), segs=8)
    mb.lathe([(0.45, 1.6), (0.45, 5.2)], "iron", segs=6)
    mb.lathe([(0.0, 0.3), (0.7, 1.6), (0.45, 1.7)], "stone_light", segs=6, smooth=False)
    mb.blob(0.9, "rock", pos=(1.6, -1.4, 0.8), level=0, noise=0.3, scale=(1.2, 1, 0.7))
    mb.blob(0.6, "rock_dark", pos=(-1.5, 1.5, 0.7), level=0, noise=0.3)


def well_pump(mb):
    mb.lathe([(1.7, 0.0), (1.7, 1.6), (1.4, 1.6), (1.4, 0.9)], "stone_grey", segs=10, smooth=False)
    mb.cyl(1.4, 1.4, 0.1, "water", pos=(0, 0, 0.9), segs=10, smooth=False)
    mb.cyl(0.3, 0.3, 3.4, "iron", pos=(0, 0.9, 0.8), segs=6)
    mb.beam((0, 0.9, 4.0), (0, -0.9, 4.6), 0.2, 0.2, "iron")
    mb.beam((0, 0.9, 3.4), (1.7, 0.9, 3.0), 0.3, 0.3, "brass")


def wooden_belt(mb):
    mb.box(1.7, 2.0, 0.5, "wood_dark")
    mb.box(1.3, 2.0, 0.16, "wood_light", pos=(0, 0, 0.5))
    for y in (-0.6, 0.0, 0.6):
        mb.box(1.3, 0.12, 0.06, "wood_dark", pos=(0, y, 0.66))
    mb.lathe([(0.0, 0.0), (0.3, 0.04), (0.0, 0.08)], "brass", segs=3, pos=(0, -0.5, 0.68), phase=-math.pi / 2, smooth=False)


def belt_turn(mb):
    mb.box(1.9, 1.9, 0.5, "wood_dark")
    mb.box(1.6, 1.6, 0.16, "wood_light", pos=(0, 0, 0.5))
    mb.beam((0, 0.7, 0.72), (0, 0, 0.72), 0.25, 0.06, "brass")
    mb.beam((0, 0, 0.72), (0.7, 0, 0.72), 0.25, 0.06, "brass")


def input_hopper(mb):
    mb.box(1.6, 1.8, 0.5, "wood_dark")
    mb.lathe([(0.35, 0.5), (0.9, 1.6), (0.95, 1.7), (0.8, 1.7), (0.3, 0.7)], "wood_light", segs=4, phase=math.pi / 4, smooth=False)
    mb.box(0.8, 0.5, 0.3, "brass", pos=(0, -0.75, 0.5))


def splitter(mb):
    mb.box(1.9, 1.9, 0.7, "wood_dark")
    mb.cyl(0.6, 0.6, 0.5, "brass", pos=(0, 0, 0.7), segs=8, smooth=False)
    for a in (0, -90, 90):
        with mb.at(R("Z", a)):
            mb.box(0.3, 0.9, 0.1, "brass", pos=(0, -0.5, 0.7))


def merger(mb):
    mb.box(1.9, 1.9, 0.7, "wood_dark")
    mb.lathe([(0.7, 0.7), (0.35, 1.2)], "iron", segs=8, smooth=False)
    mb.box(0.3, 0.9, 0.1, "brass", pos=(0, -0.5, 0.7))


def filter_sorter(mb):
    mb.box(1.9, 1.9, 0.9, "wood_dark")
    mb.box(1.3, 1.3, 0.8, "plaster_cream", pos=(0, 0, 0.9), taper=0.8)
    mb.lathe([(0.0, 1.7), (0.4, 2.0), (0.0, 2.4)], "flower_blue", segs=4, smooth=False, grad=(0.4, 0.9))
    mb.box(0.3, 0.6, 0.1, "brass", pos=(0, -0.65, 0.9))
    mb.box(0.6, 0.3, 0.1, "iron", pos=(0.65, 0, 0.9))


def vertical_lift(mb):
    mb.box(1.9, 1.9, 0.5, "wood_dark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(0.25, 0.25, 11.4, "wood_dark", pos=(sx * 0.75, sy * 0.75, 0.5))
    for z in (4.0, 8.0):
        mb.box(1.75, 0.2, 0.2, "wood_mid", pos=(0, 0.75, z))
    mb.box(1.9, 1.9, 0.25, "wood_mid", pos=(0, 0, 11.6))
    mb.box(1.2, 1.2, 0.2, "wood_light", pos=(0, 0, 2.4))
    mb.box(0.08, 0.08, 9.0, "iron", pos=(0, 0, 2.6))


def magical_gate(mb):
    mb.box(1.9, 1.9, 0.5, "stone_dark")
    for sx in (-1, 1):
        mb.box(0.4, 0.5, 2.8, "stone_light", pos=(sx * 0.7, 0, 0.5), taper=0.9)
    mb.box(1.8, 0.5, 0.4, "stone_light", pos=(0, 0, 3.3))
    mb.box(1.0, 0.1, 2.6, "flower_purple", pos=(0, 0, 0.6), grad=(0.3, 0.95))
    mb.light((0, 0, 2.0), color=(0.75, 0.5, 1.0), brightness=0.8, range_=10)


def pipe_straight(mb):
    with mb.at(T(0, 0, 0.36), R("X", 90)):
        mb.cyl(0.3, 0.3, 2.0, "brass", pos=(0, 0, -1.0), segs=6)
        mb.cyl(0.4, 0.4, 0.3, "iron", pos=(0, 0, -0.15), segs=6)
    with mb.at(T(0, 0, 0.36), R("Y", 90)):
        mb.cyl(0.3, 0.3, 2.0, "brass", pos=(0, 0, -1.0), segs=6)


def pipe_bend(mb):
    pipe_straight(mb)


def fluid_tank(mb):
    _base(mb, 4, 4)
    mb.lathe([(1.5, 0.5), (1.7, 1.0), (1.7, 4.2), (1.2, 4.9), (0.4, 5.1)], "brass", segs=10, smooth=False, grad=(0.35, 0.75))
    mb.box(0.6, 0.12, 2.4, "glass_light", pos=(0, -1.66, 1.4), grad=(0.3, 0.9))
    for z in (1.2, 3.8):
        mb.lathe([(1.74, z), (1.74, z + 0.3)], "iron", segs=10, smooth=False)


def storage_crate(mb):
    mb.box(3.5, 3.5, 3.0, "wood_light", tone=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(0.4, 0.4, 3.06, "wood_mid", pos=(sx * 1.6, sy * 1.6, 0))
    for z in (0.0, 2.7):
        for sy in (-1, 1):
            mb.box(3.56, 0.4, 0.4, "wood_mid", pos=(0, sy * 1.6, z))
        for sx in (-1, 1):
            mb.box(0.4, 3.56, 0.4, "wood_mid", pos=(sx * 1.6, 0, z))
    mb.box(0.8, 0.12, 0.6, "iron", pos=(0, -1.78, 1.2))


def shop_shelf(mb):
    for sx in (-1, 1):
        mb.box(0.3, 1.6, 6.0, "wood_dark", pos=(sx * 2.7, 0, 0))
    for z in (0.3, 2.2, 4.1, 5.8):
        mb.box(5.6, 1.6, 0.25, "wood_light", pos=(0, 0, z))
    mb.box(5.6, 0.15, 6.0, "wood_mid", pos=(0, 0.75, 0))
    cols = ("glass_blue", "flower_red", "leaf_lime", "flower_purple", "glass_lit")
    for row, z in enumerate((0.55, 2.45, 4.35)):
        for i in range(5):
            mb.lathe([(0.0, 0.0), (0.3, 0.1), (0.3, 0.6), (0.12, 0.8), (0.12, 1.0)], cols[(i + row) % 5], segs=6,
                     pos=(-2.0 + i * 1.0, -0.2, z), smooth=False, grad=(0.4, 0.85))
    mb.box(2.4, 0.2, 0.9, "cloth_red", pos=(0, -0.75, 6.1))


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
