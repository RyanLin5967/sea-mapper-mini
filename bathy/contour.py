"""Render a gridded depth surface as a contour map."""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from .grid import Grid


def plot(grid: Grid, step: float = 1.0, out: Optional[str] = None,
         soundings_xy: Optional[List[Tuple[float, float]]] = None):
    import matplotlib
    if out:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lo = np.floor(np.nanmin(grid.z) / step) * step
    hi = np.ceil(np.nanmax(grid.z) / step) * step
    # A flat (or single-level) surface needs at least two levels, or contourf raises.
    if hi <= lo:
        hi = lo + step
    levels = np.arange(lo, hi + step, step)
    if len(levels) < 2:
        levels = np.array([lo, lo + step])

    fig, ax = plt.subplots(figsize=(8, 6))
    cf = ax.contourf(grid.x, grid.y, grid.z, levels=levels, cmap="viridis_r")
    ax.contour(grid.x, grid.y, grid.z, levels=levels, colors="k", linewidths=0.3)
    if soundings_xy:
        ax.plot([p[0] for p in soundings_xy], [p[1] for p in soundings_xy],
                ".", ms=1.5, color="white", alpha=0.4)
    ax.set_aspect("equal")  # 1 m east == 1 m north, or the shape is distorted
    ax.set_xlabel("east (m)")
    ax.set_ylabel("north (m)")
    fig.colorbar(cf, ax=ax, label="depth (m)")
    if out:
        fig.savefig(out, dpi=150)
        plt.close(fig)
        return out
    plt.show()
