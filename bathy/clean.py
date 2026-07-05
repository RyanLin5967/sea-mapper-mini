"""Remove obvious spikes from a sounding track.

Consumer sonar occasionally reports a wildly wrong depth (a fish, a thermocline, a
dropout). Compare each depth to the median of its neighbours along the track and replace
the outliers.
"""
from __future__ import annotations

from statistics import median
from typing import List

from .ingest import Sounding


def despike(soundings: List[Sounding], k: int = 3, thresh: float = 2.0) -> List[Sounding]:
    """Replace a depth that differs from its local median by more than `thresh` metres
    with that median. `k` is the half-window (points on each side)."""
    depths = [s.depth_m for s in soundings]
    out: List[Sounding] = []
    n = len(depths)
    for i, s in enumerate(soundings):
        # Clamp the window to [0, n); a bare depths[i-k:...] uses a negative start index
        # near the track start, which wraps to the end (or returns an empty slice).
        window = depths[max(0, i - k):min(n, i + k + 1)]
        m = median(window)
        if abs(s.depth_m - m) > thresh:
            out.append(Sounding(s.lat, s.lon, m, s.temp_c))
        else:
            out.append(s)
    return out
