"""2D level plan drawing (matplotlib). Used for docs and for checking the layout."""
import math

import numpy as np

from . import terrain as tr
from .plan import Footprint, plaza_radius

CATEGORY_STYLE = {
    "tree": ("#3f8f46", 22), "bush": ("#6fb04f", 7), "rock": ("#8a8c90", 9), "flowers": ("#e06aa0", 4),
}


def draw(plan, manifest, path, labels=True, size=14):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    from matplotlib.patches import Polygon

    H = plan.grid.H
    fig, ax = plt.subplots(figsize=(size, size), dpi=110)
    ext = (-tr.HALF, tr.HALF, -tr.HALF, tr.HALF)
    ls = LightSource(azdeg=315, altdeg=45)
    base = np.zeros(H.shape + (3,))
    base[..., 0], base[..., 1], base[..., 2] = 0.55, 0.74, 0.42
    shade = ls.shade_rgb(base, H, vert_exag=2.2, blend_mode="soft")
    ax.imshow(shade, extent=ext, origin="lower", interpolation="bilinear")
    cs = ax.contour(np.linspace(-tr.HALF, tr.HALF, H.shape[1]), np.linspace(-tr.HALF, tr.HALF, H.shape[0]), H,
                    levels=np.arange(-10, 60, 5), colors="#35532c", linewidths=0.4, alpha=0.55)
    ax.clabel(cs, fmt="%d", fontsize=5)

    st = plan.stream
    for i in range(len(st.xy) - 1):
        t = st.tangent(i)
        n = np.array([-t[1], t[0]])
        a0, a1 = st.xy[i] + n * st.hw[i], st.xy[i] - n * st.hw[i]
        b0, b1 = st.xy[i + 1] + n * st.hw[i + 1], st.xy[i + 1] - n * st.hw[i + 1]
        ax.add_patch(Polygon([a0, a1, b1, b0], closed=True, fc="#5aa9d6", ec="none", zorder=2))

    th = np.linspace(0, 2 * math.pi, 90)
    ax.fill([plaza_radius(t) * math.cos(t) for t in th], [plaza_radius(t) * math.sin(t) for t in th],
            fc="#c9c2b2", ec="#8d8577", lw=0.8, zorder=3)
    colors = {"main": "#b9b0a0", "lane": "#a79d8e", "path": "#a98660"}
    for rd in plan.roads:
        p = rd["poly"]
        ax.plot(p.xy[:, 0], p.xy[:, 1], color=colors[rd["kind"]], lw=rd["hw"] * 2 / tr.WORLD * size * 72 * 0.86,
                solid_capstyle="round", zorder=3)
        if labels:
            mid = p.xy[len(p.xy) // 2]
            ax.text(mid[0], mid[1], rd["name"], fontsize=5.5, color="#4a4136", ha="center", va="center", zorder=9,
                    style="italic")

    for inst in plan.instances:
        a = inst["asset"]
        cat = manifest[a]["category"]
        if cat in ("houses", "landmarks") or a in ("bridge_stone", "gate_arch", "dock", "fountain", "well"):
            fp = Footprint(inst, manifest[a]["bounds_blender"], shrink=1.0)
            fc = "#b5533c" if cat == "houses" else "#7a4f9a" if cat == "landmarks" else "#6b6b6b"
            ax.add_patch(Polygon(fp.corners(), closed=True, fc=fc, ec="#2b1d14", lw=0.6, zorder=6, alpha=0.92))
            if cat in ("houses", "landmarks"):
                # door side marker
                ang = math.radians(inst["rot"])
                fx, fy = math.sin(ang), -math.cos(ang)
                ax.plot([fp.cx, fp.cx + fx * fp.hy], [fp.cy, fp.cy + fy * fp.hy], color="#ffe9a8", lw=1.0, zorder=7)
                if labels:
                    ax.text(fp.cx, fp.cy + fp.radius * 0.75 + 4, inst.get("name", a), fontsize=5.2, ha="center",
                            zorder=10, color="#1c1410",
                            bbox=dict(fc="white", ec="none", alpha=0.6, pad=0.6))
        elif a.startswith("tree"):
            ax.scatter([inst["x"]], [inst["y"]], s=20 * inst["scale"] ** 2, c="#2f6f3a" if "pine" in a else "#3f9a48",
                       alpha=0.85, lw=0, zorder=5)
        elif a.startswith("bush") or a == "hedge":
            ax.scatter([inst["x"]], [inst["y"]], s=5, c="#6fb04f", lw=0, zorder=4)
        elif a.startswith("rock"):
            ax.scatter([inst["x"]], [inst["y"]], s=8 if a != "rock_cliff" else 40, c="#7d7f84", lw=0, zorder=4)
        elif a.startswith("flowers"):
            ax.scatter([inst["x"]], [inst["y"]], s=3, c="#e0669c", lw=0, zorder=4)
        elif a.startswith("lantern"):
            ax.scatter([inst["x"]], [inst["y"]], s=9, c="#ffd24a", edgecolors="#5a4a10", lw=0.3, zorder=8)
        elif a.startswith("fence") or a == "stone_wall":
            ang = math.radians(inst["rot"])
            dx, dy = 4 * math.cos(ang), 4 * math.sin(ang)
            ax.plot([inst["x"] - dx, inst["x"] + dx], [inst["y"] - dy, inst["y"] + dy],
                    color="#6b4a2a" if a != "stone_wall" else "#666", lw=0.8, zorder=5)
        elif a in ("wheat_patch", "pumpkin_patch", "garden_bed"):
            ax.scatter([inst["x"]], [inst["y"]], s=26, marker="s", c="#d9b95a" if a == "wheat_patch" else "#8a6a3a",
                       lw=0, zorder=4)
        elif cat == "props":
            ax.scatter([inst["x"]], [inst["y"]], s=6, c="#3b3b3b", marker="D", lw=0, zorder=6)
    ax.set_xlim(-tr.HALF, tr.HALF)
    ax.set_ylim(-tr.HALF, tr.HALF)
    ax.set_aspect("equal")
    ax.set_xlabel("X (studs, east)   |   Roblox: X")
    ax.set_ylabel("Y (studs, north)   |   Roblox: -Z")
    ax.set_title("Levelplan Dorf - Blender-Koordinaten, 1 Einheit = 1 Stud", fontsize=11)
    ax.grid(color="k", alpha=0.08, lw=0.4)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
