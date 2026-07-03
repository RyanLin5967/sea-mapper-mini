"""Render a gridded depth surface as a contour map."""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from .grid import Grid


def plot(grid: Grid, step: float = 1.0, out: Optional[str] = None):
    import matplotlib
    if out:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lo = np.floor(grid.z.min() / step) * step
    hi = np.ceil(grid.z.max() / step) * step
    levels = np.arange(lo, hi + step, step)

    fig, ax = plt.subplots(figsize=(8, 6))
    cf = ax.contourf(grid.x, grid.y, grid.z, levels=levels, cmap="viridis_r")
    ax.set_aspect("equal")  # 1 m east == 1 m north, or the shape is distorted
    ax.set_xlabel("east (m)")
    ax.set_ylabel("north (m)")
    fig.colorbar(cf, ax=ax, label="depth (m)")
    if out:
        fig.savefig(out, dpi=150)
        plt.close(fig)
        return out
    plt.show()
