"""Plan a lawnmower (boustrophedon) survey over a rectangular area."""
from __future__ import annotations

import math
from typing import List, Tuple

from .geo import projector, unprojector

Pt = Tuple[float, float]


def lawnmower(xmin: float, ymin: float, xmax: float, ymax: float,
              spacing: float) -> List[Pt]:
    """Ordered (x, y) waypoints in local metres. Lines run along y, step along x."""
    if spacing <= 0:
        raise ValueError("spacing must be positive")
    # Enough lines that the last reaches xmax; a bare `while x < xmax` stops up to a full
    # spacing short and leaves the far strip unsurveyed. Clamp the last line to xmax.
    n_lines = max(1, math.ceil((xmax - xmin) / spacing)) + 1
    waypoints: List[Pt] = []
    for k in range(n_lines):
        x = min(xmin + k * spacing, xmax)
        if k % 2 == 0:
            waypoints.append((x, ymin))
            waypoints.append((x, ymax))
        else:
            waypoints.append((x, ymax))
            waypoints.append((x, ymin))
    return waypoints


def plan_latlon(corner_a: Pt, corner_b: Pt, spacing: float) -> List[Pt]:
    """Plan over the lat/lon rectangle spanned by two (lat, lon) corners; returns (lat, lon)."""
    (la, lo_a), (lb, lo_b) = corner_a, corner_b
    ref_lat = (la + lb) / 2.0
    ref_lon = (lo_a + lo_b) / 2.0
    to_xy = projector(ref_lat, ref_lon)
    to_ll = unprojector(ref_lat, ref_lon)

    xa, ya = to_xy(la, lo_a)
    xb, yb = to_xy(lb, lo_b)
    xmin, xmax = sorted((xa, xb))
    ymin, ymax = sorted((ya, yb))

    xy = lawnmower(xmin, ymin, xmax, ymax, spacing)
    return [(lat, lon) for (lon, lat) in (to_ll(x, y) for x, y in xy)]
