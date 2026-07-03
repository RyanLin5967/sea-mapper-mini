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

    for j, yy in enumerate(gy):
        for i, xx in enumerate(gx):
            d = np.hypot(px - xx, py - yy)
            hit = np.where(d == 0.0)[0]
            if hit.size:
                z[j, i] = pz[hit[0]]
                continue
            w = 1.0 / d ** power
            z[j, i] = np.sum(w * pz) / np.sum(w)
    return Grid(gx, gy, z)
