"""Grip profiles: how each held thing is gripped, where, and what counts as wrong.

Every prop is modelled in prop space (see handheld.py): +Y runs along the gripped part from the thumb /
index side to the little finger, -Z is the direction the open fingers point, origin = centre of the
grip.  A profile names the grip type and the region of the prop the hand has to hold; the grip solver
(characters.grip_prop) uses tilt and the tried handle positions, the validator (gripcheck.py) uses
the regions.

    kind      power      fingers and palm wrap a handle, the thumb closes from the other side
              hook       fingers hook around a bail, the palm need not touch (carrying)
              bundle     power grip around a bundle of stems
              ball       fingers and palm spread around a rounded lump
              pinch      flat thin thing between fingers and thumb
    region    (y0, y1)   part of the prop (prop space Y) the skin may touch; contact anywhere else fails
    forbidden [(name, y0, y1)]  parts that must never be held (blade, head, glass point ...)
    palm      the palm has to touch the prop (power grips)
"""

PROFILES = {
    "herb_bundle": dict(builder="herb_bundle", kind="bundle", tilt=6.0, region=(-0.2, 0.2),
                        forbidden=[("flowers and leaves", -1.0, -0.28)], palm=True,
                        task="hold the bundle by the tied stems, flowers up; smell it"),
    "basket": dict(builder="basket", kind="hook", tilt=4.0, region=(-0.2, 0.2), forbidden=[], palm=False,
                   task="carry by the bail with the arm down, the basket hangs below the hand"),
    "crystal": dict(builder="crystal", kind="power", tilt=8.0, region=(-0.3, 0.22),
                    forbidden=[("crystal point", -0.6, -0.4)], palm=True,
                    task="hold the crystal by its body, the point free; turn it in the light"),
    "lantern": dict(builder="lantern", kind="hook", tilt=4.0, region=(-0.3, 0.3), forbidden=[], palm=False,
                    task="carry by the bail with the arm down, the lantern hangs below the hand"),
    "potion_bottle": dict(builder="potion_bottle", kind="power", tilt=0.0, region=(-0.19, 0.22),
                          forbidden=[("cork", -0.42, -0.33), ("neck", -0.33, -0.23)], palm=True,
                          task="hold the bottle round its body, cork up; polish it, hold it to the light"),
    # a soft cloth has no wrong part: its hanging ends may touch the fingers
    "cloth": dict(builder="cloth", kind="ball", tilt=4.0, region=(-0.6, 0.6), forbidden=[], palm=True,
                  task="a crumpled cloth in the fist; rub the bottle with it"),
    "hammer": dict(builder="hammer", kind="power", tilt=14.0, region=(-0.58, 0.42),
                   forbidden=[("hammer head", -1.2, -0.6)], palm=True,
                   task="power grip on the handle, head forwards; tap the ore"),
    "ore": dict(builder="ore", kind="ball", tilt=0.0, region=(-0.25, 0.3), forbidden=[], palm=True,
                task="weigh the lump in the hand"),
    "axe": dict(builder="axe", kind="power", tilt=12.0, region=(-0.2, 0.46),
                forbidden=[("axe head", -2.4, -1.5)], palm=True,
                task="power grip at the lower third of the handle; rest the handle on the shoulder"),
    "folding_rule": dict(builder="folding_rule", kind="pinch", tilt=8.0, region=(-0.3, 0.2), forbidden=[], palm=False,
                         task="hold the first leg; sight along the rule"),
}

# who holds what (hand L = the figure's left)
HELD = {
    "selma": {"R": "herb_bundle", "L": "basket"},
    "nyra": {"R": "crystal", "L": "lantern"},
    "lio": {"R": "potion_bottle", "L": "cloth"},
    "aron": {"R": "hammer", "L": "ore"},
    "esme": {"R": "axe", "L": "folding_rule"},
}

# handle positions tried by the solver, from the knuckle line towards the wrist (studs); a hook grip
# hangs further out on the fingers, a power grip lies deeper in the palm
ALONG = {"power": (-0.01, 0.025, 0.06, 0.095), "bundle": (-0.01, 0.025, 0.06, 0.095), "ball": (-0.01, 0.025, 0.06, 0.095),
         "hook": (-0.01, 0.025, 0.06), "pinch": (-0.01, 0.025, 0.06)}


def profile(role, side):
    return PROFILES[HELD[role][side]]
