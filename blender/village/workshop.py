"""Workshop frontage in the village's -Y-facing building coordinates."""
from .building import Wing, chimney, door, finish, win
from .machines import bottle, pipe_run
from .meshkit import R, T


def facade(mb):
    house = Wing(mb, 21, 17, cx=-2.9, found=1.3, found_color="stone_warm")
    entry = (10.5 + 2.9) / 21
    house.storey(9.4, style="stone", color="stone_warm", openings={
        "front": [door(entry, arch=True, w=4.5, h=7.4, color="wood_red", hood="roof_purple", lantern=1),
                  win(0.25, w=6.1, h=3.8, z=3.25, lit=True, muntins=(2, 1))],
        "left": [win(0.42, w=3.2, z=3.0, shutters="plaster_sage")],
        "back": [win(0.32), win(0.71)],
    })
    house.storey(6.8, style="timber", color="plaster_cream", jetty={"front": 0.68}, openings={
        "front": [win(0.27, z=1.7, h=3.25, shutters="plaster_sage"),
                  win(0.76, z=1.85, h=3.0, shutters="plaster_sage", lit=True)],
        "left": [win(0.5, z=1.8, h=3.2)],
        "back": [win(0.26, z=1.8, h=3.0), win(0.71, z=1.8, h=3.0)],
    })
    house.gable("roof_purple", ridge="x", pitch=56, sag=1.0, shape=0.72,
                oe=1.45, og=1.2, gable_win="round")
    house.dormer(-3.8, side=-1, roof="roof_purple", lit=True)

    annex = Wing(mb, 7.0, 9.6, cx=9.3, cy=0.35, found=1.0, found_color="stone_warm")
    annex.storey(8.0, style="timber", color="plaster_cream", openings={
        "front": [win(0.54, w=3.5, h=3.4, z=2.55, shutters="plaster_sage", lit=True)],
        "right": [win(0.55, w=2.9, z=2.6, h=3.4, flowerbox="flower_purple")],
    })
    annex.gable("roof_slate", ridge="y", pitch=47, oe=1.0, og=0.9, gable_win="small")

    with mb.at(T(4.4, -1.8, 23.5), R("Y", 7)):
        chimney(mb, 0, 0, 0, 12.0, w=2.95, d=2.6, color="brick", pots=2)
        mb.box(2.89, 2.58, 0.24, "roof_brown", pos=(0, 0, 10.7))

    # Flasks and copper pipe silhouetted in front of the warm display backing.
    with mb.at(T(-8.15, -8.8, 4.59)):
        mb.box(6.0, 0.9, 0.26, "wood_dark", pos=(0, -0.1, -0.18))
        for x, color, scale in ((-2.15, "glass_blue", 1.22), (-0.85, "leaf_teal", 0.95),
                                (0.6, "roof_purple", 1.28), (1.88, "glass_light", 0.85)):
            bottle(mb, x, -0.57, 0.09, color, scale)
        pipe_run(mb, [(-2.55, -0.18, 0.28), (-2.55, -0.18, 2.65), (2.05, -0.18, 2.65),
                      (2.05, -0.18, 1.35)], 0.12, "brass")
    for x, y, width in ((-8.2, -9.65, 4.6), (8.5, -5.1, 3.4)):
        mb.box(width, 1.25, 0.7, "wood_mid", pos=(x, y, 0.1), taper=1.12)
        mb.box(width + 0.2, 1.38, 0.17, "wood_dark", pos=(x, y, 0.71))
        for i in range(6):
            xx = x + width * ((i + 0.5) / 6 - 0.5)
            mb.blob(0.53, ("leaf_green", "leaf_teal", "leaf_dark")[i % 3],
                    pos=(xx, y, 0.88 + mb.jitter(0.12)), scale=(1, 0.92, 1.3), level=0)
        mb.blob(0.22, "flower_purple", pos=(x + 0.38, y - 0.1, 1.28), level=0)

    with mb.at(T(4.6, -8.66, 8.3)):
        mb.box(0.66, 0.24, 1.6, "iron", pos=(0, 0, -0.95))
        mb.beam((0, 0, 0.2), (0, -2.65, 0.5), 0.21, 0.24, "iron")
        mb.beam((0, -0.04, -0.8), (0, -1.46, 0.35), 0.16, 0.14, "iron")
        with mb.at(T(0, -2.22, -1.83), R("Z", 29)):
            mb.beam((0, 0, 1.65), (0, 0, 2.3), 0.10, 0.10, "iron")
            silhouette = [(-0.66, 0), (0.66, 0), (0.94, 0.54), (0.92, 0.81),
                          (0.34, 1.18), (0.33, 1.63), (-0.33, 1.63), (-0.34, 1.18),
                          (-0.92, 0.81), (-0.94, 0.54)]
            mb.prism(silhouette, -0.17, 0.17, "iron")
            inset = [(x * 0.76, z * 0.76 + 0.17) for x, z in silhouette]
            mb.prism(inset, -0.21, -0.16, "leaf_teal", grad=(0.4, 0.78))
            mb.prism(inset, 0.16, 0.21, "leaf_teal", grad=(0.4, 0.78))
            mb.box(0.8, 0.42, 0.22, "brass", pos=(0, 0, 1.62))
    finish(mb, 35.0, taper=0.015)
    # Collision proxy for the front steps, beside the planters and clear of the portal marker.
    for i in range(2):
        top = house.found * (1 - i / 2)
        depth = 1.7 + i * 1.15
        mb.collider_box((0, -8.5 - depth / 2 + 0.02, (top - 1.9) / 2),
                        (5.9 + i * 0.25, depth, top + 1.9))
