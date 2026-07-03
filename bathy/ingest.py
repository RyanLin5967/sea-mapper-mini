"""Load logged soundings from the Deeper sonar CSV export."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Sounding:
    lat: float
    lon: float
    depth_m: float
    temp_c: Optional[float] = None


_LAT_KEYS = {"latitude", "lat"}
_LON_KEYS = {"longitude", "lon", "lng", "long"}
_DEPTH_KEYS = {"depth", "depth_m", "depth(m)"}


def _pick(header, keys):
    for i, h in enumerate(header):
        if h.strip().lower() in keys:
            return i
    return None


def load_csv(path: str) -> List[Sounding]:
    out: List[Sounding] = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"{path}: empty file")
        ilat = _pick(header, _LAT_KEYS)
        ilon = _pick(header, _LON_KEYS)
        idep = _pick(header, _DEPTH_KEYS)
        if ilat is None or ilon is None or idep is None:
            raise ValueError(f"{path}: need latitude, longitude, depth columns")
        for row in reader:
            if len(row) <= max(ilat, ilon, idep):
                continue
            depth = float(row[idep])
            # The sonar logs depth 0.0 when it has no bottom lock; those pings are not
            # real soundings and pull the interpolated surface shallow. Drop them.
            if depth <= 0.0:
                continue
            out.append(Sounding(float(row[ilat]), float(row[ilon]), depth))
    return out
