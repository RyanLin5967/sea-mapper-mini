"""Run an autonomous survey: steer the boat along the plan and log soundings.

The log is written in the CSV shape `ingest` reads, so a mission feeds straight back
into `bathy contour`.
"""
from __future__ import annotations

import csv
import time
from typing import List, Tuple

from .boat import BoatLink, SimBoat
from .navigate import WaypointFollower


def run_mission(boat: BoatLink, waypoints: List[Tuple[float, float]], out_csv: str,
                arrival_radius: float = 3.0, max_steps: int = 100000) -> int:
    follower = WaypointFollower(waypoints, arrival_radius=arrival_radius)
    n = 0
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
            if depth is not None:
                w.writerow([f"{time.time():.1f}", f"{lat:.6f}", f"{lon:.6f}", f"{depth:.2f}"])
                n += 1
    boat.close()
    return n
