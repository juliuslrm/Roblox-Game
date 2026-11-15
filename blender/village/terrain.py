"""Terrain model of the village world (pure numpy, no Blender needed).

The terrain is a regular height grid.  Every other system (roads, building
pads, scatter, Roblox voxel terrain) reads heights from this one grid using
the same triangulation as the exported terrain mesh, so objects sit exactly
on the visible ground.
"""
import math

import numpy as np

WORLD = 768.0            # world edge length in studs
HALF = WORLD / 2
CELL = 4.0               # grid spacing = Roblox voxel size
N = int(WORLD / CELL)    # cells per side (192)
CHUNK_CELLS = 32         # 6 x 6 terrain chunks of 128 studs


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def grid_xy():
    axis = np.linspace(-HALF, HALF, N + 1)
    return np.meshgrid(axis, axis)          # X[j, i], Y[j, i]


# ------------------------------------------------------------------ noise
_WAVES = [(0.0131, 0.7, 1.3, 1.0), (0.0173, 2.1, 4.1, 0.8), (0.0247, 3.9, 0.4, 0.55),
          (0.0389, 5.3, 2.2, 0.35), (0.0611, 1.4, 5.0, 0.2), (0.0933, 4.4, 3.3, 0.12)]


def noise(x, y, scale=1.0):
    """Cheap deterministic pseudo noise in roughly [-1, 1]."""
    out = 0.0
    for k, ang, ph, amp in _WAVES:
        out = out + amp * np.sin(k * scale * (x * math.cos(ang) + y * math.sin(ang)) + ph) \
            * np.cos(k * scale * 0.83 * (-x * math.sin(ang) + y * math.cos(ang)) + ph * 1.7)
    return out / 1.9


# ------------------------------------------------------------------ base terrain
HILLS = [                   # (x, y, height, sigma)
    (88.0, 262.0, 24.0, 72.0),       # chapel hill (north)
    (-262.0, 182.0, 36.0, 74.0),     # windmill hill (north-west)
    (276.0, 128.0, 30.0, 62.0),      # watchtower ridge (east)
    (-215.0, -265.0, 15.0, 88.0),    # farm knoll (south-west)
    (305.0, -215.0, 18.0, 80.0),     # wooded hill beyond the pond (south-east)
    (-60.0, 330.0, 14.0, 70.0),      # northern forest rise
]


def base_height(x, y):
    h = 2.6 * noise(x, y) + 0.8 * noise(x + 300, y - 170, 2.7)
    for hx, hy, hh, hs in HILLS:
        h = h + hh * np.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * hs * hs))
    r = np.sqrt(x * x + y * y)
    edge = np.maximum(np.abs(x), np.abs(y))
    h = h + (16.0 + 9.0 * noise(x * 1.4 + 90, y * 1.4 - 40)) * smoothstep((edge - 285.0) / 95.0)
    core = smoothstep(1.0 - r / 150.0)
    return h * (1.0 - 0.9 * core)


# ------------------------------------------------------------------ polylines
def catmull_rom(points, step=3.0):
    """Uniformly resampled centripetal-ish Catmull-Rom curve through points."""
    pts = [np.array(p, dtype=float) for p in points]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    dense = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        n = max(4, int(np.linalg.norm(p2 - p1) / 1.0))
        for k in range(n):
            t = k / n
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(pts[-1])
    dense = np.array(dense)
    seg = np.linalg.norm(np.diff(dense, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = s[-1]
    m = max(2, int(round(total / step)))
    target = np.linspace(0.0, total, m + 1)
    out = np.stack([np.interp(target, s, dense[:, 0]), np.interp(target, s, dense[:, 1])], axis=1)
    return out, target


def smooth_1d(v, window, passes=2):
    v = np.asarray(v, dtype=float)
    k = max(1, int(window)) | 1
    for _ in range(passes):
        pad = np.pad(v, (k // 2, k // 2), mode="edge")
        v = np.convolve(pad, np.ones(k) / k, mode="valid")
    return v


class Polyline:
    """Resampled 2D curve with per-point attributes (z, half width)."""

    def __init__(self, points, step=3.0):
        self.xy, self.s = catmull_rom(points, step)
        self.length = float(self.s[-1])
        self.z = np.zeros(len(self.xy))
        self.hw = np.zeros(len(self.xy))

    def tangent(self, i):
        a = self.xy[max(i - 1, 0)]
        b = self.xy[min(i + 1, len(self.xy) - 1)]
        d = b - a
        return d / np.linalg.norm(d)

    def at(self, s):
        """Position, tangent and z at arc length s."""
        s = float(np.clip(s, 0.0, self.length))
        x = np.interp(s, self.s, self.xy[:, 0])
        y = np.interp(s, self.s, self.xy[:, 1])
        i = int(np.clip(np.searchsorted(self.s, s), 1, len(self.s) - 1))
        d = self.xy[i] - self.xy[i - 1]
        return np.array([x, y]), d / np.linalg.norm(d), float(np.interp(s, self.s, self.z))

    def nearest(self, x, y):
        """(distance, arc length) of the closest point for scalar x, y."""
        d2 = (self.xy[:, 0] - x) ** 2 + (self.xy[:, 1] - y) ** 2
        i = int(np.argmin(d2))
        return float(math.sqrt(d2[i])), float(self.s[i])


def field_from_polyline(poly, X, Y, reach):
    """For every grid vertex within `reach`: distance to the polyline plus the
    interpolated z and half width at the closest point.  Returns (D, Z, HW)
    where D is inf outside the reach."""
    D = np.full(X.shape, np.inf)
    Z = np.zeros(X.shape)
    HW = np.zeros(X.shape)
    xy = poly.xy
    for k in range(len(xy) - 1):
        a, b = xy[k], xy[k + 1]
        r = reach + float(max(poly.hw[k], poly.hw[k + 1]))
        i0 = max(0, int((min(a[0], b[0]) - r + HALF) / CELL))
        i1 = min(N, int((max(a[0], b[0]) + r + HALF) / CELL) + 1)
        j0 = max(0, int((min(a[1], b[1]) - r + HALF) / CELL))
        j1 = min(N, int((max(a[1], b[1]) + r + HALF) / CELL) + 1)
        if i0 > i1 or j0 > j1:
            continue
        sx, sy = X[j0:j1 + 1, i0:i1 + 1], Y[j0:j1 + 1, i0:i1 + 1]
        ab = b - a
        t = np.clip(((sx - a[0]) * ab[0] + (sy - a[1]) * ab[1]) / (ab @ ab), 0.0, 1.0)
        d = np.sqrt((sx - (a[0] + t * ab[0])) ** 2 + (sy - (a[1] + t * ab[1])) ** 2)
        sub = D[j0:j1 + 1, i0:i1 + 1]
        better = d < sub
        sub[better] = d[better]
        Z[j0:j1 + 1, i0:i1 + 1][better] = (poly.z[k] + t * (poly.z[k + 1] - poly.z[k]))[better]
        HW[j0:j1 + 1, i0:i1 + 1][better] = (poly.hw[k] + t * (poly.hw[k + 1] - poly.hw[k]))[better]
    return D, Z, HW


# ------------------------------------------------------------------ height grid
class HeightGrid:
    """Height samples on the (N+1)^2 vertex grid with mesh-exact lookup."""

    def __init__(self, H):
        self.H = H

    def at(self, x, y):
        """Height of the terrain *mesh* at (x, y) (same diagonal split)."""
        fx = min(max((x + HALF) / CELL, 0.0), N - 1e-9)
        fy = min(max((y + HALF) / CELL, 0.0), N - 1e-9)
        i, j = int(fx), int(fy)
        u, v = fx - i, fy - j
        h00, h10, h01, h11 = self.H[j, i], self.H[j, i + 1], self.H[j + 1, i], self.H[j + 1, i + 1]
        if u >= v:
            return float(h00 + u * (h10 - h00) + v * (h11 - h10))
        return float(h00 + u * (h11 - h01) + v * (h01 - h00))

    def slope(self, x, y, d=3.0):
        return math.hypot(self.at(x + d, y) - self.at(x - d, y), self.at(x, y + d) - self.at(x, y - d)) / (2 * d)

    def bilinear(self, xs, ys):
        fx = np.clip((np.asarray(xs) + HALF) / CELL, 0, N - 1e-9)
        fy = np.clip((np.asarray(ys) + HALF) / CELL, 0, N - 1e-9)
        i, j = fx.astype(int), fy.astype(int)
        u, v = fx - i, fy - j
        H = self.H
        return (H[j, i] * (1 - u) * (1 - v) + H[j, i + 1] * u * (1 - v)
                + H[j + 1, i] * (1 - u) * v + H[j + 1, i + 1] * u * v)
