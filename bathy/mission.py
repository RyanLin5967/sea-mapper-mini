"""Run an autonomous survey: steer the boat along the plan and log soundings.

The log is written in the CSV shape `ingest` reads, so a mission feeds straight back
into `bathy contour`.
"""
from __future__ import annotations

import csv
import time
from typing import List, Tuple

from .boat import BoatLink, SimBoat
from .navigate import WaypointFollower, haversine


def run_mission(boat: BoatLink, waypoints: List[Tuple[float, float]], out_csv: str,
                arrival_radius: float = 3.0, log_spacing: float = 1.0,
                max_steps: int = 100000) -> int:
    """Drive the waypoints to completion, logging a sounding roughly every `log_spacing`
    metres of travel (not every control tick). Returns the number of soundings written."""
    follower = WaypointFollower(waypoints, arrival_radius=arrival_radius)
    n = 0
    last = None  # (lat, lon) of the last logged sounding
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Time", "Latitude", "Longitude", "Depth"])
        for _ in range(max_steps):
            lat, lon, heading, depth = boat.state()
            cmd = follower.update(lat, lon, heading)
            if cmd.done:
                break
            boat.drive(cmd)
            if isinstance(boat, SimBoat):
                boat.step()
            if depth is not None and (last is None or haversine(last[0], last[1], lat, lon) >= log_spacing):
                w.writerow([f"{time.time():.1f}", f"{lat:.6f}", f"{lon:.6f}", f"{depth:.2f}"])
                last = (lat, lon)
                n += 1
    boat.close()
    return n
