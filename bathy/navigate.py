"""Waypoint navigation: steer the boat along a list of (lat, lon) waypoints."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

_R = 6371000.0  # mean earth radius, metres


def haversine(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _R * math.asin(min(1.0, math.sqrt(a)))


def bearing(lat1, lon1, lat2, lon2) -> float:
    """Initial bearing from 1 to 2, degrees in [0, 360)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


@dataclass
class Command:
    throttle: float
    rudder: float
    done: bool = False


@dataclass
class WaypointFollower:
    waypoints: List[Tuple[float, float]]
    arrival_radius: float = 3.0
    kp: float = 0.02
    cruise: float = 0.6
    _i: int = field(default=0)

    def update(self, lat: float, lon: float, heading: float) -> Command:
        if self._i >= len(self.waypoints):
            return Command(0.0, 0.0, done=True)

        tlat, tlon = self.waypoints[self._i]
        if haversine(lat, lon, tlat, tlon) <= self.arrival_radius:
            self._i += 1
            if self._i >= len(self.waypoints):
                return Command(0.0, 0.0, done=True)
            tlat, tlon = self.waypoints[self._i]

        target = bearing(lat, lon, tlat, tlon)
        error = target - heading
        rudder = max(-1.0, min(1.0, self.kp * error))
        return Command(self.cruise, rudder)

    @property
    def index(self) -> int:
        return self._i
