"""Project geographic coordinates to a local tangent plane in metres."""
from __future__ import annotations

import math
from typing import Callable, List, Tuple

from .ingest import Sounding

_R = 6378137.0  # WGS84 equatorial radius, metres


def reference(soundings: List[Sounding]) -> Tuple[float, float]:
    n = len(soundings)
    if n == 0:
        raise ValueError("no soundings to reference")
    return sum(s.lat for s in soundings) / n, sum(s.lon for s in soundings) / n


def projector(ref_lat: float, ref_lon: float) -> Callable[[float, float], Tuple[float, float]]:
    cos_lat = math.cos(math.radians(ref_lat))

    def to_xy(lat: float, lon: float) -> Tuple[float, float]:
        # A degree of longitude is only cos(lat) as wide as a degree of latitude.
        x = math.radians(lon - ref_lon) * _R * cos_lat
        y = math.radians(lat - ref_lat) * _R
        return x, y
    return to_xy


def project_all(soundings: List[Sounding]):
    ref_lat, ref_lon = reference(soundings)
    to_xy = projector(ref_lat, ref_lon)
    pts = [(*to_xy(s.lat, s.lon), s.depth_m) for s in soundings]
    return (ref_lat, ref_lon), pts
