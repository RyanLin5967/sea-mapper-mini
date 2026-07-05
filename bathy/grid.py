"""Interpolate scattered soundings onto a regular grid (inverse distance weighting)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class Grid:
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray


def _bounds(pts, pad):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def idw_grid(pts: List[Tuple[float, float, float]], cell: float = 2.0,
             power: float = 2.0, pad: float = 5.0) -> Grid:
    if not pts:
        raise ValueError("no points to grid")
    xmin, ymin, xmax, ymax = _bounds(pts, pad)
    gx = np.arange(xmin, xmax + cell, cell)
    gy = np.arange(ymin, ymax + cell, cell)
    z = np.empty((len(gy), len(gx)))

    px = np.array([p[0] for p in pts])
    py = np.array([p[1] for p in pts])
    pz = np.array([p[2] for p in pts])

    # Vectorise across a whole grid row at once (all columns x all samples), keeping one
    # row in memory rather than the full cells x samples matrix.
    eps = 1e-6  # distance floor (m): a node on a sounding gets a dominating finite weight
    for j, yy in enumerate(gy):
        dx = gx[:, None] - px[None, :]          # (ncols, npts)
        dy = yy - py
        d = np.hypot(dx, dy[None, :])
        np.maximum(d, eps, out=d)               # no 1/0 at coincident nodes
        w = 1.0 / d ** power
        # Use an elementwise reduction, not `w @ pz`: numpy's matmul emits spurious
        # divide/overflow fp-flag warnings here even though the result is correct.
        z[j, :] = (w * pz[None, :]).sum(axis=1) / w.sum(axis=1)
    return Grid(gx, gy, z)
