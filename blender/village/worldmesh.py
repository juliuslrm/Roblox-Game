"""Meshes that belong to this specific world: terrain chunks, roads, the
paved square and the water surface."""
import math

import numpy as np

from . import terrain as tr
from .plan import PLAZA_Z, plaza_radius

# terrain material classes (plan.material); the shore is drawn by bank_mesh(),
# so the terrain mesh itself keeps grass there
MATERIAL_LEGEND = ["grass", "rock", "shore", "bed"]
# steep cells stay grass on the mesh: per-cell rock colouring produced a jagged
# saw-tooth pattern along the stream banks
MATERIAL_COLOR = ["grass", "grass", "grass", "sand"]
SKIRT_DEPTH = 36.0


def terrain_chunk(mb, plan, ci, cj):
    """Build chunk (ci, cj); vertices are local to the chunk centre.
    Returns the chunk origin (x, y, 0) in world space."""
    H = plan.grid.H
    n = tr.CHUNK_CELLS
    i0, j0 = ci * n, cj * n
    ox = -tr.HALF + (i0 + n / 2) * tr.CELL
    oy = -tr.HALF + (j0 + n / 2) * tr.CELL
    verts, normals, vtone = [], [], []
    for j in range(n + 1):
        for i in range(n + 1):
            gi, gj = i0 + i, j0 + j
            x = -tr.HALF + gi * tr.CELL
            y = -tr.HALF + gj * tr.CELL
            verts.append((x - ox, y - oy, float(H[gj, gi])))
            hl, hr = H[gj, max(gi - 1, 0)], H[gj, min(gi + 1, tr.N)]
            hd, hu = H[max(gj - 1, 0), gi], H[min(gj + 1, tr.N), gi]
            sx = (hr - hl) / ((min(gi + 1, tr.N) - max(gi - 1, 0)) * tr.CELL)
            sy = (hu - hd) / ((min(gj + 1, tr.N) - max(gj - 1, 0)) * tr.CELL)
            k = math.sqrt(sx * sx + sy * sy + 1)
            normals.append((-sx / k, -sy / k, 1 / k))
            vtone.append(float(0.10 * tr.noise(x * 4.3 + 11, y * 4.3 - 7) + 0.16 * tr.noise(x * 1.1 + 40, y * 1.1 - 15)
                               + 0.004 * min(float(H[gj, gi]), 30.0)))
    faces, fcolor, ftone = [], [], []
    w = n + 1
    for j in range(n):
        for i in range(n):
            a, b, c, d = j * w + i, j * w + i + 1, (j + 1) * w + i + 1, (j + 1) * w + i
            col = MATERIAL_COLOR[int(plan.material[j0 + j, i0 + i])]
            faces += [(a, b, c), (a, c, d)]            # same diagonal as HeightGrid.at()
            fcolor += [col, col]
            ftone += [mb.jitter(0.018), mb.jitter(0.018)]
    mb.add(verts, faces, "grass", smooth=True, grad=(0.5, 0.5), vtone=vtone, fcolor=fcolor, ftone=ftone,
           normals=normals)

    # skirts along the outer world boundary so the world has no visible underside
    def skirt(idx, outward):
        top = [verts[k] for k in idx]
        sv = top + [(x, y, -SKIRT_DEPTH) for x, y, _z in top]
        m = len(top)
        sf = [(k, k + 1, m + k + 1, m + k) for k in range(m - 1)]
        nrm = [outward] * (2 * m)
        p0, p1, p2 = sv[0], sv[1], sv[m]
        cross = ((p1[1] - p0[1]) * (p2[2] - p0[2]) - (p1[2] - p0[2]) * (p2[1] - p0[1]),
                 (p1[2] - p0[2]) * (p2[0] - p0[0]) - (p1[0] - p0[0]) * (p2[2] - p0[2]),
                 (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0]))
        if cross[0] * outward[0] + cross[1] * outward[1] < 0:
            sf = [tuple(reversed(f)) for f in sf]
        mb.add(sv, sf, "rock_dark", smooth=True, grad=(0.3, 0.5), normals=nrm)

    last = tr.N // n - 1
    if cj == 0:
        skirt([i for i in range(w)], (0, -1, 0))
    if cj == last:
        skirt([n * w + i for i in range(w)], (0, 1, 0))
    if ci == 0:
        skirt([j * w for j in range(w)], (-1, 0, 0))
    if ci == last:
        skirt([j * w + n for j in range(w)], (1, 0, 0))
    return ox, oy


ROAD_STYLE = {
    # kind: (surface, edge, skirt, crown, kerb width)
    "main": ("cobble", "cobble_dark", "cobble_dark", 0.22, 0.9),
    "lane": ("cobble", "stone_warm", "cobble_dark", 0.16, 0.6),
    "path": ("dirt", "dirt_dark", "dirt_dark", 0.10, 0.5),
}


def road_mesh(mb, plan, rd):
    """Ribbon following the road: skirt | kerb | 4 surface strips | kerb | skirt."""
    poly = rd["poly"]
    surf, edge, skirtc, crown, kerb = ROAD_STYLE[rd["kind"]]
    hw = rd["hw"]
    lift = 0.14 + 0.07 * rd["layer"]
    offs = [-hw - 0.55, -hw, -hw + kerb, -hw / 2, 0.0, hw / 2, hw - kerb, hw, hw + 0.55]
    cols = [skirtc, edge, surf, surf, surf, surf, edge, skirtc]
    rng = mb.rng
    gaps = rd.get("gaps", [])

    def in_gap(s):
        return any(a < s < b for a, b in gaps)

    section = []
    sections = []
    for i in range(len(poly.xy)):
        if in_gap(poly.s[i]):
            if len(section) > 1:
                sections.append(section)
            section = []
            continue
        section.append(i)
    if len(section) > 1:
        sections.append(section)

    for section in sections:
        rows = []
        for i in section:
            p = poly.xy[i]
            t = poly.tangent(i)
            nx, ny = -t[1], t[0]
            zc = max(poly.z[i], plan.grid.at(p[0], p[1]), plan.grid.at(p[0] + nx * hw, p[1] + ny * hw),
                     plan.grid.at(p[0] - nx * hw, p[1] - ny * hw)) + lift
            row = []
            for k, o in enumerate(offs):
                x, y = p[0] + nx * o, p[1] + ny * o
                if k in (0, len(offs) - 1):
                    z = min(zc, plan.grid.at(x, y)) - 1.3
                else:
                    z = zc + crown * (1 - (o / hw) ** 2) + (0.06 if k in (1, len(offs) - 2) else 0.0)
                row.append((float(x), float(y), float(z)))
            rows.append(row)
        # close both ends with a short drop so the ribbon has no open edge
        for end, src in ((0, rows[0]), (len(rows), rows[-1])):
            i = section[0] if end == 0 else section[-1]
            t = poly.tangent(i) * (-0.5 if end == 0 else 0.5)
            rows.insert(end, [(x + float(t[0]), y + float(t[1]), z - 1.3) for x, y, z in src])
        fcolor, ftone = [], []
        for _j in range(len(rows) - 1):
            for k in range(len(offs) - 1):
                fcolor.append(cols[k])
                ftone.append(rng.uniform(-0.09, 0.09) if cols[k] == surf else rng.uniform(-0.04, 0.04))
        mb.sheet(rows, surf, grad=(0.5, 0.5), fcolor=fcolor, ftone=ftone)


def plaza_mesh(mb):
    """Paved village square with concentric paving bands around the fountain."""
    seg = 48
    fracs = [0.2, 0.34, 0.48, 0.62, 0.76, 0.9, 1.0]
    rows = []
    z = PLAZA_Z + 0.34
    for f in fracs:
        row = []
        for k in range(seg):
            th = 2 * math.pi * k / seg
            r = plaza_radius(th) * f if f > 0.3 else 46.0 * f
            row.append((r * math.cos(th), r * math.sin(th), z))
        rows.append(row)
    rows.append([((plaza_radius(2 * math.pi * k / seg) + 0.6) * math.cos(2 * math.pi * k / seg),
                  (plaza_radius(2 * math.pi * k / seg) + 0.6) * math.sin(2 * math.pi * k / seg), z - 1.6)
                 for k in range(seg)])
    band = ["cobble", "stone_warm", "cobble", "cobble_dark", "cobble", "stone_warm", "cobble_dark"]
    fcolor, ftone = [], []
    rng = mb.rng
    for j in range(len(rows) - 1):
        for k in range(seg):
            fcolor.append(band[j])
            ftone.append(rng.uniform(-0.08, 0.08) + (0.05 if (k + j) % 2 else -0.03))
    mb.sheet(rows, "cobble", close_u=True, grad=(0.5, 0.5), fcolor=fcolor, ftone=ftone)
    # centre disc under the fountain
    inner = rows[0]
    mb.poly(inner, "cobble_dark", facing=(0, 0, 1), grad=(0.5, 0.5))


def water_mesh(mb, plan):
    """Water surface of the stream and the pond (follows the falling water level)."""
    st = plan.stream
    offs = [-1.0, -0.55, 0.0, 0.55, 1.0]
    rows = []
    for i in range(len(st.xy)):
        p = st.xy[i]
        t = st.tangent(i)
        nx, ny = -t[1], t[0]
        w = st.hw[i] + 1.6
        rows.append([(float(p[0] + nx * o * w), float(p[1] + ny * o * w), float(st.z[i])) for o in offs])
    fcolor, ftone = [], []
    rng = mb.rng
    for _j in range(len(rows) - 1):
        for k in range(len(offs) - 1):
            fcolor.append("water" if k in (0, 3) else "water_deep")
            ftone.append(rng.uniform(-0.05, 0.05) + (0.1 if k in (0, 3) else 0.0))
    mb.sheet(rows, "water", grad=(0.5, 0.5), fcolor=fcolor, ftone=ftone)


def bank_mesh(mb, plan, skip=()):
    """Sandy shore band on both sides of the stream and around the pond.
    skip: list of (x, y, radius) where no band is drawn (bridge abutments)."""
    st = plan.stream
    offs = [-1.4, 0.2, 1.8, 3.2]
    rng = mb.rng
    for side in (1, -1):
        section = []

        def flush():
            if len(section) > 1:
                fcolor, ftone = [], []
                for _j in range(len(section) - 1):
                    for k in range(len(offs) - 1):
                        fcolor.append("sand")
                        ftone.append(rng.uniform(-0.05, 0.05) + (-0.12, 0.0, 0.08)[k])
                mb.sheet(section, "sand", grad=(0.5, 0.5), fcolor=fcolor, ftone=ftone)

        for i in range(len(st.xy)):
            p = st.xy[i]
            if any(math.hypot(p[0] - sx, p[1] - sy) < sr for sx, sy, sr in skip):
                flush()
                section = []
                continue
            t = st.tangent(i)
            nx, ny = -t[1] * side, t[0] * side
            row = []
            for k, o in enumerate(offs):
                x, y = p[0] + nx * (st.hw[i] + o), p[1] + ny * (st.hw[i] + o)
                z = plan.grid.at(x, y) + (0.16 if k < len(offs) - 1 else 0.05)
                row.append((float(x), float(y), float(z)))
            section.append(row)
        flush()
