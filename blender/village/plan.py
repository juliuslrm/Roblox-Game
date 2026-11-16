"""The level plan of the village: roads, water, buildings, props and nature.

Everything here is deterministic.  Hand-authored data (road control points,
building sites, landmarks, special props) lives in the tables at the top;
build_plan() turns it into a height grid and a flat list of instances with
final positions.  All coordinates are Blender coordinates in studs
(X east, Y north, Z up, village square at the origin).
"""
import math
import random

import numpy as np

from . import terrain as tr
from .terrain import HALF, HeightGrid, Polyline, smoothstep

SEED = 20261114
PLAZA_Z = 0.0


def plaza_radius(theta):
    """Irregular outline of the village square."""
    return 46.0 + 5.0 * math.sin(2 * theta + 0.6) + 3.0 * math.sin(3 * theta + 2.0)


# ---------------------------------------------------------------- roads
# kind: main (cobbled street), lane (narrow cobbled alley), path (dirt track)
ROADS = [
    dict(id="south_road", kind="main", hw=7.0, layer=0, name="Suedstrasse",
         pts=[(-30, -384), (-42, -320), (-28, -250), (12, -185), (30, -125), (14, -75), (4, -40)]),
    dict(id="north_road", kind="main", hw=6.0, layer=0, name="Kirchgasse",
         pts=[(6, 40), (22, 80), (34, 120), (26, 160), (48, 200), (72, 230)]),
    dict(id="west_road", kind="main", hw=6.0, layer=0, name="Muehlenweg",
         pts=[(-42, 6), (-80, 22), (-125, 14), (-170, 36), (-205, 78), (-232, 120), (-248, 150)]),
    dict(id="east_road", kind="main", hw=7.0, layer=0, name="Bachstrasse",
         pts=[(44, -6), (90, -22), (150, -8), (205, -14), (262, -40), (325, -30), (384, -52)]),
    dict(id="ring_lane", kind="lane", hw=4.0, layer=1, name="Hintergasse",
         pts=[(-80, 22), (-104, 66), (-88, 112), (-44, 146), (0, 158), (26, 160)]),
    dict(id="mill_lane", kind="lane", hw=4.0, layer=1, name="Feldgasse",
         pts=[(12, -185), (-40, -168), (-96, -130), (-134, -70), (-125, 14)]),
    dict(id="pond_lane", kind="lane", hw=4.0, layer=1, name="Teichgasse",
         pts=[(30, -125), (74, -118), (112, -84), (108, -40), (90, -22)]),
    dict(id="chapel_lane", kind="lane", hw=4.0, layer=1, name="Kapellenstieg",
         pts=[(34, 120), (78, 112), (112, 78), (104, 22), (90, -22)]),
    dict(id="tower_path", kind="path", hw=2.6, layer=2, name="Turmpfad",
         pts=[(205, -14), (228, 30), (246, 72), (260, 102)]),
    dict(id="farm_path", kind="path", hw=2.6, layer=2, name="Hofweg",
         pts=[(-96, -130), (-150, -160), (-205, -178), (-246, -210)]),
    dict(id="pond_path", kind="path", hw=2.4, layer=2, name="Stegpfad",
         pts=[(112, -84), (124, -92), (134, -100)]),
    # short access paths to the workshop plots (see WORKSHOP_PLOTS)
    dict(id="plot_path_1", kind="path", hw=2.6, layer=2, name="Werkstattweg 1",
         pts=[(-134, -48), (-141, -44), (-148, -40)]),
    dict(id="plot_path_2", kind="path", hw=2.6, layer=2, name="Werkstattweg 2",
         pts=[(-47, 145), (-54, 152), (-60, 160)]),
    dict(id="plot_path_3", kind="path", hw=2.6, layer=2, name="Werkstattweg 3",
         pts=[(-143, -157), (-136, -163), (-128, -172)]),
    dict(id="plot_path_4", kind="path", hw=2.6, layer=2, name="Werkstattweg 4",
         pts=[(266, -40), (265, -48), (264, -58)]),
]

# Level building plots for the walkable player workshops, one per player (Config.maxPlayers = 4).
# The largest workshop tier is 80 x 80 studs; a plot keeps an 84 stud square level and free of
# scenery.  The village itself has no free square of that size, so the plots lie at its edge,
# each next to a road and at least 110 studs apart, so the levelled ground of one plot does not
# reach the next (chosen with a search over the previous level plan, 2026-11-16).
WORKSHOP_PLOTS = [(-188.0, -40.0), (-80.0, 200.0), (-116.0, -212.0), (262.0, -98.0)]
PLOT_HALF = 42.0
PLOT_BLEND = 24.0           # studs over which the levelled ground runs out into the landscape


def in_plot(x, y, margin=0.0):
    return any(abs(x - px) < PLOT_HALF + margin and abs(y - py) < PLOT_HALF + margin for px, py in WORKSHOP_PLOTS)

STREAM_PTS = [(215, 384), (196, 310), (212, 240), (182, 170), (160, 95), (150, -8), (152, -55),
              (172, -105), (178, -165), (158, -240), (176, -310), (190, -384)]
POND_AT = (172.0, -105.0)
BRIDGE_HALF = 14.0          # bridge_stone is 28 studs long

# ---------------------------------------------------------------- buildings
# Sites along a road: (asset, road, distance from road start, side, setback, name)
# side +1 = left of the direction of travel, -1 = right.
ALONG = [
    ("house_03_thatched_cottage", "south_road", 150, -1, 9, "Reetkate am Suedtor"),
    ("house_14_long_weaver_house", "south_road", 178, 1, 7, "Weberhaus"),
    ("house_09_twin_gable", "south_road", 226, -1, 7, "Zwillingsgiebelhaus"),
    ("house_10_saltbox", "west_road", 66, 1, 6, "Schleppdachhaus"),
    ("house_01_timber_cottage", "south_road", 322, 1, 5, "Fachwerkhaus am Markt"),
    ("house_11_stair_house", "east_road", 206, 1, 7, "Treppenhaus-Werkstatt"),
    ("house_16_porch_tower_house", "north_road", 62, 1, 6, "Haus zum Erker"),
    ("house_07_stone_manor", "north_road", 118, -1, 8, "Steinernes Herrenhaus"),
    ("house_04_farmhouse", "mill_lane", 168, 1, 8, "Bauernhaus"),
    ("house_18_tiny_cottage", "ring_lane", 62, 1, 6, "Kleines Haeuschen"),
    ("house_06_crooked_tower_house", "west_road", 132, -1, 5, "Schiefes Haus"),
    ("house_08_plank_cabin", "west_road", 196, 1, 9, "Blockhuette am Muehlenweg"),
    ("house_12_turret_house", "chapel_lane", 62, 1, 6, "Tuermchenhaus"),
    ("lm_smithy", "east_road", 58, -1, 9, "Schmiede"),
    ("house_13_fisher_hut", "pond_lane", 66, 1, 9, "Fischerhuette"),
    ("house_17_red_barn", "farm_path", 122, 1, 10, "Rote Scheune"),
]
# Free sites: (asset, x, y, look_at_x, look_at_y, name)
SITES = [
    ("lm_town_hall", -46, 62, 0, 0, "Rathaus"),
    ("house_05_bakery", 66, 22, 0, 0, "Baeckerei"),
    ("house_02_gabled_townhouse", 44, 56, 0, 0, "Giebelhaus am Markt"),
    ("lm_tavern", 60, -62, 0, 0, "Gasthaus Zum Goldenen Krug"),
    ("house_15_tower_house", -67, -12, 0, 0, "Turmhaus"),
    ("lm_market_hall", -50, -56, 0, 0, "Markthalle"),
    ("lm_chapel", 90, 262, 72, 230, "Kapelle"),
    ("lm_windmill", -262, 180, -248, 150, "Windmuehle"),
    ("lm_watchtower", 272, 124, 260, 102, "Wachturm"),
]


# ---------------------------------------------------------------- helpers
def face_rot(dx, dy):
    """Rotation (deg, around Z) that turns an asset's front (-Y) towards (dx, dy)."""
    return math.degrees(math.atan2(dx, -dy))


def local_to_world(inst, lx, ly):
    a = math.radians(inst["rot"])
    c, s = math.cos(a), math.sin(a)
    return inst["x"] + lx * c - ly * s, inst["y"] + lx * s + ly * c


class Footprint:
    """Oriented rectangle of a placed asset (for overlap checks)."""

    def __init__(self, inst, bounds, shrink=0.94):
        bmin, bmax = bounds["min"], bounds["max"]
        self.cx, self.cy = local_to_world(inst, (bmin[0] + bmax[0]) / 2, (bmin[1] + bmax[1]) / 2)
        self.hx = (bmax[0] - bmin[0]) / 2 * shrink * inst.get("scale", 1.0)
        self.hy = (bmax[1] - bmin[1]) / 2 * shrink * inst.get("scale", 1.0)
        a = math.radians(inst["rot"])
        self.ax = (math.cos(a), math.sin(a))
        self.ay = (-math.sin(a), math.cos(a))
        self.radius = math.hypot(self.hx, self.hy)

    def corners(self):
        out = []
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            out.append((self.cx + sx * self.hx * self.ax[0] + sy * self.hy * self.ay[0],
                        self.cy + sx * self.hx * self.ax[1] + sy * self.hy * self.ay[1]))
        return out

    def contains(self, x, y, margin=0.0):
        dx, dy = x - self.cx, y - self.cy
        return (abs(dx * self.ax[0] + dy * self.ax[1]) <= self.hx + margin
                and abs(dx * self.ay[0] + dy * self.ay[1]) <= self.hy + margin)

    def overlaps(self, other):
        """Separating axis test between two oriented rectangles."""
        if math.hypot(self.cx - other.cx, self.cy - other.cy) > self.radius + other.radius:
            return False
        for axis in (self.ax, self.ay, other.ax, other.ay):
            pa = [p[0] * axis[0] + p[1] * axis[1] for p in self.corners()]
            pb = [p[0] * axis[0] + p[1] * axis[1] for p in other.corners()]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
        return True


class Plan:
    """Result of build_plan()."""

    def __init__(self):
        self.grid = None
        self.roads = []          # dicts with 'poly' (Polyline incl. z)
        self.stream = None       # Polyline with z (water level) and hw
        self.instances = []
        self.footprints = {}     # instance uid -> Footprint (buildings only)
        self.road_clear = None   # grid: distance to the nearest road edge
        self.water_clear = None  # grid: distance to the water edge
        self.material = None     # grid (cells): terrain material class
        self.bridge = None
        self.plots = []          # dicts x, y, z: levelled workshop plots

    def road(self, rid):
        return next(r for r in self.roads if r["id"] == rid)


def _sample(field, x, y):
    fx = min(max((x + HALF) / tr.CELL, 0.0), tr.N - 1e-9)
    fy = min(max((y + HALF) / tr.CELL, 0.0), tr.N - 1e-9)
    i, j = int(fx), int(fy)
    u, v = fx - i, fy - j
    return float(field[j, i] * (1 - u) * (1 - v) + field[j, i + 1] * u * (1 - v)
                 + field[j + 1, i] * (1 - u) * v + field[j + 1, i + 1] * u * v)


# ---------------------------------------------------------------- terrain + roads
def _build_roads(plan, H1):
    g1 = HeightGrid(H1)
    done = []
    for rd in ROADS:
        poly = Polyline(rd["pts"], step=3.0)
        poly.hw[:] = rd["hw"]
        z = tr.smooth_1d(g1.bilinear(poly.xy[:, 0], poly.xy[:, 1]), 15, passes=3)
        # pin both ends to the plaza or to roads that already exist
        for end in (0, -1):
            x, y = poly.xy[end]
            target = None
            if math.hypot(x, y) < plaza_radius(math.atan2(y, x)) + 8:
                target = PLAZA_Z
            else:
                best = 14.0
                for other in done:
                    d, s = other["poly"].nearest(x, y)
                    if d < best:
                        best, target = d, float(np.interp(s, other["poly"].s, other["poly"].z))
            if target is not None:
                dist = poly.s if end == 0 else poly.length - poly.s
                z = z + (target - z[end]) * (1 - smoothstep(dist / 48.0))
        poly.z = z
        entry = dict(rd)
        entry["poly"] = poly
        done.append(entry)
    plan.roads = done


def _road_fields(plan, X, Y):
    W = np.zeros(X.shape)
    Z = np.zeros(X.shape)
    clear = np.full(X.shape, 1e6)
    for rd in plan.roads:
        D, Zr, HWr = tr.field_from_polyline(rd["poly"], X, Y, reach=20.0)
        w = 1 - smoothstep((D - HWr - 2.0) / 14.0)
        w[~np.isfinite(D)] = 0.0
        better = w > W
        W[better] = w[better]
        Z[better] = Zr[better]
        clear = np.minimum(clear, np.where(np.isfinite(D), D - HWr, 1e6))
    # anything further than the field reach: fall back to a coarse distance
    far = clear > 1e5
    if far.any():
        pts = np.concatenate([rd["poly"].xy[::4] for rd in plan.roads])
        fx, fy = X[far], Y[far]
        d = np.full(fx.shape, 1e6)
        for k in range(0, len(pts), 64):
            chunk = pts[k:k + 64]
            dd = np.sqrt((fx[:, None] - chunk[None, :, 0]) ** 2 + (fy[:, None] - chunk[None, :, 1]) ** 2)
            d = np.minimum(d, dd.min(axis=1))
        clear[far] = d - 4.0
    return W, Z, clear


def _place_buildings(plan, manifest, g_road):
    out = []
    for asset, rid, s, side, setback, name in ALONG:
        rd = plan.road(rid)
        p, t, _z = rd["poly"].at(s)
        n = np.array([-t[1], t[0]]) * side
        b = manifest[asset]["bounds_blender"]
        front = -b["min"][1]
        pos = p + n * (rd["hw"] + setback + front)
        out.append(dict(asset=asset, x=float(pos[0]), y=float(pos[1]), rot=face_rot(-n[0], -n[1]),
                        name=name, group="buildings", site=f"{rid}@{s}"))
    for asset, x, y, lx, ly, name in SITES:
        out.append(dict(asset=asset, x=float(x), y=float(y), rot=face_rot(lx - x, ly - y), name=name,
                        group="buildings", site="free"))
    for i, inst in enumerate(out):
        inst["uid"] = f"{inst['asset']}#1"
        inst["scale"] = 1.0
        b = manifest[inst["asset"]]["bounds_blender"]
        fp = Footprint(inst, b)
        plan.footprints[inst["uid"]] = fp
        # pad: level ground for the building, taken from the road-shaped terrain
        inst["pad_z"] = g_road.at(inst["x"], inst["y"])
        if inst["asset"] in ("lm_windmill", "lm_watchtower", "lm_chapel"):
            inst["pad_z"] = max(inst["pad_z"], g_road.at(fp.cx, fp.cy))
    return out


def build_terrain(plan, manifest):
    X, Y = tr.grid_xy()
    H0 = tr.base_height(X, Y)
    R = np.sqrt(X * X + Y * Y)
    TH = np.arctan2(Y, X)
    RP = 46.0 + 5.0 * np.sin(2 * TH + 0.6) + 3.0 * np.sin(3 * TH + 2.0)
    wp = 1 - smoothstep((R - RP - 5.0) / 24.0)
    H1 = H0 + (PLAZA_Z - H0) * wp

    # level the workshop plots before the roads are laid, so the access paths meet them
    plan.plots = []
    base = HeightGrid(H1.copy())
    for k, (px, py) in enumerate(WORKSHOP_PLOTS):
        cheb = np.maximum(np.abs(X - px), np.abs(Y - py))
        # plot level = ground where its access path leaves the village road, so the path stays flat
        jx, jy = next(r for r in ROADS if r["id"] == f"plot_path_{k + 1}")["pts"][0]
        pad = float(base.at(jx, jy))
        H1 = H1 + (pad - H1) * (1 - smoothstep((cheb - PLOT_HALF - 2.0) / PLOT_BLEND))
        plan.plots.append(dict(x=px, y=py, z=pad))

    _build_roads(plan, H1)
    W, Zr, clear = _road_fields(plan, X, Y)
    plan.road_clear = clear
    g_road = HeightGrid(H1 + (Zr - H1) * W)

    buildings = _place_buildings(plan, manifest, g_road)
    H2 = H1.copy()
    for inst in buildings:
        fp = plan.footprints[inst["uid"]]
        d = np.sqrt((X - fp.cx) ** 2 + (Y - fp.cy) ** 2)
        w = 1 - smoothstep((d - fp.radius * 0.82 - 2.0) / 13.0)
        H2 = H2 + (inst["pad_z"] - H2) * w
    H3 = H2 + (Zr - H2) * W

    # stream and pond
    st = Polyline(STREAM_PTS, step=3.0)
    g3 = HeightGrid(H3)
    zb = tr.smooth_1d(g3.bilinear(st.xy[:, 0], st.xy[:, 1]), 21, passes=3) - 4.4
    zb = np.minimum.accumulate(zb)
    st.z = tr.smooth_1d(zb, 9, passes=2)
    _d, s_pond = st.nearest(*POND_AT)
    st.hw = 5.5 + 30.0 * np.exp(-((st.s - s_pond) / 40.0) ** 2)
    bank = 9.0 + 7.0 * np.exp(-((st.s - s_pond) / 55.0) ** 2)
    st.bank = bank
    plan.stream = st
    D, Zw, HWw = tr.field_from_polyline(st, X, Y, reach=30.0)
    inside = D < HWw
    carve = Zw - 0.5 - 2.7 * (1 - np.clip(D / np.maximum(HWw, 1e-6), 0, 1) ** 2)
    H4 = np.where(inside, np.minimum(H3, carve), H3)
    # banks: use the local bank width (approximate it from the half width)
    bw = 9.0 + 7.0 * np.clip((HWw - 5.5) / 30.0, 0, 1)
    t = (D - HWw) / bw
    zone = (~inside) & (t < 1.0)
    target = (Zw - 0.5) + (H3 - (Zw - 0.5)) * smoothstep(t)
    H4 = np.where(zone, np.minimum(H4, target), H4)
    plan.water_clear = np.where(np.isfinite(D), D - HWw, 1e6)

    # Roads and building pads near a plot pull its ground out of level again.  Level it once more
    # at the end, except where a road lies (the access path ends inside the plot at pad height).
    for plot in plan.plots:
        cheb = np.maximum(np.abs(X - plot["x"]), np.abs(Y - plot["y"]))
        w = (1 - smoothstep((cheb - PLOT_HALF) / 10.0)) * (1 - W)
        H4 = H4 + (plot["z"] - H4) * w

    plan.grid = HeightGrid(H4)
    for inst in buildings:
        inst["z"] = plan.grid.at(inst["x"], inst["y"])
    plan.instances.extend(buildings)

    # bridge where the east road crosses the stream
    east = plan.road("east_road")
    best = (1e9, 0.0)
    for i in range(len(east["poly"].xy)):
        d, _s = st.nearest(*east["poly"].xy[i])
        if d < best[0]:
            best = (d, float(east["poly"].s[i]))
    p, tdir, z = east["poly"].at(best[1])
    plan.bridge = dict(road="east_road", s=best[1], x=float(p[0]), y=float(p[1]), z=z,
                       rot=math.degrees(math.atan2(tdir[1], tdir[0])))
    east["gaps"] = [(best[1] - BRIDGE_HALF + 0.6, best[1] + BRIDGE_HALF - 0.6)]

    # terrain material per cell (used for mesh colours and the Roblox voxel option)
    Hc = H4
    gx = (Hc[:-1, 1:] - Hc[:-1, :-1] + Hc[1:, 1:] - Hc[1:, :-1]) / (2 * tr.CELL)
    gy = (Hc[1:, :-1] - Hc[:-1, :-1] + Hc[1:, 1:] - Hc[:-1, 1:]) / (2 * tr.CELL)
    slope = np.sqrt(gx * gx + gy * gy)

    def cell(a):
        return (a[:-1, :-1] + a[:-1, 1:] + a[1:, :-1] + a[1:, 1:]) / 4

    wc = cell(plan.water_clear)
    mat = np.zeros(slope.shape, dtype=np.int8)                 # 0 grass
    mat[slope > 0.95] = 1                                      # 1 rock (very steep only)
    mat[wc < 3.0] = 2                                          # 2 shore
    mat[wc < -0.8] = 3                                         # 3 stream bed (under water)
    plan.material = mat
    plan.slope = slope
    return plan


# ---------------------------------------------------------------- props (hand placed + rule based)
class Placer:
    def __init__(self, plan, manifest):
        self.plan, self.manifest = plan, manifest
        self.rng = random.Random(SEED)
        self.count = {}
        self.cells = {}          # spatial hash for spacing checks

    def uid(self, asset):
        self.count[asset] = self.count.get(asset, 0) + 1
        return f"{asset}#{self.count[asset]}"

    def add(self, asset, x, y, rot=0.0, scale=1.0, group="props", name=None, dz=0.0, z=None, radius=None):
        assert asset in self.manifest, asset
        inst = dict(asset=asset, x=float(x), y=float(y), rot=float(rot) % 360.0, scale=float(scale),
                    group=group, uid=self.uid(asset))
        inst["z"] = (self.plan.grid.at(x, y) if z is None else z) + dz
        if name:
            inst["name"] = name
        self.plan.instances.append(inst)
        if radius is None:
            b = self.manifest[asset]["bounds_blender"]
            radius = 0.35 * max(b["max"][0] - b["min"][0], b["max"][1] - b["min"][1]) * scale
        self.cells.setdefault((int(x // 16), int(y // 16)), []).append((x, y, radius))
        return inst

    def free(self, x, y, radius, road=1.0, water=1.5, building=1.5):
        """True if a disc at (x, y) collides with nothing important."""
        if abs(x) > HALF - 6 or abs(y) > HALF - 6:
            return False
        if in_plot(x, y, radius + 2.0):
            return False
        if _sample(self.plan.road_clear, x, y) < radius * 0.6 + road:
            return False
        if _sample(self.plan.water_clear, x, y) < radius * 0.5 + water:
            return False
        for fp in self.plan.footprints.values():
            if math.hypot(x - fp.cx, y - fp.cy) < fp.radius + radius + building and \
                    fp.contains(x, y, radius * 0.7 + building):
                return False
        cx, cy = int(x // 16), int(y // 16)
        for i in (cx - 1, cx, cx + 1):
            for j in (cy - 1, cy, cy + 1):
                for ox, oy, orad in self.cells.get((i, j), ()):
                    if math.hypot(x - ox, y - oy) < (radius + orad) * 0.85:
                        return False
        return True

    def in_plaza(self, x, y, margin=0.0):
        return math.hypot(x, y) < plaza_radius(math.atan2(y, x)) + margin

    def line(self, asset, pts, group="props", end_post=None, flip=False):
        """Chain 8-stud segments along a polyline."""
        seg = 8.0
        last = None
        for a, b in zip(pts[:-1], pts[1:]):
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, round(length / seg))
            ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
            start = (length - n * seg) / 2
            rot = math.degrees(math.atan2(uy, ux)) + (180 if flip else 0)
            for i in range(n):
                d = start + seg * (i + 0.5)
                x, y = a[0] + ux * d, a[1] + uy * d
                if _sample(self.plan.road_clear, x, y) < 1.5 or _sample(self.plan.water_clear, x, y) < 1.0:
                    continue
                if in_plot(x, y, 3.0):
                    continue
                self.add(asset, x, y, rot=rot, group=group, radius=1.0)
                last = (a[0] + ux * (d + seg / 2), a[1] + uy * (d + seg / 2)) if not flip else \
                    (a[0] + ux * (d - seg / 2), a[1] + uy * (d - seg / 2))
            if end_post and last:
                self.add(end_post, last[0], last[1], rot=rot, group=group, radius=0.6)

    def along_road(self, rid, s, side, offset):
        rd = self.plan.road(rid)
        p, t, z = rd["poly"].at(s)
        n = np.array([-t[1], t[0]]) * side
        pos = p + n * (rd["hw"] + offset)
        return float(pos[0]), float(pos[1]), face_rot(-n[0], -n[1]), t


def place_props(plan, manifest):
    P = Placer(plan, manifest)
    rng = P.rng
    grid = plan.grid

    # --- village square
    P.add("fountain", 0, 0, name="Marktbrunnen", z=PLAZA_Z, dz=0.3)
    for ang, asset in ((-58, "market_stall_fruit"), (-22, "market_stall_bread"), (212, "market_stall_cloth"),
                       (146, "market_stall_fruit"), (68, "market_stall_cloth")):
        a = math.radians(ang)
        x, y = 27 * math.cos(a), 27 * math.sin(a)
        P.add(asset, x, y, rot=face_rot(-x, -y) + rng.uniform(-8, 8), group="market")
    for ang in (20, 105, 180, 250, 318):
        a = math.radians(ang)
        r = plaza_radius(a) - 5.5
        P.add("lantern_post_double", r * math.cos(a), r * math.sin(a), rot=math.degrees(a) + 90, group="lights")
    for ang in (38, 128, 232, 296):
        a = math.radians(ang)
        r = plaza_radius(a) - 9.0
        P.add("bench", r * math.cos(a), r * math.sin(a), rot=face_rot(-math.cos(a), -math.sin(a)))
    for ang in (2, 90, 158, 268):
        a = math.radians(ang)
        r = plaza_radius(a) - 7.5
        P.add("planter", r * math.cos(a) + 3 * math.sin(a), r * math.sin(a) - 3 * math.cos(a), rot=rng.uniform(0, 360))
    P.add("notice_board", -20, 37, rot=face_rot(20, -37), name="Anschlagtafel")
    P.add("banner_pole", 14, 14, rot=30)
    P.add("banner_pole", -15, -13, rot=210)
    P.add("cart", 31, -30, rot=205)
    P.add("barrel_stack", 40, -37, rot=15)
    P.add("crate_stack", -29, -27, rot=40)
    P.add("sack_pile", -36, -20, rot=-10)
    P.add("tree_blossom", 30, 31, group="nature", scale=1.15)
    P.add("tree_blossom", -33, 22, group="nature", scale=1.05)
    P.add("tree_round", -6, -37, group="nature", scale=1.1)

    # --- gates, signposts, well
    for rid, s in (("south_road", 96), ("east_road", 318)):
        x, y, _rot, t = P.along_road(rid, s, 1, -plan.road(rid)["hw"])
        P.add("gate_arch", x, y, rot=math.degrees(math.atan2(t[1], t[0])) + 90, name="Dorftor")
    for rid, s, side in (("south_road", 212, -1), ("east_road", 52, 1), ("west_road", 44, 1), ("north_road", 86, 1),
                         ("east_road", 172, 1), ("mill_lane", 122, 1)):
        x, y, rot, _t = P.along_road(rid, s, side, 3.0)
        if P.free(x, y, 1.0, road=0.5):
            P.add("signpost", x, y, rot=rot + rng.uniform(-25, 25))
    P.add("well", -78, 108, rot=20, name="Dorfbrunnen")
    P.add("bench", -70, 99, rot=face_rot(-8, 9))
    P.add("tree_oak_a", -66, 118, group="nature", scale=1.1)

    # --- bridge, pond
    br = plan.bridge
    P.add("bridge_stone", br["x"], br["y"], rot=br["rot"], z=br["z"], dz=0.12, name="Steinbruecke", radius=1.0)
    st = plan.stream
    _d, s_pond = st.nearest(*POND_AT)
    wz = float(np.interp(s_pond, st.s, st.z))
    P.add("dock", 137.0, -101.5, rot=face_rot(1, -0.12) + 180, z=wz, dz=1.0, name="Bootssteg", radius=1.0)
    P.add("rowboat", 152, -112, rot=35, z=wz, dz=0.0, radius=1.0)
    for ang in range(0, 360, 24):
        a = math.radians(ang + rng.uniform(-8, 8))
        r = 35.5 + rng.uniform(-6, 2)
        x, y = POND_AT[0] + r * math.cos(a) * 0.95, POND_AT[1] + r * math.sin(a) * 1.25
        wc = _sample(plan.water_clear, x, y)
        if -7 < wc < -0.5 and math.hypot(x - 137, y + 101) > 12:
            P.add("reeds", x, y, rot=rng.uniform(0, 360), group="nature", z=wz, dz=-0.9, scale=rng.uniform(0.9, 1.3))
    for dx, dy in ((8, 12), (-6, -16), (14, -9), (-14, 6), (2, 26)):
        P.add("lily_pads", POND_AT[0] + dx, POND_AT[1] + dy, rot=rng.uniform(0, 360), group="nature", z=wz,
              dz=0.05, radius=1.0)

    # --- street lanterns along the main streets
    for rd in plan.roads:
        if rd["kind"] == "path":
            continue
        gap = 46.0 if rd["kind"] == "main" else 58.0
        s, side = gap * 0.6, 1
        while s < rd["poly"].length - 12:
            x, y, rot, _t = P.along_road(rd["id"], s, side, 2.2)
            if not P.in_plaza(x, y, 6) and P.free(x, y, 0.8, road=0.3, water=4.0) and abs(x) < 350 and abs(y) < 350:
                P.add("lantern_post", x, y, rot=rot, group="lights")
            s += gap
            side = -side

    # --- gardens and yards (coordinates local to a building: +Y = behind the house)
    def b(asset):
        return next(i for i in plan.instances if i["asset"] == asset)

    def yard(asset, rect, fence, gate_side=None, extras=()):
        inst = b(asset)
        x0, y0, x1, y1 = rect
        cs = [local_to_world(inst, *c) for c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        sides = [(cs[0], cs[1]), (cs[1], cs[2]), (cs[2], cs[3]), (cs[3], cs[0])]
        for k, (p0, p1) in enumerate(sides):
            if k == gate_side:
                continue
            P.line(fence, [p0, p1], end_post="fence_post" if fence == "fence_wood" else None)
        for item, lx, ly, lrot in extras:
            x, y = local_to_world(inst, lx, ly)
            if _sample(plan.road_clear, x, y) > 1.0:
                P.add(item, x, y, rot=inst["rot"] + lrot, group="nature" if item in manifest and
                      manifest[item]["category"] == "nature" else "props")

    yard("house_03_thatched_cottage", (-22, 10, 22, 34), "fence_picket", gate_side=0, extras=(
        ("garden_bed", -10, 22, 0), ("garden_bed", 4, 22, 0), ("beehives", 15, 28, 90), ("tree_apple", -15, 30, 0),
        ("flowers_white", 13, 15, 0)))
    yard("house_14_long_weaver_house", (-24, 11, 24, 32), "fence_wood", gate_side=0, extras=(
        ("clothesline", 0, 22, 0), ("woodpile", -16, 16, 0), ("tree_apple", 17, 25, 0)))
    yard("house_01_timber_cottage", (-17, 10, 17, 30), "fence_picket", gate_side=0, extras=(
        ("garden_bed", -7, 20, 0), ("flowers_red", 8, 16, 0), ("tree_blossom", 9, 24, 0)))
    yard("house_04_farmhouse", (-22, 9, 26, 34), "fence_wood", gate_side=0, extras=(
        ("haystack", 16, 24, 0), ("woodpile", -14, 14, 0), ("garden_bed", -6, 26, 0), ("trough", 6, 14, 0)))
    yard("house_18_tiny_cottage", (-13, 7, 13, 24), "fence_picket", gate_side=0, extras=(
        ("garden_bed", 0, 16, 0), ("flowers_yellow", -8, 12, 0)))
    yard("house_08_plank_cabin", (-20, 9, 20, 30), "fence_wood", gate_side=0, extras=(
        ("woodpile", 12, 14, 0), ("tree_stump", -10, 18, 0), ("log_pile", -3, 24, 20)))
    yard("house_10_saltbox", (-17, 13, 17, 34), "hedge", gate_side=0, extras=(
        ("clothesline", 0, 24, 0), ("pumpkin_patch", -10, 20, 0)))
    yard("house_16_porch_tower_house", (-20, 9, 20, 28), "fence_picket", gate_side=0, extras=(
        ("garden_bed", -9, 18, 0), ("tree_apple", 10, 20, 0)))
    yard("house_07_stone_manor", (-24, 12, 24, 36), "stone_wall", gate_side=0, extras=(
        ("tree_round", -14, 24, 0), ("tree_round", 14, 24, 0), ("bench", 0, 30, 0), ("flowers_blue", 0, 20, 0),
        ("planter", -6, 16, 0), ("planter", 6, 16, 0)))
    yard("house_09_twin_gable", (-22, 11, 22, 30), "hedge", gate_side=0, extras=(
        ("flowers_red", -10, 18, 0), ("flowers_white", 10, 18, 0), ("tree_blossom", 0, 23, 0)))
    yard("house_13_fisher_hut", (-12, 8, 12, 8.1), "fence_wood", extras=(
        ("barrel", 11, -3, 0), ("crate_stack", -12, 2, 30)))
    yard("lm_chapel", (-34, -30, 34, 44), "stone_wall", gate_side=0, extras=(
        ("tree_poplar", -26, -16, 0), ("tree_poplar", 26, -16, 0), ("tree_oak_b", -24, 30, 0),
        ("bench", 22, -6, 90), ("flowers_white", -20, 6, 0), ("flowers_blue", 20, 22, 0), ("rock_c", 24, 34, 0)))
    yard("lm_tavern", (-26, 16, 26, 36), "fence_wood", gate_side=0, extras=(
        ("barrel_stack", -20, 20, 0), ("woodpile", 14, 22, 0), ("cart", -4, 28, 90), ("hay_bale", 20, 30, 0)))
    yard("lm_smithy", (-16, 12, 22, 12.1), "fence_wood", extras=(
        ("crate_stack", -15, 2, 0), ("barrel", -14, -6, 0), ("woodpile", 2, 15, 0)))

    # --- farm: barn yard and fenced fields
    barn = b("house_17_red_barn")
    for item, lx, ly, lrot in (("haystack", 26, -6, 0), ("haystack", 30, 8, 0), ("hay_bale", 22, 16, 30),
                               ("hay_bale", 25, 20, -20), ("cart", -26, -12, 80), ("trough", -24, 6, 90),
                               ("scarecrow", 46, 46, 180), ("beehives", -30, 22, 90)):
        x, y = local_to_world(barn, lx, ly)
        if P.free(x, y, 2.0, road=0.5):
            P.add(item, x, y, rot=barn["rot"] + lrot)
    fx0, fy0, fx1, fy1 = 16, 30, 72, 70                         # wheat field behind the barn
    corners = [local_to_world(barn, *c) for c in ((fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1), (fx0, fy0))]
    P.line("fence_wood", corners, end_post="fence_post")
    for ix in range(6):
        for iy in range(4):
            x, y = local_to_world(barn, fx0 + 6 + ix * 8.8, fy0 + 6 + iy * 9.0)
            if P.free(x, y, 3.0, road=1.0):
                P.add("wheat_patch", x, y, rot=barn["rot"] + rng.choice((0, 90, 180, 270)), group="nature",
                      scale=rng.uniform(1.0, 1.12))
    for k in range(5):                                           # pumpkin rows next to the field
        x, y = local_to_world(barn, -30 + k * 9, 44)
        if P.free(x, y, 2.5):
            P.add("pumpkin_patch", x, y, rot=rng.uniform(0, 360), group="nature")

    # --- mill and tower surroundings
    mill = b("lm_windmill")
    for item, lx, ly in (("sack_pile", 12, -12), ("cart", -15, -14), ("barrel", 13, -6), ("hay_bale", -17, 4)):
        x, y = local_to_world(mill, lx, ly)
        if P.free(x, y, 1.5, road=0.3):
            P.add(item, x, y, rot=rng.uniform(0, 360))
    tower = b("lm_watchtower")
    for item, lx, ly in (("crate_stack", 11, -6), ("barrel", -11, -5), ("banner_pole", -9, -13), ("rock_large", 20, 14)):
        x, y = local_to_world(tower, lx, ly)
        if P.free(x, y, 1.5, road=0.3):
            P.add(item, x, y, rot=rng.uniform(0, 360), group="nature" if item.startswith("rock") else "props")

    # --- orchard between Feldgasse and Suedstrasse
    for ix in range(4):
        for iy in range(3):
            x = -62 + ix * 17 + rng.uniform(-2, 2)
            y = -118 + iy * 17 + rng.uniform(-2, 2) + ix * 5
            if P.free(x, y, 5.0, road=3.0, building=4.0):
                P.add("tree_apple", x, y, rot=rng.uniform(0, 360), scale=rng.uniform(0.9, 1.12), group="nature")
    return P


# ---------------------------------------------------------------- nature scatter
def scatter_nature(plan, manifest, P):
    rng = P.rng
    grid = plan.grid

    def zone(x, y):
        """0 = village core, 1 = outskirts / meadows, 2 = forest edge."""
        edge = max(abs(x), abs(y))
        r = math.hypot(x, y)
        f = (edge - 250) / 70 + 0.25 * float(tr.noise(x * 1.3, y * 1.3)) + (r - 300) / 400
        return f

    # forest and loose trees
    step = 15.0
    n = int(tr.WORLD / step)
    for j in range(n):
        for i in range(n):
            x = -HALF + (i + 0.5) * step + rng.uniform(-6.0, 6.0)
            y = -HALF + (j + 0.5) * step + rng.uniform(-6.0, 6.0)
            f = zone(x, y)
            h = grid.at(x, y)
            dens = 0.03 + 0.52 * float(smoothstep(f)) + 0.18 * float(smoothstep((h - 14) / 14))
            copse = float(tr.noise(x * 2.2 + 500, y * 2.2 + 120))
            if f < 0.1 and copse > 0.45 and math.hypot(x, y) > 120:
                dens += 0.4                                         # small copses in the meadows
            if rng.random() > dens:
                continue
            if grid.slope(x, y) > 0.75:
                continue
            high = h > 19 or f > 0.75
            if high:
                asset = rng.choices(("tree_pine_a", "tree_pine_b", "tree_pine_c", "tree_oak_b"), (4, 3, 3, 1))[0]
            elif f > 0.15:
                asset = rng.choices(("tree_oak_a", "tree_oak_b", "tree_pine_a", "tree_pine_b", "tree_birch",
                                     "tree_autumn", "tree_poplar"), (4, 4, 2, 2, 3, 1.2, 0.6))[0]
            else:
                asset = rng.choices(("tree_oak_a", "tree_birch", "tree_round", "tree_autumn", "tree_poplar",
                                     "tree_oak_b"), (3, 3, 2, 1, 1, 1))[0]
            radius = 4.2 if "pine" in asset else 5.0
            if not P.free(x, y, radius, road=3.5, water=7.0, building=5.0) or P.in_plaza(x, y, 10):
                continue
            P.add(asset, x, y, rot=rng.uniform(0, 360), scale=rng.uniform(0.85, 1.3), group="nature", dz=-0.3,
                  radius=radius * 0.8)

    # undergrowth: bushes, rocks, flowers, grass, mushrooms
    def sprinkle(count, choose, radius, cond, scale=(0.85, 1.25), sink=-0.1, **free_kw):
        placed = tries = 0
        while placed < count and tries < count * 30:
            tries += 1
            x, y = rng.uniform(-HALF + 8, HALF - 8), rng.uniform(-HALF + 8, HALF - 8)
            if P.in_plaza(x, y, 4) or not cond(x, y):
                continue
            if not P.free(x, y, radius, **free_kw):
                continue
            P.add(choose(x, y), x, y, rot=rng.uniform(0, 360), scale=rng.uniform(*scale), group="nature", dz=sink,
                  radius=radius)
            placed += 1
        return placed

    near_village = lambda x, y: math.hypot(x, y) < 250
    sprinkle(110, lambda x, y: rng.choice(("bush_a", "bush_b", "bush_berry", "bush_a")), 2.4,
             lambda x, y: grid.slope(x, y) < 0.7 and (zone(x, y) > -0.6 or rng.random() < 0.35), road=1.5)
    sprinkle(46, lambda x, y: rng.choice(("rock_a", "rock_b", "rock_c")), 2.6,
             lambda x, y: grid.at(x, y) > 9 or zone(x, y) > 0.2 or rng.random() < 0.12, sink=-0.35, road=2.0)
    sprinkle(26, lambda x, y: "rock_large", 6.5,
             lambda x, y: (grid.at(x, y) > 14 or zone(x, y) > 0.4) and grid.slope(x, y) < 0.6, sink=-0.8, road=5.0,
             building=8.0)
    sprinkle(16, lambda x, y: "rock_cliff", 11.0,
             lambda x, y: (grid.at(x, y) > 20 or max(abs(x), abs(y)) > 330), sink=-2.0, road=10.0, building=14.0)
    sprinkle(40, lambda x, y: rng.choice(("rock_a", "rock_b")), 2.2,
             lambda x, y: 1.0 < _sample(plan.water_clear, x, y) < 9.0, sink=-0.4, water=0.5, road=2.0)
    sprinkle(140, lambda x, y: rng.choice(("flowers_red", "flowers_yellow", "flowers_blue", "flowers_white")), 2.2,
             lambda x, y: near_village(x, y) and grid.slope(x, y) < 0.5 and float(tr.noise(x * 3 + 77, y * 3)) > -0.25,
             road=1.0, building=1.0)
    sprinkle(40, lambda x, y: rng.choice(("flowers_red", "flowers_yellow", "flowers_blue", "flowers_white")), 2.2,
             lambda x, y: not near_village(x, y) and zone(x, y) < 0.5, road=1.0)
    sprinkle(260, lambda x, y: "grass_tuft", 1.0, lambda x, y: grid.slope(x, y) < 0.8, scale=(0.9, 1.6), road=0.6,
             building=0.8, water=0.8)
    sprinkle(40, lambda x, y: "mushrooms", 1.0, lambda x, y: zone(x, y) > 0.35, scale=(1.0, 1.6), road=1.0)
    sprinkle(26, lambda x, y: rng.choice(("tree_stump", "log_pile")), 3.0, lambda x, y: zone(x, y) > 0.2, road=3.0)
    sprinkle(40, lambda x, y: "reeds", 1.4, lambda x, y: -3.5 < _sample(plan.water_clear, x, y) < -0.3,
             scale=(0.9, 1.3), sink=-0.3, water=-50, road=4.0)


def build_plan(manifest):
    """Compute terrain, buildings, props and nature. manifest = asset manifest dict."""
    plan = Plan()
    build_terrain(plan, manifest)
    P = place_props(plan, manifest)
    scatter_nature(plan, manifest, P)
    for inst in plan.instances:
        inst["z"] = round(float(inst["z"]), 3)
        inst["x"], inst["y"] = round(inst["x"], 3), round(inst["y"], 3)
        inst["rot"] = round(inst["rot"] % 360.0, 2)
        inst["scale"] = round(inst["scale"], 3)
    return plan
